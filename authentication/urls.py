from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenBlacklistView
)
from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    LogoutView
)

urlpatterns = [
    # Autenticazione JWT
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', TokenBlacklistView.as_view(), name='logout'),
    
    # Registrazione utente
    path('register/', RegisterView.as_view(), name='register'),
    
    # Logout personalizzato (se necessario)
    path('custom-logout/', LogoutView.as_view(), name='custom_logout'),
]