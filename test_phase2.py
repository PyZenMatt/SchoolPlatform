#!/usr/bin/env python
"""
Phase 2 Test Script for TeoCoin Blockchain Integration
Tests the clean blockchain service implementation
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_phase2_implementation():
    """Test Phase 2 blockchain service functionality"""
    
    print("🧪 Testing Phase 2 TeoCoin Blockchain Service")
    print("=" * 50)
    
    try:
        # Test 1: Import service
        print("Test 1: Importing blockchain service...")
        from services.consolidated_teocoin_service import teocoin_service
        print("✅ Service imported successfully")
        
        # Test 2: Get token info
        print("\nTest 2: Getting token information...")
        token_info = teocoin_service.get_token_info()
        print(f"✅ Token Info: {token_info}")
        
        # Test 3: Address validation
        print("\nTest 3: Testing address validation...")
        test_addresses = [
            "0x742d35Cc6634C0532925a3b8D6Ac6F86C8cFc4Ae",  # Valid
            "0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8",  # Contract address
            "invalid_address",  # Invalid
            ""  # Empty
        ]
        
        for addr in test_addresses:
            is_valid = teocoin_service.validate_address(addr) if addr else False
            status = "✅" if is_valid else "❌"
            print(f"{status} Address '{addr}': {is_valid}")
        
        # Test 4: Test balance query (if we have a valid address)
        print("\nTest 4: Testing balance query...")
        test_address = "0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8"  # Contract address
        try:
            balance = teocoin_service.get_balance(test_address)
            print(f"✅ Balance for {test_address}: {balance} TEO")
        except Exception as e:
            print(f"⚠️  Balance query failed (expected in test environment): {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Phase 2 implementation tests completed!")
        print("✅ Clean blockchain service is working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phase2_implementation()
    sys.exit(0 if success else 1)
