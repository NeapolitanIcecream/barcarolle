Please execute the runbook at:

`/Users/chenmohan/gits/barcarolle/docs/research/agent-tuning-demo-autonomous-completion-runbook-2026-06-17.md`

Work autonomously and keep going until either the Agent Tuning Demo is complete
or Beijing time reaches `2026-06-18 08:00:00 +0800`. If the demo is incomplete,
do not voluntarily stop before `2026-06-18 07:00:00 +0800`; keep solving
blockers, running bounded experiments, and iterating on the tuning artifact or
protocol. After `07:00`, continue if completion is plausible before `08:00`,
otherwise produce the required checkpoint before the network interruption.

Paid calls needed for this demo are allowed, but every LLM/Agent/tuner/model
call must use `LLM_BASE_URL` and `LLM_API_KEY`, and every dollar of observed or
estimated cost must be recorded in the cost ledger required by the runbook. Do
not use fallback auth. Do not commit raw prompts, completions, transcripts,
workspaces, clones, caches, or secrets.

Before any medium or large paid Agent batch, audit whether the current tooling
has safe parallel paid-cell execution. If not, implement the smallest
bounded-concurrency runner needed for this demo, with stable cell ids,
idempotent resume, per-worker workspace isolation, per-cell endpoint proof,
timeouts, duplicate-paid-call prevention, and concurrency-safe cost ledger
writes. Use conservative concurrency first (`2`, at most `4` unless smoke
evidence supports more). Sequential fallback is allowed only for a genuinely
small remaining batch, a checkpoint-mode tradeoff, or a documented scheduler
blocker.

Preserve the main story: Barcarolle supplies repo-specific certified tasks,
freezes rolling-origin windows without future leakage, exports tuning feedback,
produces a deployable repo-local Agent artifact, and validates before/after on
future holdout tasks with clear cost and claim boundaries. Do not stop with only
recommendations while executable experiments remain before the time floor. Make
focused commits as packages complete and finish with either the final demo
report or the deadline checkpoint artifacts.
