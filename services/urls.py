"""
URL patterns for services app including TEO earning, staking, and TeoCoin discount endpoints
"""

from django.urls import path, include
from . import api_views
from .gas_free_urls import gas_free_urlpatterns

urlpatterns = [
    # TEO Earning endpoints
    path('earnings/history/', api_views.earnings_history, name='earnings_history'),
    
    # Staking endpoints
    path('staking/info/', api_views.staking_info, name='staking_info'),
    path('staking/stake/', api_views.stake_tokens, name='stake_tokens'),
    path('staking/unstake/', api_views.unstake_tokens, name='unstake_tokens'),
    path('staking/tiers/', api_views.staking_tiers, name='staking_tiers'),
    path('staking/calculator/', api_views.commission_calculator, name='commission_calculator'),
    
    # TeoCoin Discount endpoints
    path('discount/', include('api.discount_urls')),
    
    # Gas-Free Operations (Phase 2)
    *gas_free_urlpatterns,
]
