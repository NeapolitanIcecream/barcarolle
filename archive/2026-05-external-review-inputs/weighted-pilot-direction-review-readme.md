# Barcarolle Phase 1 Weighted Pilot External Review Bundle

This bundle is a sanitized evidence package for an external GPT-5.5-Pro review.
It contains project background, the local compiler design, the frozen weighted
pilot package, paid pilot results, and the two Python tools that produced the
selection and metrics.

No raw ACUT transcripts, raw prompts, raw completions, solver workspaces,
verifier workspaces, hidden oracle files, secrets, or local absolute paths are
intended to be included.

## Review Goal

Please help answer a non-trivial research/design question:

> Barcarolle wants to compile a small repo-specific benchmark release from a
> candidate task pool so that B_eval predicts held-out future repo work
> (H_future). A crude target-profile weighted selection method failed in a paid
> pilot, while simple unweighted/stratified baselines did better. What should
> the next algorithmic direction be?

We do not need encouragement. We need a technically grounded diagnosis and, if
appropriate, a concrete algorithm design.

## Current Project Claim

Barcarolle is not primarily a task generator or public leaderboard. It is a
target-repository benchmark compiler:

```text
candidate task pool + target repo assumptions + agent family + budget
  -> selected/weighted/split benchmark release
  -> score estimates future target-repo agent performance
```

The benchmark compiler should be evaluated by predictive validity:

```text
Does B_eval predict H_future better than simple baselines?
```

## What Happened

Previous statement-hardened paid evidence was operationally clean but did not
establish predictive validity:

```text
planned/completed/scoreable cells: 32/32/32
policy violations: 0
B_eval -> H_future gaps:
  attrs:   0.25
  boltons: 0.375
```

We then created a local pre-paid replication package:

```text
primary candidate: barcarolle_weighted_time_family_matched
baselines:
  repo_unweighted_same_budget
  repo_stratified_by_target_profile
pilot cells: 44
primary threshold: per-repo abs(B_eval predicted - H_future observed) <= 0.15
```

The paid pilot completed cleanly:

```text
planned/completed/scoreable cells: 44/44/44
policy violations: 0
observed-or-conservative cost: USD 22.0
```

But the weighted design failed:

```text
barcarolle_weighted_time_family_matched:
  attrs gap:   0.3148
  boltons gap: 0.7481
  max gap:     0.7481
  threshold met: false

repo_unweighted_same_budget:
  attrs gap:   0.25
  boltons gap: 0.125
  max gap:     0.25

repo_stratified_by_target_profile:
  attrs gap:   0.25
  boltons gap: 0.125
  max gap:     0.25
```

Simple baselines did not meet the 0.15 threshold either, but they were much
better than the weighted design.

## Important Constraints

- H_future must not be used as the target profile.
- Hidden verifier/oracle material must not affect task selection, weighting, or
  statement writing.
- Prior paid outcomes may motivate new designs, but must be treated as
  previous evidence. A redesigned release needs a new preregistered validation.
- Barcarolle should not reimplement the ACUT harness. It can only prepare
  benchmark tasks, invoke configured workspace adapters, capture diffs, verify
  patches, and score outcomes.
- Prefer mature modern software/statistical tools over bespoke infrastructure
  when possible, but preserve auditability.

## Key Files To Read First

Start with these:

```text
background/research-proposal-0519.md
background/system-design.md
results/phase1_weighted_design_paid_pilot_decision.json
results/phase1_weighted_design_paid_pilot_metrics.json
results/phase1_weighted_design_paid_pilot_baseline_comparison.json
inputs/phase1_pre_paid_replication_target_profiles.json
inputs/phase1_pre_paid_replication_strata_matching.json
inputs/phase1_pre_paid_replication_release_candidates.json
code/phase1_pre_paid_replication_compiler_readiness.py
code/phase1_weighted_design_paid_pilot.py
```

Useful human-readable summaries:

```text
reports/phase1_weighted_design_paid_pilot_decision.md
reports/phase1_weighted_design_paid_pilot_baseline_comparison.md
reports/phase1_pre_paid_replication_strata_matching.md
reports/phase1_pre_paid_replication_target_profiles.md
```

## Questions For Review

Please answer in a structured way:

1. Diagnosis:
   Why did the weighted design probably fail? Separate likely causes from
   uncertain causes.

2. Method critique:
   What is wrong or fragile about the current target-profile weighting and
   split-matching logic? Is the failure due to bad features, bad objective,
   small N, leakage constraints, target-profile definition, selection strategy,
   or something else?

3. Algorithm proposal:
   Propose a next-generation benchmark compiler algorithm suitable for small
   candidate pools and expensive paid validation. Please include:
   - task feature representation
   - target profile estimation
   - split construction
   - task weighting
   - uncertainty model
   - validation plan
   - fallback behavior when supply is too small

4. Baseline strategy:
   What baselines should be retained or added? Should the simple stratified
   baseline become the next mainline candidate until a better algorithm is
   justified?

5. Experiment design:
   What should the next local-only runbook do before any more paid calls?
   What would be enough evidence to justify another paid replication?

6. Modern stack:
   What libraries/tools/statistical packages should Barcarolle use instead of
   hand-rolled code, while preserving reproducibility and artifact auditability?

7. Stop/go recommendation:
   Should Barcarolle keep pursuing predictive benchmark compilation now, pivot
   to task certification/tuning feedback, or narrow the claim?

Please be concrete. If you recommend an algorithm, give pseudocode or an
implementation outline.

## Bundle Map

```text
background/   project framing and architecture
runbooks/     runbooks that produced the current evidence
inputs/       preregistered thresholds, target profiles, release candidates
results/      paid pilot machine-readable results
reports/      human-readable summaries
score_tables/ sanitized paid score table
code/         deterministic selection/metrics scripts
MANIFEST.sha256
```
