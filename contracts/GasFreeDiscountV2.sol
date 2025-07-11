// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title GasFreeDiscountV2 - ZERO MATIC SOLUTION
 * @dev Completely gas-free discount system where students never need MATIC
 * 
 * Key Innovation: 100% Zero-MATIC Experience for Students & Teachers
 * - Students: Only sign message (no MetaMask transaction, no MATIC needed)
 * - Teachers: Click web buttons (no MetaMask transaction, no MATIC needed)  
 * - Platform: Pays all MATIC gas fees + manages student allowances
 * 
 * Zero-MATIC Architecture:
 * 1. Platform pre-approves students during registration (platform pays gas once)
 * 2. Students use platform allowances instead of ERC20 approvals (zero MATIC)
 * 3. All future discount transactions are completely gas-free for students
 * 
 * Business Logic: Same as V1 but with platform allowance system
 */
contract GasFreeDiscountV2 is ReentrancyGuard, Ownable, Pausable {
    using ECDSA for bytes32;
    
    // ========== STATE VARIABLES ==========
    
    IERC20 public immutable teoToken;
    address public rewardPool;
    address public platformAccount;
    
    // ZERO-MATIC: Platform manages student allowances instead of ERC20 approvals
    mapping(address => uint256) public platformAllowances;
    
    // Gas-free mode toggle
    bool public gasFreeMode = true;
    
    // Discount request configuration
    uint256 public constant REQUEST_TIMEOUT = 24 hours;
    uint256 public constant TEACHER_BONUS_PERCENT = 25; // 25% bonus on top of student payment
    uint256 public constant MAX_DISCOUNT_PERCENT = 15; // Maximum 15% discount
    
    // Exchange rate: 1 TEO = 0.10 EUR discount value
    uint256 public constant TEO_TO_EUR_RATE = 10; // 1 TEO = 0.10 EUR, so 10 TEO = 1 EUR
    
    // Request tracking
    uint256 private _requestIdCounter;
    mapping(uint256 => DiscountRequest) public discountRequests;
    mapping(address => uint256[]) public studentRequests;
    mapping(address => uint256[]) public teacherRequests;
    
    // Track used signatures to prevent replay attacks
    mapping(bytes32 => bool) public usedSignatures;
    
    // Gas-free transaction tracking
    mapping(address => uint256) public studentRequestCount;
    mapping(address => uint256) public teacherRequestCount;
    
    // ========== STRUCTS ==========
    
    struct DiscountRequest {
        uint256 requestId;
        address student;
        address teacher;
        uint256 courseId;
        uint256 coursePrice; // In EUR cents (e.g., 10000 = €100.00)
        uint256 discountPercent; // 5, 10, or 15
        uint256 teoCost; // TEO amount student pays
        uint256 teacherBonus; // Bonus TEO from reward pool
        uint256 createdAt;
        uint256 deadline;
        DiscountStatus status;
        bytes studentSignature; // Pre-approval signature
    }
    
    enum DiscountStatus {
        Pending,
        Approved,
        Declined,
        Expired
    }
    
    // ========== EVENTS ==========
    
    event DiscountRequested(
        uint256 indexed requestId,
        address indexed student,
        address indexed teacher,
        uint256 courseId,
        uint256 discountPercent,
        uint256 teoCost
    );
    
    event DiscountApproved(
        uint256 indexed requestId,
        address indexed student,
        address indexed teacher,
        uint256 teoCost,
        uint256 teacherBonus
    );
    
    event DiscountDeclined(
        uint256 indexed requestId,
        address indexed student,
        address indexed teacher,
        string reason
    );
    
    event DiscountExpired(
        uint256 indexed requestId,
        address indexed student,
        address indexed teacher
    );
    
    event StudentTeoDeducted(
        address indexed student,
        uint256 requestId,
        uint256 teoAmount
    );
    
    // ZERO-MATIC EVENTS
    event PlatformAllowanceSet(
        address indexed student,
        uint256 allowance
    );
    
    event StudentApprovedByPlatform(
        address indexed student,
        uint256 allowance
    );
    
    event GasFreeModeToggled(bool enabled);
    
    event RewardPoolUpdated(address indexed oldPool, address indexed newPool);
    event PlatformAccountUpdated(address indexed oldAccount, address indexed newAccount);
    
    // ========== MODIFIERS ==========
    
    modifier onlyPlatform() {
        require(msg.sender == platformAccount, "Only platform can execute");
        _;
    }
    
    modifier validRequest(uint256 requestId) {
        require(requestId <= _requestIdCounter, "Invalid request ID");
        require(discountRequests[requestId].status == DiscountStatus.Pending, "Request not pending");
        require(block.timestamp <= discountRequests[requestId].deadline, "Request expired");
        _;
    }
    
    modifier gasFreeEnabled() {
        require(gasFreeMode, "Gas-free mode disabled");
        _;
    }
    
    // ========== CONSTRUCTOR ==========
    
    constructor(
        address _teoToken,
        address _rewardPool,
        address _platformAccount
    ) {
        require(_teoToken != address(0), "TEO token address cannot be zero");
        require(_rewardPool != address(0), "Reward pool address cannot be zero");
        require(_platformAccount != address(0), "Platform account cannot be zero");
        
        teoToken = IERC20(_teoToken);
        rewardPool = _rewardPool;
        platformAccount = _platformAccount;
        
        _requestIdCounter = 0;
    }
    
    // ========== ZERO-MATIC PLATFORM ALLOWANCE FUNCTIONS ==========
    
    /**
     * @dev Platform approves student for gas-free discounts (ZERO-MATIC solution)
     * Platform pays gas for this transaction during student registration
     * Student never needs MATIC after this point
     * 
     * @param student Student address to approve
     * @param allowance Amount of TEO the student can spend on discounts
     */
    function approveStudentForGasFree(
        address student,
        uint256 allowance
    ) external onlyPlatform {
        require(student != address(0), "Invalid student address");
        require(allowance > 0, "Allowance must be positive");
        
        platformAllowances[student] = allowance;
        
        emit PlatformAllowanceSet(student, allowance);
        emit StudentApprovedByPlatform(student, allowance);
    }
    
    /**
     * @dev Batch approve multiple students (gas efficient for platform)
     * Platform can approve many students in one transaction
     * 
     * @param students Array of student addresses
     * @param allowances Array of corresponding allowances  
     */
    function batchApproveStudents(
        address[] calldata students,
        uint256[] calldata allowances
    ) external onlyPlatform {
        require(students.length == allowances.length, "Arrays length mismatch");
        require(students.length > 0, "Empty arrays");
        
        for (uint256 i = 0; i < students.length; i++) {
            require(students[i] != address(0), "Invalid student address");
            require(allowances[i] > 0, "Allowance must be positive");
            
            platformAllowances[students[i]] = allowances[i];
            emit PlatformAllowanceSet(students[i], allowances[i]);
        }
    }
    
    /**
     * @dev Increase student's platform allowance
     * Useful for topping up allowances without overwriting
     * 
     * @param student Student address
     * @param additionalAllowance Amount to add to current allowance
     */
    function increaseStudentAllowance(
        address student,
        uint256 additionalAllowance
    ) external onlyPlatform {
        require(student != address(0), "Invalid student address");
        require(additionalAllowance > 0, "Additional allowance must be positive");
        
        platformAllowances[student] += additionalAllowance;
        emit PlatformAllowanceSet(student, platformAllowances[student]);
    }
    
    // ========== ZERO-MATIC MAIN FUNCTIONS ==========
    
    /**
     * @dev Create discount request with ZERO MATIC requirement for students
     * Uses platform allowances instead of ERC20 approvals
     * Platform pays all MATIC gas fees
     * 
     * @param student Student address requesting discount
     * @param teacher Teacher address for the course  
     * @param courseId Course identifier
     * @param coursePrice Course price in EUR cents
     * @param discountPercent Discount percentage (5, 10, or 15)
     * @param studentSignature Student's off-chain signature authorizing TEO usage
     */
    function createDiscountRequestGasFree(
        address student,
        address teacher,
        uint256 courseId,
        uint256 coursePrice,
        uint256 discountPercent,
        bytes memory studentSignature
    ) external onlyPlatform gasFreeEnabled whenNotPaused nonReentrant returns (uint256) {
        require(student != address(0), "Student address cannot be zero");
        require(teacher != address(0), "Teacher address cannot be zero");
        require(student != teacher, "Student and teacher cannot be same");
        require(discountPercent >= 5 && discountPercent <= MAX_DISCOUNT_PERCENT, "Invalid discount percent");
        require(coursePrice > 0, "Course price must be positive");
        
        // Calculate TEO amounts
        (uint256 teoCost, uint256 teacherBonus) = calculateTeoCost(coursePrice, discountPercent);
        
        // ZERO-MATIC: Check platform allowance instead of ERC20 approval
        require(platformAllowances[student] >= teoCost, "Insufficient platform allowance");
        
        // Verify student has sufficient TEO balance
        require(teoToken.balanceOf(student) >= teoCost, "Student insufficient TEO balance");
        
        // Verify reward pool has sufficient balance for teacher bonus
        require(teoToken.balanceOf(rewardPool) >= teacherBonus, "Insufficient reward pool balance");
        
        // Verify student signature and prevent replay attacks
        require(_verifyStudentSignature(student, courseId, teoCost, studentSignature), "Invalid student signature");
        
        // ZERO-MATIC: Deduct from platform allowance instead of requiring approval
        platformAllowances[student] -= teoCost;
        
        // IMMEDIATELY DEDUCT TEO FROM STUDENT TO REWARD POOL (platform pays MATIC gas)
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
        
        // Update counters for analytics
        studentRequestCount[student]++;
        teacherRequestCount[teacher]++;
        
        emit DiscountRequested(requestId, student, teacher, courseId, discountPercent, teoCost);
        emit StudentTeoDeducted(student, requestId, teoCost);
        
        return requestId;
    }
    
    /**
     * @dev Approve discount request - Teacher accepts TEO payment
     * TEO flows from reward pool to teacher + bonus from reward pool
     * Platform pays MATIC gas for this transaction
     * 
     * @param requestId Request ID to approve
     */
    function approveDiscountRequest(uint256 requestId) 
        external 
        onlyPlatform 
        gasFreeEnabled
        whenNotPaused 
        nonReentrant 
        validRequest(requestId) 
    {
        DiscountRequest storage request = discountRequests[requestId];
        
        // Update status
        request.status = DiscountStatus.Approved;
        
        // Execute transfers for TEACHER ACCEPTS scenario:
        // Teacher gets: reduced EUR + student TEO + bonus TEO
        require(
            teoToken.transferFrom(rewardPool, request.teacher, request.teoCost + request.teacherBonus),
            "Reward pool to teacher transfer failed"
        );
        
        emit DiscountApproved(
            requestId, 
            request.student, 
            request.teacher, 
            request.teoCost, 
            request.teacherBonus
        );
    }
    
    /**
     * @dev Decline discount request - Teacher refuses TEO payment
     * Teacher gets full EUR commission, platform keeps TEO (absorbs discount cost)
     * Student ALWAYS gets discount regardless
     * Platform pays MATIC gas for this transaction
     * 
     * @param requestId Request ID to decline
     * @param reason Reason for declining (optional)
     */
    function declineDiscountRequest(uint256 requestId, string memory reason) 
        external 
        onlyPlatform 
        gasFreeEnabled
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
    
    /**
     * @dev Process expired requests - Teacher gets full EUR, platform keeps TEO
     * Platform pays MATIC gas for this transaction
     * 
     * @param requestIds Array of request IDs to check for expiration
     */
    function processExpiredRequests(uint256[] memory requestIds) external gasFreeEnabled whenNotPaused {
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
    
    // ========== VIEW FUNCTIONS ==========
    
    /**
     * @dev Get discount request details
     */
    function getDiscountRequest(uint256 requestId) external view returns (DiscountRequest memory) {
        require(requestId <= _requestIdCounter, "Invalid request ID");
        return discountRequests[requestId];
    }
    
    /**
     * @dev Get student's discount requests
     */
    function getStudentRequests(address student) external view returns (uint256[] memory) {
        return studentRequests[student];
    }
    
    /**
     * @dev Get teacher's discount requests
     */
    function getTeacherRequests(address teacher) external view returns (uint256[] memory) {
        return teacherRequests[teacher];
    }
    
    /**
     * @dev Get student's platform allowance
     */
    function getStudentAllowance(address student) external view returns (uint256) {
        return platformAllowances[student];
    }
    
    /**
     * @dev Check if student is approved for gas-free discounts
     */
    function isStudentApproved(address student, uint256 amount) external view returns (bool) {
        return platformAllowances[student] >= amount;
    }
    
    /**
     * @dev Calculate TEO cost for a discount
     */
    function calculateTeoCost(uint256 coursePrice, uint256 discountPercent) public pure returns (uint256, uint256) {
        require(discountPercent >= 5 && discountPercent <= 15, "Invalid discount percent");
        
        uint256 discountValue = (coursePrice * discountPercent) / 100;
        uint256 teoCost = (discountValue * TEO_TO_EUR_RATE * 10**18) / 100; // Convert to TEO tokens with 18 decimals
        uint256 teacherBonus = (teoCost * TEACHER_BONUS_PERCENT) / 100;
        
        return (teoCost, teacherBonus);
    }
    
    /**
     * @dev Get current request counter
     */
    function getCurrentRequestId() external view returns (uint256) {
        return _requestIdCounter;
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
    
    /**
     * @dev Check if gas-free mode is enabled
     */
    function isGasFreeEnabled() external view returns (bool) {
        return gasFreeMode;
    }
    
    // ========== ADMIN FUNCTIONS ==========
    
    /**
     * @dev Toggle gas-free mode (owner only)
     * Allows switching between gas-free and traditional modes
     */
    function setGasFreeMode(bool enabled) external onlyOwner {
        gasFreeMode = enabled;
        emit GasFreeModeToggled(enabled);
    }
    
    /**
     * @dev Update reward pool address (owner only)
     */
    function updateRewardPool(address newRewardPool) external onlyOwner {
        require(newRewardPool != address(0), "New reward pool address cannot be zero");
        address oldPool = rewardPool;
        rewardPool = newRewardPool;
        emit RewardPoolUpdated(oldPool, newRewardPool);
    }
    
    /**
     * @dev Update platform account address (owner only)
     */
    function updatePlatformAccount(address newPlatformAccount) external onlyOwner {
        require(newPlatformAccount != address(0), "New platform account cannot be zero");
        address oldAccount = platformAccount;
        platformAccount = newPlatformAccount;
        emit PlatformAccountUpdated(oldAccount, newPlatformAccount);
    }
    
    /**
     * @dev Pause contract (owner only)
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause contract (owner only)
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    // ========== INTERNAL FUNCTIONS ==========
    
    /**
     * @dev Verify student's pre-approval signature for gas-free transaction
     * Student signs message off-chain, platform verifies on-chain
     * Includes replay attack protection
     * 
     * @param student Student address that should have signed
     * @param courseId Course identifier
     * @param teoCost TEO amount to be spent
     * @param signature Student's signature
     */
    function _verifyStudentSignature(
        address student,
        uint256 courseId,
        uint256 teoCost,
        bytes memory signature
    ) internal returns (bool) {
        // Create message hash that student should have signed
        bytes32 messageHash = keccak256(abi.encodePacked(
            student, 
            courseId, 
            teoCost, 
            address(this),
            block.chainid // Include chain ID for security
        ));
        
        bytes32 ethSignedMessageHash = messageHash.toEthSignedMessageHash();
        
        // Check for replay attacks
        require(!usedSignatures[ethSignedMessageHash], "Signature already used");
        
        // Mark signature as used
        usedSignatures[ethSignedMessageHash] = true;
        
        // Recover signer from signature
        address recoveredSigner = ethSignedMessageHash.recover(signature);
        return recoveredSigner == student;
    }
}
