#!/usr/bin/env python
"""
Quick test to verify the payment endpoint imports work correctly
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_imports():
    """Test that all imports in the payment view work"""
    print("🔍 TESTING PAYMENT VIEW IMPORTS")
    print("=" * 40)
    
    try:
        # Test the imports that were causing issues
        print("📦 Testing TeacherDiscountAbsorptionService import...")
        from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
        print("✅ TeacherDiscountAbsorptionService imported successfully")
        
        print("📦 Testing DBTeoCoinService import...")
        from services.db_teocoin_service import DBTeoCoinService
        print("✅ DBTeoCoinService imported successfully")
        
        # Test creating instances
        print("🔧 Testing service instantiation...")
        db_service = DBTeoCoinService()
        print("✅ DBTeoCoinService instance created")
        
        # Test a basic method call
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.first()
        
        if user:
            print("🔧 Testing basic service method...")
            balance = db_service.get_user_balance(user)
            print(f"✅ get_user_balance works: {balance['available_balance']} TEO")
        
        print("\n🎉 ALL IMPORTS AND BASIC OPERATIONS SUCCESSFUL!")
        print("The payment endpoint should now work without import errors.")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()

def test_absorption_creation():
    """Test the specific method that was failing"""
    print("\n" + "=" * 40)
    print("🔍 TESTING ABSORPTION CREATION")
    print("=" * 40)
    
    try:
        from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
        from django.contrib.auth import get_user_model
        from courses.models import Course
        
        User = get_user_model()
        
        # Find a teacher and course for testing
        teacher = User.objects.filter(is_staff=True).first()
        student = User.objects.filter(is_staff=False).first()
        course = Course.objects.first()
        
        if not all([teacher, student, course]):
            print("❌ Missing required objects for test")
            return
            
        print(f"👨‍🏫 Teacher: {teacher.username}")
        print(f"👨‍🎓 Student: {student.username}")
        print(f"📚 Course: {course.title}")
        
        # Test the exact call that was failing in payment view
        discount_data = {
            'discount_percentage': 10,
            'teo_used': 1.5,
            'discount_amount_eur': 1.5,
            'course_price_eur': 15.0
        }
        
        print("🔧 Testing absorption opportunity creation...")
        absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
            student=student,
            teacher=teacher,
            course=course,
            discount_data=discount_data
        )
        
        print(f"✅ Absorption created successfully!")
        print(f"   ID: {absorption.pk}")
        print(f"   Status: {absorption.status}")
        print(f"   Teacher TEO: {absorption.final_teacher_teo}")
        
    except Exception as e:
        print(f"❌ Absorption creation test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imports()
    test_absorption_creation()
