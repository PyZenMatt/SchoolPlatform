#!/usr/bin/env python3
"""
Alternative Approval Solution - Backend TEO Transfer
Since MetaMask RPC is having persistent issues, this provides a backend solution
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

def backend_approve_solution():
    """
    Create a backend solution for the approval since MetaMask RPC is failing
    This can be used as an emergency backup
    """
    
    print("🔧 BACKEND APPROVAL SOLUTION")
    print("=" * 40)
    print("Since MetaMask RPC has persistent issues with Polygon Amoy,")
    print("here's a backend solution for testing:")
    print()
    
    # Get settings
    from django.conf import settings
    
    rpc_url = "https://rpc-amoy.polygon.technology/"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Cannot connect to Polygon Amoy")
        return
    
    # Contract addresses
    teocoin_address = Web3.to_checksum_address('0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8')
    reward_pool = Web3.to_checksum_address('0x3b72a4E942CF1467134510cA3952F01b63005044')
    user_address = Web3.to_checksum_address('0x5741935155afbfe404269b7bdcfe7f3318358d17')
    
    # Amount that was trying to be approved
    amount_teo = 219.978
    amount_wei = int(amount_teo * 10**18)
    
    print(f"📋 Alternative Solutions:")
    print(f"")
    print(f"1. 🏗️  **Direct Transaction Construction**")
    print(f"   Use different transaction builder in frontend")
    print(f"   Status: ✅ Implemented in latest code update")
    print(f"")
    print(f"2. 📱 **Mobile MetaMask**")
    print(f"   Often works when desktop fails")
    print(f"   Instructions: Use phone browser + MetaMask app")
    print(f"")
    print(f"3. 🔄 **Account Reset**")
    print(f"   MetaMask → Settings → Advanced → Reset Account")
    print(f"   Warning: Will clear transaction history")
    print(f"")
    print(f"4. 🌐 **Alternative RPC**")
    print(f"   Add to MetaMask:")
    print(f"   RPC URL: https://polygon-amoy.drpc.org")
    print(f"   Chain ID: 80002")
    print(f"")
    print(f"5. 💰 **Manual Approval (Advanced)**")
    print(f"   Use Polygon scan directly:")
    print(f"   https://amoy.polygonscan.com/address/{teocoin_address}#writeContract")
    print(f"   Function: approve({reward_pool}, {amount_wei})")
    print(f"")
    
    # Create a test transaction to show it works
    erc20_abi = [
        {
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]
    
    try:
        contract = w3.eth.contract(address=teocoin_address, abi=erc20_abi)
        
        # Show that the transaction can be built
        tx_data = contract.functions.approve(reward_pool, amount_wei).build_transaction({
            'from': user_address,
            'gas': 60000,
            'gasPrice': w3.eth.gas_price,
            'nonce': w3.eth.get_transaction_count(user_address)
        })
        
        print(f"✅ Transaction builds successfully:")
        print(f"   To: {tx_data['to']}")
        print(f"   Gas: {tx_data['gas']}")
        print(f"   Gas Price: {tx_data['gasPrice'] / 10**9:.2f} Gwei")
        print(f"   Data: {tx_data['data'][:50]}...")
        
    except Exception as e:
        print(f"❌ Transaction build failed: {e}")
    
    print(f"\n🎯 RECOMMENDATION:")
    print(f"Try the updated frontend code first (3 fallback methods)")
    print(f"If still fails → Use mobile MetaMask or reset account")
    print(f"This is a known Polygon Amoy testnet connectivity issue")

if __name__ == "__main__":
    backend_approve_solution()
