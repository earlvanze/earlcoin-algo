import os, time
from dotenv import load_dotenv
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import AssetConfigTxn

load_dotenv()
ALGOD_ADDRESS = os.getenv("ALGOD_ADDRESS", "https://testnet-api.algonode.cloud")
ALGOD_TOKEN   = os.getenv("ALGOD_TOKEN", "")
MNEMONIC      = os.getenv("MNEMONIC", "").strip()

sk = mnemonic.to_private_key(MNEMONIC)
addr = account.address_from_private_key(sk)
client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS)
params = client.suggested_params()

# “KYC-OK” NFT class – large total; we’ll transfer exactly 1 to a wallet post-KYC
txn = AssetConfigTxn(
    sender=addr,
    sp=params,
    total=1_000_000,         # up to a million verified members
    default_frozen=False,
    unit_name="KYCOK",
    asset_name="EarlDAO KYC-Verified",
    manager=addr,
    reserve=addr,
    freeze=addr,
    clawback=addr,           # used to grant/revoke (1) token per verified wallet
    url="https://earlco.in/kyc",
    decimals=0,
)
stx = txn.sign(sk)
txid = client.send_transaction(stx)
print("Create KYC NFT TXID:", txid)

while True:
    info = client.pending_transaction_info(txid)
    if info.get("confirmed-round", 0) > 0:
        print("Confirmed in round", info["confirmed-round"])
        print("KYC NFT ASA ID:", info["asset-index"])
        break
    time.sleep(1)
