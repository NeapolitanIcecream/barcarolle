# Phase 1 Proposal Evidence/TODO Matrix

Status: internal evidence tracker aligned with proposal report v1, M2
placeholder triage, and completed M3 evidence package, 2026-06-01.

This matrix maps proposal-report claims to current evidence, missing evidence,
and recommended no-paid work. It is deliberately conservative: unsupported
claims are either routed to later no-paid milestones or marked prohibited.
The final-shape proposal draft at
`docs/research/phase-1-proposal-report-v1.md` should pull from this matrix but
should not reproduce it as a main-body evidence ledger.

Status values:

- `supported`: enough committed evidence for careful proposal use.
- `traction`: useful directional evidence, not final validation.
- `diagnostic`: negative or explanatory evidence that guides the path.
- `draft`: plausible wording that needs stronger support or review.
- `needs_evidence`: not ready until named evidence is produced.
- `prohibited`: should not appear as a proposal claim.

## Matrix

| Claim or section | Status | Current evidence | Missing evidence | Priority | Recommended milestone | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Predictive validity north star | `draft` | `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`; `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md`; `docs/architecture/system-design.md`; `/Users/chenmohan/Downloads/barcarolle-research-0519.md` | True-future or strict preregistered rolling-origin result; M5 figure rendering and final wording | P0 | M5, later validation | M4 defines the validation modes and figure spec. Use as research target only; do not claim established validity. |
| Short-term proposal claim | `traction` | `docs/research/phase-1-proposal-evidence-package.md`; `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md` | Final reviewer-facing wording and explicit deferral wording | P0 | M5 | M3 filled the one-page evidence summary. Claim should remain "problem real, measurable, tractable" rather than "validated compiler." |
| Naive weighted failure | `diagnostic` | `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`; `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`; `docs/research/phase-1-proposal-evidence-package.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526.md` | Final proposal figure/table integration if M5 wants one | P0 | M5 | Strong negative evidence; useful only when described as design diagnosis. |
| Retrospective signal | `traction` | `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`; `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md` | M5 integration and compact current-evidence caveat | P0 | M5 | M3 found candidate MAE `0.209` vs temporal `0.2149`, with 1000-seed random beats/ties share `93.4%`, but M4 classifies this below the future margin and not paid-ready. |
| Adapter-stratified reporting | `supported` | `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md`; `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_adapter_estimand.md`; `PROCESS.md` | Final proposal wording and table integration | P0 | M5 | M4 sets the estimand as per named ACUT configuration. Pooled summaries stay secondary unless preregistered. |
| Source-quality repair | `supported` | `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_source_supply_status.md` | Final proposal paragraph integration | P1 | M5 | Click is clean enough for source-quality narrative support; not predictive-validity evidence. |
| Candidate policy with labeled fallback | `diagnostic` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md`; `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_candidate_policy.md` | Feature-support repair or explicit claim narrowing before paid-readiness wording | P0 | M5, later repair | M4 sets fallback caps of overall <= `0.10` and per-repo <= `0.1667`; current candidate fails because boltons is `6/6` fallback. |
| Boltons fallback issue | `diagnostic` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md`; `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_candidate_policy.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Repair feature support or report a narrowed/composite claim | P0 | M5, later repair | M4 treats boltons fallback as claim-changing; fallback-repos-only diagnostic is worse than temporal by MAE `0.0139`. |
| Pseudo-future versus predictive validity boundary | `supported` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`; `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_claim_modes.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | M5 final wording and figure rendering | P0 | M5 | M4 bars pseudo-future replay from carrying the north-star claim; `pseudo_future_replay` can support traction and debugging only. |
| Baseline strengthening | `supported` | `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_coverage_ablation.md`; `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_baseline_registry.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Future implementation under a frozen release; M5 summary integration | P0 | M5, later validation | M4 keeps temporal recent mandatory, makes random many-seed, adds optional coverage-only and stricter temporal variants, and defers external/general comparators pending certification. |
| Task Supply v2 relevance | `diagnostic` | `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_source_supply_status.md`; `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_release_schema.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md` | Future certified-yield and source-quality gates if paid readiness is reconsidered | P1 | M5 or later | M4 encodes release schema and source-support fields. Supports supply infrastructure; not the project core and not a broad generator expansion. |
| Paid-validation readiness | `prohibited` | `docs/research/phase-1-proposal-evidence-package.md`; `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md`; `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md`; `PROCESS.md` | User decisions plus future protocol pass; current candidate fails M4 gate | P0 | M5, M6 user decision | M4 classifies the M3 candidate as not paid-ready. Current proposal must still say paid validation is unauthorized. |
| Three-repo exploratory paid pilot | `supported` | `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md` | Proposal-ready paragraph separating pilot evidence from predictive validity | P1 | M3, M5 | Endpoint/policy clean exploratory evidence; not final validity. |
| Candidate outcome-blindness | `supported` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md` | Independent reproduction or reviewer challenge if needed | P1 | M2, M4 | Supports review readiness, not predictive validity. |
| Success criteria hardening | `supported` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_success_criteria.md`; `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Future application under a frozen true-future or rolling-origin release | P0 | M5, later validation | M4 replaces the old loose rule with a joint gate: MAE margin `0.02`, adapter pass, non-concentration, fallback caps, invalid/non-scoreable sensitivity, policy compliance, source/endpoint checks, and support thresholds. |
| External review triage | `supported` | `/Users/chenmohan/Downloads/barcarolle-research-0530.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md`; `docs/research/phase-1-proposal-p0-placeholder-triage.md` | None for M2; downstream items now route to M3, M4, M5, defer, reject, or user decision | P0 | M2 complete | GPT-5.5-Pro advice is input, not controlling scope. |
| Broad predictive-validity claim | `prohibited` | `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Future outcome-unseen validation result | deferred | Post-proposal validation phase | Do not include as current claim. |

## P0 Before Reviewer-Ready Proposal

The proposal report should not be treated as reviewer-ready until these P0
items are resolved or explicitly deferred in the text:

- final short-term proposal claim wording;
- M3 evidence package integration or explicit deferral in report v1;
- M4 validation protocol and candidate-policy decisions integrated into report v1;
- paid-validation non-authorization statement;
- reviewer-facing citations, figures, and final prose integration.

M2 completed the external-review triage route map. M3 has now filled the
evidence-package items or marked their limitations. M4 has filled the
validation/candidate hardening decisions and classified the current candidate
as not paid-ready. The remaining P0 blockers are owned primarily by M5 report
revision and explicit user decisions for M6 resource and format questions.

## Deferred Or Post-Proposal Items

These are relevant to the long-term north star but should not block the
current proposal argument rewrite:

- full Task Supply v2 expansion;
- external generator adapter implementation;
- hierarchical beta-binomial uncertainty model;
- full multi-ACUT residual predictive-validity study;
- public benchmark packaging;
- broad productization or leaderboard work.

## Prohibited Claim Check

The following claims are prohibited until future evidence changes the boundary:

- "Barcarolle is a validated predictive benchmark compiler."
- "`coverage_constrained_unweighted_v1` has proven predictive validity."
- "The current evidence authorizes paid validation."
- "Codex/Kilo differences are model-only superiority evidence."
- "Pseudo-future replay establishes predictive validity."
- "Task Supply v2 or an external task generator is the main Barcarolle
  contribution."
