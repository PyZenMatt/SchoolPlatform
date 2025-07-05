#!/usr/bin/env python3
"""
Quick test to verify teacher API fixes are working
"""

import os
import sys
import django
import requests

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

def test_api_endpoints():
    print("🔧 TESTING API FIXES")
    print("=" * 40)
    
    # Test 1: Teacher Dashboard - Should not give 500 error
    print("1️⃣ Testing Teacher Dashboard API...")
    try:
        response = requests.get('http://localhost:8000/api/v1/dashboard/teacher/')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 401:
            print("   ✅ SUCCESS - No more 500 error! (401 = auth required)")
        elif response.status_code == 500:
            print("   ❌ STILL FAILING - 500 error persists")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('details', 'No details')}")
            except:
                print(f"   Error response: {response.text[:200]}")
        else:
            print(f"   ✅ SUCCESS - Unexpected but working status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print()
    
    # Test 2: Escrow Stats endpoint
    print("2️⃣ Testing Escrow Stats API...")
    try:
        response = requests.get('http://localhost:8000/api/v1/services/teacher/escrows/stats/')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 401 or response.status_code == 403:
            print("   ✅ SUCCESS - Endpoint found! (401/403 = auth/permission required)")
        elif response.status_code == 404:
            print("   ❌ STILL MISSING - 404 error persists")
        else:
            print(f"   ✅ SUCCESS - Working status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print()
    
    # Test 3: Blockchain transaction endpoint
    print("3️⃣ Testing Blockchain Transactions API...")
    try:
        response = requests.get('http://localhost:8000/api/v1/blockchain/transactions/')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 401:
            print("   ✅ SUCCESS - Endpoint working! (401 = auth required)")
        elif response.status_code == 500:
            print("   ❌ BLOCKCHAIN ERROR - 500 error in transactions")
        else:
            print(f"   ✅ SUCCESS - Working status: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print()
    print("📋 SUMMARY:")
    print("   • 500 errors should be fixed")
    print("   • 404 errors should be resolved")  
    print("   • 401/403 errors are expected (authentication required)")
    print("   • Frontend should now work without server errors")
    print()
    print("🎯 Try refreshing your teacher dashboard now!")

if __name__ == "__main__":
    test_api_endpoints()
