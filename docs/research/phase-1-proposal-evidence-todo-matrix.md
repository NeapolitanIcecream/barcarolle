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
| Predictive validity north star | `draft` | `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`; `docs/architecture/system-design.md`; `/Users/chenmohan/Downloads/barcarolle-research-0519.md` | True-future or strict preregistered rolling-origin result; final figure and wording | P0 | M4, M5 | Use as research target only; do not claim established validity. |
| Short-term proposal claim | `traction` | `docs/research/phase-1-proposal-evidence-package.md`; `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md` | Final reviewer-facing wording and explicit deferral wording | P0 | M5 | M3 filled the one-page evidence summary. Claim should remain "problem real, measurable, tractable" rather than "validated compiler." |
| Naive weighted failure | `diagnostic` | `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`; `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`; `docs/research/phase-1-proposal-evidence-package.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526.md` | Final proposal figure/table integration if M5 wants one | P0 | M5 | Strong negative evidence; useful only when described as design diagnosis. |
| Retrospective signal | `traction` | `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md` | M4 success gate, adapter estimand, and pseudo-future boundary wording | P0 | M4, M5 | M3 found candidate MAE `0.209` vs temporal `0.2149`, with 1000-seed random beats/ties share `93.4%`, but Codex/repo/window diagnostics remain mixed. |
| Adapter-stratified reporting | `supported` | `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md`; `PROCESS.md` | Final proposal wording for estimand: per-adapter support vs specified ACUT mixture | P0 | M4, M5 | Pooled summaries stay secondary unless preregistered. |
| Source-quality repair | `supported` | `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_source_supply_status.md` | Final proposal paragraph integration | P1 | M5 | Click is clean enough for source-quality narrative support; not predictive-validity evidence. |
| Candidate policy with labeled fallback | `draft` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md`; `docs/research/phase-1-proposal-p0-placeholder-triage.md` | Fallback threshold; including/excluding fallback-repo reporting rule; repair or claim-narrowing decision | P0 | M4 | Use `coverage_constrained_unweighted_v1_with_labeled_fallbacks`; M3 quantified accounting, while threshold/policy remain M4. |
| Boltons fallback issue | `diagnostic` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Fallback threshold, repair decision, or exclusion sensitivity rule | P0 | M4 | M3 quantified fallback as `6/18` overall and `6/6` for boltons; fallback-repos-only diagnostic is worse than temporal by MAE `0.0139`. |
| Pseudo-future versus predictive validity boundary | `needs_evidence` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Final protocol wording that prevents pseudo-future replay from supporting predictive-validity claims | P0 | M4 | `pseudo_future_replay` can support traction and debugging only. |
| Baseline strengthening | `traction` | `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_coverage_ablation.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | M4 stricter temporal/baseline registry and joint success criteria | P0 | M4 | M3 filled many-seed random, envelope, and limited coverage ablation; evidence remains traction because adapter/repo/window diagnostics are mixed. |
| Task Supply v2 relevance | `diagnostic` | `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`; `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_source_supply_status.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md` | Future certified-yield and source-quality gates if paid readiness is reconsidered | P1 | M4 or later | Supports supply infrastructure; not the project core and not a broad generator expansion. |
| Paid-validation readiness | `prohibited` | `docs/research/phase-1-proposal-evidence-package.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md`; `docs/research/phase-1-proposal-p0-placeholder-triage.md`; `PROCESS.md` | M4 support thresholds, fallback decision, invalid-cell rule, joint gate, and power/budget note | P0 | M4 | M3 evidence does not authorize paid validation. Current proposal must still say paid validation is unauthorized. |
| Three-repo exploratory paid pilot | `supported` | `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md` | Proposal-ready paragraph separating pilot evidence from predictive validity | P1 | M3, M5 | Endpoint/policy clean exploratory evidence; not final validity. |
| Candidate outcome-blindness | `supported` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md` | Independent reproduction or reviewer challenge if needed | P1 | M2, M4 | Supports review readiness, not predictive validity. |
| Success criteria hardening | `needs_evidence` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_success_criteria.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Joint gate: meaningful MAE margin, slice stability, adapter non-inferiority, repo/window non-concentration, invalid-cell sensitivity | P0 | M4 | Current `0.01` margin and majority rule are not enough for paid validation. |
| External review triage | `supported` | `/Users/chenmohan/Downloads/barcarolle-research-0530.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md`; `docs/research/phase-1-proposal-p0-placeholder-triage.md` | None for M2; downstream items now route to M3, M4, M5, defer, reject, or user decision | P0 | M2 complete | GPT-5.5-Pro advice is input, not controlling scope. |
| Broad predictive-validity claim | `prohibited` | `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Future outcome-unseen validation result | deferred | Post-proposal validation phase | Do not include as current claim. |

## P0 Before Reviewer-Ready Proposal

The proposal report should not be treated as reviewer-ready until these P0
items are resolved or explicitly deferred in the text:

- final short-term proposal claim wording;
- M3 evidence package integration or explicit deferral in report v1;
- pseudo-future versus predictive-validity boundary;
- M4 validation protocol and candidate-policy decisions;
- paid-validation non-authorization statement;
- reviewer-facing citations, figures, and final prose integration.

M2 completed the external-review triage route map. M3 has now filled the
evidence-package items or marked their limitations. The remaining P0 blockers
are owned primarily by M4 validation/candidate hardening, M5 report revision,
and explicit user decisions for M6 resource and format questions.

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
