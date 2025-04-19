from django.urls import path
from .views import UserTeoCoinsView,TransferTeoCoinsView, earn_teo_coins, TransactionHistoryView, teocoin_balance


urlpatterns = [
    path('teo-coins/', UserTeoCoinsView.as_view(), name='teo-coins'),
    path('transfer-teo-coins/', TransferTeoCoinsView.as_view(), name='transfer-teo-coins'),
    path('earn-teo-coins/', earn_teo_coins, name='earn_teo_coins'),
    path('teo-coins/balance/', teocoin_balance, name='teocoin-balance'),
    path('transactions/', TransactionHistoryView.as_view(),name='transaction-history'),
]