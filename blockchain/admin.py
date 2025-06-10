"""
Django Admin Configuration for Blockchain Module

This module configures the Django admin interface for blockchain-related models.
"""

from django.contrib import admin
from .models import UserWallet


@admin.register(UserWallet)
class UserWalletAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserWallet model.
    
    Security Note: Private keys are masked in the admin interface
    to prevent accidental exposure.
    """
    list_display = ('user', 'address', 'masked_private_key_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'address')
    readonly_fields = ('created_at', 'masked_private_key_display')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Wallet Details', {
            'fields': ('address', 'private_key', 'masked_private_key_display')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    @admin.display(description='Private Key (Masked)')
    def masked_private_key_display(self, obj):
        """Display masked private key in admin interface."""
        return obj.get_masked_private_key()
    
    def has_delete_permission(self, request, obj=None):
        """
        Restrict wallet deletion to superusers only.
        This prevents accidental loss of wallet data.
        """
        return request.user.is_superuser
