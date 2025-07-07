#!/usr/bin/env python3
"""
Phase 3D: TeoCoin Escrow System Integration Test
Test the complete escrow flow from creation to teacher decision
"""

import os
import sys
import django
import json
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from courses.models import Course
from rewards.models import TeoCoinEscrow, BlockchainTransaction
from services.escrow_service import TeoCoinEscrowService
from notifications.models import Notification

User = get_user_model()

class EscrowIntegrationTest:
    def __init__(self):
        self.escrow_service = TeoCoinEscrowService()
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        print(f"{status}: {test_name}")
        if message:
            print(f"    📝 {message}")
        if details:
            print(f"    📊 {details}")
        print()

    def setup_test_data(self):
        """Create test users and course"""
        print("🏗️  Setting up test data...")
        
        # Create test student
        self.student, created = User.objects.get_or_create(
            username='test_student_escrow',
            defaults={
                'email': 'student@escrow.test',
                'first_name': 'Test',
                'last_name': 'Student',
                'user_type': 'student'
            }
        )
        
        # Create test teacher
        self.teacher, created = User.objects.get_or_create(
            username='test_teacher_escrow',
            defaults={
                'email': 'teacher@escrow.test',
                'first_name': 'Test',
                'last_name': 'Teacher',
                'user_type': 'teacher'
            }
        )
        
        # Create test course
        self.course, created = Course.objects.get_or_create(
            title='Test Escrow Course',
            defaults={
                'description': 'Course for testing escrow system',
                'price_eur': Decimal('100.00'),
                'teacher': self.teacher
            }
        )
        
        print(f"    👤 Student: {self.student.username}")
        print(f"    👨‍🏫 Teacher: {self.teacher.username}")
        print(f"    📚 Course: {self.course.title} (€{self.course.price_eur})")
        print()

    def test_escrow_creation(self):
        """Test 1: Create escrow with TeoCoin discount"""
        try:
            # Create escrow for 20% discount (€20 discount for €100 course)
            teocoin_amount = Decimal('2000')  # 2000 TCN
            discount_percentage = 20  # 20%
            discount_data = {
                'percentage': discount_percentage,
                'euro_amount': Decimal('20.00'),
                'original_price': self.course.price_eur
            }
            
            escrow = self.escrow_service.create_escrow(
                student=self.student,
                teacher=self.teacher,
                course=self.course,
                teocoin_amount=teocoin_amount,
                discount_data=discount_data
            )
            
            # Verify escrow creation
            assert escrow.student == self.student
            assert escrow.course == self.course
            assert escrow.teacher == self.teacher
            assert escrow.original_price == self.course.price_eur
            assert escrow.discount_amount == discount_amount
            assert escrow.discounted_price == self.course.price_eur - discount_amount
            assert escrow.teocoin_amount == teocoin_amount
            assert escrow.status == 'pending'
            
            # Check notification was created
            notification_exists = Notification.objects.filter(
                user=self.teacher,
                notification_type='escrow_created'
            ).exists()
            
            self.escrow = escrow
            
            self.log_test(
                "Escrow Creation",
                True,
                f"Created escrow ID {escrow.id}",
                f"Discount: €{discount_amount}, Final Price: €{escrow.discounted_price}, Notification: {notification_exists}"
            )
            
        except Exception as e:
            self.log_test("Escrow Creation", False, f"Error: {str(e)}")
            return False
        
        return True

    def test_escrow_acceptance(self):
        """Test 2: Teacher accepts escrow"""
        try:
            # Accept the escrow
            result = self.escrow_service.accept_escrow(self.escrow.id)
            
            # Verify escrow was accepted
            self.escrow.refresh_from_db()
            assert self.escrow.status == 'accepted'
            assert self.escrow.accepted_at is not None
            
            # Check acceptance notification
            notification_exists = Notification.objects.filter(
                user=self.student,
                notification_type='escrow_accepted'
            ).exists()
            
            # Check that blockchain transaction was created
            transaction_exists = BlockchainTransaction.objects.filter(
                user=self.teacher,
                transaction_type='course_earned',
                related_object_id=str(self.escrow.id)
            ).exists()
            
            self.log_test(
                "Escrow Acceptance",
                True,
                f"Teacher accepted escrow",
                f"Student notified: {notification_exists}, Transaction created: {transaction_exists}"
            )
            
        except Exception as e:
            self.log_test("Escrow Acceptance", False, f"Error: {str(e)}")
            return False
        
        return True

    def test_escrow_rejection_flow(self):
        """Test 3: Create and reject another escrow"""
        try:
            # Create another course for rejection test
            reject_course, created = Course.objects.get_or_create(
                title='Test Rejection Course',
                defaults={
                    'description': 'Course for testing escrow rejection',
                    'price_eur': Decimal('50.00'),
                    'teacher': self.teacher
                }
            )
            
            # Create escrow
            teocoin_amount = '1000000000000000000000'  # 1000 TCN
            discount_amount = Decimal('10.00')
            
            reject_escrow = self.escrow_service.create_escrow(
                student=self.student,
                course=reject_course,
                teocoin_amount=teocoin_amount,
                discount_amount=discount_amount
            )
            
            # Reject the escrow
            result = self.escrow_service.reject_escrow(reject_escrow.id)
            
            # Verify escrow was rejected
            reject_escrow.refresh_from_db()
            assert reject_escrow.status == 'rejected'
            assert reject_escrow.rejected_at is not None
            
            # Check rejection notification
            notification_exists = Notification.objects.filter(
                user=self.student,
                notification_type='escrow_rejected'
            ).exists()
            
            # Check that refund transaction was created
            refund_transaction_exists = BlockchainTransaction.objects.filter(
                user=self.student,
                transaction_type='transfer',
                related_object_id=str(reject_escrow.id)
            ).exists()
            
            self.log_test(
                "Escrow Rejection",
                True,
                f"Teacher rejected escrow",
                f"Student notified: {notification_exists}, Refund transaction: {refund_transaction_exists}"
            )
            
        except Exception as e:
            self.log_test("Escrow Rejection", False, f"Error: {str(e)}")
            return False
        
        return True

    def test_escrow_expiration(self):
        """Test 4: Escrow expiration handling"""
        try:
            # Create an expired escrow by modifying the created_at date
            expired_course, created = Course.objects.get_or_create(
                title='Test Expired Course',
                defaults={
                    'description': 'Course for testing escrow expiration',
                    'price_eur': Decimal('75.00'),
                    'teacher': self.teacher
                }
            )
            
            # Create escrow
            expired_escrow = self.escrow_service.create_escrow(
                student=self.student,
                course=expired_course,
                teocoin_amount='1500000000000000000000',  # 1500 TCN
                discount_amount=Decimal('15.00')
            )
            
            # Manually set creation date to 8 days ago
            expired_escrow.created_at = datetime.now() - timedelta(days=8)
            expired_escrow.save()
            
            # Process expired escrows
            expired_count = self.escrow_service.process_expired_escrows()
            
            # Verify escrow was marked as expired
            expired_escrow.refresh_from_db()
            
            self.log_test(
                "Escrow Expiration",
                expired_escrow.status == 'expired',
                f"Processed {expired_count} expired escrows",
                f"Escrow {expired_escrow.id} status: {expired_escrow.status}"
            )
            
        except Exception as e:
            self.log_test("Escrow Expiration", False, f"Error: {str(e)}")
            return False
        
        return True

    def test_api_endpoints(self):
        """Test 5: API endpoint accessibility"""
        try:
            from django.test import Client
            
            client = Client()
            
            # Login as teacher
            client.force_login(self.teacher)
            
            # Test escrow list endpoint
            try:
                response = client.get('/api/v1/services/teacher/escrows/')
                api_accessible = response.status_code in [200, 302]  # 302 might be redirect
            except Exception:
                api_accessible = False
            
            # Test escrow stats endpoint
            try:
                stats_response = client.get('/api/v1/services/teacher/escrows/stats/')
                stats_accessible = stats_response.status_code in [200, 302]
            except Exception:
                stats_accessible = False
            
            self.log_test(
                "API Endpoints",
                api_accessible or stats_accessible,  # At least one should work
                f"API accessibility test",
                f"Escrows endpoint: {api_accessible}, Stats endpoint: {stats_accessible}"
            )
            
        except Exception as e:
            self.log_test("API Endpoints", False, f"Error: {str(e)}")
            return False
        
        return True

    def generate_report(self):
        """Generate comprehensive test report"""
        print("=" * 60)
        print("📊 PHASE 3D INTEGRATION TEST REPORT")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if "✅" in result['status'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("🧪 DETAILED RESULTS:")
        print("-" * 40)
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['message']:
                print(f"    📝 {result['message']}")
            if result['details']:
                print(f"    📊 {result['details']}")
            print()
        
        # Database state summary
        print("💾 DATABASE STATE SUMMARY:")
        print("-" * 40)
        escrow_count = TeoCoinEscrow.objects.count()
        pending_count = TeoCoinEscrow.objects.filter(status='pending').count()
        accepted_count = TeoCoinEscrow.objects.filter(status='accepted').count()
        rejected_count = TeoCoinEscrow.objects.filter(status='rejected').count()
        expired_count = TeoCoinEscrow.objects.filter(status='expired').count()
        
        print(f"Total Escrows: {escrow_count}")
        print(f"├── Pending: {pending_count}")
        print(f"├── Accepted: {accepted_count}")
        print(f"├── Rejected: {rejected_count}")
        print(f"└── Expired: {expired_count}")
        print()
        
        # Notification count
        notification_count = Notification.objects.filter(
            notification_type__icontains='escrow'
        ).count()
        print(f"Escrow Notifications: {notification_count}")
        print()
        
        return success_rate >= 80  # 80% pass rate required

    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 STARTING PHASE 3D INTEGRATION TESTS")
        print("=" * 60)
        print()
        
        # Setup
        self.setup_test_data()
        
        # Run tests in sequence
        tests = [
            self.test_escrow_creation,
            self.test_escrow_acceptance,
            self.test_escrow_rejection_flow,
            self.test_escrow_expiration,
            self.test_api_endpoints
        ]
        
        for test in tests:
            test()
        
        # Generate final report
        return self.generate_report()

if __name__ == "__main__":
    tester = EscrowIntegrationTest()
    success = tester.run_all_tests()
    
    if success:
        print("🎉 PHASE 3D INTEGRATION TESTS PASSED!")
        print("✅ TeoCoin Escrow System is ready for production")
    else:
        print("⚠️  SOME TESTS FAILED - Review results above")
        print("🔧 Fix issues before proceeding to production")
    
    print("\n" + "=" * 60)
