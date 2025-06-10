#!/usr/bin/env python3
"""
Test della nuova logica di pagamento corso:
- Lo studente paga in TeoCoins
- Il teacher riceve l'importo netto (prezzo - commissione 15%)
- La reward pool riceve la commissione
- La reward pool paga le gas fees in MATIC

Questo test verifica il funzionamento completo del sistema.
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
from courses.models import Course
from users.models import User
from eth_account import Account

def create_test_accounts():
    """Crea account di test per studente e teacher"""
    student_account = Account.create()
    teacher_account = Account.create()
    
    return {
        'student': {
            'address': student_account.address,
            'private_key': student_account.key.hex()
        },
        'teacher': {
            'address': teacher_account.address,
            'private_key': teacher_account.key.hex()
        }
    }

def test_new_course_payment_logic():
    """Test completo della nuova logica di pagamento corso"""
    print("🎓 === TEST NUOVA LOGICA PAGAMENTO CORSO ===")
    
    tcs = TeoCoinService()
    
    # 1. Stato iniziale reward pool
    print("\n📊 === STATO INIZIALE ===")
    initial_pool_balance = tcs.get_reward_pool_balance()
    reward_pool_address = os.getenv('REWARD_POOL_ADDRESS')
    initial_pool_matic = 0
    if reward_pool_address:
        from web3 import Web3
        initial_pool_matic = tcs.w3.from_wei(tcs.w3.eth.get_balance(Web3.to_checksum_address(reward_pool_address)), 'ether')
    
    print(f"💰 Reward Pool TeoCoins: {initial_pool_balance}")
    print(f"⛽ Reward Pool MATIC: {initial_pool_matic}")
    
    # Verifica se la reward pool ha abbastanza MATIC per le operazioni
    if initial_pool_matic < 0.01:  # Soglia minima 0.01 MATIC
        print(f"\n⚠️  === RICARICA REWARD POOL MATIC ===")
        print(f"MATIC insufficienti ({initial_pool_matic}), ricaricando...")
        try:
            fund_tx = tcs.emergency_fund_reward_pool_matic(Decimal('0.05'))  # 0.05 MATIC
            if fund_tx:
                print(f"✅ Ricaricati 0.05 MATIC alla reward pool - TX: {fund_tx}")
                import time
                time.sleep(10)  # Aspetta conferma
                # Aggiorna balance
                initial_pool_matic = tcs.w3.from_wei(tcs.w3.eth.get_balance(Web3.to_checksum_address(reward_pool_address)), 'ether')
                print(f"💰 Nuovo balance MATIC reward pool: {initial_pool_matic}")
            else:
                print("❌ Ricarica fallita")
        except Exception as e:
            print(f"❌ Errore nella ricarica: {e}")
    
    # 2. Crea account di test
    print("\n👥 === CREAZIONE ACCOUNT TEST ===")
    accounts = create_test_accounts()
    student_address = accounts['student']['address']
    teacher_address = accounts['teacher']['address']
    student_private_key = accounts['student']['private_key']
    
    print(f"👨‍🎓 Studente: {student_address}")
    print(f"👨‍🏫 Teacher: {teacher_address}")
    
    # 3. Inizializza studente con TeoCoins
    print("\n💰 === INIZIALIZZAZIONE STUDENTE ===")
    course_price = Decimal('20.0')  # 20 TEO
    initial_student_amount = Decimal('50.0')  # 50 TEO
    
    # Trasferisci TeoCoins dalla reward pool allo studente per test
    tx_hash = tcs.transfer_from_reward_pool(student_address, initial_student_amount)
    if not tx_hash:
        print("❌ Errore nel trasferimento iniziale allo studente")
        return
    
    print(f"✅ Trasferiti {initial_student_amount} TEO allo studente")
    print(f"📋 Transaction hash: {tx_hash}")
    
    # Attendi conferma transazione
    print("⏳ Attendo conferma transazione TeoCoins...")
    import time
    time.sleep(20)  # Attendi 20 secondi per conferma transazione TeoCoins
    
    # Verifica se la transazione è stata confermata
    try:
        receipt = tcs.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        print(f"✅ Transazione confermata - Block: {receipt['blockNumber']}, Gas Used: {receipt['gasUsed']}")
    except Exception as e:
        print(f"⚠️ Errore nella verifica della transazione: {e}")
        print("Continuiamo comunque...")
    
    # 4. Verifica balance iniziali
    print("\n💳 === BALANCE INIZIALI ===")
    student_balance = tcs.get_balance(student_address)
    teacher_balance = tcs.get_balance(teacher_address)
    
    print(f"Studente: {student_balance} TEO")
    print(f"Teacher: {teacher_balance} TEO")
    
    # Debug: verifica manualmente il balance dallo smart contract
    print("\n🔍 === DEBUG BALANCE ===")
    try:
        from web3 import Web3
        checksum_student = Web3.to_checksum_address(student_address)
        raw_balance = tcs.contract.functions.balanceOf(checksum_student).call()
        print(f"Raw balance (wei): {raw_balance}")
        print(f"Raw balance (TEO): {Web3.from_wei(raw_balance, 'ether')}")
    except Exception as e:
        print(f"Error checking raw balance: {e}")
    
    if student_balance < course_price:
        print(f"❌ Studente ha fondi insufficienti: {student_balance} < {course_price}")
        return
    
    # 5. Trasferimento MATIC allo studente per gas fees (necessario per approve)
    print("\n⛽ === TRASFERIMENTO MATIC ALLO STUDENTE ===")
    print("NOTA: In produzione, lo studente deve procurarsi MATIC da solo (faucet/exchange)")
    print("Qui lo facciamo automaticamente solo per il test")
    try:
        from web3 import Web3
        reward_pool_private_key = os.getenv('REWARD_POOL_PRIVATE_KEY')
        if reward_pool_private_key and reward_pool_address:
            # Trasferisci 0.01 MATIC per gas fees (quantità minima necessaria)
            gas_amount = Web3.to_wei('0.01', 'ether')  # 0.01 MATIC
            
            reward_pool_checksum = Web3.to_checksum_address(reward_pool_address)
            nonce = tcs.w3.eth.get_transaction_count(reward_pool_checksum)
            gas_tx = {
                'to': Web3.to_checksum_address(student_address),
                'value': gas_amount,
                'gas': 21000,
                'gasPrice': tcs.get_optimized_gas_price(),
                'nonce': nonce,
                'chainId': 80002  # Polygon Amoy chain ID
            }
            
            signed_gas_tx = tcs.w3.eth.account.sign_transaction(gas_tx, reward_pool_private_key)
            gas_tx_hash = tcs.w3.eth.send_raw_transaction(signed_gas_tx.raw_transaction)
            print(f"✅ Trasferiti 0.01 MATIC per gas allo studente - TX: {gas_tx_hash.hex()}")
            
            # Attendi conferma
            import time
            time.sleep(15)  # Aumentato a 15 secondi per attendere conferma MATIC
            
            # Verifica che il MATIC sia arrivato
            student_matic = tcs.w3.from_wei(tcs.w3.eth.get_balance(Web3.to_checksum_address(student_address)), 'ether')
            print(f"💰 Balance MATIC studente dopo trasferimento: {student_matic:.6f}")
            
            if student_matic < 0.005:  # Minimo necessario
                print("⚠️ MATIC non ancora confermato, attendo altri 10 secondi...")
                time.sleep(10)
        else:
            print("❌ Reward pool private key o address non disponibile per trasferimento gas")
    except Exception as e:
        print(f"❌ Errore nel trasferimento gas: {e}")
    
    # 6. Test pagamento corso con nuova logica pulita
    print(f"\n🎓 === PAGAMENTO CORSO ({course_price} TEO) ===")
    print("Nuova logica pulita:")
    print("1. Studente fa approve() con i suoi MATIC")
    print("2. Reward Pool fa transferFrom() studente->teacher con i suoi MATIC") 
    print("3. Reward Pool fa transferFrom() studente->reward_pool con i suoi MATIC")
    
    result = tcs.process_course_payment(
        student_private_key=student_private_key,
        teacher_address=teacher_address,
        course_price=course_price
    )
    
    if not result:
        print("❌ Pagamento corso fallito")
        return
    
    print("✅ Pagamento corso completato!")
    print(f"📋 Approval TX: {result['approval_tx']}")
    print(f"📋 Teacher Payment TX: {result['teacher_payment_tx']}")
    print(f"📋 Commission TX: {result['commission_tx']}")
    
    # 7. Verifica balance finali
    print("\n💳 === BALANCE FINALI ===")
    final_student_balance = tcs.get_balance(student_address)
    final_teacher_balance = tcs.get_balance(teacher_address)
    final_pool_balance = tcs.get_reward_pool_balance()
    
    print(f"Studente: {final_student_balance} TEO (era {student_balance})")
    print(f"Teacher: {final_teacher_balance} TEO (era {teacher_balance})")
    print(f"Reward Pool: {final_pool_balance} TEO (era {initial_pool_balance})")
    
    # 8. Calcoli e verifiche
    print("\n🧮 === VERIFICHE CALCOLI ===")
    commission_rate = Decimal('0.15')
    expected_commission = course_price * commission_rate
    expected_teacher_amount = course_price - expected_commission
    
    student_paid = student_balance - final_student_balance
    teacher_received = final_teacher_balance - teacher_balance
    commission_received = final_pool_balance - initial_pool_balance
    
    print(f"Studente ha pagato: {student_paid} TEO (atteso: {course_price})")
    print(f"Teacher ha ricevuto: {teacher_received} TEO (atteso: {expected_teacher_amount})")
    print(f"Commissione ricevuta: {commission_received} TEO (atteso: {expected_commission})")
    
    # Verifiche
    success = True
    tolerance = Decimal('0.001')  # Tolleranza per errori di arrotondamento
    
    if abs(student_paid - course_price) > tolerance:
        print(f"❌ Errore: Studente ha pagato {student_paid} invece di {course_price}")
        success = False
    
    if abs(teacher_received - expected_teacher_amount) > tolerance:
        print(f"❌ Errore: Teacher ha ricevuto {teacher_received} invece di {expected_teacher_amount}")
        success = False
    
    if abs(commission_received - expected_commission) > tolerance:
        print(f"❌ Errore: Commissione ricevuta {commission_received} invece di {expected_commission}")
        success = False
    
    if success:
        print("\n✅ === TUTTE LE VERIFICHE SONO PASSATE ===")
        print("🎉 La nuova logica di pagamento corso funziona correttamente!")
    else:
        print("\n❌ === ALCUNE VERIFICHE SONO FALLITE ===")
        print("🚨 Ci sono problemi nella logica di pagamento")
    
    # 9. Riepilogo finale
    print("\n📋 === RIEPILOGO TRANSAZIONI ===")
    print(f"💸 Studente -> Teacher: {teacher_received} TEO")
    print(f"💼 Studente -> Reward Pool (commissione): {commission_received} TEO")
    print(f"⛽ Gas fees pagati da: Reward Pool")
    print(f"💰 Totale pagato dallo studente: {student_paid} TEO")

if __name__ == "__main__":
    test_new_course_payment_logic()
