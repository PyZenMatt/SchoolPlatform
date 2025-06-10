#!/usr/bin/env python3
"""
Test per verificare che l'API blockchain funzioni con autenticazione.
"""

import requests
import json

def test_blockchain_api_with_auth():
    """Test API blockchain con autenticazione"""
    base_url = "http://127.0.0.1:8000"
    
    print("🔐 Test API Blockchain con Autenticazione")
    print("=" * 50)
    
    # Step 1: Login per ottenere il token
    print("1. Effettuo login...")
    login_data = {
        "username": "student1",
        "password": "password123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/api/v1/auth/login/", json=login_data)
        print(f"   Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            tokens = login_response.json()
            access_token = tokens.get('access')
            print("   ✅ Login riuscito!")
            
            # Step 2: Test API blockchain con token
            print("\n2. Test API blockchain...")
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Test balance
            balance_response = requests.get(f"{base_url}/api/v1/blockchain/balance/", headers=headers)
            print(f"   Balance API status: {balance_response.status_code}")
            if balance_response.status_code == 200:
                balance_data = balance_response.json()
                print(f"   ✅ Balance: {balance_data}")
            else:
                print(f"   ❌ Balance error: {balance_response.text}")
            
            # Test transactions
            tx_response = requests.get(f"{base_url}/api/v1/blockchain/transactions/", headers=headers)
            print(f"   Transactions API status: {tx_response.status_code}")
            if tx_response.status_code == 200:
                tx_data = tx_response.json()
                print(f"   ✅ Transactions count: {len(tx_data.get('results', []))}")
                if tx_data.get('results'):
                    print(f"   📊 First transaction: {tx_data['results'][0].get('transaction_type', 'N/A')}")
            else:
                print(f"   ❌ Transactions error: {tx_response.text}")
                
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("   ❌ Server non raggiungibile. Assicurati che Django sia in esecuzione.")
        return False
    except Exception as e:
        print(f"   ❌ Errore: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_blockchain_api_with_auth()
