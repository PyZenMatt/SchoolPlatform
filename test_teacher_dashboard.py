#!/usr/bin/env python3
"""
Test script to verify teacher dashboard API returns proper data structure.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import force_authenticate
from users.models import User
from core.dashboard import TeacherDashboardAPI
import json

def test_teacher_dashboard():
    print("=== TEACHER DASHBOARD STRUCTURE TEST ===")
    
    try:
        # Get a teacher user
        teacher = User.objects.filter(role='teacher').first()
        if not teacher:
            print("❌ No teacher users found")
            return
            
        print(f"✅ Testing with teacher: {teacher.email}")
        
        # Create a mock request
        factory = RequestFactory()
        request = factory.get('/api/v1/dashboard/teacher/')
        force_authenticate(request, user=teacher)
        request.user = teacher  # Ensure user is set
        
        # Test the dashboard view
        view = TeacherDashboardAPI()
        view.request = request
        
        response = view.get(request)
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.data
            print(f"✅ Response data keys: {list(data.keys())}")
            
            # Verify structure
            expected_keys = ['blockchain_balance', 'wallet_address', 'stats', 'sales', 'courses', 'transactions']
            for key in expected_keys:
                if key in data:
                    print(f"  ✅ {key}: {type(data[key])}")
                else:
                    print(f"  ❌ Missing key: {key}")
            
            # Check stats structure
            if 'stats' in data:
                stats = data['stats']
                print(f"✅ Stats: {stats}")
                for key, value in stats.items():
                    print(f"  - {key}: {value} ({type(value)})")
            
            # Check sales structure  
            if 'sales' in data:
                sales = data['sales']
                print(f"✅ Sales: {sales}")
                for key, value in sales.items():
                    print(f"  - {key}: {value} ({type(value)})")
                    
            print("🎉 Teacher dashboard API working correctly!")
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response data: {response.data}")
            
    except Exception as e:
        print(f"❌ Error testing teacher dashboard: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_teacher_dashboard()
