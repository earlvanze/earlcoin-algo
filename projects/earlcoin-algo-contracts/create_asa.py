import os, json
from dotenv import load_dotenv
from algosdk import account, mnemonic, encoding
from algosdk.v2client import algod
from algosdk.transaction import AssetConfigTxn, SuggestedParams

load_dotenv()

ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN   = os.getenv("ALGOD_TOKEN", "")
MNEMONIC      = os.getenv("MNEMONIC", "").strip()
EARL_RESERVE  = os.getenv("EARL_RESERVE_ADDR", "").strip()

words = MNEMONIC.split()
if len(words) != 25:
    raise Exception("MNEMONIC must be 25 words")

sk = mnemonic.to_private_key(" ".join(words))
addr = account.address_from_private_key(sk)
print("Creator:", addr)

# Validate reserve address; default to creator if missing/invalid
if not EARL_RESERVE or not encoding.is_valid_address(EARL_RESERVE):
    print("WARNING: EARL_RESERVE_ADDR not set or invalid; defaulting to creator:", addr)
    EARL_RESERVE = addr

client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
params: SuggestedParams = client.suggested_params()

# 1,000,000,000 with 0 decimals (whole tokens)
total = 1_000_000_000
decimals = 0
unit_name = "EARL"
asset_name = "EarlCoin"
url = "https://earlco.in"

txn = AssetConfigTxn(
    sender=addr,
    sp=params,
    total=total,
    default_frozen=False,
    unit_name=unit_name,
    asset_name=asset_name,
    manager=addr,      # you can move to a DAO-controlled address later
    reserve=EARL_RESERVE, # keeps non-circulating tokens in reserve
    freeze=addr,       # can rotate later to DAO
    clawback=addr,     # can rotate later to DAO
    url=url,
    decimals=decimals,
)

stx = txn.sign(sk)
txid = client.send_transaction(stx)
print("Create ASA TXID:", txid)

# wait for confirmation
import time
while True:
    info = client.pending_transaction_info(txid)
    if info.get("confirmed-round", 0) > 0:
        print("Confirmed in round", info["confirmed-round"])
        asset_id = info["asset-index"]
        print("EARL ASA ID:", asset_id)
        break
    time.sleep(1)
