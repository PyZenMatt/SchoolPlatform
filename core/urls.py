from django.urls import path
from .views import RegisterView, LessonListCreateView, ExerciseListCreateView, UserTeoCoinsView,TransferTeoCoinsView, earn_teo_coins, transfer_teo_coins, PurchaseLessonView, CourseListCreateView, CourseDetailView, TransactionHistoryView, NotificationListView, NotificationMarkReadView, teocoin_balance, dashboard_transactions,TeacherDashboardAPI, CreateLessonAPI, CreateCourseAPI
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView 
from .api import dashboard_data

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('lessons/', LessonListCreateView.as_view(), name='lesson_list_create'),
    path('exercises/', ExerciseListCreateView.as_view(), name='exercise_list_create'),
    path('teo-coins/', UserTeoCoinsView.as_view(), name='teo-coins'),
    path('transfer-teo-coins/', TransferTeoCoinsView.as_view(), name='transfer-teo-coins'),
    path('earn-teo-coins/', earn_teo_coins, name='earn_teo_coins'),
    path('lessons/<int:lesson_id>/purchase/', PurchaseLessonView.as_view(), name='purchase-lesson'),
    path('courses/', CourseListCreateView.as_view()),
    path('courses/<int:pk>/', CourseDetailView.as_view()),
    path('transactions/', TransactionHistoryView.as_view(),name='transaction-history'),
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('teo-coins/balance/', teocoin_balance, name='teocoin-balance'),
    path('dashboard/', dashboard_data, name='dashboard-api'),
    path('dashboard/transactions/', dashboard_transactions, name='dashboard-transactions'),
    path('teacher/dashboard/', TeacherDashboardAPI.as_view(), name='teacher_dashboard'),
    path('teacher/lessons/', CreateLessonAPI.as_view(), name='create_lesson'),
    path('teacher/courses/', CreateCourseAPI.as_view(), name='create_courses'),
   
]
