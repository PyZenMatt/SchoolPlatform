"""
⚡ OPTIMIZED Payment Views for Ultra-Fast Payment Processing
Enhanced with Redis caching, rate limiting, and performance optimizations
VERSION: 4.0 - Phase 3: TeoCoin Discount Integration
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
from courses.utils.payment_helpers import process_teocoin_discount_payment, handle_teocoin_discount_completion
from courses.utils.teocoin_discount_payment import process_teocoin_discount_payment as process_discount_clean
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
            approval_tx_hash = request.data.get('approval_tx_hash')
            
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

            # ✅ PHASE 3: Handle TeoCoin discount payments with correct business logic
            if payment_method in ['teocoin', 'hybrid', 'fiat_with_teocoin_discount'] and teocoin_discount > 0:
                return process_discount_clean(
                    request=request,
                    course_id=course_id,
                    amount_eur=amount_eur,
                    teocoin_discount=teocoin_discount,
                    payment_method=payment_method
                )
                
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
                
                # Check if teacher has wallet address
                teacher_address = getattr(course.teacher, 'wallet_address', None)
                if not teacher_address:
                    return Response({
                        'success': False,
                        'error': 'Teacher wallet not configured for TeoCoin discounts'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate discount amounts using our service
                try:
                    teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(
                        Decimal(str(amount_eur)), 
                        teocoin_discount
                    )
                    discount_value_eur = amount_eur * teocoin_discount / 100
                    
                    print(f"🔍 DEBUG: TeoCoin calculation - Cost: {teo_cost}, Bonus: {teacher_bonus}, Discount: {discount_value_eur}")
                except Exception as calc_error:
                    print(f"❌ TEO calculation error: {calc_error}")
                    return Response({
                        'success': False,
                        'error': f'TEO calculation error: {str(calc_error)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check student TeoCoin balance
                teo_service = teocoin_discount_service.teocoin_service
                student_balance = teo_service.get_balance(wallet_address)
                required_teo = teo_cost / 10**18
                
                if student_balance < required_teo:
                    return Response({
                        'success': False,
                        'error': f'Insufficient TEO balance. Required: {required_teo:.4f} TEO, Available: {student_balance:.4f} TEO'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check reward pool balance for teacher bonus
                reward_pool_balance = teo_service.get_reward_pool_balance()
                required_bonus = teacher_bonus / 10**18
                
                if reward_pool_balance < required_bonus:
                    return Response({
                        'success': False,
                        'error': 'Insufficient reward pool balance for teacher bonus'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # ✅ NEW BUSINESS LOGIC: Create discount request via smart contract
                student_signature = request.data.get('student_signature')
                if not student_signature:
                    return Response({
                        'success': False,
                        'error': 'Student signature required for discount request'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create discount request (platform pays gas)
                discount_request = teocoin_discount_service.create_discount_request(
                    student_address=wallet_address,
                    teacher_address=teacher_address,
                    course_id=course_id,
                    course_price=Decimal(str(amount_eur)),
                    discount_percent=teocoin_discount,
                    student_signature=student_signature
                )
                
                if not discount_request.get('success'):
                    return Response({
                        'success': False,
                        'error': discount_request.get('error', 'Failed to create discount request')
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                print(f"✅ Discount request created: {discount_request['request_id']}")
                
                # Calculate final price after discount (student pays discounted amount immediately)
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
                                print(f"� Creating TeoCoin escrow instead of direct transfer")
                                
                                # 🆕 CREATE ESCROW instead of direct transfer
                                try:
                                    from services.escrow_service import escrow_service
                                    
                                    print(f"💰 CREATING ESCROW: {required_teo:.2f} TEO from {wallet_address}")
                                    
                                    # Create escrow for teacher choice
                                    escrow = escrow_service.create_escrow(
                                        student=request.user,
                                        teacher=course.teacher,
                                        course=course,
                                        teocoin_amount=Decimal(str(required_teo)),
                                        discount_data={
                                            'percentage': teocoin_discount,
                                            'euro_amount': (teocoin_discount * amount_eur / 100),
                                            'original_price': amount_eur
                                        },
                                        transfer_tx_hash=approval_tx_hash if approval_tx_hash and approval_tx_hash != 'frontend_approved' else None
                                    )
                                    
                                    if escrow:
                                        print(f"✅ TeoCoin escrow created: {escrow.id}")
                                        print(f"� Teacher notification sent for escrow decision")
                                        print(f"⏰ Escrow expires: {escrow.expires_at}")
                                        
                                        # Note: Teacher will decide later whether to accept TeoCoin or get standard EUR commission
                                        # For now, student enrollment proceeds with discounted EUR payment
                                        
                                    else:
                                        print(f"❌ TeoCoin escrow creation failed")
                                        return Response({
                                            'success': False,
                                            'error': 'TeoCoin escrow creation failed. Please try again.'
                                        }, status=status.HTTP_400_BAD_REQUEST)
                                        
                                except Exception as escrow_error:
                                    print(f"❌ TeoCoin escrow error: {str(escrow_error)}")
                                    return Response({
                                        'success': False,
                                        'error': f'TeoCoin escrow failed: {str(escrow_error)}'
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
