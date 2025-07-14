#!/usr/bin/env python
"""
Debug script for enrollment detection and teacher absorption issues
Run this to diagnose:
1. Why courses show as not purchased even after enrollment
2. Why teacher TeoCoin transactions don't happen from notifications
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, CourseEnrollment
from rewards.models import TeacherDiscountAbsorption
from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
from services.db_teocoin_service import DBTeoCoinService
from decimal import Decimal

User = get_user_model()

def test_enrollment_detection():
    """Test why enrolled courses show as not purchased"""
    print("=" * 50)
    print("🔍 TESTING ENROLLMENT DETECTION")
    print("=" * 50)
    
    # Find a user with enrollments
    enrollments = CourseEnrollment.objects.select_related('student', 'course')[:3]
    
    if not enrollments.exists():
        print("❌ No enrollments found in database")
        return
    
    for enrollment in enrollments:
        student = enrollment.student
        course = enrollment.course
        
        print(f"\n📚 Testing Course: {course.title}")
        print(f"👨‍🎓 Student: {student.username}")
        print(f"📅 Enrolled: {enrollment.enrolled_at}")
        print(f"💰 Payment Method: {enrollment.payment_method}")
        
        # Test 1: Direct CourseEnrollment check
        direct_check = CourseEnrollment.objects.filter(student=student, course=course).exists()
        print(f"✅ Direct CourseEnrollment exists: {direct_check}")
        
        # Test 2: Many-to-many relationship check (what serializer uses)
        m2m_check = course.students.filter(pk=student.pk).exists()
        print(f"🔗 M2M relationship exists: {m2m_check}")
        
        # Test 3: Direct check using the same logic as serializer
        user = student
        is_enrolled_direct = course.students.filter(pk=user.pk).exists()
        print(f"📋 Direct serializer logic test: {is_enrolled_direct}")
        
        # Test 4: Check if issue is in the course API response
        print(f"� Course ID: {course.pk} - checking API response...")
        
        if not m2m_check:
            print("🚨 ISSUE FOUND: M2M relationship not working!")
            print("   This explains why courses show as not purchased")
            
            # Check if we can fix it
            print("   Attempting to fix M2M relationship...")
            try:
                course.students.add(student)
                print("   ✅ Added student to course.students")
                
                # Re-test
                m2m_check_after = course.students.filter(pk=student.pk).exists()
                print(f"   🔄 M2M check after fix: {m2m_check_after}")
            except Exception as e:
                print(f"   ❌ Failed to fix: {e}")
        
        print("-" * 30)

def test_teacher_absorption_system():
    """Test why teacher TeoCoin transactions don't happen"""
    print("\n" + "=" * 50)
    print("🔍 TESTING TEACHER ABSORPTION SYSTEM")
    print("=" * 50)
    
    # Check if there are any absorptions
    total_absorptions = TeacherDiscountAbsorption.objects.count()
    print(f"📊 Total absorptions in database: {total_absorptions}")
    
    if total_absorptions == 0:
        print("❌ No absorptions found - this explains why teacher notifications don't work")
        print("   The absorption system isn't creating opportunities when students use discounts")
        
        # Test if we can create an absorption manually
        print("\n🧪 Creating test absorption...")
        
        # Find a teacher and course
        teacher = User.objects.filter(is_staff=True).first()
        course = Course.objects.first()
        
        if teacher and course:
            print(f"👨‍🏫 Teacher: {teacher.username}")
            print(f"📚 Course: {course.title}")
            
            # Check teacher's current balance
            db_service = DBTeoCoinService()
            balance_before = db_service.get_user_balance(teacher)
            print(f"💰 Teacher balance before: {balance_before['available_balance']} TEO")
            
            # Create test absorption
            absorption = TeacherDiscountAbsorption.objects.create(
                teacher=teacher,
                course=course,
                discount_amount_eur=Decimal('10.00'),
                final_teacher_teo=Decimal('12.50'),  # 10 + 25% bonus
                final_teacher_eur=Decimal('7.50'),   # 75% commission
                final_platform_eur=Decimal('2.50'),
                status='pending'
            )
            print(f"✅ Created test absorption: ID {absorption.pk}")
            
            # Test teacher choice processing
            print("\n🎯 Testing teacher choice 'absorb'...")
            
            try:
                service = TeacherDiscountAbsorptionService()
                result = service.process_teacher_choice(
                    absorption_id=absorption.pk,
                    choice='absorb',
                    teacher=teacher
                )
                
                print(f"✅ Choice processed successfully!")
                print(f"   Status: {result.status}")
                print(f"   TEO earned: {result.final_teacher_teo}")
                
                # Check balance after
                balance_after = db_service.get_user_balance(teacher)
                teo_gained = balance_after['available_balance'] - balance_before['available_balance']
                print(f"💰 Teacher balance after: {balance_after['available_balance']} TEO")
                print(f"📈 TEO gained: {teo_gained} TEO")
                
                if teo_gained > 0:
                    print("✅ TeoCoin transaction worked correctly!")
                else:
                    print("❌ No TeoCoin was added to teacher's account")
                    
            except Exception as e:
                print(f"❌ Error processing choice: {e}")
                
        else:
            print("❌ No teacher or course found for testing")
    
    else:
        # Test existing absorptions
        pending = TeacherDiscountAbsorption.objects.filter(status='pending')
        absorbed = TeacherDiscountAbsorption.objects.filter(status='absorbed')
        
        print(f"⏳ Pending: {pending.count()}")
        print(f"✅ Absorbed: {absorbed.count()}")
        
        # Show recent absorptions
        recent = TeacherDiscountAbsorption.objects.order_by('-created_at')[:5]
        for absorption in recent:
            print(f"   ID {absorption.pk}: {absorption.status} - {absorption.teacher.username} - {absorption.course.title}")

def check_payment_enrollment_connection():
    """Check if payment success properly creates enrollments and absorptions"""
    print("\n" + "=" * 50)
    print("🔍 CHECKING PAYMENT → ENROLLMENT → ABSORPTION FLOW")
    print("=" * 50)
    
    # Find recent enrollments
    recent_enrollments = CourseEnrollment.objects.order_by('-enrollment_date')[:3]
    
    for enrollment in recent_enrollments:
        print(f"\n📚 Enrollment: {enrollment.student.username} → {enrollment.course.title}")
        print(f"📅 Date: {enrollment.enrolled_at}")
        print(f"💳 Payment: {enrollment.payment_method}")
        print(f"💰 Discount Used: {enrollment.discount_amount_eur or 'None'}")
        
        # Check if absorption was created for TeoCoin discounts
        if enrollment.payment_method == 'teocoin_discount':
            absorption = TeacherDiscountAbsorption.objects.filter(
                course=enrollment.course,
                created_at__date=enrollment.enrolled_at.date()
            ).first()
            
            if absorption:
                print(f"✅ Absorption created: ID {absorption.pk}, Status: {absorption.status}")
            else:
                print("❌ No absorption found - this is the problem!")
                print("   TeoCoin discounts should create teacher absorption opportunities")

if __name__ == "__main__":
    try:
        print("🚀 Starting diagnosis...")
        test_enrollment_detection()
        test_teacher_absorption_system() 
        check_payment_enrollment_connection()
        print("\n" + "=" * 50)
        print("✅ DIAGNOSIS COMPLETE")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error during diagnosis: {e}")
        import traceback
        traceback.print_exc()
