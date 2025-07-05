# 🏗️ TeoCoin Escrow Implementation Roadmap

## 🎯 **OBJECTIVE**
Implement teacher choice system where TeoCoin discounts go to escrow until teacher accepts/rejects them.

## 📊 **BUSINESS FLOW OVERVIEW**
```
Student applies 10% discount (100 TeoCoin + 90€)
    ↓
TeoCoin → ESCROW (hold)
    ↓
Teacher gets NOTIFICATION
    ↓
Teacher CHOOSES:
├── ACCEPT → Gets 45€ + 100 TeoCoin
└── REJECT → Gets 50€ + 0 TeoCoin (TeoCoin → Platform)
```

---

## 🗺️ **IMPLEMENTATION ROADMAP**

### **Phase 3A: Database & Models** (60 minutes)
- **3A.1** TeoCoin Escrow Model
- **3A.2** Notification Types Extension
- **3A.3** Database Migrations

### **Phase 3B: Backend Logic** (90 minutes)
- **3B.1** Escrow Service Creation
- **3B.2** Payment Flow Modification
- **3B.3** Teacher Choice API Endpoints

### **Phase 3C: Frontend Interface** (80 minutes)
- **3C.1** Teacher Choice Modal Component
- **3C.2** Notification Integration
- **3C.3** Dashboard Escrow Section

### **Phase 3D: Integration & Testing** (50 minutes)
- **3D.1** End-to-End Flow Testing
- **3D.2** Escrow Expiration Logic
- **3D.3** Error Handling & Edge Cases

**Total Estimated Time: 4.5 hours**

---

## 📋 **DETAILED STEP-BY-STEP IMPLEMENTATION**

## **PHASE 3A: DATABASE & MODELS** 📊

### **Step 3A.1: Create TeoCoin Escrow Model**
**File**: `rewards/models.py`
**Time**: 20 minutes

**Action**: Add new model after BlockchainTransaction class
```python
class TeoCoinEscrow(models.Model):
    """
    Holds TeoCoin until teacher accepts/rejects discount
    """
    ESCROW_STATUS = (
        ('pending', 'Pending Teacher Decision'),
        ('accepted', 'Teacher Accepted - TeoCoin Released'),
        ('rejected', 'Teacher Rejected - TeoCoin Returned'),
        ('expired', 'Expired - Auto Returned to Platform'),
    )
    
    # Core escrow data
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teocoin_escrows_as_student')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teocoin_escrows_as_teacher')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    
    # Financial details
    teocoin_amount = models.DecimalField(max_digits=18, decimal_places=8)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    discount_euro_amount = models.DecimalField(max_digits=10, decimal_places=2)
    original_course_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Teacher compensation options
    standard_euro_commission = models.DecimalField(max_digits=10, decimal_places=2)  # If rejected
    reduced_euro_commission = models.DecimalField(max_digits=10, decimal_places=2)   # If accepted
    
    # Blockchain details
    escrow_tx_hash = models.CharField(max_length=66, null=True, blank=True)
    release_tx_hash = models.CharField(max_length=66, null=True, blank=True)
    
    # Status and timing
    status = models.CharField(max_length=20, choices=ESCROW_STATUS, default='pending')
    expires_at = models.DateTimeField()  # Auto-reject after this
    
    # Decision tracking
    teacher_decision_at = models.DateTimeField(null=True, blank=True)
    teacher_decision_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "TeoCoin Escrow"
        verbose_name_plural = "TeoCoin Escrows"
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Escrow: {self.teocoin_amount} TEO for {self.course.title} ({self.status})"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at and self.status == 'pending'
    
    @property
    def time_remaining(self):
        if self.status != 'pending':
            return None
        remaining = self.expires_at - timezone.now()
        return remaining if remaining.total_seconds() > 0 else None
```

### **Step 3A.2: Extend Notification Types**
**File**: `notifications/models.py`
**Time**: 10 minutes

**Action**: Add new notification type to NOTIFICATION_TYPES tuple
```python
# Add to existing NOTIFICATION_TYPES tuple:
('teocoin_discount_pending', 'TeoCoin Discount - Teacher Decision Required'),
('teocoin_discount_accepted', 'TeoCoin Discount - Accepted by Teacher'),
('teocoin_discount_rejected', 'TeoCoin Discount - Rejected by Teacher'),
('teocoin_discount_expired', 'TeoCoin Discount - Expired (Auto-Rejected)'),
```

### **Step 3A.3: Create and Run Migrations**
**Time**: 30 minutes

**Actions**:
1. Generate migrations
2. Review migration files
3. Apply to database
4. Verify model creation

```bash
python manage.py makemigrations rewards notifications
python manage.py migrate
python manage.py shell
# Test: from rewards.models import TeoCoinEscrow
```

---

## **PHASE 3B: BACKEND LOGIC** ⚙️

### **Step 3B.1: Create Escrow Service**
**File**: `services/escrow_service.py` (NEW FILE)
**Time**: 30 minutes

**Action**: Create new service for escrow management
```python
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rewards.models import TeoCoinEscrow
from notifications.models import Notification

class TeoCoinEscrowService:
    """
    Manages TeoCoin escrow lifecycle
    """
    
    def create_escrow(self, student, teacher, course, teocoin_amount, discount_data):
        """Create new escrow when student uses TeoCoin discount"""
        
    def notify_teacher(self, escrow):
        """Send notification to teacher about pending escrow"""
        
    def accept_escrow(self, escrow_id, teacher):
        """Teacher accepts TeoCoin - release to teacher wallet"""
        
    def reject_escrow(self, escrow_id, teacher):
        """Teacher rejects TeoCoin - return to platform"""
        
    def process_expired_escrows(self):
        """Background task to handle expired escrows"""
        
    def calculate_teacher_options(self, course_price, discount_percentage, teacher_tier):
        """Calculate teacher compensation for both accept/reject scenarios"""
```

### **Step 3B.2: Modify Payment Flow**
**File**: `courses/views/payments.py`
**Time**: 40 minutes

**Action**: Replace direct reward pool transfer with escrow creation
```python
# REPLACE this section (around line 150):
# result = teo_service.transfer_with_reward_pool_gas(...)

# WITH escrow creation:
from services.escrow_service import TeoCoinEscrowService

escrow_service = TeoCoinEscrowService()
escrow = escrow_service.create_escrow(
    student=request.user,
    teacher=course.teacher,
    course=course,
    teocoin_amount=required_teo,
    discount_data={
        'percentage': teocoin_discount,
        'euro_amount': teocoin_discount * amount_eur / 100,
        'original_price': amount_eur
    }
)

# Continue with EUR payment processing...
```

### **Step 3B.3: Teacher Choice API Endpoints**
**File**: `api/teacher_escrow_views.py` (NEW FILE)
**Time**: 20 minutes

**Action**: Create API endpoints for teacher escrow decisions
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rewards.models import TeoCoinEscrow
from services.escrow_service import TeoCoinEscrowService

class TeacherEscrowListView(APIView):
    """GET /api/teacher/escrows/"""
    
class TeacherEscrowAcceptView(APIView):
    """POST /api/teacher/escrows/{id}/accept/"""
    
class TeacherEscrowRejectView(APIView):
    """POST /api/teacher/escrows/{id}/reject/"""
```

---

## **PHASE 3C: FRONTEND INTERFACE** 💻

### **Step 3C.1: Teacher Choice Modal Component**
**File**: `frontend/src/components/TeoCoinChoiceModal.jsx` (NEW FILE)
**Time**: 40 minutes

**Action**: Create modal for teacher escrow decisions
```jsx
import React, { useState } from 'react';
import { acceptEscrow, rejectEscrow } from '../services/api/teacher';

const TeoCoinChoiceModal = ({ escrow, onClose, onDecision }) => {
    // Component for displaying escrow details and choice buttons
    // Show calculations: Accept vs Reject scenarios
    // Handle accept/reject API calls
    // Display confirmation screens
};
```

### **Step 3C.2: Notification Integration**
**File**: `frontend/src/components/NotificationBell.jsx`
**Time**: 20 minutes

**Action**: Add escrow notifications to existing notification system
```jsx
// Add handling for teocoin_discount_pending notifications
// Show special styling for escrow notifications
// Quick action buttons in notification dropdown
```

### **Step 3C.3: Teacher Dashboard Escrow Section**
**File**: `frontend/src/components/teacher/EscrowDashboard.jsx` (NEW FILE)
**Time**: 20 minutes

**Action**: Add escrow management section to teacher dashboard
```jsx
// List pending escrows
// Show escrow history
// Quick accept/reject actions
// Escrow statistics and earnings
```

---

## **PHASE 3D: INTEGRATION & TESTING** 🧪

### **Step 3D.1: End-to-End Flow Testing**
**Time**: 30 minutes

**Test Scenarios**:
1. Student applies TeoCoin discount → Escrow created
2. Teacher receives notification → Can view escrow details  
3. Teacher accepts → TeoCoin released, reduced EUR commission
4. Teacher rejects → TeoCoin returned, standard EUR commission

### **Step 3D.2: Escrow Expiration Logic**
**File**: `services/escrow_service.py`
**Time**: 10 minutes

**Action**: Implement and test automatic expiration
```python
# Background task (Django-cron or Celery)
def process_expired_escrows():
    expired = TeoCoinEscrow.objects.filter(
        status='pending',
        expires_at__lt=timezone.now()
    )
    for escrow in expired:
        escrow_service.expire_escrow(escrow)
```

### **Step 3D.3: Error Handling & Edge Cases**
**Time**: 10 minutes

**Test Cases**:
- Teacher tries to accept expired escrow
- Multiple escrows for same teacher
- Blockchain transaction failures
- Notification delivery failures

---

## **📱 USER INTERFACE MOCKUPS**

### **Teacher Notification**
```
🔔 NEW TEOCOIN DISCOUNT REQUEST

Student: Maria Rossi wants to buy "Digital Art Basics"
Course Price: €100
Discount: 10% (100 TeoCoin)

YOUR OPTIONS:
┌─────────────────────────────────────────┐
│ ✅ ACCEPT TEOCOIN                       │
│ • You get: €45 + 100 TeoCoin           │
│ • Student saves: €10                   │
│ • TeoCoin goes to your wallet          │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│ 💰 STANDARD COMMISSION                  │  
│ • You get: €50 (standard rate)         │
│ • TeoCoin returns to platform          │
│ • No crypto management needed          │
└─────────────────────────────────────────┘

⏰ Decide within 7 days (auto-rejects after)
```

### **Teacher Dashboard Escrow Section**
```
💰 TEOCOIN ESCROW MANAGEMENT

📊 PENDING DECISIONS (2)
┌──────────────────────────────────────────┐
│ Digital Art Basics - Maria R.           │
│ 100 TEO (10% discount)                  │
│ Accept: €45 + 100 TEO | Reject: €50     │
│ ⏰ 4 days remaining                      │
│ [ACCEPT] [REJECT] [VIEW DETAILS]         │
└──────────────────────────────────────────┘

📈 THIS MONTH
• Escrows Received: 8
• Accepted: 6 (75%)
• TeoCoin Earned: 450 TEO
• Extra Earnings: +€67.50 TEO value
```

---

## **🔧 TECHNICAL ARCHITECTURE**

### **Database Relationships**
```
TeoCoinEscrow
├── student (FK → User)
├── teacher (FK → User)  
├── course (FK → Course)
└── status (pending/accepted/rejected/expired)

Notification
├── user (FK → User) [teacher]
├── notification_type = 'teocoin_discount_pending'
└── related_object_id = escrow.id
```

### **API Endpoints**
```
GET  /api/teacher/escrows/           # List teacher's escrows
POST /api/teacher/escrows/{id}/accept/  # Accept escrow
POST /api/teacher/escrows/{id}/reject/  # Reject escrow
GET  /api/escrows/{id}/details/      # Escrow details
```

### **Background Tasks**
```
Daily: process_expired_escrows()
├── Find escrows where expires_at < now()
├── Auto-reject expired escrows  
├── Return TeoCoin to platform
└── Notify teacher of missed opportunity
```

---

## **🚀 DEPLOYMENT CHECKLIST**

### **Pre-Deployment**
- [ ] Database migrations applied
- [ ] Escrow service tests passing
- [ ] Frontend components tested
- [ ] API endpoints documented
- [ ] Background task scheduled

### **Post-Deployment**  
- [ ] Monitor escrow creation rates
- [ ] Track teacher acceptance rates
- [ ] Verify blockchain transactions
- [ ] Check notification delivery
- [ ] Monitor expired escrow processing

### **Success Metrics**
- **Teacher Adoption**: >60% of teachers interact with escrows
- **Acceptance Rate**: >40% of escrows accepted by teachers  
- **System Reliability**: <1% escrow processing failures
- **User Experience**: <3 clicks to accept/reject escrow

---

## **📋 PHASE 3 COMPLETION CRITERIA**

✅ **Models & Database**
- TeoCoinEscrow model created and migrated
- Notification types extended
- Database relationships working

✅ **Backend Logic**  
- Escrow service implemented
- Payment flow modified to use escrow
- Teacher choice API endpoints functional

✅ **Frontend Interface**
- Teacher choice modal component
- Notification integration
- Dashboard escrow section

✅ **Integration**
- End-to-end flow tested
- Expiration logic working
- Error handling implemented

**🎯 Result**: Teachers can receive notifications about TeoCoin discounts and choose to accept (get TeoCoin + reduced EUR) or reject (get standard EUR commission).
