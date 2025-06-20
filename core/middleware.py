"""
Core middleware for the TeoArt School Platform.

This module contains custom middleware for JWT handling, API performance monitoring,
and access control for different user roles.
"""
import time
import datetime
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from rest_framework_simplejwt.tokens import AccessToken
from django.conf import settings

# Loggers
auth_logger = logging.getLogger('authentication')
api_logger = logging.getLogger('api_performance')


class AutoJWTFromSessionMiddleware(MiddlewareMixin):
    """
    Middleware for automatic JWT token generation and management.
    
    This middleware automatically generates JWT tokens for authenticated users
    and sets them in both session storage and HTTP-only cookies for secure access.
    """
    def process_response(self, request, response):
        """
        Generate and set JWT tokens for authenticated users.
        
        Args:
            request: The HTTP request object
            response: The HTTP response object
            
        Returns:
            Modified response with JWT tokens set in session and cookies
        """
        if request.user.is_authenticated:
            try:
                # Generate JWT token for the authenticated user
                token = AccessToken.for_user(request.user)
                
                # Store token in session for server-side access
                request.session['jwt_token'] = str(token)
                
                # Set secure HTTP-only cookie for client-side access
                response.set_cookie(
                    'jwt_token',
                    str(token),
                    httponly=True,
                    secure=not settings.DEBUG,  # Secure only in production
                    samesite='Lax',
                    expires=datetime.datetime.now() + datetime.timedelta(minutes=30)
                )
                
                auth_logger.debug(f"JWT token generated for user {request.user.username}")
                
            except Exception as e:
                auth_logger.error(f"Failed to generate JWT token for user {request.user.username}: {e}")
                
        return response
class DashboardAccessMiddleware:
    """
    Middleware for role-based access control to dashboard areas.
    
    This middleware ensures that users can only access dashboard sections
    appropriate for their role (student, teacher, admin).
    """
    
    def __init__(self, get_response):
        """Initialize the middleware with the next middleware in the chain."""
        self.get_response = get_response

    def __call__(self, request):
        """
        Process the request and enforce role-based access control.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HTTP response or redirect/forbidden response if access denied
        """
        response = self.get_response(request)
        
        # Check dashboard access permissions
        if request.path.startswith('/dashboard/'):
            if not request.user.is_authenticated:
                auth_logger.warning(f"Unauthenticated access attempt to {request.path}")
                return redirect(f'/login/?next={request.path}')
            
            # Role-based access control
            if 'student' in request.path and request.user.role != 'student':
                auth_logger.warning(f"Unauthorized access attempt by {request.user.username} to student area")
                return HttpResponseForbidden("Accesso negato: area studenti")
                
            if 'teacher' in request.path and request.user.role != 'teacher':
                auth_logger.warning(f"Unauthorized access attempt by {request.user.username} to teacher area")
                return HttpResponseForbidden("Accesso negato: area docenti")
                
            if 'admin' in request.path and request.user.role != 'admin':
                auth_logger.warning(f"Unauthorized access attempt by {request.user.username} to admin area")
                return HttpResponseForbidden("Accesso negato: area amministratori")

        return response


class APITimingMiddleware:
    """
    Middleware for monitoring API response times and performance.
    
    This middleware logs the execution time of API calls and identifies
    slow endpoints that may need optimization.
    """
    
    def __init__(self, get_response):
        """Initialize the middleware with the next middleware in the chain."""
        self.get_response = get_response

    def __call__(self, request):
        """
        Monitor API call timing and log performance metrics.
        
        Args:
            request: The HTTP request object
            
        Returns:
            HTTP response with timing information logged
        """
        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time
        
        # Log performance metrics for API calls only
        if request.path.startswith('/api/'):
            api_logger.info(
                f"API {request.method} {request.path} - "
                f"{duration:.3f}s - {response.status_code}"
            )
            
            # Log warning for slow API calls (>1 second)
            if duration > 1.0:
                api_logger.warning(
                    f"SLOW API {request.method} {request.path} - "
                    f"{duration:.3f}s - Consider optimization"
                )
                
            # Log error for very slow API calls (>3 seconds)
            if duration > 3.0:
                api_logger.error(
                    f"VERY SLOW API {request.method} {request.path} - "
                    f"{duration:.3f}s - Immediate attention required"
                )
                
        return response