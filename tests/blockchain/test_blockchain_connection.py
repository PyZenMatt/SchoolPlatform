#!/usr/bin/env python3

import os
import sys
import django

# Add the parent directory to the Python path
sys.path.append('/home/teo/Project/school/schoolplatform')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from users.models import User
from decimal import Decimal
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_blockchain_connection():
    """
    Test basic blockchain connectivity and functionality
    """
    print("=== Testing Blockchain Connection ===")
    
    try:
        service = TeoCoinService()
        print("✅ TeoCoinService initialized successfully")
        
        # Test connection
        if hasattr(service, 'w3') and service.w3:
            is_connected = service.w3.is_connected()
            print(f"Web3 connection status: {is_connected}")
            
            if is_connected:
                # Get latest block
                latest_block = service.w3.eth.block_number
                print(f"Latest block number: {latest_block}")
                
                # Get gas price
                gas_price = service.get_optimized_gas_price()
                print(f"Optimized gas price: {gas_price/1e9:.2f} gwei")
            else:
                print("❌ Not connected to blockchain network")
                return False
        else:
            print("❌ Web3 instance not initialized")
            return False
            
    except Exception as e:
        print(f"❌ Error initializing blockchain service: {e}")
        return False
    
    return True

def test_simple_mint():
    """
    Test a simple mint operation
    """
    print("\n=== Testing Simple Mint Operation ===")
    
    try:
        service = TeoCoinService()
        
        # Find a user with wallet address
        user = User.objects.filter(wallet_address__isnull=False).first()
        
        if not user:
            print("❌ No user with wallet address found")
            return
        
        print(f"Testing mint to {user.username} ({user.wallet_address})")
        
        # Get balance before
        balance_before = service.get_balance(user.wallet_address)
        print(f"Balance before: {balance_before} TEO")
        
        # Try to mint 1 TEO
        print("Attempting to mint 1 TEO...")
        tx_hash = service.mint_tokens(user.wallet_address, Decimal('1'))
        
        if tx_hash:
            print(f"✅ Mint successful - TX Hash: {tx_hash}")
            
            # Wait a moment and check balance
            import time
            time.sleep(5)
            
            balance_after = service.get_balance(user.wallet_address)
            print(f"Balance after: {balance_after} TEO")
            
        else:
            print("❌ Mint returned None - check blockchain service logs")
            
    except Exception as e:
        print(f"❌ Error during mint test: {e}")
        import traceback
        traceback.print_exc()

def check_environment_variables():
    """
    Check if all required environment variables are set
    """
    print("\n=== Checking Environment Variables ===")
    
    from django.conf import settings
    
    required_vars = [
        'POLYGON_AMOY_RPC_URL',
        'TEOCOIN_CONTRACT_ADDRESS', 
        'ADMIN_PRIVATE_KEY',
        'REWARD_POOL_ADDRESS',
        'REWARD_POOL_PRIVATE_KEY'
    ]
    
    for var in required_vars:
        value = getattr(settings, var, None)
        if value:
            if 'PRIVATE_KEY' in var:
                print(f"✅ {var}: {'*' * 20} (set)")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")

if __name__ == "__main__":
    try:
        check_environment_variables()
        
        if test_blockchain_connection():
            test_simple_mint()
    except Exception as e:
        logger.error(f"Error during blockchain test: {e}")
        import traceback
        traceback.print_exc()
