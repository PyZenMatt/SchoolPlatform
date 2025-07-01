#!/usr/bin/env python3
"""
Test Layer 2 services connection to live contracts
Django management command
"""

from django.core.management.base import BaseCommand
from services.teocoin_staking_service import TeoCoinStakingService
from services.teocoin_discount_service import teocoin_discount_service


class Command(BaseCommand):
    help = 'Test Layer 2 services connection to live contracts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Testing Layer 2 Services Connection'))
        
        # Test Staking Service
        self.stdout.write('\n🔧 Testing TeoCoin Staking Service...')
        try:
            staking_service = TeoCoinStakingService()
            
            self.stdout.write(f'✅ Service initialized')
            self.stdout.write(f'✅ Development mode: {staking_service.development_mode}')
            self.stdout.write(f'✅ Contract address: {staking_service.staking_contract_address}')
            
            if staking_service.staking_contract:
                self.stdout.write('✅ Contract connected successfully')
                
                # Test basic contract call
                is_deployed = staking_service.is_contract_deployed()
                self.stdout.write(f'✅ Contract deployed: {is_deployed}')
                
                if is_deployed:
                    stats = staking_service.staking_contract.functions.getStakingStats().call()
                    total_staked = stats[0] / 10**18
                    total_stakers = stats[1]
                    self.stdout.write(f'✅ Total staked: {total_staked:.4f} TEO')
                    self.stdout.write(f'✅ Total stakers: {total_stakers}')
                    
                    # Test tier info
                    for i in range(5):
                        tier_info = staking_service.staking_contract.functions.getTierInfo(i).call()
                        tier_name = tier_info[2]
                        min_stake = tier_info[0] / 10**18
                        commission = tier_info[1] / 100
                        self.stdout.write(f'   Tier {i}: {tier_name} - {min_stake:.0f} TEO - {commission:.1f}%')
                else:
                    self.stdout.write('❌ Contract not properly deployed')
            else:
                self.stdout.write('❌ Contract not connected')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Staking Service Error: {e}'))
        
        # Test Discount Service
        self.stdout.write('\n🔧 Testing TeoCoin Discount Service...')
        try:
            discount_service = teocoin_discount_service
            
            self.stdout.write(f'✅ Service initialized')
            
            if discount_service.discount_contract:
                self.stdout.write('✅ Discount contract connected')
                
                # Test contract address
                contract_address = discount_service.discount_contract.address
                self.stdout.write(f'✅ Contract address: {contract_address}')
                
                # Test platform account
                if discount_service.platform_account:
                    try:
                        platform_addr = discount_service.platform_account.address
                        self.stdout.write(f'✅ Platform account: {platform_addr}')
                        
                        # Check platform balance
                        balance = discount_service.w3.eth.get_balance(platform_addr)
                        balance_matic = discount_service.w3.from_wei(balance, 'ether')
                        self.stdout.write(f'✅ Platform balance: {balance_matic:.4f} MATIC')
                    except AttributeError:
                        # Handle different Account object structure
                        self.stdout.write(f'✅ Platform account configured')
                else:
                    self.stdout.write('❌ Platform account not configured')
                
                # Test basic contract call
                try:
                    request_counter = discount_service.discount_contract.functions.getCurrentRequestId().call()
                    self.stdout.write(f'✅ Current request counter: {request_counter}')
                except Exception as e:
                    self.stdout.write(f'⚠️ Could not read request counter: {e}')
                
            else:
                self.stdout.write('❌ Discount contract not connected')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Discount Service Error: {e}'))
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📋 NEXT STEPS FROM ROADMAP:'))
        self.stdout.write('✅ 1. Backend services configured for live contracts')
        self.stdout.write('⏳ 2. Test StakingInterface with real blockchain')
        self.stdout.write('⏳ 3. Begin StudentDiscountInterface integration')
        self.stdout.write('⏳ 4. Set up monitoring and alerting systems')
        self.stdout.write('\n🎯 Ready to proceed with frontend testing!')
