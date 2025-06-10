"""
TeoCoin Blockchain Service

Manages integration with the TeoCoin smart contract on Polygon Amoy testnet.
Provides functionality for token operations including minting, transfers, and balance queries.
"""

import os
from decimal import Decimal
from typing import Optional, Dict, Any
from web3 import Web3
from django.conf import settings
import json
import logging
from .teocoin_abi import TEOCOIN_ABI

logger = logging.getLogger(__name__)


class TeoCoinService:
    """
    Service class for managing TeoCoin contract operations.
    
    Provides methods for interacting with the TeoCoin smart contract including:
    - Balance queries
    - Token minting (admin only)
    - Token transfers
    - Transaction management
    """
    
    def __init__(self):
        """
        Initialize the TeoCoin service with Web3 connection and contract setup.
        
        Raises:
            ConnectionError: If unable to connect to the blockchain network
            ValueError: If required configuration is missing
        """
        # Web3 Configuration - Load from environment variables for security
        self.rpc_url = getattr(settings, 'POLYGON_AMOY_RPC_URL', 'https://rpc-amoy.polygon.technology/')
        self.contract_address = getattr(settings, 'TEOCOIN_CONTRACT_ADDRESS', None)
        self.admin_private_key = getattr(settings, 'ADMIN_PRIVATE_KEY', None)
        
        # Validate required configuration
        if not self.contract_address:
            raise ValueError("TEOCOIN_CONTRACT_ADDRESS must be set in environment variables")
        
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add middleware for PoA chains (Polygon Amoy)
        try:
            from web3.middleware import ExtraDataToPOAMiddleware
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        except ImportError:
            # Fallback for older Web3.py versions
            logger.warning("Could not load PoA middleware - using fallback")
        
        # Verify blockchain connection
        if not self.w3.is_connected():
            logger.error("Unable to connect to Polygon Amoy network")
            raise ConnectionError("Blockchain connection failed")
        
        # Initialize contract instance
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=TEOCOIN_ABI
        )
        
        logger.info(f"TeoCoinService initialized - Contract: {self.contract_address}")
    
    def get_balance(self, wallet_address: str) -> Decimal:
        """
        Get TeoCoin balance for a wallet address.
        
        Args:
            wallet_address: The wallet address to check balance for
            
        Returns:
            Decimal: Balance in TEO tokens (converted from wei)
        """
        try:
            checksum_address = Web3.to_checksum_address(wallet_address)
            balance_wei = self.contract.functions.balanceOf(checksum_address).call()
            balance_teo = Web3.from_wei(balance_wei, 'ether')
            return Decimal(str(balance_teo))
        except Exception as e:
            logger.error(f"Error retrieving balance for {wallet_address}: {e}")
            return Decimal('0')
    
    def mint_tokens(self, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Mint TeoCoin tokens to a specific address (admin only).
        
        Args:
            to_address: Recipient wallet address
            amount: Amount of TEO tokens to mint
            
        Returns:
            Optional[str]: Transaction hash if successful, None if failed
        """
        if not self.admin_private_key:
            logger.error("Admin private key not configured - minting disabled")
            return None
            
        try:
            # Convert amount to wei
            amount_wei = Web3.to_wei(amount, 'ether')
            
            # Get admin account
            admin_account = self.w3.eth.account.from_key(self.admin_private_key)
            
            # Build transaction
            tx = self.contract.functions.mint(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                'from': admin_account.address,
                'nonce': self.w3.eth.get_transaction_count(admin_account.address),
                'gasPrice': self._get_optimized_gas_price()
            })
            
            # Estimate gas and add buffer
            estimated_gas = self.w3.eth.estimate_gas(tx)
            tx['gas'] = int(estimated_gas * 1.2)  # 20% buffer
            
            # Sign and send transaction
            signed_txn = admin_account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"Minted {amount} TEO to {to_address} - TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error minting {amount} TEO to {to_address}: {e}")
            return None
    
    def transfer_tokens(self, from_private_key: str, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Transfer TeoCoin tokens between addresses.
        
        Args:
            from_private_key: Private key of sender wallet
            to_address: Recipient wallet address
            amount: Amount of TEO tokens to transfer
            
        Returns:
            Optional[str]: Transaction hash if successful, None if failed
        """
        try:
            # Convert amount to wei
            amount_wei = Web3.to_wei(amount, 'ether')
            
            # Get sender account
            from_account = self.w3.eth.account.from_key(from_private_key)
            
            # Build transaction
            tx = self.contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                'from': from_account.address,
                'nonce': self.w3.eth.get_transaction_count(from_account.address),
                'gasPrice': self._get_optimized_gas_price()
            })
            
            # Estimate gas and add buffer
            estimated_gas = self.w3.eth.estimate_gas(tx)
            tx['gas'] = int(estimated_gas * 1.2)  # 20% buffer
            
            # Sign and send transaction
            signed_txn = from_account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"Transferred {amount} TEO from {from_account.address} to {to_address} - TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error transferring {amount} TEO: {e}")
            return None
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get basic token information.
        
        Returns:
            Dict: Dictionary with name, symbol, decimals, etc.
        """
        try:
            return {
                'name': self.contract.functions.name().call(),
                'symbol': self.contract.functions.symbol().call(),
                'decimals': self.contract.functions.decimals().call(),
                'contract_address': self.contract_address,
                'total_supply': str(Web3.from_wei(self.contract.functions.totalSupply().call(), 'ether'))
            }
        except Exception as e:
            logger.error(f"Error retrieving token info: {e}")
            return {}
    
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict]:
        """
        Get transaction receipt details.
        
        Args:
            tx_hash: Transaction hash (string or bytes)
            
        Returns:
            Optional[Dict]: Transaction receipt details if found
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                'status': receipt['status'],
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'transaction_hash': receipt['transactionHash'].hex(),
                'from': receipt['from'],
                'to': receipt['to']
            }
        except Exception as e:
            logger.error(f"Error retrieving receipt for {tx_hash}: {e}")
            return None
    
    def validate_address(self, address: str) -> bool:
        """
        Validate an Ethereum address.
        
        Args:
            address: Address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            Web3.to_checksum_address(address)
            return True
        except ValueError:
            return False
    
    def _get_optimized_gas_price(self) -> int:
        """
        Get optimized gas price for Polygon Amoy testnet.
        
        Returns:
            int: Gas price in wei
        """
        try:
            # Get current network gas price
            gas_price = self.w3.eth.gas_price
            
            # Polygon Amoy minimum requirement is 25 Gwei
            min_gas_price = self.w3.to_wei('25', 'gwei')
            if gas_price < min_gas_price:
                gas_price = min_gas_price
            
            # Cap maximum to avoid excessive costs in testnet
            max_gas_price = self.w3.to_wei('50', 'gwei')
            if gas_price > max_gas_price:
                gas_price = max_gas_price
                
            return gas_price
        except Exception:
            # Fallback to 25 Gwei for Polygon Amoy testnet
            return self.w3.to_wei('25', 'gwei')


# Global service instance
teocoin_service = TeoCoinService()
