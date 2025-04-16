from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    data = {
        'user': {
            'username': request.user.username,
            'role': request.user.role,
            'teo_coins': request.user.teo_coins
        },
        'notifications': NotificationSerializer(
            Notification.objects.filter(user=request.user).order_by('-created_at')[:5],
            many=True
        ).data,
        'recent_transactions': TeoCoinTransactionSerializer(
            TeoCoinTransaction.objects.filter(user=request.user).order_by('-created_at')[:5],
            many=True
        ).data
    }
    return Response(data)