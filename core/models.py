from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import F
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.validators import MinValueValidator
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
    
    class Meta:
        app_label = 'authentication'
    
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

class Lesson(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['teacher', 'created_at']),
            models.Index(fields=['title'], name='title_idx')
        ]
    title = models.CharField(max_length=200)
    content = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lessons')
    price = models.PositiveIntegerField(
        default=0,
        validators=[
            MinValueValidator(
                0, 
                message="Il prezzo non può essere negativo"
            )
        ]
    )
    duration = models.PositiveIntegerField(default=0, help_text="Durata in minuti")
    students = models.ManyToManyField(User, related_name='purchased_lessons', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def notify_purchased(self, student):
        Notification.objects.create(
            user=student,
            message=f"Hai acquistato la lezione '{self.title}'",
            notification_type='lesson_purchased',
            related_object_id=self.id
    )

    def purchase_by_student(self, student):
        with transaction.atomic():
            if student in self.students.all():
                raise ValueError("Lezione già acquistata")
        
        student.subtract_teo_coins(self.price)
        self.students.add(student)
        self.notify_purchased(student)
        
        # Crea notifica
        Notification.objects.create(
            user=student,
            message=f"Hai acquistato la lezione '{self.title}'",
            notification_type='lesson_purchased',
            related_object_id=self.id
        )
  
        TeoCoinTransaction.objects.create(
            user=student,
            amount=-self.price,
            transaction_type='lesson_purchase'
            )
            
        teacher_earnings = int(self.price * 0.9)
        self.teacher.add_teo_coins(teacher_earnings)
        TeoCoinTransaction.objects.create(
            user=self.teacher,
            amount=teacher_earnings,
            transaction_type='lesson_earned'
            )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Lezione"
        verbose_name_plural = "Lezioni"

class Exercise(models.Model):
    STATUS_CHOICES = (
        ('submitted', 'Inviato'),
        ('reviewed', 'Valutato'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercises')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises')
    submission = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    score = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"

    def clean(self):
        if self.status == 'reviewed' and self.score is None:
            raise ValidationError({'score': 'Un esercizio valutato richiede un punteggio'})
            
        
        if self.score and (self.score < 0 or self.score > 100):
            raise ValidationError({'score': 'Il punteggio deve essere tra 0 e 100'})

    def save(self, *args, **kwargs):
        if self.pk:
            old = Exercise.objects.get(pk=self.pk)
            if (old.status != self.status or old.score != self.score) \
               and self.status == 'reviewed' \
               and self.score is not None:
                
                self.assign_teo_coins()
                self.create_notification()
        
        super().save(*args, **kwargs)

    def assign_teo_coins(self):
        if not hasattr(self, '_teocoins_assigned'):
            reward = self.score // 10
            self.student.add_teo_coins(reward)
            TeoCoinTransaction.objects.create(
                user=self.student,
                amount=reward,
                transaction_type='exercise_reward'
            )
            self._teocoins_assigned = True

    def create_notification(self):
        Notification.objects.create(
            user=self.student,
            message=f"Esercizio {self.lesson.title} valutato: {self.score}/100",
            notification_type='exercise_graded',
            related_object_id=self.id
        )

    class Meta:
        verbose_name = "Esercizio"
        verbose_name_plural = "Esercizi"

class TeoCoinTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('earned', 'Guadagnati'),
        ('spent', 'Spesi'),
        ('transferred', 'Trasferiti'),
        ('lesson_purchase', 'Acquisto Lezione'),
        ('lesson_earned', 'Guadagno Lezione'),
        ('exercise_reward', 'Ricompensa Esercizio'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.get_transaction_type_display()} - {self.amount}"

    class Meta:
        verbose_name = "Transazione TeoCoin"
        verbose_name_plural = "Transazioni TeoCoin"

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    lessons = models.ManyToManyField(Lesson, related_name='courses')
    price = models.PositiveIntegerField(default=0)
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def total_duration(self):
        return sum(lesson.duration for lesson in self.lessons.all())

    class Meta:
        verbose_name = "Corso"
        verbose_name_plural = "Corsi"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('lesson_purchased', 'Acquisto Lezione'),
        ('exercise_graded', 'Esercizio Valutato'),
        ('course_completed', 'Corso Completato'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    read = models.BooleanField(default=False)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.get_notification_type_display()}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notifica"
        verbose_name_plural = "Notifiche"
        ordering = ['-created_at']