"""
Standardized API response utilities and error handling
"""
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler
import logging

logger = logging.getLogger(__name__)


class APIResponse:
    """Standardized API response format utility"""
    
    @staticmethod
    def success(data=None, message="Success", status_code=status.HTTP_200_OK):
        """Create a standardized success response"""
        response_data = {
            "success": True,
            "message": message,
            "status_code": status_code
        }
        
        if data is not None:
            response_data["data"] = data
            
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Create a standardized error response"""
        response_data = {
            "success": False,
            "message": message,
            "status_code": status_code
        }
        
        if errors is not None:
            response_data["errors"] = errors
            
        return Response(response_data, status=status_code)
    
    @staticmethod
    def validation_error(errors, message="Validation failed"):
        """Create a standardized validation error response"""
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    @staticmethod
    def not_found(message="Resource not found"):
        """Create a standardized not found response"""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def unauthorized(message="Authentication required"):
        """Create a standardized unauthorized response"""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden(message="Permission denied"):
        """Create a standardized forbidden response"""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def server_error(message="Internal server error"):
        """Create a standardized server error response"""
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def custom_exception_handler(exc, context):
    """Custom exception handler for standardized error responses"""
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the exception
        logger.error(f"API Exception: {exc}", exc_info=True)
        
        # Standardize the error response format
        custom_response_data = {
            'success': False,
            'message': 'An error occurred',
            'status_code': response.status_code,
            'errors': response.data
        }
        
        # Customize message based on status code
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['message'] = 'Bad request'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['message'] = 'Authentication required'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['message'] = 'Permission denied'
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['message'] = 'Resource not found'
        elif response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
            custom_response_data['message'] = 'Validation failed'
        elif response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            custom_response_data['message'] = 'Internal server error'
        
        response.data = custom_response_data
    
    return response


class StandardizedAPIView:
    """Mixin for views to use standardized responses"""
    
    def handle_success(self, data=None, message="Success", status_code=status.HTTP_200_OK):
        """Handle successful operations"""
        return APIResponse.success(data, message, status_code)
    
    def handle_error(self, message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """Handle error cases"""
        return APIResponse.error(message, errors, status_code)
    
    def handle_validation_error(self, serializer):
        """Handle serializer validation errors"""
        return APIResponse.validation_error(serializer.errors)
    
    def handle_not_found(self, resource="Resource"):
        """Handle not found cases"""
        return APIResponse.not_found(f"{resource} not found")
    
    def handle_permission_denied(self):
        """Handle permission denied cases"""
        return APIResponse.forbidden()
        
    def handle_server_error(self, exception=None):
        """Handle server errors"""
        if exception:
            logger.error(f"Server error: {exception}", exc_info=True)
        return APIResponse.server_error()


class PaginatedResponse:
    """Utility for paginated API responses"""
    
    @staticmethod
    def create(data, page_info, message="Data retrieved successfully"):
        """Create a standardized paginated response"""
        response_data = {
            "results": data,
            "pagination": {
                "count": page_info.get('count', 0),
                "next": page_info.get('next'),
                "previous": page_info.get('previous'),
                "page_size": page_info.get('page_size', 20),
                "current_page": page_info.get('current_page', 1),
                "total_pages": page_info.get('total_pages', 1)
            }
        }
        
        return APIResponse.success(
            data=response_data,
            message=message
        )
