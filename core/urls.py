from django.urls import path

from .dashboard import TeacherDashboardAPI, StudentDashboardView, dashboard_transactions
from .api import dashboard_data


urlpatterns = [
    
    
    path('student/dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),
    path('dashboard/', dashboard_data, name='dashboard-api'),
    path('dashboard/transactions/', dashboard_transactions, name='dashboard-transactions'),
    path('teacher/dashboard/', TeacherDashboardAPI.as_view(), name='teacher_dashboard'),

    
    
   
]
