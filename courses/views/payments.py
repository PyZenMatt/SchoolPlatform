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

            # Handle TeoCoin discount payments
            if payment_method == 'teocoin' and teocoin_discount > 0:
                # Use the TeoCoin discount service
                from services.teo_discount_service import teo_discount_service
                from courses.models import Course
                
                course = Course.objects.get(id=course_id)
                teocoin_to_spend = Decimal(str(teocoin_discount * amount_eur / 100))  # Convert percentage to amount
                
                result = teo_discount_service.apply_teocoin_discount(
                    user=request.user,
                    course=course,
                    teocoin_to_spend=teocoin_to_spend
                )
                
                if result['success']:
                    return Response({
                        'success': True,
                        'payment_method': 'teocoin_discount',
                        'final_amount': result['final_price_eur'],
                        'discount_applied': result['discount_applied_eur'],
                        'teocoin_spent': result['teocoin_spent'],
                        'enrollment': True,  # TeoCoin payments are instant
                        'message': result['message']
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'success': False,
                        'error': result['error']
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
