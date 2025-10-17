from pyteal import *

def approval():
    is_update = Txn.on_completion() == OnComplete.UpdateApplication
    is_delete = Txn.on_completion() == OnComplete.DeleteApplication
    only_creator = Txn.sender() == Global.creator_address()

    return Cond(
        [is_update, Seq(Assert(only_creator), Approve())],
        [is_delete, Seq(Assert(only_creator), Approve())],
        # everything else: allow for now
        [Int(1), Approve()],
    )

def clear():
    return Approve()
