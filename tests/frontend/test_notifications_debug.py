#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to the Python path
sys.path.insert(0, '/home/teo/Project/school/schoolplatform')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from notifications.models import Notification
from django.utils import timezone

def test_notifications():
    print("=== TEST NOTIFICHE ===")
    
    # Trova un teacher
    teachers = User.objects.filter(role='teacher')
    print(f"Teacher trovati: {teachers.count()}")
    
    if teachers.exists():
        teacher = teachers.first()
        print(f"Teacher di test: {teacher.username} ({teacher.email})")
        
        # Verifica se ha notifiche
        notifications = Notification.objects.filter(user=teacher)
        print(f"Notifiche totali per {teacher.username}: {notifications.count()}")
        
        # Mostra le notifiche
        for notif in notifications.order_by('-created_at')[:5]:
            print(f"- {notif.created_at}: {notif.message} (Type: {notif.notification_type}, Read: {notif.read})")
        
        # Crea una notifica di test
        test_notification = Notification.objects.create(
            user=teacher,
            message="Test notification - Il tuo profilo è stato approvato!",
            notification_type='teacher_approved',
            related_object_id=teacher.pk
        )
        print(f"Creata notifica di test: {test_notification.id}")
        
        # Verifica la creazione
        total_after = Notification.objects.filter(user=teacher).count()
        print(f"Notifiche dopo il test: {total_after}")
        
    else:
        print("Nessun teacher trovato per il test")
    
    # Verifica tutte le notifiche nel sistema
    all_notifications = Notification.objects.all()
    print(f"\nTotale notifiche nel sistema: {all_notifications.count()}")
    
    # Raggruppa per tipo
    from django.db.models import Count
    notification_types = Notification.objects.values('notification_type').annotate(count=Count('id')).order_by('-count')
    print("\nNotifiche per tipo:")
    for nt in notification_types:
        print(f"- {nt['notification_type']}: {nt['count']}")

if __name__ == "__main__":
    test_notifications()
