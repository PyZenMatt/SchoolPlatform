from rest_framework import serializers
from courses.models import Lesson, Exercise
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    related_object = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'message', 'notification_type', 'read', 'created_at', 'related_object']
        ordering = ['-created_at']

    def get_related_object(self, obj):
        try:
            if obj.notification_type == 'exercise_graded':
                exercise = Exercise.objects.get(id=obj.related_object_id)
                return {
                    'id': exercise.id,
                    'score': exercise.score,
                    'lesson_title': exercise.lesson.title
                }
            elif obj.notification_type == 'lesson_purchased':
                lesson = Lesson.objects.get(id=obj.related_object_id)
                return {
                    'id': lesson.id,
                    'title': lesson.title,
                    'price': lesson.price
                }
        except Exception as e:
            return None
        
