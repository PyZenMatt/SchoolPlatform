#!/usr/bin/env python3
"""
Script di test per il sistema di reward blockchain
Simula il processo di approvazione di un esercizio e reward del reviewer
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
from courses.models import Course, Lesson, Exercise, ExerciseSubmission, ExerciseReview
from rewards.models import TeoCoinTransaction, BlockchainTransaction
from rewards.blockchain_rewards import BlockchainRewardCalculator, BlockchainRewardManager

User = get_user_model()


def test_reward_calculation():
    """
    Test calcolo e distribuzione reward
    """
    print("=== TEST CALCOLO REWARD ===")
    
    # Simula un corso da 30€
    course_price = Decimal('30.00')
    exercise_count = 3
    
    print(f"Corso: {course_price}€, Esercizi: {exercise_count}")
    
    # Crea un corso mock per il test
    class MockCourse:
        def __init__(self, price):
            self.price = price
    
    course = MockCourse(course_price)
    
    # Calcola pool reward
    reward_pool = BlockchainRewardCalculator.calculate_course_reward_pool(course)
    print(f"Pool reward totale: {reward_pool} TEO")
    
    # Calcola distribuzione
    exercise_rewards = BlockchainRewardCalculator.distribute_exercise_rewards(course, exercise_count)
    print(f"Distribuzione esercizi: {exercise_rewards}")
    print(f"Somma distribuzione: {sum(exercise_rewards)} TEO")
    
    # Test reward reviewer
    for i, exercise_reward in enumerate(exercise_rewards):
        reviewer_reward = BlockchainRewardCalculator.calculate_reviewer_reward(exercise_reward)
        print(f"Esercizio {i+1}: {exercise_reward} TEO -> Reviewer: {reviewer_reward} TEO")
    
    print()


def test_multiple_distributions():
    """
    Test multiple distribuzioni per verificare la variabilità
    """
    print("=== TEST DISTRIBUZIONI MULTIPLE ===")
    
    class MockCourse:
        def __init__(self, price):
            self.price = price
    
    course = MockCourse(Decimal('30.00'))
    exercise_count = 3
    
    print("5 distribuzioni diverse per stesso corso:")
    for i in range(5):
        rewards = BlockchainRewardCalculator.distribute_exercise_rewards(course, exercise_count)
        pool = sum(rewards)
        print(f"  {i+1}: {rewards} (totale: {pool} TEO)")
    
    print()


def test_edge_cases():
    """
    Test casi limite
    """
    print("=== TEST CASI LIMITE ===")
    
    class MockCourse:
        def __init__(self, price):
            self.price = price
    
    # Corso molto economico
    cheap_course = MockCourse(Decimal('1.00'))
    rewards = BlockchainRewardCalculator.distribute_exercise_rewards(cheap_course, 3)
    print(f"Corso 1€, 3 esercizi: {rewards}")
    
    # Corso molto caro
    expensive_course = MockCourse(Decimal('500.00'))
    rewards = BlockchainRewardCalculator.distribute_exercise_rewards(expensive_course, 2)
    print(f"Corso 500€, 2 esercizi: {rewards}")
    
    # Un solo esercizio
    single_exercise = BlockchainRewardCalculator.distribute_exercise_rewards(cheap_course, 1)
    print(f"Corso 1€, 1 esercizio: {single_exercise}")
    
    # Nessun esercizio
    no_exercise = BlockchainRewardCalculator.distribute_exercise_rewards(cheap_course, 0)
    print(f"Corso 1€, 0 esercizi: {no_exercise}")
    
    print()


def test_percentage_bounds():
    """
    Test che le percentuali siano nei limiti corretti
    """
    print("=== TEST LIMITI PERCENTUALI ===")
    
    class MockCourse:
        def __init__(self, price):
            self.price = price
    
    course = MockCourse(Decimal('100.00'))  # Corso da 100€ per semplificare i calcoli
    
    # Test 10 volte per verificare i limiti
    pools = []
    for _ in range(10):
        pool = BlockchainRewardCalculator.calculate_course_reward_pool(course)
        pools.append(pool)
    
    min_pool = min(pools)
    max_pool = max(pools)
    
    min_percentage = (min_pool / course.price) * 100
    max_percentage = (max_pool / course.price) * 100
    
    print(f"Range pool: {min_pool} - {max_pool} TEO")
    print(f"Range percentuali: {min_percentage:.1f}% - {max_percentage:.1f}%")
    print(f"Entro limiti (3%-10%): {3 <= min_percentage and max_percentage <= 10}")
    
    print()


if __name__ == "__main__":
    print("🧪 TESTING BLOCKCHAIN REWARD SYSTEM 🧪\n")
    
    test_reward_calculation()
    test_multiple_distributions() 
    test_edge_cases()
    test_percentage_bounds()
    
    print("✅ Test completati!")
    print("\nEsempio pratico:")
    print("- Corso da 30€ con 3 esercizi")
    print("- Pool reward: 3% - 10% = 0.9€ - 3€ in TEO")
    print("- Distribuzione casuale ma bilanciata tra esercizi")
    print("- Reviewer: 5% del premio di ogni esercizio")
