#!/usr/bin/env python3
"""
Script semplice per testare il contratto TeoCoin
"""

import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from web3 import Web3

def main():
    print("🔍 Analisi TeoCoin Contract")
    print("=" * 40)
    
    try:
        service = TeoCoinService()
        print(f"✅ Connesso a: {service.rpc_url}")
        print(f"📄 Contratto: {service.contract_address}")
        
        # Info base
        name = service.contract.functions.name().call()
        symbol = service.contract.functions.symbol().call()
        total_supply = service.contract.functions.totalSupply().call()
        
        print(f"\n📊 Token Info:")
        print(f"   Nome: {name}")
        print(f"   Simbolo: {symbol}")  
        print(f"   Total Supply: {total_supply}")
        
        # Check admin key
        has_admin = bool(service.admin_private_key)
        print(f"\n🔑 Admin Key: {'✅ Configurata' if has_admin else '❌ Non configurata'}")
        
        if has_admin:
            admin_account = service.w3.eth.account.from_key(service.admin_private_key)
            admin_address = admin_account.address
            balance = service.w3.eth.get_balance(admin_address)
            matic_balance = service.w3.from_wei(balance, 'ether')
            
            print(f"   Admin Address: {admin_address}")
            print(f"   MATIC Balance: {matic_balance}")
            
            # Test se l'admin può mintare
            if float(matic_balance) > 0:
                print("\n🧪 Test Minting Permissions:")
                test_addr = "0x742d35Cc6cF000000000000000000001"
                test_amount = Web3.to_wei(1, 'ether')
                
                try:
                    gas_estimate = service.contract.functions.mintTo(
                        test_addr, test_amount
                    ).estimate_gas({'from': admin_address})
                    print(f"   ✅ Admin può mintare (gas stimato: {gas_estimate})")
                except Exception as e:
                    print(f"   ❌ Admin non può mintare: {str(e)}")
            else:
                print("   ⚠️ Admin non ha MATIC per gas")
        
        # Analisi ABI per funzioni di minting
        print(f"\n🔨 Funzioni di Minting nel contratto:")
        mint_functions = []
        for item in service.contract.abi:
            if item.get('type') == 'function' and 'mint' in item.get('name', '').lower():
                name = item.get('name')
                inputs = [f"{inp.get('type')} {inp.get('name')}" for inp in item.get('inputs', [])]
                print(f"   • {name}({', '.join(inputs)})")
                mint_functions.append(name)
        
        # Raccomandazioni
        print(f"\n💡 RACCOMANDAZIONI:")
        
        if has_admin:
            print("✅ STRATEGIA RACCOMANDATA: Server-side Minting")
            print("   • Il backend controlla tutto il minting")
            print("   • Reward automatici e sicuri")
            print("   • Gas fees gestite centralmente")
            print("\n📋 TODO:")
            print("   1. Assicurarsi che admin address abbia MATIC")
            print("   2. Verificare che admin sia owner del contratto")
            print("   3. Testare minting su Amoy testnet")
        else:
            print("⚠️ CONFIGURAZIONE NECESSARIA:")
            print("   1. Impostare ADMIN_PRIVATE_KEY nelle env")
            print("   2. Aggiungere MATIC all'admin address")
            print("   3. Verificare ownership del contratto")
            print("\n🔄 ALTERNATIVA: Claim-based System")
            print("   • Utenti fanno claim dei reward")
            print("   • Serve signature verification")
            print("   • Più complesso da implementare")
        
        print(f"\n🎯 CONCLUSIONI:")
        print(f"   • Contratto ha {len(mint_functions)} funzioni di minting")
        print(f"   • Admin key: {'Configurata' if has_admin else 'Da configurare'}")
        print(f"   • Strategia consigliata: {'Server-side' if has_admin else 'Configurare admin'}")
        
    except Exception as e:
        print(f"❌ Errore: {str(e)}")

if __name__ == "__main__":
    main()
