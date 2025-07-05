**🚀 ROADMAP: Backend Proxy Architecture for TeoCoin Discount System**

## **Phase 1: Smart Contract Integration Service**

### **1.1 Create TeoCoin Discount Service** ⭐ **PRIORITY 1**
- [ ] **File**: `services/teocoin_discount_service.py`
- [ ] Load smart contract ABI and address
- [ ] Implement platform wallet gas management
- [ ] Create contract interaction functions:
  - `create_discount_request()`
  - `approve_discount_request()`
  - `decline_discount_request()`
  - `get_teacher_requests()`
  - `get_student_requests()`

### **1.2 Backend API Endpoints** ⭐ **PRIORITY 1**
- [ ] **File**: `api/teocoin_discount_views.py`
- [ ] `POST /api/v1/teocoin-discount/request/` - Student requests discount
- [ ] `GET /api/v1/teacher/discount-requests/` - List teacher's pending requests
- [ ] `POST /api/v1/teacher/discount-requests/{id}/accept/` - Teacher accepts
- [ ] `POST /api/v1/teacher/discount-requests/{id}/reject/` - Teacher rejects
- [ ] `GET /api/v1/student/discount-requests/` - Student's request history

### **1.3 Database Models (Optional)** 🔶 **PRIORITY 2**
- [ ] **File**: `rewards/models.py`
- [ ] `TeoCoinDiscountRequest` model for caching smart contract data
- [ ] Sync with blockchain events for reliability
- [ ] Add indexes for teacher/student queries

---

## **Phase 2: Frontend Integration**

### **2.1 Fix Payment Modal** ⭐ **PRIORITY 1**
- [ ] **File**: PaymentModal.jsx
- [ ] **Remove** current TeoCoin transfer logic (lines 706-775)
- [ ] **Replace** with backend API calls
- [ ] **Remove** MetaMask transaction requirements
- [ ] Add discount request UI flow

### **2.2 Teacher Dashboard Integration** ⭐ **PRIORITY 1**
- [ ] **File**: `TeacherDiscountManager.jsx` (rename from TeacherEscrowManager.jsx)
- [ ] **Replace** current escrow logic with EUR vs TEO choice UI
- [ ] Show student already received discount (guaranteed)
- [ ] Add clear Accept TEO vs Keep EUR buttons
- [ ] Display teacher bonus calculations and staking benefits
- [ ] Show 2-hour timeout countdown

### **2.3 Student Discount UI** 🔶 **PRIORITY 2**
- [ ] **File**: `frontend/src/components/student/DiscountHistory.jsx` (new)
- [ ] Show student's discount request history
- [ ] Display request status (pending/approved/declined/expired)
- [ ] Show TEO costs and discount amounts

---

## **Phase 3: Platform Configuration**

### **3.1 Environment Setup** ⭐ **PRIORITY 1**
- [ ] **File**: `.env`
- [ ] Set `PLATFORM_PRIVATE_KEY` for gas payments
- [ ] Verify `TEOCOIN_DISCOUNT_CONTRACT_ADDRESS`
- [ ] Configure gas limit and price settings

### **3.2 Django Settings** ⭐ **PRIORITY 1**
- [ ] **File**: `schoolplatform/settings.py`
- [ ] Add smart contract ABI configuration
- [ ] Set platform wallet settings
- [ ] Configure discount system parameters

### **3.3 Gas Management** 🔶 **PRIORITY 2**
- [ ] **File**: `services/gas_management.py` (new)
- [ ] Monitor platform wallet MATIC balance
- [ ] Automatic gas price optimization
- [ ] Alerts for low balance

---

## **Phase 4: Business Logic Integration**

### **4.1 Course Purchase Flow** ⭐ **PRIORITY 1**
- [ ] **File**: `courses/views/payments.py`
- [ ] Student gets immediate discount and enrollment
- [ ] Create discount request notification for teacher
- [ ] Implement teacher EUR vs TEO choice logic
- [ ] Handle platform discount absorption when teacher declines

### **4.2 Platform Economics** 🔶 **PRIORITY 2**
- [ ] **File**: `courses/utils.py`
- [ ] Calculate platform discount absorption when teacher declines TEO
- [ ] Implement 50% baseline commission with staking tier adjustments
- [ ] Handle reward pool TEO returns and bonus distributions
- [ ] Real-time TEO/EUR rate updates for discount calculations

### **4.3 Notification System** 🔶 **PRIORITY 2**
- [ ] **File**: `notifications/services.py`
- [ ] Notify teachers: "Student got discount - choose EUR vs TEO"
- [ ] Notify students of teacher's decision (accepted/declined TEO)
- [ ] Email notifications for 2-hour timeout warnings
- [ ] Show teacher staking benefits in notifications

---

## **Phase 5: Testing & Optimization**

### **5.1 Backend Testing** ⭐ **PRIORITY 1**
- [ ] **File**: `tests/test_teocoin_discount.py`
- [ ] Unit tests for service functions
- [ ] Integration tests for smart contract calls
- [ ] API endpoint testing

### **5.2 Frontend Testing** 🔶 **PRIORITY 2**
- [ ] Test discount request flow end-to-end
- [ ] Test teacher approval/rejection
- [ ] Error handling for failed transactions

### **5.3 Gas Optimization** 🔷 **PRIORITY 3**
- [ ] Batch multiple operations when possible
- [ ] Optimize gas prices dynamically
- [ ] Monitor and reduce transaction costs

---

## **Phase 6: Monitoring & Maintenance**

### **6.1 Analytics Dashboard** 🔷 **PRIORITY 3**
- [ ] Track discount request volumes
- [ ] Monitor teacher acceptance rates
- [ ] Platform gas cost analytics

### **6.2 Background Jobs** 🔶 **PRIORITY 2**
- [ ] **File**: `celery_tasks/teocoin_discount.py`
- [ ] Process expired requests automatically
- [ ] Sync blockchain events with database
- [ ] Platform wallet balance monitoring

---

## **🎯 Implementation Order:**

### **Week 1: Core Integration**
1. ✅ Create `TeoCoinDiscountService`
2. ✅ Implement backend API endpoints
3. ✅ Fix PaymentModal frontend

### **Week 2: Teacher & Student UX**
4. ✅ Update TeacherEscrowManager
5. ✅ Test teacher approval flow
6. ✅ Student discount history

### **Week 3: Testing & Polish**
7. ✅ Comprehensive testing
8. ✅ Gas optimization
9. ✅ Documentation

## **🔧 Files to Create:**
- `services/teocoin_discount_service.py`
- `api/teocoin_discount_views.py` 
- `api/teocoin_discount_urls.py`
- `frontend/src/services/api/teocoinDiscount.js`
- `frontend/src/components/teacher/TeacherDiscountManager.jsx` (new)
- `tests/test_teocoin_discount.py`

## **🔧 Files to Modify:**
- `PaymentModal.jsx` (remove MetaMask transactions)
- `TeacherEscrowManager.jsx` → rename to `TeacherDiscountManager.jsx`
- `schoolplatform/settings.py`
- `schoolplatform/urls.py`
- `courses/views/payments.py`

## **🗑️ Files to Delete/Replace:**
- `services/escrow_service.py` (replace with discount service)
- Any old escrow-related frontend components
- Old MetaMask transaction code in PaymentModal.jsx

**Ready to start with Phase 1? Should I begin with creating the `TeoCoinDiscountService`?**