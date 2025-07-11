"""
Gas-Free TeoCoin API URLs
URL patterns for gas-free discount and staking operations.
"""
from django.urls import path
from . import gas_free_api_views as views

# Gas-Free API URL patterns
gas_free_urlpatterns = [
    # Permit + Discount Operations (New - solves student gas problem)
    path('gas-free/permit-discount/signatures/', 
         views.create_permit_discount_signatures, 
         name='gas_free_permit_discount_signatures'),
    
    path('gas-free/permit-discount/execute/', 
         views.execute_permit_discount, 
         name='gas_free_permit_discount_execute'),
    
    # Discount Operations (Legacy)
    path('gas-free/discount/signature/', 
         views.create_discount_signature, 
         name='gas_free_discount_signature'),
    
    path('gas-free/discount/execute/', 
         views.execute_discount_request, 
         name='gas_free_discount_execute'),
    
    path('gas-free/discount/status/<int:request_id>/', 
         views.get_discount_request_status, 
         name='gas_free_discount_status'),
    
    # Staking Operations
    path('gas-free/staking/stake-signature/', 
         views.create_stake_signature, 
         name='gas_free_stake_signature'),
    
    path('gas-free/staking/unstake-signature/', 
         views.create_unstake_signature, 
         name='gas_free_unstake_signature'),
    
    path('gas-free/staking/stake/', 
         views.execute_stake_request, 
         name='gas_free_stake_execute'),
    
    path('gas-free/staking/unstake/', 
         views.execute_unstake_request, 
         name='gas_free_unstake_execute'),
    
    path('gas-free/staking/info/<str:user_address>/', 
         views.get_user_stake_info, 
         name='gas_free_stake_info'),
    
    # Gas Cost Estimates
    path('gas-free/gas-estimates/', 
         views.estimate_gas_costs, 
         name='gas_free_gas_estimates'),
    
    # User Information
    path('gas-free/user-stats/<str:user_address>/', 
         views.get_user_stats, 
         name='gas_free_user_stats'),
]
