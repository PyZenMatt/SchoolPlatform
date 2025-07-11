"""
Gas-Free TeoCoin API Views
REST API endpoints for gas-free discount and staking operations.
"""
import logging
from datetime import datetime
from typing import Dict, Any
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from web3 import Web3

from .gas_free_discount_service import GasFreeDiscountService
from .gas_free_staking_service import GasFreeStakingService
from .exceptions import TeoArtServiceException

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([])
def create_discount_signature(request):
    """
    Create a signature for gas-free discount request.
    
    POST /api/gas-free/discount/signature/
    {
        "student_address": "0x...",
        "course_id": 123,
        "teo_amount": 100
    }
    """
    try:
        # Get request data
        student_address = request.data.get('student_address')
        course_id = request.data.get('course_id')
        teo_amount = request.data.get('teo_amount')
        
        # Validate required fields
        if not all([student_address, course_id, teo_amount]):
            return Response({
                'error': 'Missing required fields: student_address, course_id, teo_amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert address to checksum format
        try:
            student_address = Web3.to_checksum_address(student_address)
        except Exception as e:
            return Response({
                'error': f'Invalid Ethereum address format: {student_address}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create signature
        service = GasFreeDiscountService()
        signature_data = service.create_discount_signature(
            student_address=student_address,
            course_id=int(course_id),
            teo_amount=int(teo_amount)
        )
        
        return Response({
            'success': True,
            'data': signature_data
        }, status=status.HTTP_200_OK)
        
    except TeoArtServiceException as e:
        logger.error(f"Service error in create_discount_signature: {str(e)}")
        return Response({
            'error': str(e),
            'code': getattr(e, 'code', 'SERVICE_ERROR')
        }, status=getattr(e, 'status_code', 500))
        
    except Exception as e:
        logger.error(f"Unexpected error in create_discount_signature: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([])
def execute_discount_request(request):
    """
    Execute gas-free discount request on blockchain.
    
    POST /api/gas-free/discount/execute/
    {
        "student_address": "0x...",
        "signature": "0x...",
        "course_id": 123,
        "teo_amount": 100,
        "nonce": 1641234567
    }
    """
    try:
        # Get request data
        student_address = request.data.get('student_address')
        signature = request.data.get('signature')
        course_id = request.data.get('course_id')
        teo_amount = request.data.get('teo_amount')
        nonce = request.data.get('nonce')
        
        # Validate required fields
        if not all([student_address, signature, course_id, teo_amount, nonce]):
            return Response({
                'error': 'Missing required fields: student_address, signature, course_id, teo_amount, nonce'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert address to checksum format
        try:
            student_address = Web3.to_checksum_address(student_address)
        except Exception as e:
            return Response({
                'error': f'Invalid Ethereum address format: {student_address}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Execute discount request
        service = GasFreeDiscountService()
        result = service.execute_discount_request(
            student_address=student_address,
            signature=signature,
            course_id=int(course_id),
            teo_amount=int(teo_amount),
            nonce=int(nonce)
        )
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
        
    except TeoArtServiceException as e:
        logger.error(f"Service error in execute_discount_request: {str(e)}")
        return Response({
            'error': str(e),
            'code': getattr(e, 'code', 'SERVICE_ERROR')
        }, status=getattr(e, 'status_code', 500))
        
    except Exception as e:
        logger.error(f"Unexpected error in execute_discount_request: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_discount_request_status(request, request_id):
    """
    Get status of a discount request.
    
    GET /api/gas-free/discount/status/{request_id}/
    """
    try:
        service = GasFreeDiscountService()
        status_data = service.get_discount_request_status(int(request_id))
        
        return Response({
            'success': True,
            'data': status_data
        }, status=status.HTTP_200_OK)
        
    except TeoArtServiceException as e:
        logger.error(f"Service error in get_discount_request_status: {str(e)}")
        return Response({
            'error': str(e),
            'code': getattr(e, 'code', 'SERVICE_ERROR')
        }, status=getattr(e, 'status_code', 500))
        
    except Exception as e:
        logger.error(f"Unexpected error in get_discount_request_status: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_stake_signature(request):
    """
    Create a signature for gas-free staking operation.
    
    POST /api/gas-free/staking/stake-signature/
    {
        "user_address": "0x...",
        "teo_amount": 1000
    }
    """
    try:
        # Get request data
        user_address = request.data.get('user_address')
        teo_amount = request.data.get('teo_amount')
        
        # Validate required fields
        if not all([user_address, teo_amount]):
            return Response({
                'error': 'Missing required fields: user_address, teo_amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create signature
        service = GasFreeStakingService()
        signature_data = service.create_stake_signature(
            user_address=user_address,
            teo_amount=int(teo_amount)
        )
        
        return Response({
            'success': True,
            'data': signature_data
        }, status=status.HTTP_200_OK)
        
    except TeoArtServiceException as e:
        logger.error(f"Service error in create_stake_signature: {str(e)}")
        return Response({
            'error': str(e),
            'code': getattr(e, 'code', 'SERVICE_ERROR')
        }, status=getattr(e, 'status_code', 500))
        
    except Exception as e:
        logger.error(f"Unexpected error in create_stake_signature: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_unstake_signature(request):
    """
    Create a signature for gas-free unstaking operation.
    
    POST /api/gas-free/staking/unstake-signature/
    {
        "user_address": "0x...",
        "teo_amount": 500
    }
    """
    try:
        # Get request data
        user_address = request.data.get('user_address')
        teo_amount = request.data.get('teo_amount')
        
        # Validate required fields
        if not all([user_address, teo_amount]):
            return Response({
                'error': 'Missing required fields: user_address, teo_amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create signature
        service = GasFreeStakingService()
        signature_data = service.create_unstake_signature(
            user_address=user_address,
            teo_amount=int(teo_amount)
        )
        
        return Response({
            'success': True,
            'data': signature_data
        }, status=status.HTTP_200_OK)
        
    except TeoArtServiceException as e:
        logger.error(f"Service error in create_unstake_signature: {str(e)}")
        return Response({
            'error': str(e),
            'code': getattr(e, 'code', 'SERVICE_ERROR')
        }, status=getattr(e, 'status_code', 500))
        
    except Exception as e:
        logger.error(f"Unexpected error in create_unstake_signature: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_stake_request(request):
    """
    Execute gas-free staking request on blockchain.
    
    POST /api/gas-free/staking/stake/
    {
        "user_address": "0x...",
        "signature": "0x...",
        "teo_amount": 1000,
        "nonce": 1641234567
    }
    """
    try:
        # Get request data
        user_address = request.data.get('user_address')
        signature = request.data.get('signature')
        teo_amount = request.data.get('teo_amount')
        nonce = request.data.get('nonce')
        
        # Validate required fields
        if not all([user_address, signature, teo_amount, nonce]):
            return Response({
                'error': 'Missing required fields: user_address, signature, teo_amount, nonce'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Execute stake request
        service = GasFreeStakingService()
        result = service.execute_stake_request(
            user_address=user_address,
            signature=signature,
            teo_amount=int(teo_amount),
            nonce=int(nonce)
        )
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
        
    except TeoArtServiceException as e:
        logger.error(f"Service error in execute_stake_request: {str(e)}")
        return Response({
            'error': str(e),
            'code': getattr(e, 'code', 'SERVICE_ERROR')
        }, status=getattr(e, 'status_code', 500))
        
    except Exception as e:
        logger.error(f"Unexpected error in execute_stake_request: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_unstake_request(request):
    """
    Execute gas-free unstaking request on blockchain.
    
    POST /api/gas-free/staking/unstake/
    {
        "user_address": "0x...",
        "signature": "0x...",
        "teo_amount": 500,
        "nonce": 1641234567
    }
    """
    try:
        # Get request data
        user_address = request.data.get('user_address')
        signature = request.data.get('signature')
        teo_amount = request.data.get('teo_amount')
        nonce = request.data.get('nonce')
        
        # Validate required fields
        if not all([user_address, signature, teo_amount, nonce]):
            return Response({
                'error': 'Missing required fields: user_address, signature, teo_amount, nonce'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Execute unstake request
        service = GasFreeStakingService()
        result = service.execute_unstake_request(
            user_address=user_address,
            signature=signature,
            teo_amount=int(teo_amount),
            nonce=int(nonce)
        )
        
        return Response({
            'success': True,
            'data': result
        }, status=status.HTTP_200_OK)
        
    except TeoArtServiceException as e:
        logger.error(f"Service error in execute_unstake_request: {str(e)}")
        return Response({
            'error': str(e),
            'code': getattr(e, 'code', 'SERVICE_ERROR')
        }, status=getattr(e, 'status_code', 500))
        
    except Exception as e:
        logger.error(f"Unexpected error in execute_unstake_request: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_stake_info(request, user_address):
    """
    Get user's staking information.
    
    GET /api/gas-free/staking/info/{user_address}/
    """
    try:
        service = GasFreeStakingService()
        stake_info = service.get_user_stake_info(user_address)
        
        return Response({
            'success': True,
            'data': stake_info
        }, status=status.HTTP_200_OK)
        
    except TeoArtServiceException as e:
        logger.error(f"Service error in get_user_stake_info: {str(e)}")
        return Response({
            'error': str(e),
            'code': getattr(e, 'code', 'SERVICE_ERROR')
        }, status=getattr(e, 'status_code', 500))
        
    except Exception as e:
        logger.error(f"Unexpected error in get_user_stake_info: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([])
def get_user_stats(request, user_address):
    """
    Get user's general statistics including TEO balance.
    
    GET /api/services/gas-free/user-stats/{user_address}/
    """
    try:
        # Convert address to checksum format
        try:
            user_address = Web3.to_checksum_address(user_address)
        except Exception as e:
            return Response({
                'error': f'Invalid Ethereum address format: {user_address}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize services
        staking_service = GasFreeStakingService()
        
        # Get user's TEO balance from the blockchain
        teo_balance = staking_service.get_user_teo_balance(user_address)
        
        # Try to get staking information, but don't fail if it errors
        try:
            stake_info = staking_service.get_user_stake_info(user_address)
        except Exception as stake_error:
            logger.warning(f"Failed to get stake info for {user_address}: {str(stake_error)}")
            stake_info = {
                'staked_amount': 0,
                'reward_earned': 0,
                'stake_start_time': None,
                'error': 'Could not retrieve staking information'
            }
        
        # Prepare user stats
        user_stats = {
            'user_address': user_address,
            'teo_balance': float(teo_balance),
            'staking_info': stake_info,
            'has_sufficient_balance': teo_balance >= 10,  # Minimum for discount
            'timestamp': datetime.now().isoformat()
        }
        
        return Response({
            'success': True,
            'data': user_stats
        }, status=status.HTTP_200_OK)
        
    except TeoArtServiceException as e:
        logger.error(f"Service error in get_user_stats: {str(e)}")
        return Response({
            'error': str(e),
            'code': getattr(e, 'code', 'SERVICE_ERROR')
        }, status=getattr(e, 'status_code', 500))
        
    except Exception as e:
        logger.error(f"Unexpected error in get_user_stats: {str(e)}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([])
def estimate_gas_costs(request):
    """
    Get gas cost estimates for all gas-free operations.
    
    GET /api/gas-free/gas-estimates/
    """
    try:
        discount_service = GasFreeDiscountService()
        staking_service = GasFreeStakingService()
        
        discount_costs = discount_service.estimate_gas_cost()
        staking_costs = staking_service.estimate_staking_gas_cost()
        
        return Response({
            'success': True,
            'data': {
                'discount_operations': discount_costs,
                'staking_operations': staking_costs,
                'platform_economics': {
                    'total_daily_cost_estimate': {
                        '100_mixed_operations': (
                            discount_costs.get('daily_estimates', {}).get('100_requests', 0.2) +
                            staking_costs.get('daily_estimates', {}).get('100_operations', 0.3)
                        ) / 2,
                        'monthly_estimate': (
                            discount_costs.get('daily_estimates', {}).get('100_requests', 0.2) +
                            staking_costs.get('daily_estimates', {}).get('100_operations', 0.3)
                        ) * 15,  # 30 days / 2
                    },
                    'cost_per_user_per_month': 0.15,  # Estimated
                    'break_even_users': 200  # Estimated
                }
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in estimate_gas_costs: {str(e)}")
        return Response({
            'error': 'Failed to estimate gas costs',
            'fallback_data': {
                'cost_per_operation': 0.002,
                'monthly_estimate_100_users': 15.0
            }
        }, status=status.HTTP_200_OK)


# =============================================================================
# PERMIT + DISCOUNT OPERATIONS (New - Solves Student Gas Problem)
# =============================================================================

@api_view(['POST'])
@csrf_exempt
def create_permit_discount_signatures(request):
    """
    Create both permit and discount signature data for a student.
    
    POST data:
    {
        "student_address": "0x...",
        "course_id": 123,
        "teo_amount": 10
    }
    
    Returns both permit and discount signature data that student needs to sign.
    """
    try:
        data = request.data
        student_address = data.get('student_address')
        course_id = data.get('course_id')
        teo_amount = data.get('teo_amount')
        
        if not all([student_address, course_id, teo_amount]):
            return Response({
                'error': 'Missing required fields: student_address, course_id, teo_amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = GasFreeDiscountService()
        
        # Create permit signature data (for approval)
        permit_data = service.create_permit_signature_data(
            student_address=student_address
        )
        
        # Create discount signature data
        discount_data = service.create_discount_signature(
            student_address=student_address,
            course_id=int(course_id),
            teo_amount=int(teo_amount)
        )
        
        return Response({
            'success': True,
            'permit_data': permit_data,
            'discount_data': discount_data,
            'instructions': {
                'step_1': 'Sign the permit data using eth_signTypedData_v4',
                'step_2': 'Sign the discount message hash using personal_sign',
                'step_3': 'Submit both signatures to execute endpoint',
                'gas_required': 'Zero MATIC required for signatures',
                'platform_pays': 'Platform pays all transaction gas fees'
            }
        })
        
    except TeoArtServiceException as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Internal error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def execute_permit_discount(request):
    """
    Execute permit + discount with student signatures.
    
    POST data:
    {
        "student_address": "0x...",
        "course_id": 123,
        "teo_amount": 10,
        "discount_signature": "0x...",
        "discount_nonce": 123456,
        "permit_signature": "0x...",
        "permit_deadline": 1234567890,
        "permit_nonce": 0
    }
    """
    try:
        data = request.data
        
        # Extract parameters
        student_address = data.get('student_address')
        course_id = data.get('course_id')
        teo_amount = data.get('teo_amount')
        discount_signature = data.get('discount_signature')
        discount_nonce = data.get('discount_nonce')
        permit_signature = data.get('permit_signature')
        permit_deadline = data.get('permit_deadline')
        permit_nonce = data.get('permit_nonce', 0)
        
        # Validate required fields
        required_fields = [
            'student_address', 'course_id', 'teo_amount', 
            'discount_signature', 'discount_nonce',
            'permit_signature', 'permit_deadline'
        ]
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = GasFreeDiscountService()
        
        # Parse permit signature (v, r, s)
        permit_sig = permit_signature.replace('0x', '')
        if len(permit_sig) != 130:  # 65 bytes * 2
            return Response({
                'error': 'Invalid permit signature length'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        permit_r = '0x' + permit_sig[:64]
        permit_s = '0x' + permit_sig[64:128]
        permit_v = int(permit_sig[128:130], 16)
        
        # Execute the complete transaction
        result = service.execute_discount_request(
            student_address=student_address,
            signature=discount_signature,
            course_id=int(course_id),
            teo_amount=int(teo_amount),
            nonce=int(discount_nonce),
            permit_deadline=int(permit_deadline),
            permit_v=permit_v,
            permit_r=permit_r,
            permit_s=permit_s
        )
        
        return Response({
            'success': True,
            'result': result,
            'message': 'Gas-free discount executed successfully!'
        })
        
    except TeoArtServiceException as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Internal error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
