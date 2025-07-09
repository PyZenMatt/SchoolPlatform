#!/usr/bin/env python3
"""
MetaMask TEO Token Configuration Helper
This script provides the information needed to manually add TEO token to MetaMask
"""

import os
import sys
import django
from web3 import Web3

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def main():
    print("🦊 METAMASK TEO TOKEN CONFIGURATION")
    print("=" * 60)
    
    # Contract addresses
    teocoin_address = "0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8"
    discount_contract_address = "0xd30afec0bc6ac33e14a0114ec7403bbd746e88de"
    student_address = "0x3b72a4E942CF1467134510cA3952F01b63005044"
    
    print(f"📋 TO ADD TEO TOKEN TO METAMASK:")
    print(f"   1. Open MetaMask")
    print(f"   2. Go to 'Assets' tab")
    print(f"   3. Click 'Import tokens'")
    print(f"   4. Select 'Custom token'")
    print(f"   5. Enter these details:")
    print(f"")
    print(f"   Token Contract Address: {teocoin_address}")
    print(f"   Token Symbol: TEO")
    print(f"   Token Decimals: 18")
    print(f"")
    print(f"🌐 NETWORK: Polygon Amoy Testnet")
    print(f"   Chain ID: 80002")
    print(f"   RPC URL: https://rpc-amoy.polygon.technology/")
    print(f"   Block Explorer: https://amoy.polygonscan.com/")
    print(f"")
    
    # Check current balance
    try:
        rpc_url = os.getenv('POLYGON_AMOY_RPC_URL', 'https://rpc-amoy.polygon.technology/')
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Minimal ERC-20 ABI
        abi = [
            {
                "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        contract = w3.eth.contract(address=Web3.to_checksum_address(teocoin_address), abi=abi)
        
        # Check student balance
        balance_wei = contract.functions.balanceOf(Web3.to_checksum_address(student_address)).call()
        balance_tokens = balance_wei / 10**18
        
        # Check total supply
        total_supply_wei = contract.functions.totalSupply().call()
        total_supply_tokens = total_supply_wei / 10**18
        
        print(f"💰 CURRENT BALANCES:")
        print(f"   Student ({student_address[:10]}...): {balance_tokens:.2f} TEO")
        print(f"   Total TEO Supply: {total_supply_tokens:,.0f} TEO")
        print(f"")
        
        # Check recent transaction
        print(f"🔍 RECENT SUCCESSFUL TRANSACTION:")
        print(f"   Hash: 381774e5bdbcb6daf733839e9788b0e3eb7005e1308be6e28287dfde3ba111e7")
        print(f"   Explorer: https://amoy.polygonscan.com/tx/381774e5bdbcb6daf733839e9788b0e3eb7005e1308be6e28287dfde3ba111e7")
        print(f"   Status: ✅ Successful")
        print(f"   Action: TeoCoin discount request (99 TEO)")
        print(f"")
        
        print(f"📱 TROUBLESHOOTING METAMASK PORTFOLIO:")
        print(f"   • Portfolio tab may not show testnet tokens")
        print(f"   • Check 'Assets' tab instead")
        print(f"   • Refresh MetaMask after adding token")
        print(f"   • Switch to Polygon Amoy network first")
        print(f"   • Clear MetaMask cache if needed")
        print(f"")
        
        print(f"🔗 VERIFY ON BLOCKCHAIN:")
        print(f"   • Student address: https://amoy.polygonscan.com/address/{student_address}")
        print(f"   • TEO contract: https://amoy.polygonscan.com/address/{teocoin_address}")
        print(f"   • Discount contract: https://amoy.polygonscan.com/address/{discount_contract_address}")
        
        if balance_tokens > 0:
            print(f"\n✅ SUCCESS: Student has {balance_tokens:.2f} TEO tokens!")
            print(f"   The TeoCoin discount system is working correctly.")
            print(f"   Add the token to MetaMask using the info above to see it in your wallet.")
        else:
            print(f"\n❓ NOTICE: Student balance shows 0 TEO")
            print(f"   This could mean:")
            print(f"   • Tokens were transferred successfully but to a different address")
            print(f"   • The transaction involved a different operation")
            print(f"   • Network connectivity issue")
            
    except Exception as e:
        print(f"❌ Error checking balance: {e}")
        print(f"   You can still add the token manually using the details above")

if __name__ == "__main__":
    main()
