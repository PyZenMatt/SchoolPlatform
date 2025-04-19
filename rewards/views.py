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
from schoolplatform.users.permissions import IsTeacher
from django.db.models import Count, F, Sum, ExpressionWrapper, FloatField
from schoolplatform.users.permissions import IsStudent
from rest_framework.permissions import BasePermission
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from users.models import User
from .serializers import TeoCoinTransactionSerializer
from .models import TeoCoinTransaction
from users.serializers import UserSerializer

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
    
@api_view(['GET'])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def teocoin_balance(request):
    return Response({
        'balance': int(request.user.teo_coins),
        'updated_at': timezone.now().isoformat()
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

# Create your views here.
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
    
