# scripts/deploy_app.py
import os
import base64
from pathlib import Path

from dotenv import load_dotenv
from algosdk.v2client import algod
from algosdk import account, mnemonic
from algosdk.transaction import (
    StateSchema,
    ApplicationCreateTxn,
    OnComplete,
)
from algosdk.logic import get_application_address

# ---- config / env
load_dotenv()
ALGOD_URL   = os.getenv("ALGOD_URL", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN = os.getenv("ALGOD_TOKEN", "")
MNEMONIC    = os.getenv("MNEMONIC", "").strip()

if not MNEMONIC:
    raise SystemExit("MNEMONIC not set in environment (.env)")

# ---- clients
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL)

# ---- ensure TEAL artifacts (uses your minimal governance.py)
def ensure_teal():
    appr_path  = Path("build/governance/approval.teal")
    clear_path = Path("build/governance/clear.teal")
    if appr_path.exists() and clear_path.exists():
        return appr_path, clear_path

    # Compile from PyTeal -> TEAL (no business logic, just Approve())
    from pyteal import compileTeal, Mode
    from contracts.governance import approval, clear

    appr_path.parent.mkdir(parents=True, exist_ok=True)
    appr_path.write_text(compileTeal(approval(), Mode.Application, version=8))
    clear_path.write_text(compileTeal(clear(), Mode.Application, version=8))
    return appr_path, clear_path

appr_path, clear_path = ensure_teal()
approval_teal = Path(appr_path).read_text()
clear_teal    = Path(clear_path).read_text()

# ---- compile TEAL at the node -> program bytes
def compile_teal(teal_src: str) -> bytes:
    res = client.compile(teal_src)
    return base64.b64decode(res["result"])

approval_prog = compile_teal(approval_teal)
clear_prog    = compile_teal(clear_teal)

# ---- creator keys
sk = mnemonic.to_private_key(MNEMONIC)
sender = account.address_from_private_key(sk)

print("Creator:", sender)

# ---- tx params
sp = client.suggested_params()
# flat fee for safety
sp.flat_fee = True
sp.fee = 2000  # 0.002 ALGO; bump if you add boxes/extra pages later

# ---- zero schema for this minimal app
global_schema = StateSchema(num_uints=0, num_byte_slices=0)
local_schema  = StateSchema(num_uints=0, num_byte_slices=0)

# ---- build + sign create txn
txn = ApplicationCreateTxn(
    sender=sender,
    sp=sp,
    on_complete=OnComplete.NoOpOC,
    approval_program=approval_prog,
    clear_program=clear_prog,
    global_schema=global_schema,
    local_schema=local_schema,
    extra_pages=0,
)

stx = txn.sign(sk)
txid = client.send_transaction(stx)

# ---- wait for confirmation (inline poller)
def wait_for_confirmation(client: algod.AlgodClient, txid: str, timeout=10):
    last = client.status()["last-round"]
    for _ in range(timeout):
        p = client.pending_transaction_info(txid)
        if "confirmed-round" in p and p["confirmed-round"] > 0:
            return p
        last += 1
        client.status_after_block(last)
    raise TimeoutError("Transaction not confirmed in {} rounds".format(timeout))

pending = wait_for_confirmation(client, txid, timeout=20)
app_id = pending["application-index"]
app_addr = get_application_address(app_id)

print("NEW_APP_ID:", app_id)
print("NEW_APP_ADDR:", app_addr)
