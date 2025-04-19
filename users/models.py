from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import F
from django.db import transaction
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.crypto import get_random_string


class User(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Studente'),
        ('teacher', 'Maestro'),
        ('admin', 'Amministratore'),
    )
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES,
        error_messages={
            'invalid_choice': '"%(value)s" non è una scelta valida.'
        }
    )
    teo_coins = models.PositiveIntegerField(default=0)
    email_verification_token = models.CharField(max_length=100, blank=True)

    REQUIRED_FIELDS = ['email', 'role']
    
  
    
    def __str__(self):
        return self.username

    def send_verification_email(self):
        self.email_verification_token = get_random_string(50)
        self.save()
        send_mail(
            'Verifica il tuo account TeoArt',
            f'Clicca per verificare: http://localhost:8000/auth/verify-email/{self.email_verification_token}/',
            'noreply@teoart.it',
            [self.email],
            fail_silently=False,
        )

    def add_teo_coins(self, amount):
        User.objects.filter(pk=self.pk).update(
            teo_coins=F('teo_coins') + amount
        )
        self.refresh_from_db()

    def subtract_teo_coins(self, amount):
        with transaction.atomic():
            # Usa select_for_update con nowait per deadlock
            user = User.objects.select_for_update(nowait=True).get(pk=self.pk)
            if user.teo_coins < amount:
                raise ValueError("Saldo insufficiente")
            user.teo_coins -= amount
            user.save(update_fields=['teo_coins'])
         
    def get_teocoin_balance(self):
        cache_key = f'user_{self.id}_teocoins'
        balance = cache.get(cache_key)
        if balance is None:
            balance = self.teo_coins
            cache.set(cache_key, balance, timeout=60)
        return balance

    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"
        app_label = 'users'
