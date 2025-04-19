from django.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.core.validators import MinValueValidator
from users.models import User
from notifications.models import Notification
from rewards.models import TeoCoinTransaction


class Course(models.Model):  
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_created')
    price = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0, message="Il prezzo non può essere negativo")]
    )
    students = models.ManyToManyField(User, related_name='enrolled_courses', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    lessons = models.ManyToManyField('Lesson', related_name='courses_included')
     

    def __str__(self):
        return self.title

    def purchase_by_student(self, student):
        with transaction.atomic():
            if student in self.students.all():
                raise ValueError("Corso già acquistato")
            
            student.subtract_teo_coins(self.price)
            self.students.add(student)
            
            Notification.objects.create(
                user=student,
                message=f"Hai acquistato il corso '{self.title}'",
                notification_type='course_purchased',
                related_object_id=self.id
            )
    
            TeoCoinTransaction.objects.create(
                user=student,
                amount=-self.price,
                transaction_type='course_purchase'
            )
                
            teacher_earnings = int(self.price * 0.9)
            self.teacher.add_teo_coins(teacher_earnings)
            TeoCoinTransaction.objects.create(
                user=self.teacher,
                amount=teacher_earnings,
                transaction_type='course_earned'
            )

    def total_duration(self):
        return sum(lesson.duration for lesson in self.lessons.all())
    
class Lesson(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='lessons_in_course')
    duration = models.PositiveIntegerField(default=0, help_text="Durata in minuti")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lessons', db_index=True)

    def __str__(self):
        return self.title

    def clean(self):
        if self.course and self.teacher != self.course.teacher:
            raise ValidationError("Il teacher della lezione deve corrispondere al teacher del corso")


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

