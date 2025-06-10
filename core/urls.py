from django.urls import path, include

from .dashboard import TeacherDashboardAPI, StudentDashboardView, dashboard_transactions, UserRoleDashboardAPI, AdminDashboardAPI
from .api import dashboard_data
from .batch_api import StudentBatchDataAPI, CourseBatchDataAPI, LessonBatchDataAPI
from .health_check import HealthCheckView  # Health check for monitoring

urlpatterns = [
    # Health check endpoint
    path('health/', HealthCheckView.as_view(), name='health-check'),
    
    # Dashboard endpoints
    path('dashboard/student/', StudentDashboardView.as_view(), name='student-dashboard'),
    path('dashboard/teacher/', TeacherDashboardAPI.as_view(), name='teacher_dashboard'),
    path('dashboard/admin/', AdminDashboardAPI.as_view(), name='admin_dashboard'),
    
    # ✅ OPTIMIZED - Batch API endpoints to reduce frontend calls
    path('api/student/batch-data/', StudentBatchDataAPI.as_view(), name='student-batch-data'),
    path('api/course/<int:course_id>/batch-data/', CourseBatchDataAPI.as_view(), name='course-batch-data'),
    path('api/lesson/<int:lesson_id>/batch-data/', LessonBatchDataAPI.as_view(), name='lesson-batch-data'),
    
    path('', include('notifications.urls')),  # <-- aggiungi questa riga
    
   
]
