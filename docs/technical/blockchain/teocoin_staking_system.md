📚 Overview

The TeoCoinStaking contract powers a tiered staking system that allows teachers to stake TEO in exchange for reduced platform commission rates. It forms the foundation of SchoolPlatform’s creator incentive engine, offering tangible benefits for long-term platform contributors.
🛠️ Key Features

    🔁 Tiered staking system (Bronze → Diamond)

    📉 Lower commission rates for higher staked amounts

    ⛽ Fully gas-efficient (no reward emissions)

    🛡️ OpenZeppelin protections (ReentrancyGuard, Ownable, Pausable)

    🆘 Emergency withdrawal function for safety

    📊 Comprehensive stats and user insights

📑 Contract Metadata
Field	Description
Contract Name	TeoCoinStaking
Token Used	IERC20 (TEO)
Roles	owner (admin), all users stake freely
Staking Type	Passive locking (no yield, no reward mint)
Tier Range	0–4 (Bronze to Diamond)
Tier Determined By	Staked amount in TEO
Core Benefit	Reduced platform commission rate
🧱 Staking Tiers

tiers[0] = Bronze:   0 TEO     → 50% fee
tiers[1] = Silver:   100 TEO   → 44% fee
tiers[2] = Gold:     300 TEO   → 38% fee
tiers[3] = Platinum: 600 TEO   → 31% fee
tiers[4] = Diamond:  1000 TEO  → 25% fee

📌 Note: All amounts are in wei, so 100 TEO = 100 * 10^18
🔁 Staking Lifecycle

    User calls stake(amount)

        Transfers TEO into contract

        Updates tier and platform stats

    User receives new tier benefits

        Tier-based commission rate calculated on backend

    User can unstake(amount) anytime

        Tier is downgraded if crossing thresholds

    In case of issues, user can emergencyUnstake()

🧩 Core Structs
StakingTier

struct StakingTier {
    uint256 requiredAmount;
    uint256 commissionRate; // In basis points (2500 = 25%)
    string tierName;
}

StakingInfo

struct StakingInfo {
    uint256 amount;
    uint256 tier;         // 0-4
    uint256 stakingTime;
    bool active;
}

🔍 Main Functions
Function	Description
stake(uint256 amount)	Stake TEO to gain tier benefits
unstake(uint256 amount)	Withdraw some or all staked TEO
emergencyUnstake()	Emergency full withdrawal (no input)
getUserTier(user)	Returns tier index (0–4)
getUserCommissionRate(user)	Returns commission rate in basis points
getUserStakingInfo(user)	Returns full staking data + tier info
getTierInfo(index)	Returns tier config (name, amount, commission rate)
getStakingStats()	Returns platform-wide staking totals
🔐 Admin Functions
Function	Description
updateTier()	Modify a staking tier config (owner only)
pause() / unpause()	Emergency pause of contract
recoverTokens()	Owner can recover non-TEO tokens
📊 Event Emissions

    Staked(user, amount, newTier, totalStaked)

    Unstaked(user, amount, newTier, totalStaked)

    TierUpgraded(user, oldTier, newTier, stakedAmount)

    TierConfigurationUpdated(tierIndex, required, commissionRate, name)

🛡️ Security Notes

    ✅ ReentrancyGuard on all stake/unstake flows

    ✅ Allowance checked for transferFrom calls

    ✅ Immutable token reference

    ✅ Emergency functions included

    ⚠️ No rewards auto-generated → backend tracks bonus effects

🧠 Design Philosophy

This contract intentionally avoids:

    Inflation (no minting or emissions)

    Gas-heavy compounding logic

    External oracles

Instead, it prioritizes:

    UX simplicity

    Backend reward logic (tracked off-chain)

    Instant commission benefit via tier

🚀 Deployment Notes

    TEO token must be deployed and verified

    Platform backend can read tier → apply correct % commission

    Contract can be deployed to any EVM chain (e.g., Polygon, Base, Arbitrum)

📈 Recommended Use Case

    Teacher stakes TEO

    Backend detects new tier via getUserCommissionRate()

    Applies lower platform fee automatically in payout logic

    Frontend can show "You’ve reached GOLD – only 300 more TEO for PLATINUM!"