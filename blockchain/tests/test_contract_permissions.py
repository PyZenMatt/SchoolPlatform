#!/usr/bin/env python3
"""
Script per testare il contratto TeoCoin e vedere chi può mintare
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


def test_contract_permissions():
    """
    Testa i permessi del contratto TeoCoin
    """
    print("🔍 Analisi permessi contratto TeoCoin")
    
    service = TeoCoinService()
    
    if not service.w3.is_connected():
        print("❌ Impossibile connettersi alla blockchain")
        return
    
    print(f"✅ Connesso a: {service.rpc_url}")
    print(f"📄 Contratto: {service.contract_address}")
    
    try:
        # Ottieni informazioni base del token
        token_info = service.get_token_info()
        print(f"\n📊 Info Token:")
        print(f"   Nome: {token_info.get('name', 'N/A')}")
        print(f"   Simbolo: {token_info.get('symbol', 'N/A')}")
        print(f"   Total Supply: {token_info.get('total_supply', 'N/A')}")
        
        # Prova a vedere se c'è una funzione owner
        try:
            owner = service.contract.functions.owner().call()
            print(f"   Owner: {owner}")
        except Exception as e:
            print(f"   Owner: Non disponibile (il contratto potrebbe non avere owner)")
        
        # Verifica admin key
        print(f"\n🔑 Admin Key configurata: {'✅' if service.admin_private_key else '❌'}")
        
        if service.admin_private_key:
            admin_account = service.w3.eth.account.from_key(service.admin_private_key)
            admin_address = admin_account.address
            print(f"   Admin Address: {admin_address}")
            
            # Controlla balance admin
            admin_balance = service.w3.eth.get_balance(admin_address)
            admin_matic = service.w3.from_wei(admin_balance, 'ether')
            print(f"   Admin MATIC Balance: {admin_matic}")
            
            # Controlla se admin può mintare
            if admin_matic > 0:
                print("\n🧪 Test minting (simulazione)...")
                try:
                    # Non eseguiremo realmente, solo prepariamo la transazione
                    test_address = "0x742d35Cc6cF000000000000000000001"
                    test_amount = Web3.to_wei(1, 'ether')
                    
                    transaction = service.contract.functions.mintTo(
                        test_address, 
                        test_amount
                    ).build_transaction({
                        'from': admin_address,
                        'gas': 100000,
                        'gasPrice': service.w3.to_wei('20', 'gwei'),
                        'nonce': service.w3.eth.get_transaction_count(admin_address),
                    })
                    
                    print("   ✅ Transazione mintTo preparabile (admin ha probabilmente i permessi)")
                    print(f"   Gas stimato: {transaction['gas']}")
                    
                except Exception as e:
                    print(f"   ❌ Errore preparazione mintTo: {str(e)}")
                    if "execution reverted" in str(e):
                        print("   Probabilmente l'admin non ha permessi di minting")
            else:
                print("   ⚠️ Admin non ha MATIC per gas fees")
        
    except Exception as e:
        print(f"❌ Errore analisi contratto: {str(e)}")


def recommend_minting_strategy():
    """
    Raccomanda la migliore strategia di minting
    """
    print("\n💡 RACCOMANDAZIONI STRATEGIA MINTING")
    
    service = TeoCoinService()
    has_admin_key = bool(service.admin_private_key)
    
    if has_admin_key:
        print("\n🏆 STRATEGIA RACCOMANDATA: SERVER-SIDE MINTING")
        print("✅ Pro:")
        print("   - Controllo completo sui reward")
        print("   - Sicurezza massima (private key sul server)")
        print("   - Transazioni automatiche")
        print("   - Gas fees gestite centralmente")
        
        print("\n⚠️ Requisiti:")
        print("   1. Admin address deve avere MATIC per gas")
        print("   2. Admin deve essere owner/minter del contratto")
        print("   3. Private key sicura nelle env variables")
        
        print("\n🚀 Implementazione:")
        print("   - Sistema attuale è corretto")
        print("   - Reward automatici su approvazione esercizi")
        print("   - Minting immediato on-chain")
        
    else:
        print("\n🔧 STRATEGIA ALTERNATIVA: CLAIM-BASED SYSTEM")
        print("✅ Pro:")
        print("   - Non serve private key centralizzata")
        print("   - Utenti pagano le proprie gas fees")
        print("   - Più decentralizzato")
        
        print("\n❌ Contro:")
        print("   - Utenti devono fare claim manualmente")
        print("   - Serve MATIC per gas")
        print("   - UX più complessa")
        
        print("\n🚀 Implementazione:")
        print("   - Firma digitale reward con backend")
        print("   - Frontend permette claim con firma")
        print("   - Contratto verifica firma e minta")


if __name__ == "__main__":
    print("🔗 ANALISI CONTRATTO TEOCOIN E STRATEGIA MINTING 🔗\n")
    
    test_contract_permissions()
    recommend_minting_strategy()
    
    print("\n📋 PROSSIMI PASSI:")
    print("1. Verificare che admin address sia owner del contratto")
    print("2. Aggiungere MATIC all'admin address per gas")
    print("3. Testare minting su Amoy testnet")
    print("4. Implementare fallback per errori blockchain")
