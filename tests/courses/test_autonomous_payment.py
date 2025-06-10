#!/usr/bin/env python
"""
Test autonomous payment - before and after balances
"""
import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from web3 import Web3
from decimal import Decimal

def get_balances(teocoin_service, address):
    """Get TEO and MATIC balances for an address"""
    teo_balance = teocoin_service.get_balance(address)
    matic_wei = teocoin_service.w3.eth.get_balance(Web3.to_checksum_address(address))
    matic_balance = float(teocoin_service.w3.from_wei(matic_wei, 'ether'))
    return teo_balance, matic_balance

def test_autonomous_payment():
    """Test complete autonomous payment flow"""
    print("=== TESTING AUTONOMOUS PAYMENT FLOW ===")
    
    teocoin_service = TeoCoinService()
    student_address = '0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4'
    teacher_address = '0xE2fA8AfbF1B795f5dEd1a33aa360872E9020a9A0'
    
    # Get balances BEFORE payment
    print("\n📊 BALANCES BEFORE PAYMENT:")
    student_teo_before, student_matic_before = get_balances(teocoin_service, student_address)
    teacher_teo_before, teacher_matic_before = get_balances(teocoin_service, teacher_address)
    
    print(f"Student: {student_teo_before} TEO, {student_matic_before:.6f} MATIC")
    print(f"Teacher: {teacher_teo_before} TEO, {teacher_matic_before:.6f} MATIC")
    
    # Make API call to purchase course
    print("\n💰 MAKING COURSE PURCHASE API CALL...")
    
    # Login first
    login_response = requests.post(
        'http://localhost:8000/api/auth/login/',
        json={
            'email': 'student1@teoart.it',
            'password': 'password123'
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return
    
    session_cookies = login_response.cookies
    auth_headers = {}
    if 'csrftoken' in session_cookies:
        auth_headers['X-CSRFToken'] = session_cookies['csrftoken']
    
    # Make payment request
    payment_data = {
        'teacher_address': teacher_address,
        'course_price': 15,
        'student_address': student_address,
        'course_id': 81  # Use existing course ID
    }
    
    response = requests.post(
        'http://localhost:8000/api/v1/blockchain/process-course-payment/',
        json=payment_data,
        cookies=session_cookies,
        headers=auth_headers
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Payment successful!")
        print(f"Transaction details: {json.dumps(result, indent=2)}")
        
        # Wait a moment for blockchain confirmation
        import time
        print("\n⏳ Waiting 10 seconds for blockchain confirmation...")
        time.sleep(10)
        
        # Get balances AFTER payment
        print("\n📊 BALANCES AFTER PAYMENT:")
        student_teo_after, student_matic_after = get_balances(teocoin_service, student_address)
        teacher_teo_after, teacher_matic_after = get_balances(teocoin_service, teacher_address)
        
        print(f"Student: {student_teo_after} TEO, {student_matic_after:.6f} MATIC")
        print(f"Teacher: {teacher_teo_after} TEO, {teacher_matic_after:.6f} MATIC")
        
        # Calculate changes
        print("\n📈 BALANCE CHANGES:")
        student_teo_change = student_teo_after - student_teo_before
        student_matic_change = student_matic_after - student_matic_before
        teacher_teo_change = teacher_teo_after - teacher_teo_before
        teacher_matic_change = teacher_matic_after - teacher_matic_before
        
        print(f"Student TEO: {student_teo_change:+} (should be -15)")
        print(f"Student MATIC: {student_matic_change:+.6f} (should be small negative for gas)")
        print(f"Teacher TEO: {teacher_teo_change:+} (should be +12.75)")
        print(f"Teacher MATIC: {teacher_matic_change:+.6f} (should be 0)")
        
        # Verify expected changes
        expected_student_teo = Decimal('-15')
        expected_teacher_teo = Decimal('12.75')
        
        if abs(student_teo_change - expected_student_teo) < Decimal('0.01'):
            print("✅ Student TEO change correct!")
        else:
            print("❌ Student TEO change incorrect!")
            
        if abs(teacher_teo_change - expected_teacher_teo) < Decimal('0.01'):
            print("✅ Teacher TEO change correct!")
        else:
            print("❌ Teacher TEO change incorrect!")
            
        if student_matic_change < 0:
            print("✅ Student paid gas fees!")
        else:
            print("❌ Student should have paid gas fees!")
        
    else:
        print(f"❌ Payment failed: {response.status_code}")
        try:
            error = response.json()
            print(f"Error: {json.dumps(error, indent=2)}")
        except:
            print(f"Raw response: {response.text}")

if __name__ == '__main__':
    test_autonomous_payment()
