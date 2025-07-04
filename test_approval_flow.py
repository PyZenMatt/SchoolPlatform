#!/usr/bin/env python3
"""
Test and implement TeoCoin approval + transfer flow
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
    print("🔧 Testing TeoCoin Approval + Transfer Flow")
    
    from services.teocoin_discount_service import teocoin_discount_service
    from django.conf import settings
    
    teo_service = teocoin_discount_service.teocoin_service
    
    # Student wallet
    student_wallet = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
    reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS')
    
    print(f"Student wallet: {student_wallet}")
    print(f"Reward pool: {reward_pool_address}")
    
    # Check initial balance
    balance = teo_service.get_balance(student_wallet)
    print(f"Student balance: {balance} TEO")
    
    # Step 1: Approve reward pool to spend student's tokens
    print(f"\n🔑 Step 1: Approving reward pool as spender...")
    try:
        # Check if we have the approval method
        if hasattr(teo_service, 'approve_reward_pool_as_spender'):
            approval_result = teo_service.approve_reward_pool_as_spender(student_wallet)
            print(f"Approval result: {approval_result}")
            
            if approval_result:
                print("✅ Approval successful!")
                
                # Step 2: Now try the transfer
                print(f"\n💸 Step 2: Attempting transfer after approval...")
                transfer_amount = Decimal('0.1')
                
                transfer_result = teo_service.transfer_with_reward_pool_gas(
                    student_wallet,
                    reward_pool_address,
                    transfer_amount
                )
                
                print(f"Transfer result: {transfer_result}")
                
                if transfer_result:
                    print("✅ Transfer submitted!")
                    
                    # Check transaction status
                    import time
                    print("⏱️ Waiting for transaction confirmation...")
                    time.sleep(5)
                    
                    try:
                        receipt = teo_service.get_transaction_receipt(transfer_result)
                        if receipt and receipt.get('status') == 1:
                            print("✅ Transaction confirmed!")
                            
                            # Check new balance
                            new_balance = teo_service.get_balance(student_wallet)
                            print(f"New balance: {new_balance} TEO")
                            print(f"Difference: {balance - new_balance} TEO")
                        else:
                            print("❌ Transaction failed or still pending")
                    except Exception as e:
                        print(f"❌ Error checking receipt: {e}")
                else:
                    print("❌ Transfer failed")
            else:
                print("❌ Approval failed")
        else:
            print("❌ Approval method not available")
            
    except Exception as e:
        print(f"❌ Error in approval flow: {e}")
        import traceback
        traceback.print_exc()

def create_fixed_payment_flow():
    """Create the fixed payment flow that includes approval"""
    print("\n🔧 Creating Fixed Payment Flow Code")
    
    # This is what the payment flow should look like
    fixed_code = """
# FIXED TEOCOIN PAYMENT FLOW WITH APPROVAL

def process_teocoin_payment(student_wallet, course, payment_method='hybrid'):
    '''Process TeoCoin payment with proper approval flow'''
    
    # Get services
    from services.teocoin_discount_service import teocoin_discount_service
    from django.conf import settings
    
    teo_service = teocoin_discount_service.teocoin_service
    reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS')
    
    # Calculate TEO cost
    teo_cost = course.get_teocoin_discount_amount()
    required_teo = float(teo_cost)
    
    # Check balance
    balance = teo_service.get_balance(student_wallet)
    if balance < required_teo:
        raise ValueError(f'Insufficient balance: {balance} < {required_teo}')
    
    # STEP 1: APPROVE REWARD POOL (CRITICAL!)
    print(f"🔑 Approving reward pool for {student_wallet}...")
    approval_result = teo_service.approve_reward_pool_as_spender(student_wallet)
    
    if not approval_result:
        raise ValueError('Failed to approve reward pool')
    
    # STEP 2: TRANSFER TEO TOKENS
    print(f"💸 Transferring {required_teo} TEO...")
    transfer_result = teo_service.transfer_with_reward_pool_gas(
        student_wallet,
        reward_pool_address,
        Decimal(str(required_teo))
    )
    
    if not transfer_result:
        raise ValueError('TEO transfer failed')
    
    # STEP 3: VERIFY TRANSACTION
    import time
    time.sleep(3)  # Wait for confirmation
    
    receipt = teo_service.get_transaction_receipt(transfer_result)
    if not receipt or receipt.get('status') != 1:
        raise ValueError('Transaction failed or reverted')
    
    print(f"✅ TEO transfer successful: {transfer_result}")
    return transfer_result
"""
    
    print("The fixed payment flow includes:")
    print("1. ✅ Balance checking")
    print("2. 🔑 APPROVAL of reward pool (NEW!)")
    print("3. 💸 Token transfer")
    print("4. ✅ Transaction verification")
    
    return fixed_code

if __name__ == "__main__":
    # Test 1: Try approval + transfer
    test_approval_and_transfer()
    
    # Test 2: Show fixed flow
    fixed_code = create_fixed_payment_flow()
    
    print("\n" + "="*60)
    print(" SOLUTION SUMMARY")
    print("="*60)
    print("🎯 ISSUE: TeoCoin transfers failing due to missing approval")
    print("🔧 FIX: Add approval step before transfer in payment flow")
    print("📝 IMPLEMENTATION: Update courses/views/payments.py")
    print("\n💡 The payment flow should:")
    print("1. Check student has sufficient TEO")
    print("2. 🔑 APPROVE reward pool to spend student's TEO")
    print("3. 💸 Transfer TEO from student to reward pool")
    print("4. ✅ Verify transaction success")
    print("5. Continue with Stripe payment for remainder")
