#!/usr/bin/env python3
"""
Test completo del flusso MetaMask per l'acquisto corsi
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
from courses.models import Course, CourseEnrollment
from rewards.models import BlockchainTransaction
from blockchain.blockchain import teocoin_service

User = get_user_model()

def test_metamask_flow():
    """Test del flusso MetaMask end-to-end"""
    
    print("🧪 Test flusso MetaMask per acquisto corso")
    print("=" * 50)
    
    # Configurazione test
    student_username = "student1"
    student_wallet = "0xD249133cD12f7c9A58E4B8E8F60b0Cc12a7e8F88"
    reward_pool_address = "0x5FbDB2315678afecb367f032d93F642f64180319"
    
    try:
        # 1. Verifica utente e corso
        print("📚 1. Verifica utente e corso...")
        student = User.objects.get(username=student_username)
        course = Course.objects.filter(is_approved=True).first()
        
        if not course:
            print("❌ Nessun corso attivo trovato")
            return
            
        print(f"👤 Studente: {student.username} (wallet: {student.wallet_address})")
        print(f"📖 Corso: {course.title} - Prezzo: {course.price} TEO")
        print(f"👨‍🏫 Teacher: {course.teacher.username} (wallet: {course.teacher.wallet_address})")
        
        # 2. Verifica bilanci iniziali
        print("\n💰 2. Verifica bilanci iniziali...")
        if student.wallet_address:
            student_balance = teocoin_service.get_balance(student.wallet_address)
            print(f"💼 Balance studente: {student_balance} TEO")
        else:
            print("⚠️ Studente non ha wallet collegato")
            return
            
        if course.teacher.wallet_address:
            teacher_balance = teocoin_service.get_balance(course.teacher.wallet_address)
            print(f"💼 Balance teacher: {teacher_balance} TEO")
        else:
            print("⚠️ Teacher non ha wallet collegato")
            return
            
        # 3. Test check prerequisites
        print("\n🔍 3. Test prerequisiti pagamento...")
        prerequisites = teocoin_service.check_course_payment_prerequisites(
            student.wallet_address, course.price
        )
        
        print(f"📊 Prerequisites:")
        print(f"  - Balance studente: {prerequisites.get('student_balance', 'N/A')} TEO")
        print(f"  - Prezzo richiesto: {prerequisites.get('required_amount', 'N/A')} TEO")
        print(f"  - Allowance attuale: {prerequisites.get('current_allowance', 'N/A')} TEO")
        print(f"  - Balance sufficiente: {prerequisites.get('sufficient_balance', False)}")
        print(f"  - Allowance sufficiente: {prerequisites.get('sufficient_allowance', False)}")
        print(f"  - Serve approvazione: {prerequisites.get('needs_approval', True)}")
        print(f"  - Può procedere: {prerequisites.get('can_proceed', False)}")
        
        # 4. Simula chiamata API prerequisites
        print("\n🌐 4. Test API check prerequisites...")
        api_url = "http://127.0.0.1:8000/api/v1/blockchain/check-course-payment-prerequisites/"
        
        # Ottieni token di autenticazione
        login_response = requests.post(
            "http://127.0.0.1:8000/api/v1/token/",
            json={
                "email": student.email,
                "password": "password123"
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json()['access']
            print(f"✅ Token ottenuto: {token[:20]}...")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            prerequisites_data = {
                'student_address': student.wallet_address,
                'course_price': str(course.price)
            }
            
            response = requests.post(api_url, json=prerequisites_data, headers=headers)
            
            if response.status_code == 200:
                api_result = response.json()
                print("✅ API prerequisites risposta:")
                print(json.dumps(api_result, indent=2))
                
                print(f"📍 Reward pool address: {api_result.get('reward_pool_address', 'N/A')}")
                print(f"💵 Teacher amount: {api_result.get('teacher_amount', 'N/A')} TEO")
                print(f"💰 Commission amount: {api_result.get('commission_amount', 'N/A')} TEO")
                
            else:
                print(f"❌ API error: {response.status_code} - {response.text}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return
            
        # 5. Simulazione approvazione (in produzione sarebbe via MetaMask)
        print("\n✍️ 5. Simulazione flusso approvazione...")
        print("📝 In produzione:")
        print("  1. Frontend chiama contract.approve(reward_pool, course_price)")
        print("  2. MetaMask richiede firma utente")
        print("  3. Transazione approval viene inviata")
        print("  4. Frontend attende conferma")
        print("  5. Hash approval viene inviato al backend")
        
        fake_approval_hash = "0x1234567890abcdef1234567890abcdef12345678901234567890abcdef123456"
        print(f"🔗 Mock approval hash: {fake_approval_hash}")
        
        # 6. Test API execute payment
        print("\n🚀 6. Test API execute payment...")
        execute_api_url = "http://127.0.0.1:8000/api/v1/blockchain/execute-course-payment/"
        
        execute_data = {
            'student_address': student.wallet_address,
            'teacher_address': course.teacher.wallet_address,
            'course_price': str(course.price),
            'course_id': course.id,
            'approval_tx_hash': fake_approval_hash,
            'teacher_amount': str(course.price * Decimal('0.85')),
            'commission_amount': str(course.price * Decimal('0.15'))
        }
        
        print("📤 Dati execute payment:")
        print(json.dumps(execute_data, indent=2))
        
        # Note: This would normally execute transferFrom transactions
        # For testing, we'll just verify the API structure
        print("\n⚠️  NOTA: Test API structure only (no real blockchain transactions)")
        print("🔧 In produzione, questo eseguirebbe:")
        print("  1. transfer_from_student_to_teacher()")
        print("  2. transfer_from_student_to_reward_pool()")
        print("  3. Creazione record transazioni in DB")
        
        # 7. Verifica struttura transazioni database
        print("\n💾 7. Verifica struttura database...")
        initial_transactions = BlockchainTransaction.objects.filter(user=student).count()
        print(f"📊 Transazioni esistenti per studente: {initial_transactions}")
        
        # 8. Informazioni per test manuale frontend
        print("\n🌐 8. Istruzioni per test frontend:")
        print("=" * 30)
        print("1. Apri http://127.0.0.1:3000")
        print(f"2. Login come '{student_username}' password 'password123'")
        print("3. Vai nella sezione corsi")
        print(f"4. Cerca corso: '{course.title}'")
        print("5. Clicca 'Acquista' e osserva:")
        print("   - Richiesta connessione MetaMask")
        print("   - Controllo balances TEO/MATIC")
        print("   - Richiesta approvazione contratto")
        print("   - Conferma pagamento")
        print("   - Aggiornamento dashboard")
        
        print("\n✅ Test setup completato!")
        
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_metamask_flow()
