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
        ('discount_applied', 'Discount Applied - Sconto TeoCoin applicato'),
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


class TeoCoinEscrow(models.Model):
    """
    Holds TeoCoin until teacher accepts/rejects discount
    Layer 2 escrow system for teacher choice implementation
    """
    ESCROW_STATUS = (
        ('pending', 'Pending Teacher Decision'),
        ('accepted', 'Teacher Accepted - TeoCoin Released'),
        ('rejected', 'Teacher Rejected - TeoCoin Returned'),
        ('expired', 'Expired - Auto Returned to Platform'),
    )
    
    # Core escrow data
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='teocoin_escrows_as_student'
    )
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='teocoin_escrows_as_teacher'
    )
    course = models.ForeignKey(
        'courses.Course', 
        on_delete=models.CASCADE,
        related_name='teocoin_escrows'
    )
    
    # Financial details
    teocoin_amount = models.DecimalField(
        max_digits=18, 
        decimal_places=8,
        help_text="Amount of TeoCoin held in escrow"
    )
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Percentage discount applied (e.g., 10.00 for 10%)"
    )
    discount_euro_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Euro amount of discount"
    )
    original_course_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Original course price in EUR"
    )
    
    # Teacher compensation options
    standard_euro_commission = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="EUR commission if teacher rejects TeoCoin"
    )
    reduced_euro_commission = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="EUR commission if teacher accepts TeoCoin"
    )
    
    # Blockchain details
    escrow_tx_hash = models.CharField(
        max_length=66, 
        null=True, 
        blank=True,
        help_text="Transaction hash for TeoCoin transfer to escrow"
    )
    release_tx_hash = models.CharField(
        max_length=66, 
        null=True, 
        blank=True,
        help_text="Transaction hash for TeoCoin release from escrow"
    )
    
    # Status and timing
    status = models.CharField(
        max_length=20, 
        choices=ESCROW_STATUS, 
        default='pending'
    )
    expires_at = models.DateTimeField(
        help_text="Auto-reject escrow after this datetime"
    )
    
    # Decision tracking
    teacher_decision_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When teacher made their decision"
    )
    teacher_decision_notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Optional notes from teacher about their decision"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "TeoCoin Escrow"
        verbose_name_plural = "TeoCoin Escrows"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['teacher', 'status']),
            models.Index(fields=['student', 'created_at']),
        ]
        
    def __str__(self):
        return f"Escrow: {self.teocoin_amount} TEO for {self.course.title} ({self.status})"
    
    @property
    def is_expired(self):
        """Check if escrow has expired and is still pending"""
        return timezone.now() > self.expires_at and self.status == 'pending'
    
    @property
    def time_remaining(self):
        """Get time remaining before expiration (None if not pending)"""
        if self.status != 'pending':
            return None
        remaining = self.expires_at - timezone.now()
        return remaining if remaining.total_seconds() > 0 else None
    
    @property
    def days_remaining(self):
        """Get days remaining before expiration"""
        time_left = self.time_remaining
        if time_left is None:
            return None
        return time_left.days
    
    def can_teacher_decide(self):
        """Check if teacher can still make a decision"""
        return self.status == 'pending' and not self.is_expired
    
    def get_teacher_earnings_comparison(self):
        """Compare teacher earnings for accept vs reject"""
        return {
            'accept': {
                'eur': float(self.reduced_euro_commission),
                'teo': float(self.teocoin_amount),
                'description': f"€{self.reduced_euro_commission} + {self.teocoin_amount} TEO"
            },
            'reject': {
                'eur': float(self.standard_euro_commission),
                'teo': 0,
                'description': f"€{self.standard_euro_commission} (standard commission)"
            }
        }