How It Should Platform Works 

How It Works Now vs *

### **1. Current Architecture**
The system currently has **3 different payment methods** that work independently:

#### **A) Stripe Fiat Payment (EUR)**
- Student pays with credit card
- Backend creates Stripe Payment Intent
- Full EUR amount charged to card
- Student gets enrolled immediately
- Teacher receives EUR commission (85-50% depending on staking tier)
- Platform keeps 15-50% commission

#### **B) Direct TeoCoin Payment** 
- Student approves TeoCoin spending to platform
- Backend executes `transferFrom` to take TeoCoin from student
- TeoCoin distributed: 85% to teacher, 15% to platform
- Student enrolled immediately
- No EUR involved

#### **C) Hybrid Payment (TeoCoin Discount + Stripe)**
- Student can apply TeoCoin discount (10-50%) using TEO tokens
- Student ALWAYS gets the discount and pays reduced EUR price
- Student pays: Discounted EUR + TEO tokens
- **Teacher must decide**: Accept TEO tokens OR get full EUR commission
- Platform absorbs discount cost from commission when teacher declines TEO
- If teacher accepts: gets reduced EUR + TEO tokens (for staking)
- If teacher declines: gets full EUR commission, TEO returns to reward pool

### **2. Current Discount Flow Problems**
```javascript
// Current PaymentModal.jsx - BUGGY CODE
const executeTeoCoinTransfer = async (amount) => {
    // Transfer from student wallet to reward pool (WRONG!)
    const transferTx = await extendedContract.transferFrom(
        walletAddress,        // ❌ Student wallet
        REWARD_POOL_ADDRESS,  // ❌ Goes to reward pool instead of teacher
        amountWei
    );
}
```

**Issues:**
1. Frontend transfers TeoCoin to reward pool, not teacher
2. No smart contract discount system integration
3. Manual escrow system with database-only tracking
4. Teachers must manually approve/reject each discount
5. No automatic teacher bonus calculations

---

## **DETAILED EXAMPLE: How the Discount System Really Works**

### **Scenario: €100 Course with 10% TeoCoin Discount**

#### **Step 1: Student Purchase**
```
Course Price: €100
Platform Commission: 50% = €50
Teacher Commission: 50% = €50

Student applies 10% discount using 100 TEO tokens:
- Student pays: €90 + 100 TEO
- Student gets: Full course access immediately
- Discount amount: €10
```

#### **Step 2: Teacher Decision**
Teacher receives notification with two options:

**Option A: Accept TEO Tokens (Staking Strategy)**
```
Teacher receives:
- EUR: €40 (€50 - €10 discount absorbed by teacher)
- TEO: 100 tokens + 25% bonus = 125 TEO total
- Can stake 125 TEO to increase commission tier
- Future benefit: Higher % on all future courses
```

**Option B: Decline TEO Tokens (Safe EUR Strategy)**
```
Teacher receives:
- EUR: €50 (full commission, platform absorbs the €10 discount)
- TEO: 0 tokens (returned to reward pool)
- No staking opportunity
- Platform loses: €10 from their commission
```

#### **Step 3: Platform Economics**

**If Teacher Accepts TEO:**
```
Platform gets: €50 (original commission)
Platform pays: 25 TEO bonus from reward pool
Student saved: €10
Teacher gets: €40 + 125 TEO
```

**If Teacher Declines TEO:**
```
Platform gets: €40 (€50 - €10 discount absorbed)
Platform receives: 100 TEO back to reward pool
Student saved: €10
Teacher gets: €50 + 0 TEO
```

---

## **New Implementation - What Will Change**

### **1. Smart Contract-Based Discount System**
We'll replace the current buggy discount system with the deployed `TeoCoinDiscount` smart contract:

```solidity
// TeoCoinDiscount.sol - What we'll use
contract TeoCoinDiscount {
    function requestDiscount(address teacher, uint256 amount) external;
    function approveRequest(uint256 requestId) external onlyPlatform;
    function declineRequest(uint256 requestId) external onlyPlatform;
}
```

### **2. Backend Proxy Architecture**
Instead of frontend making blockchain transactions, everything goes through backend:

```javascript
// NEW PaymentModal.jsx - Clean API calls
const handleTeoCoinDiscount = async () => {
    // NO MORE MetaMask transactions!
    const response = await fetch('/api/v1/teocoin-discount/request/', {
        method: 'POST',
        body: JSON.stringify({
            course_id: course.id,
            discount_percentage: 25
        })
    });
    
    // Backend handles all blockchain interactions
    const result = await response.json();
    if (result.success) {
        // Teacher gets notification to approve/reject
        showDiscountPendingMessage();
    }
};
```

### **3. New Service Layer**
```python
# NEW services/teocoin_discount_service.py
class TeoCoinDiscountService:
    def create_discount_request(self, student, teacher, course, percentage):
        # 1. Student gets immediate discount and enrollment
        # 2. Calculate TEO amount and 25% bonus
        # 3. Call smart contract requestDiscount()
        # 4. Platform pays gas fees
        # 5. Notify teacher of EUR vs TEO choice
        
    def approve_discount_request(self, request_id):
        # 1. Teacher chooses TEO tokens over full EUR
        # 2. Transfer TEO from student to teacher (reduced EUR commission)
        # 3. Add 25% bonus from reward pool to teacher
        # 4. Teacher gets: reduced EUR + TEO for staking
        
    def decline_discount_request(self, request_id):
        # 1. Teacher chooses full EUR commission
        # 2. Return TEO to reward pool
        # 3. Platform absorbs discount cost
        # 4. Teacher gets: full EUR, 0 TEO
```

### **4. Teacher Experience Changes**

#### **Current System:**
```jsx
// Current TeacherEscrowManager.jsx - WRONG business logic
{pendingEscrows.map(escrow => (
    <div>
        <p>❌ Student discount depends on your decision</p>
        <p>❌ Student pays full price if you reject</p>
        <p>❌ Manual escrow with 7-day window</p>
        <button onClick={() => acceptEscrow(escrow.id)}>Accept</button>
        <button onClick={() => rejectEscrow(escrow.id)}>Reject</button>
    </div>
))}
```

#### **New System:**
```jsx
// NEW TeacherDiscountManager.jsx - Smart contract integration  
{discountRequests.map(request => (
    <div className="discount-request-card">
        <h4>Student already received {request.percentage}% discount</h4>
        <p><strong>Student:</strong> {request.student_name}</p>
        <p><strong>Course:</strong> {request.course_title} (€{request.original_price})</p>
        <p><strong>Student paid:</strong> €{request.discounted_price} + {request.teo_amount} TEO</p>
        
        <div className="teacher-choice">
            <div className="option-a">
                <h5>🪙 Accept TEO Tokens</h5>
                <p>You get: €{request.reduced_eur} + {request.teo_with_bonus} TEO</p>
                <small>Stake TEO to boost future commissions</small>
                <button onClick={() => acceptTeO(request.id)}>Accept TEO</button>
            </div>
            
            <div className="option-b">
                <h5>💰 Keep Full EUR</h5>
                <p>You get: €{request.full_eur} + 0 TEO</p>
                <small>Platform absorbs discount cost</small>
                <button onClick={() => declineTeO(request.id)}>Keep EUR</button>
            </div>
        </div>
        
        <p className="expires">⏰ Choose within: {request.time_remaining}</p>
    </div>
))}
```

### **5. Gas Fee Management**
#### **Current:** Students pay gas fees for each transaction
#### **New:** Platform pays all gas fees via backend proxy

### **6. Smart Contract Benefits**
- **Automatic teacher bonuses**: 25% extra TEO from reward pool
- **Time-limited requests**: Auto-expire after 2 hours
- **Transparent on-chain**: All approvals recorded on blockchain
- **No manual escrow**: Smart contract handles everything
- **Platform-only control**: Only platform can approve/decline (prevents teacher direct manipulation)

---

## **Summary of Changes**

| **Current System** | **New Implementation** |
|-------------------|----------------------|
| ❌ Buggy frontend transfers | ✅ Backend proxy handles all blockchain |
| ❌ Manual database escrow | ✅ Smart contract automation |
| ❌ Students pay gas fees | ✅ Platform pays all gas fees |
| ❌ 7-day decision window | ✅ 2-hour time limit |
| ❌ No teacher bonuses | ✅ Automatic 25% teacher bonus |
| ❌ Direct teacher approval | ✅ Platform-mediated approval via web interface |
| ❌ Address mapping bugs | ✅ Clean API-based flow |

The new system will be **gas-free for users**, **automated via smart contracts**, and provide a **Web2-like experience** while maintaining **blockchain security** and **transparency**.