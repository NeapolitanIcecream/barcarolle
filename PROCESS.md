# Barcarolle Internal Process Notes

Last updated: 2026-07-15.

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

Complexity is justified when it can improve prediction, prevent invalid
evidence, or preserve reusable paid results. Do not add aliases for existing
concepts, uncommon names for standard methods, unused identity fields, or
frameworks without a current caller.

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
The plan is at most ten no-retry calls: five certified boltons Task/Check cells
for each of the `gpt-5.4-mini` low- and high-reasoning Agent configurations.
Using one model keeps the Result matrix on one valid price table. Run one
low-reasoning canary first, then scale only when endpoint identity, measured
usage, cost, diff replay, and hidden Check are valid. Before the canary, no paid
inference call has run.

Repository-maintenance Codex sessions used to implement, review, or coordinate
work are outside this paid-call boundary. Reviewer Codex CLI sessions should
use the user's local Codex CLI authentication/subscription unless the user
explicitly requests a different reviewer execution mode.
