# Health Check Endpoint for SchoolPlatform
# ========================================

from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache
import redis
import logging

logger = logging.getLogger(__name__)

class HealthCheckView(View):
    """
    Health check endpoint for monitoring and load balancers
    """
    
    def get(self, request):
        """
        Comprehensive health check including database, cache, and services
        """
        health_status = {
            'status': 'healthy',
            'checks': {}
        }
        
        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_status['checks']['database'] = 'healthy'
        except Exception as e:
            health_status['checks']['database'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
            logger.error(f"Database health check failed: {e}")
        
        # Redis cache check
        try:
            cache.set('health_check', 'ok', 30)
            cache_value = cache.get('health_check')
            if cache_value == 'ok':
                health_status['checks']['cache'] = 'healthy'
            else:
                health_status['checks']['cache'] = 'unhealthy: cache value mismatch'
                health_status['status'] = 'unhealthy'
        except Exception as e:
            health_status['checks']['cache'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'unhealthy'
            logger.error(f"Cache health check failed: {e}")
        
        # Celery check (optional - check if broker is accessible)
        try:
            from celery import current_app
            inspector = current_app.control.inspect()
            # Try to get worker stats with timeout
            stats = inspector.stats()
            if stats:
                health_status['checks']['celery'] = 'healthy'
            else:
                health_status['checks']['celery'] = 'no workers available'
        except Exception as e:
            health_status['checks']['celery'] = f'unhealthy: {str(e)}'
            logger.warning(f"Celery health check failed: {e}")
            # Don't mark overall status as unhealthy for Celery issues
        
        # Return appropriate HTTP status code
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return JsonResponse(health_status, status=status_code)
