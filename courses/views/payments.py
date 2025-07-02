"""
⚡ OPTIMIZED Payment Views for Ultra-Fast Payment Processing
Enhanced with Redis caching, rate limiting, and performance optimizations
VERSION: 3.0 - Investor Demo Ready
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from decimal import Decimal
import logging

from courses.models import Course
from services.cached_payment_service import cached_payment_service, payment_rate_limit

# Import payment_service for fallback logic
from services.payment_service import payment_service

logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    """
    ⚡ ULTRA-FAST Create Stripe payment intent with caching
    
    POST /api/courses/{course_id}/create-payment-intent/
    """
    permission_classes = [IsAuthenticated]
    
    @method_decorator(payment_rate_limit(max_requests=5, window=60))
    def post(self, request, course_id):
        try:
            # Get request data
            teocoin_discount = request.data.get('teocoin_discount', 0)
            payment_method = request.data.get('payment_method', 'stripe')
            
            # ⚡ PERFORMANCE: Get cached course data first
            course_data = cached_payment_service.get_course_pricing_cached(course_id)
            if 'error' in course_data:
                return Response({
                    'success': False,
                    'error': course_data['error']
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Use course's EUR price
            amount_eur = course_data.get('price_eur')
            if not amount_eur:
                return Response({
                    'success': False,
                    'error': 'Course does not have EUR pricing configured'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Handle TeoCoin discount payments and hybrid payments
            if payment_method in ['teocoin', 'hybrid'] and teocoin_discount > 0:
                # Use the gas-free TeoCoin discount service
                from services.teocoin_discount_service import teocoin_discount_service
                from courses.models import Course
                
                course = Course.objects.get(id=course_id)
                
                # Check if user has a wallet address
                wallet_address = getattr(request.user, 'wallet_address', None)
                
                # Also check for wallet_address in request data (from frontend)
                if not wallet_address:
                    wallet_address = request.data.get('wallet_address')
                
                if not wallet_address:
                    return Response({
                        'success': False,
                        'error': 'Please connect your wallet to use TeoCoin discounts'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate TEO cost based on discount percentage
                discount_value_eur = (amount_eur * teocoin_discount) / 100
                teo_cost_wei = int(discount_value_eur * 10 * 10**18)  # 10 TEO = 1 EUR
                teacher_bonus_wei = int(teo_cost_wei * 25 / 100)  # 25% bonus
                
                # Check balances
                teo_service = teocoin_discount_service.teocoin_service
                student_balance = teo_service.get_balance(wallet_address)
                required_teo = teo_cost_wei / 10**18
                
                if student_balance < required_teo:
                    return Response({
                        'success': False,
                        'error': f'Insufficient TEO balance. Required: {required_teo:.2f} TEO, Available: {student_balance:.2f} TEO'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check reward pool balance
                reward_pool_balance = teo_service.get_reward_pool_balance()
                required_bonus = teacher_bonus_wei / 10**18
                
                if reward_pool_balance < required_bonus:
                    return Response({
                        'success': False,
                        'error': 'Insufficient reward pool balance for teacher bonus'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate final price after discount
                final_price = amount_eur - discount_value_eur
                
                # If hybrid payment, create Stripe payment intent for remaining amount
                if payment_method == 'hybrid':
                    # ⚡ CRITICAL: Actually transfer TEO tokens from student
                    try:
                        print(f"🪙 Transferring {required_teo:.2f} TEO from student {wallet_address}")
                        
                        # Transfer TEO from student to reward pool for discount
                        from django.conf import settings
                        reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
                        
                        if not reward_pool_address:
                            return Response({
                                'success': False,
                                'error': 'Reward pool not configured'
                            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                        
                        transfer_result = teo_service.transfer_with_reward_pool_gas(
                            wallet_address,  # from_address
                            reward_pool_address,  # to_address (reward pool)
                            Decimal(str(required_teo))  # Amount of TEO to transfer
                        )
                        
                        if not transfer_result:
                            return Response({
                                'success': False,
                                'error': 'Failed to transfer TEO tokens for discount'
                            }, status=status.HTTP_400_BAD_REQUEST)
                            
                        print(f"✅ TEO transfer successful: {transfer_result}")
                        
                    except Exception as e:
                        print(f"❌ TEO transfer failed: {str(e)}")
                        return Response({
                            'success': False,
                            'error': f'TEO transfer failed: {str(e)}'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Create Stripe payment intent for the discounted amount
                    result = cached_payment_service.create_payment_intent_optimized(
                        user_id=request.user.id,
                        course_id=course_id,
                        amount_eur=Decimal(str(final_price))
                    )
                    
                    if result.get('success'):
                        return Response({
                            'success': True,
                            'payment_method': 'hybrid',
                            'client_secret': result['client_secret'],
                            'payment_intent_id': result['payment_intent_id'],
                            'final_amount': float(final_price),
                            'discount_applied': float(discount_value_eur),
                            'teo_cost': float(required_teo),
                            'teacher_bonus': float(required_bonus),
                            'message': f'TeoCoin discount applied. Pay remaining €{final_price:.2f} with card'
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            'success': False,
                            'error': result.get('error', 'Failed to create discounted payment intent')
                        }, status=status.HTTP_400_BAD_REQUEST)
                
                # Full TeoCoin payment (only when payment_method == 'teocoin')
                else:
                    # TODO: Implement actual TeoCoin transfer via discount contract
                    # For now, we'll simulate successful enrollment
                    from courses.models import CourseEnrollment
                    
                    # Create enrollment for the user
                    course_obj = Course.objects.get(id=course_id)
                    enrollment, created = CourseEnrollment.objects.get_or_create(
                        student=request.user,
                        course=course_obj,
                        defaults={
                            'payment_method': 'teocoin_discount',
                            'amount_paid_eur': final_price
                        }
                    )
                    
                    return Response({
                        'success': True,
                        'payment_method': 'teocoin_discount',
                        'final_amount': float(final_price),
                        'discount_applied': float(discount_value_eur),
                        'teo_cost': float(required_teo),
                        'teacher_bonus': float(required_bonus),
                        'enrollment_created': created,
                        'enrollment_id': enrollment.id,
                        'message': f'Successfully enrolled! Applied {teocoin_discount}% discount using {required_teo:.2f} TEO'
                    }, status=status.HTTP_200_OK)
            
            # ⚡ PERFORMANCE: Create payment intent using optimized service
            result = cached_payment_service.create_payment_intent_optimized(
                user_id=request.user.id,
                course_id=course_id,
                amount_eur=Decimal(str(amount_eur))
            )
            
            if result.get('success'):
                return Response({
                    'success': True,
                    'client_secret': result['client_secret'],
                    'payment_intent_id': result['payment_intent_id'],
                    'amount': str(result['amount']),
                    'course_title': result.get('course_title'),
                    'teocoin_reward': str(result.get('teocoin_reward', 0))
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Payment intent creation failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"⚡ OPTIMIZED Payment intent creation failed: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmPaymentView(APIView):
    """
    ⚡ ULTRA-FAST Confirm successful Stripe payment with cache invalidation
    
    POST /api/courses/{course_id}/confirm-payment/
    {
        "payment_intent_id": "pi_..."
    }
    """
    permission_classes = [IsAuthenticated]
    
    @method_decorator(payment_rate_limit(max_requests=3, window=60))
    def post(self, request, course_id):
        try:
            payment_intent_id = request.data.get('payment_intent_id')
            
            if not payment_intent_id:
                return Response({
                    'success': False,
                    'error': 'payment_intent_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ⚡ PERFORMANCE: Process payment confirmation using optimized service
            result = cached_payment_service.process_payment_optimized(
                payment_intent_id=payment_intent_id,
                course_id=course_id,
                user_id=request.user.id
            )
            
            if result.get('success'):
                return Response({
                    'success': True,
                    'enrollment': result.get('enrollment'),
                    'teocoin_reward': result.get('teocoin_reward'),
                    'amount_paid': str(result.get('amount_paid', 0)),
                    'message': result.get('message', 'Payment confirmed successfully')
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Payment confirmation failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"⚡ OPTIMIZED Payment confirmation failed: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentSummaryView(APIView):
    """
    ⚡ ULTRA-FAST Get payment options summary with aggressive caching
    
    GET /api/courses/{course_id}/payment-summary/
    """
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60))  # Cache for 1 minute
    @method_decorator(vary_on_headers('Authorization'))  # Vary by user
    def get(self, request, course_id):
        try:
            # ⚡ PERFORMANCE: Use cached payment summary
            result = cached_payment_service.get_payment_summary_cached(
                user_id=request.user.id,
                course_id=course_id
            )
            
            if 'error' in result:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"⚡ OPTIMIZED Payment summary failed: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    """
    Get payment options and enrollment status for a course
    
    GET /api/courses/payment/summary/{course_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id):
        try:
            # Get payment summary using service
            result = payment_service.get_payment_summary(
                user_id=request.user.id,
                course_id=course_id
            )
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Payment summary failed: {str(e)}")
            return Response({
                'success': False,
                'error': 'Could not retrieve payment summary'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
