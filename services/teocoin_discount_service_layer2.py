"""
TeoCoin Discount Service - TRUE Layer 2 Gas-Free Implementation

This service implements the proper Layer 2 architecture where:
1. Students request discounts without paying ANY gas fees
2. Reward pool handles ALL gas payments and TEO transfers  
3. Students only need to approve reward pool ONCE
4. No smart contract escrow - direct Layer 2 transfers
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
from notifications.services import teocoin_notification_service
from users.models import User


class DiscountStatus(Enum):
    PENDING = 0
    APPROVED = 1
    DECLINED = 2
    EXPIRED = 3


@dataclass
class Layer2DiscountRequest:
    """Layer 2 discount request data structure"""
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
    teo_transfer_hash: str
    decline_reason: Optional[str] = None


class TeoCoinLayer2DiscountService:
    """Service for handling TRUE Layer 2 gas-free TeoCoin discount system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.teocoin_service = TeoCoinService()
        
        # Configuration
        self.REQUEST_TIMEOUT_HOURS = 2
        self.TEACHER_BONUS_PERCENT = 25
        self.MAX_DISCOUNT_PERCENT = 15
        
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
        Create a new discount request using Layer 2 gas-free architecture
        
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
            
            # Check balances
            student_balance_wei = self.teocoin_service.contract.functions.balanceOf(
                Web3.to_checksum_address(student_address)
            ).call()
            
            if student_balance_wei < teo_cost:
                raise ValueError(f"Insufficient TEO balance. Required: {teo_cost / 10**18:.2f}, Available: {student_balance_wei / 10**18:.2f}")
            
            # Verify reward pool has sufficient balance for bonus
            reward_pool_balance = self.teocoin_service.get_reward_pool_balance()
            if reward_pool_balance < Decimal(str(teacher_bonus / 10**18)):
                raise ValueError(f"Insufficient reward pool balance for teacher bonus")
            
            # *** LAYER 2 GAS-FREE TRANSFER ***
            # Use reward pool to transfer TEO from student to platform escrow
            # Student pays ZERO gas - reward pool handles everything!
            self.logger.info(f"🚀 LAYER 2: Transferring {teo_cost / 10**18:.2f} TEO from student via reward pool")
            self.logger.info(f"✅ Student pays ZERO gas fees!")
            
            try:
                # Create platform escrow address for this request
                escrow_address = self.teocoin_service.reward_pool_address  # Use reward pool as escrow
                
                # Use Layer 2 gas-free transfer - reward pool pays all gas
                layer2_transfer_result = self.teocoin_service.transfer_with_reward_pool_gas(
                    from_address=student_address,
                    to_address=escrow_address,
                    amount=Decimal(str(teo_cost / 10**18))
                )
                
                if not layer2_transfer_result:
                    raise ValueError("Layer 2 TEO transfer failed")
                
                self.logger.info(f"✅ LAYER 2 SUCCESS: TEO transferred via reward pool: {layer2_transfer_result}")
                
            except Exception as layer2_error:
                self.logger.error(f"❌ Layer 2 transfer failed: {layer2_error}")
                # Check if it's an allowance issue
                if "allowance" in str(layer2_error).lower():
                    raise ValueError(f"Student must first approve reward pool for TEO transfers. Please approve at least {teo_cost / 10**18:.2f} TEO to the reward pool address.")
                else:
                    raise ValueError(f"Layer 2 transfer failed: {layer2_error}")
            
            # Create platform-managed discount request (no smart contract needed)
            request_id = self._create_platform_discount_request(
                student_address, teacher_address, course_id, 
                course_price_cents, discount_percent, teo_cost, 
                teacher_bonus, layer2_transfer_result
            )
            
            # Create response
            result = {
                'success': True,
                'request_id': request_id,
                'teo_transfer_hash': layer2_transfer_result,
                'student': student_address,
                'teacher': teacher_address,
                'course_id': course_id,
                'course_price': float(course_price),
                'discount_percent': discount_percent,
                'teo_cost': teo_cost,
                'teacher_bonus': teacher_bonus,
                'deadline': timezone.now() + timedelta(hours=self.REQUEST_TIMEOUT_HOURS),
                'layer2_enabled': True,
                'gas_free': True
            }
            
            # Cache request for quick access
            cache_key = f"layer2_discount_request_{request_id}"
            cache.set(cache_key, result, timeout=3600 * 24)  # 24 hours
            
            # Send notification to teacher
            self._send_teacher_notification(
                student_address, teacher_address, course_id, 
                discount_percent, teo_cost, teacher_bonus, request_id, result['deadline']
            )
            
            self.logger.info(f"✅ Layer 2 discount request created: {request_id} for student {student_address}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create Layer 2 discount request: {e}")
            return {
                'success': False,
                'error': str(e),
                'layer2_enabled': False
            }
    
    def _create_platform_discount_request(
        self, 
        student_address: str, 
        teacher_address: str, 
        course_id: int,
        course_price_cents: int, 
        discount_percent: int, 
        teo_cost: int,
        teacher_bonus: int, 
        teo_transfer_hash: str
    ) -> int:
        """Create a platform-managed discount request without smart contract"""
        
        # Generate unique request ID based on timestamp and hash
        import time
        import hashlib
        
        timestamp = int(time.time())
        hash_input = f"{student_address}{teacher_address}{course_id}{timestamp}"
        request_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8]
        request_id = int(request_hash, 16) % 1000000  # Keep it under 1 million
        
        # Store in cache/database
        request_data = {
            'request_id': request_id,
            'student': student_address,
            'teacher': teacher_address,
            'course_id': course_id,
            'course_price': course_price_cents,
            'discount_percent': discount_percent,
            'teo_cost': teo_cost,
            'teacher_bonus': teacher_bonus,
            'created_at': timezone.now(),
            'deadline': timezone.now() + timedelta(hours=self.REQUEST_TIMEOUT_HOURS),
            'status': DiscountStatus.PENDING.value,
            'teo_transfer_hash': teo_transfer_hash,
            'layer2': True
        }
        
        cache_key = f"layer2_discount_request_{request_id}"
        cache.set(cache_key, request_data, timeout=3600 * 48)  # 48 hours
        
        self.logger.info(f"📝 Platform discount request created: {request_id}")
        return request_id
    
    def approve_discount_request(self, request_id: int, approver_address: str) -> Dict:
        """Approve Layer 2 discount request and send teacher bonus"""
        try:
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
            
            # Send teacher bonus from reward pool (gas-free)
            bonus_transfer_result = self.teocoin_service.transfer_from_reward_pool(
                request_data['teacher'],
                Decimal(str(request_data['teacher_bonus'] / 10**18))
            )
            
            if not bonus_transfer_result:
                raise ValueError("Failed to send teacher bonus")
            
            # Update request status
            cache_key = f"layer2_discount_request_{request_id}"
            request_data['status'] = DiscountStatus.APPROVED.value
            request_data['bonus_transfer_hash'] = bonus_transfer_result
            cache.set(cache_key, request_data, timeout=3600 * 48)
            
            result = {
                'success': True,
                'request_id': request_id,
                'bonus_transfer_hash': bonus_transfer_result,
                'teo_transferred': request_data['teo_cost'],
                'teacher_bonus': request_data['teacher_bonus'],
                'layer2_enabled': True
            }
            
            # Send notifications
            self._send_approval_notifications(request_data)
            
            self.logger.info(f"✅ Layer 2 discount request {request_id} approved successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to approve Layer 2 discount request {request_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_discount_request(self, request_id: int) -> Optional[Dict]:
        """Get Layer 2 discount request details"""
        try:
            cache_key = f"layer2_discount_request_{request_id}"
            request_data = cache.get(cache_key)
            
            if request_data:
                return request_data
            
            self.logger.warning(f"Layer 2 discount request {request_id} not found in cache")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get Layer 2 discount request {request_id}: {e}")
            return None
    
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
        """Calculate TEO cost and teacher bonus in wei"""
        # Use integer division exactly like Solidity
        discount_value_cents = (course_price_cents * discount_percent) // 100
        
        # SIMPLIFIED: 1 TEO per 1 EUR of discount (rounded up to nearest whole TEO)
        teo_cost_tokens = max(1, round(discount_value_cents / 100))  # At least 1 TEO
        teo_cost_wei = teo_cost_tokens * 10**18
        teacher_bonus_wei = (teo_cost_wei * self.TEACHER_BONUS_PERCENT) // 100
        
        self.logger.info(f"💰 TEO calculation: {teo_cost_wei / 10**18:.0f} TEO for €{discount_value_cents/100:.2f} discount")
        
        return teo_cost_wei, teacher_bonus_wei
    
    def _send_teacher_notification(
        self, 
        student_address: str, 
        teacher_address: str, 
        course_id: int,
        discount_percent: int, 
        teo_cost: int, 
        teacher_bonus: int, 
        request_id: int, 
        deadline: datetime
    ):
        """Send notification to teacher about new discount request"""
        try:
            student_user = User.objects.filter(wallet_address__iexact=student_address).first()
            teacher_user = User.objects.filter(wallet_address__iexact=teacher_address).first()
            
            if student_user and teacher_user:
                course_title = f"Course #{course_id}"
                try:
                    from courses.models import Course
                    course = Course.objects.get(id=course_id)
                    course_title = course.title
                except:
                    pass
                
                notification_sent = teocoin_notification_service.notify_teacher_discount_pending(
                    teacher=teacher_user,
                    student=student_user,
                    course_title=course_title,
                    discount_percent=discount_percent,
                    teo_cost=teo_cost / 10**18,
                    teacher_bonus=teacher_bonus / 10**18,
                    request_id=request_id,
                    expires_at=deadline
                )
                
                if notification_sent:
                    self.logger.info(f"✅ Teacher notification sent for Layer 2 request {request_id}")
                else:
                    self.logger.warning(f"⚠️ Failed to send teacher notification for request {request_id}")
                    
        except Exception as e:
            self.logger.error(f"❌ Failed to send teacher notification: {e}")
    
    def _send_approval_notifications(self, request_data: Dict):
        """Send notifications after request approval"""
        try:
            student_user = User.objects.filter(wallet_address__iexact=request_data['student']).first()
            teacher_user = User.objects.filter(wallet_address__iexact=request_data['teacher']).first()
            
            if student_user and teacher_user:
                course_title = f"Course #{request_data['course_id']}"
                try:
                    from courses.models import Course
                    course = Course.objects.get(id=request_data['course_id'])
                    course_title = course.title
                except:
                    pass
                
                # Notify student of acceptance
                teocoin_notification_service.notify_student_teacher_decision(
                    student=student_user,
                    teacher=teacher_user,
                    course_title=course_title,
                    decision='accepted',
                    teo_amount=(request_data['teo_cost'] + request_data['teacher_bonus']) / 10**18
                )
                
                # Send staking reminder to teacher
                teocoin_notification_service.create_teacher_staking_reminder(
                    teacher=teacher_user,
                    teo_amount=(request_data['teo_cost'] + request_data['teacher_bonus']) / 10**18
                )
                
                self.logger.info(f"✅ Approval notifications sent for Layer 2 request {request_data['request_id']}")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to send approval notifications: {e}")


# Singleton instance
teocoin_layer2_discount_service = TeoCoinLayer2DiscountService()
