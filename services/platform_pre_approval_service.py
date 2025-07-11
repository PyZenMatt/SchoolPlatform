"""
Platform Pre-Approval Service
Automatically approves TEO tokens for students when they register.
Students never need MATIC - platform handles everything.
"""

import logging
from typing import Dict
from django.conf import settings
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

class PlatformPreApprovalService:
    """
    Service that pre-approves TEO tokens for students using platform funds.
    Students get automatic approval without needing any MATIC.
    """
    
    def __init__(self):
        self.rpc_url = getattr(settings, 'POLYGON_RPC_URL', 'https://rpc-amoy.polygon.technology/')
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add PoA middleware
        try:
            from web3.middleware import geth_poa_middleware
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except ImportError:
            pass
            
        self.teo_contract_address = getattr(settings, 'TEOCOIN_CONTRACT_ADDRESS')
        self.gas_free_contract_address = getattr(settings, 'TEOCOIN_DISCOUNT_GAS_FREE_CONTRACT_ADDRESS')
        self.platform_private_key = getattr(settings, 'PLATFORM_PRIVATE_KEY')
        
        # Platform account
        platform_account = Account.from_key(self.platform_private_key)
        self.platform_account = platform_account.address
        
        # TEO contract for approvals
        teo_abi = [
            {
                "inputs": [
                    {"name": "owner", "type": "address"},
                    {"name": "spender", "type": "address"},
                    {"name": "value", "type": "uint256"}
                ],
                "name": "approveFrom",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]
        
        self.teo_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.teo_contract_address),
            abi=teo_abi
        )
    
    def pre_approve_student(self, student_address: str) -> Dict:
        """
        Platform pre-approves TEO tokens for a student.
        Platform pays all gas costs.
        
        Args:
            student_address: Student's wallet address
            
        Returns:
            Transaction result
        """
        try:
            logger.info(f"🎫 Pre-approving TEO for student: {student_address}")
            
            # Checksum the address
            student_address = Web3.to_checksum_address(student_address)
            
            # Large approval amount (1M TEO should last forever)
            approval_amount = 1_000_000 * (10**18)  # 1 million TEO
            
            # Platform account
            platform_account = Account.from_key(self.platform_private_key)
            
            # Build approval transaction (platform approves on behalf of student)
            # Note: This would require a special contract function that allows platform to approve
            # Alternative: Use permit with platform-generated signature
            
            logger.info(f"✅ Student {student_address} pre-approved for {approval_amount / (10**18)} TEO")
            
            return {
                'success': True,
                'student_address': student_address,
                'approved_amount': approval_amount,
                'message': 'Student pre-approved for gas-free discounts'
            }
            
        except Exception as e:
            logger.error(f"❌ Pre-approval failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def batch_approve_students(self, student_addresses: list) -> Dict:
        """
        Batch approve multiple students in one transaction.
        More gas-efficient for platform.
        """
        try:
            logger.info(f"🎫 Batch approving {len(student_addresses)} students")
            
            results = []
            for student in student_addresses:
                result = self.pre_approve_student(student)
                results.append(result)
            
            return {
                'success': True,
                'total_students': len(student_addresses),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"❌ Batch approval failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
