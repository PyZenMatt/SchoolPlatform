#!/usr/bin/env python3
"""
Mint test TEO tokens for testing the discount system
"""

import os
import sys
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from users.models import User

def mint_test_tokens():
    """Mint test TEO tokens for testing"""
    
    print("🪙 Minting Test TEO Tokens...")
    print("=" * 50)
    
    try:
        # Initialize TeoCoin service
        teo_service = TeoCoinService()
        
        # Get admin user wallet address
        admin_user = User.objects.filter(is_superuser=True).first()
        
        # For testing, we'll use the admin wallet address or create a test address
        test_wallet = "0x17051AB7603B0F7263BC86bF1b0ce137EFfdEcc1"  # Admin wallet from .env
        
        print(f"🎯 Test wallet: {test_wallet}")
        
        # Check current balance
        current_balance = teo_service.get_balance(test_wallet)
        print(f"📊 Current balance: {current_balance} TEO")
        
        # Mint test tokens (1000 TEO for testing)
        from decimal import Decimal
        mint_amount = Decimal('1000')
        print(f"🏭 Minting {mint_amount} TEO tokens...")
        
        result = teo_service.mint_tokens(
            to_address=test_wallet,
            amount=mint_amount
        )
        
        if result.get('success'):
            print(f"✅ Minted {mint_amount} TEO successfully!")
            print(f"📜 Transaction: {result.get('transaction_hash', 'Unknown')}")
            
            # Check new balance
            new_balance = teo_service.get_balance(test_wallet)
            print(f"📊 New balance: {new_balance} TEO")
            
        else:
            print(f"❌ Minting failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error minting tokens: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("🎯 Testing Instructions:")
    print("1. Add TEO token to MetaMask:")
    print("   - Contract: 0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8")
    print("   - Symbol: TEO")
    print("   - Decimals: 18")
    print("2. Import the test wallet into MetaMask:")
    print("   - Private Key: e1636922fa350bfe8ed929096d330eb70bbe3dc17dbb03dacdcf1dd668fc4255")
    print("3. Test TeoCoin discount payments!")

if __name__ == "__main__":
    mint_test_tokens()
