from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect

class AuthSecurityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Blocca tentativi di brute force
        if request.path == '/auth/login/':
            ip = request.META.get('REMOTE_ADDR')
            if self.check_brute_force(ip):
                return HttpResponseForbidden("Troppi tentativi falliti")
    
    def check_brute_force(self, ip):
        # Logica di controllo
        return False


class AuthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Liste di path pubblici
        public_paths = [
            '/login/', 
            '/register/',
            '/password-reset/'
        ]
        
        if not request.user.is_authenticated and not any(request.path.startswith(p) for p in public_paths):
            return redirect(f'/login/?next={request.path}')
        
        return self.get_response(request)