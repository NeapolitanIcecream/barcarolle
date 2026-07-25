# Barcarolle Cross-Session Handoff

Last updated: 2026-07-25.

This file records only active direction and stop conditions. Intended behavior
lives in `docs/design/`; findings and future work live in
`docs/research-improvement-backlog.md`.

## Stable Boundaries

- Keep the eight-module graph: Records, Task Pool, Verification, Workspace,
  Result Store, Selection, Reporting, and Runner.
- Generators end at one strict prepared-candidate package. Barcarolle owns
  certification and immutable Task Pool publication. Downstream modules consume
  a validated `TaskPoolBundle`, never a Generator object.
- A user-maintained complete Task Pool is a separate read-only input. Opening
  it does not generate, copy, recertify, or republish it.
- Task Pool storage and Result storage remain independent. Result reuse is by
  exact Task/Check/Agent/Workspace/Runtime identity, not Task Pool ID.
- Scoreable execution keeps a clean solver workspace, captures its diff, and
  applies that diff in a fresh verifier workspace where private oracle material
  is first introduced.
- Imported Results require an immutable source manifest and receipt. Default
  availability has an import-time floor; producer-attested history is explicit
  and cannot silently become Barcarolle-managed evidence.
- Keep final-form rolling-origin, FeatureSnapshot, SelectorInput, fitted
  Selector, lazy fill, and prospective replay contracts. Learned algorithms
  wait for sufficient prospective evidence; their infrastructure is not
  deleted merely because current data underuses it.
- Prefer direct records and functions. Do not add a Generator registry, plugin
  host, model service, workflow DAG, Feature Store, distributed scheduler, or
  simulator platform without a concrete implementation that needs it.

## Active Research Sprint

The authorized coding-agent/model study is frozen by:

- `docs/experiments/2026-07-25-model-agent-study.md`;
- `examples/model_agent_study/study-plan.json`; and
- append-only `examples/model_agent_study/study-amendment-1.json` and
  `study-amendment-2.json`.

Current evidence:

- The certified ten-Task Pylint pool is the calibration anchor.
- A 75-Task, 54-dependency-cluster SymPy SWE-bench Verified package is frozen.
  All 75 base-fail/reference-pass pairs certified in about 66 minutes, and the
  published 75-Task/75-Check bundle reopens.
- DeepSeek V4 Pro and Gemini 3.1 Pro failed Codex Responses compatibility
  without gateway charge. These are harness/proxy protocol failures, not model
  capability results.
- Sol and Terra completed the 24-cell paired calibration with 24 scoreable
  Results. Each passed 5/10 base Tasks, their base outcomes were identical, and
  neither of the two repeated Tasks flipped. Sol cost $6.013130 versus Terra
  $2.491162 by exact gateway receipts.
- GPT-5.4 mini passed the protocol canary with a scoreable hidden failure and
  priceable usage. Claude Sonnet 4.6 was Agent-invalid with empty usage and
  zero attributed quota. Only mini enters replacement calibration.
- Per-call accounting comes from sanitized gateway token-log rows whose
  prompt/completion totals exactly match the Result. The token balance is
  eventually consistent and is used only for the global guard and aggregate
  reconciliation. Take one live balance checkpoint every six frozen cells and
  reuse a live snapshot across campaigns for at most five minutes; use exact
  attributed quota between checkpoints. Do not query or interpret an immediate
  post-call balance as one call's cost. Token-log receipt acquisition may wait
  through six bounded observations for an exact Result token match; it never
  reruns the Agent. A pass that recovers a missing receipt defers live-balance
  refresh to the next receipt-complete reconciliation.

Persist each Result immediately, but batch token-log attribution every six
cells. Pending calls reserve their full per-call ceilings, and a new block
cannot start until the previous block's receipts are exact. This keeps live
balance checkpoints at 0/6/12/18 and receipt checkpoints at 5/11/17/23.

Research sequence:

1. Complete the frozen 24-cell mini-versus-Terra replacement panel.
2. Select two main configurations by the predeclared pass, attributed-cost,
   disagreement, and family rule.
3. Run the frozen 75-Task paired main schedule and three executions on the
   preselected 30% repeat subset.
4. Reconcile Result, campaign, token-log, balance, artifact, and certification
   evidence; run the adversarial audit; publish the decision report.

## Paid-Call Boundary

This sprint is the explicit exception to the repository's default variable
names: the user authorized at most USD 300 through `LLM_BASE_URL` and
`LLM_API_KEY`. The study driver proves their endpoint/key values match the
`OPENAI_BASE_URL` and `OPENAI_API_KEY` values consumed by the harness before
each campaign.

Every paid cell requires immutable schedule authority, exact endpoint/model/
harness/config identity, a per-call ceiling, a total campaign ceiling, and
enough remaining global allowance for the next ceiling. A study-scoped lock
keeps Barcarolle paid calls serial. Metadata queries use bounded retry; Agent
cells have zero campaign retry.

The hard allowance is 150,000,000 quota points above the frozen
`total_used=707840389` baseline, with 500,000 points per USD. Before a call,
guard against the larger of:

- later global balance movement; and
- the sum of exact attributed token-log quota.

Raw credentials, URLs, prompts, completions, transcripts, workspaces, verifier
output, and gateway payloads stay under ignored outputs or are not persisted.
Commit only sanitized summaries, digests, plans, reports, schemas, and tests.

## Claim Boundary

- The current study is retrospective and source-conditional. It can support a
  practical model portfolio for the frozen Pylint/SymPy populations, not a
  universal leaderboard.
- Newly observed 2026 Results cannot be backdated into historical rolling
  origins and do not establish prospective Selector MAE.
- Task Pool bundle consistency proves artifact/link consistency, not source
  population coverage.
- Generator behavior, source-frame authority, Check quality, generated-pool
  prediction, and field calibration are separate evidence axes.
- Run repeats stay in the experiment layer unless the predeclared flip-rate
  interval crosses its promotion gate.

## Deferred Work And Reopening Triggers

- Checkout caching: reopen only when checkout plus cleanup exceeds 5% of
  scoreable-cell wall time or p95 blocks target throughput.
- Bounded Agent parallelism: the duration threshold is now met, but this study
  remains serial because attribution and isolation are part of its evidence.
  Reopen with a concrete concurrency authority, one Result writer, and
  per-call attribution that remains unambiguous.
- Certification checkpointing: the 66-minute 75-Task run makes interruption
  loss material. Before the next comparable pool, add one single-writer
  checkpoint keyed by exact package/candidate/config/Check/mode identity; do
  not add a workflow engine.
- Concrete Generator development remains outside this sprint.

Before commits, run scoped tests, Ruff, Pyright, and `git diff --check`. Preserve
all ignored campaign outputs until the final sanitized report and audit replay
their digests.
