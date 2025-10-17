from pyteal import *

# ---- Global keys ----
G_PROPOSAL_COUNTER = Bytes("p_counter")
G_EARL_ASA_ID = Bytes("earl_id")
G_KYC_NFT_ID  = Bytes("kyc_id")
G_USDC_ASA_ID = Bytes("usdc_id")

# ---- Proposal fields (stored in boxes) ----
P_CREATOR = Bytes("creator")
P_IPFS    = Bytes("ipfs")
P_START   = Bytes("start")
P_END     = Bytes("end")
P_YES     = Bytes("yes")
P_NO      = Bytes("no")

# 72 hours voting window
VOTE_WINDOW_SECS = Int(72 * 60 * 60)

# USDC (TestNet commonly 6 decimals)
ONE_USDC = Int(1_000_000)

# ---- Helpers ----

def proposal_box(pid: Expr) -> Expr:
    return Itob(pid)

def box_key(box: Expr, key: Expr) -> Expr:
    return Concat(box, Bytes(":"), key)

def bput(box: Expr, key: Expr, val: Expr):
    return App.box_put(box_key(box, key), val)

@Subroutine(TealType.none)
def assert_kyc(addr: Expr) -> Expr:
    bal = AssetHolding.balance(addr, App.globalGet(G_KYC_NFT_ID))
    return Seq(
        bal,
        Assert(bal.hasValue()),
        Assert(bal.value() >= Int(1)),
    )

@Subroutine(TealType.none)
def assert_deposit_usdc(txn_index: Expr) -> Expr:
    usdc = App.globalGet(G_USDC_ASA_ID)
    return Seq(
        Assert(Gtxn[txn_index].type_enum() == TxnType.AssetTransfer),
        Assert(Gtxn[txn_index].xfer_asset() == usdc),
        Assert(Gtxn[txn_index].asset_amount() == ONE_USDC),
        Assert(Gtxn[txn_index].asset_receiver() == Global.current_application_address()),
    )

@Subroutine(TealType.none)
def box_read_into(box_expr: Expr, key: Expr, dest: ScratchVar) -> Expr:
    read = App.box_get(box_key(box_expr, key))
    return Seq(
        read,
        Assert(read.hasValue()),
        dest.store(read.value()),
    )

# ---- Program ----

def approval():
    # Scratch vars MUST be defined before any use and within this function scope
    pid_sv  = ScratchVar(TealType.uint64)
    box_sv  = ScratchVar(TealType.bytes)
    end_sv  = ScratchVar(TealType.bytes)
    yes_sv  = ScratchVar(TealType.bytes)
    no_sv   = ScratchVar(TealType.bytes)
    w_sv    = ScratchVar(TealType.uint64)

    # on_create comes first
    on_create = Seq(
        App.globalPut(G_PROPOSAL_COUNTER, Int(0)),
        Approve(),
    )

    # local subroutine to open a proposal
    @Subroutine(TealType.none)
    def create_proposal(ipfs_uri: Expr) -> Expr:
        pid = App.globalGet(G_PROPOSAL_COUNTER)
        box = proposal_box(pid)
        now = Global.latest_timestamp()
        return Seq(
            bput(box, P_CREATOR, Txn.sender()),
            bput(box, P_IPFS, ipfs_uri),
            bput(box, P_START, Itob(now)),
            bput(box, P_END, Itob(now + VOTE_WINDOW_SECS)),
            bput(box, P_YES, Itob(Int(0))),
            bput(box, P_NO,  Itob(Int(0))),
            App.globalPut(G_PROPOSAL_COUNTER, pid + Int(1)),
        )

    # Predeclare balance expression (eval inside Seq)
    earl_bal_expr = AssetHolding.balance(Txn.sender(), App.globalGet(G_EARL_ASA_ID))

    # Branch: proposal creation (must be grouped with 1 USDC deposit in Gtxn[1])
    propose_branch = Seq(
        Assert(Global.group_size() == Int(2)),
        Assert(Txn.application_args.length() == Int(2)),
        assert_kyc(Txn.sender()),
        assert_deposit_usdc(Int(1)),
        create_proposal(Txn.application_args[1]),
        Approve(),
    )

    # Branch: vote (args: ["vote", pid:uint64, choice:bytes("yes"|"no")])
    vote_branch = Seq(
        Assert(Txn.application_args.length() == Int(3)),

        # store pid and compute box name
        pid_sv.store(Btoi(Txn.application_args[1])),
        box_sv.store(proposal_box(pid_sv.load())),

        # time window check
        box_read_into(box_sv.load(), P_END, end_sv),
        Assert(Global.latest_timestamp() <= Btoi(end_sv.load())),

        # voting weight = EARL balance
        earl_bal_expr,
        Assert(earl_bal_expr.hasValue()),
        w_sv.store(earl_bal_expr.value()),

        # tallies
        box_read_into(box_sv.load(), P_YES, yes_sv),
        box_read_into(box_sv.load(), P_NO,  no_sv),

        If(Txn.application_args[2] == Bytes("yes"))
        .Then(bput(box_sv.load(), P_YES, Itob(Btoi(yes_sv.load()) + w_sv.load())))
        .Else(bput(box_sv.load(), P_NO,  Itob(Btoi(no_sv.load())  + w_sv.load()))),

        Approve(),
    )

    # Branch: admin config
    config_branch = Seq(
        Assert(Txn.sender() == Global.creator_address()),
        Assert(Txn.application_args.length() == Int(4)),
        App.globalPut(G_EARL_ASA_ID, Btoi(Txn.application_args[1])),
        App.globalPut(G_KYC_NFT_ID,  Btoi(Txn.application_args[2])),
        App.globalPut(G_USDC_ASA_ID, Btoi(Txn.application_args[3])),
        Approve(),
    )

    handle_noop = Cond(
        [Txn.application_args[0] == Bytes("propose"), propose_branch],
        [Txn.application_args[0] == Bytes("vote"),    vote_branch],
        [Txn.application_args[0] == Bytes("config"),  config_branch],
    )

    return Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.NoOp, handle_noop],
    )


def clear():
    return Approve()
