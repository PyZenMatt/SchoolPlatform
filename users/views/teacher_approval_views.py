"""
Teacher approval management views
"""
from rest_framework import generics
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from notifications.models import Notification
from users.models import User
from users.serializers import UserSerializer
from core.api_standards import StandardizedAPIView


class PendingTeachersView(ListAPIView, StandardizedAPIView):
    """List teachers pending approval"""
    queryset = User.objects.filter(role='teacher', is_approved=False)
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]


class ApproveTeacherView(APIView, StandardizedAPIView):
    """Approve a teacher application"""
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            teacher = get_object_or_404(User, id=user_id, role='teacher')
            teacher.is_approved = True
            teacher.save()
            
            # Create approval notification
            Notification.objects.create(
                user=teacher,
                message="Il tuo profilo docente è stato approvato!",
                notification_type='teacher_approved',
                related_object_id=teacher.pk
            )
            
            return self.handle_success(
                data={
                    "teacher_id": teacher.pk,
                    "teacher_email": teacher.email
                },
                message=f"Teacher {teacher.email} has been approved."
            )
            
        except Exception as e:
            return self.handle_server_error(e)


class RejectTeacherView(APIView, StandardizedAPIView):
    """Reject a teacher application"""
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        try:
            teacher = get_object_or_404(User, id=user_id, role='teacher')
            
            # Create rejection notification before deletion
            Notification.objects.create(
                user=teacher,
                message="Il tuo profilo docente è stato rifiutato.",
                notification_type='teacher_rejected',
                related_object_id=teacher.pk
            )
            
            teacher_email = teacher.email  # Store before deletion
            teacher.delete()
            
            return self.handle_success(
                data={
                    "teacher_email": teacher_email
                },
                message=f"Teacher {teacher_email} has been rejected and removed."
            )
            
        except Exception as e:
            return self.handle_server_error(e)
