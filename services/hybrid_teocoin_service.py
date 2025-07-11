"""
Hybrid TeoCoin Service
Provides a unified interface that can use either blockchain or DB operations
for TeoCoin transactions, making migration seamless.
"""

from decimal import Decimal
from typing import Dict, Optional, List, Any, Union
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
import logging

from services.db_teocoin_service import db_teocoin_service
from services.blockchain_service import blockchain_service

User = get_user_model()
logger = logging.getLogger(__name__)


class HybridTeoCoinService:
    """
    Unified TeoCoin service that can switch between DB and blockchain operations.
    Provides backward compatibility while enabling the new DB-based system.
    """
    
    def __init__(self):
        # Configuration flag to determine which system to use
        self.use_db_system = getattr(settings, 'USE_DB_TEOCOIN_SYSTEM', True)
        self.db_service = db_teocoin_service
        self.blockchain_service = blockchain_service
        
        logger.info(f"HybridTeoCoinService initialized - Using {'DB' if self.use_db_system else 'Blockchain'} system")
    
    # ========== BALANCE OPERATIONS ==========
    
    def get_user_balance(self, user: User) -> Dict[str, Any]:
        """
        Get user's TeoCoin balance from appropriate system
        
        Returns:
            Dict with balance information compatible with existing code
        """
        if self.use_db_system:
            balance_data = self.db_service.get_user_balance(user)
            # Convert to format expected by existing code
            return {
                'balance': balance_data['total_balance'],
                'available_balance': balance_data['available_balance'],
                'staked_balance': balance_data['staked_balance'],
                'pending_withdrawal': balance_data['pending_withdrawal'],
                'total_balance': balance_data['total_balance'],
                'source': 'database'
            }
        else:
            # Use existing blockchain service
            try:
                wallet_balance = self.blockchain_service.get_user_wallet_balance(user)
                return {
                    'balance': wallet_balance.get('balance', Decimal('0.00')),
                    'available_balance': wallet_balance.get('balance', Decimal('0.00')),
                    'staked_balance': Decimal('0.00'),  # Blockchain doesn't track staking
                    'pending_withdrawal': Decimal('0.00'),
                    'total_balance': wallet_balance.get('balance', Decimal('0.00')),
                    'source': 'blockchain'
                }
            except Exception as e:
                logger.error(f"Error getting blockchain balance for {user.email}: {e}")
                return {
                    'balance': Decimal('0.00'),
                    'available_balance': Decimal('0.00'),
                    'staked_balance': Decimal('0.00'),
                    'pending_withdrawal': Decimal('0.00'),
                    'total_balance': Decimal('0.00'),
                    'source': 'error'
                }
    
    def get_available_balance(self, user: User) -> Decimal:
        """Get user's available balance for spending"""
        balance_data = self.get_user_balance(user)
        return balance_data['available_balance']
    
    # ========== CREDIT/DEBIT OPERATIONS ==========
    
    def credit_user(self, user: User, amount: Union[Decimal, float, str], 
                   reason: str = "Credit", course_id: Optional[str] = None,
                   related_user: Optional[User] = None) -> Dict[str, Any]:
        """
        Add TeoCoin to user's balance
        
        Args:
            user: User to credit
            amount: Amount to credit
            reason: Description of the transaction
            course_id: Optional course ID
            related_user: Optional related user (e.g., in teacher-student transactions)
            
        Returns:
            Dict with success status and new balance
        """
        amount_decimal = Decimal(str(amount))
        
        if self.use_db_system:
            success = self.db_service.add_balance(
                user=user,
                amount=amount_decimal,
                transaction_type='earned',
                description=reason,
                course_id=course_id
            )
            
            if success:
                new_balance = self.get_available_balance(user)
                return {
                    'success': True,
                    'new_balance': new_balance,
                    'amount_credited': amount_decimal,
                    'transaction_type': 'credit',
                    'source': 'database'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to credit user in DB system',
                    'source': 'database'
                }
        else:
            # Use blockchain service
            try:
                result = self.blockchain_service.mint_tokens_to_user(
                    user=user,
                    amount=amount_decimal,
                    reason=reason
                )
                return {
                    'success': result.get('success', False),
                    'new_balance': result.get('new_balance', Decimal('0.00')),
                    'amount_credited': amount_decimal,
                    'transaction_type': 'credit',
                    'tx_hash': result.get('tx_hash'),
                    'source': 'blockchain'
                }
            except Exception as e:
                logger.error(f"Error crediting user {user.email} via blockchain: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'source': 'blockchain'
                }
    
    def debit_user(self, user: User, amount: Union[Decimal, float, str],
                  reason: str = "Debit", course_id: Optional[str] = None,
                  related_user: Optional[User] = None) -> Dict[str, Any]:
        """
        Deduct TeoCoin from user's balance
        
        Args:
            user: User to debit
            amount: Amount to deduct
            reason: Description of the transaction
            course_id: Optional course ID
            related_user: Optional related user
            
        Returns:
            Dict with success status and new balance
        """
        amount_decimal = Decimal(str(amount))
        
        if self.use_db_system:
            success = self.db_service.deduct_balance(
                user=user,
                amount=amount_decimal,
                transaction_type='spent_discount',
                description=reason,
                course_id=course_id
            )
            
            if success:
                new_balance = self.get_available_balance(user)
                return {
                    'success': True,
                    'new_balance': new_balance,
                    'amount_debited': amount_decimal,
                    'transaction_type': 'debit',
                    'source': 'database'
                }
            else:
                return {
                    'success': False,
                    'error': 'Insufficient balance or debit failed',
                    'source': 'database'
                }
        else:
            # For blockchain system, we can't easily debit unless we implement transfers
            # This would require the platform to hold tokens and transfer them
            logger.warning(f"Debit operation not implemented for blockchain system")
            return {
                'success': False,
                'error': 'Debit operations not supported in blockchain mode',
                'source': 'blockchain'
            }
    
    # ========== DISCOUNT SYSTEM ==========
    
    def calculate_discount(self, user: User, course_price: Decimal) -> Dict[str, Any]:
        """
        Calculate TeoCoin discount for a course purchase
        
        Args:
            user: User purchasing course
            course_price: Original course price in EUR
            
        Returns:
            Dict with discount calculation details
        """
        if self.use_db_system:
            return self.db_service.calculate_discount(user, course_price)
        else:
            # Simplified discount calculation for blockchain system
            available_balance = self.get_available_balance(user)
            max_discount = course_price * Decimal('0.5')  # 50% max
            
            discount_amount = min(available_balance, max_discount)
            final_price = course_price - discount_amount
            
            return {
                'discount_amount': discount_amount,
                'final_price': final_price,
                'teo_required': discount_amount,
                'discount_percentage': (discount_amount / course_price * 100) if course_price > 0 else Decimal('0'),
                'source': 'blockchain'
            }
    
    def apply_course_discount(self, user: User, course_price: Decimal,
                            course_id: str, course_title: str = "") -> Dict[str, Any]:
        """
        Apply TeoCoin discount to a course purchase
        
        Args:
            user: User purchasing course
            course_price: Original course price
            course_id: Course identifier
            course_title: Course title for description
            
        Returns:
            Dict with discount application results
        """
        if self.use_db_system:
            return self.db_service.apply_course_discount(
                user=user,
                course_price=course_price,
                course_id=course_id,
                course_title=course_title
            )
        else:
            # For blockchain system, calculate and attempt debit
            discount_info = self.calculate_discount(user, course_price)
            teo_required = discount_info['teo_required']
            
            if teo_required == 0:
                return {
                    'success': True,
                    'discount_applied': Decimal('0.00'),
                    'final_price': course_price,
                    'message': 'No TeoCoin available for discount',
                    'source': 'blockchain'
                }
            
            # In blockchain mode, we'd need to implement transfer logic
            # For now, return calculation only
            return {
                'success': True,
                'discount_applied': discount_info['discount_amount'],
                'final_price': discount_info['final_price'],
                'teo_required': teo_required,
                'message': f'Discount calculated: {discount_info["discount_percentage"]:.1f}%',
                'note': 'Blockchain debit not implemented - calculation only',
                'source': 'blockchain'
            }
    
    # ========== STAKING OPERATIONS ==========
    
    def stake_tokens(self, user: User, amount: Union[Decimal, float, str]) -> Dict[str, Any]:
        """
        Stake TeoCoin tokens
        
        Args:
            user: User staking tokens
            amount: Amount to stake
            
        Returns:
            Dict with staking results
        """
        amount_decimal = Decimal(str(amount))
        
        if self.use_db_system:
            success = self.db_service.stake_tokens(user, amount_decimal)
            
            if success:
                balance_data = self.get_user_balance(user)
                return {
                    'success': True,
                    'staked_amount': amount_decimal,
                    'total_staked': balance_data['staked_balance'],
                    'available_balance': balance_data['available_balance'],
                    'source': 'database'
                }
            else:
                return {
                    'success': False,
                    'error': 'Insufficient balance for staking',
                    'source': 'database'
                }
        else:
            # Staking not supported in blockchain mode
            return {
                'success': False,
                'error': 'Staking not supported in blockchain mode',
                'source': 'blockchain'
            }
    
    def unstake_tokens(self, user: User, amount: Union[Decimal, float, str]) -> Dict[str, Any]:
        """
        Unstake TeoCoin tokens
        
        Args:
            user: User unstaking tokens
            amount: Amount to unstake
            
        Returns:
            Dict with unstaking results
        """
        amount_decimal = Decimal(str(amount))
        
        if self.use_db_system:
            success = self.db_service.unstake_tokens(user, amount_decimal)
            
            if success:
                balance_data = self.get_user_balance(user)
                return {
                    'success': True,
                    'unstaked_amount': amount_decimal,
                    'total_staked': balance_data['staked_balance'],
                    'available_balance': balance_data['available_balance'],
                    'source': 'database'
                }
            else:
                return {
                    'success': False,
                    'error': 'Insufficient staked balance',
                    'source': 'database'
                }
        else:
            # Unstaking not supported in blockchain mode
            return {
                'success': False,
                'error': 'Unstaking not supported in blockchain mode',
                'source': 'blockchain'
            }
    
    # ========== WITHDRAWAL OPERATIONS ==========
    
    def request_withdrawal(self, user: User, amount: Union[Decimal, float, str],
                          metamask_address: str) -> Dict[str, Any]:
        """
        Request withdrawal to MetaMask wallet
        
        Args:
            user: User requesting withdrawal
            amount: Amount to withdraw
            metamask_address: User's MetaMask wallet address
            
        Returns:
            Dict with withdrawal request results
        """
        amount_decimal = Decimal(str(amount))
        
        if self.use_db_system:
            return self.db_service.request_withdrawal(
                user=user,
                amount=amount_decimal,
                metamask_address=metamask_address
            )
        else:
            # In blockchain mode, user already has tokens
            return {
                'success': False,
                'error': 'Withdrawal not needed in blockchain mode - tokens already in wallet',
                'source': 'blockchain'
            }
    
    # ========== TRANSACTION HISTORY ==========
    
    def get_user_transactions(self, user: User, limit: int = 50) -> List[Dict]:
        """
        Get user's transaction history
        
        Args:
            user: User to get transactions for
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction dictionaries
        """
        if self.use_db_system:
            return self.db_service.get_user_transactions(user, limit)
        else:
            # Use blockchain service transaction history
            try:
                blockchain_txs = self.blockchain_service.get_user_transaction_history(user)
                # Convert to standard format
                return [
                    {
                        'id': tx.get('id', ''),
                        'type': tx.get('type', 'unknown'),
                        'amount': tx.get('amount', Decimal('0.00')),
                        'description': tx.get('description', ''),
                        'created_at': tx.get('timestamp'),
                        'source': 'blockchain'
                    }
                    for tx in blockchain_txs[:limit]
                ]
            except Exception as e:
                logger.error(f"Error getting blockchain transactions for {user.email}: {e}")
                return []
    
    # ========== TEACHER REWARDS ==========
    
    def reward_teacher_lesson_completion(self, teacher: User, student: User,
                                       lesson_reward: Decimal = Decimal('1.0')) -> Dict[str, Any]:
        """
        Reward teacher when student completes a lesson
        
        Args:
            teacher: Teacher to reward
            student: Student who completed lesson
            lesson_reward: Base reward amount
            
        Returns:
            Dict with reward results
        """
        if self.use_db_system:
            success = self.db_service.reward_teacher_lesson_completion(
                teacher=teacher,
                student=student,
                lesson_reward=lesson_reward
            )
            
            return {
                'success': success,
                'teacher_reward': lesson_reward,
                'source': 'database'
            }
        else:
            # Use blockchain service to mint tokens to teacher
            try:
                result = self.blockchain_service.mint_tokens_to_user(
                    user=teacher,
                    amount=lesson_reward,
                    reason=f"Lesson completion reward (student: {student.username})"
                )
                return {
                    'success': result.get('success', False),
                    'teacher_reward': lesson_reward,
                    'tx_hash': result.get('tx_hash'),
                    'source': 'blockchain'
                }
            except Exception as e:
                logger.error(f"Error rewarding teacher {teacher.email}: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'source': 'blockchain'
                }
    
    # ========== ADMIN/PLATFORM OPERATIONS ==========
    
    def get_platform_statistics(self) -> Dict[str, Any]:
        """
        Get platform-wide TeoCoin statistics
        
        Returns:
            Dict with platform statistics
        """
        if self.use_db_system:
            return self.db_service.get_platform_statistics()
        else:
            # Blockchain statistics would require querying all user wallets
            return {
                'total_users_with_balance': 0,
                'total_available_balance': Decimal('0.00'),
                'total_staked_balance': Decimal('0.00'),
                'total_pending_withdrawal': Decimal('0.00'),
                'total_transactions': 0,
                'pending_withdrawal_requests': 0,
                'note': 'Statistics not available in blockchain mode',
                'source': 'blockchain'
            }
    
    # ========== MIGRATION UTILITIES ==========
    
    def migrate_user_to_db_system(self, user: User) -> Dict[str, Any]:
        """
        Migrate a user's blockchain balance to DB system
        
        Args:
            user: User to migrate
            
        Returns:
            Dict with migration results
        """
        if self.use_db_system:
            return {'success': False, 'error': 'Already using DB system'}
        
        try:
            # Get blockchain balance
            blockchain_balance_data = self.blockchain_service.get_user_wallet_balance(user)
            blockchain_balance = blockchain_balance_data.get('balance', Decimal('0.00'))
            
            if blockchain_balance > 0:
                # Credit to DB system
                success = self.db_service.add_balance(
                    user=user,
                    amount=blockchain_balance,
                    transaction_type='deposit',
                    description="Migrated from blockchain balance"
                )
                
                if success:
                    return {
                        'success': True,
                        'migrated_amount': blockchain_balance,
                        'message': f'Migrated {blockchain_balance} TEO from blockchain to DB'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Failed to credit DB balance during migration'
                    }
            else:
                return {
                    'success': True,
                    'migrated_amount': Decimal('0.00'),
                    'message': 'No balance to migrate'
                }
                
        except Exception as e:
            logger.error(f"Error migrating user {user.email}: {e}")
            return {
                'success': False,
                'error': f'Migration failed: {str(e)}'
            }


# Singleton instance
hybrid_teocoin_service = HybridTeoCoinService()
