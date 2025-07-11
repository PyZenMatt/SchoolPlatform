const hre = require("hardhat");

async function main() {
  console.log("🔍 Checking deployer account...\n");

  try {
    // Get the deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deployer address:", deployer.address);
    
    // Check balance
    const balance = await deployer.getBalance();
    console.log("Account balance:", hre.ethers.utils.formatEther(balance), "MATIC");
    
    // Check if we have enough gas for deployment
    const minBalance = hre.ethers.utils.parseEther("0.1"); // 0.1 MATIC minimum
    if (balance.lt(minBalance)) {
      console.log("❌ Insufficient MATIC for deployment. Please fund the account:");
      console.log("   - Go to https://faucet.polygon.technology/");
      console.log("   - Request MATIC for address:", deployer.address);
      console.log("   - Network: Polygon Amoy Testnet");
    } else {
      console.log("✅ Sufficient balance for deployment");
    }
    
  } catch (error) {
    console.error("❌ Error checking deployer:", error.message);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
