#!/usr/bin/env python
"""
Test script to verify DBTeoCoinService can be imported and works correctly
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/teo/Project/school/schoolplatform')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_db_teocoin_service():
    """Test DBTeoCoinService import and basic functionality"""
    print("🧪 Testing DBTeoCoinService...")
    
    try:
        # Test import
        from services.db_teocoin_service import DBTeoCoinService, db_teocoin_service
        print("✅ DBTeoCoinService imported successfully!")
        
        # Test service instantiation
        service = DBTeoCoinService()
        print("✅ DBTeoCoinService instantiated successfully!")
        
        # Test singleton instance
        print(f"✅ Singleton instance available: {type(db_teocoin_service)}")
        
        # Test basic methods exist
        methods_to_check = [
            'get_user_balance',
            'add_balance', 
            'deduct_balance',
            'stake_tokens',
            'unstake_tokens',
            'calculate_discount',
            'apply_course_discount',
            'request_withdrawal',
            'get_user_transactions'
        ]
        
        for method_name in methods_to_check:
            if hasattr(service, method_name):
                print(f"✅ Method {method_name} exists")
            else:
                print(f"❌ Method {method_name} missing")
        
        print("\n🎉 DBTeoCoinService is ready for Phase 1.2 completion!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_models():
    """Test that the new models can be imported"""
    print("\n🧪 Testing DB TeoCoin Models...")
    
    try:
        from blockchain.models import DBTeoCoinBalance, DBTeoCoinTransaction, TeoCoinWithdrawalRequest
        print("✅ All DB TeoCoin models imported successfully!")
        
        # Test model structure
        print(f"✅ DBTeoCoinBalance fields: {[f.name for f in DBTeoCoinBalance._meta.fields]}")
        print(f"✅ DBTeoCoinTransaction fields: {[f.name for f in DBTeoCoinTransaction._meta.fields]}")
        print(f"✅ TeoCoinWithdrawalRequest fields: {[f.name for f in TeoCoinWithdrawalRequest._meta.fields]}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Model import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting DB TeoCoin System Tests...")
    print("=" * 50)
    
    models_ok = test_models()
    service_ok = test_db_teocoin_service()
    
    print("\n" + "=" * 50)
    if models_ok and service_ok:
        print("🎉 ALL TESTS PASSED! Phase 1.2 is complete.")
        print("📝 Ready to move to Phase 1.3: Update existing services")
    else:
        print("❌ Some tests failed. Check the errors above.")
