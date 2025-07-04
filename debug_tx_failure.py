#!/usr/bin/env python3
"""
Debug why blockchain transactions are failing
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def debug_transaction_failure():
    """Debug why transactions are failing"""
    print("🔍 Debugging Transaction Failures")
    
    from services.teocoin_discount_service import teocoin_discount_service
    
    teo_service = teocoin_discount_service.teocoin_service
    
    # Check failed transaction
    tx_hash = "62391e333b96861b759d6ea2ec02a3db964294b82b08f7f9f45e545954fd7f9c"
    
    try:
        receipt = teo_service.get_transaction_receipt(tx_hash)
        print(f"Transaction details:")
        print(f"  Hash: {tx_hash}")
        print(f"  Status: {receipt.get('status', 'Unknown')}")
        print(f"  Block: {receipt.get('blockNumber', 'Unknown')}")
        print(f"  Gas used: {receipt.get('gasUsed', 'Unknown')}")
        print(f"  Gas limit: {receipt.get('gas', 'Unknown')}")
        
        # Try to get more details
        if hasattr(teo_service, 'w3'):
            w3 = teo_service.w3
            
            # Get transaction details
            try:
                tx = w3.eth.get_transaction(tx_hash)
                print(f"\nTransaction input:")
                print(f"  From: {tx.get('from', 'Unknown')}")
                print(f"  To: {tx.get('to', 'Unknown')}")
                print(f"  Value: {tx.get('value', 'Unknown')}")
                print(f"  Gas: {tx.get('gas', 'Unknown')}")
                print(f"  Gas price: {tx.get('gasPrice', 'Unknown')}")
                
            except Exception as e:
                print(f"❌ Error getting transaction details: {e}")
                
    except Exception as e:
        print(f"❌ Error getting receipt: {e}")

def check_blockchain_config():
    """Check blockchain configuration"""
    print("\n🔧 Checking Blockchain Configuration")
    
    from services.teocoin_discount_service import teocoin_discount_service
    from django.conf import settings
    
    teo_service = teocoin_discount_service.teocoin_service
    
    # Check contract address
    print(f"Contract address: {teo_service.contract_address}")
    
    # Check reward pool address
    reward_pool = getattr(settings, 'REWARD_POOL_ADDRESS', 'Not configured')
    print(f"Reward pool address: {reward_pool}")
    
    # Check network
    if hasattr(teo_service, 'rpc_url'):
        print(f"RPC URL: {teo_service.rpc_url}")
    
    # Check if contract is deployed
    try:
        if hasattr(teo_service, 'w3'):
            w3 = teo_service.w3
            code = w3.eth.get_code(teo_service.contract_address)
            if code and code != b'\\x00':
                print("✅ Contract is deployed")
            else:
                print("❌ Contract not deployed or wrong address")
    except Exception as e:
        print(f"❌ Error checking contract: {e}")

def check_wallet_permissions():
    """Check if wallet has proper permissions"""
    print("\n🔑 Checking Wallet Permissions")
    
    from services.teocoin_discount_service import teocoin_discount_service
    
    teo_service = teocoin_discount_service.teocoin_service
    wallet_address = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
    
    try:
        # Check if wallet has approved the reward pool for spending
        if hasattr(teo_service, 'contract'):
            contract = teo_service.contract
            
            # Check allowance
            reward_pool = teo_service.reward_pool_address
            allowance = contract.functions.allowance(wallet_address, reward_pool).call()
            print(f"Allowance for reward pool: {allowance / 10**18} TEO")
            
            if allowance == 0:
                print("❌ Wallet has not approved reward pool for spending!")
                print("💡 This is likely the issue - need to approve first")
            else:
                print("✅ Wallet has approved reward pool")
                
    except Exception as e:
        print(f"❌ Error checking allowance: {e}")

def suggest_fixes():
    """Suggest how to fix the transaction failures"""
    print("\n🔧 SUGGESTED FIXES:")
    
    print("1. **Check Allowance**: Student wallets need to approve reward pool for spending")
    print("2. **Gas Issues**: Transaction might be running out of gas")
    print("3. **Contract Issues**: TeoCoin contract might have bugs")
    print("4. **Network Issues**: Wrong network or RPC problems")
    print("5. **Balance Issues**: Insufficient gas token (MATIC) for transaction fees")
    
    print("\n💡 IMMEDIATE ACTIONS:")
    print("1. Check if students need to approve spending first")
    print("2. Increase gas limit for transfers")
    print("3. Verify contract is working correctly")
    print("4. Test with a working wallet")

if __name__ == "__main__":
    debug_transaction_failure()
    check_blockchain_config()
    check_wallet_permissions()
    suggest_fixes()
