#!/usr/bin/env python
"""
Test course payment after constraint fix
"""
import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course

def test_course_payment_api():
    """Test course payment via API"""
    print("=== TESTING COURSE PAYMENT API ===")
    
    try:
        # Get a course
        course = Course.objects.first()
        if not course:
            print("❌ No course found")
            return
            
        print(f"✓ Testing with course: {course.title} (ID: {course.id})")
        
        # Get a user
        User = get_user_model()
        user = User.objects.filter(wallet_address__isnull=False).first()
        if not user:
            print("❌ No user with wallet found")
            return
            
        print(f"✓ Testing with user: {user.email}")
        print(f"✓ User wallet: {user.wallet_address}")
        
        # Prepare payment data
        payment_data = {
            'teacher_address': '0xE2fA8AfbF1B795f5dEd1a33aa360872E9020a9A0',  # Teacher address
            'course_price': 15,
            'student_address': user.wallet_address,
            'course_id': course.id
        }
        
        print(f"✓ Payment data: {payment_data}")
        
        # First login to get session/token
        print("\n🔐 Attempting login...")
        login_response = requests.post(
            'http://localhost:8000/api/auth/login/',
            json={
                'email': user.email,
                'password': 'password123'  # Default test password
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return
            
        # Get session/auth token
        session_cookies = login_response.cookies
        auth_headers = {}
        
        if 'csrftoken' in session_cookies:
            auth_headers['X-CSRFToken'] = session_cookies['csrftoken']
            
        print("✓ Login successful")
        
        # Make payment request
        print("\n💰 Processing course payment...")
        response = requests.post(
            'http://localhost:8000/api/v1/blockchain/process-course-payment/',
            json=payment_data,
            cookies=session_cookies,
            headers=auth_headers
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Payment successful!")
            result = response.json()
            print(f"Result: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Payment failed: {response.status_code}")
            try:
                error = response.json()
                print(f"Error: {json.dumps(error, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_course_payment_api()
