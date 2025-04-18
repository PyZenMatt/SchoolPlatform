from django.core.management.base import BaseCommand
from core.models import User, Lesson, Course, TeoCoinTransaction

class Command(BaseCommand):
    help = 'Popola il database con dati demo'

    def handle(self, *args, **options):
        self.stdout.write("Creazione utenti demo...")
        
        # Crea insegnante
        teacher, created = User.objects.get_or_create(
            username='prof_verdi',
            defaults={
                'email': 'verdi@teoart.it',
                'role': 'teacher',
            }
        )
        if created:
            teacher.set_password('testpass123')
            teacher.save()
            self.stdout.write(f"Insegnante creato: {teacher.username}")

        # Crea studente
        student, created = User.objects.get_or_create(
            username='student_demo',
            defaults={
                'email': 'student@teoart.it',
                'role': 'student',
                'teo_coins': 1000
            }
        )
        if created:
            student.set_password('demopass123')
            student.save()
            self.stdout.write(f"Studente creato: {student.username}")

        

        
