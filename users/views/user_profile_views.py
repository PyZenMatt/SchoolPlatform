"""
User profile management views
"""
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from courses.models import CourseEnrollment
from authentication.serializers import RegisterSerializer
from users.models import User
from ..serializers import UserProfileSerializer


class RegisterView(generics.CreateAPIView):
    """User registration view"""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get user profile with course information"""
    user = request.user
    
    # NEW: Using UserService for business logic
    try:
        from services import user_service
        profile_data = user_service.get_user_profile_data(user)
        return Response(profile_data)
    except Exception as e:
        # Fallback to old logic if service fails
        return Response(
            {"error": f"Error retrieving profile: {str(e)}"}, 
            status=500
        )
    
    # OLD CODE (kept as backup) - Remove after testing
    # try:
    #     if user.role == 'student':
    #         courses = CourseEnrollment.objects.filter(student=user).values(
    #             'course__id', 'course__title', 'completed'
    #         )
    #     elif user.role == 'teacher':
    #         courses = user.created_courses.values('id', 'title', 'enrolled_students')
    #     else:
    #         courses = []
    # except Exception as e:
    #     return Response(
    #         {"error": f"Error retrieving courses: {e}"}, 
    #         status=500
    #     )
    # 
    # return Response({
    #     'username': user.username,
    #     'role': user.role,
    #     'courses': courses,
    #     'teo_coins': user.teo_coins
    # })


class UserProfileView(APIView):
    """User profile CRUD operations"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        """Get user profile details"""
        # NEW: Using UserService for business logic
        try:
            from services import user_service
            profile_data = user_service.get_user_profile_data(request.user)
            return Response(profile_data)
        except Exception as e:
            # Fallback to old logic if service fails
            return Response(
                {"error": f"Error retrieving profile: {str(e)}"}, 
                status=500
            )
        
        # OLD CODE (kept as backup) - Remove after testing
        # serializer = UserProfileSerializer(request.user)
        # return Response(serializer.data)

    def put(self, request):
        """Update user profile"""
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
