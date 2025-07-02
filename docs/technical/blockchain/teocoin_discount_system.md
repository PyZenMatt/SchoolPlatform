📚 Overview

The TeoCoinDiscount contract powers a gasless, user-friendly discount system for an educational platform using the TeoCoin ERC-20 token. It allows students to request course discounts using TEO, while teachers can approve or reject them. The platform pays all gas fees to ensure a seamless experience.
🛠️ Key Features

    ⛽ Gasless Requests: Students initiate requests without paying gas

    🧾 Teacher Approval: Teachers approve/decline requests manually or via platform backend

    🎁 Teacher Bonus: Reward pool sends a bonus to teachers upon approval

    ⏰ Auto Expiration: Discount requests expire after 2 hours if not acted upon

    🔒 Pre-approved Signatures: Students sign discount requests off-chain using ECDSA

    🔐 Security: Built with OpenZeppelin libraries (ReentrancyGuard, Ownable, Pausable)

    📜 Audit-Friendly: Modular, readable structure for easy testing and review

📑 Contract Metadata
Field	Description
Contract Name	TeoCoinDiscount
Token Used	IERC20 (TEO)
Network	Polygon Amoy (Layer 2 testnet)
Role Access	onlyPlatform, onlyOwner
Reward Source	rewardPool address
Platform Gas Payer	platformAccount
Discount Range	5%, 10%, 15%
Bonus Percentage	25% (e.g., 30 TEO = 38 TEO to teacher)
TEO/EUR Rate	10 (1 TEO = €0.10 equivalent)
Timeout	2 hours (auto-expire)
🧩 Core Struct: DiscountRequest

struct DiscountRequest {
    uint256 requestId;
    address student;
    address teacher;
    uint256 courseId;
    uint256 coursePrice;      // In EUR cents
    uint256 discountPercent;  // 5, 10, or 15
    uint256 teoCost;          // TEO amount required
    uint256 teacherBonus;     // Bonus TEO from reward pool
    uint256 createdAt;
    uint256 deadline;
    DiscountStatus status;
    bytes studentSignature;   // ECDSA pre-approval
}

🚦 Lifecycle of a Discount Request

    Student signs a request off-chain

    Platform (backend) calls createDiscountRequest(...)

    Contract verifies TEO balances + signature

    Teacher is notified (off-chain) and decides

    Platform calls:

        approveDiscountRequest() → TEO is transferred

        declineDiscountRequest() → request closed with reason

    If no action after 2 hours → request auto-expires

🔐 Security Features
Feature	Description
nonReentrant	Prevents double-spending / re-entry attacks
onlyPlatform	Restricts write access to backend service
Pausable	Allows emergency pause
Signature Verification	Prevents impersonation / unauthorized use
Token Balance Checks	Ensures student and reward pool sufficiency
🔍 Events

    DiscountRequested(requestId, student, teacher, courseId, discountPercent, teoCost)

    DiscountApproved(requestId, student, teacher, teoCost, teacherBonus)

    DiscountDeclined(requestId, student, teacher, reason)

    DiscountExpired(requestId, student, teacher)

    RewardPoolUpdated(oldPool, newPool)

    PlatformAccountUpdated(old, new)

📈 Public Functions
Function	Description
createDiscountRequest(...)	Creates new request from student via platform
approveDiscountRequest(uint256)	Approves and processes TEO transfers
declineDiscountRequest(uint256, string)	Declines the request
processExpiredRequests(uint256[])	Marks requests as expired
getDiscountRequest(uint256)	View single request details
getStudentRequests(address)	All student requests
getTeacherRequests(address)	All teacher requests
calculateTeoCost(coursePrice, discountPercent)	Preview cost and bonus
🔧 Admin Functions

    pause() / unpause() – Temporarily disables interactions

    updateRewardPool(address) – Sets new reward pool address

    updatePlatformAccount(address) – Changes platform executor

✅ Deployment Checklist

Token deployed & verified (IERC20)

Platform backend holds platformAccount private key

Reward pool has sufficient TEO balance

Students sign using MetaMask or Web3 SDK

Contract is deployed and verified on PolygonScan