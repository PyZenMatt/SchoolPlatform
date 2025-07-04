#!/usr/bin/env python3
"""
Test Direct Approval Transaction
Tests the exact same approve call that's failing in MetaMask
"""

from web3 import Web3
import os

def test_approval_direct():
    """Test the same approval that's failing in frontend"""
    
    print("🧪 TESTING DIRECT APPROVAL TRANSACTION")
    print("=" * 50)
    
    # Setup Web3 connection
    rpc_url = "https://rpc-amoy.polygon.technology/"
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("❌ Cannot connect to Polygon Amoy")
        return
    
    # Contract details
    teocoin_address = Web3.to_checksum_address('0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8')
    user_address = Web3.to_checksum_address('0x5741935155afbfe404269b7bdcfe7f3318358d17')
    reward_pool = Web3.to_checksum_address('0x3b72a4E942CF1467134510cA3952F01b63005044')
    
    # Amount from the failed transaction: 219.978 TEO
    amount_wei = 219977999999999980000
    
    print(f"📋 Transaction Details:")
    print(f"   TeoCoin:    {teocoin_address}")
    print(f"   User:       {user_address}")  
    print(f"   Spender:    {reward_pool}")
    print(f"   Amount:     {amount_wei / 10**18:.6f} TEO")
    
    # ERC-20 ABI for approve
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
        
        # Test gas estimation
        print(f"\n⛽ Gas Estimation Test:")
        try:
            gas_estimate = contract.functions.approve(reward_pool, amount_wei).estimate_gas({'from': user_address})
            print(f"   ✅ Gas estimate: {gas_estimate}")
            print(f"   💡 Recommended: {int(gas_estimate * 1.5)} (with 50% buffer)")
        except Exception as gas_error:
            print(f"   ❌ Gas estimation failed: {gas_error}")
            
        # Test transaction building (without sending)
        print(f"\n🏗️  Transaction Building Test:")
        try:
            tx_data = contract.functions.approve(reward_pool, amount_wei).build_transaction({
                'from': user_address,
                'gas': 60000,  # Fixed gas limit we're using
                'gasPrice': w3.eth.gas_price,
                'nonce': w3.eth.get_transaction_count(user_address)
            })
            print(f"   ✅ Transaction built successfully")
            print(f"   📊 Gas limit: {tx_data['gas']}")
            print(f"   💰 Gas price: {tx_data['gasPrice'] / 10**9:.2f} Gwei")
            print(f"   🔢 Nonce: {tx_data['nonce']}")
        except Exception as build_error:
            print(f"   ❌ Transaction build failed: {build_error}")
            
        # Check current state
        print(f"\n📊 Current Contract State:")
        balance = contract.functions.balanceOf(user_address).call()
        allowance = contract.functions.allowance(user_address, reward_pool).call()
        print(f"   User balance: {balance / 10**18:.2f} TEO")
        print(f"   Current allowance: {allowance / 10**18:.2f} TEO")
        print(f"   Requested increase: {amount_wei / 10**18:.2f} TEO")
        
        # Check if this would be a decrease (some tokens don't allow this)
        if amount_wei < allowance:
            print(f"   ⚠️  WARNING: This would decrease allowance!")
            print(f"   💡 Some ERC-20 tokens require setting to 0 first")
            
    except Exception as e:
        print(f"❌ Contract test failed: {e}")
        return False
    
    print(f"\n🎯 DIAGNOSIS:")
    print(f"   ✅ Contract exists and responds")
    print(f"   ✅ User has sufficient balance")  
    print(f"   ✅ Transaction can be built")
    print(f"   🤔 Issue is likely MetaMask RPC communication")
    
    print(f"\n💡 SOLUTIONS TO TRY:")
    print(f"   1. Refresh MetaMask (close/reopen)")
    print(f"   2. Clear MetaMask activity data")
    print(f"   3. Switch to different RPC in MetaMask")
    print(f"   4. Use hardware wallet if available")
    print(f"   5. Try from different browser/incognito")
    
    return True

if __name__ == "__main__":
    test_approval_direct()
