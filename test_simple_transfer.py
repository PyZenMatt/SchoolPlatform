#!/usr/bin/env python3
"""
Simple test to verify TeoCoin transfer functionality
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_teocoin_transfer():
    """Test if TeoCoin transfers are working"""
    print("🧪 Testing TeoCoin Transfer Functionality")
    
    from services.teocoin_discount_service import teocoin_discount_service
    from django.conf import settings
    
    # Get service
    teo_service = teocoin_discount_service.teocoin_service
    
    # Test wallet (student1)
    wallet_address = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
    reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
    
    if not reward_pool_address:
        print("❌ No reward pool address configured")
        return
    
    print(f"From wallet: {wallet_address}")
    print(f"To reward pool: {reward_pool_address}")
    
    # Get initial balance
    initial_balance = teo_service.get_balance(wallet_address)
    print(f"Initial balance: {initial_balance} TEO")
    
    # Test very small transfer
    transfer_amount = Decimal('0.1')  # 0.1 TEO
    print(f"Attempting to transfer: {transfer_amount} TEO")
    
    try:
        # Call the exact same method used in payment flow
        result = teo_service.transfer_with_reward_pool_gas(
            wallet_address,
            reward_pool_address,
            transfer_amount
        )
        
        print(f"✅ Transfer completed!")
        print(f"Result: {result}")
        print(f"Result type: {type(result)}")
        
        # Check if balance changed
        new_balance = teo_service.get_balance(wallet_address)
        print(f"New balance: {new_balance} TEO")
        
        balance_diff = float(initial_balance) - float(new_balance)
        expected_diff = float(transfer_amount)
        
        print(f"Balance difference: {balance_diff} TEO")
        print(f"Expected difference: {expected_diff} TEO")
        
        if abs(balance_diff - expected_diff) < 0.01:
            print("✅ Transfer successful - balance deducted correctly!")
            return True
        else:
            print("❌ Transfer may have failed - balance not deducted correctly")
            return False
            
    except Exception as e:
        print(f"❌ Transfer failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_payment_flow_logs():
    """Check what happens in the actual payment flow"""
    print("\n🔍 Checking Payment Flow Logic")
    
    # Look at the payment flow code
    print("The payment flow should:")
    print("1. ✅ Check TeoCoin balance (working)")
    print("2. ✅ Calculate discount amount (working)")
    print("3. ❓ Transfer TEO tokens (TESTING)")
    print("4. ✅ Create Stripe payment for remainder (working)")
    print("5. ✅ Create enrollment (working)")
    
    # Check if payment flow actually calls transfer
    print("\nLet's see what the payment code does...")
    
    # Simulate the conditions in payment flow
    from courses.models import Course
    course = Course.objects.filter(teocoin_discount_percent__gt=0).first()
    
    if course:
        print(f"Test course: {course.title}")
        print(f"Discount %: {course.teocoin_discount_percent}%")
        
        # Calculate discount amount using same method as payment flow
        teo_cost_decimal = course.get_teocoin_discount_amount()
        print(f"TEO cost calculated: {teo_cost_decimal}")
        
        # This is what payment flow should transfer
        required_teo = float(teo_cost_decimal)
        print(f"Should transfer: {required_teo} TEO")

if __name__ == "__main__":
    # Test 1: Direct transfer test
    transfer_worked = test_teocoin_transfer()
    
    # Test 2: Check payment flow logic
    check_payment_flow_logs()
    
    print(f"\n🎯 CONCLUSION:")
    if transfer_worked:
        print("✅ TeoCoin transfers ARE working")
        print("❓ The issue might be that transfers are not being called in payment flow")
        print("💡 Check payment flow execution path")
    else:
        print("❌ TeoCoin transfers are NOT working")
        print("🔧 Need to fix transfer functionality first")
        print("💡 Check blockchain connection and gas settings")
