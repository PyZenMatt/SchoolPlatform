"""
TeoCoin Earning Service for SchoolPlatform
Integrates with your existing TeoCoinService to provide automatic earning rewards
"""

from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from blockchain.blockchain import TeoCoinService
from decimal import Decimal
import logging

# Import the model from services.models
from .models import TeoEarning

logger = logging.getLogger(__name__)

class TeoEarningService:
    """Enhanced earning service using your existing TeoCoinService"""
    
    # Earning rates - adjust these as needed
    EARNING_RATES = {
        'welcome_bonus': Decimal('20.0'),
        'course_completion': Decimal('0.10'),  # 10% of course price
        'exercise_submission': Decimal('2.0'),
        'quiz_perfect': Decimal('5.0'),
        'referral_student': Decimal('25.0'),
        'referral_teacher': Decimal('50.0'),
        'course_review': Decimal('10.0'),
        'weekly_streak': Decimal('15.0'),
        'monthly_streak': Decimal('50.0'),
    }
    
    def __init__(self):
        self.teo_service = TeoCoinService()
    
    def reward_course_completion(self, user_id: int, course_id: int) -> bool:
        """Reward user for completing a course"""
        try:
            user = User.objects.get(id=user_id)
            
            # Import here to avoid circular imports
            from courses.models import Course
            course = Course.objects.get(id=course_id)
            
            # Check if already rewarded
            existing = TeoEarning.objects.filter(
                user=user,
                earning_type='course_completion',
                source_id=course_id
            ).exists()
            
            if existing:
                logger.info(f"User {user_id} already rewarded for course {course_id}")
                return True
            
            # Calculate reward (10% of course price in TEO)
            teo_amount = course.price * self.EARNING_RATES['course_completion']
            
            # Get user's wallet address
            wallet_address = getattr(user, 'wallet_address', None) or getattr(user, 'amoy_address', None)
            
            if not wallet_address:
                logger.error(f"User {user_id} has no wallet address")
                return False
            
            # Mint TEO using your existing service
            tx_hash = self.teo_service.mint_tokens(
                to_address=wallet_address,
                amount=float(teo_amount),
                reason=f"Course completion: {course.title}"
            )
            
            # Record the earning
            TeoEarning.objects.create(
                user=user,
                earning_type='course_completion',
                amount=teo_amount,
                source_id=course_id,
                transaction_hash=tx_hash,
                reason=f"Completed course: {course.title}"
            )
            
            logger.info(f"Rewarded {teo_amount} TEO to user {user_id} for course {course_id}")
            
            # Send notification
            self.send_earning_notification(user, teo_amount, 'course_completion', course.title)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reward course completion: {e}")
            return False
    
    def reward_exercise_submission(self, user_id: int, exercise_id: int) -> bool:
        """Reward user for submitting an exercise"""
        try:
            user = User.objects.get(id=user_id)
            
            # Import here to avoid circular imports
            from courses.models import Exercise
            exercise = Exercise.objects.get(id=exercise_id)
            
            # Check if already rewarded for this exercise
            existing = TeoEarning.objects.filter(
                user=user,
                earning_type='exercise_submission',
                source_id=exercise_id
            ).exists()
            
            if existing:
                return True
            
            teo_amount = self.EARNING_RATES['exercise_submission']
            wallet_address = getattr(user, 'wallet_address', None) or getattr(user, 'amoy_address', None)
            
            if not wallet_address:
                logger.error(f"User {user_id} has no wallet address")
                return False
            
            # Mint TEO
            tx_hash = self.teo_service.mint_tokens(
                to_address=wallet_address,
                amount=float(teo_amount),
                reason=f"Exercise submission: {exercise.title}"
            )
            
            # Record earning
            TeoEarning.objects.create(
                user=user,
                earning_type='exercise_submission',
                amount=teo_amount,
                source_id=exercise_id,
                transaction_hash=tx_hash,
                reason=f"Submitted exercise: {exercise.title}"
            )
            
            self.send_earning_notification(user, teo_amount, 'exercise_submission', exercise.title)
            return True
            
        except Exception as e:
            logger.error(f"Failed to reward exercise submission: {e}")
            return False
    
    def give_welcome_bonus(self, user_id: int) -> bool:
        """Give one-time welcome bonus"""
        try:
            user = User.objects.get(id=user_id)
            
            # Check if already received
            existing = TeoEarning.objects.filter(
                user=user,
                earning_type='welcome_bonus'
            ).exists()
            
            if existing:
                return True
            
            wallet_address = getattr(user, 'wallet_address', None) or getattr(user, 'amoy_address', None)
            
            if not wallet_address:
                logger.error(f"User {user_id} has no wallet address for welcome bonus")
                return False
            
            teo_amount = self.EARNING_RATES['welcome_bonus']
            
            # Mint welcome TEO
            tx_hash = self.teo_service.mint_tokens(
                to_address=wallet_address,
                amount=float(teo_amount),
                reason="Welcome to SchoolPlatform!"
            )
            
            # Record earning
            TeoEarning.objects.create(
                user=user,
                earning_type='welcome_bonus',
                amount=teo_amount,
                source_id=None,
                transaction_hash=tx_hash,
                reason="Welcome bonus for joining SchoolPlatform"
            )
            
            self.send_earning_notification(user, teo_amount, 'welcome_bonus', "Welcome!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to give welcome bonus: {e}")
            return False
    
    def get_user_earnings_history(self, user_id: int, limit: int = 50):
        """Get user's TEO earning history"""
        try:
            user = User.objects.get(id=user_id)
            earnings = TeoEarning.objects.filter(user=user).order_by('-created_at')[:limit]
            
            return [{
                'id': earning.id,
                'earning_type': earning.earning_type,
                'amount': float(earning.amount),
                'reason': earning.reason,
                'transaction_hash': earning.transaction_hash,
                'created_at': earning.created_at.isoformat(),
                'source_id': earning.source_id
            } for earning in earnings]
            
        except Exception as e:
            logger.error(f"Failed to get earnings history for user {user_id}: {e}")
            return []
    
    def get_user_total_earned(self, user_id: int) -> Decimal:
        """Get total TEO earned by user"""
        try:
            user = User.objects.get(id=user_id)
            total = TeoEarning.objects.filter(user=user).aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0')
            
            return total
            
        except Exception as e:
            logger.error(f"Failed to get total earned for user {user_id}: {e}")
            return Decimal('0')
    
    def send_earning_notification(self, user, amount, earning_type, context):
        """Send notification to user about TEO earning"""
        message = f"🎉 You earned {amount} TEO for {context}!"
        
        # Log the earning
        logger.info(f"TEO Earned: {user.username} received {amount} TEO for {earning_type}")
        
        # Here you can integrate with your notification system
        # Examples:
        
        # 1. If you have a notifications app:
        # from notifications.models import Notification
        # Notification.objects.create(
        #     user=user,
        #     message=message,
        #     notification_type='teo_earned'
        # )
        
        # 2. If you have email notifications:
        # from django.core.mail import send_mail
        # send_mail(
        #     subject=f"🪙 You earned {amount} TEO!",
        #     message=message,
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[user.email],
        #     fail_silently=True
        # )
        
        # 3. If you have WebSocket notifications:
        # from channels.layers import get_channel_layer
        # channel_layer = get_channel_layer()
        # async_to_sync(channel_layer.group_send)(
        #     f"user_{user.id}",
        #     {
        #         "type": "teo_earned",
        #         "message": message,
        #         "amount": float(amount),
        #         "earning_type": earning_type
        #     }
        # )

# Service instance
teo_earning_service = TeoEarningService()
