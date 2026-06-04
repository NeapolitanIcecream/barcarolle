# Phase 0 Parallelism Policy

Canonical machine-readable policy:
`experiments/phase0_headroom/configs/parallelism_policy.yaml`.

## Policy

- Paid ACUT task-solving concurrency remains `1`.
- Codex and Kilo must not be run in paid parallel against the same endpoint.
- Shared result files require a single writer until file locking is implemented.
- Usage import must run before any future proposal to raise paid ACUT
  concurrency.

## Rationale

Local checkout, oracle extraction, no-op/reference replay, and verifier replay
can eventually run in parallel because they do not call paid LLM endpoints and
can be isolated by workspace. The current runbook still keeps paid task solving
sequential because endpoint rate limits, cache behavior, cost spikes, and Kilo
completion behavior would be confounded by cross-harness paid parallelism.

The cost importer now provides observed-token estimates, but it does not add
provider-billed dollars, endpoint rate-limit telemetry, or file-locking for
shared JSONL result files. Those are prerequisites for raising paid ACUT
parallelism.
