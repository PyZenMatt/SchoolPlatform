"""
TeoCoin Escrow Service

Manages the complete lifecycle of TeoCoin escrows for teacher choice system.
When students apply TeoCoin discounts, funds go to escrow until teacher decides.
"""

from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from rewards.models import TeoCoinEscrow, BlockchainTransaction
from notifications.models import Notification


class TeoCoinEscrowService:
    """
    Manages TeoCoin escrow lifecycle for teacher choice system
    """
    
    def __init__(self):
        self.escrow_duration_days = getattr(settings, 'TEOCOIN_ESCROW_DAYS', 7)
        self.platform_wallet = getattr(settings, 'PLATFORM_WALLET_ADDRESS', None)
    
    def create_escrow(self, student, teacher, course, teocoin_amount, discount_data, transfer_tx_hash=None):
        """
        Create new escrow when student uses TeoCoin discount
        
        Args:
            student: User who applied discount
            teacher: Course teacher who needs to decide
            course: Course being purchased
            teocoin_amount: Amount of TeoCoin in escrow (Decimal)
            discount_data: Dict with percentage, euro_amount, original_price
            transfer_tx_hash: Blockchain transaction hash for TeoCoin transfer
            
        Returns:
            TeoCoinEscrow: Created escrow instance
        """
        try:
            with transaction.atomic():
                # Calculate teacher compensation options
                teacher_options = self.calculate_teacher_options(
                    course_price=discount_data['original_price'],
                    discount_percentage=discount_data['percentage'],
                    teacher=teacher
                )
                
                # Create escrow record
                escrow = TeoCoinEscrow.objects.create(
                    student=student,
                    teacher=teacher,
                    course=course,
                    teocoin_amount=teocoin_amount,
                    discount_percentage=Decimal(str(discount_data['percentage'])),
                    discount_euro_amount=Decimal(str(discount_data['euro_amount'])),
                    original_course_price=Decimal(str(discount_data['original_price'])),
                    standard_euro_commission=teacher_options['standard_commission'],
                    reduced_euro_commission=teacher_options['reduced_commission'],
                    escrow_tx_hash=transfer_tx_hash,
                    expires_at=timezone.now() + timedelta(days=self.escrow_duration_days),
                    status='pending'
                )
                
                # Record blockchain transaction for escrow creation
                BlockchainTransaction.objects.create(
                    user=student,
                    transaction_type='discount_applied',
                    amount=-teocoin_amount,  # Negative = outgoing from student
                    from_address=getattr(student, 'wallet_address', None),
                    to_address=self.platform_wallet,  # Escrow held by platform
                    tx_hash=transfer_tx_hash,
                    status='confirmed',
                    related_object_id=str(escrow.id),
                    notes=f'TeoCoin discount escrow for course: {course.title}'
                )
                
                # Send notification to teacher
                self.notify_teacher(escrow)
                
                print(f"✅ Escrow created: {escrow.id} - {teocoin_amount} TEO for {course.title}")
                return escrow
                
        except Exception as e:
            print(f"❌ Escrow creation failed: {e}")
            raise
    
    def notify_teacher(self, escrow):
        """
        Send notification to teacher about pending escrow decision
        
        Args:
            escrow: TeoCoinEscrow instance
        """
        try:
            # Calculate days remaining
            days_remaining = (escrow.expires_at - timezone.now()).days
            
            message = (
                f"🪙 TeoCoin Discount Request\n\n"
                f"Student: {escrow.student.get_full_name() or escrow.student.username}\n"
                f"Course: {escrow.course.title}\n"
                f"Discount: {escrow.discount_percentage}% ({escrow.teocoin_amount} TeoCoin)\n\n"
                f"Your Options:\n"
                f"✅ Accept: €{escrow.reduced_euro_commission} + {escrow.teocoin_amount} TEO\n"
                f"💰 Reject: €{escrow.standard_euro_commission} (standard commission)\n\n"
                f"⏰ Decide within {days_remaining} days"
            )
            
            notification = Notification.objects.create(
                user=escrow.teacher,
                message=message,
                notification_type='teocoin_discount_pending',
                related_object_id=escrow.id
            )
            
            print(f"📬 Teacher notification sent: {notification.id}")
            return notification
            
        except Exception as e:
            print(f"❌ Teacher notification failed: {e}")
            return None
    
    def accept_escrow(self, escrow_id, teacher):
        """
        Teacher accepts TeoCoin - release to teacher wallet
        
        Args:
            escrow_id: ID of escrow to accept
            teacher: Teacher user making the decision
            
        Returns:
            dict: Result with success status and transaction details
        """
        try:
            with transaction.atomic():
                escrow = TeoCoinEscrow.objects.select_for_update().get(
                    id=escrow_id,
                    teacher=teacher,
                    status='pending'
                )
                
                # Check if expired
                if escrow.is_expired:
                    return {
                        'success': False,
                        'error': 'Escrow has expired and cannot be accepted'
                    }
                
                # Transfer TeoCoin to teacher wallet
                teacher_wallet = getattr(teacher, 'wallet_address', None)
                if not teacher_wallet:
                    return {
                        'success': False,
                        'error': 'Teacher wallet address not found. Please connect your wallet.'
                    }
                
                # Execute blockchain transfer (platform wallet → teacher wallet)
                # TODO: Implement actual blockchain transfer
                transfer_result = {
                    'success': True,
                    'tx_hash': f'0x{escrow_id}_{teacher.id}_transfer'  # Placeholder hash
                }
                
                if not transfer_result.get('success'):
                    return {
                        'success': False,
                        'error': 'Blockchain transfer failed. Please try again.'
                    }
                
                # Update escrow status
                escrow.status = 'accepted'
                escrow.teacher_decision_at = timezone.now()
                escrow.release_tx_hash = transfer_result.get('tx_hash')
                escrow.save()
                
                # Record teacher TeoCoin earning
                BlockchainTransaction.objects.create(
                    user=teacher,
                    transaction_type='course_earned',
                    amount=escrow.teocoin_amount,  # Positive = incoming to teacher
                    from_address=self.platform_wallet,
                    to_address=teacher_wallet,
                    tx_hash=escrow.release_tx_hash,
                    status='confirmed',
                    related_object_id=str(escrow.course.id),
                    notes=f'TeoCoin discount accepted for course: {escrow.course.title}'
                )
                
                # Send confirmation notification
                self._send_decision_notification(escrow, 'accepted')
                
                print(f"✅ Escrow accepted: {escrow.id} - {escrow.teocoin_amount} TEO → {teacher.username}")
                
                return {
                    'success': True,
                    'escrow_id': escrow.id,
                    'teocoin_amount': str(escrow.teocoin_amount),
                    'euro_commission': str(escrow.reduced_euro_commission),
                    'tx_hash': escrow.release_tx_hash
                }
                
        except TeoCoinEscrow.DoesNotExist:
            return {
                'success': False,
                'error': 'Escrow not found or already processed'
            }
        except Exception as e:
            print(f"❌ Escrow acceptance failed: {e}")
            return {
                'success': False,
                'error': f'Acceptance failed: {str(e)}'
            }
    
    def reject_escrow(self, escrow_id, teacher, reason=None):
        """
        Teacher rejects TeoCoin - return to platform
        
        Args:
            escrow_id: ID of escrow to reject
            teacher: Teacher user making the decision
            reason: Optional reason for rejection
            
        Returns:
            dict: Result with success status
        """
        try:
            with transaction.atomic():
                escrow = TeoCoinEscrow.objects.select_for_update().get(
                    id=escrow_id,
                    teacher=teacher,
                    status='pending'
                )
                
                # Check if expired
                if escrow.is_expired:
                    return {
                        'success': False,
                        'error': 'Escrow has already expired'
                    }
                
                # Update escrow status (TeoCoin stays with platform)
                escrow.status = 'rejected'
                escrow.teacher_decision_at = timezone.now()
                escrow.teacher_decision_notes = reason or 'Teacher declined TeoCoin'
                escrow.save()
                
                # Record platform TeoCoin retention
                BlockchainTransaction.objects.create(
                    user=teacher,  # For tracking purposes
                    transaction_type='discount_applied',
                    amount=Decimal('0'),  # No actual transfer
                    from_address=None,
                    to_address=self.platform_wallet,
                    tx_hash=None,
                    status='completed',
                    related_object_id=str(escrow.course.id),
                    notes=f'TeoCoin discount rejected - returned to platform. Course: {escrow.course.title}'
                )
                
                # Send confirmation notification
                self._send_decision_notification(escrow, 'rejected')
                
                print(f"❌ Escrow rejected: {escrow.id} - {escrow.teocoin_amount} TEO → Platform")
                
                return {
                    'success': True,
                    'escrow_id': escrow.id,
                    'euro_commission': str(escrow.standard_euro_commission),
                    'reason': reason
                }
                
        except TeoCoinEscrow.DoesNotExist:
            return {
                'success': False,
                'error': 'Escrow not found or already processed'
            }
        except Exception as e:
            print(f"❌ Escrow rejection failed: {e}")
            return {
                'success': False,
                'error': f'Rejection failed: {str(e)}'
            }
    
    def process_expired_escrows(self):
        """
        Background task to handle expired escrows (auto-reject)
        
        Returns:
            dict: Summary of processed escrows
        """
        try:
            expired_escrows = TeoCoinEscrow.objects.filter(
                status='pending',
                expires_at__lt=timezone.now()
            )
            
            processed_count = 0
            total_teocoin = Decimal('0')
            
            for escrow in expired_escrows:
                # Auto-reject expired escrow
                escrow.status = 'expired'
                escrow.teacher_decision_at = timezone.now()
                escrow.teacher_decision_notes = 'Auto-expired after 7 days'
                escrow.save()
                
                # Send expiration notification
                self._send_decision_notification(escrow, 'expired')
                
                processed_count += 1
                total_teocoin += escrow.teocoin_amount
                
                print(f"⏰ Expired escrow: {escrow.id} - {escrow.teocoin_amount} TEO")
            
            return {
                'processed_count': processed_count,
                'total_teocoin_retained': str(total_teocoin)
            }
            
        except Exception as e:
            print(f"❌ Expired escrow processing failed: {e}")
            return {'error': str(e)}
    
    def calculate_teacher_options(self, course_price, discount_percentage, teacher):
        """
        Calculate teacher compensation for both accept/reject scenarios
        
        Args:
            course_price: Original course price in EUR
            discount_percentage: Discount percentage applied
            teacher: Teacher user (for commission tier)
            
        Returns:
            dict: Commission amounts for both scenarios
        """
        # TODO: Import staking service when available
        # For now, use default 50% commission rate
        base_commission_rate = 0.50  # Default 50%
        
        # Calculate final price after discount
        final_price = course_price * (1 - discount_percentage / 100)
        
        # Standard commission (if rejected): Normal rate on full price
        standard_commission = course_price * base_commission_rate
        
        # Reduced commission (if accepted): Normal rate on discounted price
        reduced_commission = final_price * base_commission_rate
        
        return {
            'standard_commission': Decimal(str(standard_commission)),
            'reduced_commission': Decimal(str(reduced_commission)),
            'commission_rate': base_commission_rate
        }
    
    def _send_decision_notification(self, escrow, decision_type):
        """
        Send notification about escrow decision (accepted/rejected/expired)
        
        Args:
            escrow: TeoCoinEscrow instance
            decision_type: 'accepted', 'rejected', or 'expired'
        """
        try:
            if decision_type == 'accepted':
                message = (
                    f"✅ TeoCoin Discount Accepted\n\n"
                    f"You accepted {escrow.teocoin_amount} TeoCoin for {escrow.course.title}\n"
                    f"Commission: €{escrow.reduced_euro_commission} + {escrow.teocoin_amount} TEO"
                )
                notification_type = 'teocoin_discount_accepted'
                
            elif decision_type == 'rejected':
                message = (
                    f"💰 TeoCoin Discount Rejected\n\n"
                    f"You chose standard commission for {escrow.course.title}\n"
                    f"Commission: €{escrow.standard_euro_commission}"
                )
                notification_type = 'teocoin_discount_rejected'
                
            else:  # expired
                message = (
                    f"⏰ TeoCoin Discount Expired\n\n"
                    f"The TeoCoin discount for {escrow.course.title} has expired.\n"
                    f"Commission: €{escrow.standard_euro_commission} (standard rate)\n"
                    f"Missed opportunity: {escrow.teocoin_amount} TEO"
                )
                notification_type = 'teocoin_discount_expired'
            
            Notification.objects.create(
                user=escrow.teacher,
                message=message,
                notification_type=notification_type,
                related_object_id=escrow.id
            )
            
            print(f"📬 Decision notification sent: {decision_type}")
            
        except Exception as e:
            print(f"❌ Decision notification failed: {e}")
    
    def get_teacher_escrows(self, teacher, status=None):
        """
        Get escrows for a specific teacher
        
        Args:
            teacher: Teacher user
            status: Optional status filter ('pending', 'accepted', 'rejected', 'expired')
            
        Returns:
            QuerySet: Filtered escrows
        """
        queryset = TeoCoinEscrow.objects.filter(teacher=teacher).select_related(
            'student', 'course'
        ).order_by('-created_at')
        
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset
    
    def get_escrow_statistics(self, teacher):
        """
        Get escrow statistics for teacher dashboard
        
        Args:
            teacher: Teacher user
            
        Returns:
            dict: Statistics summary
        """
        try:
            escrows = self.get_teacher_escrows(teacher)
            
            total_escrows = escrows.count()
            pending_escrows = escrows.filter(status='pending').count()
            accepted_escrows = escrows.filter(status='accepted').count()
            rejected_escrows = escrows.filter(status='rejected').count()
            expired_escrows = escrows.filter(status='expired').count()
            
            # Calculate TeoCoin earnings
            accepted_teocoin = escrows.filter(status='accepted').aggregate(
                total=Sum('teocoin_amount')
            )['total'] or Decimal('0')
            
            # Calculate acceptance rate
            acceptance_rate = (accepted_escrows / total_escrows * 100) if total_escrows > 0 else 0
            
            return {
                'total_escrows': total_escrows,
                'pending_escrows': pending_escrows,
                'accepted_escrows': accepted_escrows,
                'rejected_escrows': rejected_escrows,
                'expired_escrows': expired_escrows,
                'acceptance_rate': round(acceptance_rate, 1),
                'total_teocoin_earned': str(accepted_teocoin)
            }
            
        except Exception as e:
            print(f"❌ Statistics calculation failed: {e}")
            return {}


# Create service instance
escrow_service = TeoCoinEscrowService()
