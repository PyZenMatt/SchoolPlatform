#!/usr/bin/env python
"""
Manual test script for RewardService integration
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from users.models import User
from courses.models import Course, Lesson
from rewards.models import TokenBalance

def test_reward_endpoints():
    """Test the reward endpoints manually"""
    
    # Create test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Create course
    course = Course.objects.create(
        title='Test Course',
        description='Test course description',
        price=Decimal('100.00'),
        teacher=user
    )
    
    # Create lesson
    lesson = Lesson.objects.create(
        title='Test Lesson',
        course=course,
        content='Test lesson content',
        order=1
    )
    
    # Enroll user in course
    course.students.add(user)
    
    # Create token balance
    TokenBalance.objects.create(
        user=user,
        balance=Decimal('50.00')
    )
    
    # Test API client
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Test lesson completion reward
    print("Testing lesson completion reward...")
    url = reverse('rewards:complete-lesson')
    print(f"URL: {url}")
    
    data = {'lesson_id': lesson.id}
    response = client.post(url, data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Lesson completion reward endpoint working!")
    else:
        print("❌ Lesson completion reward endpoint failed!")
    
    # Test rewards summary
    print("\nTesting rewards summary...")
    url = reverse('rewards:user-rewards-summary')
    response = client.get(url)
    
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Rewards summary endpoint working!")
    else:
        print("❌ Rewards summary endpoint failed!")
    
    # Test leaderboard
    print("\nTesting leaderboard...")
    url = reverse('rewards:reward-leaderboard')
    response = client.get(url)
    
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.json()}")
    
    if response.status_code == 200:
        print("✅ Leaderboard endpoint working!")
    else:
        print("❌ Leaderboard endpoint failed!")

if __name__ == '__main__':
    test_reward_endpoints()
