from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.auth.models import BaseUserManager
from decimal import Decimal

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'email è obbligatoria')
        if 'role' not in extra_fields or not extra_fields['role']:
            raise ValueError('Il ruolo è obbligatorio')
        email = self.normalize_email(email)
        role = extra_fields.get('role')

        # Gli studenti sono approvati automaticamente
        if role == 'student':
            extra_fields['is_approved'] = True

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Il superuser deve avere is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Il superuser deve avere is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    is_approved = models.BooleanField(
        default=False,
        help_text="Solo gli insegnanti approvati da admin possono pubblicare corsi/lezioni."
    )
    bio = models.TextField(
        blank=True, null=True,
        help_text="Breve biografia (opzionale)."
    )
    avatar = models.ImageField(
        upload_to='avatars/', blank=True, null=True,
        help_text="Immagine di profilo (opzionale)."
    )
    email = models.EmailField(unique=True)
    ROLE_CHOICES = (
        ('student', 'Studente'),
        ('teacher', 'Maestro'),
        ('admin', 'Amministratore'),
    )
    enrolled_courses = models.ManyToManyField('courses.Course', related_name='enrolled_students', blank=True)
    created_courses = models.ManyToManyField('courses.Course', related_name='teachers', blank=True)
    is_email_verified = models.BooleanField(default=False)
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES,
        error_messages={
            'invalid_choice': '"%(value)s" non è una scelta valida.'
        }
    )

    email_verification_token = models.CharField(max_length=100, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']
    objects = UserManager()
    address = models.TextField(blank=True, null=True)  # Campo per l'indirizzo
    purchased_lessons = models.ManyToManyField(
        'courses.Lesson',
        related_name='purchasers',
        blank=True
    )
    phone = models.CharField(max_length=30, blank=True)  # Nuovo campo per il numero di telefono
    
    # Blockchain Integration
    wallet_address = models.CharField(
        max_length=42, 
        blank=True, 
        null=True,
        help_text="Indirizzo wallet Ethereum/Polygon per TeoCoins"
    )
    
    # Campi specifici per la scuola d'arte
    profession = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Professione artistica (es. illustratore, pittore ad olio, scultore)"
    )
    artistic_aspirations = models.TextField(
        blank=True, 
        null=True,
        help_text="Aspirazioni e specializzazioni artistiche"
    )
    
    def __str__(self):
        return self.email
    
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

    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"
        app_label = 'users'


class UserSettings(models.Model):
    """Model for storing user preferences and settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    course_reminders = models.BooleanField(default=True)
    weekly_digest = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    # UI preferences
    theme = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    language = models.CharField(max_length=5, default='it')
    timezone = models.CharField(max_length=50, default='Europe/Rome')
    
    # Privacy settings
    show_profile = models.BooleanField(default=True)
    show_progress = models.BooleanField(default=False)
    show_achievements = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Impostazioni Utente"
        verbose_name_plural = "Impostazioni Utenti"
    
    def __str__(self):
        return f"Settings for {self.user.email}"


class UserProgress(models.Model):
    """Model for tracking user progress across categories"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    
    # Overall statistics
    total_courses_enrolled = models.PositiveIntegerField(default=0)
    total_courses_completed = models.PositiveIntegerField(default=0)
    total_lessons_completed = models.PositiveIntegerField(default=0)
    total_exercises_completed = models.PositiveIntegerField(default=0)
    total_hours_studied = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Tracking fields
    last_activity_date = models.DateTimeField(null=True, blank=True)
    streak_days = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Progresso Utente"
        verbose_name_plural = "Progressi Utenti"
    
    def __str__(self):
        return f"Progress for {self.user.email}"
    
    def calculate_overall_progress(self):
        """Calculate overall progress percentage"""
        if self.total_courses_enrolled == 0:
            return 0
        return round((self.total_courses_completed / self.total_courses_enrolled) * 100, 2)


class Achievement(models.Model):
    """Model for achievements that users can earn"""
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='award')
    color = models.CharField(max_length=7, default='#feca57')  # Hex color
    points_required = models.PositiveIntegerField(default=0)
    achievement_type = models.CharField(max_length=50, choices=[
        ('course_completion', 'Course Completion'),
        ('streak', 'Learning Streak'),
        ('score', 'High Score'),
        ('participation', 'Participation'),
        ('special', 'Special Achievement')
    ])
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"
    
    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    """Model for tracking which achievements users have earned"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_date = models.DateTimeField(auto_now_add=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        unique_together = ('user', 'achievement')
        verbose_name = "Achievement Utente"
        verbose_name_plural = "Achievements Utenti"
    
    def __str__(self):
        return f"{self.user.email} - {self.achievement.title}"


