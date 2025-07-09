// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/**
 * @title TeoCoinStakingGasFree
 * @dev Gas-free staking system with anti-abuse protection to prevent tier gaming
 * 
 * Key Innovation: 100% Gas-Free Staking + Anti-Abuse Protection
 * - Teachers: Only sign messages (no MetaMask transactions, no MATIC needed)
 * - Platform: Pays all MATIC gas fees for seamless user experience
 * - Anti-Abuse: Time restrictions prevent gaming tier system before course purchases
 * 
 * Anti-Abuse Rules:
 * - Staking: Max 2 times per 7 days, 3-day cooldown between stakes
 * - Unstaking: 7-day minimum lockup, max 1 per 7 days, 7-day cooldown
 * - Purpose: Prevents teachers from gaming tier system for unfair advantage
 * 
 * Tier System (Commission Rates):
 * - Bronze: 0 TEO (25% platform commission)
 * - Silver: 100 TEO (22% platform commission)  
 * - Gold: 300 TEO (19% platform commission)
 * - Platinum: 600 TEO (16% platform commission)
 * - Diamond: 1000 TEO (15% platform commission)
 * 
 * Gas-Free Features:
 * - Platform pays all MATIC gas fees (~$0.002-0.008 per action)
 * - Teachers only need TEO tokens, never need MATIC
 * - Signature-based authentication for security
 * - Time-based restrictions prevent abuse
 * - Non-breaking addition to existing system
 */
contract TeoCoinStakingGasFree is ReentrancyGuard, Ownable, Pausable {
    using ECDSA for bytes32;
    
    // ========== STATE VARIABLES ==========
    
    IERC20 public immutable teoToken;
    address public stakingPool; // Where staked TEO tokens are held
    address public platformAccount;
    
    // Gas-free mode toggle
    bool public gasFreeMode = true;
    
    // Staking tier configuration
    struct StakingTier {
        uint256 requiredAmount;    // TEO required to reach this tier
        uint256 commissionRate;    // Commission rate in basis points (e.g., 2500 = 25%)
        string tierName;           // Name of the tier
    }
    
    // User staking information
    struct StakingInfo {
        uint256 amount;           // Amount of TEO staked
        uint256 tier;             // Current tier (0-4)
        uint256 stakingTime;      // When the stake was created/last updated
        bool active;              // Whether the stake is active
    }
    
    // Anti-abuse tracking structures
    struct StakingRestrictions {
        uint256 lastStakeTime;
        uint256 lastUnstakeTime;
        uint256 stakingCount7Days;
        uint256 unstakingCount7Days;
        uint256 firstStakeInWindow;
        uint256 firstUnstakeInWindow;
    }
    
    // Tier definitions (indexed 0-4)
    mapping(uint256 => StakingTier) public tiers;
    
    // User staking data
    mapping(address => StakingInfo) public userStakes;
    
    // Anti-abuse restrictions per teacher
    mapping(address => StakingRestrictions) public teacherRestrictions;
    
    // Platform statistics
    uint256 public totalStaked;
    uint256 public totalStakers;
    
    // Anti-abuse constants
    uint256 public constant LOCKUP_PERIOD = 7 days;          // Minimum time before unstaking
    uint256 public constant UNSTAKE_COOLDOWN = 7 days;       // Cooldown between unstakes
    uint256 public constant STAKE_COOLDOWN = 3 days;         // Cooldown between stakes
    uint256 public constant MAX_STAKES_PER_7_DAYS = 2;       // Max stakes per week
    uint256 public constant MAX_UNSTAKES_PER_7_DAYS = 1;     // Max unstakes per week
    
    // ========== EVENTS ==========
    
    event TokensStaked(
        address indexed teacher,
        uint256 amount,
        uint256 newTier,
        uint256 newTotal
    );
    
    event TokensUnstaked(
        address indexed teacher,
        uint256 amount,
        uint256 newTier,
        uint256 newTotal
    );
    
    event TierUpgraded(
        address indexed teacher,
        uint256 oldTier,
        uint256 newTier,
        uint256 stakedAmount
    );
    
    event TierConfigurationUpdated(
        uint256 indexed tierIndex,
        uint256 requiredAmount,
        uint256 commissionRate,
        string tierName
    );
    
    event GasFreeModeToggled(bool enabled);
    
    event StakingPoolUpdated(address indexed oldPool, address indexed newPool);
    event PlatformAccountUpdated(address indexed oldAccount, address indexed newAccount);
    
    // ========== MODIFIERS ==========
    
    modifier onlyPlatform() {
        require(msg.sender == platformAccount, "Only platform can execute");
        _;
    }
    
    modifier gasFreeEnabled() {
        require(gasFreeMode, "Gas-free mode disabled");
        _;
    }
    
    // ========== CONSTRUCTOR ==========
    
    constructor(
        address _teoToken,
        address _stakingPool,
        address _platformAccount
    ) {
        require(_teoToken != address(0), "TeoCoin address cannot be zero");
        require(_stakingPool != address(0), "Staking pool address cannot be zero");
        require(_platformAccount != address(0), "Platform account cannot be zero");
        
        teoToken = IERC20(_teoToken);
        stakingPool = _stakingPool;
        platformAccount = _platformAccount;
        
        // Initialize tier configuration
        _initializeTiers();
    }
    
    // ========== INTERNAL FUNCTIONS ==========
    
    /**
     * @dev Initialize the staking tier system
     * Note: Adjusted for current supply of 10,000 TEO total
     */
    function _initializeTiers() internal {
        tiers[0] = StakingTier(0, 2500, "Bronze");           // 25% platform commission
        tiers[1] = StakingTier(100 * 10**18, 2200, "Silver");   // 22% platform commission (100 TEO)
        tiers[2] = StakingTier(300 * 10**18, 1900, "Gold");     // 19% platform commission (300 TEO)
        tiers[3] = StakingTier(600 * 10**18, 1600, "Platinum"); // 16% platform commission (600 TEO)
        tiers[4] = StakingTier(1000 * 10**18, 1500, "Diamond"); // 15% platform commission (1000 TEO)
    }
    
    /**
     * @dev Calculate user's tier based on staked amount
     */
    function _calculateTier(uint256 stakedAmount) internal view returns (uint256) {
        // Check from highest tier down
        for (uint256 i = 4; i > 0; i--) {
            if (stakedAmount >= tiers[i].requiredAmount) {
                return i;
            }
        }
        return 0; // Bronze tier
    }
    
    /**
     * @dev Update user's tier if they qualify for upgrade/downgrade
     */
    function _updateTeacherTier(address teacher) internal {
        StakingInfo storage userStake = userStakes[teacher];
        uint256 newTier = _calculateTier(userStake.amount);
        
        if (newTier != userStake.tier) {
            uint256 oldTier = userStake.tier;
            userStake.tier = newTier;
            
            emit TierUpgraded(teacher, oldTier, newTier, userStake.amount);
        }
    }
    
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
    function _canUnstake(address teacher, uint256 /* amount */) internal view returns (bool) {
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
    function _recordStakingAction(address teacher, uint256 /* amount */, bool isStaking) internal {
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
     * @dev Verify teacher's signature for gas-free staking
     */
    function _verifyTeacherStakingSignature(
        address teacher,
        uint256 amount,
        bytes memory signature
    ) internal view returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(
            "\x19Ethereum Signed Message:\n32",
            keccak256(abi.encodePacked(
                teacher,
                amount,
                "stake",
                address(this),
                block.chainid
            ))
        ));
        
        address recoveredSigner = messageHash.recover(signature);
        return recoveredSigner == teacher;
    }
    
    /**
     * @dev Verify teacher's signature for gas-free unstaking
     */
    function _verifyTeacherUnstakingSignature(
        address teacher,
        uint256 amount,
        bytes memory signature
    ) internal view returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(
            "\x19Ethereum Signed Message:\n32",
            keccak256(abi.encodePacked(
                teacher,
                amount,
                "unstake",
                address(this),
                block.chainid
            ))
        ));
        
        address recoveredSigner = messageHash.recover(signature);
        return recoveredSigner == teacher;
    }
    
    // ========== GAS-FREE STAKING FUNCTIONS ==========
    
    /**
     * @dev Gas-free staking - Platform pays MATIC, teacher signs message
     * ANTI-ABUSE: Time restrictions prevent gaming the system
     * 
     * @param teacher Teacher address staking tokens
     * @param amount Amount of TEO to stake
     * @param teacherSignature Teacher's signature authorizing staking
     */
    function stakeTokensGasFree(
        address teacher,
        uint256 amount,
        bytes memory teacherSignature
    ) external onlyPlatform gasFreeEnabled whenNotPaused nonReentrant {
        require(teacher != address(0), "Teacher address cannot be zero");
        require(amount > 0, "Amount must be positive");
        
        // ANTI-ABUSE: Check staking frequency limits
        require(_canStake(teacher), "Staking too frequently - max 2 stakes per 7 days");
        
        // Verify teacher signature for staking approval
        require(_verifyTeacherStakingSignature(teacher, amount, teacherSignature), "Invalid teacher signature");
        
        // Check teacher has sufficient TEO balance
        require(teoToken.balanceOf(teacher) >= amount, "Insufficient TEO balance");
        
        // PLATFORM PAYS MATIC GAS - Teacher pays nothing
        // Transfer TEO from teacher to staking pool
        require(
            teoToken.transferFrom(teacher, stakingPool, amount),
            "TEO staking transfer failed"
        );
        
        StakingInfo storage userStake = userStakes[teacher];
        
        // If teacher is staking for the first time
        if (!userStake.active) {
            userStake.active = true;
            userStake.stakingTime = block.timestamp;
            totalStakers++;
        }
        
        // Update staked amount
        userStake.amount += amount;
        totalStaked += amount;
        
        // ANTI-ABUSE: Record staking action with timestamp
        _recordStakingAction(teacher, amount, true); // true = stake
        
        // Update teacher tier based on new staking amount
        _updateTeacherTier(teacher);
        
        emit TokensStaked(teacher, amount, userStake.tier, userStake.amount);
    }
    
    /**
     * @dev Gas-free unstaking with LOCKUP PERIOD - Platform pays MATIC, teacher signs message
     * ANTI-ABUSE: 7-day minimum lockup + cooldown periods
     * 
     * @param teacher Teacher address unstaking tokens
     * @param amount Amount of TEO to unstake
     * @param teacherSignature Teacher's signature authorizing unstaking
     */
    function unstakeTokensGasFree(
        address teacher,
        uint256 amount,
        bytes memory teacherSignature
    ) external onlyPlatform gasFreeEnabled whenNotPaused nonReentrant {
        require(teacher != address(0), "Teacher address cannot be zero");
        require(amount > 0, "Amount must be positive");
        
        StakingInfo storage userStake = userStakes[teacher];
        require(userStake.active, "No active stake found");
        require(userStake.amount >= amount, "Insufficient staked amount");
        
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
        
        // Update staked amount
        userStake.amount -= amount;
        totalStaked -= amount;
        
        // If teacher unstaked everything, deactivate stake
        if (userStake.amount == 0) {
            userStake.active = false;
            totalStakers--;
        }
        
        // ANTI-ABUSE: Record unstaking action with timestamp + start cooldown
        _recordStakingAction(teacher, amount, false); // false = unstake
        
        // Update teacher tier based on new staking amount
        _updateTeacherTier(teacher);
        
        emit TokensUnstaked(teacher, amount, userStake.tier, userStake.amount);
    }
    
    // ========== VIEW FUNCTIONS ==========
    
    /**
     * @dev Get teacher's current tier
     */
    function getUserTier(address teacher) external view returns (uint256) {
        return userStakes[teacher].tier;
    }
    
    /**
     * @dev Get teacher's staked amount
     */
    function getStakedAmount(address teacher) external view returns (uint256) {
        return userStakes[teacher].amount;
    }
    
    /**
     * @dev Get teacher's commission rate based on their tier
     */
    function getUserCommissionRate(address teacher) external view returns (uint256) {
        uint256 tier = userStakes[teacher].tier;
        return tiers[tier].commissionRate;
    }
    
    /**
     * @dev Get complete teacher staking information
     */
    function getUserStakingInfo(address teacher) 
        external 
        view 
        returns (
            uint256 amount,
            uint256 tier,
            uint256 stakingTime,
            bool active,
            string memory tierName,
            uint256 commissionRate
        ) 
    {
        StakingInfo memory userStake = userStakes[teacher];
        StakingTier memory userTier = tiers[userStake.tier];
        
        return (
            userStake.amount,
            userStake.tier,
            userStake.stakingTime,
            userStake.active,
            userTier.tierName,
            userTier.commissionRate
        );
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
        uint256 lockupEnd = restrictions.lastStakeTime + LOCKUP_PERIOD;
        uint256 cooldownEnd = restrictions.lastUnstakeTime + UNSTAKE_COOLDOWN;
        nextUnstakeTime = lockupEnd > cooldownEnd ? lockupEnd : cooldownEnd;
        
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
    
    /**
     * @dev Get tier configuration
     */
    function getTierInfo(uint256 tierIndex) 
        external 
        view 
        returns (
            uint256 requiredAmount,
            uint256 commissionRate,
            string memory tierName
        ) 
    {
        require(tierIndex <= 4, "Invalid tier index");
        StakingTier memory tier = tiers[tierIndex];
        return (tier.requiredAmount, tier.commissionRate, tier.tierName);
    }
    
    /**
     * @dev Get platform staking statistics
     */
    function getStakingStats() 
        external 
        view 
        returns (uint256 _totalStaked, uint256 _totalStakers) 
    {
        return (totalStaked, totalStakers);
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
     */
    function setGasFreeMode(bool enabled) external onlyOwner {
        gasFreeMode = enabled;
        emit GasFreeModeToggled(enabled);
    }
    
    /**
     * @dev Update tier configuration (only owner)
     */
    function updateTier(
        uint256 tierIndex,
        uint256 requiredAmount,
        uint256 commissionRate,
        string calldata tierName
    ) external onlyOwner {
        require(tierIndex <= 4, "Invalid tier index");
        require(commissionRate <= 10000, "Commission rate cannot exceed 100%");
        
        tiers[tierIndex] = StakingTier(requiredAmount, commissionRate, tierName);
        
        emit TierConfigurationUpdated(tierIndex, requiredAmount, commissionRate, tierName);
    }
    
    /**
     * @dev Update staking pool address (owner only)
     */
    function updateStakingPool(address newStakingPool) external onlyOwner {
        require(newStakingPool != address(0), "New staking pool address cannot be zero");
        address oldPool = stakingPool;
        stakingPool = newStakingPool;
        emit StakingPoolUpdated(oldPool, newStakingPool);
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
     * @dev Pause staking operations (emergency)
     */
    function pause() external onlyOwner {
        _pause();
    }
    
    /**
     * @dev Unpause staking operations
     */
    function unpause() external onlyOwner {
        _unpause();
    }
    
    /**
     * @dev Emergency function to recover any accidentally sent tokens
     */
    function recoverTokens(address token, uint256 amount) external onlyOwner {
        require(token != address(teoToken), "Cannot recover staked TEO");
        require(IERC20(token).transfer(owner(), amount), "Recovery failed");
    }
}
