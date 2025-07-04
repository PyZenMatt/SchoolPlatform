#!/usr/bin/env python3
"""Quick test script to debug TEO calculation issues"""

import os
import sys
import django

# Add project root to path
project_root = '/home/teo/Project/school/schoolplatform'
sys.path.insert(0, project_root)
os.chdir(project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import Course

def test_teo_calculations():
    print("🔍 Testing TEO calculations...")
    
    # Get a test course
    course = Course.objects.filter(price_eur__gt=0).first()
    if not course:
        print("❌ No courses found with price > 0")
        return
    
    print(f"📚 Course: {course.title}")
    print(f"💰 Price EUR: {course.price_eur}")
    print(f"📊 Discount %: {course.teocoin_discount_percent}")
    
    # Test the calculations
    try:
        teo_discount_amount = course.get_teocoin_discount_amount()
        print(f"🪙 TEO needed for discount: {teo_discount_amount} (type: {type(teo_discount_amount)})")
        
        # Test conversion to wei
        teo_wei = int(float(teo_discount_amount) * 10**18)
        print(f"⚖️ TEO in wei: {teo_wei}")
        
        # Test EUR conversion
        eur_discount = float(teo_discount_amount) / 10.0
        print(f"💸 EUR discount value: {eur_discount}")
        
        print("✅ All calculations successful!")
        
    except Exception as e:
        print(f"❌ Error in calculations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_teo_calculations()
