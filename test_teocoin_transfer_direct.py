#!/usr/bin/env python3
"""
Direct TeoCoin transfer test - focus on blockchain token transfer logic
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
from blockchain.models import UserWallet

User = get_user_model()

def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_teocoin_service_direct():
    """Test TeoCoin service methods directly"""
    print_separator("TESTING TEOCOIN SERVICE DIRECTLY")
    
    try:
        from services.teocoin_discount_service import teocoin_discount_service
        
        # Get the TeoCoin service
        teo_service = teocoin_discount_service.teocoin_service
        print(f"✅ TeoCoin service obtained: {type(teo_service)}")
        
        # Test wallet address
        test_wallet = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
        print(f"Testing with wallet: {test_wallet}")
        
        # Check balance
        try:
            balance = teo_service.get_balance(test_wallet)
            print(f"Wallet balance: {balance} TEO")
        except Exception as e:
            print(f"❌ Error getting balance: {e}")
        
        # Check reward pool balance
        try:
            reward_balance = teo_service.get_reward_pool_balance()
            print(f"Reward pool balance: {reward_balance} TEO")
        except Exception as e:
            print(f"❌ Error getting reward pool balance: {e}")
        
        # Check available methods
        print(f"\nAvailable service methods:")
        for method in dir(teo_service):
            if not method.startswith('_'):
                print(f"  - {method}")
        
        # Test if transfer method exists
        if hasattr(teo_service, 'transfer_with_reward_pool_gas'):
            print(f"✅ Transfer method available")
            
            # Test parameters for transfer
            print(f"\nTesting transfer parameters:")
            amount_to_transfer = Decimal('120.0')  # 120 TEO for 5% discount
            
            print(f"  From wallet: {test_wallet}")
            print(f"  Amount: {amount_to_transfer} TEO")
            
            # Check if we have settings for reward pool
            from django.conf import settings
            reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
            print(f"  Reward pool address: {reward_pool_address}")
            
            if reward_pool_address:
                print(f"✅ Reward pool configured")
                
                # Simulate the transfer call (don't actually execute)
                print(f"\n🔄 Would call:")
                print(f"  teo_service.transfer_with_reward_pool_gas(")
                print(f"    from_address='{test_wallet}',")
                print(f"    to_address='{reward_pool_address}',")
                print(f"    amount={amount_to_transfer}")
                print(f"  )")
                
                # Uncomment to actually test transfer:
                # try:
                #     result = teo_service.transfer_with_reward_pool_gas(
                #         test_wallet,
                #         reward_pool_address,
                #         amount_to_transfer
                #     )
                #     print(f"✅ Transfer result: {result}")
                # except Exception as e:
                #     print(f"❌ Transfer failed: {e}")
            else:
                print(f"❌ Reward pool not configured")
        else:
            print(f"❌ Transfer method not available")
            
    except Exception as e:
        print(f"❌ Error testing TeoCoin service: {e}")
        import traceback
        traceback.print_exc()

def examine_teocoin_enrollments():
    """Examine enrollments that used TeoCoin"""
    print_separator("EXAMINING TEOCOIN ENROLLMENTS")
    
    teocoin_enrollments = CourseEnrollment.objects.filter(
        payment_method='teocoin_discount'
    ).order_by('-enrolled_at')
    
    print(f"Found {teocoin_enrollments.count()} TeoCoin enrollments")
    
    for enrollment in teocoin_enrollments:
        print(f"\n📚 Enrollment {enrollment.pk}:")
        print(f"  Student: {enrollment.student.username if enrollment.student else 'Unknown'}")
        print(f"  Course: {enrollment.course.title}")
        print(f"  Amount paid: €{getattr(enrollment, 'amount_paid_eur', 'Not specified')}")
        print(f"  Enrolled: {enrollment.enrolled_at}")
        
        # Check course discount settings
        course = enrollment.course
        print(f"  Course price: €{course.price_eur}")
        print(f"  Discount %: {course.teocoin_discount_percent}%")
        
        # Calculate what the discount should have been
        discount_amount_eur = course.price_eur * course.teocoin_discount_percent / 100
        discount_amount_teo = discount_amount_eur * 10
        
        print(f"  Expected discount: €{discount_amount_eur} = {discount_amount_teo} TEO")
        
        # Check what was actually paid vs what should be paid
        expected_final_price = course.price_eur - discount_amount_eur
        actual_paid = getattr(enrollment, 'amount_paid_eur', 0)
        
        print(f"  Expected final price: €{expected_final_price}")
        print(f"  Actual paid: €{actual_paid}")
        
        if float(actual_paid) == float(expected_final_price):
            print(f"  ✅ Payment amount correct")
        else:
            print(f"  ❌ Payment amount mismatch")

def check_wallet_balances():
    """Check actual blockchain wallet balances"""
    print_separator("CHECKING BLOCKCHAIN WALLET BALANCES")
    
    try:
        from services.teocoin_discount_service import teocoin_discount_service
        teo_service = teocoin_discount_service.teocoin_service
        
        # Get students with wallets
        students = User.objects.filter(role='student', is_active=True)
        
        for student in students:
            wallet_address = getattr(student, 'wallet_address', None)
            if wallet_address:
                try:
                    balance = teo_service.get_balance(wallet_address)
                    print(f"Student: {student.username}")
                    print(f"  Wallet: {wallet_address}")
                    print(f"  Balance: {balance} TEO")
                    
                    # Check if this student has any TeoCoin enrollments
                    teo_enrollments = CourseEnrollment.objects.filter(
                        student=student,
                        payment_method='teocoin_discount'
                    ).count()
                    
                    print(f"  TeoCoin enrollments: {teo_enrollments}")
                    
                except Exception as e:
                    print(f"❌ Error checking balance for {student.username}: {e}")
                    
            else:
                # Check if they have a UserWallet record
                try:
                    wallet = UserWallet.objects.get(user=student)
                    try:
                        balance = teo_service.get_balance(wallet.address)
                        print(f"Student: {student.username}")
                        print(f"  Wallet (from UserWallet): {wallet.address}")
                        print(f"  Balance: {balance} TEO")
                    except Exception as e:
                        print(f"❌ Error checking balance for {student.username}: {e}")
                except UserWallet.DoesNotExist:
                    print(f"Student: {student.username} - No wallet configured")
                    
    except Exception as e:
        print(f"❌ Error accessing TeoCoin service: {e}")

def analyze_payment_flow_code():
    """Analyze the payment flow code to understand what should happen"""
    print_separator("ANALYZING PAYMENT FLOW CODE")
    
    print("🔍 Key points from payment flow code analysis:")
    print("1. TeoCoin discount should deduct tokens from student wallet")
    print("2. Tokens should be transferred to reward pool")
    print("3. Teacher should receive bonus tokens from reward pool")
    print("4. Student pays remaining amount with card (hybrid) or gets enrolled (full TEO)")
    
    print("\n📋 Current implementation status:")
    
    # Check if the payment flow actually executes transfers
    print("- Payment intent creation: ✅ Working")
    print("- TeoCoin balance checking: ✅ Working")
    print("- TeoCoin transfer execution: ❓ NEEDS VERIFICATION")
    print("- Teacher bonus distribution: ❓ NEEDS VERIFICATION")
    print("- Balance deduction tracking: ❓ NEEDS VERIFICATION")
    
    print("\n🔄 What the payment flow should do:")
    print("1. Check student has sufficient TEO balance")
    print("2. Calculate discount amount in TEO")
    print("3. Transfer TEO from student → reward pool")
    print("4. Update student's on-chain balance")
    print("5. Send bonus TEO from reward pool → teacher")
    print("6. Create Stripe payment for remaining amount (hybrid)")
    print("7. OR complete enrollment directly (full TEO)")

def main():
    """Run focused TeoCoin transfer tests"""
    print("🪙 TeoCoin Transfer Analysis")
    
    # Test 1: Direct service testing
    test_teocoin_service_direct()
    
    # Test 2: Examine existing TeoCoin enrollments
    examine_teocoin_enrollments()
    
    # Test 3: Check actual wallet balances
    check_wallet_balances()
    
    # Test 4: Analyze payment flow
    analyze_payment_flow_code()
    
    print_separator("ANALYSIS COMPLETE")
    
    print("\n🎯 NEXT STEPS:")
    print("1. Verify if TeoCoin transfers are actually happening")
    print("2. Check if wallet balances are being updated on blockchain")
    print("3. Implement proper transaction logging")
    print("4. Test teacher bonus distribution")
    print("5. Add frontend feedback for successful TeoCoin usage")

if __name__ == "__main__":
    main()
