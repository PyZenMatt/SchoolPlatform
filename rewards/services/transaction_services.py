from django.db import transaction
from django.core.exceptions import ValidationError
from core.models import User
from courses.models import Course
from rewards.models import TeoCoinTransaction

class TransactionService:
    @classmethod
    @transaction.atomic
    def purchase_course(cls, user: User, course: Course):
        """
        Acquisto corso con gestione transazionale
        :raises: ValidationError
        """
        if user.teo_coins < course.price:
            raise ValidationError("Saldo TeoCoin insufficiente")

        # Lock ottimistico sull'utente
        user = User.objects.select_for_update().get(pk=user.pk)
        user.teo_coins -= course.price
        user.save(update_fields=['teo_coins'])
        
        course.students.add(user)
        
        # Registrazione transazione
        TeoCoinTransaction.objects.create(
            user=user,
            amount=-course.price,
            transaction_type='course_purchase'
        )

        # Invia segnale per notifiche/aggiornamenti secondari
        from django.db.models.signals import post_save
        post_save.send(
            sender=Course,
            instance=course,
            created=False,
            update_fields=['students']
        )

    @classmethod
    @transaction.atomic
    def transfer_teocoins(cls, sender: User, receiver: User, amount: int):
        """Transfer con lock su entrambi gli utenti"""
        if amount <= 0:
            raise ValidationError("Importo non valido")

        # Lock sugli utenti coinvolti
        sender = User.objects.select_for_update().get(pk=sender.pk)
        receiver = User.objects.select_for_update().get(pk=receiver.pk)

        if sender.teo_coins < amount:
            raise ValidationError("Saldo insufficiente")

        sender.teo_coins -= amount
        receiver.teo_coins += amount

        sender.save(update_fields=['teo_coins'])
        receiver.save(update_fields=['teo_coins'])

        # Registrazione transazioni
        TeoCoinTransaction.objects.bulk_create([
            TeoCoinTransaction(
                user=sender,
                amount=-amount,
                transaction_type='transfer_out'
            ),
            TeoCoinTransaction(
                user=receiver,
                amount=amount,
                transaction_type='transfer_in'
            )
        ])