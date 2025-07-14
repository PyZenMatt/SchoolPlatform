#!/usr/bin/env python
"""
Test script for burn deposit functionality
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from services.db_teocoin_service import DBTeoCoinService

User = get_user_model()

def test_credit_user():
    """Test the credit_user method"""
    print("🧪 Testing credit_user method...")
    
    try:
        # Get a test user
        user = User.objects.filter(email__contains='test').first()
        if not user:
            user = User.objects.first()
        
        if not user:
            print("❌ No users found in database")
            return False
        
        print(f"✅ Using test user: {user.email}")
        
        # Get initial balance
        db_service = DBTeoCoinService()
        initial_balance = db_service.get_available_balance(user)
        print(f"📊 Initial balance: {initial_balance} TEO")
        
        # Test credit_user method
        test_amount = Decimal('25.50')
        result = db_service.credit_user(
            user=user,
            amount=test_amount,
            transaction_type='deposit',
            description='Test burn deposit',
            metadata={
                'transaction_hash': '0x123test456',
                'metamask_address': '0xtest123',
                'block_number': 12345
            }
        )
        
        print(f"💰 Credit result: {result}")
        
        if result.get('success'):
            new_balance = db_service.get_available_balance(user)
            print(f"📊 New balance: {new_balance} TEO")
            print(f"✅ Balance increased by: {new_balance - initial_balance} TEO")
            return True
        else:
            print(f"❌ Credit failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_burn_deposit_api():
    """Test the burn deposit API endpoint"""
    print("\n🧪 Testing burn deposit API...")
    
    try:
        from api.burn_deposit_views import BurnDepositView
        from rest_framework.test import APIRequestFactory
        from django.contrib.auth import get_user_model
        
        factory = APIRequestFactory()
        
        # Get a test user
        user = User.objects.filter(email__contains='test').first()
        if not user:
            user = User.objects.first()
            
        # Create a test request
        request_data = {
            'transaction_hash': '0xfaketest123',
            'amount': '10.00',
            'metamask_address': '0x742d35Cc6634C0532925a3b8d4017d6e2b3D7567'
        }
        
        request = factory.post('/api/burn-deposit/', request_data, format='json')
        request.user = user
        
        view = BurnDepositView()
        view.request = request
        
        # This will fail on verification (fake hash), but we can see if the method structure works
        response = view.post(request)
        print(f"📡 API Response status: {response.status_code}")
        print(f"📄 API Response data: {response.data}")
        
        # We expect this to fail at verification, which is normal
        if response.status_code == 400 and 'Transaction not found' in str(response.data):
            print("✅ API structure is working (failed at verification as expected)")
            return True
        else:
            print("❌ Unexpected API response")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Testing Burn Deposit Functionality\n")
    
    # Test 1: credit_user method
    test1_result = test_credit_user()
    
    # Test 2: API structure
    test2_result = test_burn_deposit_api()
    
    print(f"\n📊 Test Results:")
    print(f"   Credit User Method: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   API Structure: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 All tests passed! Burn deposit should work.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
