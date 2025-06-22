"""
Staking Contract Configuration

This file will be updated after contract deployment with the actual contract address and ABI.
For now, it contains placeholder values and configuration for local development.
"""

# Contract deployment info (to be updated after deployment)
STAKING_CONTRACT_ADDRESS = None  # Will be set after deployment
STAKING_ABI = None  # Will be set after deployment

# Development/Testing Configuration
DEVELOPMENT_MODE = True

# If no deployed contract, use these settings for simulation
TIER_CONFIG = {
    0: {'min_stake': 0, 'commission_rate': 2500, 'name': 'Bronze'},      # 25%
    1: {'min_stake': 100, 'commission_rate': 2200, 'name': 'Silver'},    # 22%
    2: {'min_stake': 300, 'commission_rate': 1900, 'name': 'Gold'},      # 19%
    3: {'min_stake': 600, 'commission_rate': 1600, 'name': 'Platinum'},  # 16%
    4: {'min_stake': 1000, 'commission_rate': 1500, 'name': 'Diamond'}   # 15%
}

# Sample ABI for reference (will be replaced with actual after compilation)
SAMPLE_STAKING_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "_teoToken", "type": "address"}],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "getUserStakingInfo",
        "outputs": [
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "uint256", "name": "tier", "type": "uint256"},
            {"internalType": "uint256", "name": "stakingTime", "type": "uint256"},
            {"internalType": "bool", "name": "active", "type": "bool"},
            {"internalType": "string", "name": "tierName", "type": "string"},
            {"internalType": "uint256", "name": "commissionRate", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getStakingStats",
        "outputs": [
            {"internalType": "uint256", "name": "_totalStaked", "type": "uint256"},
            {"internalType": "uint256", "name": "_totalStakers", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "name": "stake",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}],
        "name": "unstake",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def load_contract_config():
    """Load contract configuration after deployment"""
    try:
        import json
        import os
        
        # Try to load from deployment_info.json if it exists
        deployment_file = 'deployment_info.json'
        if os.path.exists(deployment_file):
            with open(deployment_file, 'r') as f:
                deployment_info = json.load(f)
                
            global STAKING_CONTRACT_ADDRESS, STAKING_ABI, DEVELOPMENT_MODE
            STAKING_CONTRACT_ADDRESS = deployment_info.get('contract_address')
            STAKING_ABI = deployment_info.get('abi')
            DEVELOPMENT_MODE = False
            
            return {
                'address': STAKING_CONTRACT_ADDRESS,
                'abi': STAKING_ABI,
                'development_mode': False
            }
    except Exception as e:
        print(f"Could not load contract config: {e}")
    
    # Return development configuration
    return {
        'address': None,
        'abi': SAMPLE_STAKING_ABI,
        'development_mode': True
    }
