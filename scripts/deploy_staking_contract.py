"""
TeoCoin Staking Contract Deployment Script

This script deploys the TeoCoinStaking contract to Polygon Amoy testnet
and sets up the initial configuration.

Requirements:
- Web3.py installed
- Private key with MATIC for gas fees
- TeoCoin2 contract already deployed at the specified address
"""

import os
import json
from web3 import Web3
from eth_account import Account
from solcx import compile_source, install_solc, set_solc_version

# Polygon Amoy Configuration
AMOY_RPC_URL = "https://rpc-amoy.polygon.technology/"
TEOCOIN_CONTRACT_ADDRESS = "0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8"
CHAIN_ID = 80002

# Deployment Configuration
DEPLOYER_PRIVATE_KEY = os.getenv('DEPLOYER_PRIVATE_KEY')  # Set in environment
CONTRACT_FILE_PATH = './blockchain/contracts/TeoCoinStaking.sol'

def setup_web3():
    """Initialize Web3 connection to Polygon Amoy"""
    web3 = Web3(Web3.HTTPProvider(AMOY_RPC_URL))
    
    if not web3.is_connected():
        raise Exception("Failed to connect to Polygon Amoy network")
    
    print(f"✅ Connected to Polygon Amoy")
    print(f"📡 Chain ID: {web3.eth.chain_id}")
    
    return web3

def compile_contract():
    """Compile the TeoCoinStaking smart contract"""
    print("🔧 Compiling TeoCoinStaking contract...")
    
    # Install and set Solidity version
    install_solc('0.8.19')
    set_solc_version('0.8.19')
    
    # Read contract source code
    with open(CONTRACT_FILE_PATH, 'r') as file:
        contract_source = file.read()
    
    # Add OpenZeppelin imports (simplified for deployment)
    contract_source_with_imports = f"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// Simplified interfaces for deployment
interface IERC20 {{
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}}

abstract contract ReentrancyGuard {{
    uint256 private constant _NOT_ENTERED = 1;
    uint256 private constant _ENTERED = 2;
    uint256 private _status;
    
    constructor() {{
        _status = _NOT_ENTERED;
    }}
    
    modifier nonReentrant() {{
        require(_status != _ENTERED, "ReentrancyGuard: reentrant call");
        _status = _ENTERED;
        _;
        _status = _NOT_ENTERED;
    }}
}}

abstract contract Ownable {{
    address private _owner;
    
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    
    constructor() {{
        _setOwner(msg.sender);
    }}
    
    function owner() public view virtual returns (address) {{
        return _owner;
    }}
    
    modifier onlyOwner() {{
        require(owner() == msg.sender, "Ownable: caller is not the owner");
        _;
    }}
    
    function _setOwner(address newOwner) private {{
        address oldOwner = _owner;
        _owner = newOwner;
        emit OwnershipTransferred(oldOwner, newOwner);
    }}
}}

abstract contract Pausable {{
    event Paused(address account);
    event Unpaused(address account);
    
    bool private _paused;
    
    constructor() {{
        _paused = false;
    }}
    
    function paused() public view virtual returns (bool) {{
        return _paused;
    }}
    
    modifier whenNotPaused() {{
        require(!paused(), "Pausable: paused");
        _;
    }}
    
    modifier whenPaused() {{
        require(paused(), "Pausable: not paused");
        _;
    }}
    
    function _pause() internal virtual whenNotPaused {{
        _paused = true;
        emit Paused(msg.sender);
    }}
    
    function _unpause() internal virtual whenPaused {{
        _paused = false;
        emit Unpaused(msg.sender);
    }}
}}

{contract_source.split('import')[4].split('/**')[1]}  // Skip imports, keep contract
"""
    
    # Compile the contract
    compiled_sol = compile_source(contract_source_with_imports)
    
    # Get contract interface
    contract_interface = compiled_sol['<stdin>:TeoCoinStaking']
    
    print("✅ Contract compiled successfully")
    return contract_interface

def deploy_contract(web3, contract_interface, deployer_account):
    """Deploy the TeoCoinStaking contract"""
    print(f"🚀 Deploying TeoCoinStaking contract...")
    print(f"📍 Deployer: {deployer_account.address}")
    print(f"💰 Balance: {web3.from_wei(web3.eth.get_balance(deployer_account.address), 'ether')} MATIC")
    
    # Create contract instance
    contract = web3.eth.contract(
        abi=contract_interface['abi'],
        bytecode=contract_interface['bytecode']
    )
    
    # Estimate gas
    gas_estimate = contract.constructor(TEOCOIN_CONTRACT_ADDRESS).estimate_gas()
    print(f"⛽ Estimated gas: {gas_estimate}")
    
    # Build transaction
    transaction = contract.constructor(TEOCOIN_CONTRACT_ADDRESS).build_transaction({
        'chainId': CHAIN_ID,
        'gas': int(gas_estimate * 1.2),  # Add 20% buffer
        'gasPrice': web3.to_wei('30', 'gwei'),  # Polygon Amoy gas price
        'nonce': web3.eth.get_transaction_count(deployer_account.address),
    })
    
    # Sign and send transaction
    signed_txn = web3.eth.account.sign_transaction(transaction, DEPLOYER_PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    
    print(f"📤 Transaction sent: {tx_hash.hex()}")
    print("⏳ Waiting for confirmation...")
    
    # Wait for transaction receipt
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if tx_receipt.status == 1:
        print(f"✅ Contract deployed successfully!")
        print(f"📍 Contract Address: {tx_receipt.contractAddress}")
        print(f"📊 Gas Used: {tx_receipt.gasUsed}")
        print(f"🔗 View on PolygonScan: https://amoy.polygonscan.com/address/{tx_receipt.contractAddress}")
        
        return tx_receipt.contractAddress, contract_interface['abi']
    else:
        raise Exception("Contract deployment failed")

def save_deployment_info(contract_address, abi):
    """Save deployment information for backend integration"""
    deployment_info = {
        "network": "Polygon Amoy",
        "chainId": CHAIN_ID,
        "stakingContractAddress": contract_address,
        "teoTokenAddress": TEOCOIN_CONTRACT_ADDRESS,
        "deploymentTime": int(time.time()),
        "abi": abi
    }
    
    # Save to blockchain directory
    with open('./blockchain/teocoin_staking_abi.py', 'w') as f:
        f.write(f'''"""
TeoCoin Staking Contract ABI and Configuration

Deployed on Polygon Amoy testnet
Contract Address: {contract_address}
Deployment Date: {time.strftime('%Y-%m-%d %H:%M:%S')}
"""

STAKING_CONTRACT_ADDRESS = "{contract_address}"
TEOCOIN_CONTRACT_ADDRESS = "{TEOCOIN_CONTRACT_ADDRESS}"
POLYGON_AMOY_CHAIN_ID = {CHAIN_ID}

STAKING_ABI = {json.dumps(abi, indent=2)}
''')
    
    print(f"💾 Deployment info saved to blockchain/teocoin_staking_abi.py")

def verify_deployment(web3, contract_address, abi):
    """Verify the deployed contract works correctly"""
    print("🔍 Verifying deployment...")
    
    contract = web3.eth.contract(address=contract_address, abi=abi)
    
    try:
        # Test read functions
        total_staked = contract.functions.totalStaked().call()
        total_stakers = contract.functions.totalStakers().call()
        
        # Test tier info
        tier_info = contract.functions.getTierInfo(0).call()  # Bronze tier
        
        print(f"✅ Contract verification successful!")
        print(f"📊 Total Staked: {total_staked} TEO")
        print(f"👥 Total Stakers: {total_stakers}")
        print(f"🥉 Bronze Tier: {tier_info[2]} (Commission: {tier_info[1]/100}%)")
        
        return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 TeoCoin Staking Contract Deployment")
    print("=" * 50)
    
    # Check environment
    if not DEPLOYER_PRIVATE_KEY:
        raise Exception("DEPLOYER_PRIVATE_KEY environment variable not set")
    
    # Setup
    web3 = setup_web3()
    deployer_account = Account.from_key(DEPLOYER_PRIVATE_KEY)
    
    # Compile
    contract_interface = compile_contract()
    
    # Deploy
    contract_address, abi = deploy_contract(web3, contract_interface, deployer_account)
    
    # Save deployment info
    save_deployment_info(contract_address, abi)
    
    # Verify
    verify_deployment(web3, contract_address, abi)
    
    print("\n🎉 Deployment completed successfully!")
    print(f"Next steps:")
    print(f"1. Update your backend to use contract address: {contract_address}")
    print(f"2. Test staking functionality on Amoy testnet")
    print(f"3. Integrate with frontend")

if __name__ == "__main__":
    import time
    main()
