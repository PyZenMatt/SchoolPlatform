#!/usr/bin/env python3
"""
Test di integrazione completo per il sistema blockchain reward
Simula tutto il flusso: submission -> approval -> reward -> review -> reviewer reward
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from courses.models import Course, Lesson, Exercise, ExerciseSubmission, ExerciseReview
from rewards.models import TeoCoinTransaction, BlockchainTransaction
from rewards.blockchain_rewards import BlockchainRewardCalculator, BlockchainRewardManager
from django.db import transaction

User = get_user_model()


def setup_test_data():
    """
    Crea dati di test
    """
    print("📚 Setting up test data...")
    
    # Crea utenti con indirizzi wallet validi
    student, created = User.objects.get_or_create(
        email='test_student@example.com',
        defaults={
            'username': 'test_student',
            'first_name': 'Test',
            'last_name': 'Student', 
            'wallet_address': '0x691dea93DB427190CDF7B63Ba67E05b14C5deb6F'  # Valid test address
        }
    )
    
    reviewer, created = User.objects.get_or_create(
        email='test_reviewer@example.com',
        defaults={
            'username': 'test_reviewer',
            'first_name': 'Test',
            'last_name': 'Reviewer',
            'wallet_address': '0x4a1302F889f180cE7a08E8e30752f9BC8812037A'  # Valid test address
        }
    )
    
    teacher, created = User.objects.get_or_create(
        email='test_teacher@example.com',
        defaults={
            'username': 'test_teacher',
            'first_name': 'Test',
            'last_name': 'Teacher',
            'wallet_address': '0x742d35Cc6cF000000000000000000003'
        }
    )
    
    # Crea corso
    course, created = Course.objects.get_or_create(
        title='Test Blockchain Course',
        defaults={
            'description': 'Corso di test per blockchain rewards',
            'teacher': teacher,
            'price': 30,  # Intero non Decimal
            'is_approved': True
        }
    )
    
    # Crea lezione
    lesson, created = Lesson.objects.get_or_create(
        title='Test Lesson',
        defaults={
            'content': 'Lezione di test',
            'course': course,
            'teacher': teacher,
            'lesson_type': 'theory'
        }
    )
    
    # Crea esercizio
    exercise, created = Exercise.objects.get_or_create(
        title='Test Exercise',
        defaults={
            'description': 'Esercizio di test per rewards',
            'lesson': lesson,
            'exercise_type': 'practical',
            'difficulty': 'beginner'
        }
    )
    
    return student, reviewer, teacher, course, lesson, exercise


def test_full_reward_flow():
    """
    Test completo del flusso di reward
    """
    print("🚀 Testing full reward flow...")
    
    student, reviewer, teacher, course, lesson, exercise = setup_test_data()
    
    # Fase 1: Studente sottomette esercizio
    print("\n1️⃣ Studente sottomette esercizio...")
    submission = ExerciseSubmission.objects.create(
        exercise=exercise,
        student=student,
        content="Questo è il contenuto della mia submission di test",
        is_approved=False  # Non ancora approvato
    )
    print(f"   Submission creata: {submission.pk}")
    
    # Verifica che non ci siano ancora reward
    initial_teo_transactions = TeoCoinTransaction.objects.filter(user=student).count()
    print(f"   Transazioni TEO iniziali studente: {initial_teo_transactions}")
    
    # Fase 2: Simuliamo approvazione
    print("\n2️⃣ Approvazione esercizio (simulata)...")
    
    # Prima creiamo alcune review per arrivare a 3
    for i in range(3):
        review = ExerciseReview.objects.create(
            submission=submission,
            reviewer=reviewer,
            score=8,  # Punteggio sufficiente per approvazione
            reviewed_at=timezone.now()
        )
        print(f"   Review {i+1} creata con score: {review.score}")
    
    # Calcola media e approva
    ExerciseReview.calculate_average_score(submission)
    submission.refresh_from_db()
    
    print(f"   Media calcolata: {submission.average_score}")
    print(f"   Approvato: {submission.is_approved}")
    
    # Verifica che sia stato creato il reward per lo studente
    student_teo_transactions = TeoCoinTransaction.objects.filter(
        user=student, 
        transaction_type='exercise_reward'
    )
    print(f"   Transazioni reward studente: {student_teo_transactions.count()}")
    
    if student_teo_transactions.exists():
        reward_transaction = student_teo_transactions.first()
        if reward_transaction and reward_transaction.amount:
            reward_amount = Decimal(reward_transaction.amount) / Decimal('1000')  # Converti da millesimi
            print(f"   Reward studente: {reward_amount} TEO")
        
        # Verifica transazione blockchain
        blockchain_tx = BlockchainTransaction.objects.filter(
            user=student,
            related_teocoin_transaction=reward_transaction
        ).first()
        
        if blockchain_tx:
            print(f"   Transazione blockchain: {blockchain_tx.status}")
            print(f"   Amount blockchain: {blockchain_tx.amount} TEO")
        else:
            print("   ⚠️ Nessuna transazione blockchain trovata")
    
    # Fase 3: Verifica reward reviewer
    print("\n3️⃣ Verifica reward reviewer...")
    
    reviewer_teo_transactions = TeoCoinTransaction.objects.filter(
        user=reviewer,
        transaction_type='review_reward'
    )
    
    print(f"   Transazioni review reward: {reviewer_teo_transactions.count()}")
    
    if reviewer_teo_transactions.exists():
        for review_tx in reviewer_teo_transactions:
            review_reward = Decimal(review_tx.amount) / Decimal('1000')
            print(f"   Reviewer reward: {review_reward} TEO")
            
            # Verifica transazione blockchain
            blockchain_tx = BlockchainTransaction.objects.filter(
                user=reviewer,
                related_teocoin_transaction=review_tx
            ).first()
            
            if blockchain_tx:
                print(f"   Blockchain status: {blockchain_tx.status}")


def test_reward_calculation_accuracy():
    """
    Test accuratezza calcoli reward
    """
    print("\n🧮 Testing reward calculation accuracy...")
    
    student, reviewer, teacher, course, lesson, exercise = setup_test_data()
    
    # Calcola il reward teorico
    theoretical_pool = BlockchainRewardCalculator.calculate_course_reward_pool(course)
    theoretical_rewards = BlockchainRewardCalculator.distribute_exercise_rewards(course, 1)
    expected_student_reward = theoretical_rewards[0] if theoretical_rewards else Decimal('0')
    expected_reviewer_reward = BlockchainRewardCalculator.calculate_reviewer_reward(expected_student_reward, course)
    
    print(f"   Reward pool teorico: {theoretical_pool} TEO")
    print(f"   Reward studente teorico: {expected_student_reward} TEO")
    print(f"   Reward reviewer teorico: {expected_reviewer_reward} TEO")
    
    # Simula il processo
    submission = ExerciseSubmission.objects.create(
        exercise=exercise,
        student=student,
        content="Test content for reward calculation"
    )
    
    # Usa direttamente il manager per test controllato
    with transaction.atomic():
        try:
            blockchain_tx = BlockchainRewardManager.award_exercise_completion(submission)
            if blockchain_tx:
                print(f"   ✅ Reward assegnato con successo")
                print(f"   Amount effettivo: {blockchain_tx.amount} TEO")
                
                # Test reviewer reward
                review = ExerciseReview.objects.create(
                    submission=submission,
                    reviewer=reviewer,
                    score=8,
                    reviewed_at=timezone.now()
                )
                
                reviewer_tx = BlockchainRewardManager.award_review_completion(review)
                if reviewer_tx:
                    print(f"   ✅ Review reward assegnato")
                    print(f"   Reviewer amount: {reviewer_tx.amount} TEO")
                else:
                    print("   ⚠️ Review reward fallito")
            else:
                print("   ❌ Reward fallito")
                
        except Exception as e:
            print(f"   ❌ Errore durante reward: {str(e)}")


def test_idempotency():
    """
    Test che i reward non vengano duplicati
    """
    print("\n🔒 Testing reward idempotency...")
    
    student, reviewer, teacher, course, lesson, exercise = setup_test_data()
    
    submission = ExerciseSubmission.objects.create(
        exercise=exercise,
        student=student,
        content="Test idempotency",
        is_approved=True
    )
    
    # Primo tentativo
    initial_count = TeoCoinTransaction.objects.filter(user=student).count()
    tx1 = BlockchainRewardManager.award_exercise_completion(submission)
    after_first = TeoCoinTransaction.objects.filter(user=student).count()
    
    # Secondo tentativo (dovrebbe essere ignorato)
    tx2 = BlockchainRewardManager.award_exercise_completion(submission)
    after_second = TeoCoinTransaction.objects.filter(user=student).count()
    
    print(f"   Transazioni iniziali: {initial_count}")
    print(f"   Dopo primo reward: {after_first}")
    print(f"   Dopo secondo reward: {after_second}")
    print(f"   Idempotente: {after_first == after_second}")
    
    if tx1:
        print(f"   Primo TX riuscito: {tx1.amount} TEO")
    if tx2:
        print(f"   Secondo TX: {tx2.amount} TEO")
    else:
        print(f"   ✅ Secondo tentativo correttamente ignorato")


if __name__ == "__main__":
    print("🔗 BLOCKCHAIN REWARD INTEGRATION TEST 🔗\n")
    
    try:
        test_full_reward_flow()
        test_reward_calculation_accuracy() 
        test_idempotency()
        
        print("\n✅ Tutti i test completati!")
        print("\n📊 Statistiche finali:")
        print(f"   TEO Transactions: {TeoCoinTransaction.objects.count()}")
        print(f"   Blockchain Transactions: {BlockchainTransaction.objects.count()}")
        
    except Exception as e:
        print(f"\n❌ Errore durante i test: {str(e)}")
        import traceback
        traceback.print_exc()
