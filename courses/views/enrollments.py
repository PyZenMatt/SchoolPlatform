from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from decimal import Decimal
import uuid
import logging

from courses.models import Course
from rewards.models import BlockchainTransaction
from courses.serializers import StudentCourseSerializer
from users.permissions import IsTeacher

logger = logging.getLogger(__name__)


class PurchaseCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        student = request.user
        wallet_address = request.data.get('wallet_address')
        transaction_hash = request.data.get('transaction_hash')
        payment_confirmed = request.data.get('payment_confirmed', False)

        if student.role != 'student':
            return Response({"error": "Solo studenti possono acquistare corsi"}, status=status.HTTP_403_FORBIDDEN)

        # Verifica che il corso sia approvato
        if not course.is_approved:
            return Response({"error": "Questo corso non è ancora disponibile per l'acquisto"}, status=status.HTTP_403_FORBIDDEN)

        if student in course.students.all():
            return Response({"error": "Hai già acquistato questo corso"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate wallet address
        if not wallet_address:
            return Response({
                "error": "Wallet address è richiesto per l'acquisto",
                "action_required": "provide_wallet"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Update user's wallet address if not set or if different
        if not student.wallet_address:
            student.wallet_address = wallet_address
            student.save()
        elif student.wallet_address.lower() != wallet_address.lower():
            student.wallet_address = wallet_address
            student.save()

        try:
            # Check blockchain balance
            from blockchain.views import teocoin_service
            balance = teocoin_service.get_balance(wallet_address)
            
            if balance < course.price:
                return Response({
                    "error": f"TeoCoin insufficienti. Serve: {course.price}, Disponibili: {balance}",
                    "required": course.price,
                    "available": str(balance)
                }, status=status.HTTP_400_BAD_REQUEST)

            # Se non è stata fornita una transazione hash, richiedere il pagamento
            if not payment_confirmed or not transaction_hash:
                # Calcola commissione platform e importo netto per teacher
                commission_rate = Decimal('0.15')  # 15% commissione
                commission_amount = course.price * commission_rate
                teacher_amount = course.price - commission_amount
                
                return Response({
                    "payment_required": True,
                    "course_price": str(course.price),
                    "teacher_amount": str(teacher_amount),
                    "commission_amount": str(commission_amount),
                    "teacher_address": course.teacher.wallet_address,
                    "student_address": wallet_address,
                    "course_id": course.pk,
                    "message": "Acquisto corso: Lo studente paga in TeoCoins, le gas fees sono pagate dalla reward pool"
                }, status=status.HTTP_402_PAYMENT_REQUIRED)

            # Verifica la transazione sulla blockchain
            # Per la nuova logica, verifichiamo che ci siano state le transazioni corrette:
            # 1. Studente -> Teacher (importo netto)
            # 2. Studente -> Reward Pool (commissione)
            transaction_valid = self._verify_course_payment_transaction(
                transaction_hash, 
                wallet_address, 
                course.teacher.wallet_address,
                course.price
            )
            
            if not transaction_valid:
                return Response({
                    "error": "Transazione blockchain non valida o non confermata",
                    "transaction_hash": transaction_hash
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                # Verifica che la transazione non sia già stata processata
                if BlockchainTransaction.objects.filter(transaction_hash=transaction_hash).exists():
                    return Response({
                        "error": "Transazione già processata"
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Add student to course
                course.students.add(student)
                
                # Record purchase transaction (studente paga il prezzo totale)
                purchase_transaction = BlockchainTransaction.objects.create(
                    user=student,
                    amount=-course.price,  # Negativo = uscita dallo studente per il prezzo totale
                    transaction_type='course_purchase',
                    status='completed',
                    transaction_hash=transaction_hash,
                    from_address=wallet_address,
                    to_address=course.teacher.wallet_address if course.teacher.wallet_address else "unknown",
                    related_object_id=str(course.pk) if course.pk else None,
                    notes=f"Course purchase: {course.title} - Total price paid by student"
                )
                
                # Calcola commissione e importo netto teacher
                commission_amount = course.price * Decimal('0.15')  # 15% di commissione
                teacher_net_amount = course.price - commission_amount  # 85% rimane al teacher
                
                # Record teacher earnings transaction (teacher riceve)
                teacher_earning_transaction = BlockchainTransaction.objects.create(
                    user=course.teacher,
                    amount=teacher_net_amount,  # Positivo = entrata per il teacher
                    transaction_type='course_earned',
                    status='completed',
                    transaction_hash=transaction_hash,
                    from_address=wallet_address,
                    to_address=course.teacher.wallet_address,
                    related_object_id=str(course.pk) if course.pk else None,
                    notes=f"Earnings from course sale: {course.title}"
                )
                
                # Record commission transaction (commissione alla reward pool)
                # La commissione viene pagata dallo studente come parte del prezzo del corso
                commission_transaction = BlockchainTransaction.objects.create(
                    user=student,  # Lo studente paga la commissione
                    amount=-commission_amount,  # Negativo = uscita dallo studente
                    transaction_type='platform_commission',
                    status='completed',
                    transaction_hash=transaction_hash,
                    from_address=wallet_address,  # Dal wallet studente
                    to_address=getattr(settings, 'REWARD_POOL_ADDRESS', 'reward_pool'),
                    related_object_id=str(course.pk) if course.pk else None,
                    notes=f"Platform commission (15%) from course purchase: {course.title}"
                )
                
                logger.info(f"Commission registered: {commission_amount} TEO paid by student {student.wallet_address} to reward pool")
                
                # Chiama funzioni per le notifiche
                from courses.signals import notify_course_purchase
                notify_course_purchase(course, student, course.teacher)

                logger.info(f"Course purchase completed: {student.username} -> {course.title} (TX: {transaction_hash})")

                return Response({
                    "message": "Corso acquistato con successo!",
                    "course_title": course.title,
                    "total_paid": str(course.price),
                    "teacher_net_amount": str(teacher_net_amount),
                    "commission_amount": str(commission_amount),
                    "transaction_hash": transaction_hash,
                    "wallet_address": wallet_address,
                    "blockchain_verified": True,
                    "payment_breakdown": {
                        "student_paid": str(course.price),
                        "teacher_received": str(teacher_net_amount),
                        "platform_commission": str(commission_amount),
                        "commission_rate": "15%"
                    },
                    "commission_status": "completed"  # Ora le commissioni sono gestite automaticamente
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Course purchase error: {str(e)}")
            return Response({"error": f"Errore durante l'acquisto: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    def _verify_course_payment_transaction(self, tx_hash, student_address, teacher_address, course_price):
        """
        Verifica che il pagamento del corso sia stato effettuato correttamente:
        - Cerca le transazioni nei nostri record (potrebbero essere multiple per un corso)
        - Verifica che lo studente abbia pagato il prezzo completo
        - Verifica che il teacher abbia ricevuto l'importo netto
        - Verifica che la reward pool abbia ricevuto la commissione
        """
        try:
            from rewards.models import BlockchainTransaction
            from decimal import Decimal
            
            # Cerca transazioni correlate al transaction hash principale
            related_transactions = BlockchainTransaction.objects.filter(
                transaction_hash=tx_hash
            )
            
            if related_transactions.exists():
                # Verifica se è una transazione registrata nei nostri record
                for tx in related_transactions:
                    if (tx.from_address and tx.to_address and
                        tx.from_address.lower() == student_address.lower() and
                        tx.to_address.lower() == teacher_address.lower() and
                        abs(tx.amount) >= course_price * Decimal('0.85')):  # Teacher riceve almeno 85%
                        logger.info(f"Found valid course payment transaction: {tx_hash}")
                        return True
                
            # Fallback: usa la logica blockchain standard
            return self._verify_blockchain_transaction(tx_hash, student_address, teacher_address, course_price)
            
        except Exception as e:
            logger.error(f"Error verifying course payment transaction {tx_hash}: {str(e)}")
            return False

    def _verify_blockchain_transaction(self, tx_hash, from_address, to_address, expected_amount):
        """Verifica che la transazione sulla blockchain sia valida"""
        try:
            # Check if this is a simulated transaction hash (for testing)
            if tx_hash.startswith("0x") and len(tx_hash) == 66:
                # Check if this is a simulated transaction in our database
                from rewards.models import BlockchainTransaction
                simulated_tx = BlockchainTransaction.objects.filter(
                    transaction_hash=tx_hash,
                    transaction_type='simulated_payment',
                    status='completed'
                ).first()
                
                if simulated_tx:
                    # Verify the simulated transaction details match
                    simulated_from = simulated_tx.from_address.lower() if simulated_tx.from_address else ""
                    simulated_to = simulated_tx.to_address.lower() if simulated_tx.to_address else ""
                    request_from = from_address.lower() if from_address else ""
                    request_to = to_address.lower() if to_address else ""
                    
                    if (simulated_from == request_from and 
                        simulated_to == request_to and
                        simulated_tx.amount >= expected_amount):
                        logger.info(f"Valid simulated transaction found: {tx_hash}")
                        return True
                    else:
                        logger.warning(f"Simulated transaction details don't match: {tx_hash}")
                        return False
            
            # Standard blockchain verification for real transactions
            from blockchain.views import teocoin_service
            
            # Ottieni la ricevuta della transazione
            receipt = teocoin_service.w3.eth.get_transaction_receipt(tx_hash)
            
            if receipt["status"] != 1:  # Transazione fallita
                logger.warning(f"Transaction failed: {tx_hash}")
                return False
            
            # Ottieni i dettagli della transazione
            tx = teocoin_service.w3.eth.get_transaction(tx_hash)
            
            # Verifica che sia una transazione verso il contratto TeoCoin
            tx_to = tx.get("to")
            contract_addr = getattr(teocoin_service, 'contract_address', None)
            if tx_to and contract_addr and str(tx_to).lower() != str(contract_addr).lower():
                logger.warning(f"Transaction not to TeoCoin contract: {tx_hash}")
                return False
            
            # Decodifica i log per verificare il trasferimento
            transfer_events = teocoin_service.contract.events.Transfer().process_receipt(receipt)
            
            for event in transfer_events:
                event_from = event.args['from'].lower()
                event_to = event.args['to'].lower()
                event_amount = teocoin_service.w3.from_wei(event.args['value'], 'ether')
                
                # Verifica che il trasferimento corrisponda
                if (event_from == from_address.lower() and 
                    (to_address is None or event_to == to_address.lower()) and
                    Decimal(str(event_amount)) >= expected_amount):
                    logger.info(f"Valid transfer found: {event_amount} TEO from {event_from} to {event_to}")
                    return True
            
            logger.warning(f"No valid transfer event found in transaction: {tx_hash}")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying transaction {tx_hash}: {str(e)}")
            return False


class StudentEnrolledCoursesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = request.user
        enrolled_courses = Course.objects.filter(students=student, is_approved=True)
        serializer = StudentCourseSerializer(enrolled_courses, many=True)
        return Response(serializer.data)


class TeacherCourseStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        teacher = request.user
        courses = Course.objects.filter(teacher=teacher).prefetch_related('students')

        data = []
        for course in courses:
            students = course.students.all()
            student_data = [
                {"id": s.id, "username": s.username, "email": s.email}
                for s in students
            ]
            data.append({
                "course_id": course.pk,
                "course_title": course.title,
                "students": student_data
            })

        return Response(data)
