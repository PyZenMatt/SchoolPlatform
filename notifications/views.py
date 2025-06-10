from .models import Notification
from .serializers import NotificationSerializer
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as df_filters
from rest_framework.generics import UpdateAPIView

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

class NotificationMarkReadView(UpdateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    queryset = Notification.objects.all()
    lookup_url_kwarg = 'notification_id'

class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({'message': 'Tutte le notifiche sono state marcate come lette'}, 
                       status=status.HTTP_200_OK)

class NotificationClearAllView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        count = Notification.objects.filter(user=request.user).count()
        Notification.objects.filter(user=request.user).delete()
        return Response({'message': f'{count} notifiche sono state eliminate'}, 
                       status=status.HTTP_200_OK)

class NotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, notification_id):
        try:
            notification = get_object_or_404(Notification, id=notification_id, user=request.user)
            notification.delete()
            return Response({'message': 'Notifica eliminata con successo'}, 
                           status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, 
                           status=status.HTTP_400_BAD_REQUEST)
