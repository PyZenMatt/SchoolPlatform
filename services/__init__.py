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
    'TeoEarningService',
    'teo_earning_service',
    'TeoCoinStakingService',
]

def __getattr__(name):
    """Lazy import of services to avoid Django startup issues"""
    if name == 'user_service':
        from .user_service import user_service as _user_service
        return _user_service
    elif name == 'UserService':
        from .user_service import UserService
        return UserService
    elif name == 'teo_earning_service':
        from .teo_earning_service import teo_earning_service as _teo_earning_service
        return _teo_earning_service
    elif name == 'TeoEarningService':
        from .teo_earning_service import TeoEarningService
        return TeoEarningService
    elif name == 'TeoCoinStakingService':
        from .teocoin_staking_service import TeoCoinStakingService
        return TeoCoinStakingService
    elif name == 'BaseService':
        from .base import BaseService
        return BaseService
    elif name == 'TransactionalService':
        from .base import TransactionalService
        return TransactionalService
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
