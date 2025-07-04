#!/usr/bin/env python3
"""
Comprehensive test script for TeoCoin payment flow
Tests the entire buying process when using TeoCoin discount
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, CourseEnrollment
from blockchain.models import UserWallet
from django.test import Client
from django.urls import reverse
import json

User = get_user_model()

def print_separator(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_user_wallet():
    """Test user's blockchain wallet setup"""
    print_separator("TESTING USER WALLET SETUP")
    
    # Find students with wallets
    students = User.objects.filter(role='student', is_active=True)
    print(f"Found {students.count()} student users")
    
    for student in students[:5]:  # Check first 5 students
        try:
            wallet = UserWallet.objects.get(user=student)
            print(f"Student: {student.username} ({student.email})")
            print(f"  Wallet Address: {wallet.address}")
            print(f"  Private Key: {wallet.get_masked_private_key()}")
            print(f"  Created: {wallet.created_at}")
            return student, wallet
        except UserWallet.DoesNotExist:
            print(f"Student: {student.username} - No wallet")
    
    # If no wallets found, check if any user has wallet_address attribute
    for student in students[:5]:
        wallet_address = getattr(student, 'wallet_address', None)
        if wallet_address:
            print(f"Student: {student.username} has wallet_address: {wallet_address}")
            return student, wallet_address
    
    return None, None

def test_course_teocoin_settings():
    """Test course TeoCoin discount settings"""
    print_separator("TESTING COURSE TEOCOIN SETTINGS")
    
    courses = Course.objects.filter(is_approved=True)[:5]
    
    for course in courses:
        print(f"Course: {course.title}")
        print(f"  Price EUR: €{course.price_eur}")
        print(f"  TeoCoin Discount %: {course.teocoin_discount_percent}%")
        print(f"  TeoCoin Reward: {course.teocoin_reward}")
        
        # Test the discount calculation method
        try:
            discount_amount = course.get_teocoin_discount_amount()
            print(f"  Discount Amount (TEO): {discount_amount}")
            
            teocoin_price = course.get_teocoin_price()
            print(f"  TeoCoin Price: {teocoin_price}")
        except Exception as e:
            print(f"  ERROR calculating discount: {e}")
        
        print()
        
        if course.teocoin_discount_percent > 0:
            return course
    
    return None

def test_payment_intent_creation(student, course):
    """Test payment intent creation with TeoCoin discount"""
    print_separator("TESTING PAYMENT INTENT CREATION")
    
    client = Client()
    
    # Login as student
    client.force_login(student)
    
    # Test different payment scenarios
    scenarios = [
        {
            'name': 'Regular Stripe Payment',
            'data': {
                'payment_method': 'stripe'
            }
        },
        {
            'name': 'TeoCoin Discount (Hybrid)',
            'data': {
                'payment_method': 'hybrid',
                'teocoin_discount': course.teocoin_discount_percent,
                'wallet_address': getattr(student, 'wallet_address', 'test_wallet_address')
            }
        },
        {
            'name': 'Full TeoCoin Payment',
            'data': {
                'payment_method': 'teocoin',
                'teocoin_discount': course.teocoin_discount_percent,
                'wallet_address': getattr(student, 'wallet_address', 'test_wallet_address')
            }
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- Testing: {scenario['name']} ---")
        print(f"Course: {course.title}")
        print(f"Student: {student.username}")
        print(f"Data: {scenario['data']}")
        
        # Create payment intent
        url = reverse('create-payment-intent', kwargs={'course_id': course.id})
        response = client.post(url, scenario['data'], content_type='application/json')
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✅ Payment intent created successfully!")
            
            # Print relevant response fields
            for key, value in response_data.items():
                if key in ['success', 'payment_method', 'final_amount', 'discount_applied', 
                          'teo_cost', 'client_secret', 'message', 'enrollment_created']:
                    print(f"  {key}: {value}")
                    
        else:
            print(f"❌ ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw response: {response.content}")
        
        print()

def check_enrollments():
    """Check course enrollments"""
    print_separator("CHECKING COURSE ENROLLMENTS")
    
    enrollments = CourseEnrollment.objects.all().order_by('-enrolled_at')[:10]
    
    print(f"Found {enrollments.count()} total enrollments")
    
    for enrollment in enrollments:
        print(f"Enrollment ID: {enrollment.pk}")
        print(f"  Student: {enrollment.student.username}")
        print(f"  Course: {enrollment.course.title}")
        print(f"  Enrolled: {enrollment.enrolled_at}")
        print(f"  Payment Method: {getattr(enrollment, 'payment_method', 'Not specified')}")
        print(f"  Amount Paid: €{getattr(enrollment, 'amount_paid_eur', 'Not specified')}")
        print(f"  Completed: {enrollment.completed}")
        print()

def check_payment_views():
    """Check payment views and URLs"""
    print_separator("CHECKING PAYMENT VIEWS AND URLS")
    
    try:
        from courses.views.payments import CreatePaymentIntentView, ConfirmPaymentView, PaymentSummaryView
        print("✅ Payment views imported successfully")
        print(f"CreatePaymentIntentView: {CreatePaymentIntentView}")
        print(f"ConfirmPaymentView: {ConfirmPaymentView}")
        print(f"PaymentSummaryView: {PaymentSummaryView}")
    except ImportError as e:
        print(f"❌ ERROR importing payment views: {e}")
    
    # Test URL patterns
    try:
        from django.urls import reverse
        test_course_id = 1
        
        urls_to_test = [
            ('create-payment-intent', {'course_id': test_course_id}),
            ('confirm-payment', {'course_id': test_course_id}),
            ('payment-summary', {'course_id': test_course_id}),
        ]
        
        print("\n--- URL Pattern Tests ---")
        for url_name, kwargs in urls_to_test:
            try:
                url = reverse(url_name, kwargs=kwargs)
                print(f"✅ {url_name}: {url}")
            except Exception as e:
                print(f"❌ {url_name}: {e}")
                
    except Exception as e:
        print(f"❌ URL testing failed: {e}")

def test_teocoin_services():
    """Test TeoCoin service availability"""
    print_separator("TESTING TEOCOIN SERVICES")
    
    try:
        from services.teocoin_discount_service import teocoin_discount_service
        print("✅ TeoCoin discount service imported successfully")
        
        # Check if the service has the expected methods
        service = teocoin_discount_service
        methods_to_check = ['teocoin_service']
        
        for method in methods_to_check:
            if hasattr(service, method):
                print(f"✅ Service has method: {method}")
            else:
                print(f"❌ Service missing method: {method}")
                
    except ImportError as e:
        print(f"❌ ERROR importing TeoCoin service: {e}")
    
    try:
        from services.cached_payment_service import cached_payment_service
        print("✅ Cached payment service imported successfully")
    except ImportError as e:
        print(f"❌ ERROR importing cached payment service: {e}")

def simulate_teocoin_payment_flow(student, course):
    """Simulate the complete TeoCoin payment flow"""
    print_separator("SIMULATING TEOCOIN PAYMENT FLOW")
    
    # Calculate expected values
    discount_percent = course.teocoin_discount_percent
    course_price = course.price_eur
    discount_amount_eur = course_price * Decimal(discount_percent) / 100
    discount_amount_teo = discount_amount_eur * 10  # 1 EUR = 10 TEO
    
    print(f"Course: {course.title}")
    print(f"Student: {student.username}")
    print(f"Course price: €{course_price}")
    print(f"Discount percent: {discount_percent}%")
    print(f"Discount amount (EUR): €{discount_amount_eur}")
    print(f"Discount amount (TEO): {discount_amount_teo}")
    
    # Check initial enrollment status
    initial_enrolled = CourseEnrollment.objects.filter(
        student=student, course=course
    ).exists()
    
    print(f"Initially enrolled: {initial_enrolled}")
    
    if initial_enrolled:
        print("⚠️  Student already enrolled, cannot test enrollment flow")
        return
    
    # Test the payment intent creation
    client = Client()
    client.force_login(student)
    
    # Try hybrid payment with TeoCoin discount
    url = reverse('create-payment-intent', kwargs={'course_id': course.id})
    data = {
        'payment_method': 'hybrid',
        'teocoin_discount': discount_percent,
        'wallet_address': getattr(student, 'wallet_address', 'test_wallet_address')
    }
    
    print(f"\n🔄 Creating hybrid payment intent...")
    response = client.post(url, data, content_type='application/json')
    
    if response.status_code == 200:
        response_data = response.json()
        print("✅ Hybrid payment intent created!")
        
        # Check if enrollment was created (for full TeoCoin payments)
        if response_data.get('enrollment_created'):
            print("✅ Enrollment created via TeoCoin payment")
            
            # Check the actual enrollment record
            enrollment = CourseEnrollment.objects.filter(
                student=student, course=course
            ).first()
            
            if enrollment:
                print(f"✅ Enrollment found: ID {enrollment.pk}")
                print(f"   Payment method: {getattr(enrollment, 'payment_method', 'Not set')}")
                print(f"   Amount paid: €{getattr(enrollment, 'amount_paid_eur', 'Not set')}")
            else:
                print("❌ Enrollment not found in database")
        else:
            print("ℹ️  No enrollment created (normal for hybrid payments)")
            
    else:
        print(f"❌ Payment intent failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Raw response: {response.content}")

def main():
    """Run all tests"""
    print("Starting TeoCoin Payment Flow Tests")
    print(f"Django settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    
    # Test 1: Check user wallets
    student, wallet = test_user_wallet()
    if not student:
        print("⚠️  No student with wallet found, but continuing with tests...")
        # Get any student for testing
        student = User.objects.filter(role='student', is_active=True).first()
        if not student:
            print("ERROR: No student users found")
            return
    
    # Test 2: Check course settings
    course = test_course_teocoin_settings()
    if not course:
        print("ERROR: No course with TeoCoin discount found")
        return
    
    # Test 3: Check payment views and services
    check_payment_views()
    test_teocoin_services()
    
    # Test 4: Check enrollments
    check_enrollments()
    
    # Test 5: Test payment intent creation
    test_payment_intent_creation(student, course)
    
    # Test 6: Simulate full TeoCoin payment flow
    simulate_teocoin_payment_flow(student, course)
    
    print_separator("TESTS COMPLETED")
    
    # Final summary
    print("\n📊 SUMMARY:")
    print("1. Check if TeoCoin transactions are actually happening")
    print("2. Verify that wallet balances are being updated")
    print("3. Confirm that discount amounts are correctly calculated")
    print("4. Test the blockchain integration")

if __name__ == "__main__":
    main()
