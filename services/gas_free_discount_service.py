"""
Gas-Free TeoCoin Discount Service
Implements signature-based discount requests where platform pays gas fees.
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


class GasFreeDiscountService(TransactionalService):
    """
    Service for handling gas-free discount requests using signature-based authentication.
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
        self.gas_free_contract_address = getattr(settings, 'TEOCOIN_DISCOUNT_GAS_FREE_CONTRACT_ADDRESS', None)
        self.teo_contract_address = getattr(settings, 'TEOCOIN_CONTRACT_ADDRESS', None)
        self.platform_private_key = getattr(settings, 'PLATFORM_PRIVATE_KEY', None)
        
        # Validate required configuration
        if not self.gas_free_contract_address:
            raise ServiceException("TEOCOIN_DISCOUNT_GAS_FREE_CONTRACT must be set")
        if not self.teo_contract_address:
            raise ServiceException("TEOCOIN_CONTRACT_ADDRESS must be set")
        if not self.platform_private_key:
            raise ServiceException("PLATFORM_PRIVATE_KEY must be set")
            
        # Derive platform account from private key to ensure consistency
        try:
            platform_account = Account.from_key(self.platform_private_key)
            self.platform_account = platform_account.address
        except Exception as e:
            raise ServiceException(f"Invalid PLATFORM_PRIVATE_KEY: {str(e)}")
        
        # Load contract ABIs
        self.gas_free_contract = self._load_gas_free_contract()
        self.teo_contract = self._load_teo_contract()
        
    def _load_gas_free_contract(self):
        """Load the gas-free discount contract instance."""
        # Use the comprehensive gas-free contract ABI
        gas_free_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "_teoToken", "type": "address"},
                    {"internalType": "address", "name": "_rewardPool", "type": "address"},
                    {"internalType": "address", "name": "_platformAccount", "type": "address"}
                ],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "inputs": [
                    {"internalType": "address", "name": "student", "type": "address"},
                    {"internalType": "address", "name": "teacher", "type": "address"},
                    {"internalType": "uint256", "name": "courseId", "type": "uint256"},
                    {"internalType": "uint256", "name": "coursePrice", "type": "uint256"},
                    {"internalType": "uint256", "name": "discountPercent", "type": "uint256"},
                    {"internalType": "bytes", "name": "studentSignature", "type": "bytes"}
                ],
                "name": "createDiscountRequestGasFree",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "platformAccount",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "isGasFreeEnabled",
                "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "owner",
                "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getCurrentRequestId",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "name": "discountRequests",
                "outputs": [
                    {"internalType": "uint256", "name": "requestId", "type": "uint256"},
                    {"internalType": "address", "name": "student", "type": "address"},
                    {"internalType": "address", "name": "teacher", "type": "address"},
                    {"internalType": "uint256", "name": "courseId", "type": "uint256"},
                    {"internalType": "uint256", "name": "coursePrice", "type": "uint256"},
                    {"internalType": "uint256", "name": "discountPercent", "type": "uint256"},
                    {"internalType": "uint256", "name": "teoCost", "type": "uint256"},
                    {"internalType": "uint256", "name": "teacherBonus", "type": "uint256"},
                    {"internalType": "uint256", "name": "createdAt", "type": "uint256"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint8", "name": "status", "type": "uint8"},
                    {"internalType": "bytes", "name": "studentSignature", "type": "bytes"}
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "internalType": "uint256", "name": "requestId", "type": "uint256"},
                    {"indexed": True, "internalType": "address", "name": "student", "type": "address"},
                    {"indexed": True, "internalType": "address", "name": "teacher", "type": "address"},
                    {"indexed": False, "internalType": "uint256", "name": "courseId", "type": "uint256"},
                    {"indexed": False, "internalType": "uint256", "name": "discountPercent", "type": "uint256"},
                    {"indexed": False, "internalType": "uint256", "name": "teoCost", "type": "uint256"}
                ],
                "name": "DiscountRequested",
                "type": "event"
            }
        ]
        
        logger.info(f"✅ Using comprehensive gas-free contract ABI")
        
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(self.gas_free_contract_address),
            abi=gas_free_abi
        )
    
    def _load_teo_contract(self):
        """Load the TEO token contract instance."""
        # TEO contract ABI with permit support (EIP-2612)
        teo_abi = [
            {
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"},
                    {"name": "value", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "v", "type": "uint8"},
                    {"name": "r", "type": "bytes32"},
                    {"name": "s", "type": "bytes32"}
                ],
                "name": "permit",
                "outputs": [],
                "type": "function"
            },
            {
                "inputs": [],
                "name": "DOMAIN_SEPARATOR",
                "outputs": [{"name": "", "type": "bytes32"}],
                "type": "function"
            },
            {
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "nonces",
                "outputs": [{"name": "", "type": "uint256"}],
                "type": "function"
            },
            {
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "type": "function"
            }
        ]
        
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(self.teo_contract_address),
            abi=teo_abi
        )
    
    def create_discount_signature(
        self, 
        student_address: str, 
        course_id: int, 
        teo_amount: int,
        nonce: Optional[int] = None
    ) -> Dict:
        """
        Create a signature for gas-free discount request.
        
        Args:
            student_address: Student's wallet address
            course_id: Course ID for the discount
            teo_amount: Amount of TEO tokens to spend
            nonce: Optional nonce (uses timestamp if not provided)
            
        Returns:
            Dict with signature data and message hash
        """
        try:
            # Generate nonce if not provided
            if nonce is None:
                nonce = int(datetime.now().timestamp())
            
            # Validate and checksum the student address
            if not Web3.is_address(student_address):
                raise ServiceException("Invalid student address")
            
            # Ensure address is properly checksummed
            student_address = Web3.to_checksum_address(student_address)
            
            if teo_amount <= 0:
                raise InvalidAmountError(float(teo_amount))
            
            # Check student's TEO balance
            balance = self.teo_contract.functions.balanceOf(student_address).call()
            
            # Convert teo_amount to wei (18 decimals)
            teo_amount_wei = teo_amount * (10 ** 18)
            
            if balance < teo_amount_wei:
                raise ServiceException(
                    f"Insufficient TEO balance. Required: {teo_amount} TEO, Available: {balance / (10**18)} TEO"
                )
            
            # Create message hash for signing (EXACT match with contract)
            # Contract expects: keccak256(student, courseId, teoCost, contractAddress, chainId)
            inner_hash = Web3.solidity_keccak(
                ['address', 'uint256', 'uint256', 'address', 'uint256'],
                [
                    student_address, 
                    course_id, 
                    teo_amount_wei,  # Use wei amount, not human amount
                    self.gas_free_contract_address,
                    80002  # Polygon Amoy chain ID
                ]
            )
            
            logger.info(f"📝 Creating signature for:")
            logger.info(f"   Student: {student_address}")
            logger.info(f"   Course ID: {course_id}")
            logger.info(f"   TEO Amount: {teo_amount} ({teo_amount_wei} wei)")
            logger.info(f"   Contract: {self.gas_free_contract_address}")
            logger.info(f"   Chain ID: 80002")
            logger.info(f"   Inner hash: {inner_hash.hex()}")
            
            # Cache signature data for validation
            cache_key = f"discount_signature_{student_address}_{course_id}_{nonce}"
            cache.set(cache_key, {
                'student_address': student_address,
                'course_id': course_id,
                'teo_amount': teo_amount,
                'teo_amount_wei': teo_amount_wei,
                'nonce': nonce,
                'inner_hash': inner_hash.hex(),  # Store without 0x prefix for validation
                'created_at': datetime.now().isoformat()
            }, timeout=3600)  # 1 hour expiry
            
            return {
                'message_hash': f"0x{inner_hash.hex()}",  # Add 0x prefix for ethers.js compatibility
                'student_address': student_address,
                'course_id': course_id,
                'teo_amount': teo_amount,
                'teo_amount_wei': teo_amount_wei,
                'nonce': nonce,
                'contract_address': self.gas_free_contract_address,
                'instructions': {
                    'message': f"Sign this message to request discount for course {course_id}",
                    'amount': f"{teo_amount} TEO tokens",
                    'gas_free': "Platform will pay all gas fees"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating discount signature: {str(e)}")
            raise ServiceException(f"Failed to create discount signature: {str(e)}")
    
    def create_permit_signature_data(
        self, 
        student_address: str, 
        deadline: Optional[int] = None
    ) -> Dict:
        """
        Create permit signature data for gasless TEO approval.
        
        Args:
            student_address: Student's wallet address
            deadline: Optional deadline timestamp (defaults to 1 hour from now)
            
        Returns:
            EIP-712 typed data for frontend to sign
        """
        try:
            # Validate and checksum the student address
            if not Web3.is_address(student_address):
                raise ServiceException("Invalid student address")
            
            # Ensure address is properly checksummed
            student_address = Web3.to_checksum_address(student_address)
            
            # Set deadline if not provided (1 hour from now)
            if deadline is None:
                deadline = int(datetime.now().timestamp()) + 3600
            
            # Get current nonce for the student
            nonce = self.teo_contract.functions.nonces(student_address).call()
            
            # Get token name
            try:
                token_name = self.teo_contract.functions.name().call()
            except:
                token_name = "TeoCoin2"  # Fallback
            
            logger.info(f"📝 Creating permit data for {student_address}")
            logger.info(f"   Token: {token_name}")
            logger.info(f"   Nonce: {nonce}")
            logger.info(f"   Deadline: {deadline}")
            
            # EIP-712 domain
            domain = {
                'name': token_name,
                'version': '1',
                'chainId': 80002,  # Polygon Amoy
                'verifyingContract': self.teo_contract_address
            }
            
            # Permit message (balance between ethers.js compatibility and usefulness)
            # Use 100 TEO tokens but pass as string to avoid ethers.js overflow
            reasonable_approval = 100 * (10**18)  # 100 TEO tokens in wei
            minimal_approval = reasonable_approval
            message = {
                'owner': student_address,
                'spender': self.gas_free_contract_address,
                'value': str(minimal_approval),  # Pass as string to avoid ethers.js overflow
                'nonce': nonce,
                'deadline': deadline
            }
            
            # EIP-712 typed data structure
            permit_typed_data = {
                'types': {
                    'EIP712Domain': [
                        {'name': 'name', 'type': 'string'},
                        {'name': 'version', 'type': 'string'},
                        {'name': 'chainId', 'type': 'uint256'},
                        {'name': 'verifyingContract', 'type': 'address'}
                    ],
                    'Permit': [
                        {'name': 'owner', 'type': 'address'},
                        {'name': 'spender', 'type': 'address'},
                        {'name': 'value', 'type': 'uint256'},
                        {'name': 'nonce', 'type': 'uint256'},
                        {'name': 'deadline', 'type': 'uint256'}
                    ]
                },
                'primaryType': 'Permit',
                'domain': domain,
                'message': message
            }
            
            return {
                'typed_data': permit_typed_data,
                'student_address': student_address,
                'spender': self.gas_free_contract_address,
                'deadline': deadline,
                'nonce': nonce,
                'instructions': {
                    'message': "Sign this permit to allow gas-free TEO spending",
                    'method': "eth_signTypedData_v4",
                    'gas_free': "No MATIC required for this signature"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating permit signature data: {str(e)}")
            raise ServiceException(f"Failed to create permit data: {str(e)}")
    
    def validate_signature(
        self, 
        student_address: str, 
        signature: str, 
        course_id: int, 
        teo_amount: int, 
        nonce: int
    ) -> bool:
        """
        Validate student's signature for discount request.
        
        Args:
            student_address: Student's wallet address
            signature: Student's signature
            course_id: Course ID
            teo_amount: Amount of TEO tokens
            nonce: Signature nonce
            
        Returns:
            True if signature is valid
        """
        try:
            logger.info(f"🔐 Validating signature for student {student_address}")
            logger.info(f"🔐 Parameters: course_id={course_id}, teo_amount={teo_amount}, nonce={nonce}")
            logger.info(f"🔐 Signature: {signature[:20]}...{signature[-20:]} (length: {len(signature)})")
            
            # Ensure address is properly checksummed
            student_address = Web3.to_checksum_address(student_address)
            
            # Convert teo_amount to wei (18 decimals) - same as contract expects
            teo_amount_wei = teo_amount * (10 ** 18)
            
            # Create the EXACT same message hash as the contract
            # Contract: keccak256(student, courseId, teoCost, contractAddress, chainId)
            inner_hash = Web3.solidity_keccak(
                ['address', 'uint256', 'uint256', 'address', 'uint256'],
                [
                    student_address, 
                    course_id, 
                    teo_amount_wei,  # Use wei amount
                    self.gas_free_contract_address,
                    80002  # Polygon Amoy chain ID
                ]
            )
            
            logger.info(f"🔐 Inner hash: {inner_hash.hex()}")
            
            # The contract does the Ethereum message wrapping internally
            # So we need to validate using the inner hash that was signed
            message = encode_defunct(inner_hash)
            
            # Recover signer address from signature
            try:
                if isinstance(signature, str):
                    signature_bytes = bytes.fromhex(signature.replace('0x', ''))
                else:
                    signature_bytes = signature
                    
                logger.info(f"🔐 Signature bytes length: {len(signature_bytes)}")
                
                # Recover address using the standard method
                recovered_address = Account.recover_message(message, signature=signature_bytes)
                
                logger.info(f"🔐 Recovered address: {recovered_address}")
                
            except Exception as sig_error:
                logger.error(f"❌ Signature recovery failed: {sig_error}")
                raise BlockchainTransactionError(f"Invalid signature format: {str(sig_error)}")
            
            # Validate signer matches student address
            if recovered_address.lower() != student_address.lower():
                logger.error(f"❌ Signature mismatch: recovered={recovered_address}, expected={student_address}")
                raise BlockchainTransactionError("Signature does not match student address")
            
            logger.info("✅ Signature validation successful")
            
            # Check if signature was previously used
            signature_key = f"used_signature_{signature}"
            if cache.get(signature_key):
                logger.error("❌ Signature already used")
                raise BlockchainTransactionError("Signature already used")
            
            logger.info("✅ Signature is new (not previously used)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating signature: {str(e)}")
            raise BlockchainTransactionError(f"Invalid signature: {str(e)}")
    
    def execute_discount_request(
        self, 
        student_address: str, 
        signature: str, 
        course_id: int, 
        teo_amount: int, 
        nonce: int,
        permit_deadline: Optional[int] = None,
        permit_v: Optional[int] = None,
        permit_r: Optional[str] = None,
        permit_s: Optional[str] = None
    ) -> Dict:
        """
        Execute gas-free discount request on blockchain.
        Platform pays all gas fees.
        
        Args:
            student_address: Student's wallet address
            signature: Student's signature
            course_id: Course ID
            teo_amount: Amount of TEO tokens
            nonce: Signature nonce
            
        Returns:
            Transaction result with discount request ID
        """
        try:
            logger.info(f"🚀 Starting gas-free discount execution...")
            logger.info(f"📝 Parameters: student={student_address}, course_id={course_id}, teo_amount={teo_amount}, nonce={nonce}")
            
            # Validate signature
            logger.info("🔐 Validating signature...")
            self.validate_signature(student_address, signature, course_id, teo_amount, nonce)
            logger.info("✅ Signature validation passed")
            
            # Check platform account balance
            platform_balance = self.w3.eth.get_balance(self.platform_account)
            min_balance = self.w3.to_wei(0.01, 'ether')  # 0.01 MATIC minimum
            balance_matic = self.w3.from_wei(platform_balance, 'ether')
            
            logger.info(f"💰 Platform account: {self.platform_account}")
            logger.info(f"💰 Platform balance: {balance_matic} MATIC")
            
            if platform_balance < min_balance:
                raise ServiceException("Insufficient platform balance for gas fees")
            
            # Prepare transaction
            platform_account = Account.from_key(self.platform_private_key)
            
            # Calculate default values for the contract call
            default_teacher = "0x742d35Cc6636C0532925a3b8D933aa3c5a2C8A08"  # Default teacher address
            course_price = teo_amount * 100  # Assume 1 TEO = 1 EUR, price in cents
            discount_percent = 10  # 10% default discount
            
            # Convert TEO amount to wei for contract (same as signature validation)
            teo_amount_wei = teo_amount * (10 ** 18)
            
            logger.info(f"🎯 Contract parameters:")
            logger.info(f"   Student: {student_address}")
            logger.info(f"   Teacher: {default_teacher}")
            logger.info(f"   Course ID: {course_id}")
            logger.info(f"   Course Price: {course_price} cents")
            logger.info(f"   Discount %: {discount_percent}%")
            logger.info(f"   TEO Amount: {teo_amount} TEO ({teo_amount_wei} wei)")
            logger.info(f"   Signature length: {len(signature)} chars")
            
            # Check platform account in contract before transaction
            try:
                platform_check_abi = [
                    {
                        "inputs": [],
                        "name": "platformAccount",
                        "outputs": [{"name": "", "type": "address"}],
                        "type": "function"
                    }
                ]
                
                check_contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.gas_free_contract_address),
                    abi=platform_check_abi
                )
                
                contract_platform = check_contract.functions.platformAccount().call()
                logger.info(f"🔍 Contract platform account: {contract_platform}")
                logger.info(f"🔍 Our platform account: {self.platform_account}")
                
                if contract_platform.lower() != self.platform_account.lower():
                    logger.error(f"❌ Platform account mismatch! Contract: {contract_platform}, Ours: {self.platform_account}")
                    raise ServiceException(f"Platform account mismatch: contract={contract_platform}, ours={self.platform_account}")
                else:
                    logger.info("✅ Platform account matches contract")
                    
            except Exception as check_error:
                logger.warning(f"⚠️ Could not verify platform account: {check_error}")
            
            # Build transaction with the actual contract interface
            logger.info("🔨 Building transaction...")
            
            # Convert signature to bytes
            if isinstance(signature, str):
                signature_bytes = bytes.fromhex(signature.replace('0x', ''))
            else:
                signature_bytes = signature
                
            logger.info(f"🔐 Signature bytes length: {len(signature_bytes)}")
            
            # Build transaction with careful gas management
            logger.info("🔨 Building transaction...")
            
            # Convert signature to bytes
            if isinstance(signature, str):
                signature_bytes = bytes.fromhex(signature.replace('0x', ''))
            else:
                signature_bytes = signature
                
            logger.info(f"� Signature bytes length: {len(signature_bytes)}")
            
            # Get current gas price
            gas_price = self.w3.eth.gas_price
            logger.info(f"⛽ Current gas price: {self.w3.from_wei(gas_price, 'gwei')} gwei")
            
            # Handle permit if provided (gasless approval) - if it fails, check regular approval
            if all([permit_deadline, permit_v, permit_r, permit_s]):
                logger.info("🎫 Attempting permit (gasless approval)...")
                try:
                    # Execute permit to approve gas-free contract
                    # Use the same approval amount as in the permit signature
                    permit_approval_amount = 100 * (10**18)  # Match the signature amount
                    permit_function = self.teo_contract.functions.permit(
                        Web3.to_checksum_address(student_address),  # owner
                        Web3.to_checksum_address(self.gas_free_contract_address),  # spender
                        permit_approval_amount,  # Use consistent approval amount
                        permit_deadline,
                        permit_v,
                        bytes.fromhex(permit_r.replace('0x', '')),
                        bytes.fromhex(permit_s.replace('0x', ''))
                    )
                    
                    # Build permit transaction
                    permit_tx = permit_function.build_transaction({
                        'from': self.platform_account,
                        'gas': 100000,  # Standard gas for permit
                        'gasPrice': gas_price,
                        'nonce': self.w3.eth.get_transaction_count(self.platform_account),
                        'value': 0
                    })
                    
                    # Sign and send permit transaction
                    signed_permit = platform_account.sign_transaction(permit_tx)
                    permit_tx_hash = self.w3.eth.send_raw_transaction(signed_permit.raw_transaction)
                    
                    logger.info(f"🎫 Permit transaction sent: {permit_tx_hash.hex()}")
                    
                    # Wait for permit confirmation
                    permit_receipt = self.w3.eth.wait_for_transaction_receipt(permit_tx_hash, timeout=60)
                    if permit_receipt['status'] == 1:
                        logger.info("✅ Permit transaction successful!")
                    else:
                        logger.warning("⚠️ Permit transaction failed, checking regular approval...")
                        
                except Exception as permit_error:
                    logger.warning(f"⚠️ Permit execution failed: {permit_error}")
                    logger.info("🔄 Falling back to regular approval check...")
            
            # Always check allowance regardless of permit success/failure
            logger.info("ℹ️ Checking current allowance...")
            current_allowance = self.teo_contract.functions.allowance(
                Web3.to_checksum_address(student_address),
                Web3.to_checksum_address(self.gas_free_contract_address)
            ).call()
            
            if current_allowance < teo_amount_wei:
                logger.error(f"❌ Insufficient allowance: {current_allowance / (10**18)} TEO, need {teo_amount} TEO")
                raise TokenTransferError(
                    f"Student needs to approve TEO tokens first. "
                    f"Current allowance: {current_allowance / (10**18):.2f} TEO, "
                    f"Required: {teo_amount} TEO. "
                    f"Please visit the TEO contract and approve the gas-free contract: "
                    f"{self.gas_free_contract_address}"
                )
            else:
                logger.info(f"✅ Sufficient allowance: {current_allowance / (10**18)} TEO")
            
            # Build the transaction step by step
            function_call = self.gas_free_contract.functions.createDiscountRequestGasFree(
                Web3.to_checksum_address(student_address),
                Web3.to_checksum_address(default_teacher),
                course_id,
                course_price,  # EUR cents
                discount_percent,
                signature_bytes
            )
            
            # First, estimate gas with some padding
            try:
                logger.info("⛽ Estimating gas...")
                base_gas_estimate = function_call.estimate_gas({
                    'from': self.platform_account
                })
                # Add 20% padding to gas estimate
                gas_limit = int(base_gas_estimate * 1.2)
                logger.info(f"✅ Gas estimation: {base_gas_estimate} (using {gas_limit} with padding)")
            except Exception as gas_error:
                logger.error(f"❌ Gas estimation failed: {gas_error}")
                # Try with a fixed gas limit as fallback
                gas_limit = 600000
                logger.warning(f"Using fallback gas limit: {gas_limit}")
            
            # Build transaction with proper gas management
            transaction = function_call.build_transaction({
                'from': self.platform_account,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.platform_account),
                'value': 0  # No ETH/MATIC value transferred
            })
            
            logger.info(f"� Transaction built:")
            logger.info(f"   From: {transaction.get('from')}")
            logger.info(f"   To: {transaction.get('to')}")
            logger.info(f"   Gas: {transaction.get('gas')}")
            logger.info(f"   Gas Price: {self.w3.from_wei(transaction.get('gasPrice', 0), 'gwei')} gwei")
            logger.info(f"   Nonce: {transaction.get('nonce')}")
            logger.info(f"   Value: {transaction.get('value', 0)} wei")
            
            # Sign transaction
            logger.info("✍️ Signing transaction...")
            signed_txn = platform_account.sign_transaction(transaction)
            
            # Send transaction
            logger.info("📡 Sending transaction to blockchain...")
            try:
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                logger.info(f"📜 Transaction sent! Hash: {tx_hash.hex()}")
            except Exception as send_error:
                logger.error(f"❌ Failed to send transaction: {send_error}")
                raise TokenTransferError(f"Transaction submission failed: {str(send_error)}")
            
            # Wait for confirmation with timeout
            logger.info("⏳ Waiting for confirmation...")
            try:
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)  # 3 minutes timeout
            except Exception as receipt_error:
                logger.error(f"❌ Transaction receipt timeout: {receipt_error}")
                raise TokenTransferError(f"Transaction confirmation timeout: {str(receipt_error)}")
            
            logger.info(f"📋 Transaction receipt:")
            logger.info(f"   Status: {receipt['status']}")
            logger.info(f"   Block: {receipt['blockNumber']}")
            logger.info(f"   Gas Used: {receipt['gasUsed']}")
            logger.info(f"   Gas Limit: {transaction.get('gas', 'Unknown')}")
            logger.info(f"   Transaction Hash: {receipt['transactionHash'].hex()}")
            
            # Check transaction status
            if receipt['status'] == 0:
                logger.error("❌ Transaction failed on blockchain")
                logger.error(f"❌ Failed transaction hash: {receipt['transactionHash'].hex()}")
                logger.error(f"❌ Block explorer: https://amoy.polygonscan.com/tx/{receipt['transactionHash'].hex()}")
                
                # Try to get the revert reason
                try:
                    logger.info("🔍 Attempting to get revert reason...")
                    # Try to call the same transaction to get revert reason
                    self.w3.eth.call({
                        'to': receipt['to'],
                        'from': receipt['from'],
                        'data': transaction.get('data', '0x'),
                        'value': transaction.get('value', 0),
                    }, receipt['blockNumber'] - 1)
                except Exception as call_error:
                    logger.error(f"❌ Revert reason: {str(call_error)}")
                    # Parse common revert reasons
                    error_msg = str(call_error).lower()
                    if 'insufficient' in error_msg:
                        if 'balance' in error_msg:
                            logger.error("💡 Likely cause: Insufficient TEO balance")
                        elif 'allowance' in error_msg:
                            logger.error("💡 Likely cause: Insufficient TEO allowance")
                        else:
                            logger.error("💡 Likely cause: Some insufficient resource")
                    elif 'signature' in error_msg:
                        logger.error("💡 Likely cause: Invalid signature")
                    elif 'paused' in error_msg:
                        logger.error("💡 Likely cause: Contract is paused")
                    elif 'platform' in error_msg or 'owner' in error_msg:
                        logger.error("💡 Likely cause: Platform account permission denied")
                
                raise TokenTransferError("Transaction failed on blockchain")
            
            logger.info("✅ Transaction successful!")
            
            # Parse logs to get discount request ID
            discount_request_id = None
            logger.info(f"🔍 Parsing {len(receipt['logs'])} logs...")
            for i, log in enumerate(receipt['logs']):
                try:
                    logger.debug(f"📄 Log {i}: {log}")
                    # Try to decode the DiscountRequested event
                    topics = [self.w3.keccak(text="DiscountRequested(uint256,address,address,uint256,uint256,uint256)")]
                    if log['topics'][0] == topics[0]:
                        # Decode the requestId from the first indexed parameter
                        discount_request_id = int(log['topics'][1].hex(), 16)
                        logger.info(f"✅ Found discount request ID: {discount_request_id}")
                        break
                except Exception as decode_error:
                    logger.debug(f"Could not decode log {i}: {decode_error}")
                    continue
            
            if discount_request_id is None:
                logger.warning("⚠️ Could not extract discount request ID from logs")
            
            # Mark signature as used
            signature_key = f"used_signature_{signature}"
            cache.set(signature_key, True, timeout=86400)  # 24 hours
            
            # Log successful transaction
            logger.info(f"🎉 Gas-free discount request created successfully!")
            logger.info(f"   Request ID: {discount_request_id}")
            logger.info(f"   Student: {student_address}")
            logger.info(f"   Transaction: {tx_hash.hex()}")
            
            result = {
                'success': True,
                'transaction_hash': tx_hash.hex(),
                'discount_request_id': discount_request_id,
                'student_address': student_address,
                'course_id': course_id,
                'teo_amount': teo_amount,
                'gas_cost': receipt['gasUsed'] * transaction.get('gasPrice', 0),
                'block_number': receipt['blockNumber'],
                'platform_paid_gas': True
            }
            
            logger.info(f"📤 Returning result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error executing discount request: {str(e)}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise ServiceException(f"Failed to execute discount request: {str(e)}")
    
    def get_discount_request_status(self, request_id: int) -> Dict:
        """
        Get status of a discount request.
        
        Args:
            request_id: Discount request ID
            
        Returns:
            Request status and details
        """
        try:
            request_data = self.gas_free_contract.functions.discountRequests(request_id).call()
            
            return {
                'request_id': request_id,
                'student': request_data[0],
                'course_id': request_data[1],
                'teo_amount': request_data[2],
                'status': request_data[3],  # 0: Pending, 1: Approved, 2: Rejected
                'teacher': request_data[4],
                'timestamp': request_data[5],
                'is_gas_free': True
            }
            
        except Exception as e:
            logger.error(f"Error getting discount request status: {str(e)}")
            raise ServiceException(f"Failed to get request status: {str(e)}")
    
    def estimate_gas_cost(self) -> Dict:
        """
        Estimate gas costs for discount operations.
        
        Returns:
            Gas cost estimates in MATIC and USD
        """
        try:
            # Current gas price
            gas_price = self.w3.eth.gas_price
            
            # Estimated gas usage
            discount_gas = 250000  # Estimated gas for discount request
            
            # Calculate costs
            discount_cost_wei = discount_gas * gas_price
            discount_cost_matic = self.w3.from_wei(discount_cost_wei, 'ether')
            
            # Estimate USD cost (MATIC ~$0.50)
            matic_usd_rate = 0.50
            discount_cost_usd = float(discount_cost_matic) * matic_usd_rate
            
            return {
                'gas_price_gwei': self.w3.from_wei(gas_price, 'gwei'),
                'discount_request': {
                    'gas_limit': discount_gas,
                    'cost_matic': float(discount_cost_matic),
                    'cost_usd': discount_cost_usd
                },
                'daily_estimates': {
                    '10_requests': discount_cost_usd * 10,
                    '50_requests': discount_cost_usd * 50,
                    '100_requests': discount_cost_usd * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Error estimating gas costs: {str(e)}")
            return {
                'error': str(e),
                'fallback_estimate': {
                    'cost_usd_per_request': 0.002,
                    'daily_100_requests': 0.20
                }
            }
