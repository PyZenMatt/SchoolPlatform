"""
Gas-Free TeoCoin Staking Service
Implements signature-based staking operations where platform pays gas fees.
"""
import logging
import json
from decimal import Decimal
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct

from .base import TransactionalService
from .exceptions import (
    TeoArtServiceException as ServiceException,
    InvalidAmountError,
    BlockchainTransactionError,
    TokenTransferError
)

logger = logging.getLogger(__name__)


class GasFreeStakingService(TransactionalService):
    """
    Service for handling gas-free staking operations using signature-based authentication.
    Platform pays all MATIC gas fees, users only sign messages with TEO tokens.
    """
    
    def __init__(self):
        super().__init__()
        
        # Web3 Configuration
        self.rpc_url = getattr(settings, 'POLYGON_RPC_URL', 'https://rpc-amoy.polygon.technology/')
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add middleware for PoA chains (Polygon Amoy)
        try:
            from web3.middleware import geth_poa_middleware
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except ImportError:
            logger.warning("Could not load PoA middleware")
        
        # Verify blockchain connection
        if not self.w3.is_connected():
            raise ServiceException("Blockchain connection failed")
        
        # Contract addresses and keys
        self.gas_free_contract_address = getattr(settings, 'TEOCOIN_STAKING_GAS_FREE_CONTRACT_ADDRESS', None)
        self.teo_contract_address = getattr(settings, 'TEOCOIN_CONTRACT_ADDRESS', None)
        self.platform_account = getattr(settings, 'PLATFORM_ACCOUNT', None)
        self.platform_private_key = getattr(settings, 'PLATFORM_PRIVATE_KEY', None)
        
        # Validate required configuration
        if not self.gas_free_contract_address:
            raise ServiceException("TEOCOIN_STAKING_GAS_FREE_CONTRACT must be set")
        if not self.teo_contract_address:
            raise ServiceException("TEOCOIN_CONTRACT_ADDRESS must be set")
        if not self.platform_account:
            raise ServiceException("PLATFORM_ACCOUNT must be set")
        if not self.platform_private_key:
            raise ServiceException("PLATFORM_PRIVATE_KEY must be set")
        
        # Load contract ABIs
        self.gas_free_contract = self._load_gas_free_staking_contract()
        self.teo_contract = self._load_teo_contract()
        
    def _load_gas_free_staking_contract(self):
        """Load the gas-free staking contract instance."""
        # Simplified ABI for gas-free staking contract
        staking_abi = [
            {
                "inputs": [
                    {"name": "user", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "signature", "type": "bytes"}
                ],
                "name": "stakeTokensGasFree",
                "outputs": [],
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "user", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "signature", "type": "bytes"}
                ],
                "name": "unstakeTokensGasFree",
                "outputs": [],
                "type": "function"
            },
            {
                "inputs": [{"name": "user", "type": "address"}],
                "name": "getStakeInfo",
                "outputs": [
                    {"name": "amount", "type": "uint256"},
                    {"name": "tier", "type": "uint256"},
                    {"name": "stakingTime", "type": "uint256"},
                    {"name": "lastRestrictedAction", "type": "uint256"}
                ],
                "type": "function"
            },
            {
                "inputs": [{"name": "user", "type": "address"}],
                "name": "canPerformAction",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "user", "type": "address"},
                    {"indexed": False, "name": "amount", "type": "uint256"},
                    {"indexed": False, "name": "tier", "type": "uint256"}
                ],
                "name": "TokensStaked",
                "type": "event"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "user", "type": "address"},
                    {"indexed": False, "name": "amount", "type": "uint256"}
                ],
                "name": "TokensUnstaked",
                "type": "event"
            }
        ]
        
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(self.gas_free_contract_address),
            abi=staking_abi
        )
    
    def _load_teo_contract(self):
        """Load the TEO token contract instance."""
        teo_abi = [
            {
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(self.teo_contract_address),
            abi=teo_abi
        )
    
    def create_stake_signature(
        self, 
        user_address: str, 
        teo_amount: int,
        nonce: Optional[int] = None
    ) -> Dict:
        """
        Create a signature for gas-free staking operation.
        
        Args:
            user_address: User's wallet address
            teo_amount: Amount of TEO tokens to stake
            nonce: Optional nonce (uses timestamp if not provided)
            
        Returns:
            Dict with signature data and message hash
        """
        try:
            # Generate nonce if not provided
            if nonce is None:
                nonce = int(datetime.now().timestamp())
            
            # Validate inputs
            if not Web3.is_address(user_address):
                raise ServiceException("Invalid user address")
            
            if teo_amount <= 0:
                raise InvalidAmountError(float(teo_amount))
            
            # Check user's TEO balance
            balance = self.teo_contract.functions.balanceOf(
                Web3.to_checksum_address(user_address)
            ).call()
            
            if balance < teo_amount:
                raise ServiceException(
                    f"Insufficient TEO balance. Required: {teo_amount}, Available: {balance}"
                )
            
            # Check if user can perform staking action (anti-abuse)
            can_stake = self.gas_free_contract.functions.canPerformAction(
                Web3.to_checksum_address(user_address)
            ).call()
            
            if not can_stake:
                raise ServiceException("User cannot stake due to anti-abuse restrictions")
            
            # Create message hash for signing
            message_hash = Web3.solidity_keccak(
                ['address', 'uint256', 'uint256', 'string'],
                [user_address, teo_amount, nonce, 'stake']
            )
            
            # Cache signature data for validation
            cache_key = f"stake_signature_{user_address}_{teo_amount}_{nonce}"
            cache.set(cache_key, {
                'user_address': user_address,
                'teo_amount': teo_amount,
                'nonce': nonce,
                'action': 'stake',
                'message_hash': message_hash.hex(),
                'created_at': datetime.now().isoformat()
            }, timeout=3600)  # 1 hour expiry
            
            return {
                'message_hash': message_hash.hex(),
                'user_address': user_address,
                'teo_amount': teo_amount,
                'nonce': nonce,
                'action': 'stake',
                'contract_address': self.gas_free_contract_address,
                'instructions': {
                    'message': f"Sign this message to stake {teo_amount} TEO tokens",
                    'amount': f"{teo_amount} TEO tokens",
                    'gas_free': "Platform will pay all gas fees"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating stake signature: {str(e)}")
            raise ServiceException(f"Failed to create stake signature: {str(e)}")
    
    def create_unstake_signature(
        self, 
        user_address: str, 
        teo_amount: int,
        nonce: Optional[int] = None
    ) -> Dict:
        """
        Create a signature for gas-free unstaking operation.
        
        Args:
            user_address: User's wallet address
            teo_amount: Amount of TEO tokens to unstake
            nonce: Optional nonce (uses timestamp if not provided)
            
        Returns:
            Dict with signature data and message hash
        """
        try:
            # Generate nonce if not provided
            if nonce is None:
                nonce = int(datetime.now().timestamp())
            
            # Validate inputs
            if not Web3.is_address(user_address):
                raise ServiceException("Invalid user address")
            
            if teo_amount <= 0:
                raise InvalidAmountError(float(teo_amount))
            
            # Get user's staking info
            stake_info = self.gas_free_contract.functions.getStakeInfo(
                Web3.to_checksum_address(user_address)
            ).call()
            
            staked_amount = stake_info[0]
            if staked_amount < teo_amount:
                raise ServiceException(
                    f"Insufficient staked amount. Requested: {teo_amount}, Available: {staked_amount}"
                )
            
            # Check if user can perform unstaking action (anti-abuse)
            can_unstake = self.gas_free_contract.functions.canPerformAction(
                Web3.to_checksum_address(user_address)
            ).call()
            
            if not can_unstake:
                raise ServiceException("User cannot unstake due to anti-abuse restrictions")
            
            # Create message hash for signing
            message_hash = Web3.solidity_keccak(
                ['address', 'uint256', 'uint256', 'string'],
                [user_address, teo_amount, nonce, 'unstake']
            )
            
            # Cache signature data for validation
            cache_key = f"unstake_signature_{user_address}_{teo_amount}_{nonce}"
            cache.set(cache_key, {
                'user_address': user_address,
                'teo_amount': teo_amount,
                'nonce': nonce,
                'action': 'unstake',
                'message_hash': message_hash.hex(),
                'created_at': datetime.now().isoformat()
            }, timeout=3600)  # 1 hour expiry
            
            return {
                'message_hash': message_hash.hex(),
                'user_address': user_address,
                'teo_amount': teo_amount,
                'nonce': nonce,
                'action': 'unstake',
                'contract_address': self.gas_free_contract_address,
                'instructions': {
                    'message': f"Sign this message to unstake {teo_amount} TEO tokens",
                    'amount': f"{teo_amount} TEO tokens",
                    'gas_free': "Platform will pay all gas fees"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating unstake signature: {str(e)}")
            raise ServiceException(f"Failed to create unstake signature: {str(e)}")
    
    def execute_stake_request(
        self, 
        user_address: str, 
        signature: str, 
        teo_amount: int, 
        nonce: int
    ) -> Dict:
        """
        Execute gas-free staking request on blockchain.
        
        Args:
            user_address: User's wallet address
            signature: User's signature
            teo_amount: Amount of TEO tokens to stake
            nonce: Signature nonce
            
        Returns:
            Transaction result
        """
        try:
            # Validate signature
            self._validate_signature(user_address, signature, teo_amount, nonce, 'stake')
            
            # Check platform account balance
            if not self._check_platform_balance():
                raise ServiceException("Insufficient platform balance for gas fees")
            
            # Execute staking transaction
            return self._execute_transaction(
                self.gas_free_contract.functions.stakeTokensGasFree,
                [Web3.to_checksum_address(user_address), teo_amount, nonce, signature],
                'stake',
                user_address,
                teo_amount,
                signature
            )
            
        except Exception as e:
            logger.error(f"Error executing stake request: {str(e)}")
            raise ServiceException(f"Failed to execute stake request: {str(e)}")
    
    def execute_unstake_request(
        self, 
        user_address: str, 
        signature: str, 
        teo_amount: int, 
        nonce: int
    ) -> Dict:
        """
        Execute gas-free unstaking request on blockchain.
        
        Args:
            user_address: User's wallet address
            signature: User's signature
            teo_amount: Amount of TEO tokens to unstake
            nonce: Signature nonce
            
        Returns:
            Transaction result
        """
        try:
            # Validate signature
            self._validate_signature(user_address, signature, teo_amount, nonce, 'unstake')
            
            # Check platform account balance
            if not self._check_platform_balance():
                raise ServiceException("Insufficient platform balance for gas fees")
            
            # Execute unstaking transaction
            return self._execute_transaction(
                self.gas_free_contract.functions.unstakeTokensGasFree,
                [Web3.to_checksum_address(user_address), teo_amount, nonce, signature],
                'unstake',
                user_address,
                teo_amount,
                signature
            )
            
        except Exception as e:
            logger.error(f"Error executing unstake request: {str(e)}")
            raise ServiceException(f"Failed to execute unstake request: {str(e)}")
    
    def _validate_signature(
        self, 
        user_address: str, 
        signature: str, 
        teo_amount: int, 
        nonce: int,
        action: str
    ) -> bool:
        """Validate user's signature for staking operation."""
        try:
            # Recreate message hash
            message_hash = Web3.solidity_keccak(
                ['address', 'uint256', 'uint256', 'string'],
                [user_address, teo_amount, nonce, action]
            )
            
            # Recover signer address from signature
            message = encode_defunct(message_hash)
            recovered_address = Account.recover_message(message, signature=signature)
            
            # Validate signer matches user address
            if recovered_address.lower() != user_address.lower():
                raise BlockchainTransactionError("Signature does not match user address")
            
            # Check if signature was previously used
            signature_key = f"used_signature_{signature}"
            if cache.get(signature_key):
                raise BlockchainTransactionError("Signature already used")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating signature: {str(e)}")
            raise BlockchainTransactionError(f"Invalid signature: {str(e)}")
    
    def _check_platform_balance(self) -> bool:
        """Check if platform account has sufficient balance for gas fees."""
        try:
            platform_balance = self.w3.eth.get_balance(
                Web3.to_checksum_address(self.platform_account)
            )
            min_balance = self.w3.to_wei(0.01, 'ether')  # 0.01 MATIC minimum
            return platform_balance >= min_balance
        except Exception:
            return False
    
    def _execute_transaction(
        self,
        contract_function,
        args: list,
        action: str,
        user_address: str,
        teo_amount: int,
        signature: str
    ) -> Dict:
        """Execute blockchain transaction with platform account."""
        try:
            # Prepare transaction
            platform_account = Account.from_key(self.platform_private_key)
            
            # Build transaction
            transaction = contract_function(*args).build_transaction({
                'from': Web3.to_checksum_address(self.platform_account),
                'gas': 400000,  # Estimated gas limit for staking
                'gasPrice': self.w3.to_wei(30, 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(
                    Web3.to_checksum_address(self.platform_account)
                )
            })
            
            # Sign and send transaction
            signed_txn = platform_account.sign_transaction(transaction)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt['status'] == 0:
                raise TokenTransferError("Transaction failed")
            
            # Mark signature as used
            signature_key = f"used_signature_{signature}"
            cache.set(signature_key, True, timeout=86400)  # 24 hours
            
            # Log successful transaction
            logger.info(f"Gas-free {action} completed for user {user_address}: {teo_amount} TEO")
            
            return {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'user_address': user_address,
                'teo_amount': teo_amount,
                'action': action,
                'gas_cost': receipt['gasUsed'] * transaction['gasPrice'],
                'block_number': receipt['blockNumber'],
                'platform_paid_gas': True
            }
            
        except Exception as e:
            logger.error(f"Error executing {action} transaction: {str(e)}")
            raise ServiceException(f"Failed to execute {action} transaction: {str(e)}")
    
    def get_user_stake_info(self, user_address: str) -> Dict:
        """
        Get user's staking information.
        
        Args:
            user_address: User's wallet address
            
        Returns:
            User's staking details
        """
        try:
            stake_info = self.gas_free_contract.functions.getStakeInfo(
                Web3.to_checksum_address(user_address)
            ).call()
            
            can_perform_action = self.gas_free_contract.functions.canPerformAction(
                Web3.to_checksum_address(user_address)
            ).call()
            
            return {
                'user_address': user_address,
                'staked_amount': stake_info[0],
                'tier': stake_info[1],
                'staking_time': stake_info[2],
                'last_restricted_action': stake_info[3],
                'can_perform_action': can_perform_action,
                'is_gas_free': True
            }
            
        except Exception as e:
            logger.error(f"Error getting stake info: {str(e)}")
            raise ServiceException(f"Failed to get stake info: {str(e)}")
    
    def get_user_teo_balance(self, user_address: str) -> float:
        """
        Get user's TEO token balance.
        
        Args:
            user_address: User's wallet address
            
        Returns:
            TEO balance as float
        """
        try:
            # Get balance from TEO contract
            balance_wei = self.teo_contract.functions.balanceOf(
                Web3.to_checksum_address(user_address)
            ).call()
            
            # Convert from wei to TEO (assuming 18 decimals)
            balance_teo = Web3.from_wei(balance_wei, 'ether')
            
            return float(balance_teo)
            
        except Exception as e:
            logger.error(f"Error getting TEO balance: {str(e)}")
            # Return 0 if we can't get balance to avoid breaking the flow
            return 0.0
    
    def estimate_staking_gas_cost(self) -> Dict:
        """
        Estimate gas costs for staking operations.
        
        Returns:
            Gas cost estimates in MATIC and USD
        """
        try:
            # Current gas price
            gas_price = self.w3.eth.gas_price
            
            # Estimated gas usage
            stake_gas = 350000  # Estimated gas for staking
            unstake_gas = 300000  # Estimated gas for unstaking
            
            # Calculate costs
            stake_cost_wei = stake_gas * gas_price
            unstake_cost_wei = unstake_gas * gas_price
            
            stake_cost_matic = self.w3.from_wei(stake_cost_wei, 'ether')
            unstake_cost_matic = self.w3.from_wei(unstake_cost_wei, 'ether')
            
            # Estimate USD cost (MATIC ~$0.50)
            matic_usd_rate = 0.50
            stake_cost_usd = float(stake_cost_matic) * matic_usd_rate
            unstake_cost_usd = float(unstake_cost_matic) * matic_usd_rate
            
            return {
                'gas_price_gwei': self.w3.from_wei(gas_price, 'gwei'),
                'stake_operation': {
                    'gas_limit': stake_gas,
                    'cost_matic': float(stake_cost_matic),
                    'cost_usd': stake_cost_usd
                },
                'unstake_operation': {
                    'gas_limit': unstake_gas,
                    'cost_matic': float(unstake_cost_matic),
                    'cost_usd': unstake_cost_usd
                },
                'daily_estimates': {
                    '10_operations': (stake_cost_usd + unstake_cost_usd) * 5,
                    '50_operations': (stake_cost_usd + unstake_cost_usd) * 25,
                    '100_operations': (stake_cost_usd + unstake_cost_usd) * 50
                }
            }
            
        except Exception as e:
            logger.error(f"Error estimating gas costs: {str(e)}")
            return {
                'error': str(e),
                'fallback_estimate': {
                    'cost_usd_per_operation': 0.003,
                    'daily_100_operations': 0.30
                }
            }
