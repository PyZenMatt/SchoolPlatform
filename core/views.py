from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.db import transaction
from .models import User,Lesson, Exercise, Course, Notification, TeoCoinTransaction
from .serializers import RegisterSerializer, LessonSerializer, ExerciseSerializer,CourseSerializer, UserSerializer,TeoCoinTransactionSerializer, NotificationSerializer
from django.shortcuts import render
from rest_framework import generics, status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.shortcuts import get_object_or_404
from rest_framework import generics, filters as drf_filters
from .services.transaction_services import TransactionService
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as df_filters
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import user_passes_test

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

# Lezioni (solo per utenti autenticati)
class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = LessonSerializer

    def perform_create(self, serializer):
        # Verifica che l'utente sia un maestro
        if self.request.user.role != 'teacher':
            raise PermissionDenied("Solo i maestri possono creare lezioni.")

        # Imposta l'utente attualmente autenticato come insegnante (teacher) della lezione
        serializer.save(teacher=self.request.user)

# Esercizi (solo per utenti autenticati)
class ExerciseListCreateView(generics.ListCreateAPIView):
    queryset = Exercise.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = ExerciseSerializer

    def perform_create(self, serializer):
        # Imposta l'utente attualmente autenticato come creatore dell'esercizio
        serializer.save(owner=self.request.user)

class UserTeoCoinsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Visualizza il saldo TeoCoin dell'utente autenticato."""
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def post(self, request):
        try:
            amount = int(request.data.get('amount', 0))  # Converti esplicitamente
        except ValueError:
            return Response({"error": "Invalid amount"}, status=400)
        """Aggiungi TeoCoin all'utente (solo per admin o per logiche specifiche)."""
        # Solo admin possono aggiungere TeoCoin
        if not request.user.is_staff:
            return Response({"error": "You do not have permission to add TeoCoins."}, 
                            status=status.HTTP_403_FORBIDDEN)

        amount = request.data.get('amount', 0)
        
        # Controlla che l'importo sia positivo
        if amount <= 0:
            return Response({"error": "Amount must be positive."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Aggiungi i TeoCoin all'utente
        request.user.add_teo_coins(amount)

        return Response({"message": f"{amount} TeoCoins added to your balance."}, 
                         status=status.HTTP_200_OK)


class TransferTeoCoinsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Permette il trasferimento di TeoCoin tra due utenti."""
        from_user = request.user
        to_user_id = request.data.get('to_user_id')
        
        # Converti amount a intero
        try:
            amount = int(request.data.get('amount', 0))
        except ValueError:
            return Response({"error": "Importo non valido"}, status=status.HTTP_400_BAD_REQUEST)

        # Verifica se l'utente di destinazione esiste
        try:
            to_user = User.objects.get(id=to_user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Verifica che l'utente abbia abbastanza TeoCoin da trasferire
        if from_user.teo_coins < amount:
            return Response({"error": "Insufficient TeoCoins."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Riduci i TeoCoin dell'utente mittente e aggiungi quelli al destinatario
            from_user.subtract_teo_coins(amount)
            to_user.add_teo_coins(amount)
            return Response({"message": f"{amount} TeoCoins transferred to {to_user.username}."}, 
                             status=status.HTTP_200_OK)
        except ValueError as e:
            # In caso di errore (ad esempio, saldo insufficiente)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def earn_teo_coins(request):
    amount = request.data.get('amount')
    if not amount or int(amount) <= 0:
        return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    user.teo_coins += int(amount)
    user.save()

    TeoCoinTransaction.objects.create(
        user=user,
        amount=int(amount),
        transaction_type='earned'
    )

    return Response({
        "message": "TeoCoins earned successfully!",
        "new_balance": user.teo_coins  # Fixato qui
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_teo_coins(request):
    recipient_username = request.data.get('recipient')
    amount = int(request.data.get('amount', 0))

    if not recipient_username or amount <= 0:
        return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

    sender = request.user
    try:
        recipient = User.objects.get(username=recipient_username)
    except User.DoesNotExist:
        return Response({"error": "Recipient not found"}, status=status.HTTP_404_NOT_FOUND)

    if sender.teo_coins < amount:
        return Response({"error": "Insufficient balance"}, status=400)

    sender.teo_coins -= amount
    recipient.teo_coins += amount
    sender.save()
    recipient.save()

    TeoCoinTransaction.objects.create(user=sender, amount=-amount, transaction_type='spent')
    TeoCoinTransaction.objects.create(user=recipient, amount=amount, transaction_type='earned')

    return Response({
        "message": f"Transferred {amount} TeoCoins to {recipient_username}",
        "sender_balance": sender.teo_coins,  # Fixato qui
        "recipient_balance": recipient.teo_coins  # Fixato qui
    }, status=status.HTTP_200_OK)

class PurchaseLessonView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        student = request.user

        if student.role != 'student':
            return Response({"error": "Solo studenti possono acquistare lezioni"}, status=status.HTTP_403_FORBIDDEN)

        if student in lesson.students.all():
            return Response({"error": "Hai già acquistato questa lezione"}, status=status.HTTP_400_BAD_REQUEST)

        if student.teo_coins < lesson.price:
            return Response({"error": "TeoCoin insufficienti"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                student.subtract_teo_coins(lesson.price)
                lesson.teacher.add_teo_coins(int(lesson.price * 0.9))
                lesson.students.add(student)

                TeoCoinTransaction.objects.create(
                    user=student,
                    amount=-lesson.price,
                    transaction_type='lesson_purchase'
                )
                TeoCoinTransaction.objects.create(
                    user=lesson.teacher,
                    amount=int(lesson.price * 0.9),
                    transaction_type='lesson_earned'
                )

                return Response({
                    "message": "Lezione acquistata con successo!",
                    "teacher_earned": lesson.price * 0.9,
                    "platform_fee": lesson.price * 0.1
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        platform_fee = lesson.price * 0.10
        teacher_earnings = lesson.price - platform_fee

        student.subtract_teo_coins(lesson.price)
        lesson.teacher.add_teo_coins(int(teacher_earnings))
        lesson.students.add(student)  # Registra lo studente

        TeoCoinTransaction.objects.create(
            user=student,
            amount=-lesson.price,
            transaction_type='spent'
        )
        TeoCoinTransaction.objects.create(
            user=lesson.teacher,
            amount=teacher_earnings,
            transaction_type='earned'
        )

        return Response({
            "message": "Lezione acquistata con successo!",
            "teacher_earned": teacher_earnings,
            "platform_fee": platform_fee
        })
    
class TransactionHistoryView(generics.ListAPIView):
    serializer_class = TeoCoinTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['transaction_type']
    ordering_fields = ['created_at', 'amount']

    def get_queryset(self):
        user = self.request.user
        date_from = self.request.query_params.get('from')
        date_to = self.request.query_params.get('to')
        queryset = TeoCoinTransaction.objects.filter(user=user)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        return queryset
    
    def get(self, request, *args, **kwargs):
        if request.accepts('text/html'):
            transactions = self.get_queryset()
            return render(request, 'dashboard/transactions.html', {
                'transactions': transactions
            })
        return super().get(request, *args, **kwargs)

    pagination_class = None

class NotificationFilter(df_filters.FilterSet):
    created_after = df_filters.DateTimeFilter(
    field_name='created_at', 
    lookup_expr='gte',
    help_text="Filtra notifiche create dopo questa data/ora (YYYY-MM-DD HH:MM:SS)"
    )

    class Meta:
        model = Notification
        fields = ['notification_type', 'read']

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]  
    filterset_fields = ['notification_type', 'read']
    filterset_class = NotificationFilter 
    pagination_class = None

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.read = True
        notification.save()
        return Response({"status": "marked as read"})

class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_fields = ['teacher', 'price']
    search_fields = ['title', 'description']

    def perform_create(self, serializer):
        if self.request.user.role != 'teacher':
            raise PermissionDenied("Solo i maestri possono creare corsi")
        serializer.save(teacher=self.request.user)

class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CourseSerializer

    def perform_update(self, serializer):
        if serializer.instance.teacher != self.request.user:
            raise PermissionDenied("Non sei il proprietario di questo corso")
        serializer.save()

from .services.transaction_services import TransactionService

class PurchaseCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        user = request.user

        try:
            TransactionService.purchase_course(user, course)
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['GET'])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def teocoin_balance(request):
    return Response({
        'balance': int(request.user.teo_coins),
        'updated_at': timezone.now().isoformat()
    })

def is_student_or_superuser(user):
    return user.role == 'student' or user.is_superuser

@user_passes_test(is_student_or_superuser)
@login_required
@require_GET
def dashboard_transactions(request):
    transactions = TeoCoinTransaction.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'dashboard/partials/transactions.html', {
        'transactions': transactions
    })
