#!/usr/bin/env python
"""
Add test TeoCoin balance to users for frontend testing
"""
import os
import sys
import django
from decimal import Decimal

# Set up Django environment
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from services.db_teocoin_service import DBTeoCoinService

User = get_user_model()

def add_test_balance():
    """Add test TeoCoin balance to all users"""
    print("🚀 Adding test TeoCoin balances to users...")
    
    service = DBTeoCoinService()
    
    # Get all users
    users = User.objects.all()
    
    if not users.exists():
        print("❌ No users found. Please create users first.")
        return
    
    for user in users:
        print(f"\n👤 Processing user: {user.username} ({user.email})")
        
        # Check current balance
        current_balance = service.get_user_balance(user)
        print(f"   Current balance: {current_balance['total_balance']} TEO")
        
        # Add test balance if user has less than 100 TEO
        if current_balance['total_balance'] < Decimal('100.00'):
            test_amount = Decimal('250.00')
            service.add_balance(
                user=user,
                amount=test_amount,
                transaction_type='test_credit',
                description='Test balance for frontend demo'
            )
            print(f"   ✅ Added {test_amount} TEO")
            
            # Add some staking for variety
            if user.username != 'admin':  # Skip admin for staking
                stake_amount = Decimal('50.00')
                stake_result = service.stake_tokens(user, stake_amount)
                if stake_result:
                    print(f"   🔒 Staked {stake_amount} TEO")
                
        else:
            print(f"   ℹ️  User already has sufficient balance")
    
    # Show final statistics
    print("\n📊 Final Platform Statistics:")
    stats = service.get_platform_statistics()
    print(f"   Users with balance: {stats['total_users_with_balance']}")
    print(f"   Total available: {stats['total_available_balance']} TEO")
    print(f"   Total staked: {stats['total_staked_balance']} TEO")
    print(f"   Total transactions: {stats['total_transactions']}")
    
    print("\n🎉 Test balances added successfully!")
    print("💡 You can now see TeoCoin balances in the frontend!")

if __name__ == "__main__":
    add_test_balance()
