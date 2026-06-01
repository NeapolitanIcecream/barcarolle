# Phase 1 Proposal P0 Placeholder And External Review Triage

Status: M2 triage draft, 2026-06-01.

This document routes proposal-report v1 placeholders and local external-review
input into later milestone ownership. It does not fill the placeholders,
produce new evidence, authorize paid validation, or draft later runbooks.

## 1. Executive Decision

The proposal report should not move to reviewer-ready revision until the P0
items below are either filled by their owner route, explicitly deferred, or
downgraded with a written claim-boundary reason.

Primary routing decision:

- M3 owns evidence-production gaps: summary evidence, random baseline,
  baseline-envelope, coverage ablation, and supporting fallback accounting.
- M4 owns validation and candidate-policy hardening: pseudocode, release
  schema, fallback threshold, estimand, adapter claim, invalid-cell rules,
  success gates, and power/budget logic.
- M5 owns reviewer-facing prose, citations, figures, and final report
  integration after M3/M4 settle their inputs.
- M6 owns the approval artifact shape and resource ask, but several resource
  numbers require a user decision before they can be filled.

Predictive validity remains the north star, not an established result. Paid
validation remains unauthorized.

## 2. Scope And Non-Scope

In scope:

- inventorying and routing v1 Appendix D P0 and P1 placeholders;
- routing local GPT-5.5-Pro 0530 recommendations as strategy input;
- routing 0526-1 task-supply guidance without making task generation the core
  proposal claim;
- aligning claim-boundary, roadmap, evidence matrix, and process notes where
  the route map changes active handoff state.

Out of scope:

- filling citations, figures, result tables, pseudocode, schema tables, power
  notes, staffing numbers, or budget numbers;
- browsing for public citations;
- running paid ACUT cells or paid LLM calls;
- calling an external reviewer;
- changing paid outcomes, task IDs, splits, source eligibility, task
  statements, or completed decisions;
- drafting M3, M4, M5, or M6 runbooks.

## 3. P0 Placeholder Routing Table

| Placeholder | Source | Route | Priority | Claim function | Why this route | Expected output | Can affect paid-validation readiness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [NEEDS CITATION: related-work comparison for benchmark families and task generation systems] | Proposal report v1 Appendix D | M5_reviewer_ready_report_revision | P0_blocker | Distinguishes benchmark compilation from task generation and public/live benchmarks. | It is reviewer-facing framing work; M2 cannot browse or fill citations, and the citation paragraph should be integrated during report revision. | Reviewer-facing related-work paragraph with public citations and no local-plan dependency. | No, except by preventing overclaiming. |
| [NEEDS FIGURE: north-star validation design] | Proposal report v1 Appendix D | M4_validation_or_candidate_hardening | P0_blocker | Makes the future-work estimand, benchmark release, baselines, and prediction-error target auditable. | The figure depends on the validation mode and estimand decisions, so M4 should own the first concrete design output before M5 renders it. | Frozen validation-design figure spec and final figure input for M5. | Yes. |
| [NEEDS FIGURE: compiler architecture] | Proposal report v1 Appendix D | M5_reviewer_ready_report_revision | P0_blocker | Explains Barcarolle as a compiler layer between task supply and ACUT evaluation. | The existing six-layer architecture is already conceptually stable; the remaining work is reviewer-facing diagram integration. | Architecture figure showing source adapters through release score model and feedback. | No. |
| [NEEDS PSEUDOCODE: candidate benchmark assembly policy] | Proposal report v1 Appendix D | M4_validation_or_candidate_hardening | P0_blocker | Defines the candidate object, supported feature checks, fallback route, and forbidden outcome inputs. | It directly governs the candidate policy and paid-readiness boundary, especially labeled fallback behavior. | Pseudocode and checklist for `coverage_constrained_unweighted_v1_with_labeled_fallbacks`. | Yes. |
| [NEEDS TABLE: release artifact schema] | Proposal report v1 Appendix D | M4_validation_or_candidate_hardening | P0_blocker | Defines what a benchmark release contains and how each artifact supports claims. | Release schema affects artifact hygiene, reproducibility, and future validation governance before the report can treat a release as auditable. | Required-field table with owner and claim function. | Yes. |
| [NEEDS TABLE: one-page preliminary evidence summary] | Proposal report v1 Appendix D | M3_evidence_package | P0_blocker | Converts Phase 1 traction into a compact reader-facing evidence map without claiming validity. | This is the central evidence consolidation output and should be produced before M5 prose revision. | One-page table with reader question, claim strength, result, report, limitation, and remaining gap. | Indirectly; it can block readiness if evidence remains too weak. |
| [NEEDS RESULT: many-seed random baseline distribution and candidate percentile] | Proposal report v1 Appendix D | M3_evidence_package | P0_blocker | Tests whether the candidate beats a strong random same-budget distribution rather than a weak sample. | It is a no-paid evidence computation and baseline-strengthening result. | Random-seed distribution, candidate percentile, and slice diagnostics. | Yes. |
| [NEEDS RESULT: baseline-envelope comparison] | Proposal report v1 Appendix D | M3_evidence_package | P0_blocker | Compares the candidate against the best preregistered simple baseline overall and by slice. | It is evidence production needed before protocol hardening can judge readiness. | Baseline-envelope table overall, per adapter, per repo, and per time window. | Yes. |
| [NEEDS RESULT: coverage objective ablation] | Proposal report v1 Appendix D | M3_evidence_package | P0_blocker | Shows what coverage contributes beyond temporal, stratified, unweighted, and random baselines. | The first concrete output is an ablation result; M4 can then decide how much claim weight the candidate can carry. | Ablation report separating coverage objective value from fallback and simple heuristics. | Yes. |
| [NEEDS DECISION: fallback-share threshold] | Proposal report v1 Appendix D | M4_validation_or_candidate_hardening | P0_blocker | Prevents a coverage-policy claim from hiding composite/fallback behavior. | The threshold defines when the candidate must be reported as composite or narrowed. | Numeric fallback-share threshold and include/exclude fallback reporting rule. | Yes. |
| [NEEDS DECISION: estimand and adapter claim] | Proposal report v1 Appendix D | M4_validation_or_candidate_hardening | P0_blocker | Determines whether claims are per-adapter, adapter-specific, or a preregistered ACUT mixture. | Adapter-stratified reporting is a validation-protocol decision, not just prose cleanup. | Estimand statement and rule preventing pooled metrics from rescuing adapter failure. | Yes. |
| [NEEDS DECISION: catastrophic-miss and invalid-cell rules] | Proposal report v1 Appendix D | M4_validation_or_candidate_hardening | P0_blocker | Defines failure tolerance and invalid/non-scoreable sensitivity before future outcomes are joined. | These are success-gate components and must be frozen before paid validation can be discussed. | Numeric catastrophic-miss threshold and invalid-cell pass/fail sensitivity rule. | Yes. |
| [NEEDS DECISION: joint success gate] | Proposal report v1 Appendix D | M4_validation_or_candidate_hardening | P0_blocker | Replaces loose margin-or-majority logic with a jointly required validation rule. | It is a core protocol-hardening decision and should incorporate M3 baseline evidence. | Joint gate covering margin, slice stability, adapter non-inferiority, concentration, invalid cells, and policy compliance. | Yes. |
| [NEEDS ANALYSIS: power and budget note] | Proposal report v1 Appendix D | M4_validation_or_candidate_hardening | P0_blocker | Explains what effect size a future paid run could plausibly detect. | The analysis depends on validation thresholds and future cell design; it belongs with protocol hardening. | Power/budget note with detectable effect size, limits, and no-paid versus conditional-paid boundary. | Yes. |
| [NEEDS NUMBER: no-paid staffing and duration] | Proposal report v1 Appendix D | needs_user_decision | P0_blocker | Turns the research plan into a resource ask. | M2 can identify the route, but the actual staffing and duration require project-owner approval. | User-approved no-paid duration and staffing assumption for M6. | No. |
| [NEEDS NUMBER: conditional paid-validation budget ceiling] | Proposal report v1 Appendix D | needs_user_decision | P0_blocker | Caps any future paid discussion without authorizing it. | The ceiling depends on user budget policy and M4 protocol shape; M2 cannot set it unilaterally. | User-approved conditional ceiling, explicitly gated and non-authorizing. | Yes. |
| [NEEDS DELIVERABLE DETAIL: acceptance criteria and owners] | Proposal report v1 Appendix D | needs_user_decision | P0_blocker | Assigns accountability for final proposal outputs. | Acceptance criteria can be drafted later, but owner categories and approval roles require user confirmation. | Deliverable list with acceptance criteria and reviewer-facing owner category. | Indirectly. |

## 4. P1 Placeholder Routing Table

| Placeholder | Source | Route | Priority | Claim function | Why this route | Expected output | Can affect paid-validation readiness |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [NEEDS APPENDIX TABLE: report evidence index] | Proposal report v1 Appendix D | M3_evidence_package | P1_before_final_publication_or_broader_review | Lets reviewers trace claims to reports without making the main body chronological. | M3 will consolidate the evidence package and can produce the compact index. | Appendix evidence index with evidence type, claim function, numeric result, limitation, and main-text status. | No. |
| [NEEDS DECISION: approval artifact format] | Proposal report v1 Appendix D | needs_user_decision | P1_before_final_publication_or_broader_review | Determines whether M6 becomes a report, memo, deck, or combined packet. | The format depends on the user's approval audience and cannot be inferred safely from evidence alone. | User decision on M6 artifact format. | No. |
| [NEEDS DECISION: external-review triage categories] | Proposal report v1 Appendix D | M2_boundary_or_wording | P1_before_final_publication_or_broader_review | Shows how external review input was accepted, routed, deferred, or rejected. | This is the current runbook's direct output. | Completed sections 5 and 6 of this triage document plus decision artifact. | Indirectly. |
| [NEEDS CITATION: public-literature replacements for local research-plan references] | Proposal report v1 Appendix D | M5_reviewer_ready_report_revision | P1_before_final_publication_or_broader_review | Replaces local planning files with reviewer-facing public literature support. | This is citation and prose integration work, not M2 triage or no-paid evidence production. | Public citation replacements for local research-plan references. | No. |

## 5. External Review Recommendation Triage

Pending Step 2. This section will classify relevant 0530 GPT-5.5-Pro findings
as `accept_now`, `route_to_M3`, `route_to_M4`, `route_to_M5`, `defer`,
`reject_scope_expansion`, or `needs_user_decision`.

## 6. 0526-1 Task-Supply Guidance Triage

Pending Step 2. This section will classify task-supply guidance as needed for
proposal P0, relevant but M3/M4 scoped, deferred infrastructure, or rejected
as short-term scope expansion.

## 7. Claim Boundary Updates Needed

Initial Step 1 conclusion: the existing claim boundary is directionally
consistent with the placeholder routes. Later updates should only synchronize
route ownership and the explicit user-decision blockers; they should not
expand the short-term claim or authorize paid validation.

## 8. Milestone Routing Summary

| Route | P0 count | P1 count | First concrete output |
| --- | ---: | ---: | --- |
| M2_boundary_or_wording | 0 | 1 | External-review route categories and closeout decision. |
| M3_evidence_package | 4 | 1 | Evidence table, random baseline, baseline envelope, and coverage ablation. |
| M4_validation_or_candidate_hardening | 8 | 0 | Validation design, candidate policy, release schema, fallback, estimand, success gates, and power note. |
| M5_reviewer_ready_report_revision | 2 | 1 | Related-work citation integration and final report figures/prose. |
| M6_approval_artifact | 0 | 0 | None without user decisions. |
| needs_user_decision | 3 | 1 | Resource numbers, budget ceiling, owners, and approval format. |
| defer_post_proposal | 0 | 0 | None from the P0/P1 placeholder register. |
| reject_short_term_scope_expansion | 0 | 0 | None from the P0/P1 placeholder register. |
| already_satisfied_or_appendix_only | 0 | 0 | None from the P0/P1 placeholder register. |

## 9. No-Paid / No-Validation Boundary

This triage does not authorize paid validation. A future paid discussion remains
blocked unless no-paid evidence, protocol gates, support thresholds, fallback
rules, invalid-cell policy, and power/budget analysis are hardened in later
milestones.

Current boundary:

- Paid ACUT solver calls made in M2: `0`.
- Paid LLM calls made in M2: `0`.
- External reviewer calls made in M2: `0`.
- Predictive validity established: `false`.
- Paid validation authorized: `false`.
- Pseudo-future replay may support traction and debugging only.

## 10. Open User Decisions

- No-paid staffing and duration for the next research phase.
- Conditional paid-validation budget ceiling, if later no-paid and protocol
  gates justify discussing paid validation.
- Reviewer-facing owner categories for deliverables.
- Final M6 approval artifact format: report, memo, deck, or combined packet.
