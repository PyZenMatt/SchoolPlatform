from rest_framework import serializers
from .models import TeoCoinTransaction

class TeoCoinTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeoCoinTransaction
        fields = ['user', 'amount', 'created_at', 'transaction_type']