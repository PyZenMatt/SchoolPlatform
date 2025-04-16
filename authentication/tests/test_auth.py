from django.urls import reverse
from rest_framework.test import APITestCase
from core.models import User

class AuthTestCase(APITestCase):
    def test_registration(self):
        url = reverse('register')
        data = {
            'username': 'testuser',
            'email': 'test@teoart.it',  # Campo obbligatorio
            'password': 'TestPass123!',
            'role': 'student'
        }
        response = self.client.post(url, data, format='json')  # Usa formato JSON
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_jwt_login(self):
    # Crea utente con TUTTI i campi obbligatori
        user = User.objects.create_user(
        username='testuser',
        email='test@teoart.it',  # Campo obbligatorio
        password='testpass123',
        role='student',
        teo_coins=100  # Campo necessario per il serializer
    )
    
        response = self.client.post(
        reverse('token_obtain_pair'),
        {'username': 'testuser', 'password': 'testpass123'},
        format='json'  # fondamentale
    )
    
        self.assertEqual(response.status_code, 200)
        print(response.data)  # Debug: visualizza la risposta completa
        self.assertIn('user', response.data)