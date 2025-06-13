#!/usr/bin/env python3
"""
Script per creare transazioni di test per la piattaforma blockchain
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
from blockchain.models import UserWallet
from decimal import Decimal
import uuid

def create_platform_transactions():
    """Crea transazioni di esempio per diversi utenti della piattaforma"""
    print("=== CREAZIONE TRANSAZIONI PIATTAFORMA ===")
    
    # Trova diversi utenti
    admin = User.objects.filter(is_staff=True, is_superuser=True).first()
    students = list(User.objects.filter(is_staff=False, is_active=True)[:3])
    teachers = list(User.objects.filter(is_staff=True, is_superuser=False)[:2])
    
    all_users = [admin] + students + teachers
    all_users = [u for u in all_users if u is not None]
    
    print(f"Creando transazioni per {len(all_users)} utenti:")
    for user in all_users:
        role = 'Admin' if user.is_superuser else 'Teacher' if user.is_staff else 'Student'
        print(f"  - {user.username} ({role})")
    
    # Crea wallet per tutti gli utenti
    wallets = {}
    for user in all_users:
        wallet, created = UserWallet.objects.get_or_create(
            user=user,
            defaults={
                'address': f"0x{uuid.uuid4().hex[:40]}",
                'private_key': f"0x{uuid.uuid4().hex}"
            }
        )
        wallets[user.id] = wallet
        
        # Crea token balance
        balance, created = TokenBalance.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('500.0')}
        )
    
    # Template delle transazioni
    transaction_templates = [
        {'type': 'exercise_reward', 'amount': '10.0', 'note': 'Completamento esercizio di matematica'},
        {'type': 'exercise_reward', 'amount': '15.0', 'note': 'Completamento esercizio avanzato'},
        {'type': 'course_earned', 'amount': '50.0', 'note': 'Completamento corso completo'},
        {'type': 'review_reward', 'amount': '5.0', 'note': 'Review positiva corso'},
        {'type': 'mint', 'amount': '100.0', 'note': 'Mint iniziale utente'},
        {'type': 'mint', 'amount': '200.0', 'note': 'Mint bonus iscrizione'},
        {'type': 'course_purchase', 'amount': '75.0', 'note': 'Acquisto corso premium'},
        {'type': 'course_purchase', 'amount': '45.0', 'note': 'Acquisto corso base'},
        {'type': 'transfer', 'amount': '25.0', 'note': 'Trasferimento peer-to-peer'},
        {'type': 'transfer', 'amount': '30.0', 'note': 'Regalo tra studenti'},
        {'type': 'reward', 'amount': '20.0', 'note': 'Partecipazione evento'},
        {'type': 'reward', 'amount': '35.0', 'note': 'Achievement sbloccato'},
    ]
    
    created_count = 0
    for i, template in enumerate(transaction_templates):
        user = all_users[i % len(all_users)]
        wallet = wallets[user.id]
        
        # Determina indirizzi from/to
        if template['type'] in ['mint', 'reward', 'exercise_reward', 'course_earned', 'review_reward']:
            from_address = None  # Sistema
            to_address = wallet.address
        elif template['type'] == 'course_purchase':
            from_address = wallet.address
            to_address = None  # Sistema/Corso
        else:  # transfer
            from_address = wallet.address
            other_users = [u for u in all_users if u.id != user.id]
            if other_users:
                other_user = other_users[i % len(other_users)]
                to_address = wallets[other_user.id].address
            else:
                to_address = wallet.address
        
        transaction = BlockchainTransaction.objects.create(
            user=user,
            transaction_type=template['type'],
            amount=Decimal(template['amount']),
            from_address=from_address,
            to_address=to_address,
            tx_hash=f"0x{uuid.uuid4().hex}",
            status='completed',
            notes=template['note']
        )
        
        print(f"✅ {template['type']}: {template['amount']} TEO → {user.username}")
        created_count += 1
    
    print(f"\n🎉 Create {created_count} transazioni di test per la piattaforma!")

def show_all_transactions():
    """Mostra tutte le transazioni della piattaforma"""
    print("\n=== TUTTE LE TRANSAZIONI PIATTAFORMA ===")
    
    transactions = BlockchainTransaction.objects.select_related('user').order_by('-created_at')
    print(f"Totale transazioni: {transactions.count()}")
    
    for tx in transactions:
        print(f"- {tx.created_at.strftime('%Y-%m-%d %H:%M')} | {tx.transaction_type} | {tx.amount} TEO | {tx.user.username} | {tx.status}")

if __name__ == "__main__":
    print("1. Mostra tutte le transazioni")
    show_all_transactions()
    
    response = input("\nVuoi creare transazioni di test? (y/n): ")
    if response.lower() == 'y':
        create_platform_transactions()
        print("\n" + "="*50)
        show_all_transactions()
