# Joint Success Gate

Gate type: `joint_all_required`.

| Component | Rule | M3 diagnostic | Evidence |
| --- | --- | --- | --- |
| meaningful_mae_margin | candidate MAE must beat the best eligible simple baseline by at least 0.02 | fail | aggregate delta -0.0059 is smaller than the required margin |
| many_seed_random_distribution | candidate must beat or tie at least 95.0% of frozen random seeds on primary MAE | fail | M3 beats-or-ties share is 93.4% |
| catastrophic_miss | Candidate catastrophic-miss rate must be no higher than the best eligible simple baseline by more than the tolerance in every claimed adapter scope. | pass_overall_only | overall miss rate 0.5556 vs baseline 0.5556; slice checks remain fragile |
| adapter_estimand | each claimed named adapter must pass; pooled summary is secondary | fail | Codex is worse than its best baseline while Kilo is better |
| repo_window_non_concentration | improvements must not be concentrated in one favorable repo, adapter, or window | fail | 0 repos pass the margin and 2 repos are worse than their best baseline |
| fallback_governance | fallback share must stay below overall and per-repo caps or the claim narrows | fail | overall fallback share 0.3333; boltons share 1.0 |
| invalid_non_scoreable_sensitivity | sensitivity analysis must not reverse the conclusion and caps must hold | unresolved_for_future_claim | M3 reports non-scoreable counts, but the future sensitivity gate was not frozen before these retrospective outcomes |
| candidate_policy_compliance | zero policy violations and no forbidden outcome inputs | partial_pass | outcome-blindness audit exists, but fallback governance fails for the primary coverage-policy claim |
| source_endpoint_accounting | source-quality, endpoint, cost, latency, and artifact hygiene checks must pass | pass_for_existing_no_paid_artifacts | M3 made no paid calls and did not change score tables; future paid cells would need a fresh endpoint/accounting audit |
| support_thresholds | minimum repos, tasks, adapters, windows, fallback, source, and invalid-cell thresholds must hold for the intended claim | fail_for_primary_future_claim | current evidence is retrospective, sparse, and fallback-composite |

Invalid/non-scoreable rules:
- Invalid max share overall: `0.02`.
- Non-scoreable max share overall: `0.1`.
- Non-scoreable max share per slice: `0.15`.
- Policy violations allowed for primary claims: `0`.

Catastrophic miss:
- Gap threshold: `0.15`.
- Worsening tolerance: `0.02`.

M3 diagnostic result:
- Passes future gate: `False`.
- Classification: `diagnostic_traction_candidate_not_paid_ready`.
- Paid-validation authorization: `False`.
