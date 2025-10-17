# compile_contract.py
import os
from pyteal import compileTeal, Mode, Approve

# 1) Define your approval & clear programs
def approval_program():
    return Approve()

def clear_state_program():
    return Approve()

# 2) Ensure output folder
os.makedirs("build", exist_ok=True)

# 3) Compile & write TEAL
with open("build/approval.teal", "w") as f:
    f.write(compileTeal(approval_program(), mode=Mode.Application, version=6))

with open("build/clear.teal", "w") as f:
    f.write(compileTeal(clear_state_program(), mode=Mode.Application, version=6))

print("Compiled to build/approval.teal and build/clear.teal")
