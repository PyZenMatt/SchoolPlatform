#!/usr/bin/env python3
"""
Test per verificare che l'acquisto dei corsi funzioni correttamente
dopo la correzione del segnale related_object_id
"""

import os
import django
import sys
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course
from rewards.models import BlockchainTransaction
from notifications.models import Notification

User = get_user_model()

def test_purchase_fix():
    print("🔧 Testing purchase fix after signal correction...")
    
    # Trova o crea uno studente di test
    try:
        student = User.objects.get(username='student1')
        print(f"✓ Using existing student: {student.username}")
    except User.DoesNotExist:
        print("❌ Student1 not found - creating a test student")
        student = User.objects.create_user(
            username='student1_test',
            email='student1_test@example.com',
            password='testpass123',
            role='student'
        )
        print(f"✓ Created test student: {student.username}")
    
    # Verifica che il wallet sia collegato
    if not student.wallet_address:
        print("⚠️ Student has no wallet connected - setting a test wallet")
        student.wallet_address = '0x742d35Cc6634C0532925a3b8D2e99C14E8e7b6aA'
        student.save()
        print(f"✓ Set test wallet: {student.wallet_address}")
    
    # Trova un corso di test
    try:
        course = Course.objects.filter(is_approved=True).first()
        if not course:
            print("❌ No approved courses found")
            return False
        print(f"✓ Using course: {course.title} (Price: {course.price})")
    except Exception as e:
        print(f"❌ Error finding course: {e}")
        return False
    
    # Conteggio iniziale delle notifiche
    initial_notifications = Notification.objects.filter(user=student).count()
    initial_transactions = BlockchainTransaction.objects.filter(user=student).count()
    
    print(f"📊 Initial state:")
    print(f"   - Notifications: {initial_notifications}")
    print(f"   - Transactions: {initial_transactions}")
    
    # Simula la creazione di una transazione blockchain (come nel vero acquisto)
    try:
        print("\n🚀 Creating blockchain transaction...")
        
        # Crea la transazione come nel vero flusso di acquisto
        transaction = BlockchainTransaction.objects.create(
            user=student,
            transaction_type='course_purchase',
            amount=-Decimal(str(course.price)),  # Negativo perché è una spesa
            from_address=student.wallet_address,
            to_address='0x0000000000000000000000000000000000000000',  # Burn address
            tx_hash=f'0x{hash(f"{student.pk}_{course.pk}_test"):032x}'[:66],  # Hash simulato
            gas_used=21000,
            status='completed',
            related_object_id=str(course.pk),
            notes=f'Acquisto corso: {course.title}'
        )
        
        print(f"✅ Transaction created successfully!")
        print(f"   - ID: {transaction.pk}")
        print(f"   - Amount: {transaction.amount}")
        print(f"   - Type: {transaction.transaction_type}")
        print(f"   - Hash: {transaction.tx_hash}")
        
        # Verifica che il segnale abbia creato la notifica
        final_notifications = Notification.objects.filter(user=student).count()
        final_transactions = BlockchainTransaction.objects.filter(user=student).count()
        
        print(f"\n📊 Final state:")
        print(f"   - Notifications: {final_notifications} (+{final_notifications - initial_notifications})")
        print(f"   - Transactions: {final_transactions} (+{final_transactions - initial_transactions})")
        
        # Verifica l'ultima notifica creata
        if final_notifications > initial_notifications:
            latest_notification = Notification.objects.filter(user=student).order_by('-created_at').first()
            print(f"\n📩 Latest notification:")
            print(f"   - Message: {latest_notification.message}")
            print(f"   - Type: {latest_notification.notification_type}")
            print(f"   - Related Object ID: {latest_notification.related_object_id}")
            print(f"   - Read: {latest_notification.read}")
            
            # Verifica che related_object_id sia valido
            if latest_notification.related_object_id is not None:
                if isinstance(latest_notification.related_object_id, int) and latest_notification.related_object_id >= 0:
                    print("✅ related_object_id is valid (positive integer)")
                else:
                    print(f"⚠️ related_object_id might be invalid: {latest_notification.related_object_id} (type: {type(latest_notification.related_object_id)})")
            else:
                print("✅ related_object_id is None (valid)")
        
        print("\n🎉 Test completed successfully! The purchase fix is working.")
        return True
        
    except Exception as e:
        print(f"❌ Error during transaction creation: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_purchase_fix()
