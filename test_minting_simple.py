#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

# Add the project root to Python path
sys.path.append('/home/teo/Project/school/schoolplatform')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from services.teocoin_withdrawal_service import TeoCoinWithdrawalService
from django.conf import settings

def test_minting_setup():
    """Test if minting setup is working without actual transaction"""
    print("🎯 TeoCoin Minting Setup Test")
    print("=" * 50)
    
    # Check configuration
    print(f"🏛️ Platform wallet: {settings.PLATFORM_WALLET_ADDRESS}")
    print(f"📍 TeoCoin contract: {settings.TEOCOIN_CONTRACT_ADDRESS}")
    print(f"🔑 Private key configured: {'✅' if settings.PLATFORM_PRIVATE_KEY else '❌'}")
    print(f"🌐 Polygon RPC: {getattr(settings, 'POLYGON_AMOY_RPC_URL', 'Not configured')}")
    print()
    
    # Test service initialization
    withdrawal_service = TeoCoinWithdrawalService()
    
    # Test contract connection
    contract = withdrawal_service.teo_contract
    if contract:
        print(f"✅ Contract connection: {contract.address}")
        
        # Check if mintTo function exists
        if hasattr(contract.functions, 'mintTo'):
            print("✅ mintTo function available")
        elif hasattr(contract.functions, 'mint'):
            print("✅ mint function available")
        else:
            print("❌ No mint function found")
    else:
        print("❌ Contract connection failed")
    
    # Test gas estimation without transaction
    test_address = "0x742d35Cc6634C0532925a3b8d4017d6e2b3D7567"
    test_amount = Decimal("10.0")
    
    try:
        # Convert amount to Wei
        amount_wei = withdrawal_service.web3.to_wei(test_amount, 'ether')
        
        # Get function
        if hasattr(contract.functions, 'mintTo'):
            mint_function = contract.functions.mintTo(test_address, amount_wei)
        else:
            mint_function = contract.functions.mint(test_address, amount_wei)
        
        # Estimate gas
        platform_address = settings.PLATFORM_WALLET_ADDRESS
        gas_estimate = mint_function.estimate_gas({'from': platform_address})
        print(f"⛽ Gas estimation test: {gas_estimate}")
        print("✅ Minting setup is working correctly!")
        
    except Exception as e:
        print(f"❌ Gas estimation failed: {e}")
    
    print("\n💡 Next steps:")
    print("   1. Ensure PLATFORM_PRIVATE_KEY is set in environment")
    print("   2. Ensure platform wallet has MATIC for gas fees")
    print("   3. Run actual withdrawal processing")

if __name__ == "__main__":
    test_minting_setup()
