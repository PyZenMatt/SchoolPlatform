"""
Notification Service - Business Logic for Notification Management

Handles all notification-related operations including creation, retrieval,
marking as read, and notification delivery workflows.
"""

from typing import Dict, List, Optional, Any
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q

from notifications.models import Notification
from services.base import TransactionalService
from services.exceptions import (
    TeoArtServiceException,
    UserNotFoundError,
)

User = get_user_model()


class NotificationService(TransactionalService):
    """
    Service for managing notification operations.
    
    Handles notification creation, retrieval, marking as read,
    and bulk notification operations.
    """
    
    def create_notification(
        self, 
        user_id: int, 
        message: str, 
        notification_type: str,
        related_object_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new notification for a user.
        
        Args:
            user_id: ID of the user to notify
            message: Notification message
            notification_type: Type of notification (must be in NOTIFICATION_TYPES)
            related_object_id: Optional ID of related object
            
        Returns:
            Dict containing notification data
            
        Raises:
            UserNotFoundError: If user not found
            TeoArtServiceException: If notification creation fails
        """
        def _create_operation():
            # Validate user exists
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                raise UserNotFoundError(user_id=user_id)
            
            # Validate notification type
            valid_types = [choice[0] for choice in Notification.NOTIFICATION_TYPES]
            if notification_type not in valid_types:
                raise TeoArtServiceException(
                    f"Invalid notification type: {notification_type}. Must be one of: {valid_types}"
                )
            
            # Create notification
            notification = Notification.objects.create(
                user=user,
                message=message,
                notification_type=notification_type,
                related_object_id=related_object_id
            )
            
            self.log_info(f"Created notification {notification.id} for user {user_id}")
            
            return {
                'notification_id': notification.id,
                'user_id': user.id,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'related_object_id': notification.related_object_id,
                'created_at': notification.created_at.isoformat(),
                'read': notification.read,
            }
        
        try:
            return self.execute_in_transaction(_create_operation)
        except (UserNotFoundError, TeoArtServiceException):
            raise
        except Exception as e:
            self.log_error(f"Error creating notification for user {user_id}: {str(e)}")
            raise TeoArtServiceException(f"Error creating notification: {str(e)}")
    
    def get_user_notifications(
        self, 
        user_id: int, 
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get notifications for a user.
        
        Args:
            user_id: ID of the user
            unread_only: If True, return only unread notifications
            notification_type: Filter by notification type
            limit: Maximum number of notifications to return
            
        Returns:
            List of notification data
        """
        try:
            self.log_info(f"Retrieving notifications for user {user_id}")
            
            # Build query
            queryset = Notification.objects.filter(user_id=user_id)
            
            if unread_only:
                queryset = queryset.filter(read=False)
            
            if notification_type:
                queryset = queryset.filter(notification_type=notification_type)
            
            # Order by newest first and apply limit
            queryset = queryset.order_by('-created_at')
            if limit:
                queryset = queryset[:limit]
            
            notifications_data = []
            for notification in queryset:
                notifications_data.append({
                    'id': notification.id,
                    'message': notification.message,
                    'notification_type': notification.notification_type,
                    'read': notification.read,
                    'related_object_id': notification.related_object_id,
                    'created_at': notification.created_at.isoformat(),
                })
            
            self.log_info(f"Retrieved {len(notifications_data)} notifications for user {user_id}")
            return notifications_data
            
        except Exception as e:
            self.log_error(f"Error retrieving notifications for user {user_id}: {str(e)}")
            raise TeoArtServiceException(f"Error retrieving notifications: {str(e)}")
    
    def mark_notification_as_read(self, notification_id: int, user_id: int) -> Dict[str, Any]:
        """
        Mark a notification as read.
        
        Args:
            notification_id: ID of the notification
            user_id: ID of the user (for security check)
            
        Returns:
            Dict containing updated notification data
            
        Raises:
            TeoArtServiceException: If notification not found or doesn't belong to user
        """
        def _mark_read_operation():
            try:
                notification = Notification.objects.get(
                    id=notification_id,
                    user_id=user_id
                )
            except Notification.DoesNotExist:
                raise TeoArtServiceException(
                    f"Notification {notification_id} not found or doesn't belong to user {user_id}"
                )
            
            if not notification.read:
                notification.read = True
                notification.save(update_fields=['read'])
                self.log_info(f"Marked notification {notification_id} as read for user {user_id}")
            
            return {
                'notification_id': notification.id,
                'read': notification.read,
                'updated_at': timezone.now().isoformat(),
            }
        
        try:
            return self.execute_in_transaction(_mark_read_operation)
        except TeoArtServiceException:
            raise
        except Exception as e:
            self.log_error(f"Error marking notification {notification_id} as read: {str(e)}")
            raise TeoArtServiceException(f"Error marking notification as read: {str(e)}")
    
    def mark_all_notifications_as_read(self, user_id: int) -> Dict[str, Any]:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict containing count of updated notifications
        """
        def _mark_all_read_operation():
            updated_count = Notification.objects.filter(
                user_id=user_id,
                read=False
            ).update(read=True)
            
            self.log_info(f"Marked {updated_count} notifications as read for user {user_id}")
            
            return {
                'user_id': user_id,
                'updated_count': updated_count,
                'updated_at': timezone.now().isoformat(),
            }
        
        try:
            return self.execute_in_transaction(_mark_all_read_operation)
        except Exception as e:
            self.log_error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
            raise TeoArtServiceException(f"Error marking all notifications as read: {str(e)}")
    
    def get_unread_count(self, user_id: int) -> Dict[str, Any]:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict containing unread count
        """
        try:
            self.log_info(f"Getting unread count for user {user_id}")
            
            unread_count = Notification.objects.filter(
                user_id=user_id,
                read=False
            ).count()
            
            return {
                'user_id': user_id,
                'unread_count': unread_count,
            }
            
        except Exception as e:
            self.log_error(f"Error getting unread count for user {user_id}: {str(e)}")
            raise TeoArtServiceException(f"Error getting unread count: {str(e)}")
    
    def delete_notification(self, notification_id: int, user_id: int) -> Dict[str, Any]:
        """
        Delete a notification.
        
        Args:
            notification_id: ID of the notification
            user_id: ID of the user (for security check)
            
        Returns:
            Dict containing deletion result
            
        Raises:
            TeoArtServiceException: If notification not found or doesn't belong to user
        """
        def _delete_operation():
            try:
                notification = Notification.objects.get(
                    id=notification_id,
                    user_id=user_id
                )
            except Notification.DoesNotExist:
                raise TeoArtServiceException(
                    f"Notification {notification_id} not found or doesn't belong to user {user_id}"
                )
            
            notification.delete()
            self.log_info(f"Deleted notification {notification_id} for user {user_id}")
            
            return {
                'notification_id': notification_id,
                'user_id': user_id,
                'deleted': True,
                'deleted_at': timezone.now().isoformat(),
            }
        
        try:
            return self.execute_in_transaction(_delete_operation)
        except TeoArtServiceException:
            raise
        except Exception as e:
            self.log_error(f"Error deleting notification {notification_id}: {str(e)}")
            raise TeoArtServiceException(f"Error deleting notification: {str(e)}")


# Singleton instance for easy access
notification_service = NotificationService()
