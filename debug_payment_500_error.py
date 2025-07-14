#!/usr/bin/env python
"""
Debug script to find the exact error in the payment flow
Run this after the payment error to see what went wrong
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def debug_payment_error():
    """Debug the exact payment error that's happening"""
    print("🔍 DEBUGGING PAYMENT ERROR")
    print("=" * 50)
    
    try:
        from django.contrib.auth import get_user_model
        from courses.models import Course
        from services.db_teocoin_service import DBTeoCoinService
        from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
        from decimal import Decimal
        
        User = get_user_model()
        
        # Get course 23 (the one from the error)
        try:
            course = Course.objects.get(pk=23)
            print(f"✅ Found course 23: {course.title}")
            print(f"   Teacher: {course.teacher.username if course.teacher else 'No teacher'}")
            print(f"   Price: €{course.price_eur}")
        except Course.DoesNotExist:
            print("❌ Course 23 not found")
            return
        
        # Find a user with TEO balance for testing
        from blockchain.models import DBTeoCoinBalance
        balance_obj = DBTeoCoinBalance.objects.filter(available_balance__gt=5).first()
        
        if not balance_obj:
            print("❌ No user with TEO balance found")
            return
            
        user = balance_obj.user
        print(f"✅ Found user with balance: {user.username}")
        print(f"   Balance: {balance_obj.available_balance} TEO")
        
        # Test the exact same parameters as the payment
        original_price = course.price_eur
        discount_percent = 10
        discount_value_eur = original_price * Decimal(discount_percent) / Decimal('100')
        teo_cost = discount_value_eur
        
        print(f"")
        print(f"🧮 Payment Calculation:")
        print(f"   Original price: €{original_price}")
        print(f"   Discount: {discount_percent}%")
        print(f"   Discount value: €{discount_value_eur}")
        print(f"   TEO cost: {teo_cost} TEO")
        
        # Test each step that could fail
        
        # Step 1: DB Service creation
        print(f"")
        print(f"🔧 Step 1: Creating DB service...")
        db_teo_service = DBTeoCoinService()
        print(f"✅ DB service created")
        
        # Step 2: Balance check
        print(f"🔧 Step 2: Checking balance...")
        student_balance_data = db_teo_service.get_user_balance(user)
        available_teo = student_balance_data.get('available_balance', 0)
        print(f"✅ Balance check: {available_teo} TEO available")
        
        # Step 3: TEO deduction
        print(f"🔧 Step 3: Testing TEO deduction...")
        balance_before = available_teo
        success = db_teo_service.deduct_balance(
            user=user,
            amount=teo_cost,
            transaction_type='discount_test',
            description=f'Test TeoCoin discount for course: {course.title}',
            course_id=str(course.pk)
        )
        
        if success:
            print(f"✅ TEO deduction successful")
            
            # Check balance after
            balance_after_data = db_teo_service.get_user_balance(user)
            balance_after = balance_after_data.get('available_balance', 0)
            deducted = balance_before - balance_after
            print(f"   Deducted: {deducted} TEO")
        else:
            print(f"❌ TEO deduction failed")
            return
        
        # Step 4: Teacher check
        print(f"🔧 Step 4: Checking teacher...")
        teacher = course.teacher
        if not teacher:
            print(f"❌ Course has no teacher assigned!")
            return
        print(f"✅ Teacher found: {teacher.username}")
        
        # Step 5: Absorption opportunity creation (this is likely where it fails)
        print(f"🔧 Step 5: Testing absorption opportunity creation...")
        
        try:
            discount_data = {
                'discount_percentage': discount_percent,
                'teo_used': float(teo_cost),
                'discount_amount_eur': float(discount_value_eur),
                'course_price_eur': float(original_price)
            }
            
            print(f"   Discount data: {discount_data}")
            
            absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
                student=user,
                teacher=teacher,
                course=course,
                discount_data=discount_data
            )
            
            print(f"✅ Absorption opportunity created successfully!")
            print(f"   ID: {absorption.pk}")
            print(f"   Status: {absorption.status}")
            print(f"   Teacher TEO: {absorption.final_teacher_teo}")
            print(f"   Teacher EUR: {absorption.final_teacher_eur}")
            
        except Exception as absorption_error:
            print(f"❌ ABSORPTION CREATION FAILED - THIS IS THE ERROR!")
            print(f"   Error: {absorption_error}")
            import traceback
            traceback.print_exc()
            
            # This is the actual error causing the 500 response
            print(f"")
            print(f"🎯 ROOT CAUSE FOUND:")
            print(f"   The payment flow fails at absorption opportunity creation")
            print(f"   TEO is deducted successfully (which you observed)")
            print(f"   But then the absorption creation fails, causing 500 error")
            
            return
            
        print(f"")
        print(f"🎉 ALL STEPS SUCCESSFUL!")
        print(f"If this test passes, the payment should work.")
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_payment_error()
