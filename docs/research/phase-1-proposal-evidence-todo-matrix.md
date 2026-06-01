# Phase 1 Proposal Evidence/TODO Matrix

Status: internal evidence tracker aligned with proposal report v2 and M5
reviewer-ready revision, 2026-06-01.

This matrix maps proposal-report claims to current evidence, missing evidence,
and recommended no-paid work. It is deliberately conservative: unsupported
claims are either routed to later no-paid milestones or marked prohibited.
The reviewer-ready technical proposal report is now
`docs/research/phase-1-proposal-report-v2.md`. Version 1 remains source
material and a placeholder history, not the active reviewer-facing report.

M5 resolved the proposal-report P0 integration items by producing v2, the
reviewer-readiness checklist, citation matrix, risk register, and closeout
decision. Remaining open items are future validation evidence or user-owned M6
decisions, not unresolved v2 evidence placeholders.

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

## P0 Reviewer-Ready Proposal Status

The M5 reviewer-ready revision resolved the report-level P0 items:

- final short-term proposal claim wording appears in
  `docs/research/phase-1-proposal-report-v2.md`;
- M3 evidence is integrated in v2 as traction, including the `0.209` MAE,
  `0.2149` best simple aggregate baseline, `0.0059` edge, `93.4%`
  random-baseline beats/ties share, adapter caveats, and fallback caveats;
- M4 validation protocol and candidate-policy decisions are integrated in v2
  as future standards, not current proof;
- paid validation remains explicitly unauthorized;
- reviewer-facing public citations, figures, risk handling, evidence index,
  and final prose are complete for technical proposal review.

The remaining blockers are not v2 evidence placeholders. They are:

- future true-holdout or preregistered rolling-origin evidence before any
  predictive-validity claim;
- fallback repair or claim narrowing before a primary coverage-policy claim;
- user decisions for M6 artifact format, staffing/duration, owner categories,
  and any conditional paid budget ceiling.

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
