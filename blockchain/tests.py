"""
Basic Tests for Blockchain Module

This file contains basic Django model tests. More comprehensive blockchain
tests are located in the tests/ directory.

For complete blockchain testing including contract interactions,
see the tests/ directory which contains:
- Unit tests for individual components
- Integration tests for blockchain operations
- Security tests for access control
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import UserWallet

User = get_user_model()


class UserWalletModelTest(TestCase):
    """
    Test cases for the UserWallet model.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_wallet_creation(self):
        """Test basic wallet creation."""
        wallet = UserWallet.objects.create(
            user=self.user,
            address='0x742d35Cc6634C0532925a3b8D402c5FC3dD5d9b0',
            private_key='0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        )
        
        self.assertEqual(wallet.user, self.user)
        self.assertEqual(len(wallet.address), 42)
        self.assertEqual(len(wallet.private_key), 66)
        
    def test_wallet_string_representation(self):
        """Test the string representation of wallet."""
        wallet = UserWallet.objects.create(
            user=self.user,
            address='0x742d35Cc6634C0532925a3b8D402c5FC3dD5d9b0',
            private_key='0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        )
        
        expected = f"{self.user.username} - {wallet.address[:10]}..."
        self.assertEqual(str(wallet), expected)
        
    def test_masked_private_key(self):
        """Test private key masking functionality."""
        wallet = UserWallet.objects.create(
            user=self.user,
            address='0x742d35Cc6634C0532925a3b8D402c5FC3dD5d9b0',
            private_key='0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        )
        
        masked = wallet.get_masked_private_key()
        self.assertTrue(masked.startswith('0x1234'))
        self.assertTrue(masked.endswith('cdef'))
        self.assertIn('...', masked)
        
    def test_wallet_unique_address(self):
        """Test that wallet addresses must be unique."""
        address = '0x742d35Cc6634C0532925a3b8D402c5FC3dD5d9b0'
        
        # Create first wallet
        UserWallet.objects.create(
            user=self.user,
            address=address,
            private_key='0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        )
        
        # Create second user
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Try to create wallet with same address - should fail
        with self.assertRaises(Exception):
            UserWallet.objects.create(
                user=user2,
                address=address,  # Same address
                private_key='0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
            )
