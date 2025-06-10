from .views import (
    NotificationListView, 
    NotificationMarkReadView, 
    NotificationMarkAllReadView,
    NotificationClearAllView,
    NotificationDeleteView
)
from django.urls import path

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/read/', NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('notifications/<int:notification_id>/', NotificationDeleteView.as_view(), name='notification-delete'),
    path('notifications/mark-all-read/', NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('notifications/clear-all/', NotificationClearAllView.as_view(), name='notification-clear-all'),
]