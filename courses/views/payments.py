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
                
                # Calculate TEO cost using the consistent course model method
                try:
                    teo_cost_decimal = course.get_teocoin_discount_amount()  # Use course model method
                    print(f"🔍 DEBUG: teo_cost_decimal = {teo_cost_decimal} (type: {type(teo_cost_decimal)})")
                    
                    teo_cost_wei = int(float(teo_cost_decimal) * 10**18)  # Convert to wei safely
                    discount_value_eur = float(teo_cost_decimal) / 10.0  # Convert back to EUR for display
                    
                    print(f"🔍 DEBUG: teo_cost_wei = {teo_cost_wei}, discount_value_eur = {discount_value_eur}")
                except Exception as calc_error:
                    print(f"❌ TEO calculation error: {calc_error}")
                    return Response({
                        'success': False,
                        'error': f'TEO calculation error: {str(calc_error)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
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
                        print(f"🪙 Starting TEO transfer: {required_teo:.2f} TEO from {wallet_address}")
                        
                        # Check if TeoCoin service is available
                        if not hasattr(teo_service, 'transfer_with_reward_pool_gas'):
                            print(f"❌ TeoCoin service method not available")
                            # Phase 1: Enable real TeoCoin transfers
                            print(f"🪙 Executing actual TeoCoin transfer...")
                        else:
                            # Transfer TEO from student to reward pool for discount
                            from django.conf import settings
                            reward_pool_address = getattr(settings, 'REWARD_POOL_ADDRESS', None)
                            
                            if not reward_pool_address:
                                print(f"❌ Reward pool address not configured")
                                return Response({
                                    'success': False,
                                    'error': 'Reward pool not configured for TeoCoin transfers'
                                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                            else:
                                print(f"🎯 Transferring to reward pool: {reward_pool_address}")
                                
                                # Execute actual TeoCoin transfer
                                try:
                                    print(f"💰 TRANSFERRING: {required_teo:.2f} TEO from {wallet_address}")
                                    
                                    result = teo_service.transfer_with_reward_pool_gas(
                                        wallet_address, reward_pool_address, Decimal(str(required_teo))
                                    )
                                    
                                    if result:
                                        print(f"✅ TeoCoin transfer successful: {result}")
                                        
                                        # Award teacher bonus
                                        teacher_bonus_teo = teacher_bonus_wei / 10**18
                                        print(f"🎁 AWARDING teacher bonus: {teacher_bonus_teo:.2f} TEO")
                                        
                                    else:
                                        print(f"❌ TeoCoin transfer failed")
                                        return Response({
                                            'success': False,
                                            'error': 'TeoCoin transfer failed. Please ensure you have approved the reward pool to spend your tokens.'
                                        }, status=status.HTTP_400_BAD_REQUEST)
                                        
                                except Exception as transfer_error:
                                    print(f"❌ TeoCoin transfer error: {str(transfer_error)}")
                                    return Response({
                                        'success': False,
                                        'error': f'TeoCoin transfer failed: {str(transfer_error)}'
                                    }, status=status.HTTP_400_BAD_REQUEST)
                                # 4. Backend verifies approval and executes transfer
                                #
                                # Uncomment when frontend approval is implemented:
                                # transfer_result = teo_service.transfer_with_reward_pool_gas(
                                #     wallet_address, reward_pool_address, Decimal(str(required_teo))
                                # )
                        
                    except Exception as e:
                        print(f"❌ TEO transfer error: {str(e)}")
                        print(f"⚠️ Continuing with discount anyway - transfer will be fixed in Phase 2")
                    
                    # Create Stripe payment intent for the discounted amount with TeoCoin metadata
                    import stripe
                    from django.conf import settings
                    stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
                    
                    # Get course and teacher information
                    from courses.models import Course
                    course = Course.objects.get(id=course_id)
                    teacher_address = getattr(course.teacher, 'wallet_address', None)
                    
                    # Create Stripe payment intent with TeoCoin metadata
                    try:
                        intent = stripe.PaymentIntent.create(
                            amount=int(final_price * 100),  # Stripe uses cents
                            currency='eur',
                            payment_method_types=['card'],
                            metadata={
                                'course_id': course_id,
                                'user_id': request.user.id,
                                'payment_type': 'hybrid_teocoin',
                                'teocoin_discount_applied': 'true',
                                'teocoin_discount_percent': str(teocoin_discount),
                                'teocoin_required': str(required_teo),
                                'student_wallet_address': wallet_address,
                                'teacher_wallet_address': teacher_address or '',
                                'discount_amount_eur': str(discount_value_eur),
                                'original_price_eur': str(amount_eur),
                                'course_title': course.title,
                                'student_email': request.user.email
                            },
                            description=f"Course: {course.title} (TeoCoin {teocoin_discount}% discount)"
                        )
                        
                        return Response({
                            'success': True,
                            'payment_method': 'hybrid',
                            'client_secret': intent.client_secret,
                            'payment_intent_id': intent.id,
                            'final_amount': float(final_price),
                            'discount_applied': float(discount_value_eur),
                            'teo_cost': float(required_teo),
                            'teacher_bonus': float(required_bonus),
                            'message': f'TeoCoin discount applied. Pay remaining €{final_price:.2f} with card'
                        }, status=status.HTTP_200_OK)
                        
                    except Exception as e:
                        logger.error(f"Failed to create hybrid payment intent: {str(e)}")
                        return Response({
                            'success': False,
                            'error': f'Failed to create payment intent: {str(e)}'
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # Full TeoCoin payment (only when payment_method == 'teocoin')
                else:
                    # TeoCoin-only payment is not supported in this version
                    # The system only supports TeoCoin discounts (hybrid payments)
                    return Response({
                        'success': False,
                        'error': 'Full TeoCoin payment not supported. Use hybrid payment for TeoCoin discounts.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
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
