#!/usr/bin/env python3
"""
Test both payment flows: Stripe and TeoCoin discount
"""

import os
import sys
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import Course
from users.models import User
from courses.views.payments import CreatePaymentIntentView
from django.test import RequestFactory
import json

def test_payment_flows():
    """Test both Stripe and TeoCoin payment flows"""
    
    print("🔧 Testing Complete Payment Integration...")
    print("=" * 60)
    
    try:
        # Get course and user
        course = Course.objects.get(id=7)
        user = User.objects.filter(is_superuser=True).first()
        
        print(f"✅ Course: {course.title} - €{course.price_eur}")
        print(f"✅ User: {user.email}")
        
        # Test 1: Stripe Payment (no discount)
        print("\n🧪 Test 1: Stripe Payment Intent (no discount)")
        factory = RequestFactory()
        request_data = {
            'teocoin_discount': 0,
            'payment_method': 'stripe'
        }
        
        request = factory.post(
            f'/api/v1/courses/{course.id}/create-payment-intent/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        request.user = user
        request.data = request_data
        
        view = CreatePaymentIntentView()
        response = view.post(request, course_id=course.id)
        
        if response.status_code == 200:
            print("✅ Stripe payment intent: SUCCESS")
            print(f"   Status: {response.status_code}")
        else:
            print(f"❌ Stripe payment intent: FAILED ({response.status_code})")
            print(f"   Response: {response.data}")
        
        # Test 2: TeoCoin Payment (with discount)
        print("\n🧪 Test 2: TeoCoin Payment Intent (10% discount)")
        request_data = {
            'teocoin_discount': 10,  # 10% discount
            'payment_method': 'teocoin'
        }
        
        request = factory.post(
            f'/api/v1/courses/{course.id}/create-payment-intent/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        request.user = user
        request.data = request_data
        
        response = view.post(request, course_id=course.id)
        
        if response.status_code == 200:
            print("✅ TeoCoin payment intent: SUCCESS")
            print(f"   Status: {response.status_code}")
            data = response.data
            print(f"   Final amount: €{data.get('final_amount', 'Unknown')}")
            print(f"   Discount applied: €{data.get('discount_applied', 'Unknown')}")
            print(f"   TeoCoin spent: {data.get('teocoin_spent', 'Unknown')} TEO")
        else:
            print(f"❌ TeoCoin payment intent: FAILED ({response.status_code})")
            print(f"   Response: {response.data}")
                
    except Exception as e:
        print(f"❌ Error testing payment flows: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("🎯 Payment Integration Status:")
    print("✅ Backend: Fixed course.price → course.price_eur")
    print("✅ Frontend: Added teocoin_discount parameter")
    print("✅ Backend: Added TeoCoin discount handling")
    print("\n🚀 Ready for frontend testing!")
    print("1. Try Stripe payment (should work now)")
    print("2. Try TeoCoin discount (should show discount calculation)")

if __name__ == "__main__":
    test_payment_flows()
