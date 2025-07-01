"""
TeoCoin Discount Service - Layer 2 Gas-Free Implementation

This service handles the gas-free discount system where:
1. Students request discounts without paying gas
2. Platform pays all gas fees for seamless UX
3. Direct MetaMask to MetaMask transfers
4. Automatic teacher bonus from reward pool
"""

import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from eth_account.messages import encode_defunct

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from blockchain.blockchain import TeoCoinService


class DiscountStatus(Enum):
    PENDING = 0
    APPROVED = 1
    DECLINED = 2
    EXPIRED = 3


@dataclass
class DiscountRequest:
    """Discount request data structure"""
    request_id: int
    student: str
    teacher: str
    course_id: int
    course_price: int  # EUR cents
    discount_percent: int
    teo_cost: int  # TEO wei
    teacher_bonus: int  # TEO wei
    created_at: datetime
    deadline: datetime
    status: DiscountStatus
    transaction_hash: Optional[str] = None
    decline_reason: Optional[str] = None


class TeoCoinDiscountService:
    """Service for handling gas-free TeoCoin discount system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.teocoin_service = TeoCoinService()
        
        # Contract setup
        self.w3 = self.teocoin_service.w3
        self.discount_contract: Optional[Contract] = None
        self.platform_account: Optional[Account] = None
        
        # Configuration
        self.REQUEST_TIMEOUT_HOURS = 2
        self.TEACHER_BONUS_PERCENT = 25
        self.MAX_DISCOUNT_PERCENT = 15
        self.TEO_TO_EUR_RATE = 10  # 1 TEO = 0.10 EUR
        
        self._initialize_contract()
        
    def _initialize_contract(self):
        """Initialize discount contract and platform account"""
        try:
            # Load contract ABI and address from settings
            contract_address = getattr(settings, 'TEOCOIN_DISCOUNT_CONTRACT_ADDRESS', None)
            contract_abi = getattr(settings, 'TEOCOIN_DISCOUNT_CONTRACT_ABI', None)
            platform_private_key = getattr(settings, 'PLATFORM_PRIVATE_KEY', None)
            
            if not all([contract_address, contract_abi, platform_private_key]):
                self.logger.warning("Missing contract configuration in settings - discount service disabled")
                return
            
            # Initialize contract
            self.discount_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=contract_abi
            )
            
            # Initialize platform account
            self.platform_account = Account.from_key(platform_private_key)
            
            self.logger.info(f"TeoCoinDiscount contract initialized at {contract_address}")
            self.logger.info(f"Platform account: {self.platform_account.address}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize discount contract: {e}")
            self.discount_contract = None
            self.platform_account = None
    
    def create_discount_request(
        self,
        student_address: str,
        teacher_address: str,
        course_id: int,
        course_price: Decimal,  # EUR
        discount_percent: int,
        student_signature: str
    ) -> Dict:
        """
        Create a new discount request (platform pays gas)
        
        Args:
            student_address: Student's wallet address
            teacher_address: Teacher's wallet address
            course_id: Course identifier
            course_price: Course price in EUR
            discount_percent: Discount percentage (5, 10, or 15)
            student_signature: Student's pre-approval signature
            
        Returns:
            Dict with request details and transaction info
        """
        try:
            if not self.discount_contract or not self.platform_account:
                raise ValueError("Discount service not properly initialized")
            
            # Validate inputs
            self._validate_discount_request(
                student_address, teacher_address, course_id, 
                course_price, discount_percent
            )
            
            # Convert price to cents
            course_price_cents = int(course_price * 100)
            
            # Calculate TEO cost and teacher bonus
            teo_cost, teacher_bonus = self._calculate_teo_amounts(
                course_price_cents, discount_percent
            )
            
            # Verify student has sufficient TEO balance
            student_balance = self.teocoin_service.get_balance(student_address)
            if student_balance < Decimal(str(teo_cost / 10**18)):
                raise ValueError(f"Insufficient TEO balance. Required: {teo_cost / 10**18}, Available: {student_balance}")
            
            # Verify reward pool has sufficient balance for bonus
            reward_pool_balance = self.teocoin_service.get_reward_pool_balance()
            if reward_pool_balance < Decimal(str(teacher_bonus / 10**18)):
                raise ValueError(f"Insufficient reward pool balance for teacher bonus")
            
            # Build transaction
            function_call = self.discount_contract.functions.createDiscountRequest(
                Web3.to_checksum_address(student_address),
                Web3.to_checksum_address(teacher_address),
                course_id,
                course_price_cents,
                discount_percent,
                bytes.fromhex(student_signature.replace('0x', ''))
            )
            
            # Execute transaction (platform pays gas)
            tx_hash = self._execute_platform_transaction(function_call)
            
            # Get request ID from transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            request_id = self._extract_request_id_from_receipt(receipt)
            
            # Create response
            result = {
                'success': True,
                'request_id': request_id,
                'transaction_hash': tx_hash.hex(),
                'student': student_address,
                'teacher': teacher_address,
                'course_id': course_id,
                'course_price': float(course_price),
                'discount_percent': discount_percent,
                'teo_cost': teo_cost,
                'teacher_bonus': teacher_bonus,
                'deadline': timezone.now() + timedelta(hours=self.REQUEST_TIMEOUT_HOURS)
            }
            
            # Cache request for quick access
            cache_key = f"discount_request_{request_id}"
            cache.set(cache_key, result, timeout=3600 * 24)  # 24 hours
            
            self.logger.info(f"Discount request created: {request_id} for student {student_address}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create discount request: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def approve_discount_request(self, request_id: int, approver_address: str) -> Dict:
        """
        Approve discount request and execute transfers (platform pays gas)
        
        Args:
            request_id: Request ID to approve
            approver_address: Address of the approver (should be teacher)
            
        Returns:
            Dict with approval result and transaction info
        """
        try:
            if not self.discount_contract or not self.platform_account:
                raise ValueError("Discount service not properly initialized")
            
            # Get request details
            request_data = self.get_discount_request(request_id)
            if not request_data:
                raise ValueError(f"Request {request_id} not found")
            
            # Verify approver is the teacher
            if approver_address.lower() != request_data['teacher'].lower():
                raise ValueError("Only the assigned teacher can approve this request")
            
            # Verify request is still pending and not expired
            if request_data['status'] != DiscountStatus.PENDING.value:
                raise ValueError("Request is no longer pending")
            
            if timezone.now() > request_data['deadline']:
                raise ValueError("Request has expired")
            
            # Execute approval transaction (platform pays gas)
            function_call = self.discount_contract.functions.approveDiscountRequest(request_id)
            tx_hash = self._execute_platform_transaction(function_call)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Update cache
            cache_key = f"discount_request_{request_id}"
            request_data['status'] = DiscountStatus.APPROVED.value
            request_data['transaction_hash'] = tx_hash.hex()
            cache.set(cache_key, request_data, timeout=3600 * 24)
            
            result = {
                'success': True,
                'request_id': request_id,
                'transaction_hash': tx_hash.hex(),
                'gas_used': receipt['gasUsed'],
                'teo_transferred': request_data['teo_cost'],
                'teacher_bonus': request_data['teacher_bonus']
            }
            
            self.logger.info(f"Discount request {request_id} approved successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to approve discount request {request_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def decline_discount_request(
        self, 
        request_id: int, 
        decliner_address: str, 
        reason: str
    ) -> Dict:
        """
        Decline discount request
        
        Args:
            request_id: Request ID to decline
            decliner_address: Address of the decliner (should be teacher)
            reason: Reason for declining
            
        Returns:
            Dict with decline result
        """
        try:
            if not self.discount_contract or not self.platform_account:
                raise ValueError("Discount service not properly initialized")
            
            # Get request details
            request_data = self.get_discount_request(request_id)
            if not request_data:
                raise ValueError(f"Request {request_id} not found")
            
            # Verify decliner is the teacher
            if decliner_address.lower() != request_data['teacher'].lower():
                raise ValueError("Only the assigned teacher can decline this request")
            
            # Verify request is still pending
            if request_data['status'] != DiscountStatus.PENDING.value:
                raise ValueError("Request is no longer pending")
            
            # Execute decline transaction (platform pays gas)
            function_call = self.discount_contract.functions.declineDiscountRequest(
                request_id, 
                reason
            )
            tx_hash = self._execute_platform_transaction(function_call)
            
            # Update cache
            cache_key = f"discount_request_{request_id}"
            request_data['status'] = DiscountStatus.DECLINED.value
            request_data['decline_reason'] = reason
            request_data['transaction_hash'] = tx_hash.hex()
            cache.set(cache_key, request_data, timeout=3600 * 24)
            
            result = {
                'success': True,
                'request_id': request_id,
                'transaction_hash': tx_hash.hex(),
                'reason': reason
            }
            
            self.logger.info(f"Discount request {request_id} declined: {reason}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to decline discount request {request_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_discount_request(self, request_id: int) -> Optional[Dict]:
        """
        Get discount request details
        
        Args:
            request_id: Request ID
            
        Returns:
            Dict with request details or None if not found
        """
        try:
            if not self.discount_contract:
                raise ValueError("Discount service not properly initialized")
            
            # Try cache first
            cache_key = f"discount_request_{request_id}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # Get from contract
            request_data = self.discount_contract.functions.getDiscountRequest(request_id).call()
            
            # Convert to dict
            result = {
                'request_id': request_data[0],
                'student': request_data[1],
                'teacher': request_data[2],
                'course_id': request_data[3],
                'course_price': request_data[4],
                'discount_percent': request_data[5],
                'teo_cost': request_data[6],
                'teacher_bonus': request_data[7],
                'created_at': datetime.fromtimestamp(request_data[8]),
                'deadline': datetime.fromtimestamp(request_data[9]),
                'status': request_data[10]
            }
            
            # Cache for future requests
            cache.set(cache_key, result, timeout=3600 * 24)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get discount request {request_id}: {e}")
            return None
    
    def get_student_requests(self, student_address: str) -> List[Dict]:
        """Get all discount requests for a student"""
        try:
            if not self.discount_contract:
                return []
            
            request_ids = self.discount_contract.functions.getStudentRequests(
                Web3.to_checksum_address(student_address)
            ).call()
            
            requests = []
            for request_id in request_ids:
                request_data = self.get_discount_request(request_id)
                if request_data:
                    requests.append(request_data)
            
            return requests
            
        except Exception as e:
            self.logger.error(f"Failed to get student requests for {student_address}: {e}")
            return []
    
    def get_teacher_requests(self, teacher_address: str) -> List[Dict]:
        """Get all discount requests for a teacher"""
        try:
            if not self.discount_contract:
                return []
            
            request_ids = self.discount_contract.functions.getTeacherRequests(
                Web3.to_checksum_address(teacher_address)
            ).call()
            
            requests = []
            for request_id in request_ids:
                request_data = self.get_discount_request(request_id)
                if request_data:
                    requests.append(request_data)
            
            return requests
            
        except Exception as e:
            self.logger.error(f"Failed to get teacher requests for {teacher_address}: {e}")
            return []
    
    def generate_student_signature_data(
        self, 
        student_address: str, 
        course_id: int, 
        teo_cost: int
    ) -> Dict:
        """
        Generate signature data for student to sign
        
        Args:
            student_address: Student's wallet address
            course_id: Course identifier
            teo_cost: TEO cost in wei
            
        Returns:
            Dict with message hash and signing data
        """
        if not self.discount_contract:
            raise ValueError("Discount service not properly initialized")
        
        # Create message hash (same as contract)
        message_hash = Web3.solidity_keccak(
            ['address', 'uint256', 'uint256', 'address'],
            [
                Web3.to_checksum_address(student_address),
                course_id,
                teo_cost,
                self.discount_contract.address
            ]
        )
        
        # Create signable message
        signable_message = encode_defunct(message_hash)
        
        return {
            'message_hash': message_hash.hex(),
            'signable_message': signable_message,
            'instructions': {
                'message': f"Approve TeoCoin discount request for Course #{course_id}",
                'cost': f"{teo_cost / 10**18:.4f} TEO",
                'note': "This signature allows the platform to execute the transfer on your behalf when the teacher approves."
            }
        }
    
    def calculate_teo_cost(self, course_price: Decimal, discount_percent: int) -> Tuple[int, int]:
        """
        Calculate TEO cost and teacher bonus
        
        Args:
            course_price: Course price in EUR
            discount_percent: Discount percentage
            
        Returns:
            Tuple of (teo_cost_wei, teacher_bonus_wei)
        """
        course_price_cents = int(course_price * 100)
        return self._calculate_teo_amounts(course_price_cents, discount_percent)
    
    # ========== PRIVATE METHODS ==========
    
    def _validate_discount_request(
        self,
        student_address: str,
        teacher_address: str,
        course_id: int,
        course_price: Decimal,
        discount_percent: int
    ):
        """Validate discount request parameters"""
        if not Web3.is_address(student_address):
            raise ValueError("Invalid student address")
        
        if not Web3.is_address(teacher_address):
            raise ValueError("Invalid teacher address")
        
        if student_address.lower() == teacher_address.lower():
            raise ValueError("Student and teacher cannot be the same")
        
        if course_id <= 0:
            raise ValueError("Invalid course ID")
        
        if course_price <= 0:
            raise ValueError("Course price must be positive")
        
        if discount_percent < 5 or discount_percent > self.MAX_DISCOUNT_PERCENT:
            raise ValueError(f"Discount percent must be between 5 and {self.MAX_DISCOUNT_PERCENT}")
    
    def _calculate_teo_amounts(self, course_price_cents: int, discount_percent: int) -> Tuple[int, int]:
        """
        Calculate TEO cost and teacher bonus in wei
        
        Note: The contract's calculateTeoCost function has a bug where it doesn't
        multiply by 1e18 to convert to wei. We compensate for this here.
        """
        discount_value_cents = (course_price_cents * discount_percent) // 100
        teo_cost_float = (discount_value_cents * self.TEO_TO_EUR_RATE) / 100
        
        # Convert to wei (18 decimals) and compensate for contract bug
        teo_cost_wei = int(teo_cost_float * 10**18)
        teacher_bonus_wei = (teo_cost_wei * self.TEACHER_BONUS_PERCENT) // 100
        
        return teo_cost_wei, teacher_bonus_wei
    
    def _execute_platform_transaction(self, function_call) -> bytes:
        """Execute transaction with platform account paying gas"""
        try:
            if not self.platform_account:
                raise ValueError("Platform account not initialized")
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': self.platform_account.address,
                'nonce': self.w3.eth.get_transaction_count(self.platform_account.address),
                'gas': 500000,  # Reasonable gas limit
                'gasPrice': self.w3.eth.gas_price,
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, 
                private_key=self.platform_account.key
            )
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            self.logger.info(f"Platform transaction sent: {tx_hash.hex()}")
            return tx_hash
            
        except Exception as e:
            self.logger.error(f"Failed to execute platform transaction: {e}")
            raise
    
    def _extract_request_id_from_receipt(self, receipt) -> int:
        """Extract request ID from transaction receipt"""
        try:
            if not self.discount_contract:
                raise ValueError("Discount contract not initialized")
            
            # Get DiscountRequested event logs
            event_logs = self.discount_contract.events.DiscountRequested().process_receipt(receipt)
            if event_logs:
                return event_logs[0]['args']['requestId']
            else:
                raise ValueError("No DiscountRequested event found in transaction receipt")
        except Exception as e:
            self.logger.error(f"Failed to extract request ID from receipt: {e}")
            raise


# Singleton instance
teocoin_discount_service = TeoCoinDiscountService()
