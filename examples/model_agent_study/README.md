# Coding-Agent / Model Study

`study.py` runs the staged experiment frozen by `study-plan.json` and five
append-only amendments. The fixed treatment harness is Codex CLI; each
requested model and reasoning configuration is a distinct Agent. The study is
complete; `study-results.json` is the committed, sanitized result and audit
snapshot.

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
apply-main-cost-amendment
prepare-recovery-canary
run-next-recovery-canary
apply-main-continuation-amendment
preflight-main
run-next-main
summarize-main
reconcile-resource-ledger
```

`apply-main-cost-amendment` is a no-model-call recovery action. It accepts only
the exact scoreable Result named by the committed amendment, preserves the
original stop reason, raises only the campaign's conservative per-call ledger
ceiling, and appends a reauthorization event. Repeating the action is
idempotent; it cannot retry or replace the stopped cell.

`apply-main-continuation-amendment` is likewise a no-model-call action. It
binds the retained repeat-only availability failure and the separately
authorized, outcome-blind recovery canary. It permits only the remaining
already-frozen cells, keeps retries and replacement cells at zero, and makes a
second non-scoreable main Result terminal.

Raw Agent artifacts, workspaces, gateway payloads, and campaign outputs stay
under ignored `outputs/research/2026-07-25-model-agent-study`. Committed
material is limited to the plan, amendments, adapter code, tests, sanitized
report, and digests.

The main summary reports paired hidden outcomes, exact discordant counts,
McNemar's exact test, dependency-cluster bootstrap intervals, operational
cost/latency/token measures, and Agent×Task-clustered run-flip uncertainty.
These are retrospective, source-conditional claims; the study does not create
prospective Selector evidence or a universal model leaderboard.

The fixed SymPy main completed all 238 cells. Terra-high passed 53/75 base
Tasks and mini-high passed 46/75; the paired difference was +9.33 percentage
points for Terra (`p=0.0923`, dependency-cluster bootstrap 95% interval
`[0, 18.18]` points). Terra also cost less and produced more end-to-end
successes, so it is the source-conditional operational default. The 13.85%
observed repeat flip rate had a 95% interval of `[6.15%, 21.88%]`, crossing
neither promotion gate; repeats stay in the experiment layer.
