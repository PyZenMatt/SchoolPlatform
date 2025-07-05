"""
Teacher Escrow API Views

API endpoints for teachers to manage TeoCoin escrow decisions.
Teachers can view pending escrows and accept/reject TeoCoin discounts.
"""

from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rewards.models import TeoCoinEscrow
from services.escrow_service import escrow_service


class TeacherEscrowListView(APIView):
    """
    GET /api/teacher/escrows/
    
    List all escrows for the authenticated teacher with optional status filtering.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of teacher's escrows"""
        try:
            # Check if user is a teacher (has published courses)
            teacher = request.user
            if not hasattr(teacher, 'courses_taught') or not teacher.courses_taught.exists():
                return Response({
                    'success': False,
                    'error': 'Only teachers can access escrow data'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Get status filter from query params
            status_filter = request.GET.get('status', None)
            
            # Get escrows
            escrows = escrow_service.get_teacher_escrows(teacher, status_filter)
            
            # Serialize escrow data
            escrow_list = []
            for escrow in escrows:
                escrow_data = {
                    'id': escrow.id,
                    'student_name': escrow.student.get_full_name() or escrow.student.username,
                    'course_title': escrow.course.title,
                    'course_id': escrow.course.id,
                    'teocoin_amount': str(escrow.teocoin_amount),
                    'discount_percentage': str(escrow.discount_percentage),
                    'discount_euro_amount': str(escrow.discount_euro_amount),
                    'original_course_price': str(escrow.original_course_price),
                    'standard_euro_commission': str(escrow.standard_euro_commission),
                    'reduced_euro_commission': str(escrow.reduced_euro_commission),
                    'status': escrow.status,
                    'created_at': escrow.created_at.isoformat(),
                    'expires_at': escrow.expires_at.isoformat() if escrow.status == 'pending' else None,
                    'time_remaining': str(escrow.time_remaining) if escrow.time_remaining else None,
                    'is_expired': escrow.is_expired,
                    'teacher_decision_at': escrow.teacher_decision_at.isoformat() if escrow.teacher_decision_at else None,
                    'teacher_decision_notes': escrow.teacher_decision_notes
                }
                escrow_list.append(escrow_data)
            
            # Get statistics
            stats = escrow_service.get_escrow_statistics(teacher)
            
            return Response({
                'success': True,
                'escrows': escrow_list,
                'statistics': stats,
                'total_count': len(escrow_list)
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to retrieve escrows: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherEscrowDetailView(APIView):
    """
    GET /api/teacher/escrows/{id}/
    
    Get detailed information about a specific escrow.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, escrow_id):
        """Get detailed escrow information"""
        try:
            escrow = get_object_or_404(
                TeoCoinEscrow,
                id=escrow_id,
                teacher=request.user
            )
            
            # Calculate potential earnings scenarios
            accept_scenario = {
                'euro_commission': str(escrow.reduced_euro_commission),
                'teocoin_amount': str(escrow.teocoin_amount),
                'total_value_estimate': str(escrow.reduced_euro_commission + escrow.teocoin_amount)  # Assuming 1 TEO = 1 EUR for display
            }
            
            reject_scenario = {
                'euro_commission': str(escrow.standard_euro_commission),
                'teocoin_amount': '0',
                'total_value_estimate': str(escrow.standard_euro_commission)
            }
            
            escrow_detail = {
                'id': escrow.id,
                'student': {
                    'name': escrow.student.get_full_name() or escrow.student.username,
                    'username': escrow.student.username,
                    'wallet_address': getattr(escrow.student, 'wallet_address', None)
                },
                'course': {
                    'id': escrow.course.id,
                    'title': escrow.course.title,
                    'original_price': str(escrow.original_course_price)
                },
                'discount': {
                    'percentage': str(escrow.discount_percentage),
                    'euro_amount': str(escrow.discount_euro_amount),
                    'teocoin_amount': str(escrow.teocoin_amount)
                },
                'scenarios': {
                    'accept': accept_scenario,
                    'reject': reject_scenario
                },
                'status': escrow.status,
                'timing': {
                    'created_at': escrow.created_at.isoformat(),
                    'expires_at': escrow.expires_at.isoformat(),
                    'time_remaining': str(escrow.time_remaining) if escrow.time_remaining else None,
                    'is_expired': escrow.is_expired
                },
                'blockchain': {
                    'escrow_tx_hash': escrow.escrow_tx_hash,
                    'release_tx_hash': escrow.release_tx_hash
                }
            }
            
            return Response({
                'success': True,
                'escrow': escrow_detail
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to retrieve escrow details: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherEscrowAcceptView(APIView):
    """
    POST /api/teacher/escrows/{id}/accept/
    
    Teacher accepts TeoCoin escrow - releases TeoCoin to teacher wallet.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, escrow_id):
        """Accept TeoCoin escrow"""
        try:
            result = escrow_service.accept_escrow(escrow_id, request.user)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'TeoCoin escrow accepted successfully',
                    'data': result
                })
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Escrow acceptance failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherEscrowRejectView(APIView):
    """
    POST /api/teacher/escrows/{id}/reject/
    
    Teacher rejects TeoCoin escrow - gets standard EUR commission instead.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, escrow_id):
        """Reject TeoCoin escrow"""
        try:
            # Get optional rejection reason
            reason = request.data.get('reason', None)
            
            result = escrow_service.reject_escrow(escrow_id, request.user, reason)
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': 'TeoCoin escrow rejected successfully',
                    'data': result
                })
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Escrow rejection failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherEscrowStatsView(APIView):
    """
    GET /api/teacher/escrow-stats/
    
    Get comprehensive escrow statistics for teacher dashboard.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get teacher escrow statistics"""
        try:
            teacher = request.user
            stats = escrow_service.get_escrow_statistics(teacher)
            
            # Add additional useful metrics
            recent_escrows = escrow_service.get_teacher_escrows(teacher).filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            )
            
            monthly_stats = {
                'recent_escrows_count': recent_escrows.count(),
                'recent_accepted_count': recent_escrows.filter(status='accepted').count(),
                'recent_rejected_count': recent_escrows.filter(status='rejected').count(),
                'recent_pending_count': recent_escrows.filter(status='pending').count()
            }
            
            return Response({
                'success': True,
                'statistics': {
                    **stats,
                    'monthly': monthly_stats
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Failed to retrieve statistics: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
