# Barcarolle Design Reference

Status: active implementation-design authority, 2026-08-30.

Barcarolle's first principle is to provide reliable evaluation methods for
self-evolving agents. Repository-level coding agents are the first concrete
domain. A self-evolving agent retains behavior-changing updates to its model,
harness, prompts, memory, skills, tools, or other persistent state across tasks.

These documents describe the intended Barcarolle module boundaries, data
contracts, and cross-module behavior. Use them when implementation details need
the evaluation and evidence boundaries rather than an incidental code path.

Reliability is bounded by a declared task population, outcome definition, agent
lineage and optimizer, feedback interface, optimization budget, threat model,
time horizon, and decision. The primary empirical objectives are pass-rate MAE,
pass-rate-difference MAE, and retention of both under repeated evaluator-guided
optimization. They are not the whole definition: evidence must first be valid,
both errors must meet absolute deployment requirements, and comparative method
choice must remain distinct from adaptive degradation relative to `b=0`.

They do not define or limit the scientific method space. Subject evolution is
the core research context; evaluator coevolution is only one optional method.
The active research objectives and candidate methods are in
[`../research-program.md`](../research-program.md). In particular, the current
eight modules implement a primarily static task-selection path; task
generation, parent links and persistent state across agent versions,
evaluator-feedback evidence, independent prospective evidence for changing
subjects, complete reliability-claim evidence, error curves by optimization budget, and
adversarial stress testing of evaluators and metrics are planned research
capabilities, not silently implemented features.

The design assumes cooperative agents unless an execution adapter states a
stronger threat model. Fresh solver/verifier workspaces and hidden-check
separation are core behavior. Host-level isolation is an optional adapter
capability for cooperative runs and a mandatory evidence condition when the
declared threat model includes deliberate test/scorer/grader/host attacks or
mutually untrusted same-host jobs.

The core follows only the latest schema. Small one-off migrations may preserve
valuable paid results after a schema change, but compatibility layers are not a
design goal. See [Implementation status](../implementation-status.md) for gaps
between these documents and the alpha runtime.

## Documents

- [System design](system-design.md): module boundaries and responsibilities.
- [Data flow](data-flow.md): how data moves between modules.
- [Evidence storage and recovery](evidence-storage-and-recovery.md): artifact
  roots, immutable Task Pool publication, exact Result reuse, pricing views,
  and interruption recovery.
- [Design consistency check](source-alignment-check.md): consistency checks for
  vocabulary, module boundaries, and evidence flow.

Module-level design:

- [Records](modules/records.md)
- [Task Pool](modules/task-pool.md)
- [Verification](modules/verification.md)
- [Workspace](modules/workspace.md)
- [Result Store](modules/result-store.md)
- [Selection](modules/selection.md)
- [Reporting](modules/reporting.md)
- [Runner](modules/runner.md)

Each module-level document defines function boundaries. Functions specify
inputs, outputs, and effects only; they do not include implementation bodies.
The `System Boundary` section in each module document must stay consistent with
the module boundary table in [System design](system-design.md).
Names ending in `Config` are ordinary parameter groups, not first-class system
concepts or modules.

## Update Rule

These documents are not append-only. When a module-level design clarifies a
field, function, or boundary, update the system and data-flow documents in the
same change.
