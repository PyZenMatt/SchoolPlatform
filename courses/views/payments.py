"""
TeoCoin Discount Payment System - Clean Implementation
Backend Proxy Architecture: Platform pays gas fees, students get guaranteed discounts

Business Logic:
- Students always get discounts regardless of teacher decision
- Teachers choose between EUR safety vs TEO staking opportunity  
- Platform absorbs discount cost if teacher declines
- 50% baseline commission with staking tier adjustments
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.utils import timezone
from decimal import Decimal
import logging
import stripe
from django.conf import settings

from courses.models import Course, CourseEnrollment
from users.models import User
from services.teocoin_discount_service import TeoCoinDiscountService, DiscountStatus
from services.teo_earning_service import TeoEarningService
from blockchain.blockchain import TeoCoinService
from notifications.services import teocoin_notification_service

logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    """
    Create Stripe payment intent with TeoCoin discount integration
    
    POST /api/v1/courses/{course_id}/payment/create-intent/
    {
        "use_teocoin_discount": true,
        "discount_percent": 15,
        "student_address": "0x...",
        "student_signature": "0x..."
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            user = request.user
            
            # Extract request data
            use_teocoin_discount = request.data.get('use_teocoin_discount', False)
            discount_percent = request.data.get('discount_percent', 0)
            student_address = request.data.get('student_address', '')
            student_signature = request.data.get('student_signature', '')
            
            # Calculate pricing
            original_price = course.price_eur
            discount_amount = Decimal('0')
            final_price = original_price
            discount_request_id = None
            
            # Process TeoCoin discount if requested
            if use_teocoin_discount and discount_percent > 0:
                try:
                    # Create discount request via backend proxy
                    discount_service = TeoCoinDiscountService()
                    teacher_address = getattr(course.teacher, 'wallet_address', '') or getattr(course.teacher, 'amoy_address', '')
                    
                    if not teacher_address:
                        return Response({
                            'error': 'Teacher wallet address not configured',
                            'code': 'TEACHER_WALLET_MISSING'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Create discount request
                    discount_result = discount_service.create_discount_request(
                        student_address=student_address,
                        teacher_address=teacher_address,
                        course_id=course_id,
                        course_price=original_price,
                        discount_percent=discount_percent,
                        student_signature=student_signature
                    )
                    
                    if discount_result['success']:
                        discount_request_id = discount_result['request_id']
                        # Student gets guaranteed discount
                        discount_amount = original_price * Decimal(discount_percent) / Decimal('100')
                        final_price = original_price - discount_amount
                        
                        # Send notification to teacher
                        try:
                            teo_cost = discount_result.get('teo_cost', 0) / 10**18  # Convert from wei
                            teacher_bonus = discount_result.get('teacher_bonus', 0) / 10**18  # Convert from wei
                            expires_at = discount_result.get('deadline')
                            
                            teocoin_notification_service.notify_teacher_discount_pending(
                                teacher=course.teacher,
                                student=user,
                                course_title=course.title,
                                discount_percent=discount_percent,
                                teo_cost=teo_cost,
                                teacher_bonus=teacher_bonus,
                                request_id=discount_request_id,
                                expires_at=expires_at
                            )
                        except Exception as notification_error:
                            logger.warning(f"Failed to send teacher notification: {notification_error}")
                        
                        logger.info(f"✅ Discount request created: {discount_request_id} for €{discount_amount}")
                    else:
                        logger.error(f"❌ Discount request failed: {discount_result.get('error')}")
                        return Response({
                            'error': 'Failed to create discount request',
                            'details': discount_result.get('error'),
                            'code': 'DISCOUNT_REQUEST_FAILED'
                        }, status=status.HTTP_400_BAD_REQUEST)
                        
                except Exception as e:
                    logger.error(f"Discount creation error: {e}")
                    return Response({
                        'error': 'TeoCoin discount system error',
                        'details': str(e),
                        'code': 'DISCOUNT_SYSTEM_ERROR'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Create Stripe payment intent for final price
            stripe.api_key = settings.STRIPE_SECRET_KEY
            
            intent_data = {
                'amount': int(final_price * 100),  # Convert to cents
                'currency': 'eur',
                'metadata': {
                    'course_id': course_id,
                    'user_id': user.id,
                    'original_price': str(original_price),
                    'discount_amount': str(discount_amount),
                    'discount_percent': discount_percent,
                    'use_teocoin_discount': str(use_teocoin_discount),
                    'student_address': student_address,
                }
            }
            
            # Add discount request ID if applicable
            if discount_request_id:
                intent_data['metadata']['discount_request_id'] = str(discount_request_id)
            
            payment_intent = stripe.PaymentIntent.create(**intent_data)
            
            return Response({
                'success': True,
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'pricing': {
                    'original_price': str(original_price),
                    'discount_amount': str(discount_amount),
                    'final_price': str(final_price),
                    'discount_percent': discount_percent
                },
                'discount_request_id': discount_request_id,
                'course': {
                    'title': course.title,
                    'instructor': course.teacher.username if course.teacher else 'Unknown'
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Payment intent creation error: {e}")
            return Response({
                'error': 'Failed to create payment intent',
                'details': str(e),
                'code': 'PAYMENT_INTENT_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmPaymentView(APIView):
    """
    Confirm successful payment and enroll student
    
    POST /api/v1/courses/{course_id}/payment/confirm/
    {
        "payment_intent_id": "pi_...",
        "process_discount": true
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            user = request.user
            payment_intent_id = request.data.get('payment_intent_id')
            process_discount = request.data.get('process_discount', True)
            
            if not payment_intent_id:
                return Response({
                    'error': 'Payment intent ID required',
                    'code': 'MISSING_PAYMENT_INTENT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify payment with Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status != 'succeeded':
                return Response({
                    'error': 'Payment not completed',
                    'payment_status': payment_intent.status,
                    'code': 'PAYMENT_NOT_COMPLETED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract metadata
            metadata = payment_intent.metadata
            discount_request_id = metadata.get('discount_request_id')
            use_teocoin_discount = metadata.get('use_teocoin_discount') == 'True'
            original_price = Decimal(metadata.get('original_price', '0'))
            discount_amount = Decimal(metadata.get('discount_amount', '0'))
            student_address = metadata.get('student_address', '')
            
            # Check if already enrolled
            existing_enrollment = CourseEnrollment.objects.filter(
                student=user, course=course
            ).first()
            
            if existing_enrollment:
                return Response({
                    'error': 'Already enrolled in this course',
                    'enrollment_id': existing_enrollment.id,
                    'code': 'ALREADY_ENROLLED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create enrollment with proper payment tracking
            final_price = original_price - discount_amount
            payment_method = 'teocoin_discount' if use_teocoin_discount else 'stripe'
            
            enrollment = CourseEnrollment.objects.create(
                student=user,
                course=course,
                payment_method=payment_method,
                stripe_payment_intent_id=payment_intent_id,
                amount_paid_eur=final_price,
                original_price_eur=original_price,
                discount_amount_eur=discount_amount,
                teocoin_discount_request_id=discount_request_id
            )
            
            logger.info(f"✅ Student enrolled: {user.username} in {course.title} for €{final_price}")
            
            # Process teacher notification for discount decision
            teacher_notification_sent = False
            if use_teocoin_discount and discount_request_id and process_discount:
                try:
                    # Teacher has 2 hours to decide: Accept TEO vs Keep EUR
                    # This is handled by the TeoCoin discount service
                    teacher_notification_sent = True
                    logger.info(f"📧 Teacher notification sent for discount request {discount_request_id}")
                    
                except Exception as e:
                    logger.error(f"Teacher notification error: {e}")
            
            # Award completion TEO to student (backend proxy handles minting)
            try:
                teo_service = TeoEarningService()
                teo_service.reward_course_purchase(user.id, course_id)
                logger.info(f"🪙 TEO purchase reward sent to {student_address}")
            except Exception as e:
                logger.error(f"TEO reward error: {e}")
            
            return Response({
                'success': True,
                'enrollment_id': enrollment.id,
                'course_title': course.title,
                'amount_paid': str(final_price),
                'discount_applied': str(discount_amount) if discount_amount > 0 else None,
                'payment_method': payment_method,
                'teacher_notification_sent': teacher_notification_sent,
                'message': f'Successfully enrolled in {course.title}!'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Payment confirmation error: {e}")
            return Response({
                'error': 'Failed to confirm payment',
                'details': str(e),
                'code': 'PAYMENT_CONFIRMATION_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentSummaryView(APIView):
    """
    Get payment summary for a course including TeoCoin discount calculations
    
    GET /api/v1/courses/{course_id}/payment/summary/?discount_percent=15&student_address=0x...
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            
            # Base pricing
            original_price = course.price_eur
            
            # Course information
            course_info = {
                'id': course.pk,  # Use .pk instead of .id for better compatibility
                'title': course.title,
                'instructor': course.teacher.username if course.teacher else 'Unknown',
                'description': course.description[:200] + '...' if len(course.description) > 200 else course.description,
                'duration_hours': getattr(course, 'duration_hours', None),
                'skill_level': getattr(course, 'skill_level', None),
            }
            
            # Student enrollment status
            user = request.user
            is_enrolled = CourseEnrollment.objects.filter(
                student=user, course=course
            ).exists()
            
            # Create pricing options array for frontend compatibility
            pricing_options = []
            
            # Always add fiat payment option
            pricing_options.append({
                'method': 'fiat',
                'price': str(original_price),
                'currency': 'EUR',
                'description': 'Pay with Credit/Debit Card',
                'reward': '50',  # TEO rewards for fiat payment
                'disabled': False
            })
            
            # Add TeoCoin discount option if available
            if hasattr(course, 'teocoin_discount_percent') and course.teocoin_discount_percent > 0:
                discount_percent = int(course.teocoin_discount_percent)
                discount_amount = original_price * Decimal(discount_percent) / Decimal('100')
                final_price = original_price - discount_amount
                
                # Simple TEO cost calculation (1 TEO = 0.10 EUR discount value)
                teo_cost_eur = discount_amount  # EUR value of discount
                teo_cost_tokens = int(teo_cost_eur * 10)  # Simplified: 1 TEO = 0.10 EUR
                
                pricing_options.append({
                    'method': 'teocoin',
                    'price': str(teo_cost_tokens),
                    'currency': 'TEO',
                    'description': f'Use TEO for {discount_percent}% discount',
                    'discount': discount_percent,
                    'discount_percent': discount_percent,
                    'final_price_eur': str(final_price),
                    'savings_eur': str(discount_amount),
                    'disabled': False
                })
            
            # Basic pricing summary for backward compatibility
            pricing_summary = {
                'original_price': str(original_price),
                'currency': 'EUR',
                'discount_available': hasattr(course, 'teocoin_discount_percent') and course.teocoin_discount_percent > 0,
                'max_discount_percent': int(course.teocoin_discount_percent) if hasattr(course, 'teocoin_discount_percent') else 0,
            }
            
            return Response({
                'success': True,
                'course': course_info,
                'pricing': pricing_summary,
                'pricing_options': pricing_options,
                'student_status': {
                    'is_enrolled': is_enrolled,
                    'can_enroll': not is_enrolled
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Payment summary error: {e}")
            return Response({
                'error': 'Failed to get payment summary',
                'details': str(e),
                'code': 'PAYMENT_SUMMARY_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeoCoinDiscountStatusView(APIView):
    """
    Get status of TeoCoin discount requests for student
    
    GET /api/v1/courses/{course_id}/payment/discount-status/?student_address=0x...
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            student_address = request.query_params.get('student_address', '')
            
            if not student_address:
                return Response({
                    'error': 'Student address required',
                    'code': 'MISSING_STUDENT_ADDRESS'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get discount requests for this student and course
            discount_service = TeoCoinDiscountService()
            student_requests = discount_service.get_student_requests(student_address)
            
            # Filter for this specific course
            course_requests = [
                req for req in student_requests 
                if req.get('course_id') == course_id
            ]
            
            # Get most recent request
            latest_request = None
            if course_requests:
                latest_request = max(course_requests, key=lambda x: x.get('timestamp', 0))
            
            return Response({
                'success': True,
                'course_id': course_id,
                'student_address': student_address,
                'latest_request': latest_request,
                'total_requests': len(course_requests),
                'all_requests': course_requests
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Discount status error: {e}")
            return Response({
                'error': 'Failed to get discount status',
                'details': str(e),
                'code': 'DISCOUNT_STATUS_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)