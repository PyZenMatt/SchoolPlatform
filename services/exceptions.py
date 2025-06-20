"""
Custom Exceptions for TeoArt School Platform Services

These exceptions provide specific error handling for business logic
operations in the service layer.
"""


class TeoArtServiceException(Exception):
    """
    Base exception for all service-related errors.
    
    Attributes:
        message: Human-readable error message
        code: Error code for frontend handling
        status_code: HTTP status code for API responses
    """
    
    def __init__(self, message: str, code: str = None, status_code: int = 500):
        self.message = message
        self.code = code or self.__class__.__name__
        self.status_code = status_code
        super().__init__(self.message)


class UserNotFoundError(TeoArtServiceException):
    """Raised when a user is not found"""
    
    def __init__(self, user_id: int = None, email: str = None):
        if user_id:
            message = f"User with ID {user_id} not found"
        elif email:
            message = f"User with email {email} not found"
        else:
            message = "User not found"
        
        super().__init__(message, "USER_NOT_FOUND", 404)


class UserAlreadyExistsError(TeoArtServiceException):
    """Raised when trying to create a user that already exists"""
    
    def __init__(self, email: str):
        message = f"User with email {email} already exists"
        super().__init__(message, "USER_ALREADY_EXISTS", 400)


class InvalidUserRoleError(TeoArtServiceException):
    """Raised when an invalid user role is provided"""
    
    def __init__(self, role: str):
        message = f"Invalid user role: {role}"
        super().__init__(message, "INVALID_USER_ROLE", 400)


class UserNotApprovedError(TeoArtServiceException):
    """Raised when a user is not approved for an operation"""
    
    def __init__(self, user_id: int):
        message = f"User {user_id} is not approved for this operation"
        super().__init__(message, "USER_NOT_APPROVED", 403)


class CourseNotFoundError(TeoArtServiceException):
    """Raised when a course is not found"""
    
    def __init__(self, course_id: int):
        message = f"Course with ID {course_id} not found"
        super().__init__(message, "COURSE_NOT_FOUND", 404)


class InsufficientTeoCoinsError(TeoArtServiceException):
    """Raised when user doesn't have enough TeoCoins"""
    
    def __init__(self, required: float, available: float):
        message = f"Insufficient TeoCoins. Required: {required}, Available: {available}"
        super().__init__(message, "INSUFFICIENT_TEOCOINS", 400)


class BlockchainTransactionError(TeoArtServiceException):
    """Raised when a blockchain transaction fails"""
    
    def __init__(self, operation: str, reason: str = None):
        message = f"Blockchain transaction failed: {operation}"
        if reason:
            message += f" - {reason}"
        super().__init__(message, "BLOCKCHAIN_TRANSACTION_ERROR", 500)


class EmailVerificationError(TeoArtServiceException):
    """Raised when email verification fails"""
    
    def __init__(self, email: str):
        message = f"Email verification failed for {email}"
        super().__init__(message, "EMAIL_VERIFICATION_ERROR", 400)
