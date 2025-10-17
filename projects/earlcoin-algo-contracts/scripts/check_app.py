# scripts/check_app.py
import os
import base64
from hashlib import sha512
from dotenv import load_dotenv
from algosdk.v2client import algod

# Load env (ALGOD_URL, ALGOD_TOKEN, etc.)
load_dotenv()

ALGOD_URL = os.getenv("ALGOD_URL", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN = os.getenv("ALGOD_TOKEN", "")
# Add a default UA header so Algonode doesn't 403 anonymous Python requests
headers = {"User-Agent": "algosdk"}
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL, headers=headers)

# Allow overriding from env, else fallback to hardcoded for quick checks
app_id = int(os.getenv("APP_ID", "747907984"))

app = client.application_info(app_id)
params = app.get("params", {})

# Helper: compute sha512/256 (Algorand style) of program bytes
# Algorand program hash (as often shown by indexers) is sha512_256(program)
# We print it in hex for clarity.
def program_hash_from_b64(b64_prog: str) -> str:
    prog = base64.b64decode(b64_prog)
    return sha512(prog).digest()[:32].hex()

print(f"App {app_id} param keys: ", sorted(params.keys()))

# Try to read on-chain hash if present; otherwise compute it locally from the program bytes
approval_hash = params.get("approval-program-hash")
clear_hash = params.get("clear-state-program-hash")

if approval_hash is None and (ap := params.get("approval-program")):
    try:
        approval_hash = program_hash_from_b64(ap)
    except Exception as e:
        approval_hash = f"<could not compute: {e}>"

if clear_hash is None and (cp := params.get("clear-state-program")):
    try:
        clear_hash = program_hash_from_b64(cp)
    except Exception as e:
        clear_hash = f"<could not compute: {e}>"

print("approval hash:", approval_hash)
print("clear hash:", clear_hash)

# Also show program sizes for sanity
if params.get("approval-program"):
    print("approval program bytes:", len(base64.b64decode(params["approval-program"])))
if params.get("clear-state-program"):
    print("clear program bytes:", len(base64.b64decode(params["clear-state-program"])))
