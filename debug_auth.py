#!/usr/bin/env python
"""
Debug Frontend Authentication Issues
Check if the JWT tokens are working correctly
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User

def debug_teacher_auth():
    """Debug teacher authentication tokens"""
    
    print("🔐 AUTHENTICATION DEBUG")
    print("=" * 50)
    
    try:
        # Get both teachers
        teachers = ['test_teacher_notifications', 'teacher2']
        
        for username in teachers:
            try:
                user = User.objects.get(username=username)
                print(f"\n👨‍🏫 Teacher: {username}")
                print(f"   User ID: {user.id}")
                print(f"   Email: {user.email}")
                print(f"   Is Active: {user.is_active}")
                print(f"   Role: {getattr(user, 'role', 'Not set')}")
                
                # Generate fresh tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                
                print(f"   🔑 Access Token: {access_token[:50]}...")
                print(f"   🔄 Refresh Token: {str(refresh)[:50]}...")
                
                # Test token validation
                try:
                    from rest_framework_simplejwt.authentication import JWTAuthentication
                    from rest_framework.request import Request
                    from django.test import RequestFactory
                    
                    factory = RequestFactory()
                    request = factory.get('/')
                    request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
                    
                    jwt_auth = JWTAuthentication()
                    validated_user, token = jwt_auth.authenticate(request)
                    
                    if validated_user:
                        print(f"   ✅ Token validation: SUCCESS")
                        print(f"   ✅ Validated user: {validated_user.username}")
                    else:
                        print(f"   ❌ Token validation: FAILED")
                        
                except Exception as e:
                    print(f"   ❌ Token validation error: {e}")
                    
            except User.DoesNotExist:
                print(f"❌ Teacher {username} not found")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_teacher_auth()
