# Phase 1 Validation Protocol And Candidate Policy Hardening

Status: M4 hardening summary, 2026-06-01.

This document summarizes the M4 no-paid protocol hardening package. It is proposal-facing input for M5, not the reviewer-ready proposal report and not a spending approval.

## One-Page Decision Summary

| Item | Decision |
| --- | --- |
| Study mode | True-future or preregistered rolling-origin can support future validity claims only if all gates are frozen and pass; pseudo-future replay is traction/debugging only. |
| Candidate object | coverage_constrained_unweighted_v1_with_labeled_fallbacks |
| Fallback | not_paid_ready_for_primary_coverage_policy_claim |
| Adapter estimand | per_named_acut_configuration |
| Success gate | joint_all_required |
| M3 readiness | diagnostic_traction_candidate_not_paid_ready |
| Power/budget | scenario note only; budget ceiling is user-owned |

## Study-Mode Claim Table

| Mode | Can claim | Cannot claim | Freeze artifact |
| --- | --- | --- | --- |
| true_future_holdout | Predictive-validity evidence for the named scope only if every frozen gate passes. | Cannot generalize beyond named repos, adapters, task supply, source reservoirs, and release schema. | benchmark release manifest plus protocol freeze JSON committed before future outcomes are collected or joined |
| preregistered_rolling_origin | Predictive-validity evidence for preregistered cutoffs only when candidate, baselines, seeds, estimand, invalid-cell handling, support thresholds, and gate are frozen before outcomes are joined. | Cannot use cutoffs chosen after seeing joined outcomes; cannot hide failed cutoffs in a pooled-only summary. | rolling-origin preregistration manifest with outcome-blind digest and seed list |
| pseudo_future_replay | Traction, debugging, and protocol stress-testing. | Cannot carry the north-star validity claim because outcomes or outcome-derived design choices may already be visible. | retrospective replay manifest and traction-only report |
| current_m3_retrospective_evidence | Proposal traction: candidate MAE was 0.209 versus 0.2149 for the best simple aggregate baseline, with visible limitations. | Cannot be treated as current predictive-validity evidence or as a paid-readiness result. | phase1_proposal_evidence_package_decision.json and M3 supporting reports |

## Candidate Policy And Fallback

Candidate policy: `coverage_constrained_unweighted_v1_with_labeled_fallbacks`.

Fallback cap: overall <= `0.1`, per repo <= `0.1667`.

Current M3 fallback result: `not_paid_ready_for_primary_coverage_policy_claim` because boltons has fallback share `1.0`.

## Baseline Registry

Mandatory future baselines:
- `temporal_recent_baseline`
- `repo_unweighted_same_budget`
- `repo_stratified_by_target_profile`
- `many_seed_random_same_budget`

Optional/deferred:
- `coverage_only_same_budget`: add when the selector is frozen outcome-blind.
- `stricter_temporal_recent_same_eligibility`: recommended if supply supports it.
- External/general benchmark comparator: deferred until local certification and licensing are clean.

## Adapter Estimand

A claim for a named adapter requires that adapter to pass the joint gate. A cross-adapter claim requires every named adapter in scope to pass.

An equal-mixture pooled metric may be reported only as a preregistered secondary diagnostic; it cannot rescue a named-adapter failure.

Current M3 cross-adapter status: `fails_because_codex_does_not_pass_and_pooled_summary_is_secondary`.

## Joint Gate

Gate type: `joint_all_required`.

M3 does not pass the future gate. Main failures:
- aggregate MAE edge below future margin
- Codex adapter failure
- fallback caps fail because boltons is 6/6 fallback
- repo improvements concentrated and click/boltons are worse than temporal
- random beats-or-ties share below 95%
- current study mode is retrospective replay

## Support Thresholds

| Threshold | Value | Blocks if not met |
| --- | --- | --- |
| minimum_repos | `{"broader_method_claim": 5, "narrow_target_repo_claim": 3}` | Primary predictive-validity claim for the intended scope. |
| future_tasks_per_repo | 20 | Primary claim for a repo with sparse future outcomes. |
| candidate_pool_support | at least 2x selected budget per repo after source-quality filters | Coverage-policy claim for that repo; route to repair or narrowing. |
| named_acut_configurations | 2 | Adapter-general wording; one adapter can support only adapter-specific wording. |
| rolling_origin_cutoffs | 2 | Rolling-origin claim; true-future holdout may still proceed if separately frozen. |
| fallback_share | `{"overall_max": 0.1, "per_repo_max": 0.1667}` | Primary coverage-policy wording; report composite selector or repair support. |
| invalid_non_scoreable_share | `{"invalid_overall_max": 0.02, "non_scoreable_overall_max": 0.1, "non_scoreable_slice_max": 0.15}` | Primary claim unless rerun/repair is preregistered and completed. |
| independent_source_reservoirs | 2 | Source-quality or source-diversity claim for affected repo. |
| source_quality_certification_fields | provenance digest, license status, oracle-source type, leakage check, environment status, statement digest | Release inclusion for the affected task. |

## Release Schema Pointer

The full schema is in `experiments/phase1_compiler/results/phase1_validation_protocol_candidate_policy_hardening_release_schema.json` and `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_release_schema.md`. It contains `35` fields tied to reproducibility, source quality, outcome blindness, hidden-oracle protection, adapter accounting, future validation support, and artifact hygiene.

## Validation-Design Figure Spec

Flow:

```text
task supply -> certification -> frozen candidate policy -> benchmark release -> future ACUT run -> score join -> baseline comparison -> claim gate
```

Freeze points:
- task supply and cutoffs
- feature extraction
- candidate policy
- baselines and seeds
- adapter estimand
- invalid-cell rules
- support thresholds
- joint success gate

The figure should visually separate true-future and preregistered rolling-origin validation from pseudo-future replay. M5 may render it, but M4 only freezes the spec.

## Power And Budget Note

Future persuasive MAE margin: `0.02`.
M3 aggregate edge: `0.0059`, or `0.295` of the future margin.

Scenario math is in the power/budget report. It does not set a budget ceiling; staffing, duration, and spending decisions remain user-owned.

## Readiness Classification

`validation_protocol_hardened_candidate_not_paid_ready`.

M5 can proceed to report integration from this summary. M6 or any budget-bearing discussion still needs user decisions on artifact format, staffing/duration, owner categories, and a conditional budget ceiling.
