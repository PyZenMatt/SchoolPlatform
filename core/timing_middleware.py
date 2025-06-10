import time
import logging

logger = logging.getLogger('api_performance')

class APITimingMiddleware:
    """Middleware per monitorare i tempi di risposta delle API"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        # Log solo per API calls
        if request.path.startswith('/api/'):
            logger.info(f"API {request.method} {request.path} - {duration:.3f}s - {response.status_code}")
            
            # Log warning per chiamate lente (>1 secondo)
            if duration > 1.0:
                logger.warning(f"SLOW API {request.method} {request.path} - {duration:.3f}s")
                
        return response
