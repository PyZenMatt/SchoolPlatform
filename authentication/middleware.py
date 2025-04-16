from django.utils.deprecation import MiddlewareMixin

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