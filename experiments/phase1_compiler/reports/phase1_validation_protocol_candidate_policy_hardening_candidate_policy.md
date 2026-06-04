# Candidate Policy And Fallback Governance

Policy object: `coverage_constrained_unweighted_v1_with_labeled_fallbacks`.

Pseudocode:

```text
Input: certified candidate task rows for each target repo plus allowed solver-visible feature fields.
Reject rows missing release eligibility, source-quality status, statement digest, or leakage-risk status.
For each repo, derive supported feature dimensions from the frozen policy feature list and source-quality overlays.
If repo has at least budget_per_repo eligible tasks and enough supported feature coverage, select budget_per_repo tasks that maximize unweighted coarse feature coverage.
Score candidate sets without task-level outcome weights; each selected task contributes equally within its repo budget.
Break ties by sha256(seed, repo, task_id, feature_vector) with the frozen deterministic seed.
If feature support is insufficient, route the repo to the labeled insufficient_feature_support fallback.
If eligible budget is insufficient, route the repo to the labeled insufficient_budget fallback.
Mark every selected fallback slot with fallback_selected, fallback_design, fallback_reason, and source-quality overlay status.
Write selected and excluded task IDs with reasons; do not change IDs after any score or future outcome is visible.
```

Fallback thresholds:

| Scope | M3 share | Hard cap |
| --- | --- | --- |
| overall | 0.3333 | 0.1 |
| repo:attrs | 0.0 | 0.1667 |
| repo:boltons | 1.0 | 0.1667 |
| repo:click | 0.0 | 0.1667 |

Current M3 fallback classification: `not_paid_ready_for_primary_coverage_policy_claim`.

Governance:
- Include/exclude rule: Always report all repos and a sensitivity excluding repos whose per-repo fallback share exceeds the cap. If any repo is excluded, the primary claim is narrowed to support-qualified repos.
- Repair or narrowing rule: Repair feature support and rerun the frozen policy before future outcomes are joined, or narrow the claim to the composite selector with fallback-repo sensitivity.
- Boltons treatment: `claim_changing_because_fallback_share_is_6_of_6`.
- Diagnostic: boltons/fallback-repo diagnostic is worse than temporal by MAE 0.0139 in M3.

Policy violations:
- using forbidden outcome, terminal-status, score, hidden-verifier, transcript, or pass-rate fields
- changing selected task IDs, split labels, feature values, thresholds, seeds, or fallback labels after outcomes are visible
- using an unlabeled fallback slot
- omitting source-quality or leakage-risk overlays
- claiming a coverage-policy result when fallback caps fail

Boundary:
- Selected task IDs and split labels changed: `false`.
- Paid-validation authorization remains `false`.
