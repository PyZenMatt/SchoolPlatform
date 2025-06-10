"""
Management command per gestire la Reward Pool
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from blockchain.blockchain import (
    get_reward_pool_balance, 
    check_reward_pool_health, 
    TeoCoinService
)


class Command(BaseCommand):
    help = 'Gestisce la reward pool del sistema TeoCoins'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['status', 'balance', 'health', 'mint'],
            help='Azione da eseguire: status, balance, health, mint'
        )
        parser.add_argument(
            '--amount',
            type=float,
            help='Quantità di TEO da mintare nella reward pool (solo per action=mint)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'status':
            self.show_status()
        elif action == 'balance':
            self.show_balance()
        elif action == 'health':
            self.show_health()
        elif action == 'mint':
            amount = options.get('amount')
            if not amount:
                self.stdout.write(
                    self.style.ERROR('--amount è richiesto per l\'azione mint')
                )
                return
            self.mint_to_pool(Decimal(str(amount)))

    def show_status(self):
        """Mostra lo status completo della reward pool"""
        self.stdout.write(self.style.SUCCESS('\n=== REWARD POOL STATUS ==='))
        
        try:
            # Balance
            balance = get_reward_pool_balance()
            self.stdout.write(f'Balance: {balance} TEO')
            
            # Health check
            health = check_reward_pool_health()
            status = health['status']
            address = health['address']
            
            if status == 'healthy':
                status_style = self.style.SUCCESS
            elif status == 'warning':
                status_style = self.style.WARNING
            else:
                status_style = self.style.ERROR
            
            self.stdout.write(f'Address: {address}')
            self.stdout.write(status_style(f'Status: {status.upper()}'))
            self.stdout.write(f'Warning Threshold: {health["warning_threshold"]} TEO')
            self.stdout.write(f'Critical Threshold: {health["critical_threshold"]} TEO')
            
            # Statistiche aggiuntive
            if balance > 0:
                estimated_rewards = balance / Decimal('0.1')  # Assume 0.1 TEO per reward medio
                self.stdout.write(f'Estimated Rewards Available: ~{int(estimated_rewards)}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Errore nel recupero status: {e}'))

    def show_balance(self):
        """Mostra solo il balance della reward pool"""
        try:
            balance = get_reward_pool_balance()
            self.stdout.write(f'{balance}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Errore: {e}'))

    def show_health(self):
        """Mostra lo health check della reward pool"""
        try:
            health = check_reward_pool_health()
            status = health['status']
            
            if status == 'healthy':
                self.stdout.write(self.style.SUCCESS(f'HEALTHY - Balance: {health["balance"]} TEO'))
            elif status == 'warning':
                self.stdout.write(self.style.WARNING(f'WARNING - Balance: {health["balance"]} TEO (sotto {health["warning_threshold"]} TEO)'))
            else:
                self.stdout.write(self.style.ERROR(f'CRITICAL - Balance: {health["balance"]} TEO (sotto {health["critical_threshold"]} TEO)'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Errore: {e}'))

    def mint_to_pool(self, amount):
        """Minta token alla reward pool"""
        try:
            service = TeoCoinService()
            
            # Ottieni l'indirizzo della reward pool
            health = check_reward_pool_health()
            pool_address = health['address']
            
            self.stdout.write(f'Mintando {amount} TEO alla reward pool {pool_address}...')
            
            # Minta i token
            tx_hash = service.mint_tokens(pool_address, amount)
            
            if tx_hash:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Mint completato!')
                )
                self.stdout.write(f'Transaction Hash: {tx_hash}')
                
                # Mostra il nuovo balance
                new_balance = get_reward_pool_balance()
                self.stdout.write(f'Nuovo balance: {new_balance} TEO')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Mint fallito!')
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Errore durante il mint: {e}'))
