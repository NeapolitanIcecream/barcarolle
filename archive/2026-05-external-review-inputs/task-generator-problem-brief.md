# Task Generator Problem Brief

## One-Line Problem

Barcarolle's current task supply layer appears too weak for Phase 1: it uses a
thin repo-history adapter, not a strong task generator, and recent local-only
evidence cannot distinguish "repo has insufficient supply" from "our generator
did not mine enough or generate good enough tasks."

## What Barcarolle Is

Barcarolle is a target-repository benchmark compiler. It should select, certify,
weight, split, and calibrate task pools so that a small benchmark predicts
held-out future work for a target repo and agent family.

Barcarolle should remain source-agnostic:

```text
historical repo tasks
external task generators
synthetic tasks
manual/customer regression tasks
future canaries
```

The generator/source-adapter layer is necessary infrastructure, not the central
research claim.

## Current In-House Generator

The main in-house path is `repo_history_pilot.py`.

It does roughly this:

```text
git log since a cutoff
  -> keep commits with implementation .py files and changed test files
  -> reject docs/config/dependency/formatting/churn-like commits
  -> cap changed lines
  -> use parent as base_commit and commit as target_commit
  -> use changed tests as the local oracle
  -> fetch linked GitHub PR context when available
  -> otherwise fall back to commit-message context
  -> create a template solver-facing statement
  -> run local gates:
       checkout
       oracle_extractable
       no_op_fail
       reference_pass
       known_bad_fail
       flakiness_check
       ambiguity_review
       solution_leakage_review
       scope_clarity_review
       cost_boundedness
       taxonomy_labelability
```

This is conservative and auditable, but it is not a full task factory.

## Why This Became Suspect

The original Phase 1 research plan expected:

```text
3 repos
20-50 eval tasks per repo
at least 2 task sources
dev/eval/canary split
weighted scoring
uncertainty intervals
```

Current evidence is below that bar.

## Recent Evidence

### Two-Repo Certified Supply Expansion

The run tried to expand attrs and boltons.

```text
attrs total eligible:   20
boltons total eligible: 27
target: at least 30 per repo
decision: existing_repos_supply_exhausted_screen_new_repo
```

Many failures were recorded as `reference_pass`, which was surprising.

### Reference-Pass Failure Audit

The audit found no sampled proof that Barcarolle's local replay code was simply
testing the wrong thing.

Instead, sampled failures looked like historical environment drift:

```text
dependency version drift
old pytest config incompatibility
Python-version drift
```

It recommended designing historical environment synthesis and better subgate
classification.

### Historical Environment Synthesis

The next run used bounded `uv --no-project --isolated --managed-python`
profiles to replay old commits under older Python/pytest/setuptools.

Result:

```text
known failures sampled: 36
reference_pass recovered: 8
confirmed fully eligible recovery:
  attrs:   +2, projected total 22
  boltons: +4, projected total 31
```

This shows historical environments help, but not enough to keep attrs/boltons
as the only active path.

It also showed the old `reference_pass` gate is too coarse:

```text
reference_install_failed: 10
reference_import_failed:  8
reference_collect_failed: 10
reference_pass:           8
```

### Third-Repo Existing Artifact Screen

The same run screened existing local artifacts for toolz and humanize:

```text
toolz:
  candidates: 16
  certified: 6
  reference failures: 0

humanize:
  candidates: 16
  certified: 12
  near-certified: 4
  reference failures: 1
```

Neither passed the 30-certified-task gate.

Important: this was a quick screen of existing artifacts, not a broad mining
run. It should not be taken as strong evidence that toolz or humanize lack task
supply.

## What We Need From The External Review

We need a recommendation for the next Task Generator design.

Possible outcomes:

```text
A. Use an external generator/source as default.
B. Build a stronger internal repo-history generator.
C. Use a hybrid: external sources where available, internal generator as a
   fallback and certification layer.
```

The recommendation must fit Barcarolle's boundaries:

```text
Barcarolle compiles benchmarks.
Task generation is upstream supply.
Certification remains mandatory.
Hidden oracle and raw ACUT traces cannot inform generation.
No paid validation until local supply gates pass.
```

## Current Hypothesis

The current generator is probably too weak in at least four ways:

```text
1. Candidate mining is shallow:
   current third-repo artifacts only cover 16 candidates per repo.

2. Source context is weak:
   many repo-history candidates depend on PR title/body or commit-message
   fallback; this may not produce strong issue-like solver statements.

3. Environment reconstruction is basic:
   historical environment synthesis was added only after many reference_pass
   failures were observed.

4. There is no real multi-source supply:
   the plan called for at least two task sources, but current evidence is mostly
   historical commit mining.
```

The external review should confirm, reject, or refine this hypothesis.

## Files Worth Inspecting

Core implementation:

```text
code/repo_history_pilot.py
code/statement_quality.py
code/phase1_two_repo_certified_supply_expansion.py
code/phase1_historical_environment_synthesis_gate.py
```

Key results:

```text
reports/phase1_two_repo_supply_expansion_decision.md
reports/phase1_reference_pass_failure_audit_decision.md
reports/phase1_historical_environment_synthesis_decision.md
reports/phase1_third_repo_environment_gate_screen.md
results/phase1_two_repo_supply_expansion_decision.json
results/phase1_historical_environment_synthesis_decision.json
results/phase1_third_repo_environment_gate_screen.json
```

Candidate artifacts:

```text
candidate_artifacts/toolz_*
candidate_artifacts/humanize_*
candidate_artifacts/attrs_supply_expansion_20260526_*
candidate_artifacts/boltons_supply_expansion_20260526_*
```

## Desired Final Advice

The most useful answer would say:

```text
1. Whether the current generator is too weak.
2. What to use externally, if anything.
3. What to build internally, if anything.
4. How to compare generator options in one local-only runbook.
5. What evidence is enough before another paid ACUT run.
```
