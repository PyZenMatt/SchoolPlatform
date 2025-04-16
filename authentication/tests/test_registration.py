from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from core.models import User

class UserRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('register')

    def test_valid_registration(self):
        data = {
            'username': 'new_user',
            'email': 'user@teoart.it',
            'password': 'SecurePass123!',
            'role': 'student'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='new_user').exists())

    def test_invalid_role_registration(self):
        data = {
            'username': 'invalid_user',
            'email': 'invalid@teoart.it',
            'password': 'SecurePass123!',
            'role': 'admin'  # Ruolo non consentito
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)