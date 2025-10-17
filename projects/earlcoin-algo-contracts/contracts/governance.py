from pyteal import *


def approval():
    # OnCompletion helpers
    is_update   = Txn.on_completion() == OnComplete.UpdateApplication
    is_delete   = Txn.on_completion() == OnComplete.DeleteApplication
    is_optin    = Txn.on_completion() == OnComplete.OptIn
    is_closeout = Txn.on_completion() == OnComplete.CloseOut
    is_noop     = Txn.on_completion() == OnComplete.NoOp

    # Creator-only guard
    only_creator = Txn.sender() == Global.creator_address()

    # App call: set_param <uint fee>
    # Accepts a NoOp with at least two args where arg0 == "set_param"
    is_set_param = And(
        is_noop,
        Txn.application_args.length() >= Int(2),
        Txn.application_args[0] == Bytes("set_param"),
    )

    write_fee = Seq(
        App.globalPut(Bytes("fee"), Btoi(Txn.application_args[1])),
        Approve(),
    )

    return Cond(
        # Management ops must be by creator
        [is_update,   Seq(Assert(only_creator), Approve())],
        [is_delete,   Seq(Assert(only_creator), Approve())],

        # Setter: creator-only, writes global "fee"
        [is_set_param, Seq(Assert(only_creator), write_fee)],

        # Allow basic lifecycle ops (no local state used yet)
        [is_optin,    Approve()],
        [is_closeout, Approve()],
        [is_noop,     Approve()],

        # Fallback reject
        [Int(1),      Reject()],
    )


def clear():
    return Approve()
