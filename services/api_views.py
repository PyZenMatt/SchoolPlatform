"""
Django REST API endpoints for TEO earning system
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from services.teo_earning_service import teo_earning_service, TeoEarning
from blockchain.blockchain import TeoCoinService
# ...existing imports...

# Add staking service import
from services.teocoin_staking_service import TeoCoinStakingService

import logging

logger = logging.getLogger(__name__)

# ========== STAKING API ENDPOINTS ==========

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staking_info(request):
    """Get user's complete staking information"""
    try:
        staking_service = TeoCoinStakingService()
        wallet_address = request.user.userprofile.wallet_address
        
        if not wallet_address:
            return Response({
                'error': 'No wallet address associated with account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get staking info from blockchain
        staking_data = staking_service.get_user_staking_info(wallet_address)
        
        # Get platform statistics
        platform_stats = staking_service.get_platform_stats()
        
        return Response({
            'user_staking': staking_data,
            'platform_stats': platform_stats,
            'tier_config': staking_service.TIER_CONFIG
        })
        
    except Exception as e:
        logger.error(f"Error fetching staking info for user {request.user.id}: {e}")
        return Response({
            'error': 'Failed to fetch staking information'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def stake_tokens(request):
    """Stake TEO tokens to improve commission rate"""
    try:
        amount = request.data.get('amount')
        
        if not amount or float(amount) <= 0:
            return Response({
                'error': 'Invalid amount specified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        staking_service = TeoCoinStakingService()
        wallet_address = request.user.userprofile.wallet_address
        
        if not wallet_address:
            return Response({
                'error': 'No wallet address associated with account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Execute staking transaction
        result = staking_service.stake_tokens(wallet_address, float(amount))
        
        if result['success']:
            return Response({
                'success': True,
                'transaction_hash': result['transaction_hash'],
                'new_tier': result['new_tier'],
                'new_total_staked': result['new_total_staked'],
                'message': f'Successfully staked {amount} TEO'
            })
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error staking tokens for user {request.user.id}: {e}")
        return Response({
            'error': 'Failed to stake tokens'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unstake_tokens(request):
    """Unstake TEO tokens"""
    try:
        amount = request.data.get('amount')
        
        if not amount or float(amount) <= 0:
            return Response({
                'error': 'Invalid amount specified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        staking_service = TeoCoinStakingService()
        wallet_address = request.user.userprofile.wallet_address
        
        if not wallet_address:
            return Response({
                'error': 'No wallet address associated with account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Execute unstaking transaction
        result = staking_service.unstake_tokens(wallet_address, float(amount))
        
        if result['success']:
            return Response({
                'success': True,
                'transaction_hash': result['transaction_hash'],
                'new_tier': result['new_tier'],
                'new_total_staked': result['new_total_staked'],
                'message': f'Successfully unstaked {amount} TEO'
            })
        else:
            return Response({
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error unstaking tokens for user {request.user.id}: {e}")
        return Response({
            'error': 'Failed to unstake tokens'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staking_tiers(request):
    """Get all staking tier configurations"""
    try:
        staking_service = TeoCoinStakingService()
        
        return Response({
            'tiers': staking_service.TIER_CONFIG,
            'max_supply': 10000,  # TEO total supply
            'currency': 'TEO'
        })
        
    except Exception as e:
        logger.error(f"Error fetching staking tiers: {e}")
        return Response({
            'error': 'Failed to fetch staking tiers'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def commission_calculator(request):
    """Calculate commission rates and tier progression"""
    try:
        current_stake = float(request.GET.get('current_stake', 0))
        staking_service = TeoCoinStakingService()
        
        # Calculate current tier and commission rate
        current_tier = staking_service.calculate_tier(current_stake)
        current_rate = staking_service.TIER_CONFIG[current_tier]['commission_rate']
        
        # Calculate next tier requirements
        next_tier_info = None
        if current_tier < 4:  # Not at Diamond tier yet
            next_tier = current_tier + 1
            next_tier_requirement = staking_service.TIER_CONFIG[next_tier]['min_stake']
            tokens_needed = max(0, next_tier_requirement - current_stake)
            
            next_tier_info = {
                'tier': next_tier,
                'name': staking_service.TIER_CONFIG[next_tier]['name'],
                'commission_rate': staking_service.TIER_CONFIG[next_tier]['commission_rate'],
                'tokens_needed': tokens_needed
            }
        
        return Response({
            'current_tier': {
                'tier': current_tier,
                'name': staking_service.TIER_CONFIG[current_tier]['name'],
                'commission_rate': current_rate,
                'commission_percentage': current_rate / 100
            },
            'next_tier': next_tier_info,
            'potential_savings': {
                'current_commission': f"{current_rate / 100}%",
                'max_commission': f"{staking_service.TIER_CONFIG[4]['commission_rate'] / 100}%"
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating commission: {e}")
        return Response({
            'error': 'Failed to calculate commission'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def earnings_history(request):
    """Get user's TEO earning history"""
    try:
        user_id = request.user.id
        limit = int(request.GET.get('limit', 50))
        
        history = teo_earning_service.get_user_earnings_history(user_id, limit)
        total_earned = teo_earning_service.get_user_total_earned(user_id)
        
        return Response({
            'earnings_history': history,
            'total_earned': float(total_earned),
            'count': len(history)
        })
        
    except Exception as e:
        logger.error(f"Failed to get earnings history: {e}")
        return Response(
            {'error': 'Failed to fetch earnings history'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def welcome_bonus(request):
    """Give welcome bonus to user (if eligible)"""
    try:
        user_id = request.user.id
        
        # Check if user already has a welcome bonus
        existing = TeoEarning.objects.filter(
            user_id=user_id,
            earning_type='welcome_bonus'
        ).exists()
        
        if existing:
            return Response({
                'bonus_given': False,
                'reason': 'Welcome bonus already received'
            })
        
        # Check if user has wallet address
        wallet_address = getattr(request.user, 'wallet_address', None) or getattr(request.user, 'amoy_address', None)
        
        if not wallet_address:
            return Response({
                'bonus_given': False,
                'reason': 'Wallet address required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Give welcome bonus
        success = teo_earning_service.give_welcome_bonus(user_id)
        
        if success:
            return Response({
                'bonus_given': True,
                'amount': float(teo_earning_service.EARNING_RATES['welcome_bonus']),
                'message': 'Welcome bonus granted!'
            })
        else:
            return Response({
                'bonus_given': False,
                'reason': 'Failed to process welcome bonus'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Welcome bonus error: {e}")
        return Response(
            {'error': 'Failed to process welcome bonus'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teo_balance(request):
    """Get user's current TEO balance from blockchain"""
    try:
        wallet_address = getattr(request.user, 'wallet_address', None) or getattr(request.user, 'amoy_address', None)
        
        if not wallet_address:
            return Response({
                'balance': 0,
                'error': 'No wallet address found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        teo_service = TeoCoinService()
        balance = teo_service.get_balance(wallet_address)
        
        return Response({
            'balance': float(balance),
            'wallet_address': wallet_address,
            'currency': 'TEO'
        })
        
    except Exception as e:
        logger.error(f"Failed to get TEO balance: {e}")
        return Response(
            {'error': 'Failed to fetch balance'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def earning_stats(request):
    """Get user's earning statistics and opportunities"""
    try:
        user_id = request.user.id
        
        # Get basic stats
        total_earned = teo_earning_service.get_user_total_earned(user_id)
        
        # Get earning breakdown by type
        earning_breakdown = {}
        for earning_type in teo_earning_service.EARNING_RATES.keys():
            count = TeoEarning.objects.filter(
                user_id=user_id,
                earning_type=earning_type
            ).count()
            
            total_for_type = TeoEarning.objects.filter(
                user_id=user_id,
                earning_type=earning_type
            ).aggregate(total=models.Sum('amount'))['total'] or 0
            
            earning_breakdown[earning_type] = {
                'count': count,
                'total': float(total_for_type)
            }
        
        # Get earning opportunities (rates)
        opportunities = {
            earning_type: float(rate)
            for earning_type, rate in teo_earning_service.EARNING_RATES.items()
        }
        
        return Response({
            'total_earned': float(total_earned),
            'earning_breakdown': earning_breakdown,
            'earning_opportunities': opportunities,
            'currency': 'TEO'
        })
        
    except Exception as e:
        logger.error(f"Failed to get earning stats: {e}")
        return Response(
            {'error': 'Failed to fetch earning statistics'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
