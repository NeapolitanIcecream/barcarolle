# Source Alignment Check

Status: draft, 2026-06-27.

## Active Sources

- `docs/architecture/v2-system-architecture-2026-06-25.md`
- `docs/design-inputs/learned-selector-roadmap-gpt-5-5-pro-2026-06-25.md`

## Alignment Review

### Vocabulary

The design uses the active core terms:

- `Task`
- `Check`
- `Workspace`
- `Result`
- `Selector`
- `RollingOrigin`
- `Task Pool`
- `Benchmark Selection`
- `Agent Results`

No archived experiment terminology is used as an active module boundary.

### System Boundary

The system remains a target-repository benchmark compiler. It does not become
an Agent harness, public leaderboard, tuning framework, or general workflow
runtime.

### Asset Decoupling

The design keeps these assets independent:

- `Task Pool`
- `Benchmark Selection`
- `Agent Results`

This matches the architecture requirement that cached paid results can be
reused for selector research without rerunning identical Agent-task runs.

### Selector Boundary

The Selector module follows the roadmap:

- common task set and weight vector across Agents;
- metadata-only track first;
- outcome-aware track only when outcomes are available before origin;
- feature provenance with observed-at timestamps and leakage classes;
- rolling-origin policy with known-at cutoff, embargo, cluster constraints, and
  holdout overlap rules;
- MAE as primary metric;
- pairwise gap and regret as auxiliary metrics;
- conservative controller with fallback to rule-based selectors.

### Cache And Scoring Boundary

Result reuse depends on exact `ResultCacheIdentity`, not broad runtime names.
Result matrices must carry completeness, exclusion, abstention, and denominator
metadata so Agent comparisons cannot silently reuse stale or partial cells.

### Goodhart Boundary

The design keeps predictive validity separate from tuning utility. Benchmark
exposure and tuning effects are reporting concerns, not selector training
evidence.

### Archived Material

Archived files may be inspected for examples or provenance, but they do not
define active APIs. Porting any old code requires a separate review that
identifies the owner module and contract.
