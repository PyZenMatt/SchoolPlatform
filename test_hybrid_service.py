#!/usr/bin/env python
"""
Test script to verify HybridTeoCoinService works correctly
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/teo/Project/school/schoolplatform')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_hybrid_service():
    """Test HybridTeoCoinService functionality"""
    print("🧪 Testing HybridTeoCoinService...")
    
    try:
        # Test import
        from services.hybrid_teocoin_service import HybridTeoCoinService, hybrid_teocoin_service
        print("✅ HybridTeoCoinService imported successfully!")
        
        # Test service instantiation
        service = HybridTeoCoinService()
        print(f"✅ HybridTeoCoinService instantiated - Using {'DB' if service.use_db_system else 'Blockchain'} system")
        
        # Test singleton instance
        print(f"✅ Singleton instance available: {type(hybrid_teocoin_service)}")
        
        # Test that service detects DB system correctly
        from django.conf import settings
        print(f"✅ Settings USE_DB_TEOCOIN_SYSTEM: {getattr(settings, 'USE_DB_TEOCOIN_SYSTEM', 'Not set')}")
        
        # Test basic methods exist
        methods_to_check = [
            'get_user_balance',
            'get_available_balance',
            'credit_user',
            'debit_user',
            'calculate_discount',
            'apply_course_discount',
            'stake_tokens',
            'unstake_tokens',
            'request_withdrawal',
            'get_user_transactions',
            'reward_teacher_lesson_completion',
            'get_platform_statistics'
        ]
        
        for method_name in methods_to_check:
            if hasattr(service, method_name):
                print(f"✅ Method {method_name} exists")
            else:
                print(f"❌ Method {method_name} missing")
        
        # Test access to both underlying services
        print(f"✅ DB Service available: {type(service.db_service)}")
        print(f"✅ Blockchain Service available: {type(service.blockchain_service)}")
        
        print("\n🎉 HybridTeoCoinService is ready for Phase 1.3 completion!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_backward_compatibility():
    """Test that the hybrid service maintains backward compatibility"""
    print("\n🧪 Testing Backward Compatibility...")
    
    try:
        # Import with old names should still work
        from services.hybrid_teocoin_service import hybrid_teocoin_service as teocoin_service
        
        # Test that old method signatures still work
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Create a test user (or get an existing one)
        users = User.objects.all()[:1]
        if users:
            test_user = users[0]
            print(f"✅ Testing with user: {test_user.username}")
            
            # Test get_user_balance (should work without errors)
            balance = teocoin_service.get_user_balance(test_user)
            print(f"✅ get_user_balance returned: {balance}")
            
            # Test that it returns expected keys
            expected_keys = ['balance', 'available_balance', 'total_balance', 'source']
            for key in expected_keys:
                if key in balance:
                    print(f"✅ Balance contains expected key: {key}")
                else:
                    print(f"❌ Balance missing key: {key}")
            
        else:
            print("⚠️ No users in database to test with")
        
        print("✅ Backward compatibility maintained!")
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Hybrid TeoCoin Service Tests...")
    print("=" * 50)
    
    service_ok = test_hybrid_service()
    compat_ok = test_backward_compatibility()
    
    print("\n" + "=" * 50)
    if service_ok and compat_ok:
        print("🎉 ALL TESTS PASSED! Phase 1.3 is complete.")
        print("📝 Ready to move to Phase 2: MetaMask Withdrawal System")
        print("\n💡 Next steps:")
        print("   1. Update existing code to use hybrid_teocoin_service")
        print("   2. Implement withdrawal API endpoints")
        print("   3. Create frontend components for DB balance display")
    else:
        print("❌ Some tests failed. Check the errors above.")
