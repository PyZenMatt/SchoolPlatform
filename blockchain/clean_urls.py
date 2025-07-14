"""
Clean URL Configuration for Phase 2 TeoCoin Withdrawal System

Simplified, focused URL patterns for blockchain operations.
This replaces the complex legacy URL configuration.
"""

from django.urls import path
from . import clean_views

app_name = 'blockchain'

urlpatterns = [
    # Core wallet operations
    path('balance/', clean_views.get_token_balance, name='get-balance'),
    path('link-wallet/', clean_views.link_wallet_address, name='link-wallet'),
    
    # Withdrawal operations (Phase 2)
    path('request-withdrawal/', clean_views.request_withdrawal, name='request-withdrawal'),
    path('withdrawal-status/<int:withdrawal_id>/', clean_views.get_withdrawal_status, name='withdrawal-status'),
    path('withdrawal-history/', clean_views.get_withdrawal_history, name='withdrawal-history'),
    
    # Transaction operations
    path('check-transaction/', clean_views.check_transaction_status, name='check-transaction'),
    
    # Public token information
    path('token-info/', clean_views.get_token_info, name='token-info'),
    
    # Admin operations
    path('admin/process-withdrawals/', clean_views.process_pending_withdrawals, name='process-withdrawals'),
]
