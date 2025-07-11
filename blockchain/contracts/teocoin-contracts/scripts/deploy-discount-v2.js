// Deploy ONLY GasFreeDiscountV2 Contract
// TeoCoinStakingGasFree is already deployed at: 0xf76AcA8FCA2B9dE25D4c77C1343DED80280976D4

const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 Deploying GasFreeDiscountV2 Contract to Polygon Amoy...");
    console.log("=" * 60);
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    
    // Get account balance
    const balance = await deployer.getBalance();
    console.log("Account balance:", ethers.utils.formatEther(balance), "MATIC");
    
    // Contract addresses (from your existing configuration)
    const TEO_TOKEN_ADDRESS = process.env.TEOCOIN_CONTRACT_ADDRESS || "0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8";
    const REWARD_POOL_ADDRESS = process.env.REWARD_POOL_ADDRESS || "0x17051AB7603B0F7263BC86bF1b0ce137EFfdEcc1";
    const PLATFORM_ACCOUNT_ADDRESS = process.env.PLATFORM_ACCOUNT_ADDRESS || deployer.address;
    
    console.log("TEO Token Address:", TEO_TOKEN_ADDRESS);
    console.log("Reward Pool Address:", REWARD_POOL_ADDRESS);
    console.log("Platform Account:", PLATFORM_ACCOUNT_ADDRESS);
    console.log("Existing Staking Contract:", "0xf76AcA8FCA2B9dE25D4c77C1343DED80280976D4");
    
    // Deploy GasFreeDiscountV2
    console.log("\n📝 Deploying GasFreeDiscountV2...");
    const GasFreeDiscountV2 = await ethers.getContractFactory("GasFreeDiscountV2");
    
    const discountContract = await GasFreeDiscountV2.deploy(
        TEO_TOKEN_ADDRESS,
        REWARD_POOL_ADDRESS,
        PLATFORM_ACCOUNT_ADDRESS
    );
    
    await discountContract.deployed();
    console.log("✅ GasFreeDiscountV2 deployed to:", discountContract.address);
    
    // Wait for block confirmation
    console.log("\n⏳ Waiting for block confirmations...");
    await discountContract.deployTransaction.wait(3);
    
    // Immediate validation tests
    console.log("\n🔍 Running deployment validation...");
    
    try {
        const gasFreeMode = await discountContract.isGasFreeEnabled();
        console.log("✅ Gas-free mode enabled:", gasFreeMode);
        
        const platformAccount = await discountContract.platformAccount();
        console.log("✅ Platform account:", platformAccount);
        
        const rewardPool = await discountContract.rewardPool();
        console.log("✅ Reward pool:", rewardPool);
        
        const teoTokenAddress = await discountContract.teoToken();
        console.log("✅ TEO token address:", teoTokenAddress);
        
        // Test calculation function
        const [teoCost, teacherBonus] = await discountContract.calculateTeoCost(10000, 10); // €100 with 10% discount
        console.log("✅ Test calculation (€100, 10%):", {
            teoCost: ethers.utils.formatEther(teoCost),
            teacherBonus: ethers.utils.formatEther(teacherBonus)
        });
        
    } catch (error) {
        console.error("❌ Validation error:", error.message);
    }
    
    // Contract verification (optional)
    if (process.env.POLYGONSCAN_API_KEY) {
        console.log("\n🔍 Verifying contract on PolygonScan...");
        try {
            await hre.run("verify:verify", {
                address: discountContract.address,
                constructorArguments: [
                    TEO_TOKEN_ADDRESS,
                    REWARD_POOL_ADDRESS,
                    PLATFORM_ACCOUNT_ADDRESS
                ],
            });
            console.log("✅ Contract verified on PolygonScan");
        } catch (error) {
            console.log("⚠️ Verification failed:", error.message);
        }
    }
    
    // Generate environment variables for backend
    console.log("\n📄 Environment Variables for Backend Settings:");
    console.log("=" * 60);
    console.log(`# Add these to your settings.py or .env file:`);
    console.log(`DISCOUNT_CONTRACT_V2_ADDRESS=${discountContract.address}`);
    console.log(`STAKING_CONTRACT_V2_ADDRESS=0xf76AcA8FCA2B9dE25D4c77C1343DED80280976D4`);
    console.log(`TEO_TOKEN_ADDRESS=${TEO_TOKEN_ADDRESS}`);
    console.log(`REWARD_POOL_ADDRESS=${REWARD_POOL_ADDRESS}`);
    console.log(`PLATFORM_ACCOUNT_ADDRESS=${PLATFORM_ACCOUNT_ADDRESS}`);
    
    // Save deployment info
    const deploymentInfo = {
        timestamp: new Date().toISOString(),
        network: "polygonAmoy",
        chainId: (await ethers.provider.getNetwork()).chainId,
        deployer: deployer.address,
        gasUsed: discountContract.deployTransaction.gasUsed?.toString() || "estimated ~500,000",
        contracts: {
            GasFreeDiscountV2: {
                address: discountContract.address,
                transactionHash: discountContract.deployTransaction.hash,
                status: "deployed"
            },
            TeoCoinStakingGasFree: {
                address: "0xf76AcA8FCA2B9dE25D4c77C1343DED80280976D4",
                status: "already_deployed"
            },
            TeoToken: {
                address: TEO_TOKEN_ADDRESS,
                status: "existing"
            },
            RewardPool: {
                address: REWARD_POOL_ADDRESS,
                status: "existing"
            }
        },
        configuration: {
            gasFreeMode: true,
            maxDiscountPercent: 15,
            teoToEurRate: 10,
            teacherBonusPercent: 25,
            requestTimeout: "24 hours"
        }
    };
    
    // Write deployment info to file
    const fs = require('fs');
    const path = require('path');
    const outputPath = path.join(__dirname, '..', '..', '..', 'deployment_info_v2_complete.json');
    fs.writeFileSync(outputPath, JSON.stringify(deploymentInfo, null, 2));
    console.log(`\n📁 Deployment info saved to: ${outputPath}`);
    
    console.log("\n🎉 Deployment completed successfully!");
    console.log("🔗 Next steps:");
    console.log("1. Update backend settings.py with new contract address");
    console.log("2. Test contract integration with backend");
    console.log("3. Deploy frontend components for gas-free discount flow");
    console.log("4. Set up student platform allowances");
    
    console.log("\n📊 Contract Summary:");
    console.log("• GasFreeDiscountV2:", discountContract.address);
    console.log("• TeoCoinStakingGasFree:", "0xf76AcA8FCA2B9dE25D4c77C1343DED80280976D4");
    console.log("• Network: Polygon Amoy Testnet");
    console.log("• Gas-free mode: ENABLED");
    
    return {
        discountContract: discountContract.address,
        stakingContract: "0xf76AcA8FCA2B9dE25D4c77C1343DED80280976D4"
    };
}

// Run deployment
if (require.main === module) {
    main()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error("❌ Deployment failed:", error);
            process.exit(1);
        });
}

module.exports = main;
