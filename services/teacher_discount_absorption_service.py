"""
Teacher Discount Absorption Service
Handles the business logic for teachers choosing between EUR vs TEO compensation
"""
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from rewards.models import TeacherDiscountAbsorption
from services.db_teocoin_service import DBTeoCoinService


class TeacherDiscountAbsorptionService:
    """
    Service for managing teacher discount absorption choices
    """
    
    @staticmethod
    def create_absorption_opportunity(student, teacher, course, discount_data):
        """
        Create a new discount absorption opportunity when a student uses TeoCoin discount
        
        Args:
            student: User who purchased the course
            teacher: User who owns the course
            course: Course that was purchased
            discount_data: Dict containing discount information
                - discount_percentage: 5, 10, or 15
                - teo_used: Amount of TEO used by student
                - discount_amount_eur: EUR value of discount
                - course_price_eur: Original course price
        """
        teo_service = DBTeoCoinService()
        
        # Get teacher's current tier and commission rate
        teacher_balance = teo_service.get_user_balance(teacher)
        teacher_tier = teacher_balance.get('tier', 0)
        
        # Commission rates by tier (platform commission, so teacher gets 100 - this)
        tier_commission_rates = {
            0: 50,  # Bronze: Teacher gets 50%, Platform gets 50%
            1: 55,  # Silver: Teacher gets 55%, Platform gets 45%
            2: 60,  # Gold: Teacher gets 60%, Platform gets 40%
            3: 65,  # Platinum: Teacher gets 65%, Platform gets 35%
            4: 75,  # Diamond: Teacher gets 75%, Platform gets 25%
        }
        
        teacher_commission_rate = tier_commission_rates.get(int(teacher_tier), 50)
        
        # Create the absorption opportunity
        absorption = TeacherDiscountAbsorption.objects.create(
            teacher=teacher,
            course=course,
            student=student,
            course_price_eur=Decimal(str(discount_data['course_price_eur'])),
            discount_percentage=discount_data['discount_percentage'],
            teo_used_by_student=Decimal(str(discount_data['teo_used'])),
            discount_amount_eur=Decimal(str(discount_data['discount_amount_eur'])),
            teacher_tier=teacher_tier,
            teacher_commission_rate=Decimal(str(teacher_commission_rate))
        )
        
        # Calculate both options
        absorption.calculate_options()
        absorption.save()
        
        return absorption
    
    @staticmethod
    def process_teacher_choice(absorption_id, choice, teacher):
        """
        Process teacher's choice for discount absorption
        
        Args:
            absorption_id: ID of the TeacherDiscountAbsorption
            choice: 'absorb' or 'refuse'
            teacher: Teacher making the choice
        """
        try:
            absorption = TeacherDiscountAbsorption.objects.get(
                id=absorption_id,
                teacher=teacher,
                status='pending'
            )
        except TeacherDiscountAbsorption.DoesNotExist:
            raise ValueError("Invalid absorption opportunity or already processed")
        
        if absorption.is_expired:
            absorption.auto_expire()
            raise ValueError("This opportunity has expired")
        
        # Process the choice
        absorption.make_choice(choice)
        
        # If teacher chose to absorb, add TEO to their balance
        if choice == 'absorb' and absorption.status == 'absorbed':
            teo_service = DBTeoCoinService()
            teo_service.add_balance(
                user=teacher,
                amount=Decimal(str(absorption.final_teacher_teo)),
                transaction_type='discount_absorption',
                description=f"Absorbed discount for course: {absorption.course.title}"
            )
        
        return absorption
    
    @staticmethod
    def get_pending_absorptions(teacher):
        """
        Get all pending absorption opportunities for a teacher
        """
        return TeacherDiscountAbsorption.objects.filter(
            teacher=teacher,
            status='pending',
            expires_at__gt=timezone.now()
        ).select_related('course', 'student').order_by('expires_at')
    
    @staticmethod
    def get_teacher_absorption_history(teacher, days=30):
        """
        Get teacher's absorption history for the last N days
        """
        since_date = timezone.now() - timedelta(days=days)
        
        return TeacherDiscountAbsorption.objects.filter(
            teacher=teacher,
            created_at__gte=since_date
        ).select_related('course', 'student').order_by('-created_at')
    
    @staticmethod
    def get_teacher_absorption_stats(teacher, days=30):
        """
        Get statistics about teacher's absorption activity
        """
        since_date = timezone.now() - timedelta(days=days)
        
        absorptions = TeacherDiscountAbsorption.objects.filter(
            teacher=teacher,
            created_at__gte=since_date
        )
        
        total_opportunities = absorptions.count()
        absorbed_count = absorptions.filter(status='absorbed').count()
        refused_count = absorptions.filter(status='refused').count()
        expired_count = absorptions.filter(status='expired').count()
        pending_count = absorptions.filter(status='pending').count()
        
        # Calculate totals
        total_eur_earned = sum(
            a.final_teacher_eur for a in absorptions 
            if a.final_teacher_eur is not None
        )
        total_teo_earned = sum(
            a.final_teacher_teo for a in absorptions
        )
        
        absorption_rate = (absorbed_count / total_opportunities * 100) if total_opportunities > 0 else 0
        
        return {
            'total_opportunities': total_opportunities,
            'absorbed_count': absorbed_count,
            'refused_count': refused_count,
            'expired_count': expired_count,
            'pending_count': pending_count,
            'absorption_rate': round(absorption_rate, 1),
            'total_eur_earned': total_eur_earned,
            'total_teo_earned': total_teo_earned,
            'days': days
        }
    
    @staticmethod
    def expire_old_absorptions():
        """
        Auto-expire old pending absorptions (to be run as a cron job)
        """
        expired_absorptions = TeacherDiscountAbsorption.objects.filter(
            status='pending',
            expires_at__lt=timezone.now()
        )
        
        count = 0
        for absorption in expired_absorptions:
            absorption.auto_expire()
            count += 1
        
        return count
    
    @staticmethod
    def calculate_platform_savings():
        """
        Calculate how much money the platform saved through teacher absorptions
        """
        absorbed_absorptions = TeacherDiscountAbsorption.objects.filter(
            status='absorbed'
        )
        
        total_discount_absorbed = sum(
            a.discount_amount_eur for a in absorbed_absorptions
        )
        
        return {
            'total_discount_absorbed_eur': total_discount_absorbed,
            'absorption_count': absorbed_absorptions.count()
        }
