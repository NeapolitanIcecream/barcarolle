# Phase 0 Headroom Experiment Plan

Status: restart draft, 2026-05-20.

Operational companion: [Phase 0 runbook](phase-0-runbook.md).

## Goal

Phase 0 decides whether the benchmark-compiler claim is worth pursuing before
building a larger compiler. It must answer three questions:

1. Does the target repository's future work distribution differ measurably from
   general SWE benchmark distributions?
2. Do early same-repo tasks provide predictive signal for later same-repo work,
   beyond or alongside general benchmark score?
3. Is there enough certifiable task supply in repository history, external
   sources, or a minimal repo-history generator to build a small benchmark
   release?

Phase 0 does not claim product readiness, admission, license issuance, or
ranking reversal. License and admission remain possible downstream product uses,
but Phase 0 should not optimize around them.

## Experiment 0.1: Distribution Mismatch Audit

Compare a general benchmark distribution `Q` with target-repo future work
distribution `T_r`.

Candidate features:

- module or package;
- task type;
- changed-file and changed-line counts;
- test type;
- code locality and dependency radius;
- issue or PR text style;
- API surface touched;
- runtime and platform constraints.

Primary outputs:

- divergence table by feature family;
- low-dimensional target-profile draft;
- confidence labels for each stratum.

Pass condition:

At least one candidate repository shows a material, interpretable distribution
mismatch that would make a generic task mix a weak estimator of future work.

## Experiment 0.2: Oracle Repo-Specific Headroom

Start with historical tasks before building any new task generator. If external
pipelines are unavailable or do not cover the chosen repositories, add the
smallest repo-history generator needed to feed the certification funnel:

```text
early same-repo tasks -> B_real
late same-repo tasks  -> W_real
general benchmark     -> G
```

Compare predictors:

- `G -> W_real`;
- `B_real -> W_real`;
- `G + B_real -> W_real`;
- unweighted same-repo pool;
- simple stratified/weighted same-repo pool.

Metrics:

- MAE and RMSE for pass-rate prediction;
- binomial negative log likelihood;
- Brier score where probabilistic predictions exist;
- uncertainty interval coverage;
- residual improvement after adding same-repo signal.

Pass condition:

Same-repo evidence lowers held-out prediction error or explains residuals for at
least one repo/agent-family setting. If not, the project should pivot toward
tuning feedback and regression coverage rather than predictive validity.

## Experiment 0.3: Task Supply Funnel

For each candidate repository, build a supply funnel followed by certification
gates. The funnel should distinguish "can be made executable" from
"benchmark-grade".

```text
candidate anchors
-> replayable checkouts
-> environment build success
-> oracle extractable
-> oracle validity checks
-> stability and leakage checks
-> scope and labeling checks
-> benchmark-grade tasks
```

Required certification gates:

- no-op fail;
- reference pass;
- known-bad fail, using the original failing change, a reverted reference patch,
  or a small negative-control mutation where available;
- low flakiness under repeated runs;
- ambiguity review for underspecified or multi-solution tasks;
- solution-leakage review across issue text, PR comments, docs, tests, and
  generated statements;
- scope-clarity review, excluding tasks that bundle unrelated changes;
- cost boundedness for setup, agent run, and verifier runtime;
- feature-taxonomy coverage for module, task type, difficulty proxy, oracle
  type, dependency radius, and failure category.

Record rejection reasons at the first failing gate and preserve secondary
warnings when useful. Reports must separate:

- `candidate`: sourced but not replayed;
- `executable`: checkout, build, and oracle are available;
- `oracle_valid`: no-op/reference/known-bad checks pass;
- `certified`: all required gates pass;
- `near_certified`: one or more review gates are missing, weak, or manual-only.

Also record manual review minutes, rerun counts, runtime/cost summaries, and
artifact sizes.

Pass condition:

At least one repository can produce enough `certified` tasks for a 20-50 task
MVP release, or the funnel clearly identifies which source adapter, generator
capability, oracle repair, or review gate must be improved next. `near_certified`
tasks may justify continuing the project, but they do not count as
benchmark-grade release tasks until the missing gates are closed. Generator
success is judged by certified yield and task quality, not by novelty as a
standalone task factory.

## Repository Selection

Start with three repositories:

- one Python CLI/library repo similar to Click, using archived Click material as
  a smoke reference only;
- one non-Python or web-heavy repo to test language/tooling shift;
- one repo with richer feature or dependency work to avoid a bug-fix-only
  profile.

The final repo list should be chosen by task supply, deterministic local tests,
reasonable build time, and low external-service dependence.

## Minimal Artifacts

```text
experiments/phase0_headroom/
  README.md
  configs/
  candidate_sources/
  target_profiles/
  certified_tasks/
  releases/
  results/
  reports/
```

Committed artifacts should be small, reviewable, and reproducible. Large raw
runs stay out of Git and are referenced by manifest.

## Reuse From Legacy Archive

Useful archived material:

- Click task manifests and R0 release hygiene as seed examples;
- workspace-mode runner semantics;
- fresh verification and hidden verifier discipline;
- scorecard taxonomy separating verified failure, invalid submission, infra
  failure, and missing coverage.

Do not reuse old ranking-reversal conclusions. The archived M3-lite report says
the story was not established.

## Exit Criteria

Proceed to Phase 1 only when Phase 0 produces:

- at least one target-profile draft with measurable distribution mismatch;
- at least one headroom analysis comparing same-repo and general predictors;
- one task-supply funnel with gate-level rejection reasons and certified
  benchmark-grade yield estimates;
- a decision memo choosing whether to pursue predictive validity, tuning
  feedback, or regression-benchmark positioning, and noting whether downstream
  license/admission productization is plausible after the evidence improves.
