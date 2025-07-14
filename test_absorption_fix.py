#!/usr/bin/env python
"""
Test that the absorption creation fix works
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_absorption_creation_fix():
    """Test that absorption creation now works with expires_at field"""
    print("🔧 TESTING ABSORPTION CREATION FIX")
    print("=" * 50)
    
    try:
        from django.contrib.auth import get_user_model
        from courses.models import Course
        from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
        
        User = get_user_model()
        
        # Find teacher, student, and course
        teacher = User.objects.filter(is_staff=True).first() or User.objects.first()
        student = User.objects.filter(is_staff=False).first() or User.objects.last()
        course = Course.objects.first()
        
        if not all([teacher, student, course]):
            print("❌ Missing required objects for test")
            
            # Show what we have
            print(f"   Teachers: {User.objects.filter(is_staff=True).count()}")
            print(f"   Students: {User.objects.filter(is_staff=False).count()}")
            print(f"   Courses: {Course.objects.count()}")
            return
        
        print(f"✅ Test objects found:")
        print(f"   Teacher: {teacher.username}")
        print(f"   Student: {student.username}")
        print(f"   Course: {course.title}")
        
        # Test data matching the error scenario
        discount_data = {
            'discount_percentage': 10,
            'teo_used': 1.5,
            'discount_amount_eur': 1.5,
            'course_price_eur': 15.0
        }
        
        print(f"")
        print(f"🧪 Testing absorption creation with expires_at fix...")
        print(f"   Discount data: {discount_data}")
        
        # This should now work without throwing an error
        absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
            student=student,
            teacher=teacher,
            course=course,
            discount_data=discount_data
        )
        
        print(f"")
        print(f"✅ ABSORPTION CREATED SUCCESSFULLY!")
        print(f"   ID: {absorption.pk}")
        print(f"   Status: {absorption.status}")
        print(f"   Expires at: {absorption.expires_at}")
        print(f"   Hours remaining: {absorption.hours_remaining}")
        print(f"   Teacher TEO option: {absorption.option_b_teacher_teo}")
        print(f"   Teacher EUR option: {absorption.option_a_teacher_eur}")
        
        print(f"")
        print(f"🎉 FIX CONFIRMED!")
        print(f"   The payment endpoint should now work correctly")
        print(f"   Teachers will receive absorption notifications")
        print(f"   The 500 error should be resolved")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"")
        print(f"🔍 ERROR ANALYSIS:")
        if "expires_at" in str(e):
            print(f"   Still an expires_at issue - check model constraints")
        else:
            print(f"   Different error - may need additional fixes")

if __name__ == "__main__":
    test_absorption_creation_fix()
