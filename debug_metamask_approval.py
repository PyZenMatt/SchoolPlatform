#!/usr/bin/env python3
"""
Debug MetaMask Approval Issue
Analyzes the transaction that failed and provides troubleshooting steps
"""

import os
import sys
import django
from decimal import Decimal

# Add the project root to Python path
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from web3 import Web3
from eth_account import Account
import json

def analyze_failed_transaction():
    """Analyze the failed approval transaction"""
    
    print("🔍 DEBUGGING METAMASK APPROVAL FAILURE")
    print("=" * 50)
    
    # Transaction details from error
    failed_tx_data = {
        "to": "0x20d6656a31297ab3b8a87291ed562d4228be9ff8",  # TeoCoin contract
        "from": "0x5741935155afbfe404269b7bdcfe7f3318358d17",  # User wallet
        "data": "0x095ea7b30000000000000000000000003b72a4e942cf1467134510ca3952f01b6300504400000000000000000000000000000000000000000000000becced981b0e0b1e0",
        "gas": "0x8700"  # 34560 decimal
    }
    
    print(f"📋 Failed Transaction Analysis:")
    print(f"   To (TeoCoin): {failed_tx_data['to']}")
    print(f"   From (User):  {failed_tx_data['from']}")
    print(f"   Gas Limit:    {int(failed_tx_data['gas'], 16)} (0x{failed_tx_data['gas'][2:]})")
    
    # Decode the data
    # First 4 bytes: 0x095ea7b3 = approve(address,uint256)
    # Next 32 bytes: spender address (reward pool)
    # Next 32 bytes: amount in wei
    
    data = failed_tx_data['data']
    method_sig = data[:10]  # 0x095ea7b3
    spender_raw = data[10:74]  # Next 64 chars
    amount_raw = data[74:]     # Rest
    
    spender = "0x" + spender_raw[24:]  # Remove padding
    amount_wei = int(amount_raw, 16)
    amount_ether = amount_wei / 10**18
    
    print(f"\n📊 Transaction Decode:")
    print(f"   Method:       approve() [0x095ea7b3]")
    print(f"   Spender:      {spender}")
    print(f"   Amount (Wei): {amount_wei}")
    print(f"   Amount (TEO): {amount_ether}")
    
    # Connect to Polygon Amoy
    rpc_url = "https://rpc-amoy.polygon.technology/"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Cannot connect to Polygon Amoy RPC")
        return
    
    print(f"\n🌐 Network Status:")
    print(f"   Connected:    ✅ Polygon Amoy")
    print(f"   Chain ID:     {w3.eth.chain_id}")
    print(f"   Latest Block: {w3.eth.block_number}")
    
    # Check user's balance and state
    user_address = failed_tx_data['from']
    try:
        # MATIC balance
        matic_balance = w3.eth.get_balance(user_address)
        matic_formatted = matic_balance / 10**18
        
        print(f"\n💳 User Wallet Analysis ({user_address}):")
        print(f"   MATIC Balance: {matic_formatted:.6f} MATIC")
        
        if matic_formatted < 0.01:
            print("   ⚠️  WARNING: Low MATIC balance - may cause gas issues")
        else:
            print("   ✅ MATIC balance sufficient for gas")
            
        # Check if contract exists
        teocoin_address = failed_tx_data['to']
        code = w3.eth.get_code(teocoin_address)
        if len(code) > 2:  # More than '0x'
            print(f"   ✅ TeoCoin contract exists at {teocoin_address}")
        else:
            print(f"   ❌ No contract found at {teocoin_address}")
            
    except Exception as e:
        print(f"   ❌ Error checking wallet: {e}")
    
    # Gas estimation analysis
    print(f"\n⛽ Gas Analysis:")
    print(f"   Failed Gas Limit: {int(failed_tx_data['gas'], 16)}")
    print(f"   Typical ERC-20 Approve: 46,000 - 60,000")
    print(f"   Recommended: 100,000 (with buffer)")
    
    # Troubleshooting steps
    print(f"\n🔧 TROUBLESHOOTING STEPS:")
    print(f"   1. Ensure wallet is on Polygon Amoy (Chain ID: 80002)")
    print(f"   2. Add MATIC to wallet if balance < 0.01")
    print(f"   3. Try refreshing MetaMask")
    print(f"   4. Clear MetaMask transaction queue")
    print(f"   5. Use higher gas limit (100,000+)")
    
    # Get some test MATIC
    print(f"\n💰 GET TEST MATIC:")
    print(f"   Polygon Faucet: https://faucet.polygon.technology/")
    print(f"   Alchemy Faucet: https://www.alchemy.com/faucets/polygon-amoy")
    
    return {
        'user_address': user_address,
        'matic_balance': matic_formatted if 'matic_formatted' in locals() else 0,
        'amount_teo': amount_ether,
        'gas_used': int(failed_tx_data['gas'], 16)
    }

if __name__ == "__main__":
    result = analyze_failed_transaction()
    
    print(f"\n🎯 QUICK FIX SUMMARY:")
    if result['matic_balance'] < 0.01:
        print(f"   ❗ PRIMARY ISSUE: Need more MATIC for gas fees")
        print(f"   💡 SOLUTION: Get MATIC from faucet, need ~0.01 MATIC minimum")
    else:
        print(f"   ❗ PRIMARY ISSUE: Likely RPC/network connectivity")  
        print(f"   💡 SOLUTION: Try switching MetaMask network or refreshing")
