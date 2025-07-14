#!/usr/bin/env python
"""
Fix Frontend Authorization Issue
Test different token formats and fix the authorization header
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from rest_framework_simplejwt.tokens import RefreshToken
import requests

def test_authorization_formats():
    """Test different authorization header formats"""
    
    print("🔐 AUTHORIZATION HEADER DEBUG")
    print("=" * 50)
    
    try:
        # Get teacher2 user and generate token
        username = 'teacher2'
        user = User.objects.get(username=username)
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        print(f"👨‍🏫 Testing for user: {username}")
        print(f"🔑 Generated token: {access_token[:50]}...")
        
        # Test different authorization header formats
        test_cases = [
            {
                'name': 'Bearer with space',
                'header': f'Bearer {access_token}'
            },
            {
                'name': 'Token without Bearer',
                'header': access_token
            },
            {
                'name': 'JWT with space',
                'header': f'JWT {access_token}'
            }
        ]
        
        base_url = 'http://localhost:8000'
        test_endpoint = f'{base_url}/api/v1/teocoin/balance/'
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print(f"   Header: Authorization: {test_case['header'][:60]}...")
            
            try:
                response = requests.get(
                    test_endpoint,
                    headers={'Authorization': test_case['header']},
                    timeout=10
                )
                
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS!")
                    data = response.json()
                    print(f"   Balance: {data.get('available_balance', 'N/A')} TEO")
                    
                    # If this format works, test the choice endpoint
                    print(f"\n🎯 Testing choice endpoint with working format...")
                    
                    choice_url = f'{base_url}/api/v1/teocoin/teacher/absorptions/choose/'
                    choice_data = {
                        'absorption_id': 9,
                        'choice': 'absorb'
                    }
                    
                    choice_response = requests.post(
                        choice_url,
                        headers={
                            'Authorization': test_case['header'],
                            'Content-Type': 'application/json'
                        },
                        json=choice_data,
                        timeout=10
                    )
                    
                    print(f"   Choice Status: {choice_response.status_code}")
                    
                    if choice_response.status_code == 200:
                        choice_result = choice_response.json()
                        print(f"   ✅ CHOICE SUCCESS!")
                        print(f"   TEO Gained: {choice_result.get('absorption', {}).get('final_teacher_teo', 'N/A')}")
                        
                        # This is the correct format - save it
                        with open('correct_auth_format.txt', 'w') as f:
                            f.write(f"CORRECT_FORMAT={test_case['header']}\n")
                            f.write(f"TOKEN={access_token}\n")
                        
                        print(f"   💾 Saved correct format to correct_auth_format.txt")
                        return test_case['header']
                    else:
                        try:
                            error_data = choice_response.json()
                            print(f"   ❌ Choice failed: {error_data}")
                        except:
                            print(f"   ❌ Choice failed: {choice_response.text}")
                
                else:
                    try:
                        error_data = response.json()
                        print(f"   ❌ Failed: {error_data}")
                    except:
                        print(f"   ❌ Failed: {response.text}")
                        
            except requests.exceptions.RequestException as e:
                print(f"   ❌ Network error: {e}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        print(f"\n⚠️  No working authorization format found")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    working_format = test_authorization_formats()
    
    if working_format:
        print(f"\n🎉 WORKING AUTHORIZATION FORMAT FOUND!")
        print(f"Use this format in frontend: Authorization: {working_format[:60]}...")
    else:
        print(f"\n❌ NEED TO INVESTIGATE FURTHER")
        print("Check Django settings for JWT authentication configuration")
