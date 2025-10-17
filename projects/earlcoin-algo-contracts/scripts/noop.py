# scripts/noop.py
import os
from dotenv import load_dotenv
from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk import transaction as atxn

load_dotenv()
client = algod.AlgodClient(os.getenv("ALGOD_TOKEN",""), os.getenv("ALGOD_URL","https://testnet-api.algonode.cloud"), headers={"User-Agent":"algosdk"})
app_id = 747907984
sk = mnemonic.to_private_key(os.getenv("MNEMONIC").strip())
sender = account.address_from_private_key(sk)
sp = client.suggested_params()
txn = atxn.ApplicationNoOpTxn(sender, sp, app_id, app_args=[])  # add args if your router expects method name/selector
stx = txn.sign(sk)
txid = client.send_transaction(stx)
print("sent:", txid)
print("confirmed:", atxn.wait_for_confirmation(client, txid, 4)["confirmed-round"])
