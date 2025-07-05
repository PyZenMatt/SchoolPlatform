#!/usr/bin/env python3
"""
Test script to verify all teacher dashboard API endpoints are working.
"""

import requests
import json
from datetime import datetime

def test_endpoint(url, description):
    """Test an endpoint and return the status code"""
    try:
        response = requests.get(url, timeout=5)
        status = response.status_code
        
        # Check if we get proper authentication error (401) instead of server error (500)
        if status == 401:
            result = "✅ WORKING (needs auth)"
        elif status == 404:
            result = "❌ NOT FOUND"
        elif status == 500:
            result = "❌ SERVER ERROR"
        else:
            result = f"? UNKNOWN ({status})"
            
        print(f"{description}: {result}")
        return status
        
    except requests.exceptions.RequestException as e:
        print(f"{description}: ❌ CONNECTION ERROR - {e}")
        return None

def main():
    print("=== TEACHER DASHBOARD API ENDPOINT TEST ===")
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Base URL
    base_url = "http://localhost:8000"
    
    # Test endpoints
    endpoints = [
        (f"{base_url}/api/v1/dashboard/teacher/", "Teacher Dashboard API"),
        (f"{base_url}/api/v1/services/teacher/escrows/stats/", "Escrow Stats (plural/slash)"),
        (f"{base_url}/api/v1/services/teacher/escrow-stats/", "Escrow Stats (singular/dash)"),
        (f"{base_url}/api/v1/transactions/", "Blockchain Transactions"),
        (f"{base_url}/api/v1/services/teacher/escrows/", "Teacher Escrows List"),
    ]
    
    results = {}
    
    for url, description in endpoints:
        status = test_endpoint(url, description)
        results[description] = status
    
    print()
    print("=== SUMMARY ===")
    working_count = sum(1 for status in results.values() if status == 401)
    total_count = len(results)
    
    print(f"Working endpoints: {working_count}/{total_count}")
    
    if working_count == total_count:
        print("🎉 ALL ENDPOINTS ARE WORKING! (Authentication required as expected)")
    else:
        print("⚠️  Some endpoints still need attention")
        
    print()
    print("Note: 401 'Authentication credentials were not provided' is the expected")
    print("response for protected endpoints when no auth token is provided.")

if __name__ == "__main__":
    main()
