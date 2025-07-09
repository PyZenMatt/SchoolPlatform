#!/usr/bin/env python3
"""
Deploy TeoCoinDiscount Contract to Polygon Amoy

This script deploys the TeoCoinDiscount contract that enables gas-free
discount system for students and teachers.

Requirements:
- DEPLOYER_PRIVATE_KEY environment variable
- Sufficient MATIC in deployer account for gas fees
- TeoCoin2 contract already deployed at known address
"""

import os
import sys
import json
from pathlib import Path
from decimal import Decimal

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
import django
django.setup()

from web3 import Web3
from eth_account import Account
from blockchain.blockchain import TeoCoinService


def load_compiled_contract():
    """Load pre-compiled TeoCoinDiscount contract artifacts"""
    artifact_path = project_root / 'blockchain' / 'contracts' / 'teocoin-contracts' / 'artifacts-zk' / 'contracts' / 'TeoCoinDiscount.sol' / 'TeoCoinDiscount.json'
    
    if not artifact_path.exists():
        raise FileNotFoundError(f"Compiled contract not found at {artifact_path}")
    
    with open(artifact_path, 'r') as file:
        artifact = json.load(file)
    
    return {
        'abi': artifact['abi'],
        'bin': artifact['bytecode']
    }


def deploy_contract():
    """Deploy TeoCoinDiscount contract to Polygon Amoy"""
    
    # Environment checks
    deployer_private_key = os.getenv('DEPLOYER_PRIVATE_KEY')
    if not deployer_private_key:
        print("❌ ERROR: DEPLOYER_PRIVATE_KEY environment variable not set")
        print("   Please set this to your deployer account private key")
        return None
    
    # Initialize TeoCoin service to get existing contract info
    teocoin_service = TeoCoinService()
    w3 = teocoin_service.w3
    
    if not w3.is_connected():
        print("❌ ERROR: Cannot connect to Polygon Amoy network")
        return None
    
    # Get deployer account
    deployer_account = Account.from_key(deployer_private_key)
    deployer_address = deployer_account.address
    
    print(f"🔑 Deployer account: {deployer_address}")
    
    # Check deployer balance
    balance = w3.eth.get_balance(deployer_address)
    balance_matic = w3.from_wei(balance, 'ether')
    print(f"💰 Deployer balance: {balance_matic:.4f} MATIC")
    
    if balance_matic < 0.1:
        print("⚠️  WARNING: Low MATIC balance. You may need more MATIC for deployment.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return None
    
    # Get existing contract addresses
    teocoin_address = teocoin_service.contract.address
    reward_pool_address = teocoin_service.reward_pool_address
    
    print(f"🪙 TeoCoin2 address: {teocoin_address}")
    print(f"🏦 Reward pool address: {reward_pool_address}")
    
    # Load compiled contract
    try:
        contract_interface = load_compiled_contract()
    except Exception as e:
        print(f"❌ ERROR loading compiled contract: {e}")
        return None
    
    # Create contract instance
    contract = w3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bin']
    )
    
    # Prepare constructor arguments
    constructor_args = [
        teocoin_address,           # TEO token address
        reward_pool_address,       # Reward pool address  
        deployer_address          # Platform account (will be updated later)
    ]
    
    print(f"🏗️  Preparing deployment with constructor args:")
    print(f"   TEO Token: {constructor_args[0]}")
    print(f"   Reward Pool: {constructor_args[1]}")
    print(f"   Platform Account: {constructor_args[2]}")
    
    # Build deployment transaction
    try:
        transaction = contract.constructor(*constructor_args).build_transaction({
            'from': deployer_address,
            'nonce': w3.eth.get_transaction_count(deployer_address),
            'gas': 3000000,  # 3M gas limit
            'gasPrice': w3.eth.gas_price,
        })
        
        # Estimate gas
        gas_estimate = w3.eth.estimate_gas(transaction)
        gas_cost_wei = gas_estimate * transaction['gasPrice']
        gas_cost_matic = w3.from_wei(gas_cost_wei, 'ether')
        
        print(f"⛽ Estimated gas: {gas_estimate:,}")
        print(f"💸 Estimated cost: {gas_cost_matic:.6f} MATIC")
        
        # Confirm deployment
        response = input("🚀 Deploy contract? (y/N): ")
        if response.lower() != 'y':
            print("❌ Deployment cancelled")
            return None
        
        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, deployer_private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        print(f"📡 Transaction sent: {tx_hash.hex()}")
        print("⏳ Waiting for confirmation...")
        
        # Wait for confirmation
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            contract_address = receipt['contractAddress']
            print(f"✅ Contract deployed successfully!")
            print(f"📍 Contract address: {contract_address}")
            print(f"🔗 PolygonScan: https://amoy.polygonscan.com/address/{contract_address}")
            print(f"💰 Gas used: {receipt['gasUsed']:,}")
            
            # Save deployment info
            deployment_info = {
                'contract_address': contract_address,
                'deployer_address': deployer_address,
                'teocoin_address': teocoin_address,
                'reward_pool_address': reward_pool_address,
                'transaction_hash': tx_hash.hex(),
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'deployment_timestamp': int(w3.eth.get_block(receipt['blockNumber']).get('timestamp', 0)),
                'abi': contract_interface['abi']
            }
            
            # Save to file
            deployment_file = project_root / 'blockchain' / 'deployed_contracts' / 'teocoin_discount.json'
            deployment_file.parent.mkdir(exist_ok=True)
            
            with open(deployment_file, 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            print(f"💾 Deployment info saved to: {deployment_file}")
            
            # Print configuration for settings.py
            print("\n" + "="*60)
            print("📋 CONFIGURATION FOR SETTINGS.PY:")
            print("="*60)
            print(f"TEOCOIN_DISCOUNT_CONTRACT_ADDRESS = '{contract_address}'")
            print(f"# Add this ABI to TEOCOIN_DISCOUNT_CONTRACT_ABI in settings.py")
            print("\n✅ Deployment complete! Update your settings.py with the above values.")
            
            return contract_address
            
        else:
            print(f"❌ Transaction failed!")
            print(f"📄 Receipt: {receipt}")
            return None
            
    except Exception as e:
        print(f"❌ ERROR during deployment: {e}")
        return None


def verify_deployment(contract_address):
    """Verify the deployed contract is working correctly"""
    print(f"\n🔍 Verifying deployment at {contract_address}...")
    
    teocoin_service = TeoCoinService()
    w3 = teocoin_service.w3
    
    # Load deployment info
    deployment_file = project_root / 'blockchain' / 'deployed_contracts' / 'teocoin_discount.json'
    
    if not deployment_file.exists():
        print("❌ No deployment info found")
        return False
    
    with open(deployment_file, 'r') as f:
        deployment_info = json.load(f)
    
    # Create contract instance
    contract = w3.eth.contract(
        address=contract_address,
        abi=deployment_info['abi']
    )
    
    try:
        # Test basic contract functions
        teo_token = contract.functions.teoToken().call()
        reward_pool = contract.functions.rewardPool().call()
        platform_account = contract.functions.platformAccount().call()
        
        print(f"✅ TEO Token: {teo_token}")
        print(f"✅ Reward Pool: {reward_pool}")
        print(f"✅ Platform Account: {platform_account}")
        
        # Test cost calculation
        teo_cost, teacher_bonus = contract.functions.calculateTeoCost(10000, 10).call()  # €100, 10%
        print(f"✅ Cost calculation working: {teo_cost / 10**18:.2f} TEO cost, {teacher_bonus / 10**18:.2f} TEO bonus")
        
        # Check current request counter
        current_id = contract.functions.getCurrentRequestId().call()
        print(f"✅ Current request ID: {current_id}")
        
        print("🎉 Contract verification successful!")
        return True
        
    except Exception as e:
        print(f"❌ Contract verification failed: {e}")
        return False


def main():
    """Main deployment script"""
    print("🚀 TeoCoinDiscount Contract Deployment Script")
    print("=" * 50)
    
    # Deploy contract
    contract_address = deploy_contract()
    
    if contract_address:
        # Verify deployment
        if verify_deployment(contract_address):
            print("\n🎉 SUCCESS! TeoCoinDiscount contract is ready to use!")
            print("\n📋 NEXT STEPS:")
            print("1. Update TEOCOIN_DISCOUNT_CONTRACT_ADDRESS in settings.py")
            print("2. Add the ABI to TEOCOIN_DISCOUNT_CONTRACT_ABI")
            print("3. Set PLATFORM_PRIVATE_KEY for gas-free operations")
            print("4. Test the discount system end-to-end")
            print("5. Deploy to mainnet when ready")
        else:
            print("\n⚠️  Deployment completed but verification failed")
            print("Please check the contract manually on PolygonScan")
    else:
        print("\n❌ Deployment failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
