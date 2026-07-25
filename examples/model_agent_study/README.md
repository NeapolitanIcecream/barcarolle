# Coding-Agent / Model Study

`study.py` runs the staged experiment frozen by `study-plan.json` and its
append-only amendments. The fixed treatment harness is Codex CLI; each
requested model and reasoning configuration is a distinct Agent.

Paid actions execute at most one frozen cell. A study-scoped advisory lock keeps
Barcarolle calls serial, while each campaign ledger independently reserves,
records, and validates its exact cell. The driver maps the user-authorized
`LLM_BASE_URL` and `LLM_API_KEY` to the repository-standard `OPENAI_*`
variables only after proving the frozen endpoint digest.

Accounting uses two different gateway signals:

- token-log candidates selected by bound model and Result time must exactly
  reproduce Result input/output token totals. If unrelated same-model calls
  overlap, only one uniquely matching row subset is admissible. Its quota sum
  is the per-call attributed cost. One snapshot reconciles each six-cell block,
  while pending calls reserve their full per-call ceilings;
- the token balance is eventually consistent, so it is used only for the
  global budget guard and aggregate reconciliation. A live snapshot is
  requested every six cells and may be reused for at most five minutes.

This distinction matters: an immediate before/after balance delta can move
cost between adjacent calls. `reconcile-resource-ledger` recovers exact Results
after caller interruption, refreshes sanitized token-log receipts, and compares
their total with the later global balance. It never retries an Agent cell.

Typical stage actions are:

```text
prepare-protocol-canaries
preflight-protocol-canary --campaign-id ...
run-next-protocol-canary --campaign-id ...
summarize-protocol-canaries
prepare-replacement-calibration
preflight-calibration --campaign-id ...
run-next-calibration --campaign-id ...
reconcile-campaign-receipts --campaign-id ...
summarize-calibration
prepare-main
preflight-main
run-next-main
summarize-main
reconcile-resource-ledger
```

Raw Agent artifacts, workspaces, gateway payloads, and campaign outputs stay
under ignored `outputs/research/2026-07-25-model-agent-study`. Committed
material is limited to the plan, amendments, adapter code, tests, sanitized
report, and digests.

The main summary reports paired hidden outcomes, exact discordant counts,
McNemar's exact test, dependency-cluster bootstrap intervals, operational
cost/latency/token measures, and Agent×Task-clustered run-flip uncertainty.
These are retrospective, source-conditional claims; the study does not create
prospective Selector evidence or a universal model leaderboard.
