# scripts/call_set_param.py
import os
from dotenv import load_dotenv
from algosdk.v2client import algod
from algosdk import account, mnemonic
import base64
from algosdk.transaction import ApplicationNoOpTxn

load_dotenv()
client = algod.AlgodClient(os.getenv("ALGOD_TOKEN",""), os.getenv("ALGOD_URL","https://testnet-api.algonode.cloud"))
app_id = int(os.getenv("APP_ID"))
sk = mnemonic.to_private_key(os.getenv("MNEMONIC").strip())
sender = account.address_from_private_key(sk)

sp = client.suggested_params(); sp.flat_fee=True; sp.fee=2000
args = [b"set_param", (100000).to_bytes(8, "big")]  # fee = 100000
stx = ApplicationNoOpTxn(sender, sp, app_id, app_args=args).sign(sk)
txid = client.send_transaction(stx)
last = client.status()["last-round"]
while True:
    p = client.pending_transaction_info(txid)
    if p.get("confirmed-round",0) > 0: break
    last += 1; client.status_after_block(last)
print("set_param confirmed in round", p["confirmed-round"])
app_info = client.application_info(app_id)
params = app_info.get("params", {})
raw_gs = params.get("global-state", [])
if not raw_gs:
    print("No global state entries (yet).")

    # --- Also inspect boxes and the caller's local state ---
    try:
        # List all boxes (names come base64-encoded)
        boxes = client.application_boxes(app_id).get("boxes", [])
        if not boxes:
            print("No boxes found for this app.")
        else:
            print(f"Found {len(boxes)} box(es):")
            for b in boxes:
                name_b64 = b.get("name", "")
                name_bytes = base64.b64decode(name_b64) if name_b64 else b""
                # Fetch each box content
                try:
                    bx = client.application_box_by_name(app_id, name_bytes)
                    value_b64 = bx.get("value", "")
                    value_bytes = base64.b64decode(value_b64) if value_b64 else b""
                    # Try to pretty-decode; fall back to raw
                    try:
                        pretty_val = value_bytes.decode("utf-8")
                    except Exception:
                        pretty_val = value_bytes.hex()
                    print(f"  box name={name_bytes!r} value={pretty_val}")
                except Exception as e:
                    print(f"  box name={name_bytes!r} error reading box: {e}")
    except Exception as e:
        print("Error listing boxes:", e)

    # Check local state for the sender (in case contract writes there)
    try:
        lai = client.account_application_info(sender, app_id)
        kv = lai.get("app-local-state", {}).get("key-value", [])
        if not kv:
            print("No local state for sender (or not opted in).")
        else:
            local_decoded = {}
            for e in kv:
                k = base64.b64decode(e["key"]).decode("utf-8", "ignore")
                v = e["value"]
                if v.get("type") == 1:
                    local_decoded[k] = v.get("uint", 0)
                elif v.get("type") == 2:
                    try:
                        local_decoded[k] = base64.b64decode(v.get("bytes", "")).decode("utf-8", "ignore")
                    except Exception:
                        local_decoded[k] = v.get("bytes", "")
                else:
                    local_decoded[k] = v
            print("Local state for sender:", local_decoded)
    except Exception as e:
        print("Error reading local state:", e)
else:
    decoded = {}
    for e in raw_gs:
        k = base64.b64decode(e["key"]).decode("utf-8", "ignore")
        v = e["value"]
        if v.get("type") == 1:  # uint
            decoded[k] = v.get("uint", 0)
        elif v.get("type") == 2:  # bytes
            try:
                decoded[k] = base64.b64decode(v.get("bytes", "")).decode("utf-8", "ignore")
            except Exception:
                decoded[k] = v.get("bytes", "")
        else:
            decoded[k] = v
    print("Global state:", decoded)
    if "fee" in decoded:
        print("fee=", decoded["fee"])
