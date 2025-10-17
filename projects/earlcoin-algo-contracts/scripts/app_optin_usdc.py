import os
from dotenv import load_dotenv
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import ApplicationNoOpTxn, wait_for_confirmation

load_dotenv()
ALGOD_URL = os.getenv("ALGOD_URL","https://testnet-api.algonode.cloud")
ALGOD_TOKEN = os.getenv("ALGOD_TOKEN","")
MN = os.getenv("MNEMONIC","").strip()
APP_ID = int(os.getenv("GOV_APP_ID","0"))

client = algod.AlgodClient(ALGOD_TOKEN, ALGOD_URL)
sk = mnemonic.to_private_key(MN)
addr = account.address_from_private_key(sk)

sp = client.suggested_params()
txn = ApplicationNoOpTxn(addr, sp, APP_ID, app_args=[b"optin"])
stx = txn.sign(sk)
txid = client.send_transaction(stx)
wait_for_confirmation(client, txid, 4)
print("✅ App opted-in to USDC via inner txn:", txid)
