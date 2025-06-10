#!/usr/bin/env python3
"""
Test semplice per verificare che il minting funzioni con la chiave privata configurata
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from web3 import Web3

def test_simple_minting():
    """Test basilare di minting"""
    print("🧪 TEST MINTING BASILARE")
    print("=" * 40)
    
    try:
        # Inizializza servizio
        service = TeoCoinService()
        print(f"✅ Servizio inizializzato")
        print(f"   RPC: {service.rpc_url}")
        print(f"   Contratto: {service.contract_address}")
        print(f"   Admin key configurata: {'✅' if service.admin_private_key else '❌'}")
        
        if not service.admin_private_key:
            print("❌ Admin private key non configurata!")
            return False
        
        # Ottieni admin address
        admin_account = service.w3.eth.account.from_key(service.admin_private_key)
        admin_address = admin_account.address
        print(f"   Admin address: {admin_address}")
        
        # Controlla balance MATIC
        admin_balance = service.w3.eth.get_balance(admin_address)
        admin_matic = service.w3.from_wei(admin_balance, 'ether')
        print(f"   Admin MATIC: {admin_matic}")
        
        if admin_matic <= 0:
            print("❌ Admin non ha MATIC per gas fees!")
            print("   Aggiungi MATIC dal faucet: https://faucet.polygon.technology/")
            return False
        
        # Test address valido per minting
        test_address = "0x691dea93DB427190CDF7B63Ba67E05b14C5deb6F"
        test_amount = Decimal('1.0')  # 1 TEO
        
        print(f"\n🎯 TENTATIVO MINTING:")
        print(f"   To: {test_address}")
        print(f"   Amount: {test_amount} TEO")
        
        # Controlla balance iniziale
        initial_balance = service.get_balance(test_address)
        print(f"   Balance iniziale: {initial_balance} TEO")
        
        # Tenta il minting
        tx_hash = service.mint_tokens(test_address, test_amount)
        
        if tx_hash:
            print(f"✅ MINTING RIUSCITO!")
            print(f"   TX Hash: {tx_hash}")
            
            # Aspetta conferma (opzionale per test rapido)
            import time
            print("   Aspettando conferma...")
            time.sleep(5)
            
            # Controlla nuovo balance
            new_balance = service.get_balance(test_address)
            print(f"   Balance finale: {new_balance} TEO")
            print(f"   Differenza: {new_balance - initial_balance} TEO")
            
            return True
        else:
            print("❌ MINTING FALLITO")
            return False
            
    except Exception as e:
        print(f"❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_contract_info():
    """Test info contratto"""
    print("\n📋 INFO CONTRATTO:")
    print("=" * 40)
    
    try:
        service = TeoCoinService()
        
        # Info base
        name = service.contract.functions.name().call()
        symbol = service.contract.functions.symbol().call()
        total_supply = service.contract.functions.totalSupply().call()
        
        print(f"   Nome: {name}")
        print(f"   Simbolo: {symbol}")
        print(f"   Total Supply: {Web3.from_wei(total_supply, 'ether')} {symbol}")
        
        # Prova a chiamare owner (se esiste)
        try:
            # Alcuni contratti hanno owner()
            owner_data = service.w3.eth.call({
                'to': service.contract_address,
                'data': Web3.to_hex(bytes.fromhex('8da5cb5b'))
            })
            if len(owner_data) == 32:
                owner = '0x' + owner_data[-20:].hex()
                print(f"   Owner: {owner}")
                
                # Controlla se admin è owner
                admin_account = service.w3.eth.account.from_key(service.admin_private_key)
                if admin_account.address.lower() == owner.lower():
                    print("   ✅ Admin è owner del contratto!")
                else:
                    print("   ⚠️ Admin NON è owner del contratto")
            else:
                print("   Owner: Non disponibile")
        except:
            print("   Owner: Funzione non disponibile")
            
    except Exception as e:
        print(f"❌ Errore info contratto: {e}")

if __name__ == "__main__":
    print("🔗 TEST RAPIDO MINTING TEOCOIN 🔗\n")
    
    # Test info contratto
    test_contract_info()
    
    # Test minting
    success = test_simple_minting()
    
    print(f"\n🎯 RISULTATO: {'✅ SUCCESSO' if success else '❌ FALLIMENTO'}")
    
    if success:
        print("\n🚀 SISTEMA PRONTO:")
        print("   • Minting funziona correttamente")
        print("   • Admin key configurata")
        print("   • Contratto raggiungibile")
        print("   • Gas fees disponibili")
        print("\n   Ora puoi sottomettere esercizi e i reward")
        print("   verranno mintati automaticamente on-chain!")
    else:
        print("\n🔧 AZIONI NECESSARIE:")
        print("   • Verificare admin key nel .env")
        print("   • Aggiungere MATIC per gas fees")
        print("   • Verificare permessi contratto")
