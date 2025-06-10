from rest_framework import generics, filters as drf_filters
from rest_framework.permissions import IsAuthenticated
from ..serializers import TeoCoinTransactionSerializer
from ..models import TeoCoinTransaction


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
