from rest_framework import generics, filters as drf_filters
from rest_framework.permissions import IsAuthenticated
from ..serializers import TeoCoinTransactionSerializer
from ..models import TeoCoinTransaction


class TransactionHistoryView(generics.ListAPIView):
    """List view for user's TeoCoin transaction history with filtering"""
    serializer_class = TeoCoinTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['transaction_type']
    ordering_fields = ['created_at', 'amount']
    ordering = ['-created_at']  # Default ordering

    def get_queryset(self):
        """Filter transactions by authenticated user and optional date range"""
        user = self.request.user
        queryset = TeoCoinTransaction.objects.filter(user=user)
        
        # Handle date filtering
        date_from = getattr(self.request, 'query_params', self.request.GET).get('from')
        date_to = getattr(self.request, 'query_params', self.request.GET).get('to')
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
            
        return queryset
