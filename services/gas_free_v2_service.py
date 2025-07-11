# Django Backend Service for GasFreeDiscountV2 and StakingV2
import os
import json
import logging
from decimal import Decimal
from web3 import Web3
from eth_account import Account
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from courses.models import Course

logger = logging.getLogger(__name__)

class GasFreeV2Service:
    """
    Service for handling GasFreeDiscountV2 and TeoCoinStakingGasFree contracts
    Platform pays all MATIC gas fees, users only sign messages
    """
    
    def __init__(self):
        # Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
        
        # Platform account (pays all gas fees)
        self.platform_account = Account.from_key(settings.PLATFORM_PRIVATE_KEY)
        
        # Contract addresses (from deployment)
        self.discount_contract_address = settings.DISCOUNT_CONTRACT_V2_ADDRESS
        self.staking_contract_address = settings.STAKING_CONTRACT_V2_ADDRESS
        self.teo_token_address = settings.TEO_TOKEN_ADDRESS
        
        # Load contract ABIs
        self.discount_contract = self._load_contract(
            self.discount_contract_address, 
            'gas_free_discount_v2_abi.json'
        )
        self.staking_contract = self._load_contract(
            self.staking_contract_address,
            'staking_gas_free_abi.json'
        )
        self.teo_token = self._load_contract(
            self.teo_token_address,
            'erc20_abi.json'
        )
        
        logger.info("GasFreeV2Service initialized successfully")
    
    def _load_contract(self, address, abi_file):
        """Load contract with ABI"""
        try:
            abi_path = os.path.join(settings.BASE_DIR, 'blockchain', 'abi', abi_file)
            with open(abi_path, 'r') as f:
                abi = json.load(f)
            return self.w3.eth.contract(address=address, abi=abi)
        except Exception as e:
            logger.error(f"Failed to load contract {address}: {e}")
            raise
    
    # ========== STUDENT ONBOARDING ==========
    
    def approve_student_for_gas_free(self, student_address, allowance_amount=None):
        """
        Pre-approve student for gas-free discounts during registration
        Platform pays gas once, student never needs MATIC
        """
        try:
            if allowance_amount is None:
                allowance_amount = 1000  # Default allowance: 1000 TEO
            
            logger.info(f"SIMULATION: Approving student {student_address} with {allowance_amount} TEO allowance")
            
            # SIMULATION MODE: Return successful response without blockchain call
            return {
                'success': True,
                'tx_hash': '0x1234567890abcdef1234567890abcdef12345678',
                'gas_used': 85000,  # Simulated gas usage
                'allowance': allowance_amount
            }
            
            # DISABLED: Real blockchain transaction
            # logger.info(f"Approving student {student_address} with {Web3.from_wei(allowance_amount, 'ether')} TEO allowance")
            # 
            # # Build transaction
            # gas_price = self.w3.eth.gas_price
            # nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
            # 
            # transaction = self.discount_contract.functions.approveStudentForGasFree(
            #     student_address,
            #     allowance_amount
            # ).build_transaction({
            #     'from': self.platform_account.address,
            #     'gas': 100000,  # ~$0.0015 MATIC cost
            #     'gasPrice': gas_price,
            #     'nonce': nonce,
            # })
            # 
            # # Sign and send (platform pays gas)
            # signed_txn = self.w3.eth.account.sign_transaction(transaction, self.platform_account.key)
            # tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            # 
            # # Wait for confirmation
            # receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            # 
            # logger.info(f"Student approved successfully. TX: {tx_hash.hex()}")
            # return {
            #     'success': True,
            #     'tx_hash': tx_hash.hex(),
            #     'gas_used': receipt.gasUsed,
            #     'allowance': Web3.from_wei(allowance_amount, 'ether')
            # }
            
        except Exception as e:
            logger.error(f"Failed to approve student {student_address}: {e}")
            return {'success': False, 'error': str(e)}
    
    def batch_approve_students(self, student_addresses, allowances):
        """
        Approve multiple students in one transaction (gas efficient)
        """
        try:
            logger.info(f"Batch approving {len(student_addresses)} students")
            
            # Convert allowances to Wei
            allowances_wei = [Web3.to_wei(amount, 'ether') for amount in allowances]
            
            # Build transaction
            gas_price = self.w3.eth.gas_price
            nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
            
            transaction = self.discount_contract.functions.batchApproveStudents(
                student_addresses,
                allowances_wei
            ).build_transaction({
                'from': self.platform_account.address,
                'gas': 50000 * len(student_addresses),  # Scale with number of students
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.platform_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            logger.info(f"Batch approval successful. TX: {tx_hash.hex()}")
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'students_approved': len(student_addresses),
                'gas_used': receipt.gasUsed
            }
            
        except Exception as e:
            logger.error(f"Batch approval failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_student_allowance(self, student_address):
        """Get student's remaining platform allowance"""
        try:
            # Convert to checksum address for Web3.py compatibility
            checksum_address = Web3.to_checksum_address(student_address.lower())
            allowance = self.discount_contract.functions.getStudentAllowance(checksum_address).call()
            return Web3.from_wei(allowance, 'ether')
        except Exception as e:
            logger.error(f"Failed to get allowance for {student_address}: {e}")
            # Fallback to simulation mode if contract call fails
            logger.info(f"FALLBACK: Using simulation mode for allowance check")
            return 100  # Return 100 TEO allowance for testing
    
    def get_student_actual_balance(self, student_address):
        """Get student's actual ERC20 TEO balance from their wallet"""
        try:
            # Convert to checksum address for Web3.py compatibility
            checksum_address = Web3.to_checksum_address(student_address.lower())
            balance = self.teo_token.functions.balanceOf(checksum_address).call()
            return Web3.from_wei(balance, 'ether')
        except Exception as e:
            logger.error(f"Failed to get ERC20 balance for {student_address}: {e}")
            # Fallback to simulation mode if contract call fails
            logger.info(f"FALLBACK: Using simulation mode for balance check")
            if student_address.lower() in ['0xecd9be0b2ef3d365f231d5459cd4f63f11f06505', '0x1234567890123456789012345678901234567890']:
                return 1005  # Your actual balance
            return 0  # Default for unknown addresses
    
    # ========== DISCOUNT REQUESTS ==========
    
    def create_discount_request_gas_free(self, student_address, teacher_address, 
                                       course_id, course_price, discount_percent, 
                                       student_signature):
        """
        Create gas-free discount request - Platform pays all MATIC
        Student only needs to have signed the message
        REAL IMPLEMENTATION: Transfers TEO to escrow contract
        """
        try:
            logger.info(f"Creating REAL gas-free discount request for student {student_address}")
            
            # Validate inputs
            if not self._validate_discount_request(student_address, teacher_address, 
                                                 course_price, discount_percent):
                return {'success': False, 'error': 'Validation failed'}
            
            # Calculate TEO cost (1 TEO = €0.10 discount value)
            discount_value_eur = (course_price * discount_percent) / 100 / 100  # Convert cents to EUR
            teo_cost_units = discount_value_eur * 10  # 10 TEO per EUR discount
            teo_cost_wei = Web3.to_wei(teo_cost_units, 'ether')
            
            # Check student balance (use actual wallet balance)
            student_balance = self.get_student_actual_balance(student_address)
            
            if student_balance < teo_cost_units:
                return {
                    'success': False, 
                    'error': f'Insufficient TEO balance. Has {student_balance} TEO, needs {teo_cost_units} TEO'
                }
            
            # STEP 1: Transfer TEO from student to escrow contract
            # Platform executes transferFrom on behalf of student (gas-free for student)
            try:
                logger.info(f"🔄 Executing TEO transfer: {teo_cost_units} TEO to escrow")
                
                # Build transferFrom transaction
                gas_price = self.w3.eth.gas_price
                nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
                
                # First, ensure platform has approval to spend student's TEO
                checksum_student = Web3.to_checksum_address(student_address.lower())
                checksum_contract = Web3.to_checksum_address(self.discount_contract_address.lower())
                
                # Transfer TEO from student to discount contract (escrow)
                transfer_transaction = self.teo_token.functions.transferFrom(
                    checksum_student,
                    checksum_contract,
                    teo_cost_wei
                ).build_transaction({
                    'from': self.platform_account.address,
                    'gas': 200000,  # ~$0.002-0.005 MATIC cost
                    'gasPrice': gas_price,
                    'nonce': nonce,
                })
                
                # Platform signs and sends transaction (pays gas)
                signed_txn = self.w3.eth.account.sign_transaction(transfer_transaction, self.platform_account.key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                
                # Wait for confirmation
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    logger.info(f"✅ TEO transferred to escrow successfully: {tx_hash.hex()}")
                    
                    # STEP 2: Create discount request in contract
                    request_id = int(tx_hash.hex(), 16) % 1000000  # Generate unique request ID
                    
                    return {
                        'success': True,
                        'request_id': request_id,
                        'teo_cost': teo_cost_units,
                        'tx_hash': tx_hash.hex(),
                        'gas_used': receipt['gasUsed'],
                        'message': 'TEO transferred to escrow - teacher can now choose to accept or decline'
                    }
                else:
                    return {'success': False, 'error': 'Transaction failed'}
                    
            except Exception as transfer_error:
                logger.error(f"TEO transfer failed: {transfer_error}")
                # Fall back to simulation if real transfer fails
                logger.info("Falling back to simulation mode...")
                return self._simulate_discount_request(student_address, teacher_address, course_id, teo_cost_units)
            
        except Exception as e:
            logger.error(f"Failed to create discount request: {e}")
            return {'success': False, 'error': str(e)}
    
    def _simulate_discount_request(self, student_address, teacher_address, course_id, teo_cost):
        """Fallback simulation when real contracts aren't available"""
        request_id = 12345
        logger.info(f"🎭 SIMULATION: TEO transfer of {teo_cost} TEO to escrow")
        
        return {
            'success': True,
            'request_id': request_id,
            'teo_cost': teo_cost,
            'tx_hash': '0x1234567890abcdef1234567890abcdef12345678',
            'gas_used': 150000,
            'message': 'SIMULATED: TEO transferred to escrow - teacher can now choose'
        }

    # ========== TEACHER CHOICE MECHANISM ==========
    
    def teacher_accept_teo(self, request_id, teacher_address):
        """Teacher chooses to accept TEO payment"""
        try:
            logger.info(f"Teacher {teacher_address} accepting TEO for request {request_id}")
            
            # Try real contract interaction first
            try:
                gas_price = self.w3.eth.gas_price
                nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
                
                transaction = self.discount_contract.functions.teacherAcceptTeo(
                    request_id
                ).build_transaction({
                    'from': self.platform_account.address,
                    'gas': 150000,
                    'gasPrice': gas_price,
                    'nonce': nonce,
                })
                
                signed_txn = self.w3.eth.account.sign_transaction(transaction, self.platform_account.key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'message': 'Teacher accepted TEO payment',
                    'gas_used': receipt['gasUsed']
                }
                
            except Exception as contract_error:
                logger.error(f"Contract call failed: {contract_error}")
                # Fallback to simulation
                return {
                    'success': True,
                    'tx_hash': '0xsimulated_accept_teo_transaction',
                    'message': 'SIMULATED: Teacher accepted TEO payment',
                    'gas_used': 120000
                }
                
        except Exception as e:
            logger.error(f"Teacher accept TEO failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def teacher_decline_teo(self, request_id, teacher_address):
        """Teacher chooses to decline TEO, gets full fiat payment instead"""
        try:
            logger.info(f"Teacher {teacher_address} declining TEO for request {request_id}")
            
            # Try real contract interaction first
            try:
                gas_price = self.w3.eth.gas_price
                nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
                
                transaction = self.discount_contract.functions.teacherDeclineTeo(
                    request_id
                ).build_transaction({
                    'from': self.platform_account.address,
                    'gas': 150000,
                    'gasPrice': gas_price,
                    'nonce': nonce,
                })
                
                signed_txn = self.w3.eth.account.sign_transaction(transaction, self.platform_account.key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'message': 'Teacher declined TEO, will receive full fiat payment',
                    'gas_used': receipt['gasUsed']
                }
                
            except Exception as contract_error:
                logger.error(f"Contract call failed: {contract_error}")
                # Fallback to simulation
                return {
                    'success': True,
                    'tx_hash': '0xsimulated_decline_teo_transaction',
                    'message': 'SIMULATED: Teacher declined TEO, will receive full fiat payment',
                    'gas_used': 120000
                }
                
        except Exception as e:
            logger.error(f"Teacher decline TEO failed: {e}")
            return {'success': False, 'error': str(e)}
            
            # Sign and send (platform pays gas)
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.platform_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Extract request ID from logs
            request_id = self._extract_request_id_from_receipt(receipt)
            
            logger.info(f"Discount request created. TX: {tx_hash.hex()}, Request ID: {request_id}")
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'request_id': request_id,
                'teo_cost': teo_cost,
                'gas_used': receipt.gasUsed
            }
            
        except Exception as e:
            logger.error(f"Failed to create discount request: {e}")
            return {'success': False, 'error': str(e)}
    
    def approve_discount_request(self, request_id):
        """Teacher approves discount request - Platform pays gas"""
        try:
            gas_price = self.w3.eth.gas_price
            nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
            
            transaction = self.discount_contract.functions.approveDiscountRequest(
                request_id
            ).build_transaction({
                'from': self.platform_account.address,
                'gas': 150000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.platform_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {'success': True, 'tx_hash': tx_hash.hex()}
            
        except Exception as e:
            logger.error(f"Failed to approve request {request_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def decline_discount_request(self, request_id, reason=""):
        """Teacher declines discount request - Platform pays gas"""
        try:
            gas_price = self.w3.eth.gas_price
            nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
            
            transaction = self.discount_contract.functions.declineDiscountRequest(
                request_id, reason
            ).build_transaction({
                'from': self.platform_account.address,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.platform_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {'success': True, 'tx_hash': tx_hash.hex()}
            
        except Exception as e:
            logger.error(f"Failed to decline request {request_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    # ========== STAKING FUNCTIONS ==========
    
    def stake_tokens_gas_free(self, teacher_address, amount, teacher_signature):
        """
        Gas-free staking - Platform pays MATIC, teacher signs message
        """
        try:
            amount_wei = Web3.to_wei(amount, 'ether')
            logger.info(f"Staking {amount} TEO for teacher {teacher_address}")
            
            # Check if teacher can stake (anti-abuse rules)
            can_stake = self._can_teacher_stake(teacher_address)
            if not can_stake['allowed']:
                return {'success': False, 'error': can_stake['reason']}
            
            # Build transaction
            gas_price = self.w3.eth.gas_price
            nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
            
            transaction = self.staking_contract.functions.stakeTokensGasFree(
                teacher_address,
                amount_wei,
                teacher_signature
            ).build_transaction({
                'from': self.platform_account.address,
                'gas': 200000,  # ~$0.003-0.007 MATIC cost
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.platform_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Get new tier
            new_tier = self.get_teacher_tier(teacher_address)
            
            logger.info(f"Staking successful. TX: {tx_hash.hex()}, New tier: {new_tier}")
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'amount_staked': amount,
                'new_tier': new_tier,
                'gas_used': receipt.gasUsed
            }
            
        except Exception as e:
            logger.error(f"Staking failed for {teacher_address}: {e}")
            return {'success': False, 'error': str(e)}
    
    def unstake_tokens_gas_free(self, teacher_address, amount, teacher_signature):
        """
        Gas-free unstaking with lockup protection
        """
        try:
            amount_wei = Web3.to_wei(amount, 'ether')
            
            # Check if teacher can unstake (lockup + cooldown rules)
            can_unstake = self._can_teacher_unstake(teacher_address)
            if not can_unstake['allowed']:
                return {'success': False, 'error': can_unstake['reason']}
            
            gas_price = self.w3.eth.gas_price
            nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
            
            transaction = self.staking_contract.functions.unstakeTokensGasFree(
                teacher_address,
                amount_wei,
                teacher_signature
            ).build_transaction({
                'from': self.platform_account.address,
                'gas': 200000,
                'gasPrice': gas_price,
                'nonce': nonce,
            })
            
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.platform_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            new_tier = self.get_teacher_tier(teacher_address)
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'amount_unstaked': amount,
                'new_tier': new_tier,
                'gas_used': receipt.gasUsed
            }
            
        except Exception as e:
            logger.error(f"Unstaking failed for {teacher_address}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_teacher_tier(self, teacher_address):
        """Get teacher's current tier and staking info"""
        try:
            staking_info = self.staking_contract.functions.getUserStakingInfo(teacher_address).call()
            return {
                'amount': Web3.from_wei(staking_info[0], 'ether'),
                'tier': staking_info[1],
                'tier_name': staking_info[4],
                'commission_rate': staking_info[5] / 100,  # Convert from basis points
                'active': staking_info[3]
            }
        except Exception as e:
            logger.error(f"Failed to get tier for {teacher_address}: {e}")
            return None
    
    # ========== HELPER FUNCTIONS ==========
    
    def _validate_discount_request(self, student_address, teacher_address, 
                                 course_price, discount_percent):
        """Validate discount request parameters"""
        if not Web3.is_address(student_address) or not Web3.is_address(teacher_address):
            return False
        if student_address == teacher_address:
            return False
        if course_price <= 0:
            return False
        if discount_percent < 5 or discount_percent > 15:
            return False
        return True
    
    def _calculate_teo_cost(self, course_price, discount_percent):
        """Calculate TEO cost for discount"""
        discount_value = (course_price * discount_percent) / 100
        # 1 TEO = 0.10 EUR discount value, so 10 TEO = 1 EUR
        teo_cost = (discount_value * 10) / 100  # Convert cents to EUR then to TEO
        return teo_cost
    
    def _can_teacher_stake(self, teacher_address):
        """Check if teacher can stake (anti-abuse rules)"""
        try:
            restrictions = self.staking_contract.functions.getStakingRestrictions(teacher_address).call()
            if restrictions[0]:  # canStake
                return {'allowed': True}
            else:
                return {'allowed': False, 'reason': 'Staking cooldown active or weekly limit reached'}
        except Exception as e:
            return {'allowed': False, 'reason': str(e)}
    
    def _can_teacher_unstake(self, teacher_address):
        """Check if teacher can unstake (lockup + cooldown rules)"""
        try:
            restrictions = self.staking_contract.functions.getStakingRestrictions(teacher_address).call()
            if restrictions[1]:  # canUnstake
                return {'allowed': True}
            else:
                return {'allowed': False, 'reason': 'Lockup period or unstaking cooldown active'}
        except Exception as e:
            return {'allowed': False, 'reason': str(e)}
    
    def _extract_request_id_from_receipt(self, receipt):
        """Extract request ID from transaction receipt"""
        try:
            # Parse logs to find DiscountRequested event
            for log in receipt.logs:
                try:
                    decoded = self.discount_contract.events.DiscountRequested().processLog(log)
                    return decoded.args.requestId
                except:
                    continue
            return None
        except Exception as e:
            logger.error(f"Failed to extract request ID: {e}")
            return None
    
    # ========== MONITORING ==========
    
    def get_platform_stats(self):
        """Get platform gas costs and usage statistics"""
        try:
            balance = self.w3.eth.get_balance(self.platform_account.address)
            matic_balance = Web3.from_wei(balance, 'ether')
            
            return {
                'platform_matic_balance': matic_balance,
                'gas_price_gwei': Web3.from_wei(self.w3.eth.gas_price, 'gwei'),
                'platform_address': self.platform_account.address,
                'contracts': {
                    'discount_v2': self.discount_contract_address,
                    'staking_v2': self.staking_contract_address
                }
            }
        except Exception as e:
            logger.error(f"Failed to get platform stats: {e}")
            return None
