"""
URL Configuration for Blockchain Module

This module defines API endpoints for blockchain operations including:
- Wallet management and balance queries
- Token minting and rewards
- Transaction history and status checking
- Reward pool management and monitoring

All endpoints require authentication except for token information.
"""

from django.urls import path, include

from .views import (
    get_wallet_balance, 
    link_wallet, 
    reward_user, 
    get_transaction_history, 
    get_token_info, 
    check_transaction_status,
    get_reward_pool_info,
    refill_reward_pool_matic,
    transfer_with_reward_pool_gas,
    simulate_user_payment_via_pool,
    process_course_payment,
    check_course_payment_prerequisites,
    execute_course_payment,
    process_course_payment_direct,
    confirm_course_payment,
    get_reward_pool_address,
    check_student_approval,
    # Phase 5.3: Staking Management APIs
    get_teacher_staking_info,
    stake_tokens,
    unstake_tokens,
    get_unstaking_schedule,
    withdraw_unstaked_tokens,
    get_staking_statistics
)

urlpatterns = [
    # Wallet management endpoints
    path('balance/', get_wallet_balance, name='wallet-balance'),
    path('link-wallet/', link_wallet, name='link-wallet'),
    
    # Transaction and reward endpoints
    path('reward/', reward_user, name='reward-user'),
    path('transactions/', get_transaction_history, name='transaction-history'),
    path('check-status/', check_transaction_status, name='check-transaction-status'),
    path('transfer-with-pool-gas/', transfer_with_reward_pool_gas, name='transfer-with-pool-gas'),
    path('simulate-payment/', simulate_user_payment_via_pool, name='simulate-user-payment'),
    
    # Course payment endpoints - NEW APPROVE+SPLIT PROCESS
    path('process-course-payment-direct/', process_course_payment_direct, name='process-course-payment-direct'),
    path('reward-pool-address/', get_reward_pool_address, name='get-reward-pool-address'),
    path('check-student-approval/', check_student_approval, name='check-student-approval'),
    
    # Course payment endpoints - LEGACY (DEPRECATED)
    path('confirm-course-payment/', confirm_course_payment, name='confirm-course-payment'),  # Legacy
    path('check-course-payment-prerequisites/', check_course_payment_prerequisites, name='check-course-payment-prerequisites'),
    path('execute-course-payment/', execute_course_payment, name='execute-course-payment'),
    path('process-course-payment/', process_course_payment, name='process-course-payment'),  # Legacy endpoint
    
    # Phase 5.3: Staking Management APIs
    path('staking/info/', get_teacher_staking_info, name='teacher-staking-info'),
    path('staking/stake/', stake_tokens, name='stake-tokens'),
    path('staking/unstake/', unstake_tokens, name='unstake-tokens'),
    path('staking/schedule/', get_unstaking_schedule, name='unstaking-schedule'),
    path('staking/withdraw/', withdraw_unstaked_tokens, name='withdraw-unstaked'),
    path('staking/statistics/', get_staking_statistics, name='staking-statistics'),
    
    # Public token information
    path('token-info/', get_token_info, name='token-info'),
    
    # Reward pool management (admin only)
    path('reward-pool-info/', get_reward_pool_info, name='reward-pool-info'),
    path('refill-reward-pool/', refill_reward_pool_matic, name='refill-reward-pool'),
]