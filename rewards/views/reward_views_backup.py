from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
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
                return Response({
                    "message": "Lesson completion reward processed successfully",
                    "success": True
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "No reward processed - budget exhausted or already rewarded",
                    "success": False
                }, status=status.HTTP_200_OK)
                
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            return Response({"error": "Invalid user, lesson, or course ID"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error processing lesson completion reward: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_course_completion_check(request):
    """Check and trigger course completion reward if applicable"""
    try:
        course_id = request.data.get('course_id')
        user_id = request.data.get('user_id', request.user.id)
        
        if not course_id:
            return Response({"error": "course_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Only allow users to trigger rewards for themselves unless admin
        if user_id != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            from courses.models import Course
            from users.models import User
            
            user = User.objects.get(id=user_id)
            course = Course.objects.get(id=course_id)
            
            reward_system = AutomatedRewardSystem()
            result = reward_system.check_and_reward_course_completion(user, course)
            
            if result:
                return Response({
                    "message": "Course completion reward processed successfully",
                    "course_completed": True,
                    "success": True
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "Course not yet completed or already rewarded",
                    "course_completed": False,
                    "success": False
                }, status=status.HTTP_200_OK)
                
        except (User.DoesNotExist, Course.DoesNotExist) as e:
            return Response({"error": "Invalid user or course ID"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error processing course completion check: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def manual_reward_distribution(request):
    """Manual reward distribution by admin"""
    try:
        user_id = request.data.get('user_id')
        amount = request.data.get('amount')
        achievement_type = request.data.get('achievement_type', 'manual_reward')
        course_id = request.data.get('course_id')
        
        if not user_id or not amount:
            return Response({"error": "user_id and amount are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = int(amount)
            if amount <= 0:
                return Response({"error": "Amount must be positive"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from users.models import User
            from courses.models import Course
            
            user = User.objects.get(id=user_id)
            course = None
            if course_id:
                course = Course.objects.get(id=course_id)
            
            # Add TeoCoin directly for manual rewards
            user.add_teo_coins(
                amount,
                transaction_type='manual_reward',
                related_object_id=course_id
            )
            
            return Response({
                "message": "Manual reward distributed successfully",
                "tokens_earned": amount,
                "user_id": user_id,
                "new_balance": user.teo_coins
            }, status=status.HTTP_200_OK)
                
        except (User.DoesNotExist, Course.DoesNotExist) as e:
            return Response({"error": "Invalid user or course ID"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error processing manual reward distribution: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_achievement_reward(request):
    """Award achievement-based rewards"""
    try:
        achievement_type = request.data.get('achievement_type')
        user_id = request.data.get('user_id', request.user.id)
        course_id = request.data.get('course_id')
        
        if not achievement_type:
            return Response({"error": "achievement_type is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Only allow users to trigger rewards for themselves unless admin
        if user_id != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            from users.models import User
            from courses.models import Course
            
            user = User.objects.get(id=user_id)
            course = None
            if course_id:
                course = Course.objects.get(id=course_id)
            
            reward_system = AutomatedRewardSystem()
            reward_system.award_achievement(user, achievement_type, course)
            
            return Response({
                "message": f"Achievement '{achievement_type}' reward processed successfully",
                "achievement_type": achievement_type,
                "success": True
            }, status=status.HTTP_200_OK)
                
        except (User.DoesNotExist, Course.DoesNotExist) as e:
            return Response({"error": "Invalid user or course ID"}, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error processing achievement reward: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reward_summary(request):
    """Get user's reward summary"""
    try:
        user_id = request.GET.get('user_id', request.user.id)
        course_id = request.GET.get('course_id')
        
        # Only allow users to view their own summary unless admin
        if int(user_id) != request.user.id and not request.user.is_staff:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            from users.models import User
            from courses.models import Course
            
            user = User.objects.get(id=user_id)
            course = None
            if course_id:
                course = Course.objects.get(id=course_id)
            
            reward_system = AutomatedRewardSystem()
            summary = reward_system.get_student_reward_summary(user, course)
            
            return Response({
                "reward_summary": summary,
                "user_id": user_id,
                "course_id": course_id
            }, status=status.HTTP_200_OK)
                
        except (User.DoesNotExist, Course.DoesNotExist) as e:
            return Response({"error": "Invalid user or course ID"}, status=status.HTTP_400_BAD_REQUEST)
        
    except Exception as e:
        logger.error(f"Error fetching reward summary: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bulk_reward_distribution(request):
    """Bulk reward distribution for multiple users"""
    try:
        user_ids = request.data.get('user_ids', [])
        amount = request.data.get('amount')
        transaction_type = request.data.get('transaction_type', 'bulk_reward')
        
        if not user_ids or not amount:
            return Response({"error": "user_ids and amount are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            amount = int(amount)
            if amount <= 0:
                return Response({"error": "Amount must be positive"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST)
        
        from users.models import User
        
        results = []
        successful_distributions = 0
        
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                user.add_teo_coins(amount, transaction_type=transaction_type)
                successful_distributions += 1
                results.append({
                    "user_id": user_id,
                    "success": True,
                    "message": "Reward distributed successfully",
                    "tokens_earned": amount
                })
            except User.DoesNotExist:
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "message": "User not found",
                    "tokens_earned": 0
                })
            except Exception as e:
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "message": str(e),
                    "tokens_earned": 0
                })
        
        return Response({
            "message": f"Bulk reward distribution completed. {successful_distributions}/{len(user_ids)} successful",
            "results": results,
            "total_users": len(user_ids),
            "successful_distributions": successful_distributions
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error processing bulk reward distribution: {str(e)}")
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
