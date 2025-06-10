#!/usr/bin/env python3
"""
Test dell'API execute_course_payment per simulare il flusso MetaMask completo
"""

import os
import sys
import django
import requests
import json
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course
from blockchain.blockchain import teocoin_service

User = get_user_model()

def test_execute_payment_api():
    """Test dell'API execute_course_payment"""
    
    print("🚀 Test API execute_course_payment")
    print("=" * 40)
    
    try:
        # Setup
        student = User.objects.get(username="student1")
        course = Course.objects.filter(is_approved=True).first()
        
        if not course or not student.wallet_address or not course.teacher.wallet_address:
            print("❌ Setup incompleto")
            return
            
        print(f"👤 Studente: {student.username}")
        print(f"📖 Corso: {course.title} - {course.price} TEO")
        print(f"👨‍🏫 Teacher: {course.teacher.username}")
        
        # Login
        login_response = requests.post(
            "http://127.0.0.1:8000/api/v1/token/",
            data={
                "email": student.email,
                "password": "password123"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return
            
        token = login_response.json()['access']
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Bilanci iniziali
        initial_student_balance = teocoin_service.get_balance(student.wallet_address)
        initial_teacher_balance = teocoin_service.get_balance(course.teacher.wallet_address)
        
        print(f"\n💰 Bilanci iniziali:")
        print(f"  Studente: {initial_student_balance} TEO")
        print(f"  Teacher: {initial_teacher_balance} TEO")
        
        # Simula chiamata API execute payment
        execute_data = {
            'student_address': student.wallet_address,
            'teacher_address': course.teacher.wallet_address,
            'course_price': str(course.price),
            'course_id': course.id,
            'approval_tx_hash': '0xtest_approval_hash_metamask_simulation',
            'teacher_amount': str(course.price * Decimal('0.85')),
            'commission_amount': str(course.price * Decimal('0.15'))
        }
        
        print(f"\n📤 Chiamata API execute payment...")
        print(f"URL: http://127.0.0.1:8000/api/v1/blockchain/execute-course-payment/")
        
        response = requests.post(
            "http://127.0.0.1:8000/api/v1/blockchain/execute-course-payment/",
            json=execute_data,
            headers=headers
        )
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Pagamento eseguito con successo!")
            print(json.dumps(result, indent=2))
            
            # Verifica bilanci finali
            print(f"\n🔍 Verifica bilanci finali...")
            final_student_balance = teocoin_service.get_balance(student.wallet_address)
            final_teacher_balance = teocoin_service.get_balance(course.teacher.wallet_address)
            
            print(f"  Studente: {initial_student_balance} → {final_student_balance} TEO")
            print(f"  Teacher: {initial_teacher_balance} → {final_teacher_balance} TEO")
            
            # Calcola differenze
            student_diff = float(final_student_balance) - float(initial_student_balance)
            teacher_diff = float(final_teacher_balance) - float(initial_teacher_balance)
            
            print(f"\n📈 Variazioni:")
            print(f"  Studente: {student_diff:+.2f} TEO")
            print(f"  Teacher: {teacher_diff:+.2f} TEO")
            
            if abs(student_diff + float(course.price)) < 0.01:  # Tolleranza per decimali
                print("✅ Bilancio studente corretto!")
            else:
                print(f"⚠️ Bilancio studente inaspettato (atteso: -{course.price})")
                
            expected_teacher_gain = float(course.price) * 0.85
            if abs(teacher_diff - expected_teacher_gain) < 0.01:
                print("✅ Bilancio teacher corretto!")
            else:
                print(f"⚠️ Bilancio teacher inaspettato (atteso: +{expected_teacher_gain})")
                
        else:
            print(f"❌ Errore API: {response.status_code}")
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(response.text)
                
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_execute_payment_api()
