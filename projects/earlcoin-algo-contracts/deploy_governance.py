# deploy_governance.py
import os, base64, time
from dotenv import load_dotenv
from algosdk.v2client import algod
from algosdk import account, mnemonic
from algosdk.transaction import ApplicationCreateTxn, StateSchema

load_dotenv()

ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN   = os.getenv("ALGOD_TOKEN", "")
MNEMONIC      = os.getenv("MNEMONIC", "").strip()

sk = mnemonic.to_private_key(MNEMONIC)
addr = account.address_from_private_key(sk)
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)

with open("build/governance/approval.teal") as f: approval_teal = f.read()
with open("build/governance/clear.teal")     as f: clear_teal     = f.read()

ca = client.compile(approval_teal)
cc = client.compile(clear_teal)
apr = base64.b64decode(ca["result"])
clr = base64.b64decode(cc["result"])

params = client.suggested_params()
txn = ApplicationCreateTxn(
    sender=addr,
    sp=params,
    on_complete=0,
    approval_program=apr,
    clear_program=clr,
    global_schema=StateSchema(8, 8),
    local_schema=StateSchema(0, 0),
)

stx = txn.sign(sk)
txid = client.send_transaction(stx)
print("Create Governance TXID:", txid)

while True:
    info = client.pending_transaction_info(txid)
    if info.get("confirmed-round", 0) > 0:
        print("Governance App ID:", info["application-index"])
        break
    time.sleep(1)
