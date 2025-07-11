const hre = require("hardhat");

async function main() {
  console.log("🚀 Deploying Gas-Free TeoCoin Contracts to Polygon Amoy...\n");

  // Get the deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", (await deployer.getBalance()).toString());

  // Contract addresses from existing system
  const TEO_TOKEN_ADDRESS = "0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8"; // Existing TEO token
  const REWARD_POOL_ADDRESS = "0x3b72a4E942CF1467134510cA3952F01b63005044"; // Existing reward pool
  const PLATFORM_ACCOUNT = "0x17051AB7603B0F7263BC86bF1b0ce137EFfdEcc1"; // Platform account that pays gas fees

  console.log("\nUsing existing addresses:");
  console.log("TEO Token:", TEO_TOKEN_ADDRESS);
  console.log("Reward Pool:", REWARD_POOL_ADDRESS);
  console.log("Platform Account:", PLATFORM_ACCOUNT);

  // Deploy TeoCoinDiscountGasFree
  console.log("\n📋 Deploying TeoCoinDiscountGasFree...");
  const TeoCoinDiscountGasFree = await hre.ethers.getContractFactory("TeoCoinDiscountGasFree");
  const discountGasFree = await TeoCoinDiscountGasFree.deploy(
    TEO_TOKEN_ADDRESS,
    REWARD_POOL_ADDRESS,
    PLATFORM_ACCOUNT
  );

  await discountGasFree.deployed();
  console.log("✅ TeoCoinDiscountGasFree deployed to:", discountGasFree.address);

  // Deploy TeoCoinStakingGasFree
  console.log("\n🏆 Deploying TeoCoinStakingGasFree...");
  const TeoCoinStakingGasFree = await hre.ethers.getContractFactory("TeoCoinStakingGasFree");
  const stakingGasFree = await TeoCoinStakingGasFree.deploy(
    TEO_TOKEN_ADDRESS,
    REWARD_POOL_ADDRESS, // Using reward pool as staking pool
    PLATFORM_ACCOUNT
  );

  await stakingGasFree.deployed();
  console.log("✅ TeoCoinStakingGasFree deployed to:", stakingGasFree.address);

  // Wait for a few confirmations before verification
  console.log("\n⏳ Waiting for block confirmations...");
  await discountGasFree.deployTransaction.wait(3);
  await stakingGasFree.deployTransaction.wait(3);

  // Verify contracts on PolygonScan
  if (hre.network.name === "polygonAmoy") {
    console.log("\n🔍 Verifying contracts on PolygonScan...");
    
    try {
      await hre.run("verify:verify", {
        address: discountGasFree.address,
        constructorArguments: [
          TEO_TOKEN_ADDRESS,
          REWARD_POOL_ADDRESS,
          PLATFORM_ACCOUNT
        ],
      });
      console.log("✅ TeoCoinDiscountGasFree verified");
    } catch (error) {
      console.log("⚠️ TeoCoinDiscountGasFree verification failed:", error.message);
    }

    try {
      await hre.run("verify:verify", {
        address: stakingGasFree.address,
        constructorArguments: [
          TEO_TOKEN_ADDRESS,
          REWARD_POOL_ADDRESS,
          PLATFORM_ACCOUNT
        ],
      });
      console.log("✅ TeoCoinStakingGasFree verified");
    } catch (error) {
      console.log("⚠️ TeoCoinStakingGasFree verification failed:", error.message);
    }
  }

  // Test basic functionality
  console.log("\n🧪 Testing basic functionality...");
  
  // Test discount contract
  const gasFreeMode = await discountGasFree.isGasFreeEnabled();
  console.log("Gas-free mode enabled:", gasFreeMode);
  
  // Test staking contract tiers
  const bronzeTier = await stakingGasFree.getTierInfo(0);
  console.log("Bronze tier:", bronzeTier.tierName, "- Commission:", bronzeTier.commissionRate, "bp");

  // Display deployment summary
  console.log("\n" + "=".repeat(80));
  console.log("🎉 DEPLOYMENT COMPLETE!");
  console.log("=".repeat(80));
  console.log("Network:", hre.network.name);
  console.log("Block:", await hre.ethers.provider.getBlockNumber());
  console.log("");
  console.log("📋 TeoCoinDiscountGasFree:");
  console.log("   Address:", discountGasFree.address);
  console.log("   Gas-Free Mode:", gasFreeMode);
  console.log("");
  console.log("🏆 TeoCoinStakingGasFree:");
  console.log("   Address:", stakingGasFree.address);
  console.log("   Total Tiers:", 5);
  console.log("");
  console.log("💰 Platform Economics:");
  console.log("   Gas Cost per Discount: ~$0.001-0.004 USD");
  console.log("   Gas Cost per Staking: ~$0.002-0.008 USD");
  console.log("   Monthly Platform Cost: ~$15-60 USD");
  console.log("");
  console.log("🔧 Environment Variables to Add:");
  console.log(`TEOCOIN_DISCOUNT_GAS_FREE_CONTRACT=${discountGasFree.address}`);
  console.log(`TEOCOIN_STAKING_GAS_FREE_CONTRACT=${stakingGasFree.address}`);
  console.log(`PLATFORM_PRIVATE_KEY=${deployer.address} # Your platform wallet private key`);
  console.log("");
  console.log("✅ Ready for Phase 2: Backend Integration");
  console.log("=".repeat(80));
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
