"""
Staking Cont    0: {'min_stake': 0, 'commission_rate': 5000, 'name': 'Bronze'},      # 50%
    1: {'min_stake': 100, 'commission_rate': 4400, 'name': 'Silver'},    # 44%
    2: {'min_stake': 300, 'commission_rate': 3800, 'name': 'Gold'},      # 38%
    3: {'min_stake': 600, 'commission_rate': 3100, 'name': 'Platinum'},  # 31%
    4: {'min_stake': 1000, 'commission_rate': 2500, 'name': 'Diamond'},  # 25%Configuration

This file will be updated after contract deployment with the actual contract address and ABI.
For now, it contains placeholder values and configuration for local development.
"""

# Contract deployment info (LIVE CONTRACTS - July 1, 2025)
STAKING_CONTRACT_ADDRESS = "0xd74fc566c0c5b83f95fd82e6866d8a7a6eaca7a9"  # Live on Polygon Amoy
STAKING_ABI = None  # Will be loaded from ThirdWeb artifacts

# Production Configuration - Live Contracts
DEVELOPMENT_MODE = False

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
    """Load contract configuration - now using live deployed contracts"""
    import json
    import os
    from django.conf import settings
    
    try:
        # Load ABI from the extracted file
        abi_file = os.path.join(settings.BASE_DIR, 'blockchain', 'staking_abi.json')
        if os.path.exists(abi_file):
            with open(abi_file, 'r') as f:
                abi_data = json.load(f)
            
            # Use live contract configuration
            return {
                'address': STAKING_CONTRACT_ADDRESS,
                'abi': abi_data,
                'development_mode': DEVELOPMENT_MODE
            }
    except Exception as e:
        print(f"Could not load live contract config: {e}")
    
    # Fallback to development configuration
    return {
        'address': None,
        'abi': SAMPLE_STAKING_ABI,
        'development_mode': True
    }
