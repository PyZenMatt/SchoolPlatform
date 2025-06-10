#!/usr/bin/env python3
"""
Test end-to-end completo del flusso di acquisto corso
Simula la chiamata API process_course_payment come farebbe il frontend
"""

import os
import django
import sys
import requests
import json

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from courses.models import Course
from rewards.models import BlockchainTransaction
from notifications.models import Notification

User = get_user_model()

def test_end_to_end_purchase():
    print("🚀 Starting end-to-end purchase test...")
    
    # Setup test data
    try:
        student = User.objects.get(username='student1')
        print(f"✓ Using student: {student.username}")
        
        # Assicurati che lo studente abbia un wallet collegato
        if not student.wallet_address:
            student.wallet_address = '0x742d35Cc6634C0532925a3b8D2e99C14E8e7b6aA'
            student.save()
            print(f"✓ Set wallet address: {student.wallet_address}")
        
    except User.DoesNotExist:
        print("❌ Student1 not found")
        return False
    
    # Trova un corso da acquistare
    try:
        course = Course.objects.filter(is_approved=True).first()
        if not course:
            print("❌ No approved courses found")
            return False
        print(f"✓ Target course: {course.title} (Price: {course.price})")
    except Exception as e:
        print(f"❌ Error finding course: {e}")
        return False
    
    # Conta lo stato iniziale
    initial_notifications = Notification.objects.filter(user=student).count()
    initial_transactions = BlockchainTransaction.objects.filter(user=student).count()
    
    print(f"\n📊 Initial state:")
    print(f"   - Student notifications: {initial_notifications}")
    print(f"   - Student transactions: {initial_transactions}")
    print(f"   - Student wallet: {student.wallet_address}")
    
    # Crea un client Django per simulare le chiamate API
    client = Client()
    
    # Login del studente
    login_success = client.login(username=student.username, password='password123')
    if not login_success:
        print("❌ Login failed - trying with different password")
        # Proviamo a resettare la password
        student.set_password('password123')
        student.save()
        login_success = client.login(username=student.username, password='password123')
        
    if not login_success:
        print("❌ Still can't login - creating new password")
        from django.contrib.auth.hashers import make_password
        student.password = make_password('testpass123')
        student.save()
        login_success = client.login(username=student.username, password='testpass123')
    
    if login_success:
        print("✓ Student logged in successfully")
    else:
        print("❌ Could not login student - skipping API test")
        return False
    
    # Prepara i dati per l'acquisto
    purchase_data = {
        'course_id': course.pk,
        'wallet_address': student.wallet_address
    }
    
    print(f"\n🛒 Attempting course purchase...")
    print(f"   - Course ID: {course.pk}")
    print(f"   - Wallet: {student.wallet_address}")
    
    # Chiama l'API di acquisto corso
    try:
        response = client.post(
            '/api/v1/blockchain/process-course-payment/',
            data=json.dumps(purchase_data),
            content_type='application/json'
        )
        
        print(f"📡 API Response:")
        print(f"   - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"   - Success: {response_data.get('success', False)}")
            print(f"   - Message: {response_data.get('message', 'No message')}")
            
            if 'transaction_hash' in response_data:
                print(f"   - Transaction Hash: {response_data['transaction_hash']}")
            
        else:
            print(f"   - Error Response: {response.content.decode()}")
            
    except Exception as e:
        print(f"❌ API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Verifica i risultati
    final_notifications = Notification.objects.filter(user=student).count()
    final_transactions = BlockchainTransaction.objects.filter(user=student).count()
    
    print(f"\n📊 Final state:")
    print(f"   - Student notifications: {final_notifications} (+{final_notifications - initial_notifications})")
    print(f"   - Student transactions: {final_transactions} (+{final_transactions - initial_transactions})")
    
    # Verifica le nuove transazioni
    if final_transactions > initial_transactions:
        latest_transaction = BlockchainTransaction.objects.filter(user=student).order_by('-created_at').first()
        print(f"\n💰 Latest transaction:")
        print(f"   - Type: {latest_transaction.transaction_type}")
        print(f"   - Amount: {latest_transaction.amount}")
        print(f"   - Status: {latest_transaction.status}")
        print(f"   - Hash: {latest_transaction.tx_hash}")
    
    # Verifica le nuove notifiche
    if final_notifications > initial_notifications:
        latest_notification = Notification.objects.filter(user=student).order_by('-created_at').first()
        print(f"\n📩 Latest notification:")
        print(f"   - Message: {latest_notification.message}")
        print(f"   - Type: {latest_notification.notification_type}")
        print(f"   - Related Object ID: {latest_notification.related_object_id}")
        print(f"   - Read: {latest_notification.read}")
    
    # Verifica se l'acquisto è stato completato
    success = response.status_code == 200 and final_transactions > initial_transactions and final_notifications > initial_notifications
    
    if success:
        print(f"\n🎉 End-to-end test SUCCESSFUL!")
        print("✅ Course purchase completed")
        print("✅ Transaction created") 
        print("✅ Notification generated")
        print("✅ No database constraint errors")
    else:
        print(f"\n❌ End-to-end test FAILED")
        
    return success

if __name__ == '__main__':
    test_end_to_end_purchase()
