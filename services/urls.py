"""
URL patterns for services app including TEO earning and staking endpoints
"""

from django.urls import path
from . import api_views

urlpatterns = [
    # TEO Earning endpoints
    path('earnings/history/', api_views.earnings_history, name='earnings_history'),
    
    # Staking endpoints
    path('staking/info/', api_views.staking_info, name='staking_info'),
    path('staking/stake/', api_views.stake_tokens, name='stake_tokens'),
    path('staking/unstake/', api_views.unstake_tokens, name='unstake_tokens'),
    path('staking/tiers/', api_views.staking_tiers, name='staking_tiers'),
    path('staking/calculator/', api_views.commission_calculator, name='commission_calculator'),
]
