#!/usr/bin/env python
"""
Test script for blockchain API endpoints
"""
import os
import sys
import django
import requests
from django.test import Client
from django.contrib.auth import authenticate

# Setup Django environment
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from django.urls import reverse

def test_blockchain_endpoints():
    """Test blockchain API endpoints"""
    print("=== Testing Blockchain API Endpoints ===")
    
    # Get a test user
    user = User.objects.filter(role='student').first()
    if not user:
        print("❌ No student user found in database")
        return
    
    print(f"✓ Testing with user: {user.username}")
    
    # Create a test client
    client = Client()
    
    # Login the user
    client.force_login(user)
    
    print("\n=== Testing API Endpoints ===")
    
    # Test endpoints
    endpoints = [
        '/api/v1/blockchain/balance/',
        '/api/v1/blockchain/token-info/',
        '/api/v1/blockchain/check-status/',
        '/api/v1/blockchain/transactions/',
    ]
    
    for endpoint in endpoints:
        try:
            response = client.get(endpoint)
            print(f"GET {endpoint} -> Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✓ Success: {response.json()}")
            else:
                print(f"  ❌ Error: {response.content.decode()}")
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
    
    print("\n=== Testing POST Endpoints ===")
    
    # Test link wallet endpoint
    try:
        test_wallet = "0x1234567890123456789012345678901234567890"
        response = client.post('/api/v1/blockchain/link-wallet/', {
            'wallet_address': test_wallet
        }, content_type='application/json')
        print(f"POST /api/v1/blockchain/link-wallet/ -> Status: {response.status_code}")
        if response.status_code in [200, 201]:
            print(f"  ✓ Success: {response.json()}")
        else:
            print(f"  ❌ Error: {response.content.decode()}")
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")

if __name__ == "__main__":
    test_blockchain_endpoints()
