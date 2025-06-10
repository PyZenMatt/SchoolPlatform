# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notification
from courses.models import Exercise

@receiver(post_save, sender=Exercise)
def handle_exercise_graded(sender, instance, **kwargs):
    """
    Crea una notifica automaticamente quando un esercizio viene valutato
    """
    if instance.status == 'reviewed' and instance.score is not None:
        Notification.objects.create(
            user=instance.student,
            message=f"Esercizio '{instance.lesson.title}' valutato: {instance.score}/100",
            notification_type='exercise_graded',
            related_object_id=instance.id
        )