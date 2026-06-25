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

    print("Initializing GenLayer client for Studionet...")
    client = genlayer_py.create_client(chain=genlayer_py.studionet)
    
    # Create the deployer account from the private key
    account = genlayer_py.create_account(private_key)
    print(f"Deployer address: {account.address}")
    
    # Try to fund the account on Studionet
    # 10 GEN (10 * 10^18 Wei)
    fund_amount = 10 * (10**18)
    print(f"Requesting funds from Studionet faucet for {account.address}...")
    try:
        tx_hash = client.fund_account(account.address, fund_amount)
        print(f"Faucet transaction submitted. Hash: {tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash}")
        client.wait_for_transaction_receipt(tx_hash)
        print("Account successfully funded.")
    except Exception as e:
        print(f"Warning: Faucet request failed: {e}. Attempting deployment anyway...")
    
    # Read contract code
    contract_path = os.path.join(os.path.dirname(__file__), "contracts", "genshield.py")
    with open(contract_path, "r", encoding="utf-8") as f:
        code = f.read()
    
    print("Deploying GenShield contract to Studionet...")
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
            
        print(f"Successfully deployed GenShield contract!")
        print(f"Contract Address: {contract_address}")
        
        # Save address to deployed_addresses.json
        addresses = {"studionet": contract_address}
        with open("deployed_addresses.json", "w") as f:
            json.dump(addresses, f, indent=4)
        print("Saved address to deployed_addresses.json")
        
    except Exception as e:
        print(f"Error during deployment: {e}")

if __name__ == "__main__":
    main()
