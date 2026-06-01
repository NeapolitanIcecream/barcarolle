# Prompt For GPT-5.5-Pro External Adversarial Review

You are acting as an external adversarial reviewer for a research prototype
called Barcarolle.

You do not have access to the local workspace. You have been given a compressed
review bundle with the core files. If you can browse GitHub, you may inspect
additional referenced files at:

```text
Repository: https://github.com/NeapolitanIcecream/barcarolle
Branch: codex/restart-benchmark-compiler
Commit: da8d9977f823952932efb67ecab5c068f1bc5531
```

Use the bundle as the authoritative starting point. Use GitHub only for
additional context when the bundle points to a file that is not included or when
you need to verify surrounding implementation details.

## Project Context

Barcarolle is a target-repository benchmark compiler for coding-agent
evaluation and tuning. It is not an ACUT agent harness, a general SWE task
factory, an agent-license product, a public leaderboard, or a one-shot
chat-completion diff generator.

The current Phase 1 goal is traction evidence, narrative validation, and
proposal support. Formal predictive validity is not established.

The current candidate under review is:

```text
coverage_constrained_unweighted_v1
```

The latest retrospective analysis found weak directional signal for this
candidate:

```text
best simple baseline: temporal_recent_baseline, MAE 0.2149
best Barcarolle candidate: coverage_constrained_unweighted, MAE 0.209
support level: directional_retrospective_underpowered
predictive validity established: false
```

This bundle asks you to review whether the candidate policy and the frozen
validation protocol are credible enough to justify a later paid validation
runbook, not to declare the project successful.

## Files To Read First

Start with these files in order:

```text
review_packet/README_FOR_ADVERSARIAL_REVIEW.md
review_packet/CLAIM_BOUNDARY.md
review_packet/REVIEW_QUESTIONS.md
review_packet/EVIDENCE_INDEX.md

core_reports/phase1_candidate_policy_validation_protocol_decision.md
core_reports/phase1_candidate_policy_validation_protocol_policy_spec.md
core_reports/phase1_candidate_policy_validation_protocol_selection_manifest.md
core_reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md
core_reports/phase1_candidate_policy_validation_protocol_validation_protocol.md
core_reports/phase1_candidate_policy_validation_protocol_success_criteria.md

core_reports/phase1_retrospective_predictive_signal_decision.md
core_reports/phase1_retrospective_predictive_signal_baseline_comparison.md
core_reports/phase1_retrospective_predictive_signal_adapter_metrics.md
core_reports/phase1_retrospective_predictive_signal_uncertainty.md

context/PROCESS.md
context/barcarolle-research-0519.md
context/barcarolle-research-0526.md
```

Use the JSON files in `core_results/` when you need exact fields, selected task
IDs, hashes, success thresholds, or policy inputs.

## Review Questions

Please answer these questions directly and critically:

1. Is `coverage_constrained_unweighted_v1` a defensible near-term mainline
   candidate given the current evidence, or is it too close to a simple
   coverage heuristic to carry the Barcarolle compiler claim?

2. Does the proposed true future-holdout / preregistered rolling-origin
   protocol actually test predictive validity, or does it still leave a
   post-hoc or transductive loophole?

3. Are the baselines strong enough, especially `temporal_recent_baseline`,
   `repo_unweighted_same_budget`, `repo_stratified_by_target_profile`, and
   seeded random same-budget?

4. Are the success criteria too weak, too strong, or vulnerable to a single
   repo or adapter driving the conclusion? In particular, assess the
   preregistered `0.01` MAE margin and the majority-of-slices rule.

5. Does adapter-stratified reporting correctly treat Codex and Kilo as ACUT
   configurations rather than model-only comparisons?

6. How serious is the fact that `boltons` fell back to
   `repo_stratified_by_target_profile` because of insufficient feature support?
   Does that undermine the claim that the primary policy is
   `coverage_constrained_unweighted_v1`?

7. Is the proposal narrative better stated as:
   - predictive benchmark compiler;
   - auditable repo-specific benchmark construction with early predictive
     signal;
   - or something narrower?

8. What concrete changes are required before any paid validation runbook should
   be authorized?

## Expected Output

Please structure your review as:

```text
1. Executive verdict
   - Go / No-Go / Go only after fixes
   - One paragraph.

2. Major findings
   - Ordered by severity.
   - For each finding: issue, evidence, why it matters, required fix.

3. Minor findings
   - Method, reporting, or narrative improvements.

4. Assessment of candidate policy
   - Is the policy outcome-blind, meaningful, and defensible?
   - Does boltons fallback change the claim?

5. Assessment of validation protocol
   - Study design, baselines, metrics, adapter handling, success criteria.

6. Claim boundary recommendation
   - Exact claim wording you would allow now.
   - Exact claim wording you would prohibit.

7. Paid validation readiness
   - What must be changed before paid ACUT cells are run.
   - What can wait until after paid validation.

8. Suggested reviewer-facing or proposal-facing narrative
   - Short version suitable for a project proposal.
```

Be adversarial. Prefer identifying weaknesses over agreeing with the current
plan. Do not infer that predictive validity has been proven. Do not approve
paid validation unless the protocol and claim boundary are strong enough.
