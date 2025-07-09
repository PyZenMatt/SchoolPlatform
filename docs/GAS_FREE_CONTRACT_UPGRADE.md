# 🚀 Gas-Free TeoCoin Discount Contract Upgrade

## 💡 **Key Insight: Gas = MATIC, Not TEO**

**The Problem**: Students need **MATIC tokens** to pay gas fees for blockchain transactions, even though they're only using **TEO tokens** for discounts.

**The Solution**: Platform pays all **MATIC gas fees**, students only need **TEO tokens**.

## 🏦 **Reward Pool as Escrow - Best Practice**

**Why use Reward Pool instead of Contract as escrow?**

✅ **Simpler Architecture**: One unified TEO pool instead of multiple locations
✅ **Gas Efficiency**: Single transfers instead of multi-step transfers  
✅ **Easier Accounting**: Platform tracks all TEO in one place
✅ **Less Contract Code**: Simpler logic, fewer potential bugs
✅ **Unified TEO Management**: All TEO flows go through reward pool

**TEO Flow with Reward Pool Escrow:**
```
Student → Reward Pool → (Teacher or Student refund)
```
Instead of:
```
Student → Contract → Reward Pool → Teacher (more complex)
```

## 🎯 **Required Changes for True Gas-Free Experience**

### **Current Problem:**
Students must pay **MATIC gas fees** for:
1. `approve()` TEO tokens to discount contract (costs MATIC)
2. `createDiscountRequest()` which calls `transferFrom()` (costs MATIC)

**Result**: Students need both TEO tokens AND MATIC for gas fees

### **Solution: Platform Pays All Gas Fees (MATIC) + Handles TEO Flow**

## ⛽ **When MATIC Gas Fees Are Paid (Platform's Responsibility)**

### **Student Workflow (100% Gas-Free for Student):**

1. **Student Action**: Clicks "Use TEO Discount" in frontend
   - **MATIC Gas**: ❌ **ZERO** - Student pays nothing
   - **Student Only**: Signs message off-chain (free signature)

2. **Platform Action**: Calls `createDiscountRequestGasFree()`
   - **MATIC Gas**: ✅ **PLATFORM PAYS** ~0.002-0.005 MATIC
   - **TEO Transfer**: Platform executes `transferFrom(student, rewardPool, teoCost)`
   - **Who Pays**: Platform's backend wallet pays MATIC gas

3. **Teacher Decision**: Approve/Decline via platform
   - **MATIC Gas**: ✅ **PLATFORM PAYS** ~0.001-0.003 MATIC  
   - **Who Pays**: Platform's backend wallet pays MATIC gas

4. **TEO Settlement**: Transfer to teacher OR stays in reward pool
   - **MATIC Gas**: ✅ **PLATFORM PAYS** ~0.001-0.003 MATIC (only if teacher accepts)
   - **Who Pays**: Platform's backend wallet pays MATIC gas
   - **Note**: If teacher declines/expires, no transaction needed - TEO stays in reward pool

### **Total MATIC Cost Per Discount Request:**
- **Student Pays**: **0 MATIC** (100% gas-free)
- **Platform Pays**: 
  - **Teacher ACCEPTS**: **~0.003-0.008 MATIC** (2 transactions: create + approve)
  - **Teacher DECLINES**: **~0.002-0.005 MATIC** (1 transaction: create only)
- **Platform Cost**: **~$0.001-0.004 USD** per discount (at current MATIC prices)

### **Platform's MATIC Wallet Management:**
```javascript
// Backend service manages platform's MATIC wallet
const platformWallet = new ethers.Wallet(PLATFORM_PRIVATE_KEY, provider);
const contractWithSigner = discountContract.connect(platformWallet);

// Platform pays MATIC gas for student's discount request
const tx = await contractWithSigner.createDiscountRequestGasFree(
    studentAddress,
    teacherAddress, 
    courseId,
    coursePrice,
    discountPercent,
    studentSignature
); // Platform's wallet pays ~0.002-0.005 MATIC gas fee
```

## 📋 **New Contract Architecture**

### **Core Changes:**
1. **Platform pays all MATIC gas fees** for student transactions
2. **Student only needs TEO tokens** (no MATIC required)
3. **Platform executes transactions** on student's behalf using signatures
4. **TEO debt tracked** until settled or forgiven

---

## 🔧 **Updated Smart Contract Structure**

### **1. New State Variables**
```solidity
// Gas-free mode toggle
bool public gasFreeMode = true;

// Optional: Track request statistics
mapping(address => uint256) public studentRequestCount;
mapping(address => uint256) public teacherRequestCount;
```

### **2. New Events**
```solidity
event GasFreeModeToggled(bool enabled);
event StudentTeoDeducted(address indexed student, uint256 requestId, uint256 teoAmount);
```

### **3. Core Gas-Free Method**
```solidity
/**
 * @dev Create discount request with platform paying MATIC gas fees (GAS-FREE for student)
 * Platform pays MATIC for transaction, handles TEO transfers, tracks student TEO debt
 */
function createDiscountRequestGasFree(
    address student,
    address teacher,
    uint256 courseId,
    uint256 coursePrice,
    uint256 discountPercent,
    bytes memory studentSignature
) external onlyPlatform whenNotPaused nonReentrant returns (uint256) {
    require(gasFreeMode, "Gas-free mode disabled");
    require(student != address(0), "Student address cannot be zero");
    require(teacher != address(0), "Teacher address cannot be zero");
    require(coursePrice > 0, "Course price must be positive");
    require(discountPercent >= 5 && discountPercent <= 15, "Invalid discount percent");
    
    // Calculate TEO amounts
    (uint256 teoCost, uint256 teacherBonus) = calculateTeoCost(coursePrice, discountPercent);
    
    // Verify student has sufficient TEO balance (but don't transfer yet)
    require(teoToken.balanceOf(student) >= teoCost, "Student insufficient TEO balance");
    
    // Verify reward pool has sufficient balance for teacher bonus
    require(teoToken.balanceOf(rewardPool) >= teacherBonus, "Insufficient reward pool balance");
    
    // Verify student signature (off-chain pre-approval for TEO usage)
    require(_verifyStudentSignature(student, courseId, teoCost, studentSignature), "Invalid student signature");
    
    // IMMEDIATELY DEDUCT TEO FROM STUDENT TO REWARD POOL (platform pays MATIC gas)
    // Reward pool acts as escrow - simpler than contract holding TEO
    require(
        teoToken.transferFrom(student, rewardPool, teoCost),
        "Student TEO transfer to reward pool failed"
    );
    
    // Create request
    uint256 requestId = ++_requestIdCounter;
    uint256 deadline = block.timestamp + REQUEST_TIMEOUT;
    
    discountRequests[requestId] = DiscountRequest({
        requestId: requestId,
        student: student,
        teacher: teacher,
        courseId: courseId,
        coursePrice: coursePrice,
        discountPercent: discountPercent,
        teoCost: teoCost,
        teacherBonus: teacherBonus,
        createdAt: block.timestamp,
        deadline: deadline,
        status: DiscountStatus.Pending,
        studentSignature: studentSignature
    });
    
    // Track requests
    studentRequests[student].push(requestId);
    teacherRequests[teacher].push(requestId);
    
    // NOTE: Student TEO already in reward pool (escrow)
    // Student ALWAYS gets discount regardless of teacher decision
    
    emit DiscountRequested(requestId, student, teacher, courseId, discountPercent, teoCost);
    emit StudentTeoDeducted(student, requestId, teoCost);
    
    return requestId;
}
```

### **4. Updated Approve Method**
```solidity
/**
 * @dev Approve discount request - Teacher accepts TEO payment
 * TEO flows from escrow to teacher + bonus from reward pool
 * Student debt remains (to be settled separately)
 */
function approveDiscountRequest(uint256 requestId) 
    external 
    onlyPlatform 
    whenNotPaused 
    nonReentrant 
    validRequest(requestId) 
{
    DiscountRequest storage request = discountRequests[requestId];
    
    // Update status
    request.status = DiscountStatus.Approved;
    
    // Execute transfers for TEACHER ACCEPTS scenario:
    // Teacher gets: reduced EUR + student TEO + bonus TEO
    // Platform gets: higher EUR (absorbs discount in EUR, gains TEO)
    require(
        teoToken.transferFrom(rewardPool, request.teacher, request.teoCost + request.teacherBonus),
        "Reward pool to teacher transfer failed"
    );
    
    // Student's TEO + bonus goes to teacher from reward pool
    
    emit DiscountApproved(
        requestId, 
        request.student, 
        request.teacher, 
        request.teoCost, 
        request.teacherBonus
    );
}
```

### **5. Updated Decline Method**
```solidity
/**
 * @dev Decline discount request - Teacher refuses TEO payment
 * Teacher gets full EUR commission, platform keeps TEO (absorbs discount cost)
 * Student ALWAYS gets discount regardless
 */
function declineDiscountRequest(uint256 requestId, string memory reason) 
    external 
    onlyPlatform 
    whenNotPaused 
    validRequest(requestId) 
{
    DiscountRequest storage request = discountRequests[requestId];
    request.status = DiscountStatus.Declined;
    
    // PLATFORM KEEPS TEO (teacher declined, platform absorbs discount cost)
    // TEO stays in reward pool, teacher gets full EUR commission
    // Student already got discount, no refund needed
    
    emit DiscountDeclined(requestId, request.student, request.teacher, reason);
}
```

### **6. Updated Expiry Processing**
```solidity
/**
 * @dev Process expired requests - Teacher gets full EUR, platform keeps TEO
 */
function processExpiredRequests(uint256[] memory requestIds) external whenNotPaused {
    for (uint256 i = 0; i < requestIds.length; i++) {
        uint256 requestId = requestIds[i];
        if (requestId <= _requestIdCounter && 
            discountRequests[requestId].status == DiscountStatus.Pending &&
            block.timestamp > discountRequests[requestId].deadline) {
            
            DiscountRequest storage request = discountRequests[requestId];
            request.status = DiscountStatus.Expired;
            
            // PLATFORM KEEPS TEO (timeout = same as decline)
            // Teacher gets full EUR commission, platform absorbs discount cost
            // Student already got discount, no action needed
            
            emit DiscountExpired(requestId, request.student, request.teacher);
        }
    }
}
```

### **7. Admin Controls**
```solidity
/**
 * @dev Toggle gas-free mode (owner only)
 */
function setGasFreeMode(bool enabled) external onlyOwner {
    gasFreeMode = enabled;
    emit GasFreeModeToggled(enabled);
}

/**
 * @dev Get student's total request count
 */
function getStudentRequestCount(address student) external view returns (uint256) {
    return studentRequestCount[student];
}

/**
 * @dev Get teacher's total request count  
 */
function getTeacherRequestCount(address teacher) external view returns (uint256) {
    return teacherRequestCount[teacher];
}
```

---

## 🔄 **New Student Workflow (Gas-Free)**

### **Student Experience (NO MetaMask Transactions):**
1. **Student clicks "Use TEO Discount"** → Opens discount modal
2. **Student confirms TEO amount** → Reviews: "500 TEO will be deducted for 10% discount"
3. **Student signs message in MetaMask** → FREE signature (NOT a transaction, NO gas)
4. **Platform processes instantly** → Blockchain transaction executed by platform
5. **Student ALWAYS gets discount** → Course price reduced immediately

**Student MetaMask Experience:**
```
MetaMask Popup: "Sign Message" (NOT "Confirm Transaction")
- Message: "Approve 500 TEO for course discount"
- Gas Fee: None (this is just a signature)
- Click: "Sign" (NOT "Confirm")
```

### **Teacher Experience (NO MetaMask Transactions):**
1. **Teacher receives notification** → Email: "Student requested TEO discount"
2. **Teacher opens platform** → Sees pending discount requests
3. **Teacher clicks "Accept TEO" or "Keep EUR"** → Simple web button
4. **Platform processes decision** → Blockchain transaction executed by platform
5. **Teacher receives payment** → TEO tokens or EUR commission

**Teacher Decision Interface:**
```
Discount Request from Student John
Course: Advanced React (€100)
Student's Offer: 500 TEO + 250 bonus TEO = 750 TEO total

[Accept TEO Payment] [Keep EUR Payment]
   (750 TEO)         (€50 commission)
```

## 🏗️ **Platform Backend Handles All Blockchain Complexity**

### **TEO Flow (MATIC gas paid by platform, Student ALWAYS gets discount):**
- **Request Created**: Student TEO → Reward Pool (platform pays MATIC)
- **Teacher ACCEPTS**: Reward Pool → Teacher (student TEO + bonus) (platform pays MATIC)  
- **Teacher DECLINES**: TEO stays in Reward Pool, platform keeps it (platform pays MATIC)
- **Timeout**: TEO stays in Reward Pool, platform keeps it (platform pays MATIC)

### **EUR Flow Examples (€100 course, 10% discount, Bronze teacher = 50% commission):**

**Teacher DECLINES TEO:**
- Student: Pays €90, gets course
- Teacher: Gets €50 (50% of full €100 course price)  
- Platform: Gets €50 + keeps student's 500 TEO (absorbs €10 discount cost)

**Teacher ACCEPTS TEO:**
- Student: Pays €90, gets course
- Teacher: Gets €45 (50% of €90) + student's 500 TEO + 250 bonus TEO = 750 TEO total
- Platform: Gets €45 - pays 250 bonus TEO from reward pool

## 🏗️ **Backend Implementation: Platform Pays MATIC Gas**

### **Django Service Implementation:**
```python
# services/teocoin_discount_service.py
class TeoCoinDiscountService:
    def __init__(self):
        # Platform's wallet that pays all MATIC gas fees
        self.platform_account = Account.from_key(settings.PLATFORM_PRIVATE_KEY)
        self.w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
        self.contract = self.w3.eth.contract(
            address=settings.TEOCOIN_DISCOUNT_CONTRACT,
            abi=DISCOUNT_CONTRACT_ABI
        )
    
    def create_gas_free_discount_request(self, student_address, teacher_address, 
                                       course_id, course_price, discount_percent, 
                                       student_signature):
        """
        Platform pays MATIC gas fees for student's discount request
        Student only needs TEO tokens, no MATIC required
        """
        
        # Build transaction (platform pays gas)
        gas_price = self.w3.eth.gas_price
        nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
        
        # Platform wallet pays MATIC gas for this transaction
        transaction = self.contract.functions.createDiscountRequestGasFree(
            student_address,
            teacher_address,
            course_id,
            course_price,
            discount_percent,
            student_signature
        ).build_transaction({
            'from': self.platform_account.address,
            'gas': 200000,  # Platform pays ~0.002-0.005 MATIC
            'gasPrice': gas_price,
            'nonce': nonce,
        })
        
        # Sign and send transaction (platform pays MATIC)
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, 
            self.platform_account.key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Platform's MATIC balance decreased by gas fee
        # Student's TEO balance decreased by teoCost
        # Student pays ZERO MATIC
        
        return tx_hash.hex()
    
    def approve_discount_request(self, request_id):
        """Platform pays MATIC gas for teacher approval"""
        # Similar implementation - platform wallet pays gas
        pass
    
    def decline_discount_request(self, request_id, reason):
        """Platform pays MATIC gas for teacher decline"""  
        # Similar implementation - platform wallet pays gas
        pass
```

### **Platform MATIC Balance Management:**
```python
# Platform needs to maintain MATIC balance for gas fees
def check_platform_matic_balance():
    balance = w3.eth.get_balance(platform_account.address)
    matic_balance = w3.from_wei(balance, 'ether')
    
    if matic_balance < 1.0:  # Less than 1 MATIC
        send_alert("Platform MATIC balance low: {} MATIC".format(matic_balance))
        # Auto-refill MATIC balance or alert admin
```

## 🖥️ **Frontend Implementation: User Experience**

### **Student Frontend (React/JavaScript):**
```javascript
// components/DiscountModal.jsx
const DiscountModal = ({ courseId, coursePrice, teacherAddress }) => {
    const [loading, setLoading] = useState(false);
    
    const handleRequestDiscount = async () => {
        setLoading(true);
        
        // 1. Student clicks "Request Discount" - NO MetaMask transaction
        const discountPercent = 10; // 10% discount
        const teoCost = calculateTeoCost(coursePrice, discountPercent);
        
        // 2. Create message for student to sign (FREE signature)
        const message = {
            student: userAddress,
            teacher: teacherAddress,
            courseId: courseId,
            coursePrice: coursePrice,
            discountPercent: discountPercent,
            teoCost: teoCost,
            timestamp: Date.now()
        };
        
        try {
            // 3. Student signs message (NO MATIC gas, just signature)
            const signature = await window.ethereum.request({
                method: 'personal_sign',
                params: [JSON.stringify(message), userAddress]
            });
            
            // 4. Send to backend (platform handles blockchain transaction)
            const response = await fetch('/api/discount/create-gas-free/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    student: userAddress,
                    teacher: teacherAddress,
                    courseId: courseId,
                    coursePrice: coursePrice,
                    discountPercent: discountPercent,
                    signature: signature
                })
            });
            
            if (response.ok) {
                // Discount applied immediately, course price reduced
                alert('Discount applied! Course price reduced by 10%');
                window.location.reload();
            }
        } catch (error) {
            console.error('Error:', error);
        }
        
        setLoading(false);
    };
    
    return (
        <div className="discount-modal">
            <h3>Use TEO Discount</h3>
            <p>Pay {teoCost} TEO for 10% discount</p>
            <p>Course price: €{coursePrice} → €{coursePrice * 0.9}</p>
            
            <button onClick={handleRequestDiscount} disabled={loading}>
                {loading ? 'Processing...' : 'Sign & Apply Discount'}
            </button>
            
            <small>* No gas fees required, only signature needed</small>
        </div>
    );
};
```

### **Teacher Frontend (React/JavaScript):**
```javascript
// components/TeacherDashboard.jsx
const TeacherDiscountRequests = () => {
    const [requests, setRequests] = useState([]);
    
    const handleDecision = async (requestId, decision) => {
        // Teacher clicks button - NO MetaMask needed
        const response = await fetch(`/api/discount/${requestId}/decision/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decision: decision }) // 'approve' or 'decline'
        });
        
        if (response.ok) {
            alert(`Request ${decision}d successfully!`);
            // Refresh requests
            fetchRequests();
        }
    };
    
    return (
        <div className="teacher-requests">
            <h3>Student Discount Requests</h3>
            {requests.map(request => (
                <div key={request.id} className="request-card">
                    <h4>Student: {request.student_name}</h4>
                    <p>Course: {request.course_name} (€{request.course_price})</p>
                    <p>Student offers: {request.teo_cost} TEO</p>
                    <p>You would receive: {request.teo_cost + request.teacher_bonus} TEO total</p>
                    
                    <div className="decision-buttons">
                        <button 
                            onClick={() => handleDecision(request.id, 'approve')}
                            className="accept-btn"
                        >
                            Accept TEO Payment
                            <small>({request.teo_cost + request.teacher_bonus} TEO)</small>
                        </button>
                        
                        <button 
                            onClick={() => handleDecision(request.id, 'decline')}
                            className="decline-btn"
                        >
                            Keep EUR Payment
                            <small>(€{request.course_price * 0.5} commission)</small>
                        </button>
                    </div>
                    
                    <small>* No MetaMask required, platform handles transaction</small>
                </div>
            ))}
        </div>
    );
};
```

---
- Teacher: Gets €50 (50% of original €100)  
- Platform: Gets €40 + keeps 100 TEO (absorbs €10 discount cost)

**Teacher ACCEPTS TEO:**
- Student: Pays €90, gets course
- Teacher: Gets €40 + 125 TEO (100 + 25% bonus)
- Platform: Gets €50 (higher EUR but pays TEO bonus)

---

## 📋 **Implementation Checklist**

### **Smart Contract Updates:**
- [ ] Add gas-free mode toggle
- [ ] Add `createDiscountRequestGasFree()` method  
- [ ] Update `approveDiscountRequest()` (same as before)
- [ ] Update `declineDiscountRequest()` for no-refund logic
- [ ] Update `processExpiredRequests()` for no-refund logic
- [ ] Add admin controls

### **Backend Service Updates:**
- [ ] Update `TeoCoinDiscountService` to use gas-free method
- [ ] Update payment flow to handle immediate deduction
- [ ] Add pre-transaction TEO balance checks

### **Frontend Updates:**
- [ ] Remove MetaMask approval step for students
- [ ] Update UI to show "immediate TEO deduction + gas-free" experience
- [ ] Show clear policy: TEO deducted immediately, student always gets discount
- [ ] Remove any refund-related UI components

---

## 🎯 **Benefits of This Approach**

- ✅ **100% Gas-Free for Students** - No MATIC needed, no MetaMask transactions
- ✅ **Platform Pays All MATIC Gas** - Students only need TEO tokens  
- ✅ **Student ALWAYS Gets Discount** - Clear, guaranteed benefit
- ✅ **Reward Pool Escrow** - Unified TEO management, simpler architecture
- ✅ **Fair Teacher Choice** - EUR vs TEO, both options have benefits
- ✅ **Platform Economics** - Absorbs discount cost, gains TEO when declined
- ✅ **Gas Efficient** - Single transfers instead of multi-step
- ✅ **Backward Compatible** - Old method still works if needed
- ✅ **Teacher Workflow Unchanged** - Same decision process

## 🦊 **TEO Tokens & Staking in MetaMask**

### **TEO Token Display in MetaMask:**
Both students and teachers have TEO tokens visible in their MetaMask wallets:

```javascript
// Add TEO token to MetaMask for visibility
const addTeoToken = async () => {
    await window.ethereum.request({
        method: 'wallet_watchAsset',
        params: {
            type: 'ERC20',
            options: {
                address: '0xYOUR_TEO_CONTRACT_ADDRESS', // Deployed TEO contract
                symbol: 'TEO',
                decimals: 18,
                image: 'https://schoolplatform.com/teo-logo.png'
            }
        }
    });
};
```

### **Staking System (Teachers Only) - Requires MetaMask:**

**Unlike the gas-free discount system, staking requires MetaMask transactions:**

#### **Teacher Staking Process:**
1. **Teacher opens staking page** → Sees current TEO balance and staking tiers
2. **Teacher enters staking amount** → "Stake 1000 TEO to reach Bronze tier"
3. **Teacher clicks "Stake TEO"** → MetaMask opens with transaction
4. **Teacher pays MATIC gas** → Confirms transaction in MetaMask
5. **Staking tier updated** → Commission rate improves automatically

#### **Staking MetaMask Experience:**
```
🦊 MetaMask
Confirm Transaction (Staking requires gas)
┌─────────────────────────────────────┐
│ To: Staking Contract                │
│ Function: stakeTokens(1000 TEO)     │
│ Gas Fee: ~0.002 MATIC (~$0.001)     │
│ ⚠️ Teacher pays gas for staking     │
└─────────────────────────────────────┘
    [Reject]    [Confirm]
```

#### **Staking Frontend Implementation:**
```javascript
// Teacher staking interface (requires MetaMask)
const StakingInterface = () => {
    const [stakingAmount, setStakingAmount] = useState('');
    
    const handleStake = async () => {
        try {
            // Teacher transaction - requires MetaMask and MATIC
            const provider = new ethers.providers.Web3Provider(window.ethereum);
            const signer = provider.getSigner();
            const stakingContract = new ethers.Contract(
                STAKING_CONTRACT_ADDRESS, 
                STAKING_ABI, 
                signer
            );
            
            // Teacher pays gas for staking transaction
            const tx = await stakingContract.stakeTokens(
                ethers.utils.parseEther(stakingAmount)
            );
            
            await tx.wait();
            alert('Staking successful! Your tier has been updated.');
        } catch (error) {
            console.error('Staking failed:', error);
        }
    };
    
    return (
        <div className="staking-interface">
            <h3>Stake TEO to Improve Commission Rate</h3>
            <p>Current Tier: Bronze (50% commission)</p>
            <p>TEO Balance: {teoBalance} TEO</p>
            
            <input 
                type="number" 
                value={stakingAmount}
                onChange={(e) => setStakingAmount(e.target.value)}
                placeholder="Amount to stake"
            />
            
            <button onClick={handleStake}>
                Stake TEO (Requires MetaMask)
            </button>
            
            <small>* Teacher pays MATIC gas fee for staking transaction</small>
        </div>
    );
};
```

### **Two Different Systems:**

#### **Discount System (Gas-Free):**
- **Student**: Signs message only (NO gas, NO MetaMask transaction)
- **Teacher**: Web button only (NO gas, NO MetaMask transaction)
- **Platform**: Pays all MATIC gas fees

#### **Staking System (Traditional):**
- **Teacher**: MetaMask transaction required (teacher pays MATIC gas)
- **Student**: No staking available (only teachers can stake)
- **Platform**: No gas fees paid

### **Why Different Approaches?**

1. **Discount**: High frequency, small amounts → Gas-free for better UX
2. **Staking**: Low frequency, large amounts → Traditional approach acceptable
3. **TEO Visibility**: Both systems show TEO tokens in MetaMask normally
4. **Balance Updates**: MetaMask shows real-time TEO balance changes

## 🚀 **BONUS: Gas-Free Staking System (Optional Enhancement)**

### **Making Staking Gas-Free Too:**

We can apply the same gas-free approach to staking! This would eliminate ALL MATIC requirements:

#### **Gas-Free Staking Contract Methods:**
```solidity
/**
 * @dev Gas-free staking - Platform pays MATIC, teacher signs message
 * ANTI-ABUSE: Time restrictions prevent gaming the system
 */
function stakeTokensGasFree(
    address teacher,
    uint256 amount,
    bytes memory teacherSignature
) external onlyPlatform whenNotPaused nonReentrant {
    require(gasFreeMode, "Gas-free mode disabled");
    require(teacher != address(0), "Teacher address cannot be zero");
    require(amount > 0, "Amount must be positive");
    
    // ANTI-ABUSE: Check staking frequency limits
    require(_canStake(teacher), "Staking too frequently - max 2 stakes per 7 days");
    
    // Verify teacher signature for staking approval
    require(_verifyTeacherStakingSignature(teacher, amount, teacherSignature), "Invalid teacher signature");
    
    // Check teacher has sufficient TEO balance
    require(teoToken.balanceOf(teacher) >= amount, "Insufficient TEO balance");
    
    // PLATFORM PAYS MATIC GAS - Teacher pays nothing
    // Transfer TEO from teacher to staking pool via reward pool
    require(
        teoToken.transferFrom(teacher, stakingPool, amount),
        "TEO staking transfer failed"
    );
    
    // Update staking records
    teacherStakes[teacher] += amount;
    totalStaked += amount;
    
    // ANTI-ABUSE: Record staking action with timestamp
    _recordStakingAction(teacher, amount, true); // true = stake
    
    // Update teacher tier based on new staking amount
    _updateTeacherTier(teacher);
    
    emit TokensStaked(teacher, amount, block.timestamp);
}

/**
 * @dev Gas-free unstaking with LOCKUP PERIOD - Platform pays MATIC, teacher signs message
 * ANTI-ABUSE: 7-day minimum lockup + cooldown periods
 */
function unstakeTokensGasFree(
    address teacher,
    uint256 amount,
    bytes memory teacherSignature
) external onlyPlatform whenNotPaused nonReentrant {
    require(gasFreeMode, "Gas-free mode disabled");
    require(teacher != address(0), "Teacher address cannot be zero");
    require(amount > 0, "Amount must be positive");
    require(teacherStakes[teacher] >= amount, "Insufficient staked amount");
    
    // ANTI-ABUSE: Check unstaking eligibility (lockup + cooldown)
    require(_canUnstake(teacher, amount), "Cannot unstake: lockup period or cooldown active");
    
    // Verify teacher signature for unstaking approval
    require(_verifyTeacherUnstakingSignature(teacher, amount, teacherSignature), "Invalid teacher signature");
    
    // PLATFORM PAYS MATIC GAS - Teacher pays nothing
    // Transfer TEO from staking pool back to teacher
    require(
        teoToken.transferFrom(stakingPool, teacher, amount),
        "TEO unstaking transfer failed"
    );
    
    // Update staking records
    teacherStakes[teacher] -= amount;
    totalStaked -= amount;
    
    // ANTI-ABUSE: Record unstaking action with timestamp + start cooldown
    _recordStakingAction(teacher, amount, false); // false = unstake
    
    // Update teacher tier based on new staking amount
    _updateTeacherTier(teacher);
    
    emit TokensUnstaked(teacher, amount, block.timestamp);
}

/**
 * @dev Anti-abuse tracking structures
 */
struct StakingRestrictions {
    uint256 lastStakeTime;
    uint256 lastUnstakeTime;
    uint256 stakingCount7Days;
    uint256 unstakingCount7Days;
    uint256 firstStakeInWindow;
    uint256 firstUnstakeInWindow;
}

mapping(address => StakingRestrictions) public teacherRestrictions;

// Anti-abuse constants
uint256 public constant LOCKUP_PERIOD = 7 days;          // Minimum time before unstaking
uint256 public constant UNSTAKE_COOLDOWN = 7 days;       // Cooldown between unstakes
uint256 public constant STAKE_COOLDOWN = 3 days;         // Cooldown between stakes
uint256 public constant MAX_STAKES_PER_7_DAYS = 2;       // Max stakes per week
uint256 public constant MAX_UNSTAKES_PER_7_DAYS = 1;     // Max unstakes per week

/**
 * @dev Check if teacher can stake (frequency limits)
 */
function _canStake(address teacher) internal view returns (bool) {
    StakingRestrictions memory restrictions = teacherRestrictions[teacher];
    
    // Reset weekly counter if 7 days passed
    if (block.timestamp >= restrictions.firstStakeInWindow + 7 days) {
        return true; // New 7-day window
    }
    
    // Check if under weekly limit
    if (restrictions.stakingCount7Days >= MAX_STAKES_PER_7_DAYS) {
        return false; // Hit weekly limit
    }
    
    // Check cooldown between stakes
    if (block.timestamp < restrictions.lastStakeTime + STAKE_COOLDOWN) {
        return false; // Still in cooldown
    }
    
    return true;
}

/**
 * @dev Check if teacher can unstake (lockup + cooldown)
 */
function _canUnstake(address teacher, uint256 amount) internal view returns (bool) {
    StakingRestrictions memory restrictions = teacherRestrictions[teacher];
    
    // Must respect minimum lockup period
    if (block.timestamp < restrictions.lastStakeTime + LOCKUP_PERIOD) {
        return false; // Still in lockup period
    }
    
    // Check unstaking cooldown
    if (block.timestamp < restrictions.lastUnstakeTime + UNSTAKE_COOLDOWN) {
        return false; // Still in unstaking cooldown
    }
    
    // Reset weekly counter if 7 days passed
    if (block.timestamp < restrictions.firstUnstakeInWindow + 7 days) {
        // Within 7-day window, check limit
        if (restrictions.unstakingCount7Days >= MAX_UNSTAKES_PER_7_DAYS) {
            return false; // Hit weekly unstaking limit
        }
    }
    
    return true;
}

/**
 * @dev Record staking/unstaking action for anti-abuse tracking
 */
function _recordStakingAction(address teacher, uint256 amount, bool isStaking) internal {
    StakingRestrictions storage restrictions = teacherRestrictions[teacher];
    
    if (isStaking) {
        // Reset weekly counter if new 7-day window
        if (block.timestamp >= restrictions.firstStakeInWindow + 7 days) {
            restrictions.stakingCount7Days = 0;
            restrictions.firstStakeInWindow = block.timestamp;
        }
        
        restrictions.lastStakeTime = block.timestamp;
        restrictions.stakingCount7Days++;
        
        if (restrictions.firstStakeInWindow == 0) {
            restrictions.firstStakeInWindow = block.timestamp;
        }
    } else {
        // Reset weekly counter if new 7-day window
        if (block.timestamp >= restrictions.firstUnstakeInWindow + 7 days) {
            restrictions.unstakingCount7Days = 0;
            restrictions.firstUnstakeInWindow = block.timestamp;
        }
        
        restrictions.lastUnstakeTime = block.timestamp;
        restrictions.unstakingCount7Days++;
        
        if (restrictions.firstUnstakeInWindow == 0) {
            restrictions.firstUnstakeInWindow = block.timestamp;
        }
    }
}

/**
 * @dev Get teacher's staking restrictions info
 */
function getStakingRestrictions(address teacher) external view returns (
    bool canStake,
    bool canUnstake,
    uint256 nextStakeTime,
    uint256 nextUnstakeTime,
    uint256 stakesUsed7Days,
    uint256 unstakesUsed7Days
) {
    canStake = _canStake(teacher);
    canUnstake = _canUnstake(teacher, 1); // Check for any amount
    
    StakingRestrictions memory restrictions = teacherRestrictions[teacher];
    
    // Calculate next available times
    nextStakeTime = restrictions.lastStakeTime + STAKE_COOLDOWN;
    nextUnstakeTime = max(
        restrictions.lastStakeTime + LOCKUP_PERIOD,
        restrictions.lastUnstakeTime + UNSTAKE_COOLDOWN
    );
    
    // Weekly usage
    if (block.timestamp >= restrictions.firstStakeInWindow + 7 days) {
        stakesUsed7Days = 0;
    } else {
        stakesUsed7Days = restrictions.stakingCount7Days;
    }
    
    if (block.timestamp >= restrictions.firstUnstakeInWindow + 7 days) {
        unstakesUsed7Days = 0;
    } else {
        unstakesUsed7Days = restrictions.unstakingCount7Days;
    }
}
```

## 🛡️ **Anti-Abuse Staking Rules**

### **Staking Restrictions:**
- **Max Frequency**: 2 stakes per 7 days
- **Cooldown**: 3 days between stakes  
- **Purpose**: Prevent micro-staking to game commission rates

### **Unstaking Restrictions:**
- **Lockup Period**: 7 days minimum after staking
- **Max Frequency**: 1 unstake per 7 days
- **Cooldown**: 7 days between unstakes
- **Purpose**: Prevent gaming before course purchases

### **Benefits of These Restrictions:**

✅ **Prevents Tier Gaming**: Can't stake right before big purchase and unstake after  
✅ **Stable Teacher Tiers**: More predictable commission rates for students  
✅ **Fair Competition**: Teachers can't manipulate timing for unfair advantage  
✅ **Encourages Long-term Commitment**: Rewards consistent staking behavior  
✅ **Platform Stability**: Reduces frequent tier changes and system gaming
```

#### **Gas-Free Staking Frontend:**
```javascript
// Gas-free staking interface with anti-abuse restrictions
const GasFreeStakingInterface = () => {
    const [stakingAmount, setStakingAmount] = useState('');
    const [unstakingAmount, setUnstakingAmount] = useState('');
    const [loading, setLoading] = useState(false);
    const [restrictions, setRestrictions] = useState(null);
    
    // Fetch staking restrictions on component load
    useEffect(() => {
        fetchStakingRestrictions();
    }, []);
    
    const fetchStakingRestrictions = async () => {
        const response = await fetch(`/api/staking/restrictions/${teacherAddress}/`);
        const data = await response.json();
        setRestrictions(data);
    };
    
    const handleGasFreeStake = async () => {
        if (!restrictions?.canStake) {
            alert('Cannot stake: frequency limit or cooldown active');
            return;
        }
        
        setLoading(true);
        
        try {
            const stakingMessage = {
                teacher: teacherAddress,
                action: 'stake',
                amount: stakingAmount,
                timestamp: Date.now()
            };
            
            const signature = await window.ethereum.request({
                method: 'personal_sign',
                params: [JSON.stringify(stakingMessage), teacherAddress]
            });
            
            const response = await fetch('/api/staking/stake-gas-free/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    teacher: teacherAddress,
                    amount: stakingAmount,
                    signature: signature
                })
            });
            
            if (response.ok) {
                alert('Staking successful! Your tier has been updated.');
                fetchStakingInfo();
                fetchStakingRestrictions();
            }
        } catch (error) {
            console.error('Gas-free staking failed:', error);
        }
        
        setLoading(false);
    };
    
    const handleGasFreeUnstake = async () => {
        if (!restrictions?.canUnstake) {
            alert('Cannot unstake: lockup period or cooldown active');
            return;
        }
        
        setLoading(true);
        
        try {
            const unstakingMessage = {
                teacher: teacherAddress,
                action: 'unstake',
                amount: unstakingAmount,
                timestamp: Date.now()
            };
            
            const signature = await window.ethereum.request({
                method: 'personal_sign',
                params: [JSON.stringify(unstakingMessage), teacherAddress]
            });
            
            const response = await fetch('/api/staking/unstake-gas-free/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    teacher: teacherAddress,
                    amount: unstakingAmount,
                    signature: signature
                })
            });
            
            if (response.ok) {
                alert('Unstaking successful! Your tier has been updated.');
                fetchStakingInfo();
                fetchStakingRestrictions();
            }
        } catch (error) {
            console.error('Gas-free unstaking failed:', error);
        }
        
        setLoading(false);
    };
    
    const formatTimeRemaining = (timestamp) => {
        if (!timestamp || timestamp <= Date.now()) return 'Available now';
        
        const remaining = timestamp - Date.now();
        const days = Math.floor(remaining / (1000 * 60 * 60 * 24));
        const hours = Math.floor((remaining % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        
        if (days > 0) return `${days} days, ${hours} hours`;
        return `${hours} hours`;
    };
    
    return (
        <div className="gas-free-staking">
            <h3>Stake TEO (Gas-Free with Anti-Abuse Protection)</h3>
            <div className="staking-info">
                <p>Current Tier: Bronze (50% commission)</p>
                <p>TEO Balance: {teoBalance} TEO</p>
                <p>Staked: {stakedAmount} TEO</p>
            </div>
            
            {restrictions && (
                <div className="staking-restrictions">
                    <h4>🛡️ Anti-Abuse Rules</h4>
                    
                    <div className="restriction-item">
                        <strong>Staking Status:</strong>
                        <span className={restrictions.canStake ? 'available' : 'restricted'}>
                            {restrictions.canStake ? '✅ Available' : '❌ Restricted'}
                        </span>
                        {!restrictions.canStake && (
                            <small>
                                Next available: {formatTimeRemaining(restrictions.nextStakeTime)}
                                <br />Reason: {restrictions.stakesUsed7Days >= 2 ? 'Weekly limit (2/7 days)' : 'Cooldown period'}
                            </small>
                        )}
                    </div>
                    
                    <div className="restriction-item">
                        <strong>Unstaking Status:</strong>
                        <span className={restrictions.canUnstake ? 'available' : 'restricted'}>
                            {restrictions.canUnstake ? '✅ Available' : '❌ Restricted'}
                        </span>
                        {!restrictions.canUnstake && (
                            <small>
                                Next available: {formatTimeRemaining(restrictions.nextUnstakeTime)}
                                <br />Reason: {restrictions.unstakesUsed7Days >= 1 ? 'Weekly limit (1/7 days)' : 'Lockup/Cooldown period'}
                            </small>
                        )}
                    </div>
                    
                    <div className="weekly-usage">
                        <p>This Week: {restrictions.stakesUsed7Days}/2 stakes, {restrictions.unstakesUsed7Days}/1 unstakes</p>
                    </div>
                </div>
            )}
            
            <div className="staking-actions">
                <div className="stake-section">
                    <h4>Stake TEO</h4>
                    <input 
                        type="number" 
                        value={stakingAmount}
                        onChange={(e) => setStakingAmount(e.target.value)}
                        placeholder="Amount to stake"
                        disabled={!restrictions?.canStake}
                    />
                    <button 
                        onClick={handleGasFreeStake} 
                        disabled={loading || !restrictions?.canStake || !stakingAmount}
                    >
                        {loading ? 'Processing...' : 'Sign & Stake TEO'}
                    </button>
                    <small>Max 2 stakes per 7 days, 3-day cooldown between stakes</small>
                </div>
                
                <div className="unstake-section">
                    <h4>Unstake TEO</h4>
                    <input 
                        type="number" 
                        value={unstakingAmount}
                        onChange={(e) => setUnstakingAmount(e.target.value)}
                        placeholder="Amount to unstake"
                        disabled={!restrictions?.canUnstake}
                        max={stakedAmount}
                    />
                    <button 
                        onClick={handleGasFreeUnstake} 
                        disabled={loading || !restrictions?.canUnstake || !unstakingAmount}
                    >
                        {loading ? 'Processing...' : 'Sign & Unstake TEO'}
                    </button>
                    <small>7-day lockup period, max 1 unstake per 7 days</small>
                </div>
            </div>
            
            <div className="anti-abuse-info">
                <h4>📋 Anti-Abuse Rules Explained</h4>
                <ul>
                    <li><strong>Staking:</strong> Max 2 times per week, 3-day cooldown</li>
                    <li><strong>Unstaking:</strong> 7-day minimum lockup, max 1 per week</li>
                    <li><strong>Purpose:</strong> Prevents gaming tier system for unfair advantage</li>
                    <li><strong>Benefit:</strong> Stable tiers = better student experience</li>
                </ul>
            </div>
            
            <small>* No gas fees required, only signature needed</small>
            <small>* Platform pays all MATIC gas fees</small>
        </div>
    );
};
```
```

#### **Backend Gas-Free Staking Service:**
```python
# services/teocoin_staking_service.py
class GasFreeStakingService:
    def __init__(self):
        # Platform's wallet pays all MATIC gas fees
        self.platform_account = Account.from_key(settings.PLATFORM_PRIVATE_KEY)
        self.w3 = Web3(Web3.HTTPProvider(settings.POLYGON_RPC_URL))
        self.staking_contract = self.w3.eth.contract(
            address=settings.TEOCOIN_STAKING_CONTRACT,
            abi=STAKING_CONTRACT_ABI
        )
    
    def stake_tokens_gas_free(self, teacher_address, amount, teacher_signature):
        """
        Platform pays MATIC gas fees for teacher's staking transaction
        Teacher only needs TEO tokens, no MATIC required
        """
        
        # Build staking transaction (platform pays gas)
        gas_price = self.w3.eth.gas_price
        nonce = self.w3.eth.get_transaction_count(self.platform_account.address)
        
        # Platform wallet pays MATIC gas for staking transaction
        transaction = self.staking_contract.functions.stakeTokensGasFree(
            teacher_address,
            Web3.to_wei(amount, 'ether'),
            teacher_signature
        ).build_transaction({
            'from': self.platform_account.address,
            'gas': 150000,  # Platform pays ~0.003-0.007 MATIC
            'gasPrice': gas_price,
            'nonce': nonce,
        })
        
        # Sign and send transaction (platform pays MATIC)
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, 
            self.platform_account.key
        )
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Platform's MATIC balance decreased by gas fee
        # Teacher's TEO balance decreased by staking amount
        # Teacher pays ZERO MATIC
        
        return tx_hash.hex()
```

### **Fully Gas-Free Platform Benefits:**

✅ **Students**: Gas-free discounts (only signature needed)  
✅ **Teachers**: Gas-free staking + gas-free discount decisions (only signatures needed)  
✅ **Platform**: Pays all MATIC gas fees (~$0.001-0.010 per transaction)  
✅ **User Experience**: Feels like traditional web app, not crypto dApp  
✅ **Adoption**: Zero barrier to entry (no MATIC needed by users)

### **Total Platform MATIC Costs:**
- **Discount Request**: ~0.002-0.005 MATIC
- **Teacher Decision**: ~0.001-0.003 MATIC  
- **Teacher Staking**: ~0.003-0.007 MATIC
- **Teacher Unstaking**: ~0.003-0.007 MATIC

**Total Platform Cost**: ~$0.005-0.020 USD per user interaction

Would you like me to implement this updated contract?
