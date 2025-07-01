#!/usr/bin/env python3
"""
Update Django settings with live contract ABIs
"""
import json
import os

def load_abi(filename):
    """Load ABI from JSON file"""
    with open(filename, 'r') as f:
        return json.load(f)

def update_settings():
    """Update settings.py with live contract configurations"""
    
    # Load ABIs
    staking_abi = load_abi('blockchain/staking_abi.json')
    discount_abi = load_abi('blockchain/discount_abi.json')
    
    # Read current settings
    settings_file = 'schoolplatform/settings.py'
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Replace the discount contract ABI placeholder
    abi_placeholder = """TEOCOIN_DISCOUNT_CONTRACT_ABI = [
    # This will be populated when we deploy the contract
    # For now, it's a placeholder that will be updated
]"""
    
    abi_replacement = f"TEOCOIN_DISCOUNT_CONTRACT_ABI = {json.dumps(discount_abi, indent=4)}"
    
    content = content.replace(abi_placeholder, abi_replacement)
    
    # Add staking contract configuration if not present
    if 'TEOCOIN_STAKING_CONTRACT_ADDRESS' not in content:
        staking_config = f"""
# TeoCoin Staking Contract Configuration  
TEOCOIN_STAKING_CONTRACT_ADDRESS = os.getenv('TEOCOIN_STAKING_CONTRACT', '0xd74fc566c0c5b83f95fd82e6866d8a7a6eaca7a9')
TEOCOIN_STAKING_CONTRACT_ABI = {json.dumps(staking_abi, indent=4)}
"""
        # Insert before discount configuration
        insert_point = "# ========== TEOCOIN DISCOUNT SYSTEM CONFIGURATION =========="
        content = content.replace(insert_point, f"{staking_config}\n{insert_point}")
    
    # Write updated settings
    with open(settings_file, 'w') as f:
        f.write(content)
    
    print("✅ Settings updated with live contract ABIs")
    print(f"✅ Staking ABI: {len(staking_abi)} functions/events")
    print(f"✅ Discount ABI: {len(discount_abi)} functions/events")
    print("\n🔧 Next steps:")
    print("1. Restart Django server")
    print("2. Test staking service connection")
    print("3. Test discount service connection")

if __name__ == '__main__':
    update_settings()
