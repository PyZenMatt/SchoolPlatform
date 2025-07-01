"""
Cached Payment Service for Ultra-Fast Payment Processing
Optimized for investor demo performance with Redis caching
"""

from django.core.cache import cache, caches
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from functools import wraps
import hashlib
import json
import time
from typing import Dict, Any, Optional
from decimal import Decimal

from services.payment_service import payment_service as base_payment_service
from courses.models import Course, CourseEnrollment
from django.contrib.auth import get_user_model

User = get_user_model()

# ⚡ Cache instances
default_cache = cache  # Main cache
payment_cache = caches['payments']  # Fast payment cache


def payment_cache_key(func_name: str, *args, **kwargs) -> str:
    """Generate cache key for payment operations"""
    # Create deterministic key from function name and arguments
    key_data = {
        'func': func_name,
        'args': args,
        'kwargs': {k: v for k, v in kwargs.items() if k not in ['request']}
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return f"payment_{func_name}_{key_hash}"


def cached_payment_operation(timeout: int = 180):
    """Decorator for caching payment operations"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = payment_cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache first
            cached_result = payment_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            payment_cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator


class CachedPaymentService:
    """High-performance payment service with Redis caching"""
    
    def __init__(self):
        self.base_service = base_payment_service
    
    @cached_payment_operation(timeout=300)  # 5 minutes
    def get_payment_summary_cached(self, user_id: int, course_id: int) -> Dict[str, Any]:
        """
        ⚡ Ultra-fast payment summary with caching
        """
        try:
            return self.base_service.get_payment_summary(user_id, course_id)
        except Exception as e:
            # Return error format that matches API expectations
            return {
                'error': str(e),
                'already_enrolled': False,
                'pricing_options': None,
                'user_teocoin_balance': 0,
                'can_pay_with_teocoin': False,
                'wallet_connected': False,
                'course_approved': False
            }
    
    @cached_payment_operation(timeout=60)  # 1 minute - shorter for course data
    def get_course_pricing_cached(self, course_id: int) -> Dict[str, Any]:
        """
        ⚡ Ultra-fast course pricing with caching
        """
        try:
            course = Course.objects.select_related().get(id=course_id)
            return {
                'id': course.id,
                'title': course.title,
                'price_eur': float(course.price_eur) if course.price_eur else None,
                'price_teocoin': float(course.get_teocoin_price()) if hasattr(course, 'get_teocoin_price') else None,
                'teocoin_reward': float(course.teocoin_reward) if course.teocoin_reward else 0,
                'is_approved': course.is_approved,
                'teacher_id': course.teacher.id,
                'teacher_username': course.teacher.username
            }
        except Course.DoesNotExist:
            return {'error': 'Course not found'}
    
    def create_payment_intent_optimized(self, user_id: int, course_id: int, amount_eur: Decimal) -> Dict[str, Any]:
        """
        ⚡ Optimized payment intent creation (no caching for security)
        """
        # Get cached course data first
        course_data = self.get_course_pricing_cached(course_id)
        if 'error' in course_data:
            return {'success': False, 'error': course_data['error']}
        
        # Create payment intent using base service
        return self.base_service.create_fiat_payment_intent(user_id, course_id, amount_eur)
    
    def process_payment_optimized(self, payment_intent_id: str, course_id: int, user_id: int) -> Dict[str, Any]:
        """
        ⚡ Optimized payment processing with cache invalidation
        """
        result = self.base_service.process_successful_fiat_payment(
            payment_intent_id, course_id, user_id
        )
        
        # Invalidate relevant caches after successful payment
        if result.get('success'):
            self._invalidate_payment_caches(user_id, course_id)
        
        return result
    
    def _invalidate_payment_caches(self, user_id: int, course_id: int):
        """Invalidate payment-related caches after successful operations"""
        try:
            # Generate keys that might be affected
            summary_key = payment_cache_key('get_payment_summary_cached', user_id, course_id)
            course_key = payment_cache_key('get_course_pricing_cached', course_id)
            
            # Delete from cache
            payment_cache.delete_many([summary_key, course_key])
            
            # Also clear any enrollment-related cache
            pattern = f"payment_*_user_{user_id}_*"
            payment_cache.delete_pattern(pattern)
            
        except Exception as e:
            # Don't fail the operation if cache invalidation fails
            print(f"Cache invalidation warning: {e}")


# Global cached service instance
cached_payment_service = CachedPaymentService()


# ⚡ Additional optimization decorators
def payment_rate_limit(max_requests: int = 10, window: int = 60):
    """Rate limiting for payment endpoints"""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return func(request, *args, **kwargs)
            
            # Rate limit key
            rate_key = f"payment_rate_{request.user.id}_{func.__name__}"
            current_requests = payment_cache.get(rate_key, 0)
            
            if current_requests >= max_requests:
                from rest_framework.response import Response
                from rest_framework import status
                return Response({
                    'success': False,
                    'error': 'Too many payment requests. Please wait a moment.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Increment counter
            payment_cache.set(rate_key, current_requests + 1, window)
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def preload_course_data(course_ids: list):
    """
    ⚡ Preload course data into cache for faster access
    Call this during app startup or when courses are updated
    """
    for course_id in course_ids:
        try:
            cached_payment_service.get_course_pricing_cached(course_id)
        except:
            pass  # Skip errors during preloading


# ⚡ Cache warming function for better performance
def warm_payment_caches():
    """Warm up payment caches with frequently accessed data"""
    try:
        # Get active courses
        active_courses = Course.objects.filter(is_approved=True).values_list('id', flat=True)[:20]
        
        # Preload course pricing data
        preload_course_data(list(active_courses))
        
        print(f"✅ Payment cache warmed with {len(active_courses)} courses")
    except Exception as e:
        print(f"⚠️ Cache warming failed: {e}")
