from django.db import models
from users.models import User

class TeoCoinTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('earned', 'Guadagnati'),
        ('spent', 'Spesi'),
        ('transferred', 'Trasferiti'),
        ('lesson_purchase', 'Acquisto Lezione'),
        ('lesson_earned', 'Guadagno Lezione'),
        ('exercise_reward', 'Ricompensa Esercizio'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.get_transaction_type_display()} - {self.amount}"

    class Meta:
        verbose_name = "Transazione TeoCoin"
        verbose_name_plural = "Transazioni TeoCoin"