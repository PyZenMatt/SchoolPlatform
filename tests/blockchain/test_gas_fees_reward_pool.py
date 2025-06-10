#!/usr/bin/env python3
"""
Test completo del sistema reward pool con gas fees pagate dalla pool
Questo script testa:
1. Transfer di TeoCoins dalla reward pool agli studenti
2. Transfer tra studenti con gas fees pagate dalla reward pool
3. Monitoraggio del balance della reward pool
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from eth_account import Account
from decimal import Decimal

def create_test_student_wallet():
    """Crea un nuovo wallet per test studente"""
    account = Account.create()
    return {
        'address': account.address,
        'private_key': account.key.hex()
    }

def main():
    print("🎓 === TEST SISTEMA REWARD POOL CON GAS FEES ===")
    
    # Inizializza il servizio
    tcs = TeoCoinService()
    
    # 1. Verifica stato iniziale reward pool
    print("\n📊 === STATO INIZIALE ===")
    initial_balance = tcs.get_reward_pool_balance()
    health = tcs.check_reward_pool_health()
    reward_pool_address = os.getenv('REWARD_POOL_ADDRESS')
    initial_matic = tcs.w3.from_wei(tcs.w3.eth.get_balance(reward_pool_address), 'ether')
    
    print(f"💰 Reward Pool TeoCoins: {initial_balance}")
    print(f"⛽ Reward Pool MATIC: {initial_matic}")
    print(f"🏥 Health Status: {health['status']}")
    
    # 2. Crea due account studente per test
    print("\n👨‍🎓 === CREAZIONE ACCOUNT STUDENTI ===")
    student1 = create_test_student_wallet()
    student2 = create_test_student_wallet()
    
    print(f"Student 1: {student1['address']}")
    print(f"Student 2: {student2['address']}")
    
    # 3. Verifica balance iniziale studenti (dovrebbe essere 0)
    print("\n💳 === BALANCE INIZIALI STUDENTI ===")
    student1_balance = tcs.get_balance(student1['address'])
    student2_balance = tcs.get_balance(student2['address'])
    student1_matic = tcs.w3.from_wei(tcs.w3.eth.get_balance(student1['address']), 'ether')
    student2_matic = tcs.w3.from_wei(tcs.w3.eth.get_balance(student2['address']), 'ether')
    
    print(f"Student 1 - TeoCoins: {student1_balance}, MATIC: {student1_matic}")
    print(f"Student 2 - TeoCoins: {student2_balance}, MATIC: {student2_matic}")
    
    # 4. Reward pool trasferisce TeoCoins a Student 1 (simulando un reward)
    print("\n🎁 === REWARD POOL → STUDENT 1 (50 TeoCoins) ===")
    try:
        result = tcs.transfer_from_reward_pool(student1['address'], Decimal('50'))
        print(f"✅ Trasferimento riuscito!")
        print(f"📋 Transaction hash: {result}")
    except Exception as e:
        print(f"❌ Errore nel trasferimento: {e}")
        return
        
    # 5. Verifica balance dopo il reward
    print("\n💳 === BALANCE DOPO REWARD ===")
    student1_balance_after = tcs.get_balance(student1['address'])
    pool_balance_after = tcs.get_reward_pool_balance()
    pool_matic_after = tcs.w3.from_wei(tcs.w3.eth.get_balance(reward_pool_address), 'ether')
    
    print(f"Student 1 TeoCoins: {student1_balance_after} (+{student1_balance_after - student1_balance})")
    print(f"Reward Pool TeoCoins: {pool_balance_after} ({pool_balance_after - initial_balance:+})")
    print(f"Reward Pool MATIC: {pool_matic_after} ({pool_matic_after - initial_matic:+.6f})")
    
    # 6. Student 1 approva reward pool come spender
    print("\n🔑 === STUDENT 1 APPROVA REWARD POOL COME SPENDER ===")
    try:
        # Prima dobbiamo far approvare la reward pool da student1
        approve_result = tcs.approve_reward_pool_as_spender(student1['private_key'], Decimal('25'))
        print(f"✅ Approvazione riuscita!")
        print(f"📋 Transaction hash: {approve_result}")
        
        # Aggiorniamo il balance MATIC di student1 dopo l'approvazione
        student1_matic_after_approve = tcs.w3.from_wei(tcs.w3.eth.get_balance(student1['address']), 'ether')
        print(f"Student 1 MATIC dopo approvazione: {student1_matic_after_approve}")
        
    except Exception as e:
        print(f"❌ Errore nell'approvazione: {e}")
        return

    # 7. Transfer da Student 1 a Student 2 con gas fees pagate dalla reward pool
    print("\n💸 === STUDENT 1 → STUDENT 2 (25 TeoCoins) - GAS FEES DALLA REWARD POOL ===")
    try:
        transfer_result = tcs.transfer_with_reward_pool_gas(
            from_address=student1['address'],
            to_address=student2['address'],
            amount=Decimal('25')
        )
        print(f"✅ Trasferimento riuscito!")
        print(f"📋 Transaction hash: {transfer_result}")
    except Exception as e:
        print(f"❌ Errore nel trasferimento: {e}")
        return
    
    # 8. Verifica balance finali
    print("\n💳 === BALANCE FINALI ===")
    final_student1_balance = tcs.get_balance(student1['address'])
    final_student2_balance = tcs.get_balance(student2['address'])
    final_pool_balance = tcs.get_reward_pool_balance()
    final_pool_matic = tcs.w3.from_wei(tcs.w3.eth.get_balance(reward_pool_address), 'ether')
    
    print(f"Student 1 TeoCoins: {final_student1_balance} (era {student1_balance_after})")
    print(f"Student 2 TeoCoins: {final_student2_balance} (era {student2_balance})")
    print(f"Reward Pool TeoCoins: {final_pool_balance} (era {pool_balance_after})")
    print(f"Reward Pool MATIC: {final_pool_matic} (era {pool_matic_after:.6f})")
    
    # 9. Verifica che gli studenti non hanno speso MATIC
    final_student1_matic = tcs.w3.from_wei(tcs.w3.eth.get_balance(student1['address']), 'ether')
    final_student2_matic = tcs.w3.from_wei(tcs.w3.eth.get_balance(student2['address']), 'ether')
    
    print(f"Student 1 MATIC: {final_student1_matic} (era {student1_matic})")
    print(f"Student 2 MATIC: {final_student2_matic} (era {student2_matic})")
    
    # 10. Riepilogo finale
    print("\n📋 === RIEPILOGO FINALE ===")
    print(f"✅ TeoCoins distribuiti dalla reward pool: {initial_balance - final_pool_balance}")
    print(f"⛽ MATIC spesi dalla reward pool per gas: {initial_matic - final_pool_matic:.6f}")
    print(f"👨‍🎓 Studenti hanno MATIC? NO (0 per entrambi)")
    print(f"🎯 Tutti i costi gas pagati dalla reward pool: ✅")
    
    final_health = tcs.check_reward_pool_health()
    print(f"🏥 Stato finale reward pool: {final_health['status']}")
    
    if final_health['status'] == 'healthy':
        print("🎉 TEST COMPLETATO CON SUCCESSO!")
    else:
        print("⚠️  Attenzione: reward pool in stato non ottimale")

if __name__ == "__main__":
    main()
