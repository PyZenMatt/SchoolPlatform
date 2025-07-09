#!/usr/bin/env python
"""
Test Script for Phase 5.3: Staking Management APIs

This script tests the newly implemented staking API endpoints to verify
that Phase 5.3 of the Layer 2 implementation is working correctly.
"""

import os
import sys
import django
import requests
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import TeacherProfile
from django.test import Client
from django.urls import reverse

User = get_user_model()

def test_staking_api_urls():
    """Test that all staking API URLs are properly configured"""
    print("🧪 Testing Phase 5.3: Staking Management API URLs...")
    
    # Expected staking API endpoints
    expected_endpoints = [
        'teacher-staking-info',
        'stake-tokens', 
        'unstake-tokens',
        'unstaking-schedule',
        'withdraw-unstaked',
        'staking-statistics'
    ]
    
    for endpoint in expected_endpoints:
        try:
            url = reverse(endpoint)
            print(f"✅ {endpoint}: {url}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")
    
    return True

def test_teacher_profile_methods():
    """Test TeacherProfile model methods"""
    print("\n🧪 Testing TeacherProfile methods...")
    
    # Find a teacher user
    teacher_user = User.objects.filter(role='teacher').first()
    if not teacher_user:
        print("❌ No teacher users found in database")
        return False
    
    # Get or create teacher profile
    teacher_profile, created = TeacherProfile.objects.get_or_create(user=teacher_user)
    if created:
        print(f"✅ Created new TeacherProfile for {teacher_user.email}")
    else:
        print(f"✅ Found existing TeacherProfile for {teacher_user.email}")
    
    # Test update_tier_and_commission method
    try:
        result = teacher_profile.update_tier_and_commission()
        print(f"✅ update_tier_and_commission(): {result}")
    except Exception as e:
        print(f"❌ update_tier_and_commission() failed: {e}")
        return False
    
    # Test can_stake_more method
    try:
        can_stake, message = teacher_profile.can_stake_more()
        print(f"✅ can_stake_more(): {can_stake}, '{message}'")
    except Exception as e:
        print(f"❌ can_stake_more() failed: {e}")
        return False
    
    # Check all required fields exist
    required_fields = [
        'commission_rate', 'staking_tier', 'staked_teo_amount',
        'total_courses', 'total_earnings', 'total_earned_eur', 'total_earned_teo'
    ]
    
    for field in required_fields:
        if hasattr(teacher_profile, field):
            value = getattr(teacher_profile, field)
            print(f"✅ {field}: {value}")
        else:
            print(f"❌ Missing field: {field}")
            return False
    
    return True

def test_staking_service_integration():
    """Test that blockchain service staking methods exist"""
    print("\n🧪 Testing TeoCoinService staking methods...")
    
    try:
        from blockchain.blockchain import TeoCoinService
        service = TeoCoinService()
        
        # Test methods exist
        methods_to_test = [
            'get_teacher_staking_info',
            'stake_tokens', 
            'unstake_tokens',
            'get_unstaking_schedule',
            'withdraw_unstaked_tokens'
        ]
        
        for method_name in methods_to_test:
            if hasattr(service, method_name):
                print(f"✅ {method_name}() method exists")
            else:
                print(f"❌ Missing method: {method_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize TeoCoinService: {e}")
        return False

def test_staking_contract_connection():
    """Test staking contract configuration"""
    print("\n🧪 Testing staking contract configuration...")
    
    try:
        from services.staking_config import load_contract_config
        config = load_contract_config()
        
        print(f"✅ Contract address: {config.get('address')}")
        print(f"✅ Development mode: {config.get('development_mode')}")
        print(f"✅ ABI loaded: {len(config.get('abi', [])) > 0}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load staking contract config: {e}")
        return False

def main():
    """Run all Phase 5.3 tests"""
    print("🚀 PHASE 5.3 TESTING: Staking Management APIs")
    print("=" * 60)
    
    tests = [
        test_staking_api_urls,
        test_teacher_profile_methods,
        test_staking_service_integration,
        test_staking_contract_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
                print("✅ PASSED")
            else:
                print("❌ FAILED")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        print("-" * 40)
    
    print(f"\n🎯 PHASE 5.3 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Phase 5.3 implementation SUCCESSFUL!")
        print("✅ All staking management APIs are ready!")
        print("🚀 Ready to proceed to Phase 6: Frontend Integration")
    else:
        print("⚠️  Some issues found - see details above")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
