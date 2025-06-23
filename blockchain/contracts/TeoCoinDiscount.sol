// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title TeoCoinDiscount
 * @dev Layer 2 gas-free discount system for TeoCoin
 * 
 * Features:
 * - Students request discounts without paying gas fees
 * - Teachers approve/decline discount requests
 * - Platform pays all gas fees for seamless UX
 * - Direct MetaMask to MetaMask transfers
 * - Automatic teacher bonus from reward pool
 * - Time-limited discount requests (auto-decline after 2 hours)
 */
contract TeoCoinDiscount is ReentrancyGuard, Ownable, Pausable {
    using ECDSA for bytes32;
    
    // ========== STATE VARIABLES ==========
    
    IERC20 public immutable teoToken;
    address public rewardPool;
    address public platformAccount;
    
    // Discount request configuration
    uint256 public constant REQUEST_TIMEOUT = 2 hours;
    uint256 public constant TEACHER_BONUS_PERCENT = 25; // 25% bonus on top of student payment
    uint256 public constant MAX_DISCOUNT_PERCENT = 15; // Maximum 15% discount
    
    // Exchange rate: 1 TEO = 0.10 EUR discount value
    uint256 public constant TEO_TO_EUR_RATE = 10; // 1 TEO = 0.10 EUR, so 10 TEO = 1 EUR
    
    // Request tracking
    uint256 private _requestIdCounter;
    mapping(uint256 => DiscountRequest) public discountRequests;
    mapping(address => uint256[]) public studentRequests;
    mapping(address => uint256[]) public teacherRequests;
    
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
    
    // ========== MAIN FUNCTIONS ==========
    
    /**
     * @dev Create a discount request (called by platform, student pays no gas)
     * @param student Student address requesting discount
     * @param teacher Teacher address for the course
     * @param courseId Course identifier
     * @param coursePrice Course price in EUR cents
     * @param discountPercent Discount percentage (5, 10, or 15)
     * @param studentSignature Student's pre-approval signature
     */
    function createDiscountRequest(
        address student,
        address teacher,
        uint256 courseId,
        uint256 coursePrice,
        uint256 discountPercent,
        bytes memory studentSignature
    ) external onlyPlatform whenNotPaused nonReentrant returns (uint256) {
        require(student != address(0), "Student address cannot be zero");
        require(teacher != address(0), "Teacher address cannot be zero");
        require(student != teacher, "Student and teacher cannot be same");
        require(discountPercent >= 5 && discountPercent <= MAX_DISCOUNT_PERCENT, "Invalid discount percent");
        require(coursePrice > 0, "Course price must be positive");
        
        // Calculate TEO cost and teacher bonus
        uint256 discountValue = (coursePrice * discountPercent) / 100; // Discount in EUR cents
        uint256 teoCost = (discountValue * TEO_TO_EUR_RATE) / 100; // Convert to TEO (accounting for cents)
        uint256 teacherBonus = (teoCost * TEACHER_BONUS_PERCENT) / 100;
        
        // Verify student has enough TEO
        require(teoToken.balanceOf(student) >= teoCost, "Insufficient TEO balance");
        
        // Verify reward pool has enough TEO for bonus
        require(teoToken.balanceOf(rewardPool) >= teacherBonus, "Insufficient reward pool balance");
        
        // Verify student signature
        require(_verifyStudentSignature(student, courseId, teoCost, studentSignature), "Invalid student signature");
        
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
        
        emit DiscountRequested(requestId, student, teacher, courseId, discountPercent, teoCost);
        return requestId;
    }
    
    /**
     * @dev Approve discount request and execute transfers (platform pays gas)
     * @param requestId Request ID to approve
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
        
        // Execute transfers
        // 1. Transfer TEO from student to teacher (platform pays gas)
        require(
            teoToken.transferFrom(request.student, request.teacher, request.teoCost),
            "Student to teacher transfer failed"
        );
        
        // 2. Transfer bonus from reward pool to teacher
        require(
            teoToken.transferFrom(rewardPool, request.teacher, request.teacherBonus),
            "Reward pool bonus transfer failed"
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
     * @dev Decline discount request
     * @param requestId Request ID to decline
     * @param reason Reason for declining
     */
    function declineDiscountRequest(uint256 requestId, string memory reason) 
        external 
        onlyPlatform 
        whenNotPaused 
        validRequest(requestId) 
    {
        DiscountRequest storage request = discountRequests[requestId];
        request.status = DiscountStatus.Declined;
        
        emit DiscountDeclined(requestId, request.student, request.teacher, reason);
    }
    
    /**
     * @dev Process expired requests (can be called by anyone)
     * @param requestIds Array of request IDs to check for expiration
     */
    function processExpiredRequests(uint256[] memory requestIds) external whenNotPaused {
        for (uint256 i = 0; i < requestIds.length; i++) {
            uint256 requestId = requestIds[i];
            if (requestId <= _requestIdCounter && 
                discountRequests[requestId].status == DiscountStatus.Pending &&
                block.timestamp > discountRequests[requestId].deadline) {
                
                discountRequests[requestId].status = DiscountStatus.Expired;
                emit DiscountExpired(
                    requestId, 
                    discountRequests[requestId].student, 
                    discountRequests[requestId].teacher
                );
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
     * @dev Calculate TEO cost for a discount
     */
    function calculateTeoCost(uint256 coursePrice, uint256 discountPercent) external pure returns (uint256, uint256) {
        require(discountPercent >= 5 && discountPercent <= 15, "Invalid discount percent");
        
        uint256 discountValue = (coursePrice * discountPercent) / 100;
        uint256 teoCost = (discountValue * TEO_TO_EUR_RATE) / 100;
        uint256 teacherBonus = (teoCost * TEACHER_BONUS_PERCENT) / 100;
        
        return (teoCost, teacherBonus);
    }
    
    /**
     * @dev Get current request counter
     */
    function getCurrentRequestId() external view returns (uint256) {
        return _requestIdCounter;
    }
    
    // ========== ADMIN FUNCTIONS ==========
    
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
     * @dev Verify student's pre-approval signature
     */
    function _verifyStudentSignature(
        address student,
        uint256 courseId,
        uint256 teoCost,
        bytes memory signature
    ) internal view returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(
            "\x19Ethereum Signed Message:\n32",
            keccak256(abi.encodePacked(student, courseId, teoCost, address(this)))
        ));
        
        address recoveredSigner = messageHash.recover(signature);
        return recoveredSigner == student;
    }
}
