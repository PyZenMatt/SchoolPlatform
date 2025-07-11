"""
PHASE 4.1: Gas Treasury Service
Manages platform gas payments for Layer 2 operations
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from django.conf import settings
from web3 import Web3
from blockchain.blockchain import TeoCoinService

logger = logging.getLogger(__name__)


class GasTreasuryService:
    """
    Service for managing platform gas treasury for Layer 2 operations
    
    This service ensures the platform always has sufficient MATIC to pay
    gas fees for student transactions in the Layer 2 system.
    """
    
    def __init__(self):
        """Initialize gas treasury service"""
        self.blockchain_service = TeoCoinService()
        
        # Gas treasury configuration
        self.min_balance = Decimal(str(getattr(settings, 'GAS_TREASURY_MIN_BALANCE', '1.0')))  # Minimum 1 MATIC
        self.refill_amount = Decimal(str(getattr(settings, 'GAS_TREASURY_REFILL_AMOUNT', '5.0')))  # Refill to 5 MATIC
        self.low_balance_threshold = Decimal(str(getattr(settings, 'GAS_TREASURY_LOW_THRESHOLD', '2.0')))  # Warning at 2 MATIC
        
        # Gas cost estimates (in MATIC)
        self.gas_costs = {
            'teocoin_transfer': Decimal('0.002'),      # ~$0.002 per transfer
            'staking_operation': Decimal('0.008'),     # ~$0.008 per stake/unstake
            'discount_permit': Decimal('0.004'),       # ~$0.004 per permit operation
            'emergency_buffer': Decimal('0.010')       # Emergency buffer per operation
        }
    
    def get_treasury_balance(self) -> Decimal:
        """
        Get current MATIC balance of the reward pool (gas treasury)
        
        Returns:
            Current MATIC balance as Decimal
        """
        try:
            balance_wei = self.blockchain_service.get_reward_pool_matic_balance()
            balance_matic = Decimal(str(balance_wei))
            
            logger.info(f"Gas treasury balance: {balance_matic} MATIC")
            return balance_matic
            
        except Exception as e:
            logger.error(f"Failed to get treasury balance: {e}")
            return Decimal('0')
    
    def check_balance_sufficient(self, operation_type: str, quantity: int = 1) -> tuple[bool, str]:
        """
        Check if treasury has sufficient balance for operations
        
        Args:
            operation_type: Type of operation ('teocoin_transfer', 'staking_operation', etc.)
            quantity: Number of operations planned
            
        Returns:
            (sufficient, message)
        """
        try:
            current_balance = self.get_treasury_balance()
            estimated_cost = self.estimate_gas_cost(operation_type, quantity)
            
            if current_balance >= estimated_cost + self.min_balance:
                return True, f"Sufficient balance: {current_balance} MATIC"
            else:
                needed = estimated_cost + self.min_balance - current_balance
                return False, f"Insufficient balance. Need {needed} more MATIC"
                
        except Exception as e:
            logger.error(f"Balance check failed: {e}")
            return False, f"Balance check error: {str(e)}"
    
    def estimate_gas_cost(self, operation_type: str, quantity: int = 1) -> Decimal:
        """
        Estimate gas cost for operations
        
        Args:
            operation_type: Type of operation
            quantity: Number of operations
            
        Returns:
            Estimated cost in MATIC
        """
        base_cost = self.gas_costs.get(operation_type, self.gas_costs['emergency_buffer'])
        emergency_buffer = self.gas_costs['emergency_buffer']
        
        total_cost = (base_cost + emergency_buffer) * quantity
        
        logger.debug(f"Estimated gas cost for {quantity}x {operation_type}: {total_cost} MATIC")
        return total_cost
    
    def pay_gas_for_student(self, operation_type: str, student_address: str, operation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Platform pays gas for student transaction
        
        Args:
            operation_type: Type of operation ('teocoin_transfer', 'staking_operation', etc.)
            student_address: Student's wallet address
            operation_data: Operation-specific data
            
        Returns:
            Result dictionary with transaction info
        """
        try:
            # Check if we have sufficient balance
            sufficient, message = self.check_balance_sufficient(operation_type)
            
            if not sufficient:
                logger.warning(f"Insufficient gas treasury balance: {message}")
                
                # Attempt auto-refill
                if self.auto_refill_treasury():
                    logger.info("Treasury auto-refilled successfully")
                else:
                    return {
                        'success': False,
                        'error': 'Insufficient gas treasury balance and auto-refill failed',
                        'balance_info': message
                    }
            
            # Execute the sponsored transaction
            result = self.execute_sponsored_transaction(operation_type, student_address, operation_data)
            
            if result and result.get('success'):
                # Log successful gas payment
                gas_cost = self.estimate_gas_cost(operation_type)
                logger.info(f"Platform paid {gas_cost} MATIC gas for student {student_address}")
                
                return {
                    'success': True,
                    'transaction_hash': result.get('tx_hash'),
                    'gas_paid_by_platform': str(gas_cost),
                    'student_gas_cost': '0 MATIC (Gas-free!)',
                    'operation_type': operation_type
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Transaction execution failed')
                }
                
        except Exception as e:
            logger.error(f"Gas payment failed for {operation_type}: {e}")
            return {
                'success': False,
                'error': f"Gas payment error: {str(e)}"
            }
    
    def execute_sponsored_transaction(self, operation_type: str, student_address: str, operation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute blockchain transaction with platform paying gas
        
        Args:
            operation_type: Type of operation
            student_address: Student's address
            operation_data: Operation-specific data
            
        Returns:
            Transaction result
        """
        try:
            if operation_type == 'teocoin_transfer':
                # Platform pays gas for TEO transfer
                tx_hash = self.blockchain_service.transfer_with_reward_pool_gas(
                    from_address=student_address,
                    to_address=operation_data.get('to_address'),
                    amount=Decimal(str(operation_data.get('amount')))
                )
                
                if tx_hash:
                    return {
                        'success': True,
                        'tx_hash': tx_hash,
                        'operation': 'teocoin_transfer'
                    }
            
            elif operation_type == 'staking_operation':
                # Handle staking operations (stake/unstake)
                # This would integrate with the gas-free staking service
                pass
            
            elif operation_type == 'discount_permit':
                # Handle discount permit operations
                # This would integrate with the gas-free discount service
                pass
            
            return {
                'success': False,
                'error': f'Unsupported operation type: {operation_type}'
            }
            
        except Exception as e:
            logger.error(f"Sponsored transaction execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def auto_refill_treasury(self) -> bool:
        """
        Automatically refill gas treasury when low
        
        Returns:
            True if refill successful, False otherwise
        """
        try:
            current_balance = self.get_treasury_balance()
            
            if current_balance >= self.min_balance:
                logger.info(f"Treasury balance sufficient: {current_balance} MATIC")
                return True
            
            logger.warning(f"Treasury balance low: {current_balance} MATIC. Attempting refill...")
            
            # In a production environment, this would:
            # 1. Transfer MATIC from main treasury account
            # 2. Or trigger automated purchase of MATIC
            # 3. Or send alerts to administrators
            
            # For now, log the requirement
            needed_amount = self.refill_amount - current_balance
            logger.critical(f"TREASURY REFILL NEEDED: {needed_amount} MATIC required")
            
            # Return False to indicate manual intervention needed
            return False
            
        except Exception as e:
            logger.error(f"Auto-refill failed: {e}")
            return False
    
    def get_treasury_status(self) -> Dict[str, Any]:
        """
        Get comprehensive treasury status
        
        Returns:
            Treasury status information
        """
        try:
            current_balance = self.get_treasury_balance()
            
            # Calculate capacity (how many operations we can support)
            capacity = {}
            for operation_type, cost in self.gas_costs.items():
                if operation_type != 'emergency_buffer':
                    max_operations = int((current_balance - self.min_balance) / (cost + self.gas_costs['emergency_buffer']))
                    capacity[operation_type] = max(0, max_operations)
            
            # Determine status
            if current_balance >= self.low_balance_threshold:
                status = 'healthy'
            elif current_balance >= self.min_balance:
                status = 'low'
            else:
                status = 'critical'
            
            return {
                'status': status,
                'current_balance': str(current_balance),
                'min_balance': str(self.min_balance),
                'low_threshold': str(self.low_balance_threshold),
                'capacity': capacity,
                'requires_refill': current_balance < self.min_balance,
                'estimated_costs': {k: str(v) for k, v in self.gas_costs.items()}
            }
            
        except Exception as e:
            logger.error(f"Treasury status check failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# Global instance
gas_treasury_service = GasTreasuryService()
