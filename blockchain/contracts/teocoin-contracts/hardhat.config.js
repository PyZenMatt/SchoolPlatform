require("dotenv").config();
require("@matterlabs/hardhat-zksync-solc");
require("@nomiclabs/hardhat-ethers");
// Only require etherscan plugin for Polygon networks
if (process.env.HARDHAT_NETWORK === 'polygon' || process.env.HARDHAT_NETWORK === 'polygonAmoy') {
  require("@nomiclabs/hardhat-etherscan");
} else {
  require("@matterlabs/hardhat-zksync-verify");
}

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  zksolc: {
    version: "1.4.1",
    compilerSource: "binary",
    settings: {
      optimizer: {
        enabled: true,
      },
    },
  },
  networks: {
    // zkSync Networks
    zkSyncSepoliaTestnet: {
      url: "https://sepolia.era.zksync.dev",
      ethNetwork: "sepolia",
      zksync: true,
      chainId: 300,
      verifyURL:
        "https://explorer.sepolia.era.zksync.dev/contract_verification",
    },
    zkSyncMainnet: {
      url: "https://mainnet.era.zksync.io",
      ethNetwork: "mainnet",
      zksync: true,
      chainId: 324,
      verifyURL:
        "https://zksync2-mainnet-explorer.zksync.io/contract_verification",
    },
    // Polygon Networks
    polygonAmoy: {
      url: "https://rpc-amoy.polygon.technology/",
      chainId: 80002,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      gasPrice: 30000000000, // 30 gwei
    },
    polygon: {
      url: "https://polygon-rpc.com/",
      chainId: 137,
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
      gasPrice: 30000000000, // 30 gwei
    },
    // Local development
    hardhat: {
      chainId: 31337
    }
  },
  etherscan: {
    apiKey: {
      polygon: process.env.POLYGONSCAN_API_KEY || "",
      polygonAmoy: process.env.POLYGONSCAN_API_KEY || ""
    },
    customChains: [
      {
        network: "polygonAmoy",
        chainId: 80002,
        urls: {
          apiURL: "https://api-amoy.polygonscan.com/api",
          browserURL: "https://amoy.polygonscan.com"
        }
      }
    ]
  },
  paths: {
    artifacts: "./artifacts-zk",
    cache: "./cache-zk",
    sources: "./contracts",
    tests: "./test",
  },
  solidity: {
    version: "0.8.19", // Updated to match our contracts
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
};
