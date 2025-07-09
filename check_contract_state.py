#!/usr/bin/env python3
"""
Check smart contract state and permissions
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from web3 import Web3
from eth_account import Account

def check_contract_state():
    """Check the deployed contract state and permissions"""
    
    print("🔍 CHECKING SMART CONTRACT STATE AND PERMISSIONS")
    print("=" * 60)
    
    # Connect to blockchain
    rpc_url = os.getenv('POLYGON_AMOY_RPC_URL', 'https://rpc-amoy.polygon.technology/')
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    contract_address = Web3.to_checksum_address("0xd30afec0bc6ac33e14a0114ec7403bbd746e88de")
    platform_private_key = os.getenv('PLATFORM_PRIVATE_KEY')
    platform_account = Account.from_key(platform_private_key)
    
    print(f"Connection:")
    print(f"   RPC: {rpc_url}")
    print(f"   Contract: {contract_address}")
    print(f"   Platform: {platform_account.address}")
    
    # Extended ABI for checking contract state
    extended_abi = [
        {
            "inputs": [],
            "name": "getCurrentRequestId",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "platformAccount",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "rewardPool", 
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "adminWallet",
            "outputs": [{"internalType": "address", "name": "", "type": "address"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "TEO_TO_EUR_RATE",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "TEACHER_BONUS_PERCENT",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"internalType": "uint256", "name": "coursePrice", "type": "uint256"},
                {"internalType": "uint256", "name": "discountPercent", "type": "uint256"}
            ],
            "name": "calculateTeoCost",
            "outputs": [
                {"internalType": "uint256", "name": "", "type": "uint256"},
                {"internalType": "uint256", "name": "", "type": "uint256"}
            ],
            "stateMutability": "pure",
            "type": "function"
        }
    ]
    
    try:
        contract = w3.eth.contract(address=contract_address, abi=extended_abi)
        
        print(f"\n📊 CONTRACT STATE:")
        
        # Check basic state
        current_id = contract.functions.getCurrentRequestId().call()
        print(f"   Current request ID: {current_id}")
        
        # Check key addresses
        try:
            platform_addr = contract.functions.platformAccount().call()
            print(f"   Platform account: {platform_addr}")
            print(f"   Our platform: {platform_account.address}")
            print(f"   Platform match: {platform_addr.lower() == platform_account.address.lower()}")
        except Exception as e:
            print(f"   ❌ Platform account read failed: {e}")
            
        try:
            reward_pool = contract.functions.rewardPool().call()
            print(f"   Reward pool: {reward_pool}")
        except Exception as e:
            print(f"   ❌ Reward pool read failed: {e}")
            
        try:
            admin_wallet = contract.functions.adminWallet().call()
            print(f"   Admin wallet: {admin_wallet}")
        except Exception as e:
            print(f"   ❌ Admin wallet read failed: {e}")
            
        # Check rates and percentages
        try:
            teo_rate = contract.functions.TEO_TO_EUR_RATE().call()
            print(f"   TEO to EUR rate: {teo_rate}")
        except Exception as e:
            print(f"   ❌ TEO rate read failed: {e}")
            
        try:
            bonus_percent = contract.functions.TEACHER_BONUS_PERCENT().call()
            print(f"   Teacher bonus %: {bonus_percent}")
        except Exception as e:
            print(f"   ❌ Bonus percent read failed: {e}")
            
        # Test calculation function
        print(f"\n🧮 TESTING CONTRACT CALCULATION:")
        try:
            # Test with our parameters
            course_price = 9999  # €99.99
            discount_percent = 10
            
            teo_cost, teacher_bonus = contract.functions.calculateTeoCost(course_price, discount_percent).call()
            print(f"   Course price: {course_price} cents")
            print(f"   Discount: {discount_percent}%")
            print(f"   Contract TEO cost: {teo_cost}")
            print(f"   Contract teacher bonus: {teacher_bonus}")
            
            # Compare with our calculation
            our_discount_value = (course_price * discount_percent) // 100
            our_teo_cost = (our_discount_value * 100) // 100  # Using TEO_TO_EUR_RATE = 100
            our_bonus = (our_teo_cost * 25) // 100  # Using TEACHER_BONUS_PERCENT = 25
            
            print(f"   Our calculation:")
            print(f"     Discount value: {our_discount_value}")
            print(f"     TEO cost: {our_teo_cost}")
            print(f"     Teacher bonus: {our_bonus}")
            print(f"   Match: {teo_cost == our_teo_cost and teacher_bonus == our_bonus}")
            
        except Exception as calc_error:
            print(f"   ❌ Calculation test failed: {calc_error}")
            
        # Check if there are any paused/disabled states
        print(f"\n🔒 CHECKING CONTRACT PERMISSIONS:")
        
        # Try to see if we can read any pause/disable flags
        # (Note: these might not exist, but worth checking)
        try:
            # Common paused state check
            code = w3.eth.get_code(contract_address)
            print(f"   Contract code length: {len(code)} bytes")
            print(f"   Contract has code: {len(code) > 0}")
        except Exception as e:
            print(f"   ❌ Code check failed: {e}")
            
        return True
        
    except Exception as contract_error:
        print(f"❌ Contract interaction failed: {contract_error}")
        return False

if __name__ == "__main__":
    success = check_contract_state()
    
    if success:
        print(f"\n✅ Contract state check completed")
        print(f"\n💡 NEXT STEPS:")
        print(f"   1. Verify platform account matches contract expectation")
        print(f"   2. Check if TEO cost calculation matches exactly")
        print(f"   3. Verify contract is not paused or restricted")
    else:
        print(f"\n❌ Contract state check failed")
        print(f"   The contract might not be deployed or accessible")
