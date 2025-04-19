from django.db import models
from users.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('lesson_purchased', 'Acquisto Lezione'),
        ('exercise_graded', 'Esercizio Valutato'),
        ('course_completed', 'Corso Completato'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    read = models.BooleanField(default=False)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.get_notification_type_display()}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notifica"
        verbose_name_plural = "Notifiche"