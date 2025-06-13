#!/usr/bin/env python3
"""
Script per verificare e/o creare transazioni admin per testare la dashboard
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from rewards.models import BlockchainTransaction, TokenBalance

def check_admin_transactions():
    """Verifica le transazioni esistenti per gli admin"""
    print("=== VERIFICA TRANSAZIONI ADMIN ===")
    
    # Trova tutti gli admin
    admins = User.objects.filter(is_staff=True)
    print(f"Admin trovati: {admins.count()}")
    
    for admin in admins:
        print(f"\nAdmin: {admin.username} (ID: {admin.id})")
        print(f"Email: {admin.email}")
        print(f"Wallet: {getattr(admin.blockchain_profile, 'wallet_address', 'N/A') if hasattr(admin, 'blockchain_profile') else 'N/A'}")
        
        # Transazioni come mittente (admin che invia)
        sent_transactions = BlockchainTransaction.objects.filter(user=admin, transaction_type__in=['transfer', 'course_purchase'])
        print(f"Transazioni inviate: {sent_transactions.count()}")
        
        # Transazioni come destinatario (admin che riceve)
        received_transactions = BlockchainTransaction.objects.filter(user=admin, transaction_type__in=['mint', 'reward', 'exercise_reward', 'review_reward', 'course_earned'])
        print(f"Transazioni ricevute: {received_transactions.count()}")
        
        # Tutte le transazioni dell'admin
        all_transactions = BlockchainTransaction.objects.filter(user=admin)
        print(f"Transazioni totali: {all_transactions.count()}")
        
        # Mostra le ultime 5 transazioni
        if all_transactions.exists():
            print("\nUltime 5 transazioni:")
            for tx in all_transactions.order_by('-created_at')[:5]:
                print(f"  - {tx.created_at}: {tx.transaction_type} - {tx.amount} TEO")
                print(f"    User: {tx.user.username}")
                print(f"    Da: {tx.from_address or 'Sistema'}")
                print(f"    A: {tx.to_address or 'N/A'}")
                print(f"    Hash: {tx.tx_hash or 'N/A'}")
                print(f"    Status: {tx.status}")
                print()

def create_test_platform_transactions():
    """Crea alcune transazioni di test per l'admin"""
    from blockchain.models import UserWallet
    from decimal import Decimal
    import uuid
    
    print("\n=== CREAZIONE TRANSAZIONI TEST ADMIN ===")
    
    # Trova l'admin principale
    admin = User.objects.filter(is_staff=True, is_superuser=True).first()
    if not admin:
        print("Nessun superuser trovato!")
        return
    
    print(f"Creando transazioni per admin: {admin.username}")
    
    # Crea o ottieni il wallet dell'admin
    wallet, created = UserWallet.objects.get_or_create(
        user=admin,
        defaults={
            'address': f"0x{uuid.uuid4().hex[:40]}",
            'private_key': f"0x{uuid.uuid4().hex}"
        }
    )
    
    if created:
        print(f"Creato wallet per {admin.username}: {wallet.address}")
    
    # Crea o aggiorna il token balance
    balance, created = TokenBalance.objects.get_or_create(
        user=admin,
        defaults={'balance': Decimal('1000.0')}
    )
    
    # Trova uno studente per le transazioni
    student = User.objects.filter(is_staff=False, is_active=True).first()
    student_wallet = None
    if student:
        student_wallet, _ = UserWallet.objects.get_or_create(
            user=student,
            defaults={
                'address': f"0x{uuid.uuid4().hex[:40]}",
                'private_key': f"0x{uuid.uuid4().hex}"
            }
        )
    
    # Crea transazioni di esempio
    transactions_data = [
        {
            'transaction_type': 'reward',
            'amount': Decimal('50.0'),
            'from_address': None,  # Sistema
            'to_address': wallet.address,
            'status': 'completed',
            'notes': 'Reward amministrativo automatico'
        },
        {
            'transaction_type': 'mint',
            'amount': Decimal('100.0'),
            'from_address': None,
            'to_address': wallet.address,
            'status': 'completed',
            'notes': 'Minting di TeoCoin per admin'
        },
        {
            'transaction_type': 'exercise_reward',
            'amount': Decimal('25.0'),
            'from_address': None,
            'to_address': wallet.address,
            'status': 'completed',
            'notes': 'Premio per gestione esercizi'
        }
    ]
    
    if student_wallet:
        transactions_data.append({
            'transaction_type': 'transfer',
            'amount': Decimal('30.0'),
            'from_address': wallet.address,
            'to_address': student_wallet.address,
            'status': 'completed',
            'notes': f'Trasferimento a {student.username if student else "studente"}'
        })
    
    for tx_data in transactions_data:
        transaction = BlockchainTransaction.objects.create(
            user=admin,
            tx_hash=f"0x{uuid.uuid4().hex}",
            **tx_data
        )
        print(f"Creata transazione: {transaction.transaction_type} - {transaction.amount} TEO")
    
    print(f"\nTransazioni create con successo!")

if __name__ == "__main__":
    print("1. Verifica transazioni esistenti")
    check_admin_transactions()
    
    # Chiedi se creare transazioni di test
    response = input("\nVuoi creare transazioni di test per tutta la piattaforma? (y/n): ")
    if response.lower() == 'y':
        create_test_platform_transactions()
        print("\n" + "="*50)
        print("Verifica transazioni dopo la creazione:")
        check_admin_transactions()
