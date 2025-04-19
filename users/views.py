from django.shortcuts import render
from users.models import User
from .serializers import RegisterSerializer
from rest_framework import generics
from rest_framework.permissions import AllowAny



# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny)
    serializer_class = RegisterSerializer