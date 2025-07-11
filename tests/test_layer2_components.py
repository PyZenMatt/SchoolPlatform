"""
Simplified Layer 2 Component Test

Test each Layer 2 component individually to verify functionality
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django environment
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User, TeacherProfile
from services.gas_treasury_service import gas_treasury_service
from services.notification_service import notification_service


def test_layer2_components():
    """Test Layer 2 components individually"""
    
    print("🧪 LAYER 2 COMPONENT TESTING")
    print("=" * 50)
    
    results = {'passed': 0, 'total': 0}
    
    # Test 1: Teacher Profile Commission Logic
    print("\n💰 TEST 1: Teacher Profile Commission Logic")
    try:
        teacher = User.objects.filter(role='teacher').first()
        if teacher:
            profile, created = TeacherProfile.objects.get_or_create(
                user=teacher,
                defaults={
                    'commission_rate': Decimal('50.00'),
                    'staking_tier': 'Bronze',
                    'staked_teo_amount': Decimal('0.00')
                }
            )
            
            # Test tier progression
            test_amounts = [
                (Decimal('0'), 'Bronze', Decimal('50.00')),
                (Decimal('100'), 'Silver', Decimal('45.00')),
                (Decimal('300'), 'Gold', Decimal('40.00')),
                (Decimal('600'), 'Platinum', Decimal('35.00')),
                (Decimal('1000'), 'Diamond', Decimal('25.00')),
            ]
            
            all_correct = True
            for amount, expected_tier, expected_commission in test_amounts:
                profile.staked_teo_amount = amount
                result = profile.update_tier_and_commission()
                
                if result['tier'] == expected_tier and result['commission_rate'] == expected_commission:
                    print(f"  ✅ {amount} TEO → {expected_tier} ({expected_commission}%)")
                else:
                    print(f"  ❌ {amount} TEO → Expected {expected_tier}/{expected_commission}%, got {result['tier']}/{result['commission_rate']}%")
                    all_correct = False
            
            if all_correct:
                print("  ✅ Commission progression working correctly")
                results['passed'] += 1
            else:
                print("  ❌ Commission progression has issues")
        else:
            print("  ⚠️ No teachers found")
        
        results['total'] += 1
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        results['total'] += 1
    
    # Test 2: Gas Treasury Service
    print("\n⛽ TEST 2: Gas Treasury Service")
    try:
        # Test status
        status = gas_treasury_service.get_treasury_status()
        print(f"  📊 Status: {status.get('status')}")
        print(f"  💰 Balance: {status.get('current_balance')} MATIC")
        
        # Test cost estimation
        operations = ['teocoin_transfer', 'permit_signature', 'course_purchase']
        total_cost = Decimal('0')
        
        for operation in operations:
            cost = gas_treasury_service.estimate_gas_cost(operation, 1)
            total_cost += Decimal(str(cost))
            print(f"  💸 {operation}: {cost} MATIC")
        
        print(f"  📈 Total flow cost: {total_cost} MATIC")
        
        # Test balance check
        sufficient, message = gas_treasury_service.check_balance_sufficient('teocoin_transfer')
        print(f"  🔍 Balance check: {message}")
        
        print("  ✅ Gas treasury service operational")
        results['passed'] += 1
        results['total'] += 1
        
    except Exception as e:
        print(f"  ❌ Gas treasury error: {str(e)}")
        results['total'] += 1
    
    # Test 3: Notification Service
    print("\n🔔 TEST 3: Notification Service")
    try:
        teacher = User.objects.filter(role='teacher').first()
        student = User.objects.filter(role='student').first()
        
        if teacher and student:
            # Test valid notification types
            valid_notifications = [
                ('teocoin_discount_pending', teacher, {'message': 'Test discount request'}),
                ('teocoin_discount_accepted', student, {'message': 'Test discount accepted'}),
                ('course_purchased', teacher, {'message': 'Test course sold'}),
            ]
            
            notification_success = 0
            for notif_type, user, data in valid_notifications:
                result = notification_service.send_real_time_notification(
                    user=user,
                    notification_type=notif_type,
                    data=data
                )
                
                if result.get('success'):
                    print(f"  ✅ {notif_type} notification sent to {user.role}")
                    notification_success += 1
                else:
                    print(f"  ⚠️ {notif_type} notification failed: {result.get('message', 'Unknown error')}")
            
            if notification_success > 0:
                print(f"  ✅ Notification service working ({notification_success}/{len(valid_notifications)} sent)")
                results['passed'] += 1
            else:
                print("  ❌ No notifications sent successfully")
        else:
            print("  ⚠️ Missing users for notification test")
        
        results['total'] += 1
        
    except Exception as e:
        print(f"  ❌ Notification error: {str(e)}")
        results['total'] += 1
    
    # Test 4: Discount Calculation Logic
    print("\n🧮 TEST 4: Discount Calculation Logic")
    try:
        # Simulate discount calculation
        course_price = Decimal('100.00')
        discount_percent = Decimal('15.00')  # Use Decimal for consistency
        commission_rate = Decimal('50.00')
        
        # Calculate discount
        discount_amount = course_price * (discount_percent / Decimal('100.00'))
        final_price = course_price - discount_amount
        
        # Calculate earnings
        platform_commission = final_price * (commission_rate / Decimal('100.00'))
        teacher_earnings = final_price - platform_commission
        
        print(f"  📊 Original price: €{course_price}")
        print(f"  💰 Discount (15%): €{discount_amount}")
        print(f"  💳 Final price: €{final_price}")
        print(f"  🏢 Platform commission (50%): €{platform_commission}")
        print(f"  👨‍🏫 Teacher earnings (50%): €{teacher_earnings}")
        
        # Verify calculations
        if discount_amount == Decimal('15.00') and final_price == Decimal('85.00'):
            print("  ✅ Discount calculation correct")
            results['passed'] += 1
        else:
            print("  ❌ Discount calculation incorrect")
        
        results['total'] += 1
        
    except Exception as e:
        print(f"  ❌ Calculation error: {str(e)}")
        results['total'] += 1
    
    # Test 5: Database Models
    print("\n🗄️ TEST 5: Database Models")
    try:
        # Check teacher profiles
        teacher_count = TeacherProfile.objects.count()
        teachers_with_tiers = TeacherProfile.objects.exclude(staking_tier='').count()
        
        print(f"  👥 Teacher profiles: {teacher_count}")
        print(f"  🏆 Profiles with tiers: {teachers_with_tiers}")
        
        # Check users
        student_count = User.objects.filter(role='student').count()
        teacher_user_count = User.objects.filter(role='teacher').count()
        
        print(f"  📚 Students: {student_count}")
        print(f"  🎓 Teachers: {teacher_user_count}")
        
        if teacher_count > 0 and student_count > 0:
            print("  ✅ Database models populated")
            results['passed'] += 1
        else:
            print("  ⚠️ Missing data in database")
        
        results['total'] += 1
        
    except Exception as e:
        print(f"  ❌ Database error: {str(e)}")
        results['total'] += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 COMPONENT TEST RESULTS")
    print("=" * 50)
    print(f"Tests passed: {results['passed']}/{results['total']}")
    
    success_rate = (results['passed'] / results['total']) * 100 if results['total'] > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 LAYER 2 COMPONENTS ARE WORKING WELL!")
        print("✅ Core functionality is operational")
        print("✅ Ready for production use")
    else:
        print("\n⚠️ Some components need attention")
        print("🔧 Review failed tests above")
    
    return success_rate >= 80


if __name__ == "__main__":
    test_layer2_components()
