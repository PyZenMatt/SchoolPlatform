# Layer 2 TeoCoin Discount Views - Gas-Free Implementation
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from decimal import Decimal
import logging

from django.contrib.auth.models import User
from courses.models import Course
from blockchain.blockchain import TeoCoinService
# Import the Layer 2 service (we'll create a simpler inline version)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_layer2_discount_request(request):
    """
    Create a gas-free TeoCoin discount request using Layer 2 infrastructure
    """
    try:
        data = request.data
        student = request.user  # Use actual authenticated user
        course_id = int(data.get('course_id'))  # Ensure integer
        discount_amount_eur = Decimal(str(data.get('discount_amount', 0)))
        discount_percentage = int(data.get('discount_percentage', 0))
        teo_amount = data.get('teo_amount')  # For full purchases
        student_wallet = data.get('student_wallet', '').lower()
        
        # Determine if this is a discount or full purchase
        is_full_purchase = teo_amount is not None and discount_amount_eur == 0
        
        logger.info(f"Layer 2 request: Student {student.id if student else 'None'}, Course {course_id}")
        if is_full_purchase:
            logger.info(f"Full purchase: {teo_amount} TEO")
        else:
            logger.info(f"Discount: €{discount_amount_eur} ({discount_percentage}%)")
        
        # Validate inputs - allow full purchases (discount_amount_eur can be 0)
        if not course_id:
            return Response({
                'success': False,
                'error': 'Invalid course ID'
            }, status=400)
            
        if discount_amount_eur < 0:
            return Response({
                'success': False,
                'error': 'Invalid discount amount'
            }, status=400)
            
        if not student_wallet or len(student_wallet) != 42:
            return Response({
                'success': False,
                'error': 'Valid student wallet address required'
            }, status=400)
        
        # Get course and teacher
        try:
            course = Course.objects.get(id=course_id)
            teacher = course.teacher
        except Course.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Course not found'
            }, status=404)
        
        # Initialize TeoCoin service with Layer 2 capabilities
        teo_service = TeoCoinService()
        
        # Calculate TEO cost (1 TEO = 1 EUR)
        teo_cost = discount_amount_eur  # 1:1 ratio
        
        # Execute gas-free transfer using Layer 2 infrastructure
        # CRITICAL FIX: Student must transfer TEO TO platform, not receive FROM platform
        try:
            # Check if student has sufficient balance first
            student_balance = teo_service.get_balance(student_wallet)
            if student_balance < teo_cost:
                return Response({
                    'success': False,
                    'error': f'Insufficient TEO balance. Have: {student_balance} TEO, Need: {teo_cost} TEO'
                }, status=400)
            
            # Get platform/treasury address where TEO should go
            platform_address = "0xd74fc566c0c5b83f95fd82e6866d8a7a6eaca7a9"  # Layer 2 contract
            
            # CORRECT FLOW: Student transfers TEO to platform (gas paid by reward pool)
            # This requires the student to have pre-approved the platform
            tx_hash = teo_service.transfer_with_reward_pool_gas(
                from_address=student_wallet,
                to_address=platform_address,
                amount=teo_cost
            )
            
            # If transferFrom fails (no approval), return error instead of fallback
            if not tx_hash:
                return Response({
                    'success': False,
                    'error': 'TeoCoin transfer failed. Please ensure you have approved the platform to spend your TEO tokens and try again.'
                }, status=400)
            
            # Generate request ID
            import uuid
            request_id = str(uuid.uuid4())
            
            if tx_hash:
                # 🚀 CRITICAL FIX: Enroll student in course after successful TeoCoin transfer
                from courses.models import CourseEnrollment
                from django.utils import timezone
                
                try:
                    # Check if already enrolled
                    existing_enrollment = CourseEnrollment.objects.filter(
                        student=student,
                        course=course
                    ).first()
                    
                    if not existing_enrollment:
                        # Create enrollment record for TeoCoin discount payment
                        enrollment = CourseEnrollment.objects.create(
                            student=student,
                            course=course,
                            payment_method='teocoin_discount',  # Mark as TeoCoin discount payment
                            amount_paid_eur=course.price_eur - discount_amount_eur,  # Amount paid after discount
                            original_price_eur=course.price_eur,  # Original price
                            discount_amount_eur=discount_amount_eur,  # Track discount amount
                            amount_paid_teocoin=teo_cost,  # Track TEO used
                            teocoin_discount_request_id=tx_hash,  # Store transaction hash in this field
                            teocoin_reward_given=0,  # No additional reward since they used TEO
                        )
                        
                        logger.info(f"✅ Student {student.username} enrolled in course {course.title} with TeoCoin discount")
                        
                        # 🔔 Send notification to teacher
                        try:
                            from notifications.models import Notification
                            
                            Notification.objects.create(
                                user=teacher,
                                message=f"🎉 New student enrolled! {student.username} joined '{course.title}' using TeoCoin discount (€{discount_amount_eur} off, paid €{course.price_eur - discount_amount_eur})",
                                notification_type='course_enrollment',
                                related_object_id=str(enrollment.pk)
                            )
                            
                            logger.info(f"✅ Teacher notification sent to {teacher.username}")
                            
                        except Exception as notification_error:
                            logger.error(f"⚠️ Teacher notification failed: {notification_error}")
                        
                        enrollment_created = True
                        enrollment_id = enrollment.pk
                        
                    else:
                        logger.info(f"Student {student.username} already enrolled in course {course.title}")
                        enrollment_created = False
                        enrollment_id = existing_enrollment.pk
                    
                except Exception as enrollment_error:
                    logger.error(f"❌ Course enrollment failed: {enrollment_error}")
                    result = {
                        'success': False,
                        'error': f'TeoCoin transfer succeeded but enrollment failed: {str(enrollment_error)}'
                    }
                    return Response(result, status=500)
                
                result = {
                    'success': True,
                    'request_id': request_id,
                    'teo_cost': float(teo_cost),
                    'transaction_hash': tx_hash,
                    'message': 'Gas-free transfer completed via Layer 2',
                    'enrollment_created': enrollment_created,
                    'enrollment_id': enrollment_id,
                    'course_access_granted': True
                }
            else:
                result = {
                    'success': False,
                    'error': 'Layer 2 transfer failed - no transaction hash returned'
                }
        except Exception as e:
            result = {
                'success': False,
                'error': f'Layer 2 transfer failed: {str(e)}'
            }
        
        if result['success']:
            return Response({
                'success': True,
                'message': 'Gas-free TeoCoin discount applied successfully!',
                'data': {
                    'request_id': result['request_id'],
                    'teo_cost': str(result['teo_cost']),
                    'discount_amount_eur': str(discount_amount_eur),
                    'discount_percentage': discount_percentage,
                    'transaction_hash': result.get('transaction_hash'),
                    'gas_paid_by_platform': True,
                    'student_gas_cost': '0 ETH'
                }
            })
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=400)
            
    except Exception as e:
        logger.error(f"Layer 2 discount request failed: {str(e)}")
        return Response({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_student_teo_balance(request):
    """
    Check student's TEO balance for Layer 2 discount validation
    """
    try:
        student_wallet = request.GET.get('wallet_address', '').lower()
        
        if not student_wallet:
            return Response({
                'success': False,
                'error': 'Wallet address required'
            }, status=400)
        
        # Initialize TeoCoin service
        teo_service = TeoCoinService()
        
        # Get student's TEO balance (already converted from wei to TEO)
        balance_teo_decimal = teo_service.get_balance(student_wallet)
        balance_teo = float(balance_teo_decimal)
        
        return Response({
            'success': True,
            'data': {
                'wallet_address': student_wallet,
                'teo_balance': balance_teo,
                'has_sufficient_balance': balance_teo >= 1.0  # Minimum for discount (1 TEO = 1 EUR)
            }
        })
        
    except Exception as e:
        logger.error(f"Balance check failed: {str(e)}")
        return Response({
            'success': False,
            'error': f'Balance check failed: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def simulate_layer2_discount(request):
    """
    Simulate a Layer 2 discount to show costs and verify feasibility
    """
    try:
        data = request.data
        discount_amount_eur = Decimal(str(data.get('discount_amount', 10)))
        
        # Calculate TEO cost directly (1 TEO = 1 EUR)
        teo_cost = discount_amount_eur  # 1:1 ratio - 1 TEO for 1 EUR discount
        
        return Response({
            'success': True,
            'simulation': {
                'discount_amount_eur': str(discount_amount_eur),
                'teo_cost': str(teo_cost),
                'teo_to_eur_rate': '1.0',  # 1 TEO = 1 EUR
                'gas_cost_student': '0 ETH',
                'gas_cost_platform': 'Covered by reward pool',
                'layer2_enabled': True,
                'requires_approval': False
            }
        })
        
    except Exception as e:
        logger.error(f"Layer 2 simulation failed: {str(e)}")
        return Response({
            'success': False,
            'error': f'Simulation failed: {str(e)}'
        }, status=500)
