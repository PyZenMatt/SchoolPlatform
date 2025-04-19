from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from .models import Lesson, Exercise, Course, TeoCoinTransaction, Course
from .serializers import LessonSerializer, ExerciseSerializer, CourseSerializer
from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.shortcuts import get_object_or_404
from rest_framework import generics, filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.views.decorators.http import require_GET
from users.permissions import IsTeacher
from users.permissions import IsStudent
from rest_framework.permissions import BasePermission
from django.contrib.auth.decorators import login_required

# Create your views here.
# Lezioni (solo per utenti autenticati)
class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = LessonSerializer

    def perform_create(self, serializer):
        # Verifica che l'utente sia un maestro
        if self.request.user.role != 'teacher':
            raise PermissionDenied("Solo i maestri possono creare lezioni.")

        # Imposta l'utente attualmente autenticato come insegnante (teacher) della lezione
        serializer.save(teacher=self.request.user)

# Esercizi (solo per utenti autenticati)
class ExerciseListCreateView(generics.ListCreateAPIView):
    queryset = Exercise.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseSerializer

    def perform_create(self, serializer):
        # Imposta l'utente attualmente autenticato come creatore dell'esercizio
        serializer.save(owner=self.request.user)

class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_fields = ['teacher', 'price']
    search_fields = ['title', 'description']

    def perform_create(self, serializer):
        if self.request.user.role != 'teacher':
            raise PermissionDenied("Solo i maestri possono creare corsi")
        serializer.save(teacher=self.request.user)

class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def perform_update(self, serializer):
        if serializer.instance.teacher != self.request.user:
            raise PermissionDenied("Non sei il proprietario di questo corso")
        serializer.save()

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'student'

class PurchaseCourseView(APIView):
    permission_classes = [IsStudent]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        student = request.user

        if student.teo_coins < course.price:
            return Response(
                {"error": "TeoCoin insufficienti"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Transazione atomica
        with transaction.atomic():
            student.teo_coins -= course.price
            student.save()
            
            course.teacher.teo_coins += course.price * 0.9
            course.teacher.save()

            course.students.add(student)

            # Crea transazione
            TeoCoinTransaction.objects.create(
                user=student,
                amount=-course.price,
                transaction_type='course_purchase'
            )
            TeoCoinTransaction.objects.create(
                user=course.teacher,
                amount=course.price * 0.9,
                transaction_type='course_earned'
            )

        return Response({"success": "Corso acquistato!"})
        

class PurchaseLessonView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        student = request.user

        if student.role != 'student':
            return Response({"error": "Solo studenti possono acquistare lezioni"}, status=status.HTTP_403_FORBIDDEN)

        if student in lesson.students.all():
            return Response({"error": "Hai già acquistato questa lezione"}, status=status.HTTP_400_BAD_REQUEST)

        if student.teo_coins < lesson.price:
            return Response({"error": "TeoCoin insufficienti"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                student.subtract_teo_coins(lesson.price)
                lesson.teacher.add_teo_coins(int(lesson.price * 0.9))
                lesson.students.add(student)

                TeoCoinTransaction.objects.create(
                    user=student,
                    amount=-lesson.price,
                    transaction_type='lesson_purchase'
                )
                TeoCoinTransaction.objects.create(
                    user=lesson.teacher,
                    amount=int(lesson.price * 0.9),
                    transaction_type='lesson_earned'
                )

                return Response({
                    "message": "Lezione acquistata con successo!",
                    "teacher_earned": lesson.price * 0.9,
                    "platform_fee": lesson.price * 0.1
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        platform_fee = lesson.price * 0.10
        teacher_earnings = lesson.price - platform_fee

        student.subtract_teo_coins(lesson.price)
        lesson.teacher.add_teo_coins(int(teacher_earnings))
        lesson.students.add(student)  # Registra lo studente

        TeoCoinTransaction.objects.create(
            user=student,
            amount=-lesson.price,
            transaction_type='spent'
        )
        TeoCoinTransaction.objects.create(
            user=lesson.teacher,
            amount=teacher_earnings,
            transaction_type='earned'
        )

        return Response({
            "message": "Lezione acquistata con successo!",
            "teacher_earned": teacher_earnings,
            "platform_fee": platform_fee
        })
    
class CreateLessonAPI(APIView):
    permission_classes = [IsTeacher]

    def post(self, request):
        serializer = LessonSerializer(data=request.data)
        if serializer.is_valid():
            lesson = serializer.save(teacher=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateCourseAPI(APIView):
    permission_classes = [IsTeacher]

    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            course = serializer.save(teacher=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class CourseEnrollmentAPI(APIView):
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        
        if request.user in course.students.all():
            return Response(
                {"error": "Sei già iscritto a questo corso"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        course.students.add(request.user)
        return Response(
            {"success": "Iscrizione completata"},
            status=status.HTTP_201_CREATED
        )
    
class ExerciseSubmitAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Se lo studente è l'utente loggato
        request.data['student'] = request.user.username
        
        serializer = ExerciseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
# View per creare corsi
class CourseCreateAPI(generics.CreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsTeacher]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

# View per gestire lezioni
class LessonCreateAPI(generics.CreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsTeacher]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

# View per assegnare lezioni a corsi
class AssignLessonToCourseAPI(generics.UpdateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsTeacher]

    def perform_update(self, serializer):
        course = serializer.validated_data.get('course')
        if course.teacher != self.request.user:
            raise PermissionDenied("Non sei il proprietario di questo corso")
        serializer.save()