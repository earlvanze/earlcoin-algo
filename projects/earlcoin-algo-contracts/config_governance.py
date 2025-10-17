# config_governance.py
import os, time
from dotenv import load_dotenv
from algosdk.v2client import algod
from algosdk import account, mnemonic
from algosdk.transaction import ApplicationCallTxn

load_dotenv()
ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN   = os.getenv("ALGOD_TOKEN", "")
MNEMONIC      = os.getenv("MNEMONIC", "").strip()

GOV_APP_ID    = int(os.getenv("GOV_APP_ID", "747907984"))
EARL_ASA_ID   = int(os.getenv("EARL_ASA_ID", "747899490"))
KYC_NFT_ID    = int(os.getenv("KYC_NFT_ID", "747899498"))
USDC_ASSET_ID = int(os.getenv("USDC_ASSET_ID", "10458941"))

sk = mnemonic.to_private_key(MNEMONIC)
addr = account.address_from_private_key(sk)
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
params = client.suggested_params()

args = [
    b"config",
    EARL_ASA_ID.to_bytes(8, "big"),
    KYC_NFT_ID.to_bytes(8, "big"),
    USDC_ASSET_ID.to_bytes(8, "big"),
]

txn = ApplicationCallTxn(
    sender=addr, sp=params, index=GOV_APP_ID, app_args=args
)
stx = txn.sign(sk)
txid = client.send_transaction(stx)
print("Config TXID:", txid)

while True:
    info = client.pending_transaction_info(txid)
    if info.get("confirmed-round", 0) > 0:
        print("Configured in round", info["confirmed-round"])
        break
    time.sleep(1)
