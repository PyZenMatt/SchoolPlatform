#!/usr/bin/env python3
"""
End-to-End TeoCoin Discount Test
Simulates the complete discount request and teacher decision process
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.utils import timezone
from users.models import User
from courses.models import Course, TeacherDiscountDecision
from notifications.models import Notification
from services.teocoin_discount_service import teocoin_discount_service
from blockchain.blockchain import TeoCoinService


def simulate_student_discount_request():
    """Simulate a complete student discount request workflow"""
    print("🎓 SIMULATING STUDENT DISCOUNT REQUEST")
    print("=" * 50)
    
    # Find existing users
    try:
        student = User.objects.filter(role='student').first()
        teacher = User.objects.filter(role='teacher').first()
        
        if not student or not teacher:
            print("❌ Need existing student and teacher users")
            return False
            
        print(f"👨‍🎓 Student: {student.username} ({student.email})")
        print(f"👩‍🏫 Teacher: {teacher.username} ({teacher.email})")
        
        # Use actual wallet addresses if available
        student_address = getattr(student, 'wallet_address', None) or "0x1111111111111111111111111111111111111111"
        teacher_address = getattr(teacher, 'wallet_address', None) or "0x2222222222222222222222222222222222222222"
        
        print(f"💳 Student Wallet: {student_address}")
        print(f"💳 Teacher Wallet: {teacher_address}")
        print()
        
    except Exception as e:
        print(f"❌ User setup failed: {e}")
        return False
    
    # Test parameters
    course_id = 1
    course_price = Decimal('50.00')  # €50 course
    discount_percent = 15  # 15% discount
    
    print(f"📚 Course ID: {course_id}")
    print(f"💰 Course Price: €{course_price}")
    print(f"🏷️ Discount: {discount_percent}%")
    print()
    
    # Check TEO requirements
    print("🔍 CHECKING REQUIREMENTS")
    try:
        teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(course_price, discount_percent)
        teo_required = teo_cost / 10**18
        bonus_required = teacher_bonus / 10**18
        
        print(f"   TEO Required from Student: {teo_required:.2f} TEO")
        print(f"   Bonus for Teacher: {bonus_required:.2f} TEO")
        print(f"   Total Teacher Gets: {teo_required + bonus_required:.2f} TEO")
        print()
        
        # Check balances
        teo_service = TeoCoinService()
        student_balance = teo_service.get_balance(student_address)
        reward_pool_balance = teo_service.get_reward_pool_balance()
        
        print(f"   💰 Student Balance: {student_balance:.2f} TEO")
        print(f"   💰 Reward Pool Balance: {reward_pool_balance:.2f} TEO")
        
        if student_balance < teo_required:
            shortage = float(teo_required) - float(student_balance)
            print(f"   ⚠️ Student needs {shortage:.2f} more TEO")
            print("   🚀 Proceeding with simulation anyway...")
        else:
            print(f"   ✅ Student has sufficient TEO")
            
        print()
        
    except Exception as e:
        print(f"   ❌ Requirements check failed: {e}")
        return False
    
    # Simulate discount request (this would normally come from frontend)
    print("📝 SIMULATING DISCOUNT REQUEST")
    try:
        # Generate mock signature (normally done by MetaMask)
        mock_signature = "0x" + "a" * 130  # Mock signature
        
        print(f"   Student Signature: {mock_signature[:20]}...")
        print(f"   Creating discount request...")
        
        # This would normally happen when student completes payment
        # We'll simulate by creating the TeacherDiscountDecision directly
        
        # Check if course exists
        course = Course.objects.filter(id=course_id).first()
        if not course:
            print(f"   ⚠️ Course {course_id} not found, creating mock course")
            course_title = f"Test Course {course_id}"
        else:
            course_title = course.title
            print(f"   📚 Found course: {course_title}")
        
        # Create discount decision record
        decision = TeacherDiscountDecision.objects.create(
            teacher=teacher,
            student=student,
            course_id=course_id,
            course_price=course_price,
            discount_percentage=discount_percent,
            teo_cost=teo_cost,
            teacher_bonus=teacher_bonus,
            teacher_commission_rate=50.00,  # Mock 50% commission
            teacher_staking_tier="Bronze",
            expires_at=timezone.now() + timedelta(hours=2)
        )
        
        print(f"   ✅ Created TeacherDiscountDecision #{decision.pk}")
        
        # Send teacher notification
        from notifications.services import teocoin_notification_service
        
        notification_sent = teocoin_notification_service.notify_teacher_discount_pending(
            teacher=teacher,
            student=student,
            course_title=course_title,
            discount_percent=discount_percent,
            teo_cost=teo_required,
            teacher_bonus=bonus_required,
            request_id=decision.pk,
            expires_at=decision.expires_at
        )
        
        if notification_sent:
            print(f"   ✅ Teacher notification sent")
            
            # Show the notification
            notification = Notification.objects.filter(
                user=teacher,
                notification_type='teocoin_discount_pending'
            ).last()
            
            if notification:
                print(f"   📱 Notification Message:")
                print(f"   {notification.message}")
                print()
        else:
            print(f"   ❌ Teacher notification failed")
            
    except Exception as e:
        print(f"   ❌ Discount request simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Show next steps
    print("⏰ NEXT STEPS (Teacher has 2 hours to decide):")
    print("1. Teacher receives notification")
    print("2. Teacher chooses:")
    print(f"   Option A: Accept {teo_required:.2f} TEO + {bonus_required:.2f} bonus = {teo_required + bonus_required:.2f} TEO total")
    print(f"   Option B: Keep EUR commission (TEO goes to platform)")
    print("3. If no choice in 2 hours: Auto-EUR selection")
    print()
    
    print("✅ DISCOUNT REQUEST SIMULATION COMPLETE")
    print(f"📋 TeacherDiscountDecision ID: {decision.pk}")
    print(f"⏰ Expires at: {decision.expires_at}")
    
    return True


def show_pending_teacher_decisions():
    """Show all pending teacher discount decisions"""
    print("\n📋 PENDING TEACHER DISCOUNT DECISIONS")
    print("=" * 40)
    
    pending_decisions = TeacherDiscountDecision.objects.filter(
        decision='pending',
        expires_at__gt=timezone.now()
    )
    
    if not pending_decisions.exists():
        print("No pending discount decisions")
        return
    
    for decision in pending_decisions:
        time_left = decision.expires_at - timezone.now()
        hours_left = time_left.total_seconds() / 3600
        
        print(f"Decision #{decision.pk}:")
        print(f"  Teacher: {decision.teacher.username}")
        print(f"  Student: {decision.student.username}")
        print(f"  Course Price: €{decision.course_price}")
        print(f"  Discount: {decision.discount_percentage}%")
        print(f"  TEO Amount: {decision.teo_cost / 10**18:.2f} TEO")
        print(f"  Teacher Bonus: {decision.teacher_bonus / 10**18:.2f} TEO")
        print(f"  Time Left: {hours_left:.1f} hours")
        print(f"  Expires: {decision.expires_at}")
        print()


if __name__ == "__main__":
    try:
        print("🚀 STARTING END-TO-END DISCOUNT TEST\n")
        
        # Show current pending decisions
        show_pending_teacher_decisions()
        
        # Simulate new discount request
        success = simulate_student_discount_request()
        
        if success:
            # Show all pending decisions
            show_pending_teacher_decisions()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
