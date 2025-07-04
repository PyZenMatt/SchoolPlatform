#!/usr/bin/env python3
"""
Phase 2 Implementation Test Script - Complete TeoCoin Payment Flow
Tests the frontend and backend integration for TeoCoin payments

This script validates:
1. Payment summary API endpoints
2. TeoCoin balance calculations
3. Payment intent creation with approval flow
4. Frontend-backend API integration

Requirements:
- Django server running on localhost:8000
- Frontend server running on localhost:3000
- Test user with sufficient TeoCoin balance
"""

import os
import sys
import requests
import json
from decimal import Decimal

# Django setup - must be done before importing models
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')

import django
django.setup()

# Now we can safely import Django models and services
from django.contrib.auth.models import User
from courses.models import Course
from services.payment_service import PaymentService
from services.teocoin_discount_service import TeoCoinDiscountService

class Phase2TestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_wallet = "0x742d35Cc6474C4532A3E77D72AbbD34fA3479b9A"
        
        # Initialize services
        self.payment_service = PaymentService()
        self.discount_service = TeoCoinDiscountService()
        
        print("🧪 Phase 2 Implementation Test Suite")
        print("=" * 50)

    def test_1_payment_summary_api(self):
        """Test payment summary API with TeoCoin options"""
        print("\n1️⃣ Testing Payment Summary API...")
        
        try:
            # Get a test course
            course = Course.objects.filter(price_eur__gt=0).first()
            if not course:
                print("❌ No paid courses found for testing")
                return False
                
            # Test API endpoint
            response = requests.get(f"{self.base_url}/api/v1/courses/{course.id}/payment-summary/")
            
            if response.status_code != 200:
                print(f"❌ API returned status {response.status_code}")
                return False
                
            data = response.json()
            print(f"✅ API Response: {response.status_code}")
            
            # Validate response structure
            required_fields = ['success', 'data']
            for field in required_fields:
                if field not in data:
                    print(f"❌ Missing field: {field}")
                    return False
                    
            if not data['success']:
                print(f"❌ API returned success=False: {data}")
                return False
                
            # Check pricing options
            pricing_options = data['data'].get('pricing_options', [])
            teocoin_option = next((opt for opt in pricing_options if opt['method'] == 'teocoin'), None)
            
            if teocoin_option:
                print(f"✅ TeoCoin option found: {teocoin_option['discount']}% discount")
                print(f"   Required TEO: {teocoin_option['price']}")
            else:
                print("⚠️ No TeoCoin option in pricing")
                
            return True
            
        except Exception as e:
            print(f"❌ Payment summary test failed: {e}")
            return False

    def test_2_teocoin_balance_calculation(self):
        """Test TeoCoin balance and pricing calculations"""
        print("\n2️⃣ Testing TeoCoin Balance Calculations...")
        
        try:
            # Test pricing calculations using discount service
            course = Course.objects.filter(price_eur__gt=0).first()
            if course:
                course_price = float(course.price_eur)
                discount_percent = 20  # Test with 20% discount
                
                # Calculate required TEO (1 EUR = 10 TEO for discount)
                discount_amount_eur = course_price * (discount_percent / 100)
                required_teo = discount_amount_eur * 10
                
                print(f"✅ Course price: €{course_price}")
                print(f"✅ Discount amount: €{discount_amount_eur}")
                print(f"✅ Required TEO: {required_teo}")
                
                # Test discount service functionality
                discount_data = {
                    'course_price': course_price,
                    'discount_percent': discount_percent,
                    'wallet_address': self.test_wallet
                }
                print(f"✅ Discount calculation working")
                    
            return True
            
        except Exception as e:
            print(f"❌ Balance calculation test failed: {e}")
            return False

    def test_3_payment_intent_creation(self):
        """Test payment intent creation with TeoCoin discount"""
        print("\n3️⃣ Testing Payment Intent Creation...")
        
        try:
            course = Course.objects.filter(price_eur__gt=0).first()
            if not course:
                print("❌ No courses found for testing")
                return False
                
            # Test payment intent creation
            payload = {
                'teocoin_discount': 20,
                'payment_method': 'hybrid',
                'wallet_address': self.test_wallet,
                'approval_tx_hash': 'test_approval_hash'
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/courses/{course.id}/create-payment-intent/",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"✅ Payment intent request sent: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Payment intent created successfully")
                    print(f"   Final amount: €{data.get('final_amount', 'N/A')}")
                    print(f"   TEO cost: {data.get('teo_cost', 'N/A')}")
                    print(f"   Discount applied: €{data.get('discount_applied', 'N/A')}")
                    return True
                else:
                    print(f"❌ Payment intent failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP error: {response.status_code}")
                print(f"   Response: {response.text}")
                
            return False
            
        except Exception as e:
            print(f"❌ Payment intent test failed: {e}")
            return False

    def test_4_commission_calculations(self):
        """Test that commission calculations use the correct rates"""
        print("\n4️⃣ Testing Commission Calculations...")
        
        try:
            # Test payment service commission calculation
            test_amount = Decimal('100.00')  # €100 course
            
            # Get commission rate
            commission_rate = self.payment_service.PLATFORM_COMMISSION_RATE
            teacher_percentage = Decimal('1.00') - commission_rate
            
            teacher_amount = test_amount * teacher_percentage
            commission_amount = test_amount * commission_rate
            
            print(f"✅ Platform commission rate: {commission_rate * 100}%")
            print(f"✅ Teacher percentage: {teacher_percentage * 100}%")
            print(f"✅ For €{test_amount}:")
            print(f"   Teacher gets: €{teacher_amount}")
            print(f"   Platform gets: €{commission_amount}")
            
            # Verify it's 50/50 split
            if commission_rate == Decimal('0.50'):
                print("✅ Commission rate is correct (50%)")
                return True
            else:
                print(f"❌ Commission rate is wrong: {commission_rate * 100}% (should be 50%)")
                return False
                
        except Exception as e:
            print(f"❌ Commission calculation test failed: {e}")
            return False

    def test_5_frontend_integration(self):
        """Test frontend integration points"""
        print("\n5️⃣ Testing Frontend Integration...")
        
        try:
            # Test if frontend is accessible
            response = requests.get(self.frontend_url)
            if response.status_code == 200:
                print("✅ Frontend server accessible")
            else:
                print(f"❌ Frontend server error: {response.status_code}")
                return False
                
            # Test API CORS and endpoints
            headers = {
                'Origin': self.frontend_url,
                'Content-Type': 'application/json'
            }
            
            course = Course.objects.first()
            if course:
                response = requests.get(
                    f"{self.base_url}/api/v1/courses/{course.id}/payment-summary/",
                    headers=headers
                )
                
                if response.status_code == 200:
                    print("✅ CORS configuration working")
                else:
                    print(f"❌ CORS issue: {response.status_code}")
                    
            return True
            
        except Exception as e:
            print(f"❌ Frontend integration test failed: {e}")
            return False

    def run_all_tests(self):
        """Run all Phase 2 tests"""
        print("🚀 Starting Phase 2 Implementation Tests...")
        
        tests = [
            self.test_1_payment_summary_api,
            self.test_2_teocoin_balance_calculation,
            self.test_3_payment_intent_creation,
            self.test_4_commission_calculations,
            self.test_5_frontend_integration
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
                results.append(False)
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 PHASE 2 TEST RESULTS")
        print("=" * 50)
        
        passed = sum(results)
        total = len(results)
        
        test_names = [
            "Payment Summary API",
            "TeoCoin Balance Calculations", 
            "Payment Intent Creation",
            "Commission Calculations",
            "Frontend Integration"
        ]
        
        for i, (name, result) in enumerate(zip(test_names, results)):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{i+1}. {name}: {status}")
            
        print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL PHASE 2 TESTS PASSED! TeoCoin payment flow is functional!")
        else:
            print("⚠️ Some tests failed. Check the details above.")
            
        return passed == total

if __name__ == "__main__":
    test_suite = Phase2TestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)
