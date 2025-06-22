"""
Services App Models

This module contains database models used by the services layer.
"""

from django.db import models
from django.conf import settings


class TeoEarning(models.Model):
    """Track all TEO earnings for users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teo_earnings')
    earning_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=18, decimal_places=8)
    source_id = models.IntegerField(null=True, blank=True)  # course_id, exercise_id, etc.
    transaction_hash = models.CharField(max_length=66, null=True, blank=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'teo_earnings'
        indexes = [
            models.Index(fields=['user', 'earning_type']),
            models.Index(fields=['created_at']),
        ]
        
    def __str__(self):
        return f"{self.user.username} - {self.amount} TEO ({self.earning_type})"
