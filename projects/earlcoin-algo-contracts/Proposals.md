Global (app) config (small, fixed)
	•	admin (address): who can pause/upgrade/param-set (often the creator/DAO multisig).
	•	treasury (address): where fees go (or the app address itself if escrowed).
	•	fee_amt (uint64): proposal fee in microAlgos (or 0).
	•	vote_asset (uint64): ASA ID used for voting weight (0 = ALGO balance / 1-acct-1-vote, etc).
	•	quorum_bps (uint64): quorum as basis points of total supply/eligible weight (e.g., 2000 = 20%).
	•	thresh_bps (uint64): pass threshold as basis points (e.g., >50% = 5001).
	•	min_duration / max_duration (uint64): voting window bounds in rounds or seconds.
	•	vetoer (address, optional): address able to veto in emergencies.
	•	nonce (uint64): monotonic value to avoid replay in certain flows (optional).
	•	version (uint64 | bytes): schema/app version so you can migrate cleanly.
	•	paused (uint64 bool): circuit breaker.

Per-proposal (box) fields

Use one box per proposal (e.g., name: b"p:" + itob(pid)), and encode a compact struct (ABI Tuple or raw packing). Suggested fields:

Identity & metadata
	•	pid (uint64): proposal ID.
	•	proposer (address): who created it.
	•	created_ts (uint64): creation timestamp (or round).
	•	title_uri (bytes): URI/IPFS CID for title/summary (optional to save space).
	•	detail_uri (bytes): IPFS CID/URL to full proposal text/spec.
	•	detail_hash (bytes32): hash (e.g., keccak256/sha256) of the off-chain payload to pin integrity.

Voting window
	•	start (uint64): start timestamp/round when voting opens.
	•	end (uint64): end timestamp/round when voting closes.
	•	snapshot (uint64): round/ts used to measure voting power consistently.

Rule set (snapshotted)
	•	quorum_bps (uint64)
	•	thresh_bps (uint64)
	•	vote_asset (uint64)
	•	voting_mode (uint64): enum (0=for/against/abstain, 1=multi-choice, 2=ranked…).
	•	options (uint64): number of options for multi-choice (>=2).

Tally
	•	for (uint128 as two uint64s, or uint64 if you know it fits)
	•	against (same)
	•	abstain (same)
	•	option_i (array for multi-choice; either store in a separate box b"t:"+itob(pid) or as a dynamic ABI array if you’re comfortable with parsing).
	•	total_weight (uint128/uint64): running total to save re-sums.

Status / lifecycle
	•	state (uint64 enum): 0=Pending, 1=Active, 2=Succeeded, 3=Defeated, 4=Queued, 5=Executed, 6=Cancelled, 7=Vetoed, 8=Expired.
	•	executed (uint64 bool)
	•	cancelled (uint64 bool)
	•	vetoed (uint64 bool)
	•	eta (uint64): earliest execution time (if you use a timelock/queue).
	•	last_action_round (uint64): for audit/UX.

Execution payload (if proposals can execute on-chain)
Store either:
	•	Minimal: call_target_app (uint64), call_method_sig (bytes), call_args_hash (bytes32)
	•	Or rich: arrays of targets/types/args in a separate box b"x:" + itob(pid) (easier to extend).

Anti-spam / attribution
	•	fee_paid (uint64): microAlgos paid.
	•	referrer (address, optional): if you use referral incentives.

Local state (per voter, optional)
	•	last_vote_pid (uint64): last proposal they voted on (UX).
	•	voted_weight (uint64/uint128): weight they used (for receipts).
	•	ballot_hash (bytes32): if using commit-reveal.

Method surface (ARC-4 ABI names)

At minimum:
	•	propose(cid:byte[], start:uint64, end:uint64, …): creates a proposal, checks fee, initializes box.
	•	vote(pid:uint64, support:uint64, weight:uint64 | auto): casts vote; checks snapshot & double-vote guard.
	•	tally(pid:uint64): tallies and transitions to Succeeded/Defeated after end.
	•	queue(pid:uint64) / execute(pid:uint64): optional, if you do timelock/execution.
	•	set_param(key:byte[], val:uint64|byte[]): admin-only tweaks (fee_amt, quorum_bps, etc).
	•	cancel(pid:uint64) / veto(pid:uint64): admin/vetoer-only as designed.
	•	opt_in() (NoOp) if you keep voter receipts in local state.

Encoding tips on Algorand
	•	Prefer boxes for proposal records; keep global state tiny.
	•	Use ABI Tuple to pack proposal data deterministically (easier upgrades than ad-hoc byte slicing).
	•	When referencing off-chain content, store IPFS CID as bytes and its hash so the on-chain record can be verified.
	•	Use a snapshot round to avoid governance power changing mid-vote.
	•	If requiring a fee, verify a grouped PaymentTxn to get_application_address(app_id) with the exact amount in the same group as propose.
