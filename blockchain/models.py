from django.db import models
from django.conf import settings

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
