from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings
import datetime

class AutoJWTFromSessionMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if request.user.is_authenticated:
            # Genera/aggiorna token JWT
            token = AccessToken.for_user(request.user)
            
            # Imposta in session
            request.session['jwt_token'] = str(token)
            
            # Imposta cookie HTTP-only
            response.set_cookie(
                'jwt_token',
                str(token),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                expires=datetime.datetime.now() + datetime.timedelta(minutes=30)
            )
        return response