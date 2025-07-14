#!/usr/bin/env python
"""
Complete End-to-End TeoCoin Discount Flow Test
Tests: Payment → Notification → Teacher Choice → TEO Transfer
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_complete_end_to_end_flow():
    """Test the complete flow from student payment to teacher receiving TEO"""
    print("🚀 TESTING COMPLETE END-TO-END TEOCOIN FLOW")
    print("=" * 70)
    
    try:
        from django.contrib.auth import get_user_model
        from courses.models import Course, CourseEnrollment
        from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
        from services.db_teocoin_service import DBTeoCoinService
        from rewards.models import TeacherDiscountAbsorption
        from notifications.models import Notification
        from decimal import Decimal
        
        User = get_user_model()
        
        # STEP 1: Setup - Find course and users
        print("\n📋 STEP 1: SETUP")
        print("-" * 30)
        
        course = Course.objects.filter(teacher__isnull=False).first()
        if not course:
            print("❌ No course with teacher found")
            return False
            
        teacher = course.teacher
        print(f"✅ Course: {course.title}")
        print(f"✅ Teacher: {teacher.username}")
        print(f"✅ Course price: €{course.price_eur}")
        
        # Find or create a student with TEO balance
        from blockchain.models import DBTeoCoinBalance
        balance_obj = DBTeoCoinBalance.objects.filter(available_balance__gt=50).first()
        
        if not balance_obj:
            # Create a test student with TEO balance
            student = User.objects.create_user(
                username='test_student_flow',
                email='test.student.flow@example.com',
                password='testpass123'
            )
            
            db_service = DBTeoCoinService()
            db_service.add_balance(
                user=student,
                amount=Decimal('100.00'),
                transaction_type='test_credit',
                description='Test balance for flow testing'
            )
            print(f"✅ Created test student: {student.username} with 100 TEO")
        else:
            student = balance_obj.user
            print(f"✅ Using existing student: {student.username}")
        
        # STEP 2: Check initial balances
        print("\n💰 STEP 2: INITIAL BALANCES")
        print("-" * 30)
        
        db_service = DBTeoCoinService()
        student_balance_before = db_service.get_user_balance(student)
        teacher_balance_before = db_service.get_user_balance(teacher)
        
        print(f"Student initial balance: {student_balance_before['available_balance']} TEO")
        print(f"Teacher initial balance: {teacher_balance_before['available_balance']} TEO")
        
        # STEP 3: Simulate student payment with discount
        print("\n🛒 STEP 3: STUDENT PAYMENT WITH DISCOUNT")
        print("-" * 30)
        
        discount_percent = 15
        original_price = course.price_eur
        discount_value_eur = original_price * Decimal(discount_percent) / Decimal('100')
        teo_cost = discount_value_eur  # 1:1 ratio
        
        print(f"Original price: €{original_price}")
        print(f"Discount: {discount_percent}% = €{discount_value_eur}")
        print(f"TEO cost: {teo_cost} TEO")
        print(f"Final price: €{original_price - discount_value_eur}")
        
        # Deduct TEO from student
        success = db_service.deduct_balance(
            user=student,
            amount=teo_cost,
            transaction_type='discount',
            description=f'TeoCoin discount for course: {course.title}',
            course_id=str(course.pk)
        )
        
        if not success:
            print("❌ TEO deduction failed")
            return False
            
        student_balance_after_payment = db_service.get_user_balance(student)
        teo_deducted = student_balance_before['available_balance'] - student_balance_after_payment['available_balance']
        print(f"✅ TEO deducted from student: {teo_deducted} TEO")
        
        # STEP 4: Create absorption opportunity (should trigger notification)
        print("\n🔔 STEP 4: CREATE ABSORPTION OPPORTUNITY & NOTIFICATION")
        print("-" * 30)
        
        notifications_before = Notification.objects.filter(user=teacher).count()
        
        absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
            student=student,
            teacher=teacher,
            course=course,
            discount_data={
                'discount_percentage': discount_percent,
                'teo_used': float(teo_cost),
                'discount_amount_eur': float(discount_value_eur),
                'course_price_eur': float(original_price)
            }
        )
        
        notifications_after = Notification.objects.filter(user=teacher).count()
        new_notifications = notifications_after - notifications_before
        
        print(f"✅ Absorption opportunity created (ID: {absorption.pk})")
        print(f"✅ Teacher notifications: {notifications_before} → {notifications_after} (+{new_notifications})")
        print(f"   Status: {absorption.status}")
        print(f"   Option A (EUR): Teacher gets €{absorption.option_a_teacher_eur}")
        print(f"   Option B (TEO): Teacher gets {absorption.option_b_teacher_teo} TEO")
        print(f"   Expires: {absorption.expires_at}")
        
        # Check the notification content
        latest_notification = Notification.objects.filter(
            user=teacher,
            notification_type='teocoin_discount_pending'
        ).order_by('-created_at').first()
        
        if latest_notification:
            print(f"✅ Notification created:")
            print(f"   Type: {latest_notification.notification_type}")
            print(f"   Message preview: {latest_notification.message[:100]}...")
        else:
            print("⚠️  No notification found")
        
        # STEP 5: Test teacher choice - ABSORB (choose TEO)
        print("\n🎯 STEP 5: TEACHER CHOOSES TEO (ABSORB DISCOUNT)")
        print("-" * 30)
        
        teacher_balance_before_choice = db_service.get_user_balance(teacher)
        student_notifications_before = Notification.objects.filter(user=student).count()
        
        # Teacher chooses to absorb the discount for TEO
        processed_absorption = TeacherDiscountAbsorptionService.process_teacher_choice(
            absorption_id=absorption.pk,
            choice='absorb',
            teacher=teacher
        )
        
        teacher_balance_after_choice = db_service.get_user_balance(teacher)
        student_notifications_after = Notification.objects.filter(user=student).count()
        
        teo_gained = teacher_balance_after_choice['available_balance'] - teacher_balance_before_choice['available_balance']
        student_new_notifications = student_notifications_after - student_notifications_before
        
        print(f"✅ Teacher choice processed:")
        print(f"   Choice: {processed_absorption.status}")
        print(f"   Teacher TEO gained: {teo_gained} TEO")
        print(f"   Expected TEO: {processed_absorption.final_teacher_teo} TEO")
        print(f"   Match: {'✅' if abs(float(teo_gained) - float(processed_absorption.final_teacher_teo)) < 0.01 else '❌'}")
        print(f"   Student notifications: {student_notifications_before} → {student_notifications_after} (+{student_new_notifications})")
        
        # Check student notification
        student_latest_notification = Notification.objects.filter(
            user=student,
            notification_type='teocoin_discount_accepted'
        ).order_by('-created_at').first()
        
        if student_latest_notification:
            print(f"✅ Student notification created:")
            print(f"   Type: {student_latest_notification.notification_type}")
            print(f"   Message preview: {student_latest_notification.message[:100]}...")
        else:
            print("⚠️  No student notification found")
        
        # Check for teacher staking reminder notification
        teacher_staking_notification = Notification.objects.filter(
            user=teacher,
            notification_type='bonus_received'
        ).order_by('-created_at').first()
        
        if teacher_staking_notification:
            print(f"✅ Teacher staking reminder created:")
            print(f"   Message preview: {teacher_staking_notification.message[:100]}...")
        
        # STEP 6: Verify transaction records
        print("\n📊 STEP 6: VERIFY TRANSACTION RECORDS")
        print("-" * 30)
        
        # Check teacher's recent transactions
        teacher_transactions = db_service.get_user_transactions(teacher, limit=5)
        recent_absorption_tx = None
        
        for tx in teacher_transactions:
            if tx['type'] == 'discount_absorption':
                recent_absorption_tx = tx
                break
        
        if recent_absorption_tx:
            print(f"✅ Teacher absorption transaction found:")
            print(f"   Amount: {recent_absorption_tx['amount']} TEO")
            print(f"   Description: {recent_absorption_tx['description']}")
        else:
            print("⚠️  No absorption transaction found for teacher")
        
        # Check student's discount transaction
        student_transactions = db_service.get_user_transactions(student, limit=5)
        recent_discount_tx = None
        
        for tx in student_transactions:
            if tx['type'] == 'discount' and 'course' in tx['description'].lower():
                recent_discount_tx = tx
                break
        
        if recent_discount_tx:
            print(f"✅ Student discount transaction found:")
            print(f"   Amount: {recent_discount_tx['amount']} TEO")
            print(f"   Description: {recent_discount_tx['description']}")
        else:
            print("⚠️  No discount transaction found for student")
        
        # STEP 7: Final balance verification
        print("\n💰 STEP 7: FINAL BALANCE VERIFICATION")
        print("-" * 30)
        
        student_final_balance = db_service.get_user_balance(student)
        teacher_final_balance = db_service.get_user_balance(teacher)
        
        print(f"Student balance: {student_balance_before['available_balance']} → {student_final_balance['available_balance']} TEO")
        print(f"Teacher balance: {teacher_balance_before['available_balance']} → {teacher_final_balance['available_balance']} TEO")
        
        student_net_change = student_final_balance['available_balance'] - student_balance_before['available_balance']
        teacher_net_change = teacher_final_balance['available_balance'] - teacher_balance_before['available_balance']
        
        print(f"Student net change: {student_net_change} TEO")
        print(f"Teacher net change: {teacher_net_change} TEO")
        
        # STEP 8: Test summary
        print("\n🎯 COMPLETE FLOW TEST SUMMARY")
        print("=" * 50)
        
        all_checks_passed = True
        
        # Check 1: TEO deducted from student
        check1 = abs(float(student_net_change)) >= float(teo_cost) * 0.9  # Allow for small floating point differences
        print(f"1. Student TEO deducted: {'✅' if check1 else '❌'}")
        if not check1:
            all_checks_passed = False
        
        # Check 2: Absorption opportunity created
        check2 = absorption.pk is not None and processed_absorption.status == 'absorbed'
        print(f"2. Absorption opportunity created: {'✅' if check2 else '❌'}")
        if not check2:
            all_checks_passed = False
        
        # Check 3: Teacher notification sent
        check3 = new_notifications > 0
        print(f"3. Teacher notification sent: {'✅' if check3 else '❌'}")
        if not check3:
            all_checks_passed = False
        
        # Check 4: Teacher received TEO
        check4 = teacher_net_change > 0
        print(f"4. Teacher received TEO: {'✅' if check4 else '❌'}")
        if not check4:
            all_checks_passed = False
        
        # Check 5: Student received notification about teacher choice
        check5 = student_new_notifications > 0
        print(f"5. Student notified of teacher choice: {'✅' if check5 else '❌'}")
        if not check5:
            all_checks_passed = False
        
        # Check 6: Transaction records created
        check6 = recent_absorption_tx is not None and recent_discount_tx is not None
        print(f"6. Transaction records created: {'✅' if check6 else '❌'}")
        if not check6:
            all_checks_passed = False
        
        print(f"\n🎉 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_checks_passed else '❌ SOME TESTS FAILED'}")
        
        if all_checks_passed:
            print("\n🚀 Complete TeoCoin discount flow is working perfectly!")
            print("   • Student can pay with TEO discount")
            print("   • Teacher receives notification immediately")
            print("   • Teacher can choose TEO vs EUR")
            print("   • TEO is transferred to teacher when absorbed")
            print("   • Both parties receive notification confirmations")
            print("   • All transactions are recorded properly")
        
        return all_checks_passed
        
    except Exception as e:
        print(f"❌ Complete flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_teacher_refuses_teo():
    """Test what happens when teacher refuses TEO and chooses EUR"""
    print("\n\n🔄 TESTING TEACHER REFUSES TEO SCENARIO")
    print("=" * 50)
    
    try:
        from django.contrib.auth import get_user_model
        from courses.models import Course
        from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
        from services.db_teocoin_service import DBTeoCoinService
        from rewards.models import TeacherDiscountAbsorption
        from notifications.models import Notification
        from decimal import Decimal
        
        User = get_user_model()
        
        # Find existing absorption opportunity
        pending_absorption = TeacherDiscountAbsorption.objects.filter(
            status='pending'
        ).first()
        
        if not pending_absorption:
            print("⚠️  No pending absorption found, creating one...")
            # Create a quick test absorption
            course = Course.objects.filter(teacher__isnull=False).first()
            if not course:
                print("❌ No course with teacher found")
                return False
                
            teacher = course.teacher
            student = User.objects.exclude(pk=teacher.pk).first()
            
            if not student:
                print("❌ No student found")
                return False
            
            pending_absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
                student=student,
                teacher=teacher,
                course=course,
                discount_data={
                    'discount_percentage': 10,
                    'teo_used': 24.0,
                    'discount_amount_eur': 24.0,
                    'course_price_eur': 240.0
                }
            )
        
        teacher = pending_absorption.teacher
        student = pending_absorption.student
        
        print(f"Testing with absorption ID: {pending_absorption.pk}")
        print(f"Teacher: {teacher.username}")
        print(f"Student: {student.username}")
        
        # Check balances before
        db_service = DBTeoCoinService()
        teacher_balance_before = db_service.get_user_balance(teacher)
        student_notifications_before = Notification.objects.filter(user=student).count()
        
        print(f"Teacher balance before: {teacher_balance_before['available_balance']} TEO")
        
        # Teacher refuses (chooses EUR)
        result = TeacherDiscountAbsorptionService.process_teacher_choice(
            absorption_id=pending_absorption.pk,
            choice='refuse',
            teacher=teacher
        )
        
        teacher_balance_after = db_service.get_user_balance(teacher)
        student_notifications_after = Notification.objects.filter(user=student).count()
        
        teo_change = teacher_balance_after['available_balance'] - teacher_balance_before['available_balance']
        
        print(f"✅ Teacher choice processed:")
        print(f"   Status: {result.status}")
        print(f"   Teacher TEO change: {teo_change} TEO (should be 0)")
        print(f"   Student notifications: {student_notifications_before} → {student_notifications_after}")
        
        # Check student notification about EUR choice
        student_rejection_notification = Notification.objects.filter(
            user=student,
            notification_type='teocoin_discount_rejected'
        ).order_by('-created_at').first()
        
        if student_rejection_notification:
            print(f"✅ Student EUR choice notification:")
            print(f"   Message: {student_rejection_notification.message[:150]}...")
        
        refuse_success = (
            result.status == 'refused' and
            teo_change == 0 and
            student_notifications_after > student_notifications_before
        )
        
        print(f"\n🎯 Refuse scenario: {'✅ PASSED' if refuse_success else '❌ FAILED'}")
        return refuse_success
        
    except Exception as e:
        print(f"❌ Refuse test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Complete End-to-End TeoCoin Flow Tests...")
    
    # Test 1: Complete flow with teacher accepting TEO
    test1_passed = test_complete_end_to_end_flow()
    
    # Test 2: Teacher refusing TEO scenario
    test2_passed = test_teacher_refuses_teo()
    
    print("\n" + "=" * 70)
    print("🏁 FINAL TEST RESULTS")
    print("=" * 70)
    print(f"Complete Flow (Accept TEO): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Teacher Refuses TEO: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL END-TO-END TESTS PASSED!")
        print("🚀 The complete TeoCoin discount notification system is working!")
        print("\n📋 System is ready for:")
        print("   ✅ Student TeoCoin discount payments")
        print("   ✅ Real-time teacher notifications")
        print("   ✅ Teacher choice processing")
        print("   ✅ Automatic TEO transfers")
        print("   ✅ Student notification confirmations")
        print("   ✅ Complete transaction tracking")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
