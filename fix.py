from web3 import Web3
import json

# BSC Mainnet RPC endpoint
BSC_RPC = "https://bsc-dataseed1.defibit.io/"  # or another RPC
CONTRACT_ADDRESS = "0x54a387e9f25A9636065Bce8D4E303312Bf93A011"
OWNER_ADDRESS = "0x0F9Bf01fe3b3eE9027CBf569383761ED55A0b5a2"
OWNER_PRIVATE_KEY = "ll0"



# === LOAD ABI ===
with open("omo.json") as f:
    CONTRACT_ABI = json.load(f)


# Connect to BSC
w3 = Web3(Web3.HTTPProvider(BSC_RPC))
assert w3.is_connected(), "Failed to connect to BSC node!"

# Prepare contract
contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDRESS), abi=CONTRACT_ABI)

# Get nonce for owner
nonce = w3.eth.get_transaction_count(OWNER_ADDRESS)

# Build the transaction
tx = contract.functions.enableTrading().build_transaction({
    'from': OWNER_ADDRESS,
    'nonce': nonce,
    'gas': 200000,  # adjust if needed
    'gasPrice': w3.to_wei('5', 'gwei'),  # adjust if needed
    'chainId': 56  # BSC Mainnet chain ID
})

# Sign the transaction
signed_tx = w3.eth.account.sign_transaction(tx, private_key=OWNER_PRIVATE_KEY)

# Send transaction
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

print(f"Transaction sent: {tx_hash.hex()}")

# Wait for confirmation (optional)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print(f"✅ Transaction confirmed in block: {receipt.blockNumber}")
