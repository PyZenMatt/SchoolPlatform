from rest_framework import status
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework_simplejwt.views import TokenObtainPairView
from authentication.serializers import RegisterSerializer, CustomTokenObtainPairSerializer   
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.generic import CreateView
from django.urls import reverse_lazy
from core.models import User
from .forms import CustomUserCreationForm
from django.contrib.auth import get_user_model
User = get_user_model()

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

class RegisterView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'registration/register.html'  # Definito come attributo della classe
    success_url = reverse_lazy('login')  # URL di redirect dopo registrazione
    
    # Aggiungi la gestione del parametro role
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role'] = self.request.GET.get('role', 'student')
        return context

    def form_valid(self, form):
        role = self.request.GET.get('role', 'student')
        form.instance.role = role
        return super().form_valid(form)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {"error": "Invalid token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data["refresh_token"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "Logout effettuato con successo"})
    except Exception as e:
        return Response({"error": str(e)}, status=400)