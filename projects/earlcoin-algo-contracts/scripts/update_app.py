# scripts/update_app.py
import os, base64
from pathlib import Path
from algosdk import transaction as atxn
from dotenv import load_dotenv
from algosdk import account, mnemonic
from algosdk.v2client import algod

load_dotenv()
ALGOD_URL = os.getenv("ALGOD_URL", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN = os.getenv("ALGOD_TOKEN","")
MNEMONIC = os.getenv("MNEMONIC","").strip()
APP_ID = int(os.getenv("GOV_APP_ID", "0"))

if not MNEMONIC:
    raise SystemExit("MNEMONIC is missing in environment")
if APP_ID <= 0:
    raise SystemExit("GOV_APP_ID must be set to a positive integer")

# Resolve TEAL paths
base = Path(__file__).resolve().parents[1] / "build" / "governance"
approval_path = base / "approval.teal"
clear_path = base / "clear.teal"
if not approval_path.exists() or not clear_path.exists():
    raise SystemExit(f"Missing TEAL; expected {approval_path} and {clear_path}. Run: poetry run python compile_governance.py")

with open(approval_path, "r") as f:
    approval_teal = f.read()
with open(clear_path, "r") as f:
    clear_teal = f.read()

# Client + keys
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL, headers={"User-Agent": "algosdk"})
sk = mnemonic.to_private_key(MNEMONIC)
sender = account.address_from_private_key(sk)
print(f"Updating APP_ID={APP_ID} as sender={sender}")

# Compile TEAL source to program bytes
comp_approval = client.compile(approval_teal)
approval_prog = base64.b64decode(comp_approval["result"])
comp_clear = client.compile(clear_teal)
clear_prog = base64.b64decode(comp_clear["result"])

# Fee/params
sp = client.suggested_params()

# Build update Tx
txn = atxn.ApplicationUpdateTxn(
    sender=sender,
    sp=sp,
    index=APP_ID,
    approval_program=approval_prog,
    clear_program=clear_prog,
)

stx = txn.sign(sk)
txid = client.send_transaction(stx)
result = atxn.wait_for_confirmation(client, txid, 4)
app_txn = result.get("txn", {}).get("txn", {})
print("Update confirmed in round:", result.get("confirmed-round"))
print("Txn type:", app_txn.get("type"))
print("App ID:", app_txn.get("apid", APP_ID))
