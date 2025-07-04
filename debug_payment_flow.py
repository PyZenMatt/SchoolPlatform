#!/usr/bin/env python3
"""
Debug the exact payment flow to see where TeoCoin transfer fails
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, CourseEnrollment
from services.teocoin_discount_service import teocoin_discount_service

User = get_user_model()

def simulate_payment_flow():
    """Simulate the exact payment flow with detailed logging"""
    print("🔍 Simulating Payment Flow with TeoCoin Discount")
    
    # Get student and course
    student = User.objects.filter(
        role='student', 
        wallet_address__isnull=False
    ).first()
    
    if not student:
        print("❌ No student with wallet found")
        return
    
    course = Course.objects.filter(
        is_approved=True,
        teocoin_discount_percent__gt=0
    ).first()
    
    if not course:
        print("❌ No course with TeoCoin discount found")
        return
    
    print(f"Student: {student.username}")
    print(f"Wallet: {student.wallet_address}")
    print(f"Course: {course.title}")
    print(f"Course price: €{course.price_eur}")
    print(f"Discount %: {course.teocoin_discount_percent}%")
    
    # Get TeoCoin service
    teo_service = teocoin_discount_service.teocoin_service
    
    # Check wallet balance
    wallet_address = student.wallet_address
    initial_balance = teo_service.get_balance(wallet_address)
    print(f"Initial TEO balance: {initial_balance}")
    
    # Calculate discount
    discount_percent = course.teocoin_discount_percent
    course_price = course.price_eur
    discount_amount_eur = course_price * Decimal(discount_percent) / 100
    teo_cost_decimal = course.get_teocoin_discount_amount()  # Use course method
    
    print(f"Discount amount (EUR): €{discount_amount_eur}")
    print(f"TEO cost: {teo_cost_decimal} TEO")
    
    # Check if sufficient balance
    required_teo = float(teo_cost_decimal)
    if initial_balance < required_teo:
        print(f"❌ Insufficient balance. Required: {required_teo}, Available: {initial_balance}")
        return
    
    print(f"✅ Sufficient balance available")
    
    # Check reward pool
    reward_pool_balance = teo_service.get_reward_pool_balance()
    print(f"Reward pool balance: {reward_pool_balance} TEO")
    
    # Get reward pool address
    from django.conf import settings
    reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
    
    if not reward_pool_address:
        print("❌ Reward pool address not configured")
        return
    
    print(f"Reward pool address: {reward_pool_address}")
    
    # Simulate the transfer attempt
    print(f"\n🔄 Simulating TEO transfer...")
    print(f"Calling: teo_service.transfer_with_reward_pool_gas(")
    print(f"  from_address='{wallet_address}',")
    print(f"  to_address='{reward_pool_address}',")
    print(f"  amount={Decimal(str(required_teo))}")
    print(f")")
    
    # Check if the method exists
    if not hasattr(teo_service, 'transfer_with_reward_pool_gas'):
        print("❌ Transfer method not available")
        return
    
    print("✅ Transfer method exists")
    
    # Try the actual transfer
    try:
        print("\n🚀 Executing actual transfer...")
        transfer_result = teo_service.transfer_with_reward_pool_gas(
            wallet_address,
            reward_pool_address,
            Decimal(str(required_teo))
        )
        
        print(f"Transfer result: {transfer_result}")
        print(f"Transfer result type: {type(transfer_result)}")
        
        if transfer_result:
            print("✅ Transfer appears successful!")
            
            # Check new balance
            new_balance = teo_service.get_balance(wallet_address)
            print(f"New balance: {new_balance} TEO")
            print(f"Difference: {initial_balance - new_balance} TEO")
            
            if abs((initial_balance - new_balance) - required_teo) < 0.01:
                print("✅ Balance deduction matches expected amount")
            else:
                print("❌ Balance deduction doesn't match expected amount")
        else:
            print("❌ Transfer returned None/False")
            
    except Exception as e:
        print(f"❌ Transfer failed with exception: {e}")
        import traceback
        traceback.print_exc()
        
        # Check if balance changed anyway
        try:
            new_balance = teo_service.get_balance(wallet_address)
            if new_balance != initial_balance:
                print(f"⚠️ Balance changed despite exception: {initial_balance} → {new_balance}")
            else:
                print(f"✅ Balance unchanged after exception: {new_balance}")
        except:
            print("❌ Could not check balance after exception")

def check_why_no_deduction():
    """Check why previous TeoCoin enrollments didn't deduct tokens"""
    print("\n🔍 Analyzing Previous TeoCoin Enrollments")
    
    # Get TeoCoin enrollments
    teocoin_enrollments = CourseEnrollment.objects.filter(
        payment_method='teocoin_discount'
    ).order_by('-enrolled_at')
    
    teo_service = teocoin_discount_service.teocoin_service
    
    for enrollment in teocoin_enrollments:
        print(f"\n📚 Enrollment {enrollment.pk}:")
        print(f"  Student: {enrollment.student.username if enrollment.student else 'Unknown'}")
        print(f"  Course: {enrollment.course.title}")
        print(f"  Enrolled: {enrollment.enrolled_at}")
        
        if enrollment.student and hasattr(enrollment.student, 'wallet_address'):
            wallet_address = enrollment.student.wallet_address
            if wallet_address:
                current_balance = teo_service.get_balance(wallet_address)
                print(f"  Current wallet balance: {current_balance} TEO")
                
                # Calculate what should have been deducted
                course = enrollment.course
                teo_cost = course.get_teocoin_discount_amount()
                print(f"  Should have deducted: {teo_cost} TEO")
                
                # If this was recent, the balance should be lower
                print(f"  ❓ Was {teo_cost} TEO actually deducted?")
            else:
                print(f"  ❌ No wallet address")
        else:
            print(f"  ❌ No student or wallet info")

if __name__ == "__main__":
    simulate_payment_flow()
    check_why_no_deduction()
