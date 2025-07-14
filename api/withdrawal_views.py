"""
TeoCoin Withdrawal API Views - Phase 1 Implementation
Provides REST API endpoints for withdrawal functionality following GitHub best practices

This module implements the withdrawal API endpoints as outlined in the
TeoCoin MetaMask Integration specification.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from decimal import Decimal
import logging

from services.teocoin_withdrawal_service import teocoin_withdrawal_service
from services.hybrid_teocoin_service import hybrid_teocoin_service

logger = logging.getLogger(__name__)


class CreateWithdrawalView(APIView):
    """Create a new withdrawal request"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Create withdrawal request
        
        Body:
        {
            "amount": "50.00",
            "metamask_address": "0x742d35Cc6475C1C2C6b2FF4a4F5D6f865c123456"
        }
        """
        try:
            amount = request.data.get('amount')
            metamask_address = request.data.get('metamask_address')
            
            # Validation
            if not amount:
                return Response({
                    'success': False,
                    'error': 'Amount is required',
                    'error_code': 'MISSING_AMOUNT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not metamask_address:
                return Response({
                    'success': False,
                    'error': 'MetaMask address is required',
                    'error_code': 'MISSING_ADDRESS'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                amount_decimal = Decimal(str(amount))
                if amount_decimal <= 0:
                    return Response({
                        'success': False,
                        'error': 'Amount must be greater than 0',
                        'error_code': 'INVALID_AMOUNT'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Invalid amount format',
                    'error_code': 'INVALID_AMOUNT_FORMAT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get client IP and user agent for security
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Create withdrawal request
            result = teocoin_withdrawal_service.create_withdrawal_request(
                user=request.user,
                amount=amount_decimal,
                wallet_address=metamask_address,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'withdrawal_id': result['withdrawal_id'],
                    'amount': result['amount'],
                    'metamask_address': result['metamask_address'],
                    'status': result['status'],
                    'estimated_processing_time': result['estimated_processing_time'],
                    'daily_withdrawal_count': result['daily_withdrawal_count'],
                    'message': result['message']
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'error': result['error'],
                    'error_code': result.get('error_code', 'UNKNOWN_ERROR')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error creating withdrawal for user {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        else:
            return request.META.get('REMOTE_ADDR')


class WithdrawalStatusView(APIView):
    """Get status of a withdrawal request"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, withdrawal_id):
        """Get withdrawal status by ID"""
        try:
            result = teocoin_withdrawal_service.get_withdrawal_status(
                withdrawal_id=withdrawal_id,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'withdrawal': result['withdrawal']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['error'],
                    'error_code': result.get('error_code', 'UNKNOWN_ERROR')
                }, status=status.HTTP_404_NOT_FOUND)
                
        except Exception as e:
            logger.error(f"Error getting withdrawal status {withdrawal_id}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserWithdrawalHistoryView(APIView):
    """Get user's withdrawal history"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's withdrawal history"""
        try:
            limit = int(request.query_params.get('limit', 20))
            limit = min(limit, 100)  # Cap at 100
            
            status_filter = request.query_params.get('status')
            
            withdrawals = teocoin_withdrawal_service.get_user_withdrawal_history(
                user=request.user,
                limit=limit,
                status=status_filter
            )
            
            return Response({
                'success': True,
                'withdrawals': withdrawals,
                'count': len(withdrawals)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting withdrawal history for {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelWithdrawalView(APIView):
    """Cancel a pending withdrawal request"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, withdrawal_id):
        """Cancel withdrawal request"""
        try:
            result = teocoin_withdrawal_service.cancel_withdrawal_request(
                withdrawal_id=withdrawal_id,
                user=request.user
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'message': result['message'],
                    'amount_returned': result['amount_returned']
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result['error'],
                    'error_code': result.get('error_code', 'UNKNOWN_ERROR')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Error cancelling withdrawal {withdrawal_id}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserTeoCoinBalanceView(APIView):
    """Get user's TeoCoin balance"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current user's TeoCoin balance"""
        try:
            balance_data = hybrid_teocoin_service.get_user_balance(request.user)
            
            return Response({
                'success': True,
                'balance': {
                    'available': str(balance_data['available_balance']),
                    'staked': str(balance_data['staked_balance']),
                    'pending_withdrawal': str(balance_data['pending_withdrawal']),
                    'total': str(balance_data['total_balance'])
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting balance for {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawalLimitsView(APIView):
    """Get withdrawal limits and requirements"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get withdrawal limits for current user"""
        try:
            from datetime import date
            from blockchain.models import TeoCoinWithdrawalRequest
            
            # Get daily usage
            today = date.today()
            daily_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
                user=request.user,
                created_at__date=today
            )
            
            daily_count = daily_withdrawals.count()
            daily_amount = sum(w.amount for w in daily_withdrawals)
            
            # Get limits from service
            limits = {
                'min_amount': str(teocoin_withdrawal_service.MIN_WITHDRAWAL_AMOUNT),
                'max_amount': str(teocoin_withdrawal_service.MAX_WITHDRAWAL_AMOUNT),
                'max_daily_withdrawals': teocoin_withdrawal_service.MAX_DAILY_WITHDRAWALS,
                'max_daily_amount': str(teocoin_withdrawal_service.MAX_DAILY_AMOUNT),
                'daily_usage': {
                    'withdrawals_used': daily_count,
                    'amount_used': str(daily_amount),
                    'withdrawals_remaining': max(0, teocoin_withdrawal_service.MAX_DAILY_WITHDRAWALS - daily_count),
                    'amount_remaining': str(max(0, teocoin_withdrawal_service.MAX_DAILY_AMOUNT - daily_amount))
                }
            }
            
            return Response({
                'success': True,
                'limits': limits
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting withdrawal limits for {request.user.email}: {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========== ADMIN VIEWS ==========

class AdminPendingWithdrawalsView(APIView):
    """Admin view for pending withdrawals"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get all pending withdrawal requests (admin only)"""
        try:
            limit = int(request.query_params.get('limit', 50))
            limit = min(limit, 200)  # Cap at 200
            
            pending_withdrawals = teocoin_withdrawal_service.get_pending_withdrawals(limit)
            
            return Response({
                'success': True,
                'pending_withdrawals': pending_withdrawals,
                'count': len(pending_withdrawals)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting pending withdrawals (admin): {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminWithdrawalStatsView(APIView):
    """Admin view for withdrawal statistics"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        """Get withdrawal statistics (admin only)"""
        try:
            days = int(request.query_params.get('days', 30))
            days = min(days, 365)  # Cap at 1 year
            
            stats = teocoin_withdrawal_service.get_withdrawal_statistics(days)
            
            return Response({
                'success': True,
                'statistics': stats
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting withdrawal statistics (admin): {e}")
            return Response({
                'success': False,
                'error': 'Internal server error',
                'error_code': 'INTERNAL_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
