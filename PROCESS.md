# Barcarolle Internal Process Notes

Last updated: 2026-07-14.

These notes are for repository-maintenance agents. They are not user
documentation and they are not a source of truth for intended system behavior.
For implementation, use the current design documents under `docs/design/` as
the design authority. If this file conflicts with those documents, the design
documents win.

## Current Mode

The current maintenance direction is to close evidence-chain gaps found by the
2026-07-14 implementation audit. `docs/design/` remains the intended boundary;
`docs/implementation-status.md` records which effects the alpha implementation
actually enforces.

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
- Core code serves only the latest schema. When a schema change affects
  valuable paid results, prefer a small one-off migration tool; do not maintain
  compatibility branches or grow a migration framework.
- Design learned data and parameter contracts with a concrete algorithm. MAE is
  the current primary prediction objective.

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

Current design documents do not require paid benchmark or evidence-producing
LLM or Agent calls. When a task explicitly requires benchmark/evidence-producing
paid calls, use only:

```text
LLM_BASE_URL
LLM_API_KEY
```

Record a protocol before running paid calls that affect evidence, benchmark
results, selector training, or research claims.

Repository-maintenance Codex sessions used to implement, review, or coordinate
work are outside this paid-call boundary. Reviewer Codex CLI sessions should use
the user's local Codex CLI authentication/subscription unless the user
explicitly requests a different reviewer execution mode.
