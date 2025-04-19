from .models import Notification
from .serializers import NotificationSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as df_filters

class NotificationFilter(df_filters.FilterSet):
    created_after = df_filters.DateTimeFilter(
    field_name='created_at', 
    lookup_expr='gte',
    help_text="Filtra notifiche create dopo questa data/ora (YYYY-MM-DD HH:MM:SS)"
    )

    class Meta:
        model = Notification
        fields = ['notification_type', 'read']

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]  
    filterset_fields = ['notification_type', 'read']
    filterset_class = NotificationFilter 
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.read = True
        notification.save()
        return Response({"status": "marked as read"})
