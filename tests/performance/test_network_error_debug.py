#!/usr/bin/env python3

import os
import sys
import django

# Add the parent directory to the Python path
sys.path.append('/home/teo/Project/school/schoolplatform')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import ExerciseSubmission, ExerciseReview
from rewards.models import BlockchainTransaction
from users.models import User
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_network_error_issue():
    """
    Test to reproduce and check the network error issue
    """
    print("=== Testing Network Error Issue ===")
    
    # Find a submission that has reviews but is not yet reviewed
    submissions = ExerciseSubmission.objects.filter(reviewed=False)
    print(f"Found {submissions.count()} unreviewed submissions")
    
    if submissions.count() == 0:
        print("No unreviewed submissions found. Creating test data...")
        return
    
    submission = submissions.first()
    print(f"Testing with submission {submission.id} by {submission.student.username}")
    
    # Check existing reviews
    reviews = ExerciseReview.objects.filter(submission=submission)
    print(f"Reviews for this submission: {reviews.count()}")
    
    for review in reviews:
        print(f"  - Reviewer: {review.reviewer.username}, Score: {review.score}")
    
    # Check if any reviews are missing scores
    reviews_without_scores = reviews.filter(score__isnull=True)
    print(f"Reviews without scores: {reviews_without_scores.count()}")
    
    if reviews_without_scores.count() == 0:
        print("All reviews have scores - submission should be marked as reviewed")
        return
    
    # Simulate completing the last review
    last_review = reviews_without_scores.first()
    print(f"Simulating completion of review by {last_review.reviewer.username}")
    
    # Check existing reward transactions
    existing_rewards = BlockchainTransaction.objects.filter(
        transaction_type__in=['exercise_reward', 'review_reward'],
        related_object_id=str(submission.id)
    )
    print(f"Existing reward transactions: {existing_rewards.count()}")
    
    for reward in existing_rewards:
        print(f"  - {reward.transaction_type}: {reward.amount} TEO for {reward.user.username} - Status: {reward.status}")
    
    return submission, last_review

def check_recent_failed_transactions():
    """
    Check for recent failed reward transactions
    """
    print("\n=== Checking Recent Failed Transactions ===")
    
    failed_rewards = BlockchainTransaction.objects.filter(
        transaction_type__in=['exercise_reward', 'review_reward'],
        status='failed'
    ).order_by('-created_at')[:10]
    
    print(f"Recent failed reward transactions: {failed_rewards.count()}")
    
    for reward in failed_rewards:
        print(f"  - {reward.transaction_type}: {reward.amount} TEO for {reward.user.username}")
        print(f"    Error: {reward.error_message}")
        print(f"    Created: {reward.created_at}")
        print()

def check_pending_transactions():
    """
    Check for pending reward transactions
    """
    print("\n=== Checking Pending Transactions ===")
    
    pending_rewards = BlockchainTransaction.objects.filter(
        transaction_type__in=['exercise_reward', 'review_reward'],
        status='pending'
    ).order_by('-created_at')
    
    print(f"Pending reward transactions: {pending_rewards.count()}")
    
    for reward in pending_rewards:
        print(f"  - {reward.transaction_type}: {reward.amount} TEO for {reward.user.username}")
        print(f"    Created: {reward.created_at}")

if __name__ == "__main__":
    try:
        test_network_error_issue()
        check_recent_failed_transactions()
        check_pending_transactions()
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
