"""
URL patterns for TeoCoin Discount System API

Provides REST endpoints for the gas-free discount system
"""

from django.urls import path
from .discount_views import (
    SignatureDataView,
    CreateDiscountRequestView, 
    ApproveDiscountRequestView,
    DeclineDiscountRequestView,
    DiscountRequestDetailView,
    StudentRequestsView,
    TeacherRequestsView,
    DiscountStatsView,
    CalculateDiscountCostView,
    SystemStatusView
)

app_name = 'discount_api'

urlpatterns = [
    # Signature and request creation
    path('signature-data/', SignatureDataView.as_view(), name='signature_data'),
    path('create/', CreateDiscountRequestView.as_view(), name='create_request'),
    
    # Request management
    path('approve/', ApproveDiscountRequestView.as_view(), name='approve_request'),
    path('decline/', DeclineDiscountRequestView.as_view(), name='decline_request'),
    
    # Request details and listings
    path('request/<int:request_id>/', DiscountRequestDetailView.as_view(), name='request_detail'),
    path('student/<str:student_address>/', StudentRequestsView.as_view(), name='student_requests'),
    path('teacher/<str:teacher_address>/', TeacherRequestsView.as_view(), name='teacher_requests'),
    
    # Utilities and stats
    path('calculate/', CalculateDiscountCostView.as_view(), name='calculate_cost'),
    path('stats/', DiscountStatsView.as_view(), name='stats'),
    path('status/', SystemStatusView.as_view(), name='system_status'),
]
