"""
Phase 2 Blockchain Services for TeoCoin Withdrawal System

Clean, modern implementation using the existing TeoCoin2 contract.
This replaces the complex legacy blockchain.py file with focused functionality.
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from web3 import Web3
from django.conf import settings
import json

logger = logging.getLogger(__name__)


class TeoCoinBlockchainService:
    """
    Clean blockchain service for TeoCoin withdrawal operations.
    
    Provides minimal, focused functionality for:
    - Minting tokens to user wallets (withdrawals from DB balance)
    - Balance queries
    - Transaction verification
    """
    
    def __init__(self):
        """Initialize with the existing TeoCoin2 contract."""
        # Load contract configuration
        self.rpc_url = getattr(settings, 'POLYGON_AMOY_RPC_URL', 'https://rpc-amoy.polygon.technology/')
        self.contract_address = getattr(settings, 'TEOCOIN_CONTRACT_ADDRESS', '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8')
        self.admin_private_key = getattr(settings, 'ADMIN_PRIVATE_KEY', None)
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Verify connection
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Polygon Amoy network")
        
        # Load contract ABI from the existing file
        import json
        import os
        
        abi_path = os.path.join(os.path.dirname(__file__), 'abi', 'teoCoin2_ABI.json')
        with open(abi_path, 'r') as f:
            TEOCOIN2_ABI = json.load(f)
        
        # Initialize contract
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=TEOCOIN2_ABI
        )
        
        logger.info(f"TeoCoin2 service initialized - Contract: {self.contract_address}")
    
    def mint_tokens_to_address(self, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Mint TeoCoin tokens to a specific address using the existing contract.
        
        Args:
            to_address: Recipient wallet address
            amount: Amount of TEO tokens to mint
            
        Returns:
            Transaction hash if successful, None if failed
        """
        if not self.admin_private_key:
            logger.error("Admin private key not configured")
            return None
        
        try:
            # Get admin account
            admin_account = self.w3.eth.account.from_key(self.admin_private_key)
            
            # Convert amount to wei (18 decimals)
            amount_wei = Web3.to_wei(amount, 'ether')
            
            # Prepare transaction using mintTo function
            checksum_to = Web3.to_checksum_address(to_address)
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            
            # Get nonce
            nonce = self.w3.eth.get_transaction_count(admin_account.address)
            
            # Build transaction
            transaction = self.contract.functions.mintTo(
                checksum_to,
                amount_wei
            ).build_transaction({
                'from': admin_account.address,
                'gas': 100000,  # Standard gas limit for minting
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(transaction, self.admin_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            logger.info(f"Minted {amount} TEO to {to_address} - TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error minting {amount} TEO to {to_address}: {e}")
            return None
    
    def get_balance(self, wallet_address: str) -> Decimal:
        """
        Get TeoCoin balance for a wallet address.
        
        Args:
            wallet_address: The wallet address to check
            
        Returns:
            Balance in TEO tokens
        """
        try:
            checksum_address = Web3.to_checksum_address(wallet_address)
            balance_wei = self.contract.functions.balanceOf(checksum_address).call()
            balance_teo = Web3.from_wei(balance_wei, 'ether')
            return Decimal(str(balance_teo))
        except Exception as e:
            logger.error(f"Error getting balance for {wallet_address}: {e}")
            return Decimal('0')
    
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction receipt for verification.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction receipt dict or None
        """
        try:
            # Web3.py expects the hash, ignore typing for compatibility
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)  # type: ignore
            return {
                'status': receipt['status'],
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'transaction_hash': receipt['transactionHash'].hex(),
                'from': receipt['from'],
                'to': receipt['to']
            }
        except Exception as e:
            logger.error(f"Error getting receipt for {tx_hash}: {e}")
            return None
    
    def validate_address(self, address: str) -> bool:
        """
        Validate an Ethereum address format.
        
        Args:
            address: Address to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            Web3.to_checksum_address(address)
            return True
        except ValueError:
            return False
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get basic token information.
        
        Returns:
            Dictionary with token details
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
            logger.error(f"Error getting token info: {e}")
            return {}
    
    def burn_tokens_from_address(self, from_address: str, amount: Decimal, private_key: str) -> Optional[str]:
        """
        Burn TeoCoin tokens from a specific address (for deposit system).
        
        Args:
            from_address: Address to burn tokens from
            amount: Amount of TEO tokens to burn
            private_key: Private key of the address (for signing)
            
        Returns:
            Transaction hash if successful, None if failed
        """
        try:
            # Get account from private key
            account = self.w3.eth.account.from_key(private_key)
            
            # Verify the address matches
            if account.address.lower() != from_address.lower():
                logger.error(f"Address mismatch: {account.address} != {from_address}")
                return None
            
            # Convert amount to wei (18 decimals)
            amount_wei = Web3.to_wei(amount, 'ether')
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            
            # Get nonce
            nonce = self.w3.eth.get_transaction_count(account.address)
            
            # Build burn transaction
            transaction = self.contract.functions.burn(
                amount_wei
            ).build_transaction({
                'from': account.address,
                'gas': 100000,  # Standard gas limit for burning
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            # Sign and send transaction
            signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            logger.info(f"Burned {amount} TEO from {from_address} - TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error burning {amount} TEO from {from_address}: {e}")
            return None


# Global service instance
teocoin_service = TeoCoinBlockchainService()
