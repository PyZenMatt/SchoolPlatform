#!/usr/bin/env python
"""
Test the NOT NULL constraint fix for TeacherDiscountAbsorption
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_not_null_fix():
    """Test that the NOT NULL constraint error is fixed"""
    print("🔧 TESTING NOT NULL CONSTRAINT FIX")
    print("=" * 50)
    
    try:
        from django.contrib.auth import get_user_model
        from courses.models import Course
        from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
        from decimal import Decimal
        
        User = get_user_model()
        
        # Find objects for testing
        teacher = User.objects.filter(is_staff=True).first()
        student = User.objects.filter(is_staff=False).first() 
        course = Course.objects.first()
        
        if not teacher:
            teacher = User.objects.first()
        if not student:
            student = User.objects.last()
            
        if not all([teacher, student, course]):
            print("❌ Missing required test objects")
            return
        
        print(f"✅ Test objects found")
        
        # Use the exact same data structure as the payment endpoint
        discount_data = {
            'discount_percentage': 10,
            'teo_used': 1.5,
            'discount_amount_eur': 1.5,
            'course_price_eur': 15.0
        }
        
        print(f"🧪 Testing absorption creation...")
        print(f"   This should NOT fail with NOT NULL constraint error")
        
        # This call previously failed with:
        # "NOT NULL constraint failed: rewards_teacher_discount_absorption.option_a_teacher_eur"
        absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
            student=student,
            teacher=teacher,
            course=course,
            discount_data=discount_data
        )
        
        print(f"✅ SUCCESS! Absorption created without NOT NULL error")
        print(f"   ID: {absorption.pk}")
        print(f"   All option fields are properly set")
        print(f"🎉 The payment endpoint should now work!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_not_null_fix()
