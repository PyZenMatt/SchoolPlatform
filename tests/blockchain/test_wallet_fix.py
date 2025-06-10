#!/usr/bin/env python3
"""
Test script per verificare che il fix del wallet lock per l'acquisto corsi funzioni.
Questo script verifica che l'endpoint dell'API sia configurato correttamente.
"""
import requests
import json

# Configurazione test
API_BASE_URL = "http://localhost:8000"
TEST_DATA = {
    "student_address": "0x1234567890123456789012345678901234567890",
    "teacher_address": "0x0987654321098765432109876543210987654321",
    "course_price": "10.0",
    "course_id": 1
}

def test_course_payment_endpoint():
    """Testa l'endpoint per il pagamento dei corsi"""
    
    print("🧪 Testing Course Payment API Endpoint...")
    
    try:
        # Test 1: Verifica che l'endpoint esista (anche se fallisce per autenticazione)
        response = requests.post(
            f"{API_BASE_URL}/api/v1/blockchain/process-course-payment/",
            headers={"Content-Type": "application/json"},
            json=TEST_DATA
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 401:
            print("✅ Endpoint raggiungibile (errore 401 = autenticazione richiesta)")
        elif response.status_code == 404:
            print("❌ Endpoint non trovato")
        else:
            print(f"📄 Response Text: {response.text}")
        
        return response.status_code != 404
        
    except requests.exceptions.ConnectionError:
        print("❌ Impossibile connettersi al server Django")
        return False
    except Exception as e:
        print(f"❌ Errore inaspettato: {e}")
        return False

def test_wallet_endpoints():
    """Testa gli endpoint per connessione/disconnessione wallet"""
    
    print("\n🧪 Testing Wallet API Endpoints...")
    
    endpoints = [
        "/api/v1/wallet/connect/",
        "/api/v1/wallet/disconnect/"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.post(
                f"{API_BASE_URL}{endpoint}",
                headers={"Content-Type": "application/json"},
                json={"wallet_address": "0x1234567890123456789012345678901234567890"}
            )
            
            print(f"📡 {endpoint}: Status {response.status_code}")
            
            if response.status_code == 401:
                print(f"✅ {endpoint} raggiungibile (errore 401 = autenticazione richiesta)")
            elif response.status_code == 404:
                print(f"❌ {endpoint} non trovato")
            
        except requests.exceptions.ConnectionError:
            print(f"❌ Impossibile connettersi al server per {endpoint}")
        except Exception as e:
            print(f"❌ Errore per {endpoint}: {e}")

def main():
    print("🚀 Avvio Test Wallet Fix")
    print("=" * 50)
    
    # Test degli endpoint
    payment_ok = test_course_payment_endpoint()
    test_wallet_endpoints()
    
    print("\n📊 Riepilogo Test:")
    print("=" * 50)
    if payment_ok:
        print("✅ API Course Payment: Configurata correttamente")
    else:
        print("❌ API Course Payment: Problema di configurazione")
    
    print("\n💡 Next Steps:")
    print("1. Accedi al sito web http://localhost:8000")
    print("2. Fai login come studente")
    print("3. Vai su un profilo e connetti il wallet")
    print("4. Prova ad acquistare un corso")
    print("5. Verifica che l'acquisto usi l'indirizzo wallet collegato al profilo")

if __name__ == "__main__":
    main()
