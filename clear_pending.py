import os, sys, django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.models import TeoCoinWithdrawalRequest, DBTeoCoinBalance
from services.teocoin_withdrawal_service import teocoin_withdrawal_service
from decimal import Decimal

# Clear pending withdrawals
pending = TeoCoinWithdrawalRequest.objects.filter(status='pending')
print(f"🔄 Processing {pending.count()} pending withdrawals...")

for withdrawal in pending:
    print(f"👤 {withdrawal.user.email}: {withdrawal.amount} TEO → {withdrawal.metamask_address}")
    
    # Process with minting
    result = teocoin_withdrawal_service.mint_tokens_to_address(
        amount=withdrawal.amount,
        to_address=withdrawal.metamask_address,
        withdrawal_id=withdrawal.pk
    )
    
    if result['success']:
        withdrawal.status = 'completed'
        withdrawal.transaction_hash = result.get('transaction_hash', 'demo')
        withdrawal.save()
        
        # Update balance
        balance_obj = DBTeoCoinBalance.objects.get(user=withdrawal.user)
        balance_obj.pending_withdrawal -= withdrawal.amount
        balance_obj.save()
        
        print(f"✅ Completed! TX: {result.get('transaction_hash', 'N/A')}")
    else:
        print(f"❌ Failed: {result.get('error')}")

print("🎉 All pending withdrawals cleared!")
