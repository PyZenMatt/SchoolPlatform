from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters
from django.contrib.auth import get_user_model
from django.db import models

from users.permissions import IsAdminOrApprovedTeacherOrReadOnly, IsTeacher
from courses.models import Course
from courses.serializers import CourseSerializer


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdminOrApprovedTeacherOrReadOnly]
    
    def get_queryset(self):
        # ✅ OTTIMIZZATO - Prevent N+1 queries with select_related and prefetch_related
        return Course.objects.select_related('teacher').prefetch_related(
            'students', 'lessons', 'enrollments'
        ).annotate(
            student_count=models.Count('students')
        )


class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdminOrApprovedTeacherOrReadOnly]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['teacher', 'price', 'category']
    search_fields = ['title', 'description', 'teacher__username']
    ordering_fields = ['created_at', 'price', 'student_count']
    ordering = ['-created_at']  # Default ordering by newest

    def get_queryset(self):
        # Mostra solo corsi approvati per utenti non admin
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Admin può vedere tutti i corsi
            queryset = Course.objects.all()
        else:
            # Altri utenti vedono solo corsi approvati
            queryset = Course.objects.filter(is_approved=True)
            
        queryset = queryset.annotate(
            student_count=models.Count('students')
        ).prefetch_related('students', 'teacher', 'lessons')
        
        # Filtro per categoria se specificato tramite query params
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        return queryset

    def perform_create(self, serializer):
        if getattr(self.request.user, 'role', None) != 'teacher':
            raise PermissionDenied("Solo i maestri possono creare corsi")
        User = get_user_model()
        user = User.objects.get(pk=self.request.user.pk)
        if not getattr(user, 'is_approved', False):
            raise PermissionDenied("Solo i teacher approvati possono creare corsi. Aspetta l'approvazione dell'admin.")
        serializer.save(teacher=user)


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdminOrApprovedTeacherOrReadOnly]
    queryset = Course.objects.all()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        # Admin può vedere tutto, altri solo corsi approvati
        if not (user.is_staff or user.is_superuser) and not obj.is_approved:
            raise PermissionDenied("Corso non approvato")
        return obj

    def perform_update(self, serializer):
        if serializer.instance.teacher != self.request.user:
            raise PermissionDenied("Non sei il proprietario di questo corso")
        serializer.save()


class CreateCourseAPI(generics.CreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsTeacher]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)