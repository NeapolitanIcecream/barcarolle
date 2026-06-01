# Phase 1 Proposal Evidence Package

Status: M3 no-paid evidence package, 2026-06-01.

This document fills the M3 evidence-producing proposal placeholders. It does not claim predictive validity and does not authorize paid validation.

## One-Page Evidence Summary

| Reader question | Claim strength | Key result/status | Canonical report | Limitation | Proposal use |
| --- | --- | --- | --- | --- | --- |
| Is the target-repository benchmark-construction problem real? | supported_for_proposal | Old weighted pilot gaps were attrs 0.3148 and boltons 0.7481; simple same-budget baselines were 0.25 and 0.125. | phase1_weighted_design_paid_pilot_decision.md; phase1_local_algorithm_bakeoff_decision.md | Negative evidence for naive weighting, not a positive predictive-validity result. | Use to show benchmark construction choices materially affect estimates. |
| Did the naive weighted design fail in a diagnosable way? | diagnostic_negative | Local bakeoff kept repo_stratified/simple designs as conservative baselines and did not promote old weighted target-profile matching. | phase1_local_algorithm_bakeoff_decision.md | Does not by itself identify the next successful compiler. | Use as a design-learning result and negative control. |
| Is workspace ACUT protocol and artifact hygiene technically tractable? | supported_for_proposal | Three-repo paid pilot completed 120/120 cells with scoreability 1.0, endpoint compliance pass, and no raw logs/prompts/workspaces committed. | phase1_three_repo_paid_validation_decision.md | Exploratory pilot evidence only. | Use to justify feasibility of clean benchmark-side execution and accounting. |
| Is the click source-quality caveat repaired enough for the source-quality story? | supported_for_proposal | Click repair: 30/30 public-context repaired; paid LLM calls 0; paid ACUT cells 0. | phase1_click_llm_source_context_repair_decision.md | Historical paid outcomes were not rewritten or rerun. | Use click as clean enough for source-quality narrative support. |
| Should adapter-level reporting be primary? | supported_for_proposal | codex_workspace candidate_worse (delta 0.0253); kilo_workspace candidate_better (delta -0.0297) | phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md; phase1_retrospective_predictive_signal_adapter_metrics.md | Does not resolve the final M4 adapter estimand. | Use adapter-stratified tables first; keep pooled summaries secondary. |
| Is the retrospective signal directional but underpowered? | traction_only | Candidate MAE 0.209 vs best envelope baseline temporal_recent_baseline MAE 0.2149; candidate beats/random-ties share 93.4%. | phase1_proposal_evidence_package_baseline_envelope.md; phase1_proposal_evidence_package_random_baseline_distribution.md | Pseudo-future replay with sparse support; not predictive validity. | Use as route-finding evidence for M4 protocol hardening. |
| Is the candidate policy composite because of labeled fallback? | needs_M4_protocol_decision | Fallback share 0.3333 overall; boltons fallback share 1.0; no M3 threshold set. | phase1_candidate_policy_validation_protocol_selection_manifest.md; phase1_proposal_evidence_package_fallback_share.md | M4 must set threshold, inclusion/exclusion rule, or repair path. | Use the full name coverage_constrained_unweighted_v1_with_labeled_fallbacks. |

## Detailed M3 Outputs

- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_coverage_ablation.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_source_supply_status.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_report_evidence_index.md`

## Boundary

- Predictive validity established: `false`.
- Paid validation authorized: `false`.
- Paid ACUT solver cells run in M3: `0`.
- Paid LLM calls run in M3: `0`.
- External reviewer calls run in M3: `0`.
- Public citation browsing run in M3: `false`.

## Remaining Handoff

M4 should use this package to harden the validation protocol and candidate-policy gates: fallback threshold, adapter estimand, invalid-cell rule, joint success gate, support thresholds, and power/budget note. User decisions remain needed before M6 approval artifact work or any budget-bearing paid-validation discussion.
