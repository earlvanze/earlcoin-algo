import os
import base64
from algosdk.v2client import algod
from algosdk import account, mnemonic
from algosdk.transaction import ApplicationCreateTxn, StateSchema
from time import sleep

# Load environment variables if using a .env file
from dotenv import load_dotenv
load_dotenv()

# Configuration
ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS", "http://localhost:4001")
ALGOD_TOKEN   = os.getenv("ALGOD_TOKEN", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
MNEMONIC      = os.getenv("MNEMONIC")  # Ensure this is set in your environment

# Ensure mnemonic is valid
words = MNEMONIC.strip().split()
print("Mnemonic words:", len(words))
if len(words) != 25:
    raise Exception(f"Mnemonic length is {len(words)} words, but must be exactly 25.")

# Derive account
private_key = mnemonic.to_private_key(" ".join(words))
sender      = account.address_from_private_key(private_key)

# Initialize algod client
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

# Read compiled TEAL programs
with open("build/approval.teal", "r") as f:
    approval_teal = f.read()
with open("build/clear.teal", "r") as f:
    clear_teal = f.read()

# Compile the TEAL to bytecode
approval_response = client.compile(approval_teal)
clear_response    = client.compile(clear_teal)

# Decode base64 to raw bytes
approval_bytes = base64.b64decode(approval_response['result'])
clear_bytes    = base64.b64decode(clear_response['result'])

# Get network parameters
params = client.suggested_params()

# Create application transaction
txn = ApplicationCreateTxn(
    sender=sender,
    sp=params,
    on_complete=0,  # NoOp
    approval_program=approval_bytes,
    clear_program=clear_bytes,
    global_schema=StateSchema(num_uints=0, num_byte_slices=0),
    local_schema=StateSchema(num_uints=0, num_byte_slices=0),
)

# Sign and send transaction
signed_txn = txn.sign(private_key)
txid = client.send_transaction(signed_txn)
print("TXID:", txid)

# Wait for confirmation
print("Waiting for confirmation...")
while True:
    info = client.pending_transaction_info(txid)
    if info.get("confirmed-round", 0) > 0:
        print("Confirmed in round", info["confirmed-round"])
        print("Application ID:", info["application-index"])
        break
    sleep(1)
