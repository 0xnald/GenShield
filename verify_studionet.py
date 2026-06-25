import os
import json
import hashlib
from dotenv import load_dotenv
import genlayer_py

def main():
    load_dotenv()
    
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key or private_key == "your_private_key_here":
        print("Error: PRIVATE_KEY is not configured in the .env file.")
        return

    # Load contract address
    address_path = "deployed_addresses.json"
    if not os.path.exists(address_path):
        print(f"Error: {address_path} not found. Please run deploy_studionet.py first.")
        return
        
    with open(address_path, "r") as f:
        addresses = json.load(f)
        
    contract_address = addresses.get("studionet")
    if not contract_address:
        print("Error: Studionet contract address not found in deployed_addresses.json.")
        return
        
    print(f"Loaded GenShield contract address: {contract_address}")

    print("Initializing GenLayer client for Studionet...")
    account = genlayer_py.create_account(private_key)
    client = genlayer_py.create_client(chain=genlayer_py.studionet, account=account)
    
    # 1. Verify View Methods
    print("\n--- Verifying View Methods ---")
    try:
        owner = client.read_contract(contract_address, "get_owner")
        print(f"Contract Owner on-chain: {owner}")
        print(f"Your Account address:     {account.address}")
        
        min_fee = client.read_contract(contract_address, "get_min_fee")
        print(f"Minimum Fee on-chain:    {min_fee} Wei")
    except Exception as e:
        print(f"Error calling view methods: {e}")
        return

    # 2. Run a Live Security Audit
    print("\n--- Running Live Security Audit on Studionet ---")
    sample_code = (
        '# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }\n'
        'from genlayer import *\n'
        'class Target(gl.Contract):\n'
        '    val: u256\n'
        '    def __init__(self):\n'
        '        self.val = 0\n'
    )
    
    code_hash = hashlib.sha256(sample_code.encode('utf-8')).hexdigest()
    print(f"Sample contract code SHA-256 hash: {code_hash}")
    
    # Audit fee (must be >= min_fee)
    audit_fee = 1000
    
    print("Submitting sample contract for audit...")
    try:
        tx_hash = client.write_contract(
            address=contract_address,
            function_name="submit_audit",
            account=account,
            value=audit_fee,
            args=["SafeDummyContract", sample_code]
        )
        print(f"Audit transaction submitted. Hash: {tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash}")
        
        print("Waiting for audit transaction to reach consensus / finality...")
        receipt = client.wait_for_transaction_receipt(tx_hash)
        print("Audit transaction receipt received.")
        
        # Check transaction execution status
        print(f"Transaction status: {receipt.get('status')}")
        
        # 3. Query the Certificate
        print("\n--- Verifying Security Certificate ---")
        certificate = client.read_contract(
            contract_address,
            "get_certificate",
            args=[code_hash],
            account=account
        )
        
        if not certificate:
            print("No certificate was found for this code hash. The audit may have failed or consensus rejected the safety result.")
            print("Full receipt details:", json.dumps(receipt, default=str))
            return
            
        print("Successfully retrieved security certificate from GenShield!")
        print(json.dumps(certificate, indent=4))
        
    except Exception as e:
        print(f"Error during audit validation: {e}")

if __name__ == "__main__":
    main()
