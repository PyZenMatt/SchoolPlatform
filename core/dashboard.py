from notifications.models import Notification 
from courses.models import Lesson, Exercise
from rewards.models import TeoCoinTransaction
from notifications.serializers import NotificationSerializer
from courses.serializers import LessonSerializer, TeacherCourseSerializer
from rewards.serializers import TeoCoinTransactionSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsTeacher
from django.db.models import Count
from users.permissions import IsStudent
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_GET



class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]  # Assicurati che IsStudent sia definito correttamente

    def get(self, request):
        user = request.user

        # Lezioni acquistate dallo studente
        purchased_lessons = Lesson.objects.filter(students=user)
        lessons_data = LessonSerializer(purchased_lessons, many=True).data

        # Transazioni recenti TeoCoin
        recent_transactions = TeoCoinTransaction.objects.filter(user=user).order_by('-created_at')[:5]
        transactions_data = TeoCoinTransactionSerializer(recent_transactions, many=True).data

        # Esercizi completati (supponendo che tu abbia una logica per questo)
        completed_exercises = Exercise.objects.filter(completed_by=user) if hasattr(Exercise, 'completed_by') else []

        # Notifiche (se hai implementato questo modello)
        notifications = Notification.objects.filter(user=user, is_read=False).order_by('-created_at')[:5]
        notifications_data = NotificationSerializer(notifications, many=True).data

        return Response({
            "username": user.username,
            "teo_coins": user.teo_coins,
            "lessons": lessons_data,
            "recent_transactions": transactions_data,
            "completed_exercises_count": len(completed_exercises),
            "notifications": notifications_data,
        })

class TeacherDashboardAPI(APIView):
    permission_classes = [IsTeacher]

    def get(self, request):
        # Ottieni i corsi dell'insegnante con lezioni e studenti
        courses = request.user.courses_created.prefetch_related('lessons', 'students')

        # Statistiche individuali per ogni corso
        course_data = courses.annotate(
            student_count=Count('students', distinct=True)
        )

        total_courses = courses.count()
        total_earnings = 0
        total_students_set = set()

        for course in course_data:
            total_earnings += (course.price or 0) * course.student_count * 0.9
            total_students_set.update(course.students.values_list('id', flat=True))

        data = {
            "stats": {
                "total_courses": total_courses,
                "total_earnings": round(total_earnings, 2),
                "active_students": len(total_students_set),
            },
            "courses": TeacherCourseSerializer(courses, many=True).data
        }

        return Response(data)
    
def is_student_or_superuser(user):
    return user.role == 'student' or user.is_superuser

@user_passes_test(is_student_or_superuser)
@login_required
@require_GET
def dashboard_transactions(request):
    transactions = TeoCoinTransaction.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'dashboard/partials/transactions.html', {
        'transactions': transactions
    })