# Barcarolle

Barcarolle is a target-repository benchmark compiler for coding-agent evaluation
and tuning.

Given a target repository, a time cutoff, candidate task sources, an agent
family, an evaluation budget, target-work assumptions, and a tuning objective,
Barcarolle compiles a versioned benchmark release. A release is more than a task
list: it includes certified tasks, task strata, dev/eval/canary/holdout splits,
target-work weights, execution environments, oracle-quality metadata, leakage
and flakiness reports, score aggregation, uncertainty estimates, failure labels,
and optimizer-readable feedback.

## Current Direction

The active research claim is:

> Public SWE benchmarks and scalable task generators supply tasks when they are
> available; Barcarolle decides which tasks should become the benchmark for this
> repository, this agent family, this evaluation budget, and this tuning
> objective.

Barcarolle is not primarily:

- an agent license or admission product in the current research phase;
- a general-purpose SWE task factory as the core contribution;
- a ranking-reversal experiment;
- a public leaderboard.

Those can be downstream uses or comparison settings, but they are not the core
project object. Barcarolle may still need repo-history task construction or
source adapters when upstream task-generation pipelines are unavailable. In that
case, task generation is input supply infrastructure; the research contribution
remains certification, target-work modeling, benchmark assembly, calibration,
and tuning feedback.

License or G0-G5-style admission remains a natural product extension once the
benchmark compiler has credible evidence. It is preserved as future work, not as
an active deliverable for this restart.

## Active Documents

- [System design](docs/architecture/system-design.md)
- [Phase 0 headroom experiment plan](docs/experiments/phase-0-headroom-plan.md)
- [Restart consensus notes](docs/restart/2026-05-20-restart-consensus.md)

## Legacy Archive

The previous Agent License architecture, G0-G5 admission semantics, and
core-narrative ranking-reversal experiments are preserved under
[archive/2026-05-agent-license-reset](archive/2026-05-agent-license-reset/README.md).

Archived material is audit history, not active product semantics. Reuse it only
after checking whether it supports the benchmark-compiler framing.
