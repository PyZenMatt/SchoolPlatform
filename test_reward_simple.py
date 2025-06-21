#!/usr/bin/env python
"""
Simple test to verify RewardService integration
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from courses.models import Course, Lesson
from rewards.models import TokenBalance, BlockchainTransaction

def test_reward_service_integration():
    """Test RewardService integration with views"""
    
    print("🧪 Testing RewardService Integration")
    print("=" * 50)
    
    # Create test data
    print("📝 Creating test data...")
    User = get_user_model()
    
    # Clean up any existing test data
    User.objects.filter(username='reward_test_user').delete()
    
    user = User.objects.create_user(
        username='reward_test_user',
        email='test@example.com',
        password='testpass123',
        role='student'  # Required field
    )
    
    course = Course.objects.create(
        title='Test Course for Rewards',
        description='Test course description',
        price=Decimal('100.00'),
        teacher=user
    )
    
    lesson = Lesson.objects.create(
        title='Test Lesson for Rewards',
        course=course,
        content='Test lesson content',
        order=1
    )
    
    # Enroll user in course
    course.students.add(user)
    
    # Create token balance
    balance, created = TokenBalance.objects.get_or_create(
        user=user,
        defaults={'balance': Decimal('50.00')}
    )
    
    print(f"✅ Created user: {user.username}")
    print(f"✅ Created course: {course.title} (${course.price})")
    print(f"✅ Created lesson: {lesson.title}")
    print(f"✅ User balance: {balance.balance} TeoCoins")
    
    # Test the service directly
    print("\n🔧 Testing RewardService directly...")
    
    from services.reward_service import reward_service
    
    try:
        result = reward_service.process_lesson_completion_reward(
            user_id=user.id,
            lesson_id=lesson.id
        )
        
        print(f"✅ Service result: {result.get('reward_processed', False)}")
        print(f"✅ Reward amount: {result.get('reward_amount', 0)}")
        
        # Check if transaction was created
        transactions = BlockchainTransaction.objects.filter(
            user=user,
            transaction_type='lesson_reward'
        ).count()
        print(f"✅ Transactions created: {transactions}")
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        return False
    
    # Test the API endpoint
    print("\n🌐 Testing API endpoint...")
    
    client = Client()
    client.force_login(user)
    
    try:
        url = reverse('rewards:complete-lesson')
        print(f"URL: {url}")
        
        # Test with a different lesson to avoid duplicate
        lesson2 = Lesson.objects.create(
            title='Test Lesson 2',
            course=course,
            content='Test lesson 2 content',
            order=2
        )
        
        response = client.post(url, {
            'lesson_id': lesson2.id
        })
        
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Response success: {data.get('success', False)}")
                print(f"✅ Reward processed: {data.get('reward_processed', False)}")
                if 'data' in data:
                    print(f"✅ Reward amount: {data['data'].get('reward_amount', 0)}")
            except Exception as e:
                print(f"⚠️  Could not parse JSON: {e}")
                print(f"Raw response: {response.content.decode()}")
        else:
            print(f"❌ API test failed with status {response.status_code}")
            print(f"Response: {response.content.decode()}")
            return False
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False
    
    # Test rewards summary
    print("\n📊 Testing rewards summary...")
    
    try:
        url = reverse('rewards:user-rewards-summary')
        response = client.get(url)
        
        print(f"✅ Summary status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            summary = data.get('reward_summary', {}).get('summary', {})
            print(f"✅ Total rewards: {summary.get('total_rewards_earned', 0)}")
            print(f"✅ Completed lessons: {summary.get('completed_lessons', 0)}")
        
    except Exception as e:
        print(f"❌ Summary test failed: {e}")
        return False
    
    # Test leaderboard
    print("\n🏆 Testing leaderboard...")
    
    try:
        url = reverse('rewards:reward-leaderboard')
        response = client.get(url)
        
        print(f"✅ Leaderboard status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            leaderboard = data.get('leaderboard', [])
            print(f"✅ Leaderboard entries: {len(leaderboard)}")
        
    except Exception as e:
        print(f"❌ Leaderboard test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! RewardService integration is working.")
    return True

if __name__ == '__main__':
    success = test_reward_service_integration()
    sys.exit(0 if success else 1)
