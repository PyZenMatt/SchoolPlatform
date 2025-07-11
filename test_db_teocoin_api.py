#!/usr/bin/env python
"""
Test script for DB-based TeoCoin API endpoints
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
from blockchain.models import DBTeoCoinBalance, DBTeoCoinTransaction

User = get_user_model()

def test_db_teocoin_system():
    """Test the complete DB-based TeoCoin system"""
    print("🧪 Testing DB-based TeoCoin System")
    print("=" * 50)
    
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='test_user_teocoin',
            defaults={
                'email': 'test@teocoin.test',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        print(f"📝 Using test user: {user.username} (created: {created})")
        
        # Initialize service
        service = DBTeoCoinService()
        
        # Test 1: Check initial balance
        print("\n1️⃣ Testing initial balance")
        balance = service.get_user_balance(user)
        print(f"   Initial balance: {balance} TEO")
        
        # Test 2: Add balance
        print("\n2️⃣ Testing add balance")
        service.add_balance(user, Decimal('100.50'), "Test credit")
        new_balance = service.get_user_balance(user)
        print(f"   Balance after adding 100.50 TEO: {new_balance} TEO")
        
        # Test 3: Stake tokens
        print("\n3️⃣ Testing staking")
        stake_result = service.stake_tokens(user, Decimal('50.00'))
        if stake_result:
            print(f"   ✅ Staked 50 TEO successfully")
            balance_info = service.get_user_balance(user)
            print(f"   Available balance: {balance_info['available_balance']} TEO")
            print(f"   Staked balance: {balance_info['staked_balance']} TEO")
        else:
            print(f"   ❌ Staking failed")
        
        # Test 4: Check staking info (get balance details)
        print("\n4️⃣ Testing balance after staking")
        balance_info = service.get_user_balance(user)
        print(f"   Available amount: {balance_info['available_balance']} TEO")
        print(f"   Staked amount: {balance_info['staked_balance']} TEO")
        print(f"   Total balance: {balance_info['total_balance']} TEO")
        
        # Test 5: Calculate discount
        print("\n5️⃣ Testing discount calculation")
        discount_info = service.calculate_discount(user, Decimal('200.00'))
        print(f"   Course price: 200.00 EUR")
        print(f"   TEO required: {discount_info['teo_required']} TEO")
        print(f"   Discount amount: {discount_info['discount_amount']} EUR")
        print(f"   Final price: {discount_info['final_price']} EUR")
        print(f"   Discount percentage: {discount_info['discount_percentage']}%")
        
        # Test 6: Apply discount
        print("\n6️⃣ Testing discount application")
        discount_amount = discount_info['teo_required']
        discount_result = service.apply_course_discount(
            user, 
            Decimal('200.00'), 
            "test_course_123", 
            "Test Course"
        )
        if discount_result['success']:
            print(f"   ✅ Applied discount successfully")
            print(f"   Discount value: {discount_result['discount_amount']} EUR")
            print(f"   Final price: {discount_result['final_price']} EUR")
        else:
            print(f"   ❌ Discount failed: {discount_result['message']}")
        
        # Test 7: Request withdrawal
        print("\n7️⃣ Testing withdrawal request")
        withdrawal_result = service.request_withdrawal(user, Decimal('10.00'), "0x1234567890123456789012345678901234567890")
        if withdrawal_result:
            print(f"   ✅ Withdrawal requested successfully")
            balance_info = service.get_user_balance(user)
            print(f"   Remaining balance: {balance_info['available_balance']} TEO")
        else:
            print(f"   ❌ Withdrawal failed")
        
        # Test 8: Transaction history
        print("\n8️⃣ Testing transaction history")
        transactions = service.get_user_transactions(user)
        print(f"   Total transactions: {len(transactions)}")
        for i, tx in enumerate(transactions[:3], 1):  # Show first 3
            print(f"   {i}. {tx['type']} - {tx['amount']} TEO - {tx['description']}")
        
        # Test 9: Platform statistics
        print("\n9️⃣ Testing platform statistics")
        stats = service.get_platform_statistics()
        print(f"   Users with balance: {stats['total_users_with_balance']}")
        print(f"   Total available: {stats['total_available_balance']} TEO")
        print(f"   Total staked: {stats['total_staked_balance']} TEO")
        print(f"   Total transactions: {stats['total_transactions']}")
        print(f"   Pending withdrawals: {stats['pending_withdrawal_requests']}")
        
        print("\n🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_teocoin_system()
