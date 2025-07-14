"""
URL Configuration for Frontend TeoCoin Withdrawal System
"""

from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    # Main withdrawal page
    path('withdrawal/', views.teocoin_withdrawal_page, name='withdrawal_page'),
    
    # Demo page for comprehensive testing
    path('withdrawal/demo/', views.withdrawal_demo_page, name='withdrawal_demo'),
    
    # 🎯 NEW: Integrated dashboard with TeoCoin widget
    path('dashboard/', views.integrated_dashboard, name='integrated_dashboard'),
    
    # Widget demo
    path('widget/demo/', views.teocoin_widget_demo, name='widget_demo'),
    
    # API endpoints for frontend
    path('api/balance/', views.get_user_db_balance, name='get_balance'),
    path('api/demo/add-balance/', views.demo_add_balance, name='demo_add_balance'),
]
