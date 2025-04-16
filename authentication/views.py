from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from core.models import User
from rest_framework import generics, permissions, status
from rest_framework_simplejwt.views import TokenObtainPairView
from authentication.serializers import RegisterSerializer, CustomTokenObtainPairSerializer   
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)


class VerifyEmailView(APIView):
    def get(self, request, token):
        try:
            user = User.objects.get(email_verification_token=token)
            user.is_active = True
            user.email_verification_token = ''
            user.save()
            return Response({'status': 'Email verificata con successo'})
        except User.DoesNotExist:
            return Response({'error': 'Token non valido'}, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = []  # Rimuovi qualsiasi restrizione

    def perform_create(self, serializer):
        # Sovrascrivi per gestire la creazione corretta
        user = serializer.save()
        user.set_password(serializer.validated_data['password'])
        user.save()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer