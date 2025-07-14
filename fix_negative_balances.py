#!/usr/bin/env python3
"""
Emergency script to fix negative TeoCoin balances caused by double-deduction bug
"""

import os
import django
import sys

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.models import DBTeoCoinBalance, TeoCoinWithdrawalRequest
from decimal import Decimal
from django.db import transaction

def fix_negative_balances():
    """Fix negative balances by analyzing withdrawal requests"""
    
    print("🔍 Scanning for negative balances...")
    
    negative_balances = DBTeoCoinBalance.objects.filter(available_balance__lt=0)
    
    for balance in negative_balances:
        user = balance.user
        negative_amount = abs(balance.available_balance)
        
        print(f"\n👤 User: {user.email}")
        print(f"💰 Current available balance: {balance.available_balance} TEO")
        print(f"⏳ Current pending withdrawal: {balance.pending_withdrawal} TEO")
        
        # Check if there are pending withdrawals that might have been double-deducted
        pending_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
            user=user,
            status='pending'
        ).order_by('-created_at')
        
        total_pending = sum(w.amount for w in pending_withdrawals)
        
        print(f"📋 Pending withdrawal requests: {len(pending_withdrawals)}")
        print(f"💸 Total pending amount: {total_pending} TEO")
        
        # Calculate what the balance should be if we hadn't double-deducted
        corrected_available = balance.available_balance + negative_amount
        
        print(f"🔧 Suggested correction:")
        print(f"   Available balance: {balance.available_balance} TEO → {corrected_available} TEO")
        
        # Ask for confirmation
        response = input(f"\n❓ Fix this balance? (y/n): ").lower().strip()
        
        if response == 'y':
            with transaction.atomic():
                balance.available_balance = corrected_available
                balance.save()
                print(f"✅ Fixed! New available balance: {balance.available_balance} TEO")
        else:
            print("⏭️ Skipped")
    
    if not negative_balances.exists():
        print("✅ No negative balances found!")

def analyze_withdrawal_issue():
    """Analyze the withdrawal double-deduction issue"""
    
    print("\n🔍 Analyzing recent withdrawal patterns...")
    
    recent_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
        status='pending'
    ).order_by('-created_at')[:10]
    
    for withdrawal in recent_withdrawals:
        user = withdrawal.user
        balance = DBTeoCoinBalance.objects.filter(user=user).first()
        
        if balance:
            print(f"\n👤 {user.email}")
            print(f"   Withdrawal: {withdrawal.amount} TEO")
            print(f"   Available: {balance.available_balance} TEO")
            print(f"   Pending: {balance.pending_withdrawal} TEO")
            print(f"   Status: {withdrawal.status}")
            print(f"   Created: {withdrawal.created_at}")

if __name__ == "__main__":
    print("🚨 TeoCoin Balance Fix Tool")
    print("=" * 50)
    
    analyze_withdrawal_issue()
    fix_negative_balances()
    
    print("\n✅ Analysis and fixes complete!")
    print("💡 Recommendation: Apply the withdrawal service fixes to prevent future issues.")
