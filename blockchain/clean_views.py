"""
Clean Blockchain Views for Phase 2 TeoCoin Withdrawal System

Simplified, focused API endpoints for:
- Processing withdrawals from DB balance to MetaMask
- Token information and balance queries
- Transaction status checking
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
import logging

from .services import teocoin_service
from services.teocoin_withdrawal_service import teocoin_withdrawal_service

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_token_balance(request):
    """
    Get TeoCoin balance for user's linked wallet.
    
    Returns:
        JSON with balance and wallet information
    """
    user = request.user
    
    if not user.wallet_address:
        return Response({
            'error': 'No wallet linked to account',
            'balance': '0',
            'wallet_address': None
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        balance = teocoin_service.get_balance(user.wallet_address)
        
        return Response({
            'balance': str(balance),
            'wallet_address': user.wallet_address,
            'token_info': teocoin_service.get_token_info()
        })
        
    except Exception as e:
        logger.error(f"Error getting balance for {user.email}: {e}")
        return Response({
            'error': 'Failed to retrieve balance',
            'balance': '0'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_wallet_address(request):
    """
    Link MetaMask wallet address to user account.
    
    Request Body:
        wallet_address (str): Ethereum/Polygon wallet address
    """
    user = request.user
    wallet_address = request.data.get('wallet_address')
    
    if not wallet_address:
        return Response({
            'error': 'wallet_address is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate address format
    if not teocoin_service.validate_address(wallet_address):
        return Response({
            'error': 'Invalid wallet address format'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Check if address is already used by another user
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(wallet_address=wallet_address).exclude(id=user.id).exists():
            return Response({
                'error': 'Wallet address already linked to another account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Link wallet to user
        user.wallet_address = wallet_address
        user.save()
        
        # Get initial balance
        balance = teocoin_service.get_balance(wallet_address)
        
        return Response({
            'message': 'Wallet linked successfully',
            'wallet_address': wallet_address,
            'balance': str(balance)
        })
        
    except Exception as e:
        logger.error(f"Error linking wallet for {user.email}: {e}")
        return Response({
            'error': 'Failed to link wallet'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_withdrawal(request):
    """
    Request withdrawal of TeoCoin from DB balance to MetaMask wallet.
    
    Request Body:
        amount (str): Amount of TEO to withdraw
        metamask_address (str): MetaMask wallet address to receive tokens
    """
    user = request.user
    amount = request.data.get('amount')
    metamask_address = request.data.get('metamask_address')
    
    if not amount or not metamask_address:
        return Response({
            'error': 'amount and metamask_address are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            return Response({
                'error': 'Amount must be positive'
            }, status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, TypeError):
        return Response({
            'error': 'Invalid amount format'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate MetaMask address
    if not teocoin_service.validate_address(metamask_address):
        return Response({
            'error': 'Invalid MetaMask address format'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Create withdrawal request using our Phase 1 service
        withdrawal_result = teocoin_withdrawal_service.create_withdrawal_request(
            user=user,
            amount=amount_decimal,
            wallet_address=metamask_address,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        if not withdrawal_result['success']:
            return Response({
                'error': withdrawal_result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'withdrawal_id': withdrawal_result['withdrawal_id'],
            'amount': str(amount_decimal),
            'metamask_address': metamask_address,
            'status': 'pending',
            'estimated_processing_time': '5-10 minutes'
        })
        
    except Exception as e:
        logger.error(f"Error creating withdrawal for {user.email}: {e}")
        return Response({
            'error': 'Failed to create withdrawal request'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_withdrawal_status(request, withdrawal_id):
    """
    Get status of a withdrawal request.
    
    Args:
        withdrawal_id: ID of the withdrawal request
    """
    user = request.user
    
    try:
        withdrawal_status = teocoin_withdrawal_service.get_withdrawal_status(
            user=user,
            withdrawal_id=withdrawal_id
        )
        
        if not withdrawal_status:
            return Response({
                'error': 'Withdrawal request not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(withdrawal_status)
        
    except Exception as e:
        logger.error(f"Error getting withdrawal status for {user.email}, ID {withdrawal_id}: {e}")
        return Response({
            'error': 'Failed to retrieve withdrawal status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_withdrawal_history(request):
    """
    Get withdrawal history for the authenticated user.
    """
    user = request.user
    
    try:
        history = teocoin_withdrawal_service.get_user_withdrawal_history(user)
        
        return Response({
            'withdrawals': history,
            'total_count': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error getting withdrawal history for {user.email}: {e}")
        return Response({
            'error': 'Failed to retrieve withdrawal history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_transaction_status(request):
    """
    Check the status of a blockchain transaction.
    
    Request Body:
        tx_hash (str): Transaction hash to check
    """
    tx_hash = request.data.get('tx_hash')
    
    if not tx_hash:
        return Response({
            'error': 'tx_hash is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        receipt = teocoin_service.get_transaction_receipt(tx_hash)
        
        if receipt:
            return Response({
                'status': 'confirmed' if receipt['status'] == 1 else 'failed',
                'block_number': receipt['block_number'],
                'gas_used': receipt['gas_used'],
                'transaction_hash': receipt['transaction_hash']
            })
        else:
            return Response({
                'status': 'pending',
                'message': 'Transaction still in progress'
            })
    
    except Exception as e:
        logger.error(f"Error checking transaction {tx_hash}: {e}")
        return Response({
            'error': 'Failed to check transaction status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_token_info(request):
    """
    Get TeoCoin token information (public endpoint).
    """
    try:
        token_info = teocoin_service.get_token_info()
        return Response(token_info)
    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        return Response({
            'error': 'Failed to retrieve token information'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Admin endpoints for Phase 2 (if needed)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_pending_withdrawals(request):
    """
    Process pending withdrawals (admin only).
    """
    if not request.user.is_staff:
        return Response({
            'error': 'Admin access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        # Process withdrawals using our management command
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('process_withdrawals', stdout=out)
        output = out.getvalue()
        
        return Response({
            'message': 'Withdrawal processing initiated',
            'output': output
        })
        
    except Exception as e:
        logger.error(f"Error processing withdrawals: {e}")
        return Response({
            'error': 'Failed to process withdrawals'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
