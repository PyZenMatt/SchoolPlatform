from .views import NotificationListView, NotificationMarkReadView
from django.urls import path

urlpatterns = [
    
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
]