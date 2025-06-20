"""
Services Package for TeoArt School Platform

This package contains all business logic services that handle
the core operations of the platform, separated from views.

Services:
- UserService: User management and authentication
- CourseService: Course management and enrollment
- BlockchainService: Blockchain and TeoCoin operations
- NotificationService: Email and in-app notifications
"""

from .base import BaseService, TransactionalService
from .user_service import UserService, user_service
from .blockchain_service import BlockchainService, blockchain_service
from .exceptions import (
    TeoArtServiceException,
    InsufficientTeoCoinsError,
    CourseNotFoundError,
    UserNotFoundError,
    WalletNotFoundError,
    InvalidWalletAddressError,
    TokenTransferError,
    MintingError,
    InvalidAmountError,
    BlockchainTransactionError,
)

__all__ = [
    'BaseService',
    'TransactionalService',
    'UserService',
    'user_service',
    'BlockchainService',
    'blockchain_service',
    'TeoArtServiceException',
    'InsufficientTeoCoinsError', 
    'CourseNotFoundError',
    'UserNotFoundError',
    'WalletNotFoundError',
    'InvalidWalletAddressError',
    'TokenTransferError',
    'MintingError',
    'InvalidAmountError',
    'BlockchainTransactionError',
]
