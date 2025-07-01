"""
TeoCoin Staking Service

This service handles all staking-related operations including:
- Staking/unstaking TEO tokens
- Tier management and commission rate updates
- User staking information queries
- Integration with the platform's commission system
"""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from web3 import Web3
from web3.exceptions import ContractLogicError
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from users.models import User

# Import blockchain configuration
from blockchain.blockchain import TeoCoinService
from .staking_config import load_contract_config, TIER_CONFIG

logger = logging.getLogger(__name__)

class TeoCoinStakingService:
    """Service for managing TeoCoin staking operations"""
    
    # Staking tier definitions - adjusted for 10,000 TEO total supply
    TIER_CONFIG = TIER_CONFIG
    
    def __init__(self):
        self.teo_service = TeoCoinService()
        self.web3 = self.teo_service.w3  # Use w3 instead of web3
        
        # Load contract configuration
        contract_config = load_contract_config()
        self.staking_contract_address = contract_config['address']
        self.staking_abi = contract_config['abi']
        self.development_mode = contract_config['development_mode']
        
        # Initialize contract if deployed
        if self.staking_contract_address and self.staking_abi:
            self.staking_contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(self.staking_contract_address),
                abi=self.staking_abi
            )
            logger.info(f"Staking contract initialized at: {self.staking_contract_address}")
        else:
            self.staking_contract = None
            logger.warning("Staking contract not deployed yet - using development mode")
    
    def validate_supply_constraints(self) -> Dict:
        """
        Validate that staking tiers are realistic given current TEO supply
        Returns analysis of maximum possible stakers per tier
        """
        try:
            total_supply = self.teo_service.get_total_supply()
            total_supply_teo = total_supply / 10**18
            
            analysis = {
                'total_supply_teo': total_supply_teo,
                'tier_analysis': {},
                'warnings': []
            }
            
            for tier_idx, tier_config in self.TIER_CONFIG.items():
                min_stake = tier_config['min_stake']
                if min_stake > 0:
                    max_stakers = int(total_supply_teo // min_stake)
                    analysis['tier_analysis'][tier_config['name']] = {
                        'min_stake': min_stake,
                        'max_possible_stakers': max_stakers,
                        'commission_rate': f"{tier_config['commission_rate'] / 100}%"
                    }
                    
                    if max_stakers < 5:
                        analysis['warnings'].append(
                            f"{tier_config['name']} tier ({min_stake} TEO) allows max {max_stakers} stakers"
                        )
                        
            return analysis
            
        except Exception as e:
            logger.error(f"Supply validation error: {e}")
            return {'error': str(e)}

    # ========== TIER MANAGEMENT ==========
    
    def get_tier_info(self, tier_index: int) -> Dict:
        """Get information about a specific staking tier"""
        try:
            if not self.staking_contract:
                raise Exception("Staking contract not initialized")
            
            tier_info = self.staking_contract.functions.getTierInfo(tier_index).call()
            
            return {
                'tier_index': tier_index,
                'required_amount': tier_info[0],
                'required_amount_formatted': self.web3.from_wei(tier_info[0], 'ether'),
                'commission_rate': tier_info[1],
                'commission_percentage': tier_info[1] / 100,  # Convert basis points to percentage
                'tier_name': tier_info[2],
                'teacher_earnings_percentage': 100 - (tier_info[1] / 100)
            }
        except Exception as e:
            logger.error(f"Error getting tier info for tier {tier_index}: {e}")
            raise
    
    def get_all_tiers(self) -> List[Dict]:
        """Get information about all staking tiers"""
        tiers = []
        for i in range(5):  # Bronze (0) to Diamond (4)
            try:
                tier_info = self.get_tier_info(i)
                tiers.append(tier_info)
            except Exception as e:
                logger.error(f"Error getting tier {i}: {e}")
                break
        return tiers
    
    # ========== USER STAKING OPERATIONS ==========
    
    def get_user_staking_info(self, user_address: str) -> Dict:
        """Get complete staking information for a user"""
        try:
            if not self.staking_contract:
                raise Exception("Staking contract not initialized")
            
            # Get user staking info from contract
            staking_info = self.staking_contract.functions.getUserStakingInfo(user_address).call()
            
            amount = staking_info[0]
            tier = staking_info[1]
            staking_time = staking_info[2]
            active = staking_info[3]
            tier_name = staking_info[4]
            commission_rate = staking_info[5]
            
            # Calculate additional information
            result = {
                'address': user_address,
                'staked_amount': amount,
                'staked_amount_formatted': float(self.web3.from_wei(amount, 'ether')),
                'current_tier': tier,
                'tier_name': tier_name,
                'commission_rate': commission_rate,
                'commission_percentage': commission_rate / 100,
                'teacher_earnings_percentage': 100 - (commission_rate / 100),
                'staking_time': staking_time,
                'is_active': active
            }
            
            # Add next tier information if not at max tier
            if tier < 4:  # Not Diamond tier
                next_tier_info = self.get_tier_info(tier + 1)
                additional_teo_needed = max(0, next_tier_info['required_amount'] - amount)
                result.update({
                    'next_tier': {
                        'tier_index': tier + 1,
                        'tier_name': next_tier_info['tier_name'],
                        'required_amount': next_tier_info['required_amount'],
                        'additional_teo_needed': additional_teo_needed,
                        'additional_teo_needed_formatted': float(self.web3.from_wei(additional_teo_needed, 'ether')),
                        'commission_percentage': next_tier_info['commission_percentage']
                    }
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting staking info for {user_address}: {e}")
            raise
    
    def stake_teo(self, user_address: str, amount_teo: float, private_key: str) -> Dict:
        """
        Stake TEO tokens for a user
        
        Args:
            user_address: User's wallet address
            amount_teo: Amount of TEO to stake (in TEO units, not wei)
            private_key: User's private key for signing transaction
            
        Returns:
            Dict with transaction information and new staking status
        """
        try:
            if not self.staking_contract:
                raise Exception("Staking contract not initialized")
            
            # Convert TEO to wei
            amount_wei = self.web3.to_wei(amount_teo, 'ether')
            
            # Check user's TEO balance
            current_balance = self.teo_service.get_balance(user_address)
            if current_balance < amount_wei:
                raise Exception(f"Insufficient TEO balance. Required: {amount_teo}, Available: {self.web3.from_wei(current_balance, 'ether')}")
            
            # Check allowance (user needs to approve staking contract first)
            allowance = self.teo_service.teocoin_contract.functions.allowance(
                user_address, 
                self.staking_contract_address
            ).call()
            
            if allowance < amount_wei:
                raise Exception(f"Insufficient allowance. Please approve staking contract to spend {amount_teo} TEO")
            
            # Build staking transaction
            function_call = self.staking_contract.functions.stake(amount_wei)
            
            # Estimate gas
            gas_estimate = function_call.estimate_gas({'from': user_address})
            
            # Build transaction
            transaction = function_call.build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': int(gas_estimate * 1.2),
                'gasPrice': self.web3.to_wei('30', 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(user_address),
            })
            
            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if tx_receipt.status != 1:
                raise Exception("Staking transaction failed")
            
            # Get updated staking info
            updated_info = self.get_user_staking_info(user_address)
            
            # Clear cache
            self._clear_user_cache(user_address)
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'gas_used': tx_receipt.gasUsed,
                'staked_amount': amount_teo,
                'new_total_staked': updated_info['staked_amount_formatted'],
                'new_tier': updated_info['tier_name'],
                'new_commission_rate': updated_info['commission_percentage'],
                'staking_info': updated_info
            }
            
        except Exception as e:
            logger.error(f"Error staking TEO for {user_address}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def unstake_teo(self, user_address: str, amount_teo: float, private_key: str) -> Dict:
        """
        Unstake TEO tokens for a user
        
        Args:
            user_address: User's wallet address
            amount_teo: Amount of TEO to unstake (in TEO units, not wei)
            private_key: User's private key for signing transaction
            
        Returns:
            Dict with transaction information and new staking status
        """
        try:
            if not self.staking_contract:
                raise Exception("Staking contract not initialized")
            
            # Convert TEO to wei
            amount_wei = self.web3.to_wei(amount_teo, 'ether')
            
            # Check user's staked amount
            staking_info = self.get_user_staking_info(user_address)
            if not staking_info['is_active']:
                raise Exception("No active stake found")
            
            if staking_info['staked_amount'] < amount_wei:
                raise Exception(f"Insufficient staked amount. Available: {staking_info['staked_amount_formatted']}")
            
            # Build unstaking transaction
            function_call = self.staking_contract.functions.unstake(amount_wei)
            
            # Estimate gas
            gas_estimate = function_call.estimate_gas({'from': user_address})
            
            # Build transaction
            transaction = function_call.build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': int(gas_estimate * 1.2),
                'gasPrice': self.web3.to_wei('30', 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(user_address),
            })
            
            # Sign and send transaction
            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if tx_receipt.status != 1:
                raise Exception("Unstaking transaction failed")
            
            # Get updated staking info
            updated_info = self.get_user_staking_info(user_address)
            
            # Clear cache
            self._clear_user_cache(user_address)
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'gas_used': tx_receipt.gasUsed,
                'unstaked_amount': amount_teo,
                'new_total_staked': updated_info['staked_amount_formatted'],
                'new_tier': updated_info['tier_name'],
                'new_commission_rate': updated_info['commission_percentage'],
                'staking_info': updated_info
            }
            
        except Exception as e:
            logger.error(f"Error unstaking TEO for {user_address}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== TEACHER COMMISSION INTEGRATION ==========
    
    def update_teacher_commission_rate(self, user_id: int) -> Dict:
        """
        Update teacher's commission rate based on their staking tier
        
        Args:
            user_id: User ID in the platform database
            
        Returns:
            Dict with update information
        """
        try:
            # Get user from database
            user = User.objects.get(id=user_id)
            
            if not hasattr(user, 'teacher_profile'):
                raise Exception("User is not a teacher")
            
            # Get user's wallet address
            if not hasattr(user, 'polygon_address') or not user.polygon_address:
                raise Exception("User doesn't have a wallet address")
            
            # Get staking information
            staking_info = self.get_user_staking_info(user.polygon_address)
            
            # Update teacher profile with new commission rate
            with transaction.atomic():
                teacher_profile = user.teacher_profile
                old_commission_rate = teacher_profile.commission_rate
                new_commission_rate = staking_info['commission_percentage']
                
                teacher_profile.commission_rate = new_commission_rate
                teacher_profile.staking_tier = staking_info['current_tier']
                teacher_profile.staked_teo_amount = staking_info['staked_amount_formatted']
                teacher_profile.save()
                
                # Log the change
                logger.info(f"Updated commission rate for teacher {user.email}: {old_commission_rate}% -> {new_commission_rate}%")
                
                return {
                    'success': True,
                    'user_id': user_id,
                    'old_commission_rate': old_commission_rate,
                    'new_commission_rate': new_commission_rate,
                    'tier_name': staking_info['tier_name'],
                    'staked_amount': staking_info['staked_amount_formatted']
                }
                
        except Exception as e:
            logger.error(f"Error updating commission rate for user {user_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # ========== PUBLIC API METHODS ==========
    
    def get_user_staking_info(self, wallet_address: str) -> Dict:
        """Get complete user staking information"""
        try:
            if not self.staking_contract:
                raise Exception("Staking contract not initialized")
            
            # Get user staking info from contract
            result = self.staking_contract.functions.getUserStakingInfo(wallet_address).call()
            amount, tier, staking_time, active, tier_name, commission_rate = result
            
            # Convert wei to TEO
            amount_teo = self.web3.from_wei(amount, 'ether')
            
            return {
                'wallet_address': wallet_address,
                'staked_amount': float(amount_teo),
                'tier': tier,
                'tier_name': tier_name,
                'commission_rate': commission_rate,
                'commission_percentage': commission_rate / 100,
                'staking_time': staking_time,
                'active': active,
                'last_updated': cache.get(f'staking_last_updated_{wallet_address}', None)
            }
            
        except Exception as e:
            logger.error(f"Error getting user staking info: {e}")
            return {
                'wallet_address': wallet_address,
                'staked_amount': 0,
                'tier': 0,
                'tier_name': 'Bronze',
                'commission_rate': 2500,
                'commission_percentage': 25.0,
                'staking_time': 0,
                'active': False,
                'error': str(e)
            }
    
    def get_platform_stats(self) -> Dict:
        """Get platform-wide staking statistics"""
        try:
            if not self.staking_contract:
                raise Exception("Staking contract not initialized")
            
            stats = self.staking_contract.functions.getStakingStats().call()
            total_staked_wei, total_stakers = stats
            
            # Convert wei to TEO
            total_staked_teo = self.web3.from_wei(total_staked_wei, 'ether')
            
            return {
                'total_staked': float(total_staked_teo),
                'total_stakers': total_stakers,
                'average_stake': float(total_staked_teo) / max(total_stakers, 1),
                'utilization_percentage': (float(total_staked_teo) / 10000) * 100  # 10K TEO supply
            }
            
        except Exception as e:
            logger.error(f"Error getting platform stats: {e}")
            return {
                'total_staked': 0,
                'total_stakers': 0,
                'average_stake': 0,
                'utilization_percentage': 0,
                'error': str(e)
            }
    
    def stake_tokens(self, wallet_address: str, amount: float) -> Dict:
        """Stake TEO tokens for a user"""
        try:
            if not self.staking_contract:
                raise Exception("Staking contract not initialized")
            
            # Convert TEO to wei
            amount_wei = self.web3.to_wei(amount, 'ether')
            
            # Check user's TEO balance first
            teo_balance = self.teo_service.get_balance(wallet_address)
            if teo_balance < amount:
                return {
                    'success': False,
                    'error': f'Insufficient TEO balance. Required: {amount}, Available: {teo_balance}'
                }
            
            # Check if user has approved the staking contract to spend their tokens
            # Note: This would require user interaction in frontend
            logger.info(f"Staking {amount} TEO for user {wallet_address}")
            
            # For now, return a success simulation since actual staking requires user wallet interaction
            # In production, this would trigger a MetaMask transaction
            
            # Get current staking info to calculate new tier
            current_info = self.get_user_staking_info(wallet_address)
            new_total = current_info['staked_amount'] + amount
            new_tier = self.calculate_tier(new_total)
            
            # Cache the pending transaction
            cache.set(f'pending_stake_{wallet_address}', {
                'amount': amount,
                'timestamp': cache.time.time()
            }, 300)  # 5 minutes
            
            return {
                'success': True,
                'transaction_hash': f'0x{"0" * 64}',  # Placeholder - would be real tx hash
                'new_tier': new_tier,
                'new_total_staked': new_total,
                'requires_wallet_approval': True,
                'message': 'Transaction prepared. Please approve in your wallet.'
            }
            
        except Exception as e:
            logger.error(f"Error staking tokens: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def unstake_tokens(self, wallet_address: str, amount: float) -> Dict:
        """Unstake TEO tokens for a user"""
        try:
            if not self.staking_contract:
                raise Exception("Staking contract not initialized")
            
            # Get current staking info
            current_info = self.get_user_staking_info(wallet_address)
            
            if not current_info['active']:
                return {
                    'success': False,
                    'error': 'No active stake found'
                }
            
            if current_info['staked_amount'] < amount:
                return {
                    'success': False,
                    'error': f'Insufficient staked amount. Staked: {current_info["staked_amount"]}, Requested: {amount}'
                }
            
            # Calculate new totals
            new_total = current_info['staked_amount'] - amount
            new_tier = self.calculate_tier(new_total)
            
            logger.info(f"Unstaking {amount} TEO for user {wallet_address}")
            
            # Cache the pending transaction
            cache.set(f'pending_unstake_{wallet_address}', {
                'amount': amount,
                'timestamp': cache.time.time()
            }, 300)  # 5 minutes
            
            return {
                'success': True,
                'transaction_hash': f'0x{"1" * 64}',  # Placeholder - would be real tx hash
                'new_tier': new_tier,
                'new_total_staked': new_total,
                'requires_wallet_approval': True,
                'message': 'Unstaking transaction prepared. Please approve in your wallet.'
            }
            
        except Exception as e:
            logger.error(f"Error unstaking tokens: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_tier(self, staked_amount: float) -> int:
        """Calculate tier based on staked amount"""
        for tier in range(4, -1, -1):  # Check from highest to lowest
            if staked_amount >= self.TIER_CONFIG[tier]['min_stake']:
                return tier
        return 0  # Bronze tier
    
    # ========== UTILITY FUNCTIONS ==========
    
    def _clear_user_cache(self, user_address: str):
        """Clear cached data for a user"""
        cache_keys = [
            f'staking_info_{user_address}',
            'staking_statistics'
        ]
        cache.delete_many(cache_keys)
    
    def is_contract_deployed(self) -> bool:
        """Check if the staking contract is deployed and accessible"""
        try:
            if not self.staking_contract:
                return False
            
            # Try to call a read function
            self.staking_contract.functions.totalStaked().call()
            return True
        except:
            return False
    
    def prepare_approval_transaction(self, user_address: str, amount_teo: float) -> Dict:
        """
        Prepare an approval transaction for staking
        
        This allows the frontend to request user approval before staking
        """
        try:
            amount_wei = self.web3.to_wei(amount_teo, 'ether')
            
            # Build approval transaction for TEO contract
            function_call = self.teo_service.teocoin_contract.functions.approve(
                self.staking_contract_address,
                amount_wei
            )
            
            # Estimate gas
            gas_estimate = function_call.estimate_gas({'from': user_address})
            
            # Build transaction data
            transaction_data = function_call.build_transaction({
                'chainId': self.web3.eth.chain_id,
                'gas': int(gas_estimate * 1.2),
                'gasPrice': self.web3.to_wei('30', 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(user_address),
            })
            
            return {
                'success': True,
                'transaction_data': transaction_data,
                'gas_estimate': gas_estimate,
                'amount_teo': amount_teo,
                'spender': self.staking_contract_address
            }
            
        except Exception as e:
            logger.error(f"Error preparing approval transaction: {e}")
            return {
                'success': False,
                'error': str(e)
            }
