from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Lesson, TeoCoinTransaction, Notification
from .serializers import LessonSerializer, TeoCoinTransactionSerializer, NotificationSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    user = request.user
    return Response({
        'user': {
            'username': user.username,
            'teo_coins': user.teo_coins,
            'role': user.role
        },
        'lessons': LessonSerializer(
            Lesson.objects.filter(students=user).select_related('teacher'),
            many=True
        ).data,
        'transactions': TeoCoinTransactionSerializer(
            TeoCoinTransaction.objects.filter(user=user).order_by('-created_at')[:10],
            many=True
        ).data,
        'notifications': NotificationSerializer(
            Notification.objects.filter(user=user).order_by('-created_at')[:5], 
            many=True
        ).data
    })
