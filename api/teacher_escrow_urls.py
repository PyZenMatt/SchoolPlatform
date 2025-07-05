"""
URL configuration for teacher escrow management endpoints.
"""

from django.urls import path
from api.teacher_escrow_views import (
    TeacherEscrowListView,
    TeacherEscrowDetailView,
    TeacherEscrowAcceptView,
    TeacherEscrowRejectView,
    TeacherEscrowStatsView
)

app_name = 'teacher_escrow_api'

urlpatterns = [
    # Escrow management endpoints
    path('escrows/', TeacherEscrowListView.as_view(), name='escrow-list'),
    path('escrows/<int:escrow_id>/', TeacherEscrowDetailView.as_view(), name='escrow-detail'),
    path('escrows/<int:escrow_id>/accept/', TeacherEscrowAcceptView.as_view(), name='escrow-accept'),
    path('escrows/<int:escrow_id>/reject/', TeacherEscrowRejectView.as_view(), name='escrow-reject'),
    path('escrows/stats/', TeacherEscrowStatsView.as_view(), name='escrow-stats-alt'),  # Alternative endpoint
    path('escrow-stats/', TeacherEscrowStatsView.as_view(), name='escrow-stats'),
]
