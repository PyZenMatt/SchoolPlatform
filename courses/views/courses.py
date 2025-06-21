from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters
from django.contrib.auth import get_user_model
from django.db import models
import logging

from users.permissions import IsAdminOrApprovedTeacherOrReadOnly, IsTeacher
from courses.models import Course
from courses.serializers import CourseSerializer
from services.course_service import course_service
from services.exceptions import CourseNotFoundError, TeoArtServiceException

logger = logging.getLogger(__name__)


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


class CourseListAPIView(generics.ListAPIView):
    """
    API view for listing courses using CourseService
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        try:
            # Use CourseService with fallback to original logic
            try:
                courses_data = course_service.get_available_courses(user=request.user)
                return Response({
                    'courses': courses_data,
                    'count': len(courses_data),
                    'service_used': 'CourseService',
                    'success': True
                })
            except Exception as e:
                # TODO: Remove fallback logic in production once CourseService is fully stable
                logger.warning(f"CourseService failed, using fallback: {e}")
                
                user = request.user
                if user.is_staff or user.is_superuser:
                    queryset = Course.objects.all()
                else:
                    queryset = Course.objects.filter(is_approved=True)
                
                queryset = queryset.select_related('teacher').prefetch_related('students')
                
                courses_data = []
                for course in queryset:
                    is_enrolled = course.students.filter(id=user.id).exists() if user.is_authenticated else False
                    courses_data.append({
                        'id': course.id,
                        'title': course.title,
                        'description': course.description,
                        'price': float(course.price),
                        'category': course.category,
                        'cover_image': course.cover_image.url if course.cover_image else None,
                        'creator': {
                            'id': course.teacher.id,
                            'username': course.teacher.username,
                        },
                        'is_enrolled': is_enrolled,
                        'lesson_count': course.lessons_in_course.count(),
                        'created_at': course.created_at.isoformat(),
                    })
                
                return Response({
                    'courses': courses_data,
                    'count': len(courses_data),
                    'service_used': 'Fallback'
                })
                
        except Exception as e:
            return Response(
                {'error': f'Error retrieving courses: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CourseDetailAPIView(generics.RetrieveAPIView):
    """
    API view for course details using CourseService
    """
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        try:
            course_id = kwargs.get('pk')
            
            # Use CourseService with fallback to original logic
            try:
                course_details = course_service.get_course_details(course_id, user=request.user)
                return Response({
                    **course_details,
                    'service_used': 'CourseService',
                    'success': True
                })
            except CourseNotFoundError:
                return Response(
                    {'error': 'Course not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                # TODO: Remove fallback logic in production once CourseService is fully stable  
                logger.warning(f"CourseService failed, using fallback: {e}")
                
                try:
                    course = Course.objects.select_related('teacher').get(
                        id=course_id,
                        is_approved=True
                    )
                except Course.DoesNotExist:
                    return Response(
                        {'error': 'Course not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                
                is_enrolled = course.students.filter(id=request.user.id).exists()
                lessons = course.lessons_in_course.all().order_by('id')
                
                lessons_data = []
                for lesson in lessons:
                    lessons_data.append({
                        'id': lesson.id,
                        'title': lesson.title,
                        'content': lesson.content,
                        'lesson_type': lesson.lesson_type,
                        'duration': lesson.duration,
                        'is_completed': False,  # Simplified for fallback
                    })
                
                course_details = {
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'price': float(course.price),
                    'category': course.category,
                    'cover_image': course.cover_image.url if course.cover_image else None,
                    'creator': {
                        'id': course.teacher.id,
                        'username': course.teacher.username,
                        'bio': getattr(course.teacher, 'bio', ''),
                    },
                    'is_enrolled': is_enrolled,
                    'progress': 0,  # Simplified for fallback
                    'lessons': lessons_data,
                    'total_lessons': len(lessons_data),
                    'created_at': course.created_at.isoformat(),
                    'updated_at': course.updated_at.isoformat(),
                    'service_used': 'Fallback'
                }
                
                return Response(course_details)
                
        except Exception as e:
            return Response(
                {'error': f'Error retrieving course details: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )