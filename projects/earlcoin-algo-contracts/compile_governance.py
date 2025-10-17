# compile_governance.py
import os
from pyteal import *
from contracts.governance import approval, clear

out = "build/governance"
os.makedirs(out, exist_ok=True)

with open(f"{out}/approval.teal", "w") as f:
    f.write(compileTeal(approval(), Mode.Application, version=8))

with open(f"{out}/clear.teal", "w") as f:
    f.write(compileTeal(clear(), Mode.Application, version=8))

print("Governance TEAL written to build/governance/")
