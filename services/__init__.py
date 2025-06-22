"""
Services Package for TeoArt School Platform

This package contains all business logic services that handle
the core operations of the platform, separated from views.

Services:
- UserService: User management and authentication
- CourseService: Course management and enrollment
- BlockchainService: Blockchain and TeoCoin operations
- NotificationService: Email and in-app notifications
- TeoCoinStakingService: Staking system operations
- TeoEarningService: TEO earning tracking
"""

# Default app config
default_app_config = 'services.apps.ServicesConfig'

# Services will be imported dynamically to avoid Django startup issues
__all__ = [
    'BaseService',
    'TransactionalService',
    'UserService',
    'user_service',
    'BlockchainService',
    'blockchain_service',
    'CourseService',
    'course_service',
    'NotificationService',
    'notification_service',
    'TeoCoinStakingService',
    'TeoEarningService',
    'teo_earning_service',
    'payment_service',
    'reward_service'
]
