#!/usr/bin/env python3
"""
Teacher Accept Escrow Demo - Complete the TeoCoin discount flow
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, CourseEnrollment
from rewards.models import TeoCoinEscrow
from services.escrow_service import TeoCoinEscrowService

User = get_user_model()

def simulate_teacher_accept():
    print("👨‍🏫 TEACHER ESCROW DECISION SIMULATION")
    print("=" * 50)
    print()
    
    try:
        # Get the pending escrow
        escrow = TeoCoinEscrow.objects.filter(
            status='pending'
        ).order_by('-created_at').first()
        
        if not escrow:
            print("❌ No pending escrow found")
            return
            
        teacher = escrow.teacher
        student = escrow.student
        course = escrow.course
        
        print(f"📋 Escrow Details:")
        print(f"   Student: {student.username}")
        print(f"   Teacher: {teacher.username}")
        print(f"   Course: {course.title}")
        print(f"   TeoCoin Amount: {escrow.teocoin_amount} TCN")
        print(f"   Discount: €{escrow.discount_euro_amount}")
        print(f"   Status: {escrow.status}")
        print()
        
        print("🤔 Teacher's Decision Options:")
        print(f"   ✅ ACCEPT: Get €{escrow.reduced_euro_commission} + {escrow.teocoin_amount} TCN")
        print(f"   ❌ REJECT: Get €{escrow.standard_euro_commission} (student pays full price)")
        print()
        
        # Simulate teacher accepts
        print("💭 Teacher decides to ACCEPT the TeoCoin discount...")
        print()
        
        try:
            escrow_service = TeoCoinEscrowService()
            result = escrow_service.accept_escrow(
                escrow_id=escrow.pk,
                teacher=teacher
            )
            
            # Refresh escrow
            escrow.refresh_from_db()
            
            if escrow.status == 'accepted':
                print("🎉 ESCROW ACCEPTED SUCCESSFULLY!")
                print(f"   ✅ Status changed to: {escrow.status}")
                print(f"   ✅ Decision time: {escrow.teacher_decision_at}")
                print()
                
                # Now create the student enrollment (this would happen in the real system)
                enrollment, created = CourseEnrollment.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        'payment_method': 'teocoin',
                        'amount_paid_eur': course.price_eur - escrow.discount_euro_amount,
                        'amount_paid_teocoin': escrow.teocoin_amount
                    }
                )
                
                if created:
                    print("🎓 STUDENT ENROLLED IN COURSE!")
                    print(f"   ✅ Payment method: {enrollment.payment_method}")
                    print(f"   ✅ EUR paid: €{enrollment.amount_paid_eur}")
                    print(f"   ✅ TeoCoin used: {enrollment.amount_paid_teocoin} TCN")
                    print(f"   ✅ Enrolled at: {enrollment.enrolled_at}")
                else:
                    print("ℹ️  Student was already enrolled")
                
                print()
                print("💰 FINAL OUTCOME:")
                print(f"   🎓 Student: Saved €{escrow.discount_euro_amount} and got course access")
                print(f"   👨‍🏫 Teacher: Received €{escrow.reduced_euro_commission} + {escrow.teocoin_amount} TCN")
                print(f"   🏫 Platform: Successful TeoCoin discount transaction")
                
            else:
                print(f"❌ Escrow status is still: {escrow.status}")
                
        except Exception as e:
            print(f"❌ Error accepting escrow: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    simulate_teacher_accept()
