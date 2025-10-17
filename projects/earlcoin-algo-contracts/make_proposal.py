# make_proposal.py
import os, time, base64
from dotenv import load_dotenv
from algosdk.v2client import algod
from algosdk import account, mnemonic
from algosdk.transaction import (
    ApplicationCallTxn, AssetTransferTxn, SuggestedParams, assign_group_id,
)

load_dotenv()
ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN   = os.getenv("ALGOD_TOKEN", "")
MNEMONIC      = os.getenv("MNEMONIC", "").strip()

GOV_APP_ID    = int(os.getenv("GOV_APP_ID", "0"))
USDC_ASSET_ID = int(os.getenv("USDC_ASSET_ID", "0"))

# change ONE_USDC if your USDC has different decimals
ONE_USDC = 1_000_000  # 6 decimals

ipfs_uri = os.getenv("IPFS_URI", "ipfs://bafy...")

sk = mnemonic.to_private_key(MNEMONIC)
addr = account.address_from_private_key(sk)
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
sp: SuggestedParams = client.suggested_params()

# Tx0: app call propose(ipfs_uri)
app_call = ApplicationCallTxn(
    sender=addr,
    sp=sp,
    index=GOV_APP_ID,
    app_args=[b"propose", ipfs_uri.encode()],
)

# Tx1: USDC transfer of exactly ONE_USDC to app addr
app_addr = client.application_info(GOV_APP_ID)["params"]["creator"]  # we can use app address instead:
app_address = client.application_info(GOV_APP_ID)["params"]["creator"]
# Actually use the current app address:
from algosdk.logic import get_application_address
app_address = get_application_address(GOV_APP_ID)

usdc_pay = AssetTransferTxn(
    sender=addr,
    sp=sp,
    index=USDC_ASSET_ID,
    receiver=app_address,
    amt=ONE_USDC,
)

group = assign_group_id([app_call, usdc_pay])
stx0 = group[0].sign(sk)
stx1 = group[1].sign(sk)

txid = client.send_transactions([stx0, stx1])
print("Propose TXID:", txid)

while True:
    info = client.pending_transaction_info(txid)
    if info.get("confirmed-round", 0) > 0:
        print("Proposal submitted in round", info["confirmed-round"])
        break
    time.sleep(1)
