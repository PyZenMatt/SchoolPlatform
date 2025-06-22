"""
Payment Views for Fiat Payment Integration
Handles Stripe payment intents, confirmations, and payment summaries
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from decimal import Decimal
import logging

from courses.models import Course
from services.payment_service import payment_service

logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    """
    Create Stripe payment intent for fiat course purchase
    
    POST /api/courses/payment/create-intent/
    {
        "course_id": 1,
        "amount_eur": "29.99"
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            course_id = request.data.get('course_id')
            amount_eur = request.data.get('amount_eur')
            
            if not course_id:
                return Response({
                    'success': False,
                    'error': 'course_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not amount_eur:
                return Response({
                    'success': False,
                    'error': 'amount_eur is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Convert to Decimal
            try:
                amount_eur = Decimal(str(amount_eur))
            except (ValueError, TypeError):
                return Response({
                    'success': False,
                    'error': 'Invalid amount format'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create payment intent using service
            result = payment_service.create_fiat_payment_intent(
                user_id=request.user.id,
                course_id=course_id,
                amount_eur=amount_eur
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
            logger.error(f"Payment intent creation failed: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmPaymentView(APIView):
    """
    Confirm successful Stripe payment and enroll student
    
    POST /api/courses/payment/confirm/
    {
        "payment_intent_id": "pi_...",
        "course_id": 1
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            payment_intent_id = request.data.get('payment_intent_id')
            course_id = request.data.get('course_id')
            
            if not payment_intent_id:
                return Response({
                    'success': False,
                    'error': 'payment_intent_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not course_id:
                return Response({
                    'success': False,
                    'error': 'course_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Process payment confirmation using service
            result = payment_service.process_successful_fiat_payment(
                payment_intent_id=payment_intent_id,
                course_id=course_id,
                user_id=request.user.id
            )
            
            if result.get('success'):
                return Response({
                    'success': True,
                    'enrollment': result['enrollment'],
                    'teocoin_reward': str(result.get('teocoin_reward', 0)),
                    'amount_paid': str(result.get('amount_paid', 0)),
                    'message': 'Payment successful and enrollment completed'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Payment confirmation failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Payment confirmation failed: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentSummaryView(APIView):
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
