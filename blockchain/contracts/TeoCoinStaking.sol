// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title TeoCoinStaking
 * @dev Staking contract for TeoCoin with tier-based commission system for teachers
 * 
 * Features:
 * - Multi-tier staking system (Bronze, Silver, Gold, Platinum, Diamond)
 * - Commission rate benefits for teachers based on staked amount
 * - Secure staking/unstaking with reentrancy protection
 * - Emergency pause functionality
 * - Event tracking for all staking activities
 */
contract TeoCoinStaking is ReentrancyGuard, Ownable, Pausable {
    
    // ========== STATE VARIABLES ==========
    
    IERC20 public immutable teoToken;
    
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
    
    // Tier definitions (indexed 0-4)
    mapping(uint256 => StakingTier) public tiers;
    
    // User staking data
    mapping(address => StakingInfo) public userStakes;
    
    // Platform statistics
    uint256 public totalStaked;
    uint256 public totalStakers;
    
    // ========== EVENTS ==========
    
    event Staked(
        address indexed user,
        uint256 amount,
        uint256 newTier,
        uint256 newTotal
    );
    
    event Unstaked(
        address indexed user,
        uint256 amount,
        uint256 newTier,
        uint256 newTotal
    );
    
    event TierUpgraded(
        address indexed user,
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
    
    // ========== CONSTRUCTOR ==========
    
    constructor(address _teoToken) {
        require(_teoToken != address(0), "TeoCoin address cannot be zero");
        teoToken = IERC20(_teoToken);
        
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
     * @dev Update user's tier if they qualify for upgrade
     */
    function _updateUserTier(address user) internal {
        StakingInfo storage userStake = userStakes[user];
        uint256 newTier = _calculateTier(userStake.amount);
        
        if (newTier != userStake.tier) {
            uint256 oldTier = userStake.tier;
            userStake.tier = newTier;
            
            emit TierUpgraded(user, oldTier, newTier, userStake.amount);
        }
    }
    
    // ========== PUBLIC VIEW FUNCTIONS ==========
    
    /**
     * @dev Get user's current tier
     */
    function getUserTier(address user) external view returns (uint256) {
        return userStakes[user].tier;
    }
    
    /**
     * @dev Get user's staked amount
     */
    function getStakedAmount(address user) external view returns (uint256) {
        return userStakes[user].amount;
    }
    
    /**
     * @dev Get user's commission rate based on their tier
     */
    function getUserCommissionRate(address user) external view returns (uint256) {
        uint256 tier = userStakes[user].tier;
        return tiers[tier].commissionRate;
    }
    
    /**
     * @dev Get complete user staking information
     */
    function getUserStakingInfo(address user) 
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
        StakingInfo memory userStake = userStakes[user];
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
    
    // ========== STAKING FUNCTIONS ==========
    
    /**
     * @dev Stake TEO tokens to improve commission rate
     * @param amount Amount of TEO to stake (in wei)
     */
    function stake(uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "Amount must be greater than 0");
        require(
            teoToken.balanceOf(msg.sender) >= amount,
            "Insufficient TEO balance"
        );
        require(
            teoToken.allowance(msg.sender, address(this)) >= amount,
            "Insufficient allowance"
        );
        
        // Transfer TEO from user to contract
        require(
            teoToken.transferFrom(msg.sender, address(this), amount),
            "Transfer failed"
        );
        
        StakingInfo storage userStake = userStakes[msg.sender];
        
        // If user is staking for the first time
        if (!userStake.active) {
            userStake.active = true;
            userStake.stakingTime = block.timestamp;
            totalStakers++;
        }
        
        // Update staked amount
        userStake.amount += amount;
        totalStaked += amount;
        
        // Update user's tier
        _updateUserTier(msg.sender);
        
        emit Staked(msg.sender, amount, userStake.tier, userStake.amount);
    }
    
    /**
     * @dev Unstake TEO tokens (partial or full)
     * @param amount Amount of TEO to unstake (in wei)
     */
    function unstake(uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "Amount must be greater than 0");
        
        StakingInfo storage userStake = userStakes[msg.sender];
        require(userStake.active, "No active stake found");
        require(userStake.amount >= amount, "Insufficient staked amount");
        
        // Update staked amount
        userStake.amount -= amount;
        totalStaked -= amount;
        
        // If user unstaked everything, deactivate stake
        if (userStake.amount == 0) {
            userStake.active = false;
            totalStakers--;
        }
        
        // Update user's tier (might be downgraded)
        _updateUserTier(msg.sender);
        
        // Transfer TEO back to user
        require(
            teoToken.transfer(msg.sender, amount),
            "Transfer failed"
        );
        
        emit Unstaked(msg.sender, amount, userStake.tier, userStake.amount);
    }
    
    /**
     * @dev Emergency unstake all tokens (for user safety)
     */
    function emergencyUnstake() external nonReentrant {
        StakingInfo storage userStake = userStakes[msg.sender];
        require(userStake.active, "No active stake found");
        require(userStake.amount > 0, "No tokens to unstake");
        
        uint256 amount = userStake.amount;
        
        // Reset user stake
        userStake.amount = 0;
        userStake.tier = 0;
        userStake.active = false;
        
        // Update global stats
        totalStaked -= amount;
        totalStakers--;
        
        // Transfer TEO back to user
        require(
            teoToken.transfer(msg.sender, amount),
            "Emergency transfer failed"
        );
        
        emit Unstaked(msg.sender, amount, 0, 0);
    }
    
    // ========== ADMIN FUNCTIONS ==========
    
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
