#!/usr/bin/env python3
"""
Test actual TeoCoin transfer execution
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from services.teocoin_discount_service import teocoin_discount_service

def test_actual_transfer():
    """Test an actual TeoCoin transfer to see what happens"""
    print("🧪 Testing Actual TeoCoin Transfer")
    
    teo_service = teocoin_discount_service.teocoin_service
    
    # Test wallet with balance
    wallet_address = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
    
    # Get initial balance
    initial_balance = teo_service.get_balance(wallet_address)
    print(f"Initial balance: {initial_balance} TEO")
    
    # Get reward pool address
    from django.conf import settings
    reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
    print(f"Reward pool address: {reward_pool_address}")
    
    if not reward_pool_address:
        print("❌ Reward pool address not configured - cannot test transfer")
        return
    
    # Small test transfer
    transfer_amount = Decimal('1.0')  # 1 TEO test
    
    print(f"\n🔄 Attempting transfer:")
    print(f"  From: {wallet_address}")
    print(f"  To: {reward_pool_address}")
    print(f"  Amount: {transfer_amount} TEO")
    
    try:
        result = teo_service.transfer_with_reward_pool_gas(
            wallet_address,
            str(reward_pool_address),  # Ensure string type
            transfer_amount
        )
        
        print(f"Transfer result: {result}")
        
        if result:
            print("✅ Transfer successful!")
            
            # Check new balance
            new_balance = teo_service.get_balance(wallet_address)
            print(f"New balance: {new_balance} TEO")
            print(f"Difference: {initial_balance - new_balance} TEO")
        else:
            print("❌ Transfer returned falsy result")
            
    except Exception as e:
        print(f"❌ Transfer failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_actual_transfer()
