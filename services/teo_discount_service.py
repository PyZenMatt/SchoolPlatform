"""
TeoCoin Virtual Discount System - Smart Solution for Student Discounts
Avoids gas fees while providing real TeoCoin utility and value

BUSINESS MODEL:
- Students earn TeoCoin rewards from course purchases (no gas fees - we mint)
- Students can "spend" TeoCoin for discounts (no gas fees - database only)
- Teachers receive full EUR payments (no complexity)
- Platform covers discounts as customer acquisition cost
- Real TeoCoin stays in student wallets (can be used later for other purposes)
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import transaction
from django.db import models
from django.utils import timezone

from users.models import User
from courses.models import Course
from rewards.models import BlockchainTransaction
from core.economics import platform_economics

class TeoDiscountService:
    """
    Virtual TeoCoin discount system without gas fees
    Integrated with platform economics configuration
    """
    
    # Import economics configuration
    TEOCOIN_TO_EUR_DISCOUNT_RATE = platform_economics.TEOCOIN_EURO_EXCHANGE_RATE
    MAX_DISCOUNT_PERCENTAGE = Decimal('0.15')  # Updated to 15% as requested
    MIN_TEOCOIN_FOR_DISCOUNT = platform_economics.MIN_TEOCOIN_FOR_DISCOUNT
    
    @classmethod
    def calculate_available_discount(cls, user: User, course: Course) -> Dict[str, Any]:
        """
        Calculate how much discount a user can get with their TeoCoin balance
        
        Returns:
            dict: Contains max_discount_eur, teocoin_needed, discount_percentage, etc.
        """
        try:
            # Get user's TeoCoin balance (from database mirror)
            user_balance = cls._get_user_virtual_balance(user)
            
            if user_balance < cls.MIN_TEOCOIN_FOR_DISCOUNT:
                return {
                    'can_use_discount': False,
                    'reason': f'Minimum {cls.MIN_TEOCOIN_FOR_DISCOUNT} TEO required',
                    'user_balance': float(user_balance),
                    'min_required': float(cls.MIN_TEOCOIN_FOR_DISCOUNT)
                }
            
            course_price = course.price_eur
            if not course_price:
                return {
                    'can_use_discount': False,
                    'reason': 'Course does not have EUR pricing',
                    'user_balance': float(user_balance)
                }
            
            # Calculate maximum possible discount (20% of course price)
            max_discount_by_percentage = course_price * cls.MAX_DISCOUNT_PERCENTAGE
            
            # Calculate discount based on user's TeoCoin balance
            max_discount_by_balance = user_balance * cls.TEOCOIN_TO_EUR_DISCOUNT_RATE
            
            # Use the smaller of the two limits
            max_available_discount = min(max_discount_by_percentage, max_discount_by_balance)
            
            # Calculate how many TeoCoin needed for max discount
            teocoin_needed_for_max = max_available_discount / cls.TEOCOIN_TO_EUR_DISCOUNT_RATE
            
            # Final discounted price
            discounted_price = course_price - max_available_discount
            
            return {
                'can_use_discount': True,
                'user_balance': float(user_balance),
                'course_price_eur': float(course_price),
                'max_discount_eur': float(max_available_discount),
                'discounted_price_eur': float(discounted_price),
                'teocoin_needed': float(teocoin_needed_for_max),
                'discount_percentage': float((max_available_discount / course_price) * 100),
                'discount_rate': f'1 TEO = €{cls.TEOCOIN_TO_EUR_DISCOUNT_RATE}',
                'savings': f'Save €{max_available_discount:.2f} with {teocoin_needed_for_max:.1f} TEO'
            }
            
        except Exception as e:
            return {
                'can_use_discount': False,
                'reason': f'Error calculating discount: {str(e)}',
                'user_balance': 0
            }
    
    @classmethod
    def apply_teocoin_discount(
        cls, 
        user: User, 
        course: Course, 
        teocoin_to_spend: Decimal
    ) -> Dict[str, Any]:
        """
        Apply TeoCoin discount by virtually spending TeoCoin (database only)
        
        Args:
            user: User applying discount
            course: Course being purchased
            teocoin_to_spend: Amount of TeoCoin to "spend" for discount
            
        Returns:
            dict: Contains final_price, discount_applied, virtual_transaction_id
        """
        
        with transaction.atomic():
            try:
                # Validate user balance
                user_balance = cls._get_user_virtual_balance(user)
                
                if user_balance < teocoin_to_spend:
                    return {
                        'success': False,
                        'error': f'Insufficient TeoCoin balance. Have: {user_balance}, Need: {teocoin_to_spend}'
                    }
                
                if teocoin_to_spend < cls.MIN_TEOCOIN_FOR_DISCOUNT:
                    return {
                        'success': False,
                        'error': f'Minimum {cls.MIN_TEOCOIN_FOR_DISCOUNT} TEO required for discount'
                    }
                
                # Calculate discount
                discount_eur = teocoin_to_spend * cls.TEOCOIN_TO_EUR_DISCOUNT_RATE
                max_allowed_discount = course.price_eur * cls.MAX_DISCOUNT_PERCENTAGE
                
                if discount_eur > max_allowed_discount:
                    return {
                        'success': False,
                        'error': f'Discount too large. Max allowed: €{max_allowed_discount:.2f}'
                    }
                
                # Calculate final price
                final_price_eur = course.price_eur - discount_eur
                
                # Create virtual spending transaction (database only - no blockchain)
                virtual_transaction = BlockchainTransaction.objects.create(
                    user=user,
                    transaction_type='virtual_discount_spend',
                    amount=-teocoin_to_spend,  # Negative = spending
                    status='completed',
                    transaction_hash=f'virtual_discount_{timezone.now().timestamp()}',
                    related_object_id=str(course.id),
                    notes=f'Virtual TeoCoin discount: {teocoin_to_spend} TEO for €{discount_eur:.2f} off {course.title}',
                    from_address=user.wallet_address or 'virtual',
                    to_address='discount_pool'
                )
                
                return {
                    'success': True,
                    'final_price_eur': float(final_price_eur),
                    'discount_applied_eur': float(discount_eur),
                    'teocoin_spent': float(teocoin_to_spend),
                    'virtual_transaction_id': virtual_transaction.id,
                    'original_price_eur': float(course.price_eur),
                    'savings_percentage': float((discount_eur / course.price_eur) * 100),
                    'message': f'Applied {teocoin_to_spend} TEO discount (€{discount_eur:.2f} off)'
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Failed to apply discount: {str(e)}'
                }
    
    @classmethod
    def _get_user_virtual_balance(cls, user: User) -> Decimal:
        """
        Get user's virtual TeoCoin balance from database transactions
        This mirrors their actual blockchain balance but allows for virtual spending
        """
        try:
            # Sum all TeoCoin transactions for this user
            total_earned = BlockchainTransaction.objects.filter(
                user=user,
                transaction_type__in=['reward', 'bonus'],
                status='completed'
            ).aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0')
            
            # Sum all virtual spending
            total_spent = BlockchainTransaction.objects.filter(
                user=user,
                transaction_type='virtual_discount_spend',
                status='completed'
            ).aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0')
            
            # Balance = earned + spent (spent is negative)
            balance = total_earned + total_spent
            
            return max(balance, Decimal('0'))  # Never negative
            
        except Exception:
            return Decimal('0')
    
    @classmethod
    def get_user_discount_history(cls, user: User) -> list:
        """Get user's TeoCoin discount usage history"""
        try:
            discount_transactions = BlockchainTransaction.objects.filter(
                user=user,
                transaction_type='virtual_discount_spend',
                status='completed'
            ).order_by('-created_at')
            
            history = []
            for tx in discount_transactions:
                try:
                    course = Course.objects.get(id=int(tx.related_object_id))
                    course_title = course.title
                except:
                    course_title = 'Unknown Course'
                
                history.append({
                    'date': tx.created_at,
                    'teocoin_spent': float(abs(tx.amount)),
                    'course_title': course_title,
                    'notes': tx.notes,
                    'transaction_id': tx.id
                })
            
            return history
            
        except Exception:
            return []
    
    @classmethod
    def get_course_economics_with_teo(cls, course: Course, teo_to_spend: Decimal = Decimal('0')) -> Dict[str, Any]:
        """
        Get complete course economics including TeoCoin discount calculations
        
        Args:
            course: Course object
            teo_to_spend: Amount of TeoCoin to apply (optional)
            
        Returns:
            dict: Complete economic breakdown with TeoCoin integration
        """
        try:
            if teo_to_spend > 0:
                # Calculate with TeoCoin discount
                economics = platform_economics.get_discount_with_teo(
                    course.price_eur, 
                    teo_to_spend
                )
                economics['using_teocoin_discount'] = True
            else:
                # Calculate standard economics
                economics = platform_economics.calculate_course_economics(course.price_eur)
                economics['using_teocoin_discount'] = False
                economics['available_teo_discount'] = cls.calculate_available_discount(
                    course=course, 
                    user=None  # Generic calculation
                )
            
            # Add course-specific information
            economics.update({
                'course_id': course.id,
                'course_title': course.title,
                'teacher_name': course.teacher.get_full_name() or course.teacher.username,
                'category': course.get_category_display(),
            })
            
            return economics
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to calculate course economics: {str(e)}'
            }
    
    @classmethod
    def create_discount_request(cls, course: Course, student: User, teo_to_spend: Decimal) -> Dict[str, Any]:
        """
        Create a discount request for teacher approval
        
        Args:
            course: Course object
            student: Student requesting discount
            teo_to_spend: Amount of TeoCoin student wants to spend
            
        Returns:
            dict: Discount request details for teacher notification
        """
        try:
            # Calculate discount details
            discount_info = cls.calculate_available_discount(course, student, teo_to_spend)
            
            if not discount_info['can_apply_discount']:
                return {
                    'success': False,
                    'error': discount_info.get('error', 'Cannot apply discount')
                }
            
            # Calculate TEO compensation for teacher (125%)
            teo_compensation = teo_to_spend * Decimal('1.25')
            
            # Create notification data
            request_data = {
                'course_id': course.id,
                'course_title': course.title,
                'course_price_eur': float(course.price_eur),
                'student_id': student.id,
                'student_name': student.get_full_name() or student.username,
                'teo_to_spend': float(teo_to_spend),
                'discount_amount_eur': float(discount_info['discount_amount']),
                'final_price_eur': float(discount_info['final_price']),
                'teacher_teo_compensation': float(teo_compensation),
                'discount_percentage': float((discount_info['discount_amount'] / course.price_eur) * 100),
                'expires_at': timezone.now() + timezone.timedelta(hours=2),
                'recommendation': cls._get_discount_recommendation(course.teacher, discount_info['discount_amount'])
            }
            
            return {
                'success': True,
                'request_data': request_data,
                'notification_message': cls._create_notification_message(request_data)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create discount request: {str(e)}'
            }
    
    @classmethod
    def _get_discount_recommendation(cls, teacher: User, discount_amount: Decimal) -> Dict[str, Any]:
        """
        Generate recommendation for teacher whether to accept discount
        """
        # Get teacher's current TEO balance and staking tier
        # This would integrate with your user TEO balance system
        teacher_teo = getattr(teacher, 'teo_balance', Decimal('0'))
        
        # Calculate distance to next staking tier
        tiers = [
            ('silver', 500), ('gold', 1500), 
            ('platinum', 3000), ('diamond', 5000)
        ]
        
        next_tier = None
        for tier_name, required_teo in tiers:
            if teacher_teo < required_teo:
                next_tier = {
                    'name': tier_name,
                    'required_teo': required_teo,
                    'teo_needed': required_teo - teacher_teo
                }
                break
        
        teo_compensation = discount_amount * Decimal('2.5')  # 125% compensation
        
        recommendation = {
            'action': 'accept' if discount_amount <= Decimal('20') else 'consider',
            'reason': 'Good TEO earning opportunity',
            'teo_compensation': float(teo_compensation),
            'next_tier': next_tier,
            'progress_help': float(teo_compensation) if next_tier else 0
        }
        
        if next_tier and teo_compensation >= next_tier['teo_needed'] * Decimal('0.1'):
            recommendation['reason'] = f"Helps reach {next_tier['name']} tier faster!"
            recommendation['action'] = 'strongly_recommend'
        
        return recommendation
    
    @classmethod
    def _create_notification_message(cls, request_data: Dict[str, Any]) -> str:
        """
        Create user-friendly notification message for teacher
        """
        return f"""
🎨 Discount Request for "{request_data['course_title']}"

Student: {request_data['student_name']}
Original Price: €{request_data['course_price_eur']:.2f}
Discount: €{request_data['discount_amount_eur']:.2f} ({request_data['discount_percentage']:.1f}%)
Your TEO Bonus: {request_data['teacher_teo_compensation']:.0f} TEO

💡 {request_data['recommendation']['reason']}

Expires in 2 hours - Tap to respond!
"""

# Create global service instance
teo_discount_service = TeoDiscountService()
