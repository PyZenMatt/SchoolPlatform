#!/usr/bin/env python3
"""
Check transaction status on blockchain
"""
import os
import sys
import django
import time
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def check_transaction_status():
    """Check the status of our test transaction"""
    print("🔍 Checking Transaction Status")
    
    from services.teocoin_discount_service import teocoin_discount_service
    
    # Get service
    teo_service = teocoin_discount_service.teocoin_service
    
    # The transaction hash from our previous test
    tx_hash = "549c75e1a54309c1c471516b9c331b9325808766ca559c8e5a43b296addefe89"
    print(f"Transaction hash: {tx_hash}")
    
    try:
        # Check transaction receipt
        receipt = teo_service.get_transaction_receipt(tx_hash)
        
        if receipt:
            print("✅ Transaction found!")
            print(f"Status: {receipt.get('status', 'Unknown')}")
            print(f"Block number: {receipt.get('blockNumber', 'Unknown')}")
            print(f"Gas used: {receipt.get('gasUsed', 'Unknown')}")
            
            if receipt.get('status') == 1:
                print("✅ Transaction was successful!")
            else:
                print("❌ Transaction failed!")
                
        else:
            print("❌ Transaction not found or still pending")
            
    except Exception as e:
        print(f"❌ Error checking transaction: {e}")
    
    # Check balance again after some time
    wallet_address = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
    
    print(f"\n⏱️ Checking balance again...")
    current_balance = teo_service.get_balance(wallet_address)
    print(f"Current balance: {current_balance} TEO")
    
    print(f"\n💡 If balance is still 1237.418, the transaction might:")
    print(f"1. Still be pending in mempool")
    print(f"2. Have failed due to gas issues")
    print(f"3. Have been reverted")
    print(f"4. Be on a different network/testnet")

def do_another_transfer_test():
    """Try another transfer with more logging"""
    print("\n🧪 Attempting Another Transfer Test")
    
    from services.teocoin_discount_service import teocoin_discount_service
    from django.conf import settings
    
    teo_service = teocoin_discount_service.teocoin_service
    
    wallet_address = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
    reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS')
    
    # Get balance before
    balance_before = teo_service.get_balance(wallet_address)
    print(f"Balance before: {balance_before} TEO")
    
    # Try transfer
    transfer_amount = Decimal('0.01')  # Even smaller amount
    print(f"Attempting transfer: {transfer_amount} TEO")
    
    try:
        result = teo_service.transfer_with_reward_pool_gas(
            wallet_address,
            reward_pool_address,
            transfer_amount
        )
        
        print(f"Transaction hash: {result}")
        
        # Wait a bit and check balance
        print("⏱️ Waiting 3 seconds...")
        time.sleep(3)
        
        balance_after = teo_service.get_balance(wallet_address)
        print(f"Balance after: {balance_after} TEO")
        
        if balance_before != balance_after:
            print("✅ Balance changed - transfer working!")
        else:
            print("❌ Balance unchanged - transfer not working or pending")
            
        return result
        
    except Exception as e:
        print(f"❌ Transfer error: {e}")
        return None

if __name__ == "__main__":
    check_transaction_status()
    new_tx = do_another_transfer_test()
    
    if new_tx:
        print(f"\n📝 NEW TRANSACTION: {new_tx}")
        print("💡 To debug further:")
        print("1. Check transaction on block explorer")
        print("2. Verify network configuration")
        print("3. Check gas price settings")
        print("4. Confirm contract addresses")
