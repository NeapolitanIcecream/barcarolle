# Phase 1 Proposal Evidence/TODO Matrix

Status: internal evidence tracker aligned with proposal report v1,
2026-05-30.

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
| Short-term proposal claim | `traction` | `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md` | One-page evidence summary; final reviewer-facing wording; explicit limitations | P0 | M3, M5 | Claim should be "problem real, measurable, tractable" rather than "validated compiler." |
| Naive weighted failure | `diagnostic` | `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md`; `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526.md` | Proposal-ready explanatory table/figure of failure mode | P0 | M3 | Strong negative evidence; useful only when described as design diagnosis. |
| Retrospective signal | `traction` | `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md` | Baseline envelope; many-seed random percentile; adapter/repo fragility summary | P0 | M3, M4 | Current MAE edge `0.209` vs `0.2149` is route-finding evidence only. |
| Adapter-stratified reporting | `supported` | `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md`; `PROCESS.md` | Final proposal wording for estimand: per-adapter support vs specified ACUT mixture | P0 | M4, M5 | Pooled summaries stay secondary unless preregistered. |
| Source-quality repair | `supported` | `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md` | Short source-supply status paragraph covering attrs, boltons, click, and remaining caveats | P1 | M3 | Click is clean enough for source-quality narrative support; not predictive-validity evidence. |
| Candidate policy with labeled fallback | `draft` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md` | Final name and wording; fallback thresholds; including/excluding fallback-repo reporting plan | P0 | M2, M4 | Prefer `coverage_constrained_unweighted_v1_with_labeled_fallbacks` until fallback is repaired. |
| Boltons fallback issue | `diagnostic` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Fallback share by repo/task slot; repair decision or exclusion sensitivity | P0 | M3, M4 | One repo and six task slots use fallback due to insufficient feature support. |
| Pseudo-future versus predictive validity boundary | `needs_evidence` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md`; `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Final protocol wording that prevents pseudo-future replay from supporting predictive-validity claims | P0 | M4 | `pseudo_future_replay` can support traction and debugging only. |
| Baseline strengthening | `needs_evidence` | `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Many-seed random distribution; baseline envelope; stricter temporal baseline; simple coverage ablation if needed | P0 | M3, M4 | Needed before paid-validation readiness or stronger proposal claims. |
| Task Supply v2 relevance | `diagnostic` | `experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md` | Concise Layer 1 status; certified-yield and source-quality summary; no broad generator scope expansion | P1 | M3 | Supports supply infrastructure; not the project core. |
| Paid-validation readiness | `prohibited` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md`; `PROCESS.md` | External review triage; baseline hardening; support thresholds; fallback decision; power/budget note | P0 | M2, M3, M4 | Current proposal must say paid validation is not authorized. |
| Three-repo exploratory paid pilot | `supported` | `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md` | Proposal-ready paragraph separating pilot evidence from predictive validity | P1 | M3, M5 | Endpoint/policy clean exploratory evidence; not final validity. |
| Candidate outcome-blindness | `supported` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md` | Independent reproduction or reviewer challenge if needed | P1 | M2, M4 | Supports review readiness, not predictive validity. |
| Success criteria hardening | `needs_evidence` | `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_success_criteria.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Joint gate: meaningful MAE margin, slice stability, adapter non-inferiority, repo/window non-concentration, invalid-cell sensitivity | P0 | M4 | Current `0.01` margin and majority rule are not enough for paid validation. |
| External review triage | `needs_evidence` | `/Users/chenmohan/Downloads/barcarolle-research-0530.md`; `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md` | Formal triage: accept now, consider for no-paid proposal evidence, defer, reject scope expansion | P0 | M2 | GPT-5.5-Pro advice is input, not controlling scope. |
| Broad predictive-validity claim | `prohibited` | `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md`; `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_decision.md`; `/Users/chenmohan/Downloads/barcarolle-research-0530.md` | Future outcome-unseen validation result | deferred | Post-proposal validation phase | Do not include as current claim. |

## P0 Before Reviewer-Ready Proposal

The proposal report should not be treated as reviewer-ready until these P0
items are resolved or explicitly deferred in the text:

- final short-term proposal claim wording;
- one-page Phase 1 evidence summary table;
- retrospective baseline table with adapter/repo fragility labels;
- fallback-share accounting and `boltons` fallback wording;
- pseudo-future versus predictive-validity boundary;
- baseline strengthening plan;
- paid-validation non-authorization statement;
- external review triage of GPT-5.5-Pro recommendations.

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
