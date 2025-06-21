"""
Payment Service for TeoArt School Platform

Handles all payment-related operations including course purchases,
commission calculations, blockchain transactions, and payment verification.
"""

from typing import Dict, List, Any, Optional
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
import uuid
import logging

from .base import TransactionalService
from .exceptions import (
    TeoArtServiceException, 
    UserNotFoundError, 
    CourseNotFoundError,
    InsufficientTeoCoinsError,
    BlockchainTransactionError
)

# Models
from courses.models import Course
from rewards.models import BlockchainTransaction

User = get_user_model()

logger = logging.getLogger(__name__)


class PaymentServiceException(TeoArtServiceException):
    """Payment-specific exceptions"""
    pass


class PaymentService(TransactionalService):
    """
    Service for handling payment operations.
    
    Handles course purchases, commission calculations, 
    blockchain verification, and transaction recording.
    """
    
    # Payment configuration
    PLATFORM_COMMISSION_RATE = Decimal('0.15')  # 15%
    
    def __init__(self):
        super().__init__()
        self.service_name = "PaymentService"
    
    def initiate_course_purchase(
        self,
        user_id: int,
        course_id: int,
        wallet_address: str
    ) -> Dict[str, Any]:
        """
        Initiate a course purchase workflow.
        
        Returns payment requirements and details.
        """
        def _initiate_operation():
            # Validate user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id)
            
            # Validate course
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)
            
            # Validate user role
            if user.role != 'student':
                raise PaymentServiceException(
                    "Only students can purchase courses",
                    "INVALID_USER_ROLE",
                    403
                )
            
            # Check if course is approved
            if not course.is_approved:
                raise PaymentServiceException(
                    "Course is not available for purchase",
                    "COURSE_NOT_APPROVED",
                    403
                )
            
            # Check if user already enrolled
            if user in course.students.all():
                raise PaymentServiceException(
                    "User already enrolled in this course",
                    "ALREADY_ENROLLED",
                    400
                )
            
            # Check teacher has wallet
            if not course.teacher.wallet_address:
                raise PaymentServiceException(
                    "Teacher wallet not configured",
                    "TEACHER_WALLET_MISSING",
                    400
                )
            
            # Update user wallet if needed
            if not user.wallet_address or user.wallet_address.lower() != wallet_address.lower():
                user.wallet_address = wallet_address
                user.save()
            
            # Check balance
            balance = self._get_user_balance(wallet_address)
            if balance < course.price:
                raise InsufficientTeoCoinsError(
                    required=float(course.price),
                    available=float(balance)
                )
            
            # Calculate payment breakdown
            commission_amount = course.price * self.PLATFORM_COMMISSION_RATE
            teacher_amount = course.price - commission_amount
            
            return {
                'payment_required': True,
                'course_id': course.id,
                'course_title': course.title,
                'course_price': float(course.price),
                'teacher_amount': float(teacher_amount),
                'commission_amount': float(commission_amount),
                'commission_rate': f"{float(self.PLATFORM_COMMISSION_RATE * 100)}%",
                'teacher_address': course.teacher.wallet_address,
                'student_address': wallet_address,
                'student_balance': float(balance),
                'payment_breakdown': {
                    'total_price': float(course.price),
                    'teacher_receives': float(teacher_amount),
                    'platform_commission': float(commission_amount),
                    'commission_percentage': float(self.PLATFORM_COMMISSION_RATE * 100)
                }
            }
        
        try:
            return self.execute_in_transaction(_initiate_operation)
        except Exception as e:
            self.log_error(f"Failed to initiate course purchase: {str(e)}")
            raise
    
    def complete_course_purchase(
        self,
        user_id: int,
        course_id: int,
        transaction_hash: str,
        wallet_address: str
    ) -> Dict[str, Any]:
        """
        Complete a course purchase after blockchain payment.
        
        Verifies payment and enrolls user in course.
        """
        def _complete_operation():
            # Validate user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id)
            
            # Validate course
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)
            
            # Check if transaction already processed
            if BlockchainTransaction.objects.filter(transaction_hash=transaction_hash).exists():
                raise PaymentServiceException(
                    "Transaction already processed",
                    "TRANSACTION_ALREADY_PROCESSED",
                    400
                )
            
            # Verify blockchain transaction
            if not self._verify_payment_transaction(
                transaction_hash, 
                wallet_address, 
                course.teacher.wallet_address,
                course.price
            ):
                raise PaymentServiceException(
                    "Blockchain transaction verification failed",
                    "TRANSACTION_VERIFICATION_FAILED",
                    400
                )
            
            # Calculate amounts
            commission_amount = course.price * self.PLATFORM_COMMISSION_RATE
            teacher_amount = course.price - commission_amount
            
            # Enroll student in course
            course.students.add(user)
            
            # Record purchase transaction
            purchase_tx = BlockchainTransaction.objects.create(
                user=user,
                amount=-course.price,
                transaction_type='course_purchase',
                status='completed',
                transaction_hash=transaction_hash,
                from_address=wallet_address,
                to_address=course.teacher.wallet_address,
                related_object_id=str(course.id),
                notes=f"Course purchase: {course.title}"
            )
            
            # Record teacher earnings
            teacher_tx = BlockchainTransaction.objects.create(
                user=course.teacher,
                amount=teacher_amount,
                transaction_type='course_earned',
                status='completed',
                transaction_hash=transaction_hash,
                from_address=wallet_address,
                to_address=course.teacher.wallet_address,
                related_object_id=str(course.id),
                notes=f"Earnings from course sale: {course.title}"
            )
            
            # Record commission transaction
            commission_tx = BlockchainTransaction.objects.create(
                user=user,
                amount=-commission_amount,
                transaction_type='platform_commission',
                status='completed',
                transaction_hash=transaction_hash,
                from_address=wallet_address,
                to_address=getattr(settings, 'REWARD_POOL_ADDRESS', 'reward_pool'),
                related_object_id=str(course.id),
                notes=f"Platform commission from course purchase: {course.title}"
            )
            
            # Send notifications
            self._send_purchase_notifications(course, user, course.teacher)
            
            self.log_info(f"Course purchase completed: user {user_id} -> course {course_id}")
            
            return {
                'success': True,
                'message': 'Course purchased successfully',
                'course_id': course.id,
                'course_title': course.title,
                'student_id': user.id,
                'student_username': user.username,
                'total_paid': float(course.price),
                'teacher_received': float(teacher_amount),
                'platform_commission': float(commission_amount),
                'transaction_hash': transaction_hash,
                'enrollment_confirmed': True,
                'transactions_recorded': {
                    'purchase_id': purchase_tx.id,
                    'teacher_earning_id': teacher_tx.id,
                    'commission_id': commission_tx.id
                }
            }
        
        try:
            return self.execute_in_transaction(_complete_operation)
        except Exception as e:
            self.log_error(f"Failed to complete course purchase: {str(e)}")
            raise
    
    def get_user_purchase_history(
        self,
        user_id: int,
        transaction_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's purchase history.
        """
        try:
            # Validate user
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id)
            
            # Build query
            queryset = BlockchainTransaction.objects.filter(user=user)
            
            if transaction_type:
                queryset = queryset.filter(transaction_type=transaction_type)
            
            # Order by newest first
            queryset = queryset.order_by('-created_at')
            
            if limit:
                queryset = queryset[:limit]
            
            transactions = []
            for tx in queryset:
                # Get related course if available
                related_course = None
                if tx.related_object_id and tx.transaction_type in ['course_purchase', 'course_earned']:
                    try:
                        course = Course.objects.get(id=int(tx.related_object_id))
                        related_course = {
                            'id': course.id,
                            'title': course.title,
                            'teacher': course.teacher.username
                        }
                    except (Course.DoesNotExist, ValueError):
                        pass
                
                transactions.append({
                    'id': tx.id,
                    'amount': float(tx.amount),
                    'transaction_type': tx.transaction_type,
                    'status': tx.status,
                    'transaction_hash': tx.transaction_hash,
                    'from_address': tx.from_address,
                    'to_address': tx.to_address,
                    'notes': tx.notes,
                    'created_at': tx.created_at.isoformat(),
                    'related_course': related_course
                })
            
            self.log_info(f"Retrieved {len(transactions)} transactions for user {user_id}")
            return transactions
            
        except Exception as e:
            self.log_error(f"Failed to get user purchase history: {str(e)}")
            raise
    
    def get_course_sales_stats(self, course_id: int) -> Dict[str, Any]:
        """
        Get sales statistics for a course.
        """
        try:
            # Validate course
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)
            
            # Get purchase transactions
            purchase_transactions = BlockchainTransaction.objects.filter(
                transaction_type='course_purchase',
                related_object_id=str(course_id)
            )
            
            # Get earning transactions (for teacher)
            earning_transactions = BlockchainTransaction.objects.filter(
                transaction_type='course_earned',
                related_object_id=str(course_id)
            )
            
            # Calculate stats
            total_sales = purchase_transactions.count()
            total_revenue = sum(abs(tx.amount) for tx in purchase_transactions)
            total_teacher_earnings = sum(tx.amount for tx in earning_transactions)
            total_commission = total_revenue - total_teacher_earnings
            
            return {
                'course_id': course.id,
                'course_title': course.title,
                'teacher_id': course.teacher.id,
                'teacher_username': course.teacher.username,
                'total_sales': total_sales,
                'total_revenue': float(total_revenue),
                'teacher_earnings': float(total_teacher_earnings),
                'platform_commission': float(total_commission),
                'average_sale_value': float(total_revenue / total_sales) if total_sales > 0 else 0,
                'commission_rate': f"{float(self.PLATFORM_COMMISSION_RATE * 100)}%"
            }
            
        except Exception as e:
            self.log_error(f"Failed to get course sales stats: {str(e)}")
            raise
    
    def _get_user_balance(self, wallet_address: str) -> Decimal:
        """Get user's TeoCoins balance"""
        try:
            from blockchain.views import teocoin_service
            balance = teocoin_service.get_balance(wallet_address)
            return Decimal(str(balance))
        except Exception as e:
            self.log_error(f"Failed to get balance for {wallet_address}: {str(e)}")
            return Decimal('0')
    
    def _verify_payment_transaction(
        self, 
        tx_hash: str, 
        from_address: str, 
        to_address: str, 
        expected_amount: Decimal
    ) -> bool:
        """Verify blockchain payment transaction"""
        try:
            # Check our database first
            related_transactions = BlockchainTransaction.objects.filter(
                transaction_hash=tx_hash
            )
            
            if related_transactions.exists():
                for tx in related_transactions:
                    if (tx.from_address and tx.to_address and
                        tx.from_address.lower() == from_address.lower() and
                        tx.to_address.lower() == to_address.lower() and
                        abs(tx.amount) >= expected_amount * Decimal('0.85')):
                        return True
            
            # Fallback to blockchain verification
            return self._verify_blockchain_transaction(tx_hash, from_address, to_address, expected_amount)
            
        except Exception as e:
            self.log_error(f"Transaction verification failed: {str(e)}")
            return False
    
    def _verify_blockchain_transaction(
        self, 
        tx_hash: str, 
        from_address: str, 
        to_address: str, 
        expected_amount: Decimal
    ) -> bool:
        """Verify transaction on the blockchain"""
        try:
            # Check for simulated transactions (testing)
            if tx_hash.startswith("0x") and len(tx_hash) == 66:
                simulated_tx = BlockchainTransaction.objects.filter(
                    transaction_hash=tx_hash,
                    transaction_type='simulated_payment',
                    status='completed'
                ).first()
                
                if simulated_tx:
                    return (simulated_tx.from_address.lower() == from_address.lower() and
                            simulated_tx.to_address.lower() == to_address.lower() and
                            simulated_tx.amount >= expected_amount)
            
            # Real blockchain verification
            from blockchain.views import teocoin_service
            
            receipt = teocoin_service.w3.eth.get_transaction_receipt(tx_hash)
            if receipt["status"] != 1:
                return False
            
            tx = teocoin_service.w3.eth.get_transaction(tx_hash)
            contract_addr = getattr(teocoin_service, 'contract_address', None)
            
            if tx.get("to") and contract_addr:
                if str(tx.get("to")).lower() != str(contract_addr).lower():
                    return False
            
            transfer_events = teocoin_service.contract.events.Transfer().process_receipt(receipt)
            
            for event in transfer_events:
                event_from = event.args['from'].lower()
                event_to = event.args['to'].lower()
                event_amount = Decimal(str(teocoin_service.w3.from_wei(event.args['value'], 'ether')))
                
                if (event_from == from_address.lower() and 
                    event_to == to_address.lower() and
                    event_amount >= expected_amount):
                    return True
            
            return False
            
        except Exception as e:
            self.log_error(f"Blockchain verification failed: {str(e)}")
            return False
    
    def _send_purchase_notifications(self, course, student, teacher):
        """Send notifications for course purchase"""
        try:
            from courses.signals import notify_course_purchase
            notify_course_purchase(course, student, teacher)
        except Exception as e:
            self.log_error(f"Failed to send purchase notifications: {str(e)}")


# Global service instance
payment_service = PaymentService()
