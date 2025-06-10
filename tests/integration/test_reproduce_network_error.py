#!/usr/bin/env python3

import os
import sys
import django

# Add the parent directory to the Python path
sys.path.append('/home/teo/Project/school/schoolplatform')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import ExerciseSubmission, ExerciseReview, Exercise, Lesson, Course
from rewards.models import BlockchainTransaction
from users.models import User
from django.utils import timezone
from django.test import RequestFactory
from courses.views.exercises import ReviewExerciseView
from django.contrib.auth.models import AnonymousUser
import logging
import random
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_fresh_test_scenario():
    """
    Create a completely fresh test scenario to simulate the user's issue
    """
    print("=== Creating Fresh Test Scenario ===")
    
    # Find course and exercise
    course = Course.objects.filter(is_approved=True).first()
    lesson = course.lessons.first() if course else None
    exercise = lesson.exercises.first() if lesson else None
    
    if not exercise:
        print("❌ No exercise found")
        return None, None
    
    # Find student enrolled in course
    student = course.students.first() if course else None
    if not student:
        print("❌ No student enrolled")
        return None, None
    
    print(f"Creating new submission for {student.username} on exercise {exercise.title}")
    
    # Create completely new submission
    submission = ExerciseSubmission.objects.create(
        exercise=exercise,
        student=student,
        content="Fresh test submission to reproduce network error",
        reviewed=False,  # Ensure it's not reviewed
        passed=False     # Set default value explicitly
    )
    
    # Assign 3 reviewers
    reviewers = list(User.objects.exclude(id=student.id)[:3])
    
    for reviewer in reviewers:
        ExerciseReview.objects.create(
            submission=submission,
            reviewer=reviewer,
            assigned_at=timezone.now(),
            score=None  # No score yet
        )
        submission.reviewers.add(reviewer)
    
    submission.save()
    
    print(f"✅ Created submission {submission.id} with {len(reviewers)} reviewers")
    for i, reviewer in enumerate(reviewers):
        print(f"  - Reviewer {i+1}: {reviewer.username}")
    
    return submission, reviewers

def simulate_api_review_calls(submission, reviewers):
    """
    Simulate the actual API calls that would be made from the frontend
    """
    print("\n=== Simulating API Review Calls ===")
    
    factory = RequestFactory()
    view = ReviewExerciseView()
    
    # Complete first two reviews
    for i, reviewer in enumerate(reviewers[:2]):
        print(f"Completing review {i+1} by {reviewer.username}")
        
        # Create request as if coming from frontend
        request = factory.post(f'/api/submissions/{submission.id}/review/', {
            'score': random.randint(6, 10)
        }, content_type='application/json')
        request.user = reviewer
        
        try:
            response = view.post(request, submission.id)
            print(f"  Response status: {response.status_code}")
            print(f"  Response data: {response.data}")
            
            # Check submission status
            submission.refresh_from_db()
            print(f"  Submission reviewed: {submission.reviewed}")
            
        except Exception as e:
            print(f"  ❌ Error in review {i+1}: {e}")
            import traceback
            traceback.print_exc()
    
    # Now complete the LAST review (this is where the issue happens)
    print(f"\n🎯 Completing FINAL review by {reviewers[2].username} (this should trigger rewards)")
    
    request = factory.post(f'/api/submissions/{submission.id}/review/', {
        'score': random.randint(6, 10)
    }, content_type='application/json')
    request.user = reviewers[2]
    
    try:
        # Check state before
        submission.refresh_from_db()
        print(f"Before final review - Submission reviewed: {submission.reviewed}")
        
        existing_rewards = BlockchainTransaction.objects.filter(
            transaction_type__in=['exercise_reward', 'review_reward'],
            related_object_id=str(submission.id)
        )
        print(f"Existing rewards before: {existing_rewards.count()}")
        
        # Make the final review call
        response = view.post(request, submission.id)
        
        print(f"✅ Final review response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        # Check state after
        submission.refresh_from_db()
        print(f"After final review - Submission reviewed: {submission.reviewed}")
        print(f"After final review - Submission passed: {submission.passed}")
        
        # Check rewards created
        all_rewards = BlockchainTransaction.objects.filter(
            transaction_type__in=['exercise_reward', 'review_reward'],
            related_object_id=str(submission.id)
        ).order_by('-created_at')
        
        print(f"Total rewards after: {all_rewards.count()}")
        
        for reward in all_rewards:
            print(f"  - {reward.transaction_type}: {reward.amount} TEO for {reward.user.username}")
            print(f"    Status: {reward.status}, Created: {reward.created_at}")
            if reward.status == 'failed':
                print(f"    Error: {reward.error_message}")
        
        # Check if all reviewers got rewards
        reviewer_rewards = all_rewards.filter(transaction_type='review_reward')
        print(f"\nReview rewards created: {reviewer_rewards.count()}/3 expected")
        
        for reviewer in reviewers:
            reviewer_reward = reviewer_rewards.filter(user=reviewer).first()
            if reviewer_reward:
                print(f"  ✅ {reviewer.username}: {reviewer_reward.amount} TEO ({reviewer_reward.status})")
            else:
                print(f"  ❌ {reviewer.username}: NO REWARD FOUND")
        
        return response.status_code == 201 and response.data.get('success')
        
    except Exception as e:
        print(f"❌ ERROR in final review: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Reproducing User's Network Error Issue")
    print("=" * 50)
    
    submission, reviewers = create_fresh_test_scenario()
    
    if not submission or not reviewers:
        print("❌ Failed to create test scenario")
        return
    
    success = simulate_api_review_calls(submission, reviewers)
    
    if success:
        print("\n✅ Test completed successfully - No network error reproduced")
    else:
        print("\n❌ Test failed - This might be the network error issue!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
