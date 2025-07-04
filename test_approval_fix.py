#!/usr/bin/env python3
"""
Test the improved payment flow with approval
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_approval_and_transfer():
    """Test the complete approval + transfer flow"""
    print("🧪 Testing Improved Payment Flow with Approval")
    
    from services.teocoin_discount_service import teocoin_discount_service
    from blockchain.models import UserWallet
    from django.contrib.auth import get_user_model
    from django.conf import settings
    
    User = get_user_model()
    teo_service = teocoin_discount_service.teocoin_service
    
    # Get student1 who has wallet
    student = User.objects.get(username='student1')
    print(f"Student: {student.username}")
    
    try:
        # Get user wallet with private key
        user_wallet = UserWallet.objects.get(user=student)
        wallet_address = user_wallet.address
        private_key = user_wallet.private_key
        
        print(f"Wallet address: {wallet_address}")
        print(f"Private key: {user_wallet.get_masked_private_key()}")
        
    except UserWallet.DoesNotExist:
        print("❌ User wallet not found")
        return
    
    # Get reward pool address
    reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS')
    print(f"Reward pool: {reward_pool_address}")
    
    # Check initial balance
    initial_balance = teo_service.get_balance(wallet_address)
    print(f"Initial balance: {initial_balance} TEO")
    
    # Check current allowance
    current_allowance = teo_service.contract.functions.allowance(
        wallet_address, 
        reward_pool_address
    ).call()
    
    allowance_teo = current_allowance / 10**18
    print(f"Current allowance: {allowance_teo} TEO")
    
    # Test amount
    test_amount = Decimal('0.1')
    print(f"Test transfer amount: {test_amount} TEO")
    
    # Step 1: Approve if needed
    if allowance_teo < float(test_amount):
        print(f"\n🔑 Step 1: Approving reward pool...")
        
        approval_result = teo_service.approve_reward_pool_as_spender(
            private_key,
            test_amount * 2  # Approve 2x for safety
        )
        
        if approval_result:
            print(f"✅ Approval successful: {approval_result}")
            
            # Wait for approval to be mined
            import time
            print("⏱️ Waiting for approval to be mined...")
            time.sleep(5)
            
            # Check new allowance
            new_allowance = teo_service.contract.functions.allowance(
                wallet_address, 
                reward_pool_address
            ).call()
            
            new_allowance_teo = new_allowance / 10**18
            print(f"New allowance: {new_allowance_teo} TEO")
            
        else:
            print(f"❌ Approval failed")
            return
    else:
        print(f"✅ Sufficient allowance already available")
    
    # Step 2: Transfer
    print(f"\n🔄 Step 2: Transferring TEO...")
    
    transfer_result = teo_service.transfer_with_reward_pool_gas(
        wallet_address,
        reward_pool_address,
        test_amount
    )
    
    if transfer_result:
        print(f"✅ Transfer submitted: {transfer_result}")
        
        # Wait and check transaction status
        import time
        print("⏱️ Waiting for transfer to be mined...")
        time.sleep(5)
        
        try:
            receipt = teo_service.get_transaction_receipt(transfer_result)
            
            if receipt:
                status = receipt.get('status', 0)
                print(f"Transaction status: {status}")
                
                if status == 1:
                    print("✅ Transfer successful on blockchain!")
                    
                    # Check balance change
                    final_balance = teo_service.get_balance(wallet_address)
                    print(f"Final balance: {final_balance} TEO")
                    
                    balance_diff = initial_balance - final_balance
                    print(f"Balance difference: {balance_diff} TEO")
                    
                    if abs(float(balance_diff) - float(test_amount)) < 0.01:
                        print("✅ SUCCESS: TeoCoin transfer is now working!")
                        return True
                    else:
                        print("❌ Balance change doesn't match transfer amount")
                        
                else:
                    print("❌ Transfer failed on blockchain")
            else:
                print("❌ No transaction receipt found")
                
        except Exception as e:
            print(f"❌ Error checking transaction: {e}")
    else:
        print(f"❌ Transfer submission failed")
    
    return False

if __name__ == "__main__":
    success = test_approval_and_transfer()
    
    if success:
        print(f"\n🎉 SOLUTION IMPLEMENTED!")
        print(f"✅ TeoCoin transfers are now working")
        print(f"💡 The payment flow has been fixed to include approval step")
        print(f"🔄 Students can now use TeoCoin discounts properly")
    else:
        print(f"\n❌ Still needs work")
        print(f"🔧 Check blockchain connection and contract setup")
