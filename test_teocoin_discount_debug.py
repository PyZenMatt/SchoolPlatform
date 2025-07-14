#!/usr/bin/env python
"""
Debug TeoCoin discount payment flow to find the exact error
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course
from services.db_teocoin_service import DBTeoCoinService
from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
from decimal import Decimal

User = get_user_model()

def test_teocoin_discount_flow():
    """Test the exact same flow as the payment endpoint"""
    print("🔍 TESTING TEOCOIN DISCOUNT FLOW")
    print("=" * 50)
    
    try:
        # Find a user with TEO balance and a course
        db_service = DBTeoCoinService()
        
        # Find user with available balance
        from blockchain.models import DBTeoCoinBalance
        balance_obj = DBTeoCoinBalance.objects.filter(available_balance__gt=10).first()
        
        if not balance_obj:
            print("❌ No user with sufficient TEO balance found")
            return
            
        user = balance_obj.user
        course = Course.objects.first()
        
        if not course:
            print("❌ No courses found")
            return
            
        print(f"👤 User: {user.username}")
        print(f"📚 Course: {course.title}")
        print(f"💰 Course price: €{course.price_eur}")
        
        # Test parameters (same as frontend would send)
        original_price = course.price_eur
        discount_percent = 10  # 10% discount
        
        print(f"🎯 Testing {discount_percent}% discount...")
        
        # Step 1: Check balance
        balance_before = db_service.get_user_balance(user)
        print(f"💳 Balance before: {balance_before['available_balance']} TEO")
        
        # Step 2: Calculate TEO cost (same logic as payment endpoint)
        discount_value_eur = original_price * Decimal(discount_percent) / Decimal('100')
        teo_cost = discount_value_eur  # 1 TEO = 1 EUR
        
        print(f"🔢 Discount value: €{discount_value_eur}")
        print(f"🔢 TEO cost: {teo_cost} TEO")
        
        # Step 3: Check if sufficient balance
        available_teo = balance_before.get('available_balance', 0)
        if available_teo < teo_cost:
            print(f"❌ Insufficient TEO: need {teo_cost}, have {available_teo}")
            return
            
        print("✅ Sufficient TEO balance")
        
        # Step 4: Test TEO deduction
        print("🔄 Testing TEO deduction...")
        success = db_service.deduct_balance(
            user=user,
            amount=teo_cost,
            transaction_type='discount',
            description=f'TeoCoin discount for course: {course.title}',
            course_id=str(course.pk)
        )
        
        if not success:
            print("❌ Failed to deduct TEO")
            return
            
        print("✅ TEO deduction successful")
        
        # Step 5: Test absorption opportunity creation
        print("🔄 Testing absorption opportunity creation...")
        
        try:
            absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
                student=user,
                teacher=course.teacher,
                course=course,
                discount_data={
                    'discount_percentage': discount_percent,
                    'teo_used': float(teo_cost),
                    'discount_amount_eur': float(discount_value_eur),
                    'course_price_eur': float(original_price)
                }
            )
            
            print(f"✅ Absorption opportunity created: ID {absorption.pk}")
            print(f"   Status: {absorption.status}")
            print(f"   Teacher: {absorption.teacher.username}")
            print(f"   TEO reward: {absorption.final_teacher_teo}")
            
        except Exception as abs_error:
            print(f"❌ Absorption creation failed: {abs_error}")
            import traceback
            traceback.print_exc()
            return
        
        # Step 6: Check balance after
        balance_after = db_service.get_user_balance(user)
        teo_deducted = balance_before['available_balance'] - balance_after['available_balance']
        
        print(f"💳 Balance after: {balance_after['available_balance']} TEO")
        print(f"📊 TEO deducted: {teo_deducted} TEO")
        
        print("\n🎉 ALL STEPS SUCCESSFUL!")
        print("The payment flow should work correctly.")
        
    except Exception as e:
        print(f"❌ Error in discount flow: {e}")
        import traceback
        traceback.print_exc()

def test_user_role_check():
    """Check if user role issues are causing problems"""
    print("\n" + "=" * 50)
    print("🔍 TESTING USER ROLES")
    print("=" * 50)
    
    try:
        # Find users with balance
        from blockchain.models import DBTeoCoinBalance
        balance_objs = DBTeoCoinBalance.objects.filter(available_balance__gt=0)[:5]
        
        for balance_obj in balance_objs:
            user = balance_obj.user
            print(f"\n👤 User: {user.username}")
            print(f"   Staff: {user.is_staff}")
            print(f"   Superuser: {user.is_superuser}")
            print(f"   Role: {getattr(user, 'role', 'No role attribute')}")
            print(f"   TEO Balance: {balance_obj.available_balance}")
            
            # Check if user is a teacher
            has_teacher_profile = hasattr(user, 'teacher_profile')
            print(f"   Has teacher_profile: {has_teacher_profile}")
            
    except Exception as e:
        print(f"❌ Error checking user roles: {e}")

if __name__ == "__main__":
    test_teocoin_discount_flow()
    test_user_role_check()
