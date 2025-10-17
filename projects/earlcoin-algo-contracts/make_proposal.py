# make_proposal.py
import os, time, base64, binascii
from dotenv import load_dotenv
from algosdk.v2client import algod
from algosdk import account, mnemonic
from algosdk.transaction import (
    ApplicationCallTxn, PaymentTxn, SuggestedParams, assign_group_id, OnComplete,
)

from datetime import datetime, timezone

load_dotenv()
ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN   = os.getenv("ALGOD_TOKEN", "")
MNEMONIC      = os.getenv("MNEMONIC", "").strip()

GOV_APP_ID    = int(os.getenv("GOV_APP_ID", "0"))


# amount of ALGO (in whole ALGOs) required to propose; default 5
FEE_ALGO = int(os.getenv("FEE_ALGO", "5"))
FEE_MICROALGOS = FEE_ALGO * 1_000_000  # 1 ALGO = 1_000_000 microAlgos

# Proposal metadata and timing
TITLE_URI = os.getenv("TITLE_URI", "ipfs://bafy.../title.txt")
DETAIL_HASH_HEX = os.getenv("DETAIL_HASH_HEX", "").strip()  # 64 hex chars (32 bytes), optional
START_DELAY_SEC = int(os.getenv("START_DELAY_SEC", "0"))     # seconds from now until start
DURATION_SEC    = int(os.getenv("DURATION_SEC", "3600"))     # default 1 hour

ipfs_uri = os.getenv("IPFS_URI", "ipfs://bafy...")

# Parse 32-byte detail hash if provided (optional)
raw_hex = DETAIL_HASH_HEX.strip()
# accept `0x` prefix if provided
if raw_hex.lower().startswith("0x"):
    raw_hex = raw_hex[2:]

if raw_hex:
    try:
        dh = binascii.unhexlify(raw_hex)
        if len(dh) != 32:
            print("WARN: DETAIL_HASH_HEX must be 64 hex chars (32 bytes); using empty hash instead.")
            detail_hash = b"\x00" * 32
        else:
            detail_hash = dh
    except binascii.Error:
        print("WARN: DETAIL_HASH_HEX is not valid hex; using empty hash instead.")
        detail_hash = b"\x00" * 32
else:
    # If not provided, use 32 zero bytes (clients can still verify off-chain content by URI)
    detail_hash = b"\x00" * 32

# Compute start/end times (UNIX seconds)
now_ts = int(time.time())
start_ts = now_ts + START_DELAY_SEC
end_ts = start_ts + max(1, DURATION_SEC)

sk = mnemonic.to_private_key(MNEMONIC)
addr = account.address_from_private_key(sk)
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
sp: SuggestedParams = client.suggested_params()
sp.flat_fee = True
sp.fee = 2000

# (safety: check DURATION_SEC and times are valid - see contract requirements)

# Tx0: app call propose(detail_uri, title_uri, detail_hash, start, end)
app_call = ApplicationCallTxn(
    sender=addr,
    sp=sp,
    index=GOV_APP_ID,
    on_complete=OnComplete.NoOpOC,
    app_args=[
        b"propose",
        ipfs_uri.encode(),
        TITLE_URI.encode(),
        detail_hash,
        end_ts.to_bytes(8, "big"),
        start_ts.to_bytes(8, "big"),
    ],
)

from algosdk.logic import get_application_address
app_address = get_application_address(GOV_APP_ID)

# Tx1: Pay the proposal fee of FEE_ALGO ALGOs to the app address (enforced in-program via group)
algo_pay = PaymentTxn(
    sender=addr,
    sp=sp,
    receiver=app_address,
    amt=FEE_MICROALGOS,
)

group = assign_group_id([app_call, algo_pay])
stx0 = group[0].sign(sk)
stx1 = group[1].sign(sk)

txid = client.send_transactions([stx0, stx1])

print("Propose TXID:", txid)
print(f"Proposer: {addr}")
print(f"Fee sent: {FEE_ALGO} ALGO")
print(f"Start: {start_ts} ({datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat()})")
print(f"End:   {end_ts} ({datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat()})")

while True:
    info = client.pending_transaction_info(txid)
    if info.get("confirmed-round", 0) > 0:
        print("Proposal submitted in round", info["confirmed-round"])
        break
    time.sleep(1)
