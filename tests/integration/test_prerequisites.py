#!/usr/bin/env python3
"""
Test della funzione di verifica prerequisiti per il pagamento corso
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from eth_account import Account

def test_prerequisites():
    """Test dei prerequisiti per il pagamento corso"""
    print("🔍 === TEST PREREQUISITI PAGAMENTO CORSO ===")
    
    tcs = TeoCoinService()
    
    # Crea un account test senza fondi
    test_account = Account.create()
    student_address = test_account.address
    course_price = Decimal('20.0')
    
    print(f"👨‍🎓 Account test: {student_address}")
    print(f"💰 Prezzo corso: {course_price} TEO")
    
    # Verifica prerequisiti
    result = tcs.check_course_payment_prerequisites(student_address, course_price)
    
    print("\n📋 === RISULTATO VERIFICA ===")
    print(f"🎯 Pronto per pagamento: {result.get('ready', False)}")
    
    if result.get('student'):
        student_info = result['student']
        print(f"👨‍🎓 Studente TEO Balance: {student_info.get('teo_balance', 0)}")
        print(f"⛽ Studente MATIC Balance: {student_info.get('matic_balance', 0)}")
        print(f"✅ Ha abbastanza TEO: {student_info.get('has_enough_teo', False)}")
        print(f"⛽ Ha abbastanza MATIC: {student_info.get('has_enough_matic', False)}")
    
    if result.get('reward_pool'):
        pool_info = result['reward_pool']
        print(f"🏦 Reward Pool MATIC: {pool_info.get('matic_balance', 0)}")
        print(f"✅ Pool ha abbastanza MATIC: {pool_info.get('has_enough_matic', False)}")
    
    # Test anche con studente che ha fondi
    print("\n🔄 === TEST CON STUDENTE CON FONDI ===")
    # Usa uno degli account admin per testare con fondi
    admin_address = os.getenv('ADMIN_ADDRESS', '')
    if admin_address:
        result2 = tcs.check_course_payment_prerequisites(admin_address, course_price)
        print(f"🎯 Admin pronto per pagamento: {result2.get('ready', False)}")
        if result2.get('student'):
            student_info = result2['student']
            print(f"👨‍💼 Admin TEO Balance: {student_info.get('teo_balance', 0)}")
            print(f"⛽ Admin MATIC Balance: {student_info.get('matic_balance', 0)}")

if __name__ == "__main__":
    test_prerequisites()
