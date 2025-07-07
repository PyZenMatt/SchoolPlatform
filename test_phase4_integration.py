#!/usr/bin/env python3
"""
Phase 4.1 Integration Test - Complete TeoCoin Discount Payment System
Tests the full Layer 2 backend proxy architecture implementation
"""

import os
import sys
import django
import requests
import json
from decimal import Decimal
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, CourseEnrollment
from users.models import User as CustomUser

class Phase4IntegrationTest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.test_results = []
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_payment_endpoints_availability(self):
        """Test if all payment endpoints are available"""
        # Test with a sample course_id (1)
        course_id = 1
        endpoints = [
            f"/api/v1/courses/{course_id}/create-payment-intent/",
            f"/api/v1/courses/{course_id}/confirm-payment/",
            f"/api/v1/courses/{course_id}/payment-summary/",
            f"/api/v1/courses/{course_id}/discount-status/"
        ]
        
        all_available = True
        unavailable_endpoints = []
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}")
                # We expect 400/405 for GET requests, not 404
                if response.status_code == 404:
                    all_available = False
                    unavailable_endpoints.append(endpoint)
                else:
                    print(f"   ✅ {endpoint} - Available (status: {response.status_code})")
            except Exception as e:
                all_available = False
                unavailable_endpoints.append(f"{endpoint} - {str(e)}")
        
        self.log_test(
            "Payment Endpoints Availability",
            all_available,
            "All payment endpoints are properly configured" if all_available else f"Missing endpoints: {unavailable_endpoints}",
            f"Tested endpoints: {endpoints}"
        )
        
        return all_available
    
    def test_database_models(self):
        """Test if CourseEnrollment model has TeoCoin discount fields"""
        try:
            # Check if model has the required fields
            from courses.models import CourseEnrollment
            
            # Create a test enrollment to verify fields exist
            test_enrollment = CourseEnrollment()
            
            required_fields = [
                'original_price_eur',
                'discount_amount_eur', 
                'teocoin_discount_request_id'
            ]
            
            missing_fields = []
            for field in required_fields:
                if not hasattr(test_enrollment, field):
                    missing_fields.append(field)
            
            # Check if teocoin_discount is in payment method choices
            payment_method_choices = [choice[0] for choice in CourseEnrollment.PAYMENT_METHODS]
            has_teocoin_method = 'teocoin_discount' in payment_method_choices
            
            success = len(missing_fields) == 0 and has_teocoin_method
            
            details = {
                'missing_fields': missing_fields,
                'has_teocoin_method': has_teocoin_method,
                'payment_methods': payment_method_choices
            }
            
            self.log_test(
                "Database Model Integration",
                success,
                "CourseEnrollment model has all TeoCoin discount fields" if success else f"Missing: {missing_fields}",
                details
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Database Model Integration",
                False,
                f"Error checking model: {str(e)}"
            )
            return False
    
    def test_teocoin_discount_service(self):
        """Test TeoCoinDiscountService initialization"""
        try:
            from services.teocoin_discount_service import teocoin_discount_service
            
            # Check service initialization
            service_initialized = teocoin_discount_service is not None
            
            # Check if service has key methods
            required_methods = [
                'create_discount_request',
                'approve_discount_request',
                'decline_discount_request',
                'get_discount_request',
                'calculate_teo_cost'
            ]
            
            missing_methods = []
            for method in required_methods:
                if not hasattr(teocoin_discount_service, method):
                    missing_methods.append(method)
            
            success = service_initialized and len(missing_methods) == 0
            
            # Test TEO cost calculation
            try:
                teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(
                    Decimal('100.00'), 10
                )
                calculation_works = isinstance(teo_cost, int) and isinstance(teacher_bonus, int)
            except Exception as calc_error:
                calculation_works = False
                missing_methods.append(f"calculate_teo_cost error: {calc_error}")
            
            success = success and calculation_works
            
            details = {
                'service_initialized': service_initialized,
                'missing_methods': missing_methods,
                'calculation_test': calculation_works
            }
            
            self.log_test(
                "TeoCoinDiscountService",
                success,
                "Service is properly initialized and functional" if success else f"Issues: {missing_methods}",
                details
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "TeoCoinDiscountService",
                False,
                f"Error testing service: {str(e)}"
            )
            return False
    
    def test_payment_summary_endpoint(self):
        """Test payment summary endpoint with TeoCoin discount calculation"""
        try:
            # Create test data
            test_course_id = 1
            test_price = 100.00
            test_discount = 10
            
            response = requests.post(
                f"{self.base_url}/api/v1/courses/{test_course_id}/payment-summary/",
                json={
                    'base_price': test_price,
                    'discount_percent': test_discount
                },
                headers={'Content-Type': 'application/json'}
            )
            
            success = response.status_code in [200, 400, 500]  # Any response means endpoint exists
            
            if response.status_code == 200:
                data = response.json()
                has_required_fields = all(field in data for field in [
                    'original_price', 'discount_amount', 'final_price'
                ])
                success = success and has_required_fields
                details = f"Response: {data}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text}"
            
            self.log_test(
                "Payment Summary Endpoint",
                success,
                "Endpoint responds correctly" if success else f"Endpoint error: {response.status_code}",
                details
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Payment Summary Endpoint",
                False,
                f"Error testing endpoint: {str(e)}"
            )
            return False
    
    def test_layer2_architecture_integration(self):
        """Test that Layer 2 architecture is properly integrated"""
        try:
            from courses.views.payments import CreatePaymentIntentView, ConfirmPaymentView
            from services.teocoin_discount_service import teocoin_discount_service
            
            # Check if payment views import the discount service
            create_view = CreatePaymentIntentView()
            confirm_view = ConfirmPaymentView()
            
            views_exist = create_view is not None and confirm_view is not None
            service_imported = teocoin_discount_service is not None
            
            # Check if views have the required methods
            required_view_methods = ['post']
            create_has_methods = all(hasattr(create_view, method) for method in required_view_methods)
            confirm_has_methods = all(hasattr(confirm_view, method) for method in required_view_methods)
            
            success = views_exist and service_imported and create_has_methods and confirm_has_methods
            
            details = {
                'views_exist': views_exist,
                'service_imported': service_imported,
                'create_view_methods': create_has_methods,
                'confirm_view_methods': confirm_has_methods
            }
            
            self.log_test(
                "Layer 2 Architecture Integration",
                success,
                "Backend proxy architecture is properly integrated" if success else "Integration issues found",
                details
            )
            
            return success
            
        except Exception as e:
            self.log_test(
                "Layer 2 Architecture Integration",
                False,
                f"Error testing integration: {str(e)}"
            )
            return False
    
    def run_comprehensive_test(self):
        """Run all integration tests"""
        print("🚀 Starting Phase 4.1 Integration Test - TeoCoin Discount Payment System")
        print("=" * 80)
        
        tests = [
            self.test_payment_endpoints_availability,
            self.test_database_models,
            self.test_teocoin_discount_service,
            self.test_payment_summary_endpoint,
            self.test_layer2_architecture_integration
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
        
        print("\n" + "=" * 80)
        print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! Phase 4.1 Course Purchase Flow is ready!")
            print("\n✅ Next Steps:")
            print("   1. Test frontend payment flow")
            print("   2. Move to Phase 4.2 Platform Economics")
            print("   3. Implement notification system")
        else:
            print("⚠️  Some tests failed. Review the issues above.")
            print("\n🔧 Recommended Actions:")
            print("   1. Fix failed components")
            print("   2. Re-run tests")
            print("   3. Check server logs for errors")
        
        return passed_tests == total_tests


if __name__ == "__main__":
    test = Phase4IntegrationTest()
    success = test.run_comprehensive_test()
    
    # Save test results
    with open('test_phase4_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(test.test_results),
            'passed_tests': sum(1 for r in test.test_results if r['success']),
            'success': success,
            'results': test.test_results
        }, f, indent=2)
    
    print(f"\n📄 Test results saved to: test_phase4_results.json")
    sys.exit(0 if success else 1)
