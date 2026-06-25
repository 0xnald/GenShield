import os
import json
from dotenv import load_dotenv
import genlayer_py

def main():
    load_dotenv()
    
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key or private_key == "your_private_key_here":
        print("Error: PRIVATE_KEY is not configured in the .env file.")
        print("Please configure PRIVATE_KEY in .env with your private key hex and try again.")
        return

    print("Initializing GenLayer client for Bradbury Testnet...")
    client = genlayer_py.create_client(chain=genlayer_py.testnet_bradbury)
    
    # Create the deployer account from the private key
    account = genlayer_py.create_account(private_key)
    print(f"Deployer address: {account.address}")
    
    # Read contract code
    contract_path = os.path.join(os.path.dirname(__file__), "contracts", "genshield.py")
    with open(contract_path, "r", encoding="utf-8") as f:
        code = f.read()
    
    print("Deploying GenShield contract to Bradbury Testnet...")
    # Minimum fee of 1000 Wei for audits
    min_fee = 1000
    
    try:
        tx_hash = client.deploy_contract(code, account=account, args=[min_fee])
        print(f"Deployment transaction submitted. Hash: {tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash}")
        
        print("Waiting for deployment transaction to be accepted...")
        receipt = client.wait_for_transaction_receipt(tx_hash)
        print("Transaction receipt received.")
        
        # Extract contract address
        contract_address = receipt.get("data", {}).get("contract_address")
        if not contract_address:
            contract_address = receipt.get("txDataDecoded", {}).get("contractAddress")
            
        if not contract_address:
            print("Could not find contract address automatically. Receipt keys:", list(receipt.keys()))
            print("Full receipt:", json.dumps(receipt, default=str))
            return
            
        print(f"Successfully deployed GenShield contract on Bradbury!")
        print(f"Contract Address: {contract_address}")
        
        # Load existing deployed addresses if file exists
        addresses = {}
        address_path = "deployed_addresses.json"
        if os.path.exists(address_path):
            with open(address_path, "r") as f:
                addresses = json.load(f)
                
        addresses["bradbury"] = contract_address
        with open(address_path, "w") as f:
            json.dump(addresses, f, indent=4)
        print("Saved address to deployed_addresses.json")
        
    except Exception as e:
        print(f"Error during deployment: {e}")

if __name__ == "__main__":
    main()
