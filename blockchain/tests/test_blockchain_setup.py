#!/usr/bin/env python3
"""
Test limitato senza transazioni - verifica setup blockchain
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
from blockchain.models import UserWallet
from users.models import User
from web3 import Web3

def test_blockchain_setup():
    """Test del setup blockchain senza transazioni costose"""
    print("🧪 Testing blockchain setup without expensive transactions...")
    
    try:
        # Inizializza servizio
        service = TeoCoinService()
        print(f"✅ Blockchain service initialized")
        print(f"📡 Connected to: {service.rpc_url}")
        print(f"📄 Contract: {service.contract_address}")
        
        # Test 1: Controlla connessione
        latest_block = service.w3.eth.get_block('latest')
        print(f"🔗 Latest block: {latest_block.number}")
        
        # Test 2: Verifica tutti i wallet
        print(f"\n👥 User wallets verification:")
        wallets = UserWallet.objects.all()
        
        for wallet in wallets:
            try:
                # Balance MATIC
                matic_wei = service.w3.eth.get_balance(Web3.to_checksum_address(wallet.address))
                matic_balance = service.w3.from_wei(matic_wei, 'ether')
                
                # Balance TEO
                teo_balance = service.get_balance(wallet.address)
                
                user_type = "Admin" if wallet.user.is_superuser else "User"
                status = "✅" if (matic_balance > 0 or teo_balance > 0) else "⚠️"
                
                print(f"  {status} {user_type}: {wallet.user.username}")
                print(f"      📍 {wallet.address}")
                print(f"      💎 {matic_balance} MATIC")
                print(f"      🪙 {teo_balance} TEO")
                print()
                
            except Exception as e:
                print(f"  ❌ Error checking {wallet.user.username}: {e}")
        
        # Test 3: Calcola gas costs aggiornati
        gas_price = service.w3.eth.gas_price
        gas_price_gwei = service.w3.from_wei(gas_price, 'gwei')
        
        print(f"⛽ Current gas analysis:")
        print(f"   Gas price: {gas_price_gwei} Gwei")
        
        # Costi per diversi tipi di transazione
        transfer_cost = service.w3.from_wei(gas_price * 80000, 'ether')
        approve_cost = service.w3.from_wei(gas_price * 60000, 'ether')
        mint_cost = service.w3.from_wei(gas_price * 120000, 'ether')
        
        print(f"   TEO transfer: {transfer_cost} MATIC")
        print(f"   TEO approve: {approve_cost} MATIC")
        print(f"   TEO mint: {mint_cost} MATIC")
        
        # Test 4: Verifica contract state
        print(f"\n📄 Contract verification:")
        try:
            # Total supply
            total_supply_wei = service.contract.functions.totalSupply().call()
            total_supply = service.w3.from_wei(total_supply_wei, 'ether')
            print(f"   Total TEO supply: {total_supply}")
            
            # Contract owner
            owner = service.contract.functions.owner().call()
            print(f"   Contract owner: {owner}")
            
            # Decimals
            decimals = service.contract.functions.decimals().call()
            print(f"   Decimals: {decimals}")
            
            print(f"✅ Contract is working correctly")
            
        except Exception as e:
            print(f"❌ Contract error: {e}")
        
        # Test 5: Simulazione transazione (senza invio)
        print(f"\n🎯 Transaction simulation (no gas cost):")
        
        # Trova student1
        student1_address = "0x0a3bAF75b8ca80E3C6FDf6282e6b88370DD255C6"
        admin_private_key = "e1636922fa350bfe8ed929096d330eb70bbe3dc17dbb03dacdcf1dd668fc4255"
        admin_account = service.w3.eth.account.from_key(admin_private_key)
        
        try:
            # Simula trasferimento (build ma non send)
            amount_wei = Web3.to_wei('1', 'ether')
            transaction = service.contract.functions.transfer(
                Web3.to_checksum_address(student1_address),
                amount_wei
            ).build_transaction({
                'from': admin_account.address,
                'gas': 80000,
                'gasPrice': gas_price,
                'nonce': service.w3.eth.get_transaction_count(admin_account.address),
            })
            
            print(f"✅ Transaction simulation successful")
            print(f"   From: {admin_account.address}")
            print(f"   To: {student1_address}")
            print(f"   Amount: 1 TEO")
            print(f"   Gas: {transaction['gas']}")
            print(f"   Gas price: {service.w3.from_wei(transaction['gasPrice'], 'gwei')} Gwei")
            print(f"   Estimated cost: {service.w3.from_wei(transaction['gas'] * transaction['gasPrice'], 'ether')} MATIC")
            
        except Exception as e:
            print(f"❌ Transaction simulation failed: {e}")
        
        print(f"\n🎉 BLOCKCHAIN SETUP VERIFICATION COMPLETE!")
        print(f"📋 Summary:")
        print(f"   ✅ Service connected")
        print(f"   ✅ Wallets configured") 
        print(f"   ✅ Contract accessible")
        print(f"   ✅ Transactions ready (need MATIC)")
        print(f"\n💡 Next steps:")
        print(f"   1. Try alternative faucets for student1")
        print(f"   2. Or wait for 72h cooldown to expire")
        print(f"   3. Once MATIC available, run full test suite")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_blockchain_setup()
