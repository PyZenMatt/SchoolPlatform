from django.db import models
from django.conf import settings
from django.utils import timezone


class UserWallet(models.Model):
    """
    User wallet model for managing blockchain wallet information.
    
    WARNING: This model stores private keys in plain text which is NOT secure
    for production use. Private keys should be encrypted or stored using a
    secure key management system (HSM, KMS, etc.).
    
    For production deployment, consider:
    - Using encrypted fields for private keys
    - Implementing HSM/KMS integration
    - Using deterministic wallet generation
    - Implementing proper key rotation
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='blockchain_wallet',
        help_text="User associated with this wallet"
    )
    address = models.CharField(
        max_length=42,
        unique=True,
        help_text="Public Ethereum/Polygon wallet address (0x...)"
    )
    private_key = models.CharField(
        max_length=66,
        help_text="Private key for wallet - SECURITY WARNING: stored in plain text!"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when wallet was created"
    )
    
    class Meta:
        verbose_name = "User Wallet"
        verbose_name_plural = "User Wallets"
        db_table = "blockchain_user_wallet"
    
    def __str__(self):
        return f"{self.user.username} - {self.address[:10]}..."
    
    def get_masked_private_key(self):
        """Return a masked version of the private key for display purposes."""
        if self.private_key:
            return f"{self.private_key[:6]}...{self.private_key[-4:]}"
        return "No private key"


class TeoCoinDiscountRequest(models.Model):
    """
    Model for tracking TeoCoin discount requests from students to teachers.
    
    Business Logic:
    1. Student requests discount by paying TEO tokens
    2. Teacher chooses between EUR commission or TEO staking
    3. System handles automatic expiration if teacher doesn't respond
    """
    
    STATUS_CHOICES = [
        (0, 'Pending'),      # Waiting for teacher decision
        (1, 'Approved'),     # Teacher accepted TEO tokens
        (2, 'Declined'),     # Teacher chose EUR commission
        (3, 'Expired'),      # Request expired, auto-EUR
    ]
    
    # Core identifiers
    student_address = models.CharField(
        max_length=42,
        help_text="Student's wallet address"
    )
    teacher_address = models.CharField(
        max_length=42,
        help_text="Teacher's wallet address"
    )
    course_id = models.PositiveIntegerField(
        help_text="ID of the course being purchased"
    )
    
    # Financial details (stored in smallest units for precision)
    course_price = models.PositiveIntegerField(
        help_text="Original course price in cents (EUR)"
    )
    discount_percent = models.PositiveIntegerField(
        help_text="Discount percentage in basis points (1000 = 10%)"
    )
    teo_cost = models.PositiveBigIntegerField(
        help_text="TEO tokens student pays (in wei, 18 decimals)"
    )
    teacher_bonus = models.PositiveBigIntegerField(
        help_text="Bonus TEO for teacher if accepted (in wei, 18 decimals)"
    )
    
    # Status and timing
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES,
        default=0,
        help_text="Current status of the discount request"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the request was created"
    )
    expires_at = models.DateTimeField(
        help_text="When the request expires (auto-EUR)"
    )
    teacher_decision_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When teacher made their decision"
    )
    
    # Optional fields
    decline_reason = models.TextField(
        blank=True,
        help_text="Optional reason if teacher declined"
    )
    blockchain_tx_hash = models.CharField(
        max_length=66,
        blank=True,
        help_text="Transaction hash for blockchain operations"
    )
    
    class Meta:
        verbose_name = "TeoCoin Discount Request"
        verbose_name_plural = "TeoCoin Discount Requests"
        db_table = "blockchain_teocoin_discount_request"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student_address', 'status']),
            models.Index(fields=['teacher_address', 'status']),
            models.Index(fields=['course_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Discount Request #{self.id} - Course {self.course_id} ({self.get_status_display()})"
    
    @property
    def is_expired(self):
        """Check if the request has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def discount_amount_eur(self):
        """Calculate discount amount in EUR"""
        return (self.course_price * self.discount_percent) / (100 * 10000)  # cents to EUR, basis points to percent
    
    @property
    def final_price_eur(self):
        """Calculate final price student pays in EUR"""
        return (self.course_price / 100) - self.discount_amount_eur
    
    @property
    def teo_cost_formatted(self):
        """Format TEO cost for display"""
        return self.teo_cost / (10 ** 18)
    
    @property
    def teacher_bonus_formatted(self):
        """Format teacher bonus for display"""
        return self.teacher_bonus / (10 ** 18)
    
    def can_teacher_decide(self):
        """Check if teacher can still make a decision"""
        return self.status == 0 and not self.is_expired
    
    def mark_expired(self):
        """Mark request as expired"""
        if self.status == 0:  # Only if still pending
            self.status = 3
            self.teacher_decision_at = timezone.now()
            self.save()
            return True
        return False
