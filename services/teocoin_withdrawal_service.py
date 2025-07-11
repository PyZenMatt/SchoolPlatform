"""
TeoCoin Withdrawal Service (DB-based)
Handles withdrawal requests without blockchain integration yet.
This creates the infrastructure for future blockchain withdrawals.
"""

from decimal import Decimal
from typing import Dict, Optional, List, Any, Union
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import logging

from services.db_teocoin_service import db_teocoin_service
from blockchain.models import TeoCoinWithdrawalRequest, DBTeoCoinBalance

User = get_user_model()
logger = logging.getLogger(__name__)


class TeoCoinWithdrawalService:
    """
    Handle TeoCoin withdrawal requests (DB-based)
    Creates withdrawal requests that can be processed later with blockchain integration
    """
    
    def __init__(self):
        self.db_service = db_teocoin_service
    
    @transaction.atomic
    def create_withdrawal_request(self, user, amount: Union[Decimal, float, str], 
                                 wallet_address: str) -> Dict[str, Any]:
        """
        Create withdrawal request - moves TEO from available to pending_withdrawal
        
        Args:
            user: User requesting withdrawal
            amount: Amount to withdraw
            wallet_address: User's MetaMask wallet address
            
        Returns:
            Dict with success status and withdrawal details
        """
        try:
            amount_decimal = Decimal(str(amount))
            
            # Validate amount
            if amount_decimal <= 0:
                return {
                    'success': False,
                    'error': 'Amount must be greater than 0'
                }
            
            # Validate wallet address
            if not wallet_address or len(wallet_address) != 42 or not wallet_address.startswith('0x'):
                return {
                    'success': False,
                    'error': 'Invalid wallet address format'
                }
            
            # Check user balance
            balance_data = self.db_service.get_user_balance(user)
            
            if balance_data['available_balance'] < amount_decimal:
                return {
                    'success': False,
                    'error': f'Insufficient balance. Available: {balance_data["available_balance"]} TEO'
                }
            
            # Move from available to pending withdrawal
            balance_obj, created = DBTeoCoinBalance.objects.get_or_create(
                user=user,
                defaults={
                    'available_balance': Decimal('0.00'),
                    'staked_balance': Decimal('0.00'),
                    'pending_withdrawal': Decimal('0.00')
                }
            )
            
            balance_obj.available_balance -= amount_decimal
            balance_obj.pending_withdrawal += amount_decimal
            balance_obj.updated_at = timezone.now()
            balance_obj.save()
            
            # Create withdrawal request
            withdrawal_request = TeoCoinWithdrawalRequest.objects.create(
                user=user,
                amount=amount_decimal,
                wallet_address=wallet_address,
                status='pending'
            )
            
            # Record transaction
            success = self.db_service.add_balance(
                user=user,
                amount=-amount_decimal,  # Negative amount for withdrawal
                transaction_type='withdrawal_request',
                description=f"Withdrawal request to {wallet_address}",
                course_id=None
            )
            
            if not success:
                # Rollback if transaction recording failed
                balance_obj.available_balance += amount_decimal
                balance_obj.pending_withdrawal -= amount_decimal
                balance_obj.save()
                withdrawal_request.delete()
                
                return {
                    'success': False,
                    'error': 'Failed to record withdrawal transaction'
                }
            
            return {
                'success': True,
                'withdrawal_id': withdrawal_request.id,
                'amount': amount_decimal,
                'wallet_address': wallet_address,
                'status': 'pending',
                'estimated_processing_time': '5-10 minutes',
                'message': 'Withdrawal request created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating withdrawal request for {user.email}: {e}")
            return {
                'success': False,
                'error': f'Failed to create withdrawal request: {str(e)}'
            }
    
    def get_withdrawal_status(self, withdrawal_id: int, user) -> Dict[str, Any]:
        """
        Get status of a withdrawal request
        
        Args:
            withdrawal_id: ID of the withdrawal request
            user: User who made the request
            
        Returns:
            Dict with withdrawal details
        """
        try:
            withdrawal = TeoCoinWithdrawalRequest.objects.get(
                id=withdrawal_id,
                user=user
            )
            
            return {
                'success': True,
                'withdrawal': {
                    'id': withdrawal.id,
                    'amount': str(withdrawal.amount),
                    'wallet_address': withdrawal.wallet_address,
                    'status': withdrawal.status,
                    'blockchain_tx_hash': withdrawal.blockchain_tx_hash,
                    'error_message': withdrawal.error_message,
                    'created_at': withdrawal.created_at.isoformat(),
                    'completed_at': withdrawal.completed_at.isoformat() if withdrawal.completed_at else None
                }
            }
            
        except TeoCoinWithdrawalRequest.DoesNotExist:
            return {
                'success': False,
                'error': 'Withdrawal request not found'
            }
        except Exception as e:
            logger.error(f"Error getting withdrawal status {withdrawal_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to get withdrawal status: {str(e)}'
            }
    
    def get_user_withdrawal_history(self, user, limit: int = 20) -> List[Dict]:
        """
        Get user's withdrawal history
        
        Args:
            user: User to get history for
            limit: Maximum number of withdrawals to return
            
        Returns:
            List of withdrawal dictionaries
        """
        try:
            withdrawals = TeoCoinWithdrawalRequest.objects.filter(
                user=user
            ).order_by('-created_at')[:limit]
            
            return [
                {
                    'id': w.id,
                    'amount': str(w.amount),
                    'wallet_address': w.wallet_address,
                    'status': w.status,
                    'blockchain_tx_hash': w.blockchain_tx_hash,
                    'error_message': w.error_message,
                    'created_at': w.created_at.isoformat(),
                    'completed_at': w.completed_at.isoformat() if w.completed_at else None
                }
                for w in withdrawals
            ]
            
        except Exception as e:
            logger.error(f"Error getting withdrawal history for {user.email}: {e}")
            return []
    
    @transaction.atomic
    def cancel_withdrawal_request(self, withdrawal_id: int, user) -> Dict[str, Any]:
        """
        Cancel a pending withdrawal request
        
        Args:
            withdrawal_id: ID of the withdrawal request
            user: User who made the request
            
        Returns:
            Dict with cancellation status
        """
        try:
            withdrawal = TeoCoinWithdrawalRequest.objects.get(
                id=withdrawal_id,
                user=user
            )
            
            if withdrawal.status != 'pending':
                return {
                    'success': False,
                    'error': f'Cannot cancel withdrawal with status: {withdrawal.status}'
                }
            
            # Move amount back from pending to available
            balance_obj = DBTeoCoinBalance.objects.get(user=user)
            balance_obj.available_balance += withdrawal.amount
            balance_obj.pending_withdrawal -= withdrawal.amount
            balance_obj.updated_at = timezone.now()
            balance_obj.save()
            
            # Update withdrawal status
            withdrawal.status = 'cancelled'
            withdrawal.error_message = 'Cancelled by user'
            withdrawal.save()
            
            # Record cancellation transaction
            self.db_service.add_balance(
                user=user,
                amount=withdrawal.amount,
                transaction_type='withdrawal_cancelled',
                description=f"Cancelled withdrawal to {withdrawal.wallet_address}",
                course_id=None
            )
            
            return {
                'success': True,
                'message': 'Withdrawal request cancelled successfully',
                'amount_returned': withdrawal.amount
            }
            
        except TeoCoinWithdrawalRequest.DoesNotExist:
            return {
                'success': False,
                'error': 'Withdrawal request not found'
            }
        except Exception as e:
            logger.error(f"Error cancelling withdrawal {withdrawal_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to cancel withdrawal: {str(e)}'
            }
    
    # ========== ADMIN/PLATFORM METHODS ==========
    
    def get_pending_withdrawals(self, limit: int = 50) -> List[Dict]:
        """
        Get all pending withdrawal requests (admin only)
        
        Args:
            limit: Maximum number of withdrawals to return
            
        Returns:
            List of pending withdrawal dictionaries
        """
        try:
            withdrawals = TeoCoinWithdrawalRequest.objects.filter(
                status='pending'
            ).order_by('-created_at')[:limit]
            
            return [
                {
                    'id': w.id,
                    'user_email': w.user.email,
                    'user_id': w.user.id,
                    'amount': str(w.amount),
                    'wallet_address': w.wallet_address,
                    'status': w.status,
                    'created_at': w.created_at.isoformat(),
                    'age_hours': (timezone.now() - w.created_at).total_seconds() / 3600
                }
                for w in withdrawals
            ]
            
        except Exception as e:
            logger.error(f"Error getting pending withdrawals: {e}")
            return []
    
    def get_withdrawal_statistics(self) -> Dict[str, Any]:
        """
        Get platform withdrawal statistics
        
        Returns:
            Dict with withdrawal statistics
        """
        try:
            from django.db.models import Sum, Count
            
            total_requests = TeoCoinWithdrawalRequest.objects.count()
            pending_requests = TeoCoinWithdrawalRequest.objects.filter(status='pending').count()
            completed_requests = TeoCoinWithdrawalRequest.objects.filter(status='completed').count()
            failed_requests = TeoCoinWithdrawalRequest.objects.filter(status='failed').count()
            cancelled_requests = TeoCoinWithdrawalRequest.objects.filter(status='cancelled').count()
            
            total_amount_requested = TeoCoinWithdrawalRequest.objects.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            
            pending_amount = TeoCoinWithdrawalRequest.objects.filter(
                status='pending'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            return {
                'total_requests': total_requests,
                'pending_requests': pending_requests,
                'completed_requests': completed_requests,
                'failed_requests': failed_requests,
                'cancelled_requests': cancelled_requests,
                'total_amount_requested': str(total_amount_requested),
                'pending_amount': str(pending_amount),
                'completion_rate': (completed_requests / total_requests * 100) if total_requests > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting withdrawal statistics: {e}")
            return {
                'total_requests': 0,
                'pending_requests': 0,
                'completed_requests': 0,
                'failed_requests': 0,
                'cancelled_requests': 0,
                'total_amount_requested': '0.00',
                'pending_amount': '0.00',
                'completion_rate': 0
            }


# Singleton instance
teocoin_withdrawal_service = TeoCoinWithdrawalService()
