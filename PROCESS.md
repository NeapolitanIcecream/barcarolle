# Barcarolle Internal Process Notes

Last updated: 2026-07-17.

These notes are for repository-maintenance agents. They are not user
documentation and they are not a source of truth for intended system behavior.
For implementation, use the current design documents under `docs/design/` as
the design authority. If this file conflicts with those documents, the design
documents win.

## Current Mode

The current development direction is predictive validity. The active work makes
task certification executable, binds replayable Task/Check/certification
evidence, keeps rolling-origin inputs time-correct, captures real usage and
unknown cost accurately, and evaluates Adaptive methods by paired MAE.
`docs/implementation-status.md` records which effects the alpha implementation
enforces.

The fixed real-task Pylint pilot is complete. It observed one high-only pass
among ten single-run low/high pairs, which is too sparse to separate a
reasoning-effort effect from run-level variation or train a controller. Its
hindsight per-task oracle tied always-high at 5/10, so it did not demonstrate
an adaptive accuracy gain. The next outcome-facing step is a larger paired
history followed by rolling-origin MAE comparisons, not another controller
schema or framework.

Complexity is justified when it can improve prediction, prevent invalid
evidence, or preserve reusable paid results. Do not add aliases for existing
concepts, uncommon names for standard methods, unused identity fields, or
frameworks without a current caller.

Reports support Task Pool coverage only after loading the referenced Task,
Check, and certification-evidence files, validating Task/Check semantics, and
matching complete base-fail/reference-patch-pass evidence to every accepted
Task/Check and rejected candidate. Reports also recompute current aggregate
Selector metrics from their bound matrices before supporting metric claims.
Persisted Selector inputs must retain the complete rolling-history denominator;
benchmark infrastructure failures stop certification instead of shrinking it,
and selection metrics abstain if exclusions leave any Agent without results.

The default runtime target is a cooperative Agent. Fresh workspaces, diff
replay, and verifier-only hidden material are required benchmark behavior.
Filesystem, network, process, CPU, and memory limits are optional adapter
requirements for adversarial or shared-host execution.

Archived material is historical reference. It is not an active implementation
input and should not be imported without a specific review.

## Design Rules

- Design before implementation.
- Keep module boundaries direct and small.
- Keep the core data vocabulary to `Task`, `Check`, `Workspace`, `Result`,
  `Selector`, `RollingOrigin`, `Task Pool`, `Benchmark Selection`, and
  `Agent Results`.
- Use the current module vocabulary: `Records`, `Task Pool`, `Verification`,
  `Workspace`, `Result Store`, `Selection`, `Reporting`, and `Runner`.
- Prefer the current module vocabulary; avoid alternate module names.
- Do not introduce a new first-class concept when one of those terms is enough.
- Every design document must include a source-alignment check against the
  architecture document.
- Module-level design should define function names, inputs, outputs, and
  effects, but not implementation bodies.
- Later module documents may refine earlier system documents. Update the
  affected documents instead of leaving contradictions.
- Design learned data and parameter contracts with a concrete algorithm. MAE is
  the current primary prediction objective.

## Schema And Result Preservation

Core code reads and writes only the latest schema. Do not keep runtime
compatibility branches for old records.

When a schema change affects valuable paid results, preserve them with a small
one-off migration that validates the new records and leaves the source
untouched. Drop an old result only when it cannot be migrated without guessing
evidence. Stop extending the migration when it starts becoming a compatibility
framework.

Preserved does not mean exact-cache reusable. When Agent-visible task material
or repository-history boundaries change, keep the old paid record for analysis
instead of rewriting its execution identity without proof of equivalence.

## Design Review Stop Line

Future design review should only request document changes for gaps that can
break the trustworthy evidence chain. Continue fixing design docs when a gap
could cause:

- stale paid results to be reused;
- Selectors to see future results or future-derived features;
- Task, Check, or oracle mismatches;
- selected or future denominators to become unauditable;
- frozen selections, results, or metrics to be changed after the fact;
- reports to lose traceability to cell, matrix, or result evidence.

Do not continue expanding design docs only to make fields more complete, feature
provenance more detailed, reports more expressive, validators more exhaustive,
or schemas more strongly typed. Defer those refinements to implementation paths
that actually need them.

## Paid Calls

The user authorized up to USD 300 for the current paired rolling-origin
experiment. Use only:

```text
OPENAI_BASE_URL
OPENAI_API_KEY
```

The ignored protocol and exact resource ledger are under
`outputs/user-journeys/2026-07-15-openai-paired-rolling-origin/`. Estimate cost
with current OpenAI standard API prices, as explicitly approved by the user;
label it as an estimate because the gateway does not publish billing rates.
The ten-call, no-retry boltons mechanism experiment is complete: five certified
Task/Check cells for each of the `gpt-5.4-mini` low- and high-reasoning Agent
configurations. All ten Results were scoreable; nine passed and one failed.
Official-price estimated cost was USD 0.35245695. The held-out origin 2 rule
mixture MAE was 0.00, tying coverage and random and beating recency at 0.25.
This is mechanism evidence only because the five tasks and availability times
are controlled. The sanitized report is
`docs/boltons-paired-mae-mechanism.md`.

The v1 paid diffs retained generated Python caches. Preserve those Results
unchanged. Commit `c052addc` excludes `.pytest_cache` and `__pycache__` from
future captured diffs and binds examples to adapter v2. The next predictive
experiment needs a larger Task Pool with multiple future tasks per origin.

The fixed Pylint pilot used real availability times and executable SWE-bench
`FAIL_TO_PASS`/`PASS_TO_PASS` certification. The first transport-aborted attempt
is preserved under its ignored output directory: one known-cost Result used
USD 0.13451550 and one interrupted Result has unknown usage and cost. The
replacement matrix restored Codex CLI default transport retries and completed
20/20 scoreable cells for USD 2.46819345 estimated at official prices. Low
passed 4/10; high passed 5/10; the only disagreement was high-only. The
sanitized report is `docs/pylint-swe-bench-reasoning-pilot.md`.

Future Pylint pools use a semantic Check manifest that excludes ignored output
directories and local harness paths while retaining the check implementation,
SWE-bench revision, verifier image, timeout, and hidden-oracle digest. The
exact runtime command is still checked before execution. Current paid Results
keep their original identities and remain loadable from their original output
directory; do not rewrite them to claim equivalence.

Known authorized spend across the boltons mechanism run and both Pylint
attempts is USD 2.95516590. Keep the interrupted Pylint cell's cost unknown; do
not subtract a guessed zero from the USD 300 authorization.

Repository-maintenance Codex sessions used to implement, review, or coordinate
work are outside this paid-call boundary. Reviewer Codex CLI sessions should
use the user's local Codex CLI authentication/subscription unless the user
explicitly requests a different reviewer execution mode.

## Local Experiment Time Estimates

Estimate task supply, deterministic certification, preflight, paid execution,
and analysis separately. Record active wall time for each phase and exclude
user pauses or known network outages instead of folding them into throughput.

For a serial paid matrix, wait for at least three scoreable cells per Agent
configuration, then estimate remaining wall time as:

```text
overhead factor * sum(remaining cells for config * observed mean workspace seconds for config)
```

Use `result time span / summed workspace seconds` as the overhead factor. This
pilot observed 1.009; use 1.02 for the same local serial runner until a later
run replaces it. Low averaged 67.77 seconds and high averaged 148.44 seconds,
so the observed pair mean was 216.21 seconds. At that rate, 30 paired tasks take
about 1.8 paid hours and 50 take about 3.0, before setup and analysis.

Do not extrapolate research and task-source repair from warm recertification.
The first ten-task supply pass took 81 minutes 6 seconds because it included
source research, a rejected task, an architecture probe, and repository repair.
Rebuilding the same fixed ten tasks from warm local inputs took 7 minutes 34
seconds; preflight took 3 seconds. State which case an estimate uses.
