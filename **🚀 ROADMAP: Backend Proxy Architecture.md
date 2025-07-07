**🚀 ROADMAP: Backend Proxy Architecture for TeoCoin Discount System**

## **Phase 1: Smart Contract Integration Service**

### **1.1 Create TeoCoin Discount Service** ⭐ **PRIORITY 1** ✅ **COMPLETED**
- [x] **File**: `services/teocoin_discount_service.py`
- [x] Load smart contract ABI and address
- [x] Implement platform wallet gas management
- [x] Create contract interaction functions:
  - `create_discount_request()`
  - `approve_discount_request()`
  - `decline_discount_request()`
  - `get_teacher_requests()`
  - `get_student_requests()`

### **1.2 Backend API Endpoints** ⭐ **PRIORITY 1** ✅ **COMPLETED**
- [x] **File**: `api/teocoin_discount_views.py`
- [x] `POST /api/v1/services/discount/create/` - Student requests discount
- [x] `GET /api/v1/services/discount/teacher/{address}/` - List teacher's pending requests
- [x] `POST /api/v1/services/discount/approve/` - Teacher accepts
- [x] `POST /api/v1/services/discount/decline/` - Teacher rejects
- [x] `GET /api/v1/services/discount/student/{address}/` - Student's request history
- [x] **File**: `api/teocoin_discount_urls.py` - URL configuration
- [x] **File**: `services/urls.py` - Registered discount endpoints

### **1.3 Database Models (Optional)** 🔶 **PRIORITY 2**
- [ ] **File**: `rewards/models.py`
- [ ] `TeoCoinDiscountRequest` model for caching smart contract data
- [ ] Sync with blockchain events for reliability
- [ ] Add indexes for teacher/student queries

---

## **Phase 2: Frontend Integration**

### **2.1 Fix Payment Modal** ⭐ **PRIORITY 1** ✅ **COMPLETED**
- [x] **File**: PaymentModal.jsx
- [x] **Remove** current TeoCoin transfer logic (lines 706-775)
- [x] **Replace** with backend API calls
- [x] **Remove** MetaMask transaction requirements
- [x] Add discount request UI flow
- [x] **File**: `frontend/src/services/api/teocoinDiscount.js` - API service layer
- [x] Updated UI text to reflect correct business logic
- [x] Fixed import references in TeacherDashboard.jsx and NavBar

### **2.2 Teacher Dashboard Integration** ⭐ **PRIORITY 1** ✅ **COMPLETED**
- [x] **File**: `TeacherDiscountDashboard.jsx` (enhanced existing component)
- [x] **Replace** current escrow logic with EUR vs TEO choice UI
- [x] Show student already received discount (guaranteed)
- [x] Add clear Accept TEO vs Keep EUR buttons
- [x] Display teacher bonus calculations and staking benefits
- [x] Show 2-hour timeout countdown
- [x] Professional Material-UI dialogs with business logic explanations
- [x] Real-time analytics dashboard (earnings, approval rates, monthly stats)
- [x] API integration via teocoinDiscount service
- [x] Enhanced user notifications and error handling

### **2.3 Student Discount UI** 🔶 **PRIORITY 2**
- [ ] **File**: `frontend/src/components/student/DiscountHistory.jsx` (new)
- [ ] Show student's discount request history
- [ ] Display request status (pending/approved/declined/expired)
- [ ] Show TEO costs and discount amounts

---

## **Phase 3: Platform Configuration**

### **3.1 Environment Setup** ⭐ **PRIORITY 1** ✅ **COMPLETED**
- [x] **File**: `.env`
- [x] Set `PLATFORM_PRIVATE_KEY` for gas payments
- [x] Verify `TEOCOIN_DISCOUNT_CONTRACT_ADDRESS`
- [x] Configure gas limit and price settings

### **3.2 Django Settings** ⭐ **PRIORITY 1** ✅ **COMPLETED**
- [x] **File**: `schoolplatform/settings.py`
- [x] Add smart contract ABI configuration
- [x] Set platform wallet settings
- [x] Configure discount system parameters

### **3.3 Gas Management** 🔶 **PRIORITY 2**
- [ ] **File**: `services/gas_management.py` (new)
- [ ] Monitor platform wallet MATIC balance
- [ ] Automatic gas price optimization
- [ ] Alerts for low balance

---

## **Phase 4: Business Logic Integration**

### **4.1 Course Purchase Flow** ⭐ **PRIORITY 1** ✅ **COMPLETED**
- [x] **File**: `courses/views/payments.py`
- [x] Student gets immediate discount and enrollment
- [x] Create discount request notification for teacher
- [x] Implement teacher EUR vs TEO choice logic
- [x] Handle platform discount absorption when teacher declines
- [x] **Database Migration**: Enhanced CourseEnrollment model with TeoCoin tracking fields
- [x] **URL Configuration**: Payment endpoints properly registered
- [x] **Layer 2 Integration**: Backend proxy architecture fully implemented

### **4.2 Platform Economics** 🔶 **PRIORITY 2**
- [ ] **File**: `courses/utils.py`
- [ ] Calculate platform discount absorption when teacher declines TEO
- [ ] Implement 50% baseline commission with staking tier adjustments
- [ ] Handle reward pool TEO returns and bonus distributions
- [ ] Real-time TEO/EUR rate updates for discount calculations

### **4.3 Notification System** ⭐ **PRIORITY 1** ✅ **COMPLETED**
- [x] **File**: `notifications/services.py`
- [x] Notify teachers: "Student got discount - choose EUR vs TEO"
- [x] Notify students of teacher's decision (accepted/declined TEO)
- [x] Email notifications for 2-hour timeout warnings
- [x] Show teacher staking benefits in notifications
- [x] **Integration**: Notifications sent from payment creation flow
- [x] **Templates**: Support for email notifications

---

## **Phase 5: Testing & Optimization**

### **5.1 Backend Testing** ⭐ **PRIORITY 1** ✅ **COMPLETED**
- [x] **File**: `tests/test_teocoin_discount.py`
- [x] Unit tests for service functions
- [x] Integration tests for smart contract calls
- [x] API endpoint testing
- [x] **Core Tests**: `tests/test_teocoin_core.py` - Essential functionality validated
- [x] **Business Logic**: TEO cost calculations verified
- [x] **Database Models**: CourseEnrollment TeoCoin fields tested

### **5.2 Frontend Testing** 🔶 **PRIORITY 2** ✅ **READY FOR TESTING**
- [x] **Payment Options Fixed**: TeoCoin discount option now visible in PaymentModal
- [x] **Backend API**: PaymentSummaryView updated with pricing_options array
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

### **Week 1: Core Integration** ✅ **COMPLETED**
1. ✅ Create `TeoCoinDiscountService`
2. ✅ Implement backend API endpoints
3. ✅ Fix PaymentModal frontend

### **Week 2: Teacher & Student UX** ✅ **COMPLETED**
4. ✅ Update TeacherDiscountDashboard
5. ✅ Enhanced teacher approval/decline flow with correct business logic
6. ✅ Student discount history (existing component sufficient)

### **Week 3: Database & Payment Integration** ✅ **COMPLETED**
7. ✅ Enhanced CourseEnrollment model with TeoCoin discount tracking
8. ✅ Complete payment system integration with Layer 2 architecture
9. ✅ Database migrations and URL configuration

### **Week 4: Testing & Polish** 🟡 **IN PROGRESS**
10. ⏳ Comprehensive testing and validation
11. ⏳ Gas optimization and monitoring
12. ⏳ Documentation and deployment

## **🔧 Files Created:**
- ✅ `services/teocoin_discount_service.py`
- ✅ `api/teocoin_discount_views.py` 
- ✅ `api/teocoin_discount_urls.py`
- ✅ `frontend/src/services/api/teocoinDiscount.js`
- ⏳ `frontend/src/components/teacher/TeacherDiscountManager.jsx` (updated existing)
- ⏳ `tests/test_teocoin_discount.py`

## **🔧 Files Modified:**
- ✅ `PaymentModal.jsx` (removed MetaMask transactions)
- ✅ `services/urls.py` (registered discount endpoints)
- ✅ `frontend/src/views/dashboard/TeacherDashboard.jsx` (fixed imports)
- ✅ `frontend/src/layouts/AdminLayout/NavBar/NavRight/index.jsx` (fixed imports)
- ⏳ `schoolplatform/settings.py`
- ⏳ `schoolplatform/urls.py`
- ⏳ `courses/views/payments.py`

## **🗑️ Files Deleted:**
- ✅ `services/escrow_service.py` (conflicting business logic)
- ✅ `test_reward_manual.py` (outdated logic)
- ✅ `test_reward_simple.py` (outdated logic)
- ✅ `teacher_accept_demo.py` (wrong business logic)
- ✅ `payment_demonstration.py` (wrong business logic)
- ✅ `frontend/src/services/api/escrow.js` (outdated)

**Phase 1 Complete! Ready for Phase 2: Teacher Dashboard Enhancement**