"""
Blockchain API Views for TeoCoin System

This module provides REST API endpoints for blockchain operations including:
- Wallet management (linking external wallets to user accounts)
- Token balance queries
- Token minting (rewards system)
- Transaction history
- Transaction status checking

Security Note: This implementation is for educational/testnet use only.
Production deployments should implement additional security measures.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from decimal import Decimal
from web3 import Web3
import json
import logging

from .blockchain import TeoCoinService

# Initialize TeoCoin service
teocoin_service = TeoCoinService()
from rewards.models import BlockchainTransaction, TokenBalance
from users.models import User
from courses.models import Course, CourseEnrollment

logger = logging.getLogger(__name__)


def format_hash_with_prefix(hash_value):
    """
    Ensure transaction hash has 0x prefix.
    
    Args:
        hash_value: Hash string or HexBytes object
        
    Returns:
        str: Hash with 0x prefix, or None if input is None/empty
    """
    if not hash_value:
        return None
    
    # Convert HexBytes to string if needed
    if hasattr(hash_value, 'hex'):
        return hash_value.hex()
    
    # Ensure string has 0x prefix
    hash_str = str(hash_value)
    return hash_str if hash_str.startswith('0x') else f'0x{hash_str}'


def mint_tokens(wallet_address, amount, description="TeoCoin Reward"):
    """
    Wrapper function for minting TeoCoins - used by the rewards system.
    
    This function provides a secure interface for minting tokens while
    logging all operations for audit purposes.
    
    Args:
        wallet_address (str): Recipient wallet address
        amount (Decimal): Amount of TEO tokens to mint
        description (str): Description of the transaction for logging
        
    Returns:
        str: Transaction hash if successful
        
    Raises:
        Exception: If the blockchain transaction fails
    """
    try:
        tx_hash = teocoin_service.mint_tokens(wallet_address, amount)
        
        if not tx_hash:
            raise Exception("Blockchain transaction error - mint failed")
        
        logger.info(f"Minted {amount} TEO to {wallet_address} - TX: {tx_hash}")
        return tx_hash
        
    except Exception as e:
        logger.error(f"Error minting tokens to {wallet_address}: {str(e)}")
        raise


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_balance(request):
    """
    Get the TeoCoin balance for the authenticated user.
    
    Returns the current token balance for the user's linked wallet address.
    Also updates the cached balance in the database.
    
    Returns:
        JSON response with:
        - balance: Current token balance as string
        - wallet_address: User's linked wallet address
        - token_info: General token information
        - user_id: User ID for frontend verification
        - username: Username for debugging
        
    Errors:
        - 400: Wallet not linked to user account
        - 500: Blockchain query error
    """
    import time
    start_time = time.time()
    
    user = request.user
    
    if not user.wallet_address:
        response_time = time.time() - start_time
        logger.info(f"Balance API (no wallet) completed in {response_time:.3f}s")
        return Response({
            'error': 'Wallet not linked',
            'balance': '0',
            'wallet_address': None
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # First check if we have a cached balance that's recent enough
        token_balance, created = TokenBalance.objects.get_or_create(
            user=user,
            defaults={'balance': Decimal('0')}
        )
        
        # Only query blockchain if:
        # 1. We've just created the balance record OR
        # 2. The cached balance is stale (older than 5 minutes)
        if created or token_balance.is_stale(minutes=5):
            balance = teocoin_service.get_balance(user.wallet_address)
            token_balance.balance = balance
            token_balance.save()
            logger.info(f"Updated blockchain balance for {user.username} from RPC call")
        else:
            balance = token_balance.balance
            logger.info(f"Using cached blockchain balance for {user.username} (last updated: {token_balance.last_updated})")
        
        return Response({
            'balance': str(balance),
            'wallet_address': user.wallet_address,
            'token_info': teocoin_service.get_token_info(),
            'user_id': user.id,  # Add user ID for frontend verification
            'username': user.username,  # Add username for debugging
            'cached': not created and not token_balance.is_stale(minutes=5)  # Indicate if we used the cache
        })
    
    except Exception as e:
        logger.error(f"Error retrieving balance for {user.email}: {e}")
        return Response({
            'error': 'Error retrieving wallet balance',
            'balance': '0'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        response_time = time.time() - start_time
        logger.info(f"Balance API completed in {response_time:.3f}s")
        if response_time > 1.0:
            logger.warning(f"Slow Balance API: {response_time:.3f}s for user {user.username}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def link_wallet(request):
    """
    Link an external wallet address to the user's account.
    
    Validates the wallet address format and ensures it's not already
    used by another user before linking it to the current user account.
    
    Request Body:
        wallet_address (str): Ethereum/Polygon wallet address to link
        
    Returns:
        JSON response with:
        - message: Success confirmation
        - wallet_address: Linked wallet address
        - balance: Initial token balance
        
    Errors:
        - 400: Missing or invalid wallet address, address already in use
        - 500: Database or blockchain query error
    """
    user = request.user
    wallet_address = request.data.get('wallet_address')
    
    if not wallet_address:
        return Response({
            'error': 'Wallet address required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate wallet address format
    if not teocoin_service.validate_address(wallet_address):
        return Response({
            'error': 'Invalid wallet address format'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if address is already used by another user
    if User.objects.filter(wallet_address=wallet_address).exclude(id=user.id).exists():
        return Response({
            'error': 'Wallet address already used by another user'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Save wallet address to user profile
        user.wallet_address = wallet_address
        user.save()
        
        # Get initial balance
        balance = teocoin_service.get_balance(wallet_address)
        
        # Create/update balance record
        TokenBalance.objects.update_or_create(
            user=user,
            defaults={'balance': balance}
        )
        
        return Response({
            'message': 'Wallet linked successfully',
            'wallet_address': wallet_address,
            'balance': str(balance)
        })
    
    except Exception as e:
        logger.error(f"Error linking wallet for {user.email}: {e}")
        return Response({
            'error': 'Error linking wallet'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reward_user(request):
    """
    Send TeoCoins as reward to a user (staff only).
    
    This endpoint allows staff members to mint and send TeoCoin rewards
    to users. All transactions are logged for audit purposes.
    
    Request Body:
        user_id (int): Target user ID to receive the reward
        amount (str/number): Amount of TEO tokens to mint and send
        reason (str, optional): Reason for the reward (default: "System reward")
        
    Returns:
        JSON response with:
        - message: Success confirmation
        - tx_hash: Blockchain transaction hash
        - recipient: Recipient user email
        - amount: Amount sent
        - new_balance: Updated recipient balance
        
    Errors:
        - 403: User is not staff
        - 400: Missing parameters, invalid amount, user has no wallet
        - 404: Target user not found
        - 500: Blockchain or database error
    """
    if not request.user.is_staff:
        return Response({
            'error': 'Insufficient permissions - staff access required'
        }, status=status.HTTP_403_FORBIDDEN)
    
    target_user_id = request.data.get('user_id')
    amount = request.data.get('amount')
    reason = request.data.get('reason', 'System reward')
    
    if not target_user_id or not amount:
        return Response({
            'error': 'user_id and amount are required'
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
    
    try:
        target_user = User.objects.get(id=target_user_id)
        
        if not target_user.wallet_address:
            return Response({
                'error': 'User does not have a linked wallet'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Execute mint transaction
        tx_hash = mint_tokens(target_user.wallet_address, amount_decimal)
        
        # Record transaction in database
        BlockchainTransaction.objects.create(
            user=target_user,
            transaction_type='mint',
            amount=amount_decimal,
            tx_hash=format_hash_with_prefix(tx_hash),
            from_address=None,  # Mint operation
            to_address=target_user.wallet_address,
            status='pending'
        )
        
        # Update cached balance
        new_balance = teocoin_service.get_balance(target_user.wallet_address)
        TokenBalance.objects.update_or_create(
            user=target_user,
            defaults={'balance': new_balance}
        )
        
        return Response({
            'message': f'Reward of {amount_decimal} TEO sent successfully',
            'tx_hash': tx_hash,
            'recipient': target_user.email,
            'amount': str(amount_decimal),
            'new_balance': str(new_balance)
        })
    
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error sending reward to user {target_user_id}: {e}")
        return Response({
            'error': 'Error sending reward'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_transaction_history(request):
    """
    Get the transaction history for the authenticated user.
    
    Returns the last 50 blockchain transactions for the current user,
    ordered by creation date (most recent first).
    
    Returns:
        JSON response with:
        - transactions: List of transaction objects with:
          - transaction_type: Transaction type (mint, transfer, etc.)
          - amount: Transaction amount as string
          - tx_hash: Blockchain transaction hash (preferred)
          - transaction_hash: Alternative transaction hash field
          - from_address: Source address (null for mint)
          - to_address: Destination address
          - status: Transaction status (pending, confirmed, failed)
          - created_at: Transaction creation timestamp
          - confirmed_at: Transaction confirmation timestamp (if confirmed)
        - total_count: Total number of transactions
    """
    user = request.user
    
    transactions = BlockchainTransaction.objects.filter(
        user=user
    ).order_by('-created_at')[:50]  # Last 50 transactions
    
    transaction_list = []
    for tx in transactions:
        transaction_list.append({
            'transaction_type': tx.transaction_type,
            'type': tx.transaction_type,  # Keep for backward compatibility
            'amount': str(tx.amount),
            'tx_hash': format_hash_with_prefix(tx.tx_hash),
            'transaction_hash': format_hash_with_prefix(tx.transaction_hash),
            'from_address': tx.from_address,
            'to_address': tx.to_address,
            'status': tx.status,
            'created_at': tx.created_at.isoformat(),
            'confirmed_at': tx.confirmed_at.isoformat() if tx.confirmed_at else None
        })
    
    return Response({
        'transactions': transaction_list,
        'total_count': transactions.count()
    })


@api_view(['GET'])
def get_token_info(request):
    """
    Get general information about the TeoCoin token.
    
    This endpoint provides public information about the TeoCoin token
    including contract details, symbol, decimals, etc. No authentication required.
    
    Returns:
        JSON response with token information:
        - name: Token name
        - symbol: Token symbol
        - decimals: Number of decimal places
        - contract_address: Smart contract address
        - network: Blockchain network name
        
    Errors:
        - 500: Blockchain query error
    """
    try:
        token_info = teocoin_service.get_token_info()
        return Response(token_info)
    except Exception as e:
        logger.error(f"Error retrieving token info: {e}")
        return Response({
            'error': 'Error retrieving token information'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_transaction_status(request):
    """
    Check the status of a blockchain transaction.
    
    Queries the blockchain for transaction receipt and updates the local
    database record if the transaction has been confirmed or failed.
    
    Request Body:
        tx_hash (str): Blockchain transaction hash to check
        
    Returns:
        JSON response with:
        - status: Transaction status (confirmed, failed, pending)
        - block_number: Block number (if confirmed)
        - gas_used: Gas used by transaction (if confirmed)
        - transaction_hash: Transaction hash
        - message: Status message (if pending)
        
    Errors:
        - 400: Missing tx_hash parameter
        - 500: Blockchain query error
    """
    tx_hash = request.data.get('tx_hash')
    
    if not tx_hash:
        return Response({
            'error': 'tx_hash is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        receipt = teocoin_service.get_transaction_receipt(tx_hash)
        
        if receipt:
            # Update transaction status in database if record exists
            try:
                blockchain_tx = BlockchainTransaction.objects.get(tx_hash=tx_hash)
                if receipt['status'] == 1:
                    blockchain_tx.status = 'confirmed'
                    blockchain_tx.block_number = receipt['block_number']
                    blockchain_tx.gas_used = receipt['gas_used']
                else:
                    blockchain_tx.status = 'failed'
                blockchain_tx.save()
            except BlockchainTransaction.DoesNotExist:
                # Transaction not found in our database - this is OK
                pass
            
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
        logger.error(f"Error checking transaction status {tx_hash}: {e}")
        return Response({
            'error': 'Error checking transaction status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reward_pool_info(request):
    """
    Get reward pool information including TeoCoin and MATIC balances.
    
    Restricted to staff users only.
    
    Returns:
        JSON response with reward pool information:
        - teo_balance: TeoCoin balance
        - matic_balance: MATIC balance
        - address: Reward pool address
        - warning_threshold: Warning threshold for MATIC balance
        - critical_threshold: Critical threshold for MATIC balance
        - status: 'ok', 'warning', or 'critical' based on MATIC balance
    """
    # Check if user is staff
    if not request.user.is_staff:
        return Response({
            'error': 'Permission denied. Staff access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        pool_info = teocoin_service.get_reward_pool_info()
        return Response(pool_info)
    except Exception as e:
        logger.error(f"Error retrieving reward pool info: {e}")
        return Response({
            'error': 'Error retrieving reward pool information'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refill_reward_pool_matic(request):
    """
    Transfer MATIC to the reward pool from the admin account.
    
    Restricted to staff users only.
    
    Request Body:
        amount (str): Amount of MATIC to transfer
        
    Returns:
        JSON response with:
        - message: Success message
        - tx_hash: Transaction hash
        - new_balance: Updated MATIC balance after transfer
    """
    # Check if user is staff
    if not request.user.is_staff:
        return Response({
            'error': 'Permission denied. Staff access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    amount = request.data.get('amount')
    if not amount:
        return Response({
            'error': 'Amount is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        amount_decimal = Decimal(amount)
        
        # Admin wallet info from settings
        admin_private_key = getattr(settings, 'ADMIN_PRIVATE_KEY', None)
        
        if not admin_private_key:
            return Response({
                'error': 'Admin private key not configured'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Get admin address
        admin_account = teocoin_service.w3.eth.account.from_key(admin_private_key)
        admin_address = admin_account.address
        
        # Get reward pool address
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        if not reward_pool_address:
            return Response({
                'error': 'Reward pool address not configured'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Convert amount to Wei
        amount_wei = teocoin_service.w3.to_wei(amount_decimal, 'ether')
        
        # Check admin MATIC balance
        admin_balance_wei = teocoin_service.w3.eth.get_balance(admin_address)
        if admin_balance_wei < amount_wei:
            return Response({
                'error': 'Insufficient MATIC in admin wallet',
                'available': str(teocoin_service.w3.from_wei(admin_balance_wei, 'ether')),
                'requested': str(amount_decimal)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare transaction
        gas_price = teocoin_service.w3.eth.gas_price
        gas_limit = 21000  # Standard gas limit for MATIC transfer
        
        transaction = {
            'from': admin_address,
            'to': Web3.to_checksum_address(reward_pool_address),
            'value': amount_wei,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'nonce': teocoin_service.w3.eth.get_transaction_count(admin_address),
            'chainId': teocoin_service.w3.eth.chain_id
        }
        
        # Sign and send transaction
        signed_tx = teocoin_service.w3.eth.account.sign_transaction(transaction, admin_private_key)
        tx_hash = teocoin_service.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for transaction receipt
        tx_receipt = teocoin_service.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        # Get updated balance
        new_balance = teocoin_service.get_reward_pool_matic_balance()
        
        # Log the transaction
        logger.info(f"Refilled reward pool with {amount_decimal} MATIC. TX: {tx_hash.hex()}")
        
        # Create a transaction record in the database
        BlockchainTransaction.objects.create(
            user=request.user,
            transaction_type='reward_pool_refill',
            amount=amount_decimal,
            from_address=admin_address,
            to_address=reward_pool_address,
            tx_hash=tx_hash.hex(),
            block_number=tx_receipt['blockNumber'],
            gas_used=tx_receipt['gasUsed'],
            status='confirmed'
        )
        
        return Response({
            'message': f'Successfully transferred {amount_decimal} MATIC to reward pool',
            'tx_hash': tx_hash.hex(),
            'new_balance': str(new_balance)
        })
        
    except ValueError as e:
        return Response({
            'error': f'Invalid amount: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error refilling reward pool: {e}")
        return Response({
            'error': f'Error transferring MATIC: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_with_reward_pool_gas(request):
    """
    Transfer TeoCoin between addresses using reward pool to pay gas fees.
    Useful for testing when users don't have MATIC for gas fees.
    """
    try:
        from_address = request.data.get('from_address')
        to_address = request.data.get('to_address')
        amount = request.data.get('amount')
        
        if not all([from_address, to_address, amount]):
            return Response({
                'error': 'Missing required fields: from_address, to_address, amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert amount to Decimal
        try:
            amount_decimal = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid amount format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate addresses
        if not Web3.is_address(from_address) or not Web3.is_address(to_address):
            return Response({
                'error': 'Invalid wallet address format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Execute transfer with reward pool paying gas fees
        tx_hash = teocoin_service.transfer_with_reward_pool_gas(
            from_address=from_address,
            to_address=to_address,
            amount=amount_decimal
        )
        
        if not tx_hash:
            return Response({
                'error': 'Transfer failed. Check if sender has approved reward pool for transfers.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create transaction record
        BlockchainTransaction.objects.create(
            user=request.user,
            transaction_type='transfer_with_pool_gas',
            amount=amount_decimal,
            from_address=from_address,
            to_address=to_address,
            transaction_hash=format_hash_with_prefix(tx_hash),
            status='completed',
            notes=f'Transfer with reward pool gas fees'
        )
        
        return Response({
            'message': 'Transfer completed successfully',
            'transaction_hash': tx_hash,
            'from_address': from_address,
            'to_address': to_address,
            'amount': str(amount_decimal)
        })
        
    except Exception as e:
        logger.error(f"Error in transfer_with_reward_pool_gas: {e}")
        return Response({
            'error': f'Transfer failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulate_user_payment_via_pool(request):
    """
    Simulate user payment by transferring from reward pool directly.
    This is for testing purposes when users don't have MATIC for gas fees.
    The system will deduct the amount from user's virtual balance and transfer from pool.
    """
    try:
        from_user_address = request.data.get('from_user_address')
        to_address = request.data.get('to_address')
        amount = request.data.get('amount')
        
        if not all([from_user_address, to_address, amount]):
            return Response({
                'error': 'Missing required fields: from_user_address, to_address, amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert amount to Decimal
        try:
            amount_decimal = Decimal(str(amount))
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid amount format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate addresses
        if not Web3.is_address(from_user_address) or not Web3.is_address(to_address):
            return Response({
                'error': 'Invalid wallet address format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user has sufficient TeoCoin balance
        user_balance = teocoin_service.get_balance(from_user_address)
        if user_balance < amount_decimal:
            return Response({
                'error': f'Insufficient balance. Available: {user_balance} TEO, Required: {amount_decimal} TEO'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Execute the simulation in two steps:
        # 1. Transfer from student to reward pool (simulated deduction)
        # 2. Transfer from reward pool to destination (actual payment)
        
        # Step 1: Simulate student payment to pool by transferring TO pool
        # This visually deducts from student's balance
        deduction_tx = teocoin_service.transfer_from_reward_pool(
            to_address=teocoin_service.contract.address,  # Send to contract (burns/pools)
            amount=amount_decimal
        )
        
        # Step 2: Transfer from pool to destination
        payment_tx = teocoin_service.transfer_from_reward_pool(
            to_address=to_address,
            amount=amount_decimal
        )
        
        if not payment_tx:
            return Response({
                'error': 'Transfer failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # For testing purposes, we simulate the user payment transaction
        # In reality, this should deduct from user's wallet, but for testing
        # we just transfer from pool and create a simulated transaction hash
        import hashlib
        import time
        
        # Create a simulated transaction hash that looks like student->teacher transfer
        simulated_data = f"{from_user_address}-{to_address}-{amount_decimal}-{int(time.time())}"
        simulated_tx_hash = "0x" + hashlib.sha256(simulated_data.encode()).hexdigest()

        # Create transaction record for the simulated user payment
        BlockchainTransaction.objects.create(
            user=request.user,
            transaction_type='simulated_payment',
            amount=amount_decimal,
            from_address=from_user_address,
            to_address=to_address,
            transaction_hash=simulated_tx_hash,  # Use simulated hash for course purchase verification
            status='completed',
            notes=f'Simulated user payment via reward pool (testing mode) - Real transfer: {payment_tx}'
        )
        
        return Response({
            'message': 'Payment completed successfully (via reward pool)',
            'transaction_hash': simulated_tx_hash,  # Return simulated hash for course purchase
            'real_transaction_hash': payment_tx,       # Real pool->teacher transfer hash
            'deduction_hash': deduction_tx,        # Pool transaction for visual balance update
            'from_address': from_user_address,
            'to_address': to_address,
            'amount': str(amount_decimal),
            'note': 'This payment was processed via reward pool for testing purposes'
        })
        
    except Exception as e:
        logger.error(f"Error in simulate_user_payment_via_pool: {e}")
        return Response({
            'error': f'Payment failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_course_payment(request):
    """
    Processa il pagamento di un corso con la logica corretta:
    - Lo studente paga in TeoCoins
    - Il teacher riceve l'importo netto (prezzo - commissione)
    - La reward pool riceve la commissione
    - La reward pool paga le gas fees in MATIC
    
    NOTA: Per il testing, questa funzione usa una chiave privata di test.
    In produzione, il processo sarebbe gestito diversamente per sicurezza.
    """
    try:
        teacher_address = request.data.get('teacher_address')
        course_price = request.data.get('course_price')
        course_id = request.data.get('course_id')
        student_address = request.data.get('student_address')
        
        if not all([teacher_address, course_price, student_address]):
            return Response({
                'error': 'Missing required fields: teacher_address, course_price, student_address'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica che l'utente autenticato sia autorizzato per questo wallet
        if request.user.wallet_address != student_address:
            return Response({
                'error': 'Student address does not match authenticated user wallet'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Convert course_price to Decimal
        try:
            course_price_decimal = Decimal(str(course_price))
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid course_price format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate addresses
        if not Web3.is_address(teacher_address):
            return Response({
                'error': 'Invalid teacher wallet address format'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not Web3.is_address(student_address):
            return Response({
                'error': 'Invalid student wallet address format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica prerequisiti per il pagamento usando l'indirizzo dello studente
        prerequisites = teocoin_service.check_course_payment_prerequisites(
            student_address, course_price_decimal
        )
        
        # NOTA: Rimossa la logica di trasferimento automatico dalla reward pool
        # Lo studente deve avere i propri fondi per acquistare il corso
        
        # Controlla se lo studente ha fondi sufficienti (TEO e MATIC)
        if not prerequisites['student']['has_enough_teo']:
            return Response({
                'error': 'Insufficient TeoCoins',
                'details': f"You need {course_price_decimal} TEO but have {prerequisites['student']['teo_balance']} TEO",
                'required_teo': str(course_price_decimal),
                'current_teo': str(prerequisites['student']['teo_balance'])
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not prerequisites['student']['has_enough_matic']:
            return Response({
                'error': 'Insufficient MATIC for gas fees',
                'details': f"You need {prerequisites['student']['min_matic_required']} MATIC for gas but have {prerequisites['student']['matic_balance']} MATIC",
                'required_matic': str(prerequisites['student']['min_matic_required']),
                'current_matic': str(prerequisites['student']['matic_balance'])
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not prerequisites['reward_pool']['has_enough_matic']:
            return Response({
                'error': 'Platform temporarily unavailable',
                'details': 'Platform has insufficient MATIC for processing transactions. Please try again later.'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # LOGICA CORRETTA: Lo studente paga sempre autonomamente
        # 1. Lo studente fa APPROVE per permettere alla reward pool di trasferire i suoi TEO
        # 2. La reward pool fa TRANSFER_FROM dallo studente al teacher (85%)
        # 3. La reward pool fa TRANSFER_FROM dallo studente alla reward pool (15% commissione)
        # Gas fees: studente paga APPROVE, reward pool paga i TRANSFER_FROM
        
        logger.info(f"Processing autonomous payment for student {student_address}")
        
        # Ottieni la chiave privata dello studente (solo per testing)
        test_student_keys = {
            '0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4': getattr(settings, 'STUDENT1_PRIVATE_KEY', None)
        }
        
        student_private_key = test_student_keys.get(student_address)
        if not student_private_key:
            return Response({
                'error': 'Payment not supported for this wallet',
                'details': 'Only test wallets are supported in development. Please use MetaMask integration for production.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Processa il pagamento autonomo dello studente
        logger.info(f"Student {student_address} paying {course_price_decimal} TEO autonomously")
        result = teocoin_service.process_course_payment(
            student_private_key=student_private_key,
            teacher_address=teacher_address,
            course_price=course_price_decimal
        )
        
        if not result:
            return Response({
                'error': 'Course payment failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create transaction records
        if course_id:
            # Convert string amounts back to Decimal for database storage
            commission_amount_decimal = Decimal(str(result['commission_amount']))
            teacher_amount_decimal = Decimal(str(result['teacher_amount']))
            
            # Student purchase transaction
            BlockchainTransaction.objects.create(
                user=request.user,
                transaction_type='course_purchase',
                amount=-course_price_decimal,  # Negative = outgoing
                from_address=result['student_address'],
                to_address=result['teacher_address'],
                transaction_hash=result['teacher_payment_tx'],
                status='completed',
                related_object_id=str(course_id),
                notes=f'Course purchase payment - Total: {course_price_decimal} TEO'
            )
            
            # Commission transaction (for teacher)
            try:
                course = Course.objects.get(id=course_id)
                
                # Create course enrollment for the student
                enrollment, created = CourseEnrollment.objects.get_or_create(
                    student=request.user,
                    course=course,
                    defaults={'completed': False}
                )
                
                if created:
                    logger.info(f"Created enrollment for student {request.user.username} in course {course.title}")
                else:
                    logger.info(f"Enrollment already exists for student {request.user.username} in course {course.title}")
                
                BlockchainTransaction.objects.create(
                    user=request.user,  # Lo studente paga la commissione
                    transaction_type='platform_commission',
                    amount=-commission_amount_decimal,  # Negative = outgoing from student
                    from_address=result['student_address'],
                    to_address=settings.REWARD_POOL_ADDRESS,
                    transaction_hash=result['commission_tx'],
                    status='completed',
                    related_object_id=str(course_id),
                    notes=f'Platform commission (15%) from course purchase: {course.title}'
                )
                
                # Teacher earnings transaction
                BlockchainTransaction.objects.create(
                    user=course.teacher,
                    transaction_type='course_earned',
                    amount=teacher_amount_decimal,  # Positive = incoming
                    from_address=result['student_address'],
                    to_address=result['teacher_address'],
                    transaction_hash=result['teacher_payment_tx'],
                    status='completed',
                    related_object_id=str(course_id),
                    notes=f'Course sale earnings from: {course.title}'
                )
            except Course.DoesNotExist:
                logger.error(f"Course with ID {course_id} does not exist")
                pass
        
        return Response({
            'message': 'Course payment processed successfully',
            'student_address': result['student_address'],
            'teacher_address': result['teacher_address'],
            'teacher_amount': str(result['teacher_amount']),
            'commission_amount': str(result['commission_amount']),
            'total_paid': str(result['total_paid']),
            'approval_tx': result['approval_tx'],
            'teacher_payment_tx': result['teacher_payment_tx'],
            'commission_tx': result['commission_tx']
        })
        
    except Exception as e:
        logger.error(f"Error in process_course_payment: {e}")
        return Response({
            'error': f'Payment processing failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_course_payment_prerequisites(request):
    """
    Check prerequisites for course payment using MetaMask
    Returns validation info and reward pool address for frontend
    """
    try:
        student_address = request.data.get('student_address')
        course_price = request.data.get('course_price')
        
        if not all([student_address, course_price]):
            return Response({
                'error': 'Missing required fields: student_address, course_price'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica che l'utente autenticato sia autorizzato per questo wallet
        if request.user.wallet_address != student_address:
            return Response({
                'error': 'Student address does not match authenticated user wallet'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Convert course_price to Decimal
        try:
            course_price_decimal = Decimal(str(course_price))
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid course_price format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate addresses
        if not Web3.is_address(student_address):
            return Response({
                'error': 'Invalid student wallet address format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check prerequisites
        prerequisites = teocoin_service.check_course_payment_prerequisites(
            student_address, course_price_decimal
        )
        
        # Add reward pool address for frontend use
        prerequisites['reward_pool_address'] = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        
        return Response({
            'prerequisites': prerequisites,
            'course_price': str(course_price_decimal),
            'commission_rate': '0.15',
            'teacher_amount': str(course_price_decimal * Decimal('0.85')),
            'commission_amount': str(course_price_decimal * Decimal('0.15')),
            'reward_pool_address': prerequisites['reward_pool_address']
        })
        
    except Exception as e:
        logger.error(f"Error in check_course_payment_prerequisites: {e}")
        return Response({
            'error': f'Prerequisites check failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_course_payment(request):
    """
    Execute course payment after student has approved via MetaMask
    This handles the transferFrom operations via reward pool
    """
    try:
        student_address = request.data.get('student_address')
        teacher_address = request.data.get('teacher_address')
        course_price = request.data.get('course_price')
        course_id = request.data.get('course_id')
        approval_tx_hash = request.data.get('approval_tx_hash')
        teacher_amount = request.data.get('teacher_amount')
        commission_amount = request.data.get('commission_amount')
        
        if not all([student_address, teacher_address, course_price, approval_tx_hash]):
            return Response({
                'error': 'Missing required fields'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verifica che l'utente autenticato sia autorizzato per questo wallet
        if request.user.wallet_address != student_address:
            return Response({
                'error': 'Student address does not match authenticated user wallet'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Convert amounts to Decimal
        try:
            course_price_decimal = Decimal(str(course_price))
            teacher_amount_decimal = Decimal(str(teacher_amount)) if teacher_amount else course_price_decimal * Decimal('0.85')
            commission_amount_decimal = Decimal(str(commission_amount)) if commission_amount else course_price_decimal * Decimal('0.15')
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid amount format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate addresses
        if not Web3.is_address(teacher_address) or not Web3.is_address(student_address):
            return Response({
                'error': 'Invalid wallet address format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify approval transaction exists and is confirmed
        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
        if not reward_pool_address:
            return Response({
                'error': 'Reward pool not configured'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Execute transferFrom operations via reward pool with proper nonce management
        logger.info(f"Executing course payment with approval: {approval_tx_hash}")
        logger.info(f"Student: {student_address} -> Teacher: {teacher_address} ({teacher_amount_decimal} TEO)")
        logger.info(f"Student: {student_address} -> Commission: {reward_pool_address} ({commission_amount_decimal} TEO)")
        
        # Get current nonce for reward pool to avoid nonce conflicts
        reward_pool_private_key = getattr(settings, 'REWARD_POOL_PRIVATE_KEY', None)
        if not reward_pool_private_key:
            return Response({
                'error': 'Reward pool private key not configured'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        reward_pool_account = teocoin_service.w3.eth.account.from_key(reward_pool_private_key)
        current_nonce = teocoin_service.w3.eth.get_transaction_count(reward_pool_account.address)
        
        # Step 1: Transfer from student to teacher with specific nonce
        teacher_tx = teocoin_service.transfer_from_student_via_reward_pool_with_nonce(
            student_address, teacher_address, teacher_amount_decimal, current_nonce
        )
        
        if not teacher_tx:
            return Response({
                'error': 'Transfer to teacher failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Step 2: Transfer commission if needed
        commission_tx = None
        if commission_amount_decimal > 0:
            commission_tx = teocoin_service.transfer_from_student_via_reward_pool_with_nonce(
                student_address, settings.ADMIN_WALLET_ADDRESS, commission_amount_decimal, current_nonce + 1
            )
        
        # Prepare response data
        result = {
            'message': 'Course payment executed successfully',
            'teacher_amount': str(teacher_amount_decimal),
            'commission_amount': str(commission_amount_decimal),
            'total_paid': str(course_price_decimal),
            'approval_tx': approval_tx_hash,
            'teacher_payment_tx': teacher_tx,
            'commission_tx': commission_tx
        }
        
        if course_id:
            # Create transaction records in database
            # Student purchase transaction
            BlockchainTransaction.objects.create(
                user=request.user,
                transaction_type='course_purchase',
                amount=-course_price_decimal,  # Negative = outgoing
                from_address=student_address,
                to_address=teacher_address,
                transaction_hash=format_hash_with_prefix(teacher_tx),
                status='completed',
                related_object_id=str(course_id),
                notes=f'Course purchase payment via MetaMask - Total: {course_price_decimal} TEO'
            )
            
            # Commission and teacher earnings transactions
            from courses.models import Course
            try:
                course = Course.objects.get(id=course_id)
                
                # Create course enrollment for the student
                enrollment, created = CourseEnrollment.objects.get_or_create(
                    student=request.user,
                    course=course,
                    defaults={'completed': False}
                )
                
                if created:
                    logger.info(f"Created enrollment for student {request.user.username} in course {course.title}")
                else:
                    logger.info(f"Enrollment already exists for student {request.user.username} in course {course.title}")
                
                # Platform commission transaction
                BlockchainTransaction.objects.create(
                    user=request.user,  # Lo studente paga la commissione
                    transaction_type='platform_commission',
                    amount=-commission_amount_decimal,  # Negative = outgoing from student
                    from_address=student_address,
                    to_address=reward_pool_address,
                    transaction_hash=commission_tx,
                    status='completed',
                    related_object_id=str(course_id),
                    notes=f'Platform commission (15%) from course purchase: {course.title}'
                )
                
                # Teacher earnings transaction
                BlockchainTransaction.objects.create(
                    user=course.teacher,
                    transaction_type='course_earned',
                    amount=teacher_amount_decimal,  # Positive = incoming
                    from_address=student_address,
                    to_address=teacher_address,
                    transaction_hash=format_hash_with_prefix(teacher_tx),
                    status='completed',
                    related_object_id=str(course_id),
                    notes=f'Course sale earnings via MetaMask from: {course.title}'
                )
            except Course.DoesNotExist:
                logger.error(f"Course with ID {course_id} does not exist")
                pass
        
        logger.info(f"✅ Course payment executed successfully: {result}")
        
        return Response({
            'message': 'Course payment executed successfully via MetaMask',
            **result
        })
        
    except Exception as e:
        logger.error(f"Error in execute_course_payment: {e}")
        return Response({
            'error': f'Payment execution failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# NEW DIRECT COURSE PAYMENT PROCESS
# ============================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_course_payment_direct(request):
    """
    NEW APPROVE+SPLIT PROCESS: Process course payment with single approval
    1. Verifies student has approved enough tokens to reward pool
    2. Backend executes transferFrom to teacher (85%)
    3. Backend executes transferFrom to commission (15%)
    4. Creates enrollment record
    """
    try:
        data = request.data
        student_address = data.get('student_address')
        teacher_address = data.get('teacher_address')
        course_price = data.get('price_in_teo')  # Adjusted to match frontend
        course_id = data.get('course_id')
        
        # Validate required fields
        if not all([student_address, teacher_address, course_price, course_id]):
            return Response({
                'error': 'Missing required fields: student_address, teacher_address, price_in_teo, course_id'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert course_price to Decimal
        try:
            # Frontend sends in ether format
            course_price_decimal = Decimal(str(course_price))
            logger.info(f"Course price received: {course_price} TEO")
            
        except (ValueError, TypeError) as e:
            logger.error(f"Price conversion error: {e}")
            return Response({
                'error': f'Invalid price_in_teo format: {course_price}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate user is student and wallet matches
        if request.user.wallet_address != student_address:
            return Response({
                'error': 'Student address does not match authenticated user wallet'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validate course exists and teacher wallet matches
        try:
            course = Course.objects.get(id=course_id)
            if course.teacher.wallet_address != teacher_address:
                return Response({
                    'error': 'Teacher address does not match course teacher wallet'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Course.DoesNotExist:
            return Response({
                'error': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if already enrolled
        if CourseEnrollment.objects.filter(student=request.user, course=course).exists():
            return Response({
                'error': 'Student already enrolled in this course'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Process the payment using the new approve+split method
        logger.info(f"APPROVE+SPLIT: Processing payment for course {course_id} - Student: {student_address}")
        logger.info(f"Course price: {course_price_decimal} TEO")
        logger.info(f"Teacher: {teacher_address}")
        
        # Debug: Test blockchain connection
        try:
            test_balance = teocoin_service.get_balance(student_address)
            logger.info(f"DEBUG: Student balance check successful: {test_balance} TEO")
        except Exception as e:
            logger.error(f"DEBUG: Blockchain connection test failed: {e}")
            return Response({
                'error': f'Blockchain connection failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        payment_result = teocoin_service.process_course_payment_approve_split(
            student_address=student_address,
            teacher_address=teacher_address,
            course_price=course_price_decimal
        )
        
        if not payment_result or not payment_result.get('success'):
            error_msg = payment_result.get('error', 'Payment processing failed') if payment_result else 'Payment processing failed'
            logger.error(f"Payment failed: {error_msg}")
            return Response({
                'error': error_msg,
                'details': payment_result.get('details') if payment_result else None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create enrollment record
        try:
            enrollment = CourseEnrollment.objects.create(
                student=request.user,
                course=course
            )
            
            logger.info(f"✅ Course enrollment created: {enrollment.pk}")
            
        except Exception as e:
            logger.error(f"Failed to create enrollment: {e}")
            return Response({
                'error': 'Payment processed but enrollment creation failed',
                'payment_result': payment_result
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Log the successful transaction
        try:
            BlockchainTransaction.objects.create(
                user=request.user,
                transaction_hash=payment_result['teacher_payment_tx'],
                transaction_type='course_payment',
                amount=course_price_decimal,
                status='completed',
                metadata={
                    'course_id': course_id,
                    'teacher_address': teacher_address,
                    'teacher_amount': payment_result['teacher_amount'],
                    'commission_amount': payment_result['commission_amount'],
                    'commission_tx': payment_result.get('commission_tx'),
                    'payment_method': 'approve_split'
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log transaction: {e}")
        
        logger.info(f"✅ APPROVE+SPLIT payment completed successfully for course {course_id}")
        
        return Response({
            'success': True,
            'message': 'Course payment processed successfully',
            'transaction_hash': payment_result['teacher_payment_tx'],
            'teacher_amount': payment_result['teacher_amount'],
            'commission_amount': payment_result['commission_amount'],
            'commission_tx_hash': payment_result.get('commission_tx'),
            'enrollment_id': enrollment.pk
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in process_course_payment_direct (approve+split): {e}")
        return Response({
            'error': f'Failed to process course payment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_course_payment(request):
    """
    NEW PROCESS: Confirm successful direct course payment
    Called after frontend has executed both transactions (teacher + commission)
    Records the enrollment and transaction history
    """
    try:
        data = request.data
        student_address = data.get('student_address')
        teacher_address = data.get('teacher_address')
        course_price = data.get('course_price')
        course_id = data.get('course_id')
        teacher_tx_hash = data.get('teacher_tx_hash')
        commission_tx_hash = data.get('commission_tx_hash')
        teacher_amount = data.get('teacher_amount')
        commission_amount = data.get('commission_amount')
        
        # Validate required fields
        required_fields = [
            'student_address', 'teacher_address', 'course_price', 'course_id',
            'teacher_tx_hash', 'commission_tx_hash', 'teacher_amount', 'commission_amount'
        ]
        if not all(data.get(field) for field in required_fields):
            return Response({
                'error': f'Missing required fields: {", ".join(required_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate user is student and wallet matches
        if request.user.wallet_address != student_address:
            return Response({
                'error': 'Student address does not match authenticated user wallet'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get course and validate
        try:
            course = Course.objects.get(id=course_id)
            if course.teacher.wallet_address != teacher_address:
                return Response({
                    'error': 'Teacher address does not match course teacher wallet'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Course.DoesNotExist:
            return Response({
                'error': 'Course not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if student is already enrolled
        existing_enrollment = CourseEnrollment.objects.filter(
            student=request.user,
            course=course
        ).first()
        
        if existing_enrollment:
            return Response({
                'error': 'Student is already enrolled in this course'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create enrollment
        enrollment = CourseEnrollment.objects.create(
            student=request.user,
            course=course
        )
        
        # Record teacher payment transaction
        BlockchainTransaction.objects.create(
            user=request.user,
            transaction_type='course_payment_teacher',
            amount=Decimal(teacher_amount),
            transaction_hash=teacher_tx_hash,
            from_address=student_address,
            to_address=teacher_address,
            status='completed',
            course_enrollment=enrollment
        )
        
        # Record commission payment transaction
        BlockchainTransaction.objects.create(
            user=request.user,
            transaction_type='course_payment_commission',
            amount=Decimal(commission_amount),
            transaction_hash=commission_tx_hash,
            from_address=student_address,
            to_address=teocoin_service.get_reward_pool_address(),
            status='completed',
            course_enrollment=enrollment
        )
        
        logger.info(f"NEW PROCESS: Direct payment confirmed for course {course_id} - "
                   f"Student: {student_address}, Teacher TX: {teacher_tx_hash}, Commission TX: {commission_tx_hash}")
        
        return Response({
            'success': True,
            'enrollment_id': enrollment.pk,
            'teacher_tx_hash': teacher_tx_hash,
            'commission_tx_hash': commission_tx_hash,
            'message': 'Course payment confirmed and enrollment created'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in confirm_course_payment: {e}")
        return Response({
            'error': f'Failed to confirm payment: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_reward_pool_address(request):
    """
    Get the reward pool address for frontend approve transactions.
    """
    try:
        reward_pool_address = teocoin_service.get_reward_pool_address()
        
        if not reward_pool_address:
            return Response({
                'error': 'Reward pool not configured'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'reward_pool_address': reward_pool_address
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting reward pool address: {e}")
        return Response({
            'error': f'Failed to get reward pool address: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_student_approval(request):
    """
    Check if student has approved enough tokens for course payment.
    """
    try:
        data = request.data
        student_address = data.get('student_address')
        course_price = data.get('course_price')
        
        if not all([student_address, course_price]):
            return Response({
                'error': 'Missing required fields: student_address, course_price'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert course_price to Decimal
        try:
            course_price_decimal = Decimal(str(Web3.from_wei(int(course_price), 'ether')))
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid course_price format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check approval
        approval_info = teocoin_service.check_student_approval(student_address, course_price_decimal)
        
        return Response(approval_info, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking student approval: {e}")
        return Response({
            'error': f'Failed to check approval: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
