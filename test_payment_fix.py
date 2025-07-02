#!/usr/bin/env python3
"""
Test payment intent creation after fixing the course.price issue
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

def test_payment_intent():
    """Test payment intent creation"""
    
    print("🔧 Testing Payment Intent Creation...")
    
    try:
        # Get course and user
        course = Course.objects.get(id=7)
        user = User.objects.filter(is_superuser=True).first()
        
        print(f"✅ Course: {course.title} - €{course.price_eur}")
        print(f"✅ User: {user.email}")
        
        # Create a mock request
        factory = RequestFactory()
        request_data = {
            'teocoin_discount': 0,  # No discount for now
            'payment_method': 'stripe'
        }
        
        request = factory.post(
            f'/api/v1/courses/{course.id}/create-payment-intent/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        request.user = user
        
        # Create view instance and test
        view = CreatePaymentIntentView()
        view.request = request
        
        response = view.post(request, course_id=course.id)
        
        if response.status_code == 200:
            print("✅ Payment intent created successfully!")
            print("✅ Status: 200 OK")
            print("\n🎉 Stripe payment should now work in frontend!")
        else:
            print(f"❌ Payment intent failed with status: {response.status_code}")
            if hasattr(response, 'data'):
                print(f"   Response: {response.data}")
                
    except Exception as e:
        print(f"❌ Error testing payment intent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payment_intent()
