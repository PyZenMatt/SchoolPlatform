# 🔐 TeoCoin Staking Deployment Guide

## Prerequisites Checklist ✅

### 1. Network & Dependencies
- ✅ Polygon Amoy connectivity verified
- ✅ Python dependencies installed (web3, py-solc-x, eth-account)
- ✅ TeoCoin2 contract verified at: `0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8`

### 2. Smart Contract Ready
- ✅ `TeoCoinStaking.sol` contract completed
- ✅ Realistic staking tiers for 10K TEO supply:
  - Bronze (0 TEO): 50% platform commission
  - Silver (100 TEO): 44% platform commission  
  - Gold (300 TEO): 38% platform commission
  - Platinum (600 TEO): 31% platform commission
  - Diamond (1,000 TEO): 25% platform commission

### 3. Deployment Scripts Ready
- ✅ `deploy_staking_contract.py` - Main deployment script
- ✅ `verify_deployment_ready.py` - Prerequisites checker
- ✅ `setup_deployment.sh` - Setup helper

## 🚀 Deployment Steps

### Step 1: Get Test MATIC
1. Visit: https://faucet.polygon.technology/
2. Select **Polygon Amoy**
3. Enter your wallet address
4. Request test MATIC (0.1 MATIC should be sufficient)

### Step 2: Set Up Private Key
```bash
# Export your MetaMask private key (testnet account only!)
export DEPLOYER_PRIVATE_KEY=your_test_private_key_here

# Verify setup
python3 scripts/verify_deployment_ready.py
```

### Step 3: Deploy Contract
```bash
# Run deployment
python3 scripts/deploy_staking_contract.py
```

### Step 4: Post-Deployment
The script will:
1. ✅ Deploy TeoCoinStaking contract to Amoy
2. ✅ Save deployment info to `deployment_info.json`
3. ✅ Verify contract deployment
4. ✅ Display contract address and next steps

## 🔒 Security Notes

- **NEVER** use mainnet private keys
- **NEVER** commit private keys to git
- Use a dedicated test account
- Only deploy to testnets initially

## 📁 Generated Files

After deployment:
- `deployment_info.json` - Contract address, ABI, and deployment details
- Console output with contract address and verification

## 🔄 Next Steps After Deployment

1. **Backend Integration**: Update `teocoin_staking_service.py` with contract address
2. **Frontend Integration**: Add staking UI components
3. **Testing**: Test stake/unstake functionality
4. **Documentation**: Update API docs with staking endpoints

## ⚡ Quick Commands

```bash
# Check if ready to deploy
python3 scripts/verify_deployment_ready.py

# Deploy (when ready)
python3 scripts/deploy_staking_contract.py

# Check deployment status
cat deployment_info.json
```

---

**Current Status**: ⏳ Ready to deploy - only missing DEPLOYER_PRIVATE_KEY
