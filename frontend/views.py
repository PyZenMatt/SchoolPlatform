"""
Frontend Views for TeoCoin Withdrawal System
Serves the MetaMask integration frontend
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import json

from services.db_teocoin_service import db_teocoin_service


@login_required
def teocoin_withdrawal_page(request):
    """
    Serve the TeoCoin withdrawal frontend page.
    """
    # Get user's current DB balance for initial display
    try:
        balance = db_teocoin_service.get_user_balance(request.user)
        user_balance = balance['available_balance'] if balance else Decimal('0')
    except Exception:
        user_balance = Decimal('0')
    
    context = {
        'user_balance': str(user_balance),
        'user_wallet': getattr(request.user, 'wallet_address', '') or '',
        'min_withdrawal': '10.00',
        'max_withdrawal': '10000.00',
    }
    
    return render(request, 'teocoin_withdrawal.html', context)


@login_required
@require_http_methods(['GET'])
def get_user_db_balance(request):
    """
    API endpoint to get user's database TeoCoin balance.
    """
    try:
        balance = db_teocoin_service.get_user_balance(request.user)
        
        if balance:
            return JsonResponse({
                'success': True,
                'available_balance': str(balance['available_balance']),
                'staked_balance': str(balance['staked_balance']),
                'pending_withdrawal': str(balance['pending_withdrawal']),
                'total_balance': str(balance['total_balance'])
            })
        else:
            return JsonResponse({
                'success': True,
                'available_balance': '0.00',
                'staked_balance': '0.00', 
                'pending_withdrawal': '0.00',
                'total_balance': '0.00'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to retrieve balance: {str(e)}'
        }, status=500)


@login_required 
@require_http_methods(['POST'])
def demo_add_balance(request):
    """
    Demo endpoint to add TeoCoin balance for testing.
    THIS IS FOR TESTING ONLY - Remove in production.
    """
    try:
        data = json.loads(request.body)
        amount = Decimal(str(data.get('amount', 0)))
        
        if amount <= 0 or amount > 1000:
            return JsonResponse({
                'success': False,
                'error': 'Amount must be between 0.01 and 1000 TEO'
            }, status=400)
        
        # Add balance using DB service
        result = db_teocoin_service.add_balance(
            user=request.user,
            amount=amount,
            transaction_type='demo_credit',
            description=f'Demo credit: {amount} TEO added for testing'
        )
        
        if result:
            # Get updated balance
            updated_balance = db_teocoin_service.get_user_balance(request.user)
            return JsonResponse({
                'success': True,
                'message': f'Added {amount} TEO to your balance',
                'new_balance': str(updated_balance['available_balance'])
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to add balance'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to add balance: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(['GET'])
def withdrawal_demo_page(request):
    """
    Serve a comprehensive demo page for testing the withdrawal system.
    """
    try:
        balance = db_teocoin_service.get_user_balance(request.user)
        user_balance = balance['available_balance'] if balance else Decimal('0')
    except Exception:
        user_balance = Decimal('0')
    
    context = {
        'user': request.user,
        'user_balance': str(user_balance),
        'user_email': request.user.email,
        'user_wallet': request.user.wallet_address or '',
        'is_demo': True,
    }
    
    return render(request, 'withdrawal_demo.html', context)


@login_required
def integrated_dashboard(request):
    """
    Serve the integrated dashboard with TeoCoin withdrawal functionality.
    This demonstrates how to embed the TeoCoin widget into existing dashboards.
    """
    return render(request, 'dashboard_with_teocoin.html', {
        'user': request.user,
        'title': 'Dashboard with TeoCoin Withdrawal'
    })


@login_required 
@require_http_methods(['GET'])
def teocoin_widget_demo(request):
    """
    Demo page showing just the TeoCoin widget in isolation.
    """
    try:
        balance = db_teocoin_service.get_user_balance(request.user)
        user_balance = balance['available_balance'] if balance else Decimal('0')
    except Exception:
        user_balance = Decimal('0')
    
    context = {
        'user': request.user,
        'user_balance': str(user_balance),
        'title': 'TeoCoin Widget Demo'
    }
    
    return render(request, 'widget_demo.html', context)
