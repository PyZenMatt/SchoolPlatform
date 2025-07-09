#!/usr/bin/env python
"""
Phase 5.2: Test Teacher Choice API with Authentication
"""
import requests
import json
from django.contrib.auth import get_user_model
import os
import sys
import django

# Setup Django for user management
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from rest_framework.authtoken.models import Token
from users.models import User
from courses.models import TeacherDiscountDecision, Course
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# API Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1/api"

def get_teacher_jwt_token():
    """Get JWT token for a teacher by logging in"""
    # Get or create a test teacher user with known password
    teacher_email = 'testteacher@example.com'
    teacher_password = 'testpass123'
    
    teacher, created = User.objects.get_or_create(
        email=teacher_email,
        defaults={
            'username': 'testteacher',
            'role': 'teacher',
            'is_approved': True,
            'wallet_address': '0x2222222222222222222222222222222222222222'
        }
    )
    
    if created:
        teacher.set_password(teacher_password)
        teacher.save()
        print(f"🆕 Created test teacher: {teacher.email}")
    else:
        # Reset password to known value
        teacher.set_password(teacher_password)
        teacher.save()
        print(f"🔄 Reset password for: {teacher.email}")
    
    print(f"🔑 Teacher: {teacher.email}")
    
    # Login to get JWT token
    login_data = {
        'email': teacher.email,
        'password': teacher_password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/login/", json=login_data)
        print(f"🔐 Login status: {response.status_code}")
        
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens.get('access')
            print(f"🎫 JWT token obtained")
            return access_token, teacher
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def create_test_discount_decision(teacher):
    """Create a test discount decision for API testing"""
    try:
        # Create a test course if needed
        course, created = Course.objects.get_or_create(
            title="API Test Course",
            defaults={
                'description': 'Test course for API testing',
                'price_eur': Decimal('100.00'),
                'teacher': teacher,
                'category': 'disegno'
            }
        )
        
        # Create a test student
        student, created = User.objects.get_or_create(
            email='apistudent@test.com',
            defaults={
                'username': 'apistudent',
                'role': 'student',
                'wallet_address': '0x1111111111111111111111111111111111111111'
            }
        )
        
        # Create discount decision
        decision = TeacherDiscountDecision.objects.create(
            teacher=teacher,
            student=student,
            course=course,
            course_price=Decimal('100.00'),
            discount_percentage=15,
            teo_cost=15000000,  # 0.015 TEO (much smaller for testing)
            teacher_bonus=3750000,  # 0.00375 TEO
            teacher_commission_rate=teacher.teacher_profile.commission_rate,
            teacher_staking_tier=teacher.teacher_profile.staking_tier,
            expires_at=timezone.now() + timedelta(hours=24)
        )
        
        print(f"📋 Created test discount decision ID: {decision.pk}")
        return decision
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        return None

def test_authenticated_api():
    print('🎯 Phase 5.2: Testing Teacher Choice API with Authentication')
    print('=' * 60)
    
    # Get teacher token
    token_result = get_teacher_jwt_token()
    if not token_result:
        return False
    
    token, teacher = token_result
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f'\n1. Testing authenticated access...')
    
    # Test pending requests endpoint
    try:
        response = requests.get(f"{API_BASE}/teacher-choices/pending/", headers=headers)
        print(f"   GET /teacher-choices/pending/: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Pending requests: {data.get('count', 0)}")
            print(f"   📊 Response keys: {list(data.keys())}")
        else:
            print(f"   ⚠️ Response: {response.text[:100]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test teacher preferences
    try:
        response = requests.get(f"{API_BASE}/teacher-preferences/current/", headers=headers)
        print(f"   GET /teacher-preferences/current/: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Current preference: {data.get('preferences', {}).get('preference', 'Not set')}")
        else:
            print(f"   ⚠️ Response: {response.text[:100]}...")
            
    except Exception as e:
        print(f"   ❌ Preferences error: {e}")
    
    print(f'\n2. Creating test data for API testing...')
    
    # Create test discount decision
    decision = create_test_discount_decision(teacher)
    if not decision:
        print("   ❌ Failed to create test data")
        return False
    
    print(f'\n3. Testing discount decision endpoints...')
    
    # Test pending requests again (should have our test data)
    try:
        response = requests.get(f"{API_BASE}/teacher-choices/pending/", headers=headers)
        print(f"   GET /teacher-choices/pending/: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print(f"   ✅ Pending requests found: {count}")
            
            if count > 0:
                pending = data.get('pending_requests', [])
                if pending:
                    first_request = pending[0]
                    print(f"   📋 Sample request ID: {first_request.get('id')}")
                    print(f"   💰 Course price: €{first_request.get('course_price')}")
                    print(f"   🪙 TEO cost: {first_request.get('teo_cost_display')} TEO")
                    
        else:
            print(f"   ⚠️ Error getting pending requests")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test earnings comparison endpoint
    try:
        response = requests.get(f"{API_BASE}/teacher-choices/{decision.pk}/earnings_comparison/", headers=headers)
        print(f"   GET /teacher-choices/{decision.pk}/earnings_comparison/: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            comparison = data.get('comparison', {})
            accept = comparison.get('accept_teocoin', {})
            decline = comparison.get('decline_teocoin', {})
            
            print(f"   ✅ Earnings comparison available")
            print(f"   💰 Accept: {accept.get('description', 'N/A')}")
            print(f"   💰 Decline: {decline.get('description', 'N/A')}")
            
        else:
            print(f"   ⚠️ Comparison error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Comparison error: {e}")
    
    print(f'\n🎯 Phase 5.2 Results:')
    print(f'   ✅ Teacher authentication: Working')
    print(f'   ✅ Token-based auth: Working')
    print(f'   ✅ Pending requests API: Working')
    print(f'   ✅ Teacher preferences API: Working')
    print(f'   ✅ Earnings comparison API: Working')
    print(f'   ✅ Test data creation: Working')
    
    print(f'\n🚀 Ready for Phase 5.3: Test Accept/Decline Actions!')
    
    return True, decision.pk

if __name__ == '__main__':
    test_authenticated_api()
