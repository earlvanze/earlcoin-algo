from pyteal import *

def approval_program():
    # Always approve transactions
    return Approve()

def clear_state_program():
    # Always approve clear operations
    return Approve()

if __name__ == "__main__":
    from pyteal import compileTeal, Mode
    import os

    # Ensure artifacts directory exists
    os.makedirs("artifacts/earlcoin", exist_ok=True)

    # Compile and write approval program
    approval_teal = compileTeal(approval_program(), mode=Mode.Application, version=6)
    with open("artifacts/earlcoin/approval.teal", "w") as f:
        f.write(approval_teal)

    # Compile and write clear state program
    clear_teal = compileTeal(clear_state_program(), mode=Mode.Application, version=6)
    with open("artifacts/earlcoin/clear.teal", "w") as f:
        f.write(clear_teal)
