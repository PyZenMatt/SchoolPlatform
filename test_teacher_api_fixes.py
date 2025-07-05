#!/usr/bin/env python3
"""
Test Teacher Dashboard API fixes
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

User = get_user_model()

def test_teacher_apis():
    print("🧪 TESTING TEACHER API FIXES")
    print("=" * 50)
    
    try:
        # Get the test teacher
        teacher = User.objects.get(username='payment_test_teacher')
        client = Client()
        client.force_login(teacher)
        
        print(f"👨‍🏫 Testing with teacher: {teacher.username}")
        print()
        
        # Test 1: Teacher Dashboard API
        print("1️⃣ Testing Teacher Dashboard API...")
        try:
            response = client.get('/api/v1/dashboard/teacher/')
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS - Dashboard data received")
                print(f"   📊 Stats: {data.get('stats', {})}")
                print(f"   💰 Sales: {data.get('sales', {})}")
                print(f"   📚 Courses: {len(data.get('courses', []))} courses")
            else:
                print(f"   ❌ FAILED - {response.status_code}")
                if hasattr(response, 'json'):
                    try:
                        print(f"   Error: {response.json()}")
                    except:
                        print(f"   Error: {response.content.decode()}")
                        
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
        
        print()
        
        # Test 2: Teacher Escrow List API
        print("2️⃣ Testing Teacher Escrow List API...")
        try:
            response = client.get('/api/v1/services/teacher/escrows/')
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS - Escrow data received")
                print(f"   📋 Escrows: {len(data.get('escrows', []))} total")
                print(f"   📊 Stats: {data.get('stats', {})}")
            elif response.status_code == 403:
                print(f"   ⚠️  FORBIDDEN - Teacher permission check failed")
                print(f"   Error: {response.json().get('error', 'No error message')}")
            else:
                print(f"   ❌ FAILED - {response.status_code}")
                        
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
        
        print()
        
        # Test 3: Teacher Escrow Stats API
        print("3️⃣ Testing Teacher Escrow Stats API...")
        try:
            response = client.get('/api/v1/services/teacher/escrows/stats/')
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ SUCCESS - Stats data received")
                print(f"   📊 Stats: {data}")
            elif response.status_code == 403:
                print(f"   ⚠️  FORBIDDEN - Teacher permission check failed")
            else:
                print(f"   ❌ FAILED - {response.status_code}")
                        
        except Exception as e:
            print(f"   ❌ EXCEPTION: {e}")
        
        print()
        
        # Summary
        print("📝 SUMMARY:")
        print("   • Fixed Decimal arithmetic in teacher dashboard")
        print("   • Fixed TeoCoin service import issues")
        print("   • Fixed teacher permission checks (courses_taught → courses_created)")
        print("   • Added alternative escrows/stats/ endpoint")
        print("   • Fixed .id access issues (using .pk)")
        print()
        print("🎯 RECOMMENDED ACTIONS:")
        print("   1. Clear browser cache and reload the teacher dashboard")
        print("   2. Check that the teacher user has created courses")
        print("   3. Verify authentication tokens are valid")
        print("   4. Frontend should handle 403 responses gracefully")
        
    except User.DoesNotExist:
        print("❌ Test teacher 'payment_test_teacher' not found")
        print("   Run the payment flow test first to create test data")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_teacher_apis()
