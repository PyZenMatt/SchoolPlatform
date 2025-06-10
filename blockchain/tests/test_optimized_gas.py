#!/usr/bin/env python3
"""
Test del gas price ottimizzato per Polygon Amoy
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

def test_optimized_gas():
    """Test del trasferimento con gas price ottimizzato"""
    print("🔧 Testing optimized gas price for Polygon Amoy...")
    
    try:
        # Inizializza il servizio
        service = TeoCoinService()
        
        # Test 1: Controlla gas price attuale dalla rete
        current_gas_price = service.w3.eth.gas_price
        current_gas_gwei = service.w3.from_wei(current_gas_price, 'gwei')
        print(f"📊 Current network gas price: {current_gas_gwei} Gwei")
        
        # Test 2: Simula calcolo gas price ottimizzato
        min_gas_price = service.w3.to_wei('2', 'gwei')
        max_gas_price = service.w3.to_wei('10', 'gwei')
        
        optimized_gas_price = current_gas_price
        if optimized_gas_price < min_gas_price:
            optimized_gas_price = min_gas_price
        if optimized_gas_price > max_gas_price:
            optimized_gas_price = max_gas_price
            
        optimized_gas_gwei = service.w3.from_wei(optimized_gas_price, 'gwei')
        print(f"⚡ Optimized gas price: {optimized_gas_gwei} Gwei")
        
        # Test 3: Calcola costo transazione stimato
        gas_limit = 80000  # Per transfer
        estimated_cost_matic = service.w3.from_wei(optimized_gas_price * gas_limit, 'ether')
        print(f"💰 Estimated transaction cost: {estimated_cost_matic} MATIC")
        
        # Test 4: Trova admin wallet
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("❌ Admin user not found")
            return
            
        admin_wallet = UserWallet.objects.filter(user=admin_user).first()
        if not admin_wallet:
            print("❌ Admin wallet not found")
            return
            
        print(f"👤 Admin wallet: {admin_wallet.address}")
        
        # Test 5: Controlla balance MATIC admin
        admin_balance_wei = service.w3.eth.get_balance(service.w3.to_checksum_address(admin_wallet.address))
        admin_balance_matic = service.w3.from_wei(admin_balance_wei, 'ether')
        print(f"💳 Admin MATIC balance: {admin_balance_matic}")
        
        # Test 6: Verifica se admin ha abbastanza MATIC per la transazione
        if admin_balance_matic > estimated_cost_matic:
            print(f"✅ Admin has enough MATIC for transaction")
            
            # Test 7: Trova uno studente per test transfer
            student = User.objects.filter(is_superuser=False, is_staff=False).first()
            if student:
                student_wallet = UserWallet.objects.filter(user=student).first()
                if student_wallet:
                    print(f"🎯 Test target: {student.username} ({student_wallet.address})")
                    
                    # Test 8: Tentativo di trasferimento con gas ottimizzato
                    print(f"🚀 Attempting transfer with optimized gas...")
                    result = service.transfer_tokens(
                        from_private_key=admin_wallet.private_key,
                        to_address=student_wallet.address,
                        amount=Decimal('1.0')
                    )
                    
                    if result:
                        print(f"✅ Transfer successful! TX: {result}")
                        print(f"🎉 Gas optimization working!")
                    else:
                        print(f"❌ Transfer failed - check logs for details")
                else:
                    print(f"❌ Student wallet not found")
            else:
                print(f"❌ No student found for test")
        else:
            print(f"❌ Admin has insufficient MATIC ({admin_balance_matic}) for transaction cost ({estimated_cost_matic})")
            print(f"💡 Need to add MATIC to admin wallet from Polygon faucet")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimized_gas()
