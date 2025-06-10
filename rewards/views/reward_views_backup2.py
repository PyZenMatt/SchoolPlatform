from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from courses.models import Lesson, Course
from users.models import User
from ..automation import AutomatedRewardSystem
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_lesson_completion_reward(request):
    """Trigger reward for lesson completion"""
    try:
        lesson_id = request.data.get('lesson_id')
        course_id = request.data.get('course_id')
        user_id = request.data.get('user_id', request.user.id)
        
        if not lesson_id:
            return Response({"error": "lesson_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Only allow users to trigger rewards for themselves unless admin
        if user_id != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = get_object_or_404(User, id=user_id)
            lesson = get_object_or_404(Lesson, id=lesson_id)
            
            if course_id:
                course = get_object_or_404(Course, id=course_id)
            else:
                course = lesson.course
            
            if not course:
                return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
            
            reward_system = AutomatedRewardSystem()
            result = reward_system.reward_lesson_completion(user, lesson, course)
            
            if result:
                # Calculate the reward amount that was given
                reward_amount = reward_system.calculate_lesson_reward(course, lesson)
                return Response({
                    "message": "Lesson completion reward processed successfully",
                    "reward_amount": reward_amount,
                    "success": True
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "No reward processed - budget exhausted or already rewarded",
                    "success": False
                }, status=status.HTTP_200_OK)
                
        except ObjectDoesNotExist:
            return Response({"error": "Invalid user, lesson, or course ID"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error processing lesson completion reward: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_course_completion_check(request):
    """Check and trigger course completion rewards"""
    try:
        course_id = request.data.get('course_id')
        user_id = request.data.get('user_id', request.user.id)
        
        if not course_id:
            return Response({"error": "course_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Only allow users to trigger rewards for themselves unless admin
        if user_id != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = get_object_or_404(User, id=user_id)
            course = get_object_or_404(Course, id=course_id)
            
            reward_system = AutomatedRewardSystem()
            result = reward_system.check_and_reward_course_completion(user, course)
            
            if result:
                # Calculate the bonus amount that was given
                bonus_amount = reward_system.calculate_course_completion_bonus(course)
                return Response({
                    "message": "Course completion reward processed successfully",
                    "reward_amount": bonus_amount,
                    "achievement_unlocked": True,
                    "success": True
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "Course not completed or already rewarded",
                    "success": False
                }, status=status.HTTP_200_OK)
                
        except ObjectDoesNotExist:
            return Response({"error": "Invalid user or course ID"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error processing course completion check: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_achievement_reward(request):
    """Trigger achievement reward manually"""
    try:
        achievement_type = request.data.get('achievement_type')
        course_id = request.data.get('course_id')
        user_id = request.data.get('user_id', request.user.id)
        
        if not achievement_type:
            return Response({"error": "achievement_type is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        # Only allow users to trigger rewards for themselves unless admin
        if user_id != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Validate achievement type
            from core.constants import ACHIEVEMENT_TYPES
            if achievement_type not in ACHIEVEMENT_TYPES:
                return Response({"error": "Invalid achievement type"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid achievement type"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = get_object_or_404(User, id=user_id)
            course = None
            
            if course_id:
                course = get_object_or_404(Course, id=course_id)
            
            reward_system = AutomatedRewardSystem()
            if course:
                reward_system.award_achievement(user, achievement_type, course)
            else:
                # Handle achievements that don't require a course
                reward_system.award_achievement(user, achievement_type, None)
            
            return Response({
                "message": f"Achievement '{achievement_type}' reward processed successfully",
                "success": True
            }, status=status.HTTP_200_OK)
                
        except ObjectDoesNotExist:
            return Response({"error": "Invalid user or course ID"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error processing achievement reward: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reward_summary(request):
    """Get reward summary for a user and course"""
    try:
        course_id = request.query_params.get('course_id')
        user_id = request.query_params.get('user_id', request.user.id)
        
        # Only allow users to get summaries for themselves unless admin
        if int(user_id) != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = get_object_or_404(User, id=user_id)
            course = None
            
            if course_id:
                course = get_object_or_404(Course, id=course_id)
            
            reward_system = AutomatedRewardSystem()
            if course:
                summary = reward_system.get_student_reward_summary(user, course)
            else:
                # Get overall summary without course filter
                summary = reward_system.get_student_reward_summary(user, None)
            
            return Response({
                "message": "Reward summary retrieved successfully",
                "reward_summary": summary,
                "success": True
            }, status=status.HTTP_200_OK)
                
        except ObjectDoesNotExist:
            return Response({"error": "Invalid user or course ID"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error retrieving reward summary: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_process_rewards(request):
    """Bulk process rewards for multiple users (admin only)"""
    try:
        user_ids = request.data.get('user_ids', [])
        reward_type = request.data.get('reward_type')
        
        if not user_ids or not reward_type:
            return Response({
                "error": "user_ids and reward_type are required"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from core.constants import ACHIEVEMENT_TYPES
            if reward_type not in ACHIEVEMENT_TYPES:
                return Response({"error": "Invalid reward type"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid reward type"}, status=status.HTTP_400_BAD_REQUEST)
        
        results = []
        reward_system = AutomatedRewardSystem()
        
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                # Process the reward based on type
                reward_system.award_achievement(user, reward_type, None)
                results.append({
                    "user_id": user_id,
                    "success": True,
                    "message": f"Reward '{reward_type}' processed successfully"
                })
            except User.DoesNotExist:
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "message": "User not found"
                })
            except Exception as e:
                logger.error(f"Error processing reward for user {user_id}: {str(e)}")
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "message": f"Error: {str(e)}"
                })
        
        return Response({
            "message": "Bulk reward processing completed",
            "results": results,
            "success": True
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in bulk reward processing: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
