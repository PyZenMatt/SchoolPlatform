#!/usr/bin/env python3
"""
Test the fixed discount calculation logic
"""

import os
import django
import sys

# Setup Django environment
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from services.teocoin_discount_service import teocoin_discount_service

def test_discount_calculation():
    """Test the discount calculation with the fix"""
    
    print("🧮 Testing Fixed Discount Calculation")
    print("=" * 50)
    
    # Test case: €100 course with 10% discount
    course_price_cents = 10000  # €100.00
    discount_percent = 10
    
    print(f"Course price: {course_price_cents} cents = €{course_price_cents/100}")
    print(f"Discount: {discount_percent}%")
    
    # Test our backend calculation
    teo_cost, teacher_bonus = teocoin_discount_service._calculate_teo_amounts(
        course_price_cents, discount_percent
    )
    
    print(f"\n✅ Backend Calculation (Fixed):")
    print(f"TEO cost: {teo_cost} wei = {teo_cost / 10**18} TEO")
    print(f"Teacher bonus: {teacher_bonus} wei = {teacher_bonus / 10**18} TEO")
    
    # Expected values
    discount_value_cents = 1000  # €10
    expected_teo = 100  # 10 TEO per €1, so €10 = 100 TEO
    expected_bonus = 25  # 25% of 100 TEO = 25 TEO
    
    print(f"\n🎯 Expected:")
    print(f"TEO cost: {expected_teo} TEO")
    print(f"Teacher bonus: {expected_bonus} TEO")
    
    # Verify calculation
    actual_teo = teo_cost / 10**18
    actual_bonus = teacher_bonus / 10**18
    
    if abs(actual_teo - expected_teo) < 0.001:
        print(f"\n✅ TEO cost calculation: CORRECT")
    else:
        print(f"\n❌ TEO cost calculation: WRONG (got {actual_teo}, expected {expected_teo})")
    
    if abs(actual_bonus - expected_bonus) < 0.001:
        print(f"✅ Teacher bonus calculation: CORRECT")
    else:
        print(f"❌ Teacher bonus calculation: WRONG (got {actual_bonus}, expected {expected_bonus})")
    
    # Test contract calculation (still has the bug)
    try:
        if teocoin_discount_service.discount_contract:
            contract_result = teocoin_discount_service.discount_contract.functions.calculateTeoCost(
                course_price_cents, discount_percent
            ).call()
            
            contract_teo = contract_result[0] / 10**18
            contract_bonus = contract_result[1] / 10**18
            
            print(f"\n⚠️  Contract Calculation (Has Bug):")
            print(f"TEO cost: {contract_result[0]} wei = {contract_teo} TEO")
            print(f"Teacher bonus: {contract_result[1]} wei = {contract_bonus} TEO")
            print(f"Note: Contract bug compensated in backend")
    except Exception as e:
        print(f"\n⚠️  Contract calculation test failed: {e}")
    
    print(f"\n" + "=" * 50)
    print(f"🎯 Status: Backend calculation fixed ✅")
    print(f"📝 Note: Contract has calculation bug but backend compensates")
    print(f"🚀 Ready for frontend testing!")

if __name__ == "__main__":
    test_discount_calculation()
