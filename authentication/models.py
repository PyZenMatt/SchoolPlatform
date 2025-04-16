from django.contrib.auth.models import AbstractUser
from django.db import models

class AuthProfile(models.Model):
    user = models.OneToOneField('core.User', on_delete=models.CASCADE)
    last_password_change = models.DateTimeField(auto_now=True)
    failed_login_attempts = models.IntegerField(default=0)