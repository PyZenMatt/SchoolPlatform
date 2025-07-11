"""
API endpoint for creating permit + discount signature data.
This solves the student gas problem.
"""
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt

from services.gas_free_discount_service import GasFreeDiscountService
from services.exceptions import TeoArtServiceException

@api_view(['POST'])
@csrf_exempt
def create_permit_discount_signatures(request):
    """
    Create both permit and discount signature data for a student.
    
    POST data:
    {
        "student_address": "0x...",
        "course_id": 123,
        "teo_amount": 10
    }
    
    Returns both permit and discount signature data that student needs to sign.
    """
    try:
        data = request.data
        student_address = data.get('student_address')
        course_id = data.get('course_id')
        teo_amount = data.get('teo_amount')
        
        if not all([student_address, course_id, teo_amount]):
            return Response({
                'error': 'Missing required fields: student_address, course_id, teo_amount'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = GasFreeDiscountService()
        
        # Create permit signature data (for approval)
        permit_data = service.create_permit_signature_data(
            student_address=student_address
        )
        
        # Create discount signature data
        discount_data = service.create_discount_signature(
            student_address=student_address,
            course_id=int(course_id),
            teo_amount=int(teo_amount)
        )
        
        return Response({
            'success': True,
            'permit_data': permit_data,
            'discount_data': discount_data,
            'instructions': {
                'step_1': 'Sign the permit data using eth_signTypedData_v4',
                'step_2': 'Sign the discount message hash using personal_sign',
                'step_3': 'Submit both signatures to execute endpoint',
                'gas_required': 'Zero MATIC required for signatures',
                'platform_pays': 'Platform pays all transaction gas fees'
            }
        })
        
    except TeoArtServiceException as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Internal error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def execute_permit_discount(request):
    """
    Execute permit + discount with student signatures.
    
    POST data:
    {
        "student_address": "0x...",
        "course_id": 123,
        "teo_amount": 10,
        "discount_signature": "0x...",
        "discount_nonce": 123456,
        "permit_signature": "0x...",
        "permit_deadline": 1234567890,
        "permit_nonce": 0
    }
    """
    try:
        data = request.data
        
        # Extract parameters
        student_address = data.get('student_address')
        course_id = data.get('course_id')
        teo_amount = data.get('teo_amount')
        discount_signature = data.get('discount_signature')
        discount_nonce = data.get('discount_nonce')
        permit_signature = data.get('permit_signature')
        permit_deadline = data.get('permit_deadline')
        permit_nonce = data.get('permit_nonce', 0)
        
        # Validate required fields
        required_fields = [
            'student_address', 'course_id', 'teo_amount', 
            'discount_signature', 'discount_nonce',
            'permit_signature', 'permit_deadline'
        ]
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        service = GasFreeDiscountService()
        
        # Parse permit signature (v, r, s)
        permit_sig = permit_signature.replace('0x', '')
        if len(permit_sig) != 130:  # 65 bytes * 2
            return Response({
                'error': 'Invalid permit signature length'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        permit_r = '0x' + permit_sig[:64]
        permit_s = '0x' + permit_sig[64:128]
        permit_v = int(permit_sig[128:130], 16)
        
        # Execute the complete transaction
        result = service.execute_discount_request(
            student_address=student_address,
            signature=discount_signature,
            course_id=int(course_id),
            teo_amount=int(teo_amount),
            nonce=int(discount_nonce),
            permit_deadline=int(permit_deadline),
            permit_v=permit_v,
            permit_r=permit_r,
            permit_s=permit_s
        )
        
        return Response({
            'success': True,
            'result': result,
            'message': 'Gas-free discount executed successfully!'
        })
        
    except TeoArtServiceException as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'error': f'Internal error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
