from notifications.models import Notification 
from courses.models import Lesson, Exercise, Course
from rewards.models import BlockchainTransaction
from notifications.serializers import NotificationSerializer
from courses.serializers import LessonSerializer, TeacherCourseSerializer, CourseSerializer
from core.serializers import BlockchainTransactionSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.permissions import IsTeacher, IsStudent
from django.db.models import Count, Sum, F, Q
from django.db import models
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_GET
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.views.decorators.cache import cache_page


class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        user = request.user
        
        # ✅ OTTIMIZZATO - Cache dashboard data for 5 minutes
        cache_key = f'student_dashboard_{user.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)

        # ✅ OTTIMIZZATO - Single optimized query for purchased courses using enrollments
        from courses.models import CourseEnrollment
        purchased_courses = Course.objects.filter(
            enrollments__student=user, is_approved=True
        ).select_related('teacher').prefetch_related('lessons').annotate(
            lessons_count=Count('lessons'),
            completed_lessons_count=Count('lessons__completions', filter=Q(lessons__completions__student=user))
        ).distinct()
        courses_data = CourseSerializer(purchased_courses, many=True, context={'request': request}).data

        # ✅ OTTIMIZZATO - Limit and optimize transactions query
        recent_transactions = BlockchainTransaction.objects.filter(
            user=user
        ).select_related().order_by('-created_at')[:10]
        transactions_data = BlockchainTransactionSerializer(recent_transactions, many=True).data

        # ✅ OTTIMIZZATO - Limit notifications query
        notifications = Notification.objects.filter(
            user=user, read=False
        ).order_by('-created_at')[:5]
        notifications_data = NotificationSerializer(notifications, many=True).data

        # Get blockchain balance instead of database balance
        blockchain_balance = "0"
        if user.wallet_address:
            try:
                from blockchain.blockchain import teocoin_service
                blockchain_balance = str(teocoin_service.get_balance(user.wallet_address))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error getting blockchain balance: {e}")
                blockchain_balance = "0"

        data = {
            "username": user.username,
            "blockchain_balance": blockchain_balance,
            "wallet_address": user.wallet_address,
            "courses": courses_data,
            "recent_transactions": transactions_data,
            "notifications": notifications_data,
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, data, 300)
        
        return Response(data)

class TeacherDashboardAPI(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        user = request.user
        
        # ✅ OTTIMIZZATO - Cache teacher dashboard for 10 minutes
        cache_key = f'teacher_dashboard_{user.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        # ✅ OTTIMIZZATO - Single query with annotations instead of N+1
        courses = user.courses_created.prefetch_related(
            'students', 'lessons', 'lessons__exercises'
        ).annotate(
            student_count=Count('students'),
            total_revenue=Count('students') * F('price')
        )
        
        total_courses = courses.count()
        
        # Calculate aggregated values from annotated queryset
        total_earnings = 0
        total_students_set = set()
        
        # Process courses data efficiently 
        for course in courses:
            # Use annotated student_count instead of calling .count() 
            student_count = course.student_count
            course_earnings = (course.price or 0) * student_count * 0.9
            total_earnings += course_earnings
            
            # Collect all unique student IDs efficiently
            total_students_set.update(course.students.values_list('id', flat=True))

        # ✅ OTTIMIZZATO - Calculate sales with single queries per period
        now = timezone.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        # Single aggregated query for all sales periods
        sales_data = BlockchainTransaction.objects.filter(
            user=user,
            transaction_type='course_earned'  # Only teacher earnings
        ).aggregate(
            daily=Sum('amount', filter=Q(created_at__gte=start_of_day)),
            monthly=Sum('amount', filter=Q(created_at__gte=start_of_month)),
            yearly=Sum('amount', filter=Q(created_at__gte=start_of_year))
        )

        # ✅ OTTIMIZZATO - Single query for recent transactions
        recent_transactions = BlockchainTransaction.objects.filter(
            user=user
        ).select_related().order_by('-created_at')[:10]
        transactions_data = BlockchainTransactionSerializer(recent_transactions, many=True).data
        # Get blockchain balance
        blockchain_balance = "0"
        if user.wallet_address:
            try:
                from blockchain.blockchain import teocoin_service
                blockchain_balance = str(teocoin_service.get_balance(user.wallet_address))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error getting blockchain balance: {e}")
                blockchain_balance = "0"
    
        data = {
            "blockchain_balance": blockchain_balance,
            "wallet_address": user.wallet_address,
            "stats": {
                "total_courses": total_courses,
                "total_earnings": round(total_earnings, 2),
                "active_students": len(total_students_set),
            },
            "sales": {
                "daily": round(sales_data['daily'] or 0, 2),
                "monthly": round(sales_data['monthly'] or 0, 2),
                "yearly": round(sales_data['yearly'] or 0, 2),
            },
            "courses": TeacherCourseSerializer(courses, many=True, context={'request': request}).data,
            "transactions": transactions_data,
        }

        # Cache for 10 minutes 
        cache.set(cache_key, data, 600)
        
        return Response(data)
    
    
def is_student_or_superuser(user):
    return user.role == 'student' or user.is_superuser

@user_passes_test(is_student_or_superuser)
@login_required
@require_GET
def dashboard_transactions(request):
    transactions = BlockchainTransaction.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'dashboard/partials/transactions.html', {
        'transactions': transactions
    })

class UserRoleDashboardAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == 'student':
            dashboard_url = '/dashboard/student'
        elif user.role == 'teacher':
            dashboard_url = '/dashboard/teacher'
        else:
            dashboard_url = '/dashboard'  # Default dashboard

        return Response({
            "role": user.role,
            "dashboard_url": dashboard_url
        })

class AdminDashboardAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Get blockchain balance
        blockchain_balance = "0"
        if user.wallet_address:
            try:
                from blockchain.blockchain import teocoin_service
                blockchain_balance = str(teocoin_service.get_balance(user.wallet_address))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error getting blockchain balance: {e}")
        
        # Mostra saldo blockchain e info admin
        return Response({
            "username": user.username,
            "blockchain_balance": blockchain_balance,
            "wallet_address": user.wallet_address,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        })