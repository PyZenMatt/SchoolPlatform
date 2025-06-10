from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.validators import MinValueValidator
from users.models import User
from notifications.models import Notification
from rewards.models import BlockchainTransaction
from django.conf import settings
from PIL import Image
from .validators import validate_video_file


class Course(models.Model):  
    CATEGORY_CHOICES = [
        ('disegno', '✏️ Disegno'),
        ('pittura-olio', '🎨 Pittura ad Olio'),
        ('acquerello', '💧 Acquerello'),
        ('tempera', '🖌️ Tempera'),
        ('acrilico', '🌈 Pittura Acrilica'),
        ('scultura', '🗿 Scultura'),
        ('storia-arte', '📚 Storia dell\'Arte'),
        ('fotografia', '📸 Fotografia Artistica'),
        ('illustrazione', '🖊️ Illustrazione'),
        ('arte-digitale', '💻 Arte Digitale'),
        ('ceramica', '🏺 Ceramica e Terracotta'),
        ('incisione', '⚱️ Incisione e Stampa'),
        ('mosaico', '🔷 Mosaico'),
        ('restauro', '🛠️ Restauro Artistico'),
        ('calligrafia', '✒️ Calligrafia'),
        ('fumetto', '💭 Fumetto e Graphic Novel'),
        ('design-grafico', '🎨 Design Grafico'),
        ('arte-contemporanea', '🆕 Arte Contemporanea'),
        ('arte-classica', '🏛️ Arte Classica'),
        ('other', '🎭 Altro')
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='other',
        help_text="Categoria del corso per facilitare la navigazione"
    )
    cover_image = models.ImageField(
        upload_to='course_covers/',
        blank=True,
        null=True,
        help_text="Immagine di copertina del corso (opzionale)"
    )
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_created')
    price = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0, message="Il prezzo non può essere negativo")]
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='CourseEnrollment',
        related_name='core_students',)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    lessons = models.ManyToManyField('Lesson', related_name='courses_included')
    is_approved = models.BooleanField(default=False, help_text="Il corso deve essere approvato da un admin prima di essere messo in vendita.")
    reward_distributed = models.PositiveIntegerField(
        default=0,
        help_text="Totale TeoCoins distribuiti come ricompensa per questo corso"
    )

    def __str__(self):
        return self.title

    def purchase_by_student(self, student):
        """
        Handle course purchase using blockchain TeoCoins.
        This method is now deprecated - use the blockchain-integrated purchase_course API instead.
        """
        with transaction.atomic():
            if student in self.students.all():
                raise ValueError("Corso già acquistato")
            
            # Check blockchain balance instead of database balance
            from blockchain.views import teocoin_service
            if not student.wallet_address:
                raise ValueError("Wallet non collegato. Collega il tuo wallet per acquistare corsi.")
            
            balance = teocoin_service.get_balance(student.wallet_address)
            if balance < self.price:
                raise ValueError("TeoCoin insufficienti nel wallet")
            
            # For now, we just add the student to the course
            # The actual payment will be handled by the blockchain integration
            self.students.add(student)
            
            # Create notification
            Notification.objects.create(
                user=student,
                message=f"Hai acquistato il corso '{self.title}'",
                notification_type='course_purchased',
                related_object_id=str(self.pk) if self.pk else None
            )
            
            # Record blockchain transaction
            BlockchainTransaction.objects.create(
                user=student,
                amount=self.price,
                transaction_type='course_purchase',
                status='pending',
                related_object_id=str(self.pk) if self.pk else None
            )

    def total_duration(self):
        return sum(lesson.duration for lesson in self.lessons.all())
    
class Lesson(models.Model):
    LESSON_TYPE_CHOICES = [
        ('theory', 'Teoria'),
        ('practical', 'Pratica'),
        ('video', 'Video'),
        ('mixed', 'Mista'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPE_CHOICES,
        default='theory',
        help_text="Tipo di lezione"
    )
    video_file = models.FileField(
        upload_to='lesson_videos/',
        blank=True,
        null=True,
        validators=[validate_video_file],
        help_text="File video per lezioni video (max 200MB, formati: MP4, AVI, MOV, WMV, FLV, WebM, MKV)"
    )
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='lessons_in_course', null=True, blank=True)
    duration = models.PositiveIntegerField(default=0, help_text="Durata in minuti")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lessons', db_index=True)
    materials = models.JSONField(
        default=list, blank=True,
        help_text="Lista di URL per materiali di supporto (immagini, PDF)."
    )
    order = models.PositiveIntegerField(
        default = 1,
        help_text="Posizione della lezione all'interno del corso."
    )

    class Meta:
        ordering = ['order']  # ordina automaticamente per order

    def __str__(self):
        if self.course:
            return f"{self.course.title} – Lezione {self.order}: {self.title}"
        return f"Lezione {self.order}: {self.title}"

    def clean(self):
        if self.course and self.teacher != self.course.teacher:
            raise ValidationError("Il teacher della lezione deve corrispondere al teacher del corso")


class Exercise(models.Model):
    STATUS_CHOICES = (
        ('created', 'Creato'),
        ('submitted', 'Inviato'),
        ('reviewed', 'Valutato'),
    )
    
    EXERCISE_TYPE_CHOICES = [
        ('practical', 'Pratico'),
        ('study', 'Studio'),
        ('technique', 'Tecnica'),
        ('creative', 'Creativo'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzato'),
    ]
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='exercises',
        null=True,  # Permette valori nulli
        blank=True  # Permette di lasciare il campo vuoto nei form
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercises')
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    exercise_type = models.CharField(
        max_length=20,
        choices=EXERCISE_TYPE_CHOICES,
        default='practical',
        help_text="Tipo di esercizio"
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner',
        help_text="Livello di difficoltà"
    )
    time_estimate = models.PositiveIntegerField(
        default=60,
        help_text="Tempo stimato per completare l'esercizio (in minuti)"
    )
    materials = models.TextField(
        blank=True,
        help_text="Lista dei materiali necessari per l'esercizio"
    )
    instructions = models.TextField(
        blank=True,
        help_text="Istruzioni dettagliate per svolgere l'esercizio"
    )
    reference_image = models.ImageField(
        upload_to='exercise_references/',
        blank=True,
        null=True,
        help_text="Immagine di riferimento per l'esercizio (opzionale)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    score = models.PositiveIntegerField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        if self.status == 'reviewed' and self.score is None:
            raise ValidationError({'score': 'Un esercizio valutato richiede un punteggio'})
            
        if self.score and (self.score < 0 or self.score > 100):
            raise ValidationError({'score': 'Il punteggio deve essere tra 0 e 100'})

    def save(self, *args, **kwargs):
        if self.pk and self.student:
            old = Exercise.objects.get(pk=self.pk)
            if (old.status != self.status or old.score != self.score) \
               and self.status == 'reviewed' \
               and self.score is not None:
                
                self.assign_teo_coins()
                self.create_notification()
        
        super().save(*args, **kwargs)

    def assign_teo_coins(self):
        """
        Assign TeoCoin rewards for completed exercises using blockchain.
        This method now integrates with the blockchain reward system.
        """
        if self.student and not hasattr(self, '_teocoins_assigned') and self.score:
            reward = self.score // 10  # Same reward calculation
            
            # Use blockchain reward system instead of fake coins
            if self.student.wallet_address:
                try:
                    from blockchain.views import mint_tokens
                    from decimal import Decimal
                    
                    # Mint reward tokens directly to student's wallet
                    tx_hash = mint_tokens(
                        self.student.wallet_address,
                        Decimal(str(reward)),
                        f"Exercise reward for {self.title}"
                    )
                    
                    # Record blockchain transaction
                    BlockchainTransaction.objects.create(
                        user=self.student,
                        amount=reward,
                        transaction_type='exercise_reward',
                        tx_hash=tx_hash,
                        status='completed',
                        related_object_id=str(self.pk) if self.pk else None
                    )
                    
                    self._teocoins_assigned = True
                    
                except Exception as e:
                    # Log error but don't fail the exercise grading
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to mint reward for exercise {self.pk}: {str(e)}")
            else:
                # Student doesn't have wallet linked - create pending reward
                BlockchainTransaction.objects.create(
                    user=self.student,
                    amount=reward,
                    transaction_type='exercise_reward',
                    status='pending_wallet',
                    related_object_id=str(self.pk) if self.pk else None,
                    notes="Reward pending - wallet not linked"
                )

    def create_notification(self):
        if self.student and self.pk:
            Notification.objects.create(
                user=self.student,
                message=f"Esercizio {self.title} valutato: {self.score}/100",
                notification_type='exercise_graded',
                related_object_id=str(self.pk)
            )

    class Meta:
        verbose_name = "Esercizio"
        verbose_name_plural = "Esercizi"


class CourseEnrollment(models.Model):
    """
    Rappresenta l'iscrizione di uno studente a un corso e il suo stato di completamento.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(
        default=False,
        help_text="Flag che indica se lo studente ha completato tutte le lezioni (per il certificato)."
    )

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        status = "Completato" if self.completed else "In corso"
        return f"{self.student.username} → {self.course.title} ({status})"

class ExerciseSubmission(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    average_score = models.FloatField(default=0)
    is_approved = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)
    reviewers = models.ManyToManyField(User, related_name='assigned_reviews')
    reward_amount = models.PositiveIntegerField(default=0)


    @staticmethod
    def notify_reviewers(submission, num_reviewers=3):
        reviewers = User.objects.filter(groups__name='Valutatori').order_by('?')[:num_reviewers]  # Supponendo che i valutatori siano in un gruppo specifico
        for reviewer in reviewers:
            Notification.objects.create(
                user=reviewer,
                message=f"Un nuovo esercizio è stato sottomesso per la revisione: {submission.exercise.title}",
                notification_type='exercise_submission',
                related_object_id=submission.id
            )


    def notify_student(self):
        status = "approvato" if self.is_approved else "non approvato"
        Notification.objects.create(
            user=self.student,
            message=f"Il tuo esercizio '{self.exercise.title}' è stato {status}.",
            notification_type='exercise_status',
            related_object_id=str(self.pk) if self.pk else None
        )
            

class ExerciseReview(models.Model):
    assigned_at = models.DateTimeField(auto_now_add=True)
    submission = models.ForeignKey(ExerciseSubmission, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    

    @staticmethod
    def calculate_average_score(submission):
        reviews = submission.reviews.all()
        if reviews.exists():
            average = reviews.aggregate(models.Avg('score'))['score__avg']
            submission.average_score = average
            # Approvato solo se almeno 3 review e media >= 6
            if reviews.count() >= 3:
                submission.is_approved = average >= 6
            submission.save()
            return submission.is_approved if reviews.count() >= 3 else None
        return None

    @staticmethod
    def reward_reviewer(review):
        """
        Reward reviewers with blockchain TeoCoins for their work.
        This method now integrates with the blockchain reward system.
        """
        reward_amount = 1  # 1 TeoCoin per review
        
        if review.reviewer.wallet_address:
            try:
                from blockchain.views import mint_tokens
                from decimal import Decimal
                
                # Mint reward tokens directly to reviewer's wallet
                tx_hash = mint_tokens(
                    review.reviewer.wallet_address,
                    Decimal(str(reward_amount)),
                    f"Review reward for submission {review.submission.id}"
                )
                
                # Record blockchain transaction
                BlockchainTransaction.objects.create(
                    user=review.reviewer,
                    amount=reward_amount,
                    transaction_type='review_reward',
                    tx_hash=tx_hash,
                    status='completed',
                    related_object_id=str(review.pk) if review.pk else None
                )
                
                review.reward = reward_amount
                review.save()
                
            except Exception as e:
                # Log error but don't fail the review process
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to mint reward for review {review.pk}: {str(e)}")
        else:
            # Reviewer doesn't have wallet linked - create pending reward
            BlockchainTransaction.objects.create(
                user=review.reviewer,
                amount=reward_amount,
                transaction_type='review_reward',
                status='pending_wallet',
                related_object_id=str(review.pk) if review.pk else None,
                notes="Reward pending - wallet not linked"
            )

class ReviewerReputation(models.Model):
    reviewer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reputation')
    reputation_score = models.FloatField(default=5.0)  # Da 1 a 10

    @staticmethod
    def update_reputation(reviewer, submission, score):
        average_score = submission.reviews.exclude(reviewer=reviewer).aggregate(models.Avg('score'))['score__avg']
        if average_score:
            difference = abs(score - average_score)
            penalty = difference / 10  # Penalità proporzionale alla differenza
            reputation = ReviewerReputation.objects.get(reviewer=reviewer)
            reputation.reputation_score = max(1, reputation.reputation_score - penalty)
            reputation.save()

class LessonCompletion(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='completed_lessons')
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'lesson')
        verbose_name = 'Completamento Lezione'
        verbose_name_plural = 'Completamenti Lezioni'

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"