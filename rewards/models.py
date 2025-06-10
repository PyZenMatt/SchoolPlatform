from django.db import models
from users.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class BlockchainTransaction(models.Model):
    """
    Modello per tracciare transazioni blockchain (mint, transfer, burn)
    """
    TRANSACTION_TYPES = (
        ('mint', 'Mint - Crea nuovi token'),
        ('transfer', 'Transfer - Trasferimento tra wallet'),
        ('burn', 'Burn - Distruzione token'),
        ('course_purchase', 'Course Purchase - Acquisto corso'),
        ('course_earned', 'Course Earned - Guadagno insegnante'),
        ('reward', 'Reward - Premio per attività'),
        ('exercise_reward', 'Exercise Reward - Premio per esercizio completato'),
        ('review_reward', 'Review Reward - Premio per review completata'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'In Attesa'),
        ('confirmed', 'Confermata'),
        ('completed', 'Completata'),
        ('failed', 'Fallita'),
    )
    
    # Dati transazione
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='blockchain_transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=18, decimal_places=8)  # Supporta decimali come blockchain
    
    # Dati blockchain
    from_address = models.CharField(max_length=42, blank=True, null=True)
    to_address = models.CharField(max_length=42, blank=True, null=True)
    tx_hash = models.CharField(max_length=66, unique=True, blank=True, null=True)
    transaction_hash = models.CharField(max_length=100, blank=True, null=True)  # Additional transaction identifier
    block_number = models.PositiveIntegerField(blank=True, null=True)
    gas_used = models.PositiveIntegerField(blank=True, null=True)
    
    # Additional metadata for transactions
    related_object_id = models.CharField(max_length=100, blank=True, null=True)  # Course ID or other object ID
    notes = models.TextField(blank=True, null=True)  # Additional notes
    
    # Status e metadata
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} TEO - {self.status}"
    
    @property
    def explorer_url(self):
        """Link all'explorer Polygon per visualizzare la transazione"""
        if self.tx_hash:
            return f"https://amoy.polygonscan.com/tx/{self.tx_hash}"
        return None
    
    class Meta:
        verbose_name = "Transazione Blockchain"
        verbose_name_plural = "Transazioni Blockchain"
        ordering = ['-created_at']


class TokenBalance(models.Model):
    """
    Cache del balance blockchain per performance
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='token_balance'
    )
    balance = models.DecimalField(
        max_digits=18, 
        decimal_places=8, 
        default=Decimal('0')
    )
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} - {self.balance} TEO"
    
    def is_stale(self, minutes=5):
        """Controlla se il balance è scaduto (default 5 minuti)"""
        return timezone.now() - self.last_updated > timedelta(minutes=minutes)
    
    class Meta:
        verbose_name = "Balance Token"
        verbose_name_plural = "Balance Token"