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

The 2026-05-30 GPT-5.5-Pro review is strategy input, not controlling scope.
The accepted boundary is: go only after no-paid fixes; do not authorize paid
validation from the current packet.

| Recommendation | Source | Class | Route | Priority | Claim impact | Why this route | Expected output | Can affect paid-validation readiness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rename the current object as a coverage-constrained unweighted selector with explicit fallback, not the whole Barcarolle compiler. | 0530 Finding 1; candidate-policy assessment | accept_now | M2_boundary_or_wording, then M4_validation_or_candidate_hardening | P0_blocker | Prevents the candidate from carrying a stronger compiler claim than the evidence supports. | The name already matches the proposal boundary; M4 must make the policy and fallback governance inspectable. | Consistent use of `coverage_constrained_unweighted_v1_with_labeled_fallbacks` plus candidate-policy pseudocode. | Yes. |
| Add an ablation showing what the coverage objective contributes beyond stratified, temporal-recent, and many-seed random baselines. | 0530 Finding 1 | route_to_M3 | M3_evidence_package | P0_blocker | Tests whether the coverage objective adds signal beyond simple heuristics. | This is result production, not protocol prose. | Coverage-objective ablation report and report-ready summary row. | Yes. |
| Treat the current retrospective edge as below the proposed future margin and block paid authorization unless no-paid evidence passes the same rule or the paid run is explicitly exploratory. | 0530 Finding 2 | route_to_M4 | M4_validation_or_candidate_hardening | P0_blocker | Keeps weak retrospective traction from becoming paid-validation authorization. | This belongs in paid-readiness gates and success criteria. | No-paid readiness gate tied to the exact future success rule. | Yes. |
| Split `true_future_holdout` or strict outcome-unseen rolling-origin claims from `pseudo_future_replay`, which can support only traction and debugging. | 0530 Finding 3 | accept_now | M4_validation_or_candidate_hardening | P0_blocker | Preserves the predictive-validity boundary. | The boundary is accepted now; M4 must freeze the protocol wording. | Study-mode claim table and rule excluding pseudo-future replay from validity claims. | Yes. |
| Freeze repos, task supply, cutoffs, feature extraction, source-quality overlays, candidate policy, baselines, seeds, invalid-cell rules, adapter handling, and success thresholds before future outcomes exist or are joined. | 0530 Finding 3 | route_to_M4 | M4_validation_or_candidate_hardening | P0_blocker | Prevents post-hoc validation design. | These are protocol-hardening inputs. | Frozen-input checklist for future validation. | Yes. |
| Strengthen many-seed random and baseline-envelope reporting; keep temporal-recent as a serious comparator. | 0530 Finding 4 | route_to_M3 | M3_evidence_package | P0_blocker | Ensures the candidate is compared against strong simple baselines. | The first output is no-paid baseline evidence. | Many-seed percentile and baseline-envelope evidence package. | Yes. |
| Add stricter temporal baseline details, simple coverage baseline, and external/general benchmark comparator where feasible. | 0530 Finding 4 | route_to_M4 | M4_validation_or_candidate_hardening | P1_before_final_publication_or_broader_review | Defines the future baseline registry without requiring broad external adapter work now. | Temporal and coverage baselines affect validation design; external/general comparator can be conditional on clean supply/licensing. | Baseline registry update with feasibility caveats. | Yes. |
| Replace `margin OR majority` with a joint gate: meaningful MAE margin, slice stability, adapter non-inferiority or narrowed claim, repo/window non-concentration, catastrophic miss, invalid-cell sensitivity, and policy compliance. | 0530 Finding 5 | route_to_M4 | M4_validation_or_candidate_hardening | P0_blocker | Makes future success criteria harder to game and easier to audit. | This is central validation-protocol hardening. | Joint success gate decision. | Yes. |
| Keep adapter-level reporting primary and prevent pooled improvement from rescuing adapter failure. | 0530 Finding 6 | accept_now | M4_validation_or_candidate_hardening | P0_blocker | Keeps ACUT configuration inside the estimand instead of treating adapter differences as noise. | This is already a process guardrail, but M4 must decide per-adapter versus mixture wording. | Estimand and adapter claim decision. | Yes. |
| Treat `boltons` fallback as claim-changing; set a fallback-rate blocker and report including/excluding fallback repos if validation proceeds. | 0530 Finding 7 | route_to_M4 | M4_validation_or_candidate_hardening | P0_blocker | Prevents a primary coverage-policy claim when one repo uses fallback. | Thresholds and inclusion/exclusion rules belong in candidate-policy hardening. | Fallback-share threshold and fallback sensitivity rule. | Yes. |
| Quantify fallback share by repo and task slot before using the candidate in the proposal evidence story. | 0530 Finding 7 | route_to_M3 | M3_evidence_package | P0_blocker | Gives M4 the factual basis for the threshold and claim wording. | This is evidence accounting rather than a policy decision. | Fallback-share table and source-support caveat. | Yes. |
| Strengthen the outcome-blindness story with independent reproduction if needed. | 0530 minor finding | defer | defer_post_proposal | P1_before_final_publication_or_broader_review | Could improve reviewer confidence but is not the first blocker for proposal P0 routing. | Current audit is enough for M2; future review can request reproduction. | Optional independent reproduction or adversarial audit. | Indirectly. |
| Add a compact box showing that current evidence would not pass future paid-success criteria. | 0530 minor finding | route_to_M5 | M5_reviewer_ready_report_revision | P1_before_final_publication_or_broader_review | Prevents accidental overclaiming in the reviewer-facing report. | The box belongs in final report presentation after M3/M4 settle criteria. | Report callout separating current traction from future criteria. | No. |
| Soften "best Barcarolle candidate" to "best promoted research candidate in this retrospective comparison." | 0530 minor finding | accept_now | M5_reviewer_ready_report_revision | P1_before_final_publication_or_broader_review | Avoids making the current candidate sound like an established mainline. | This is wording cleanup for reviewer-ready revision. | Consistent softened wording in v1 revision. | No. |
| Define quantitative support requirements for repos, windows, future tasks, adapter cells, and fallback share. | 0530 minor finding and paid-readiness section | route_to_M4 | M4_validation_or_candidate_hardening | P0_blocker | Sparse support is currently a claim-boundary issue. | Support thresholds are protocol gates. | Quantitative support threshold table. | Yes. |
| Resolve review-bundle commit provenance drift before any paid runbook. | 0530 minor finding | route_to_M4 | M4_validation_or_candidate_hardening | P1_before_final_publication_or_broader_review | Paid readiness needs a single immutable artifact set. | This is hygiene for future validation, not current M2 evidence. | Immutable artifact-set rule in future protocol. | Yes. |
| Full hierarchical beta-binomial modeling, shrinkage-weighted compiler revival, tuning-loop integration, public benchmark packaging, and broad productization can wait. | 0530 paid-readiness section | reject_scope_expansion | reject_short_term_scope_expansion | P2_deferred | Keeps M2-M6 from absorbing long-term infrastructure or product scope. | These ideas are not proposal P0 blockers and should not drive the short-term plan. | Explicit non-scope list. | No. |

## 6. 0526-1 Task-Supply Guidance Triage

The 2026-05-26-1 task-supply plan is useful source-adapter guidance, but it
must stay inside Layer 1 supply infrastructure. It should not turn the proposal
into a general task-generator project.

| Guidance | Source | Class | Route | Priority | Claim impact | Why this route | Expected output | Can affect paid-validation readiness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Preserve Barcarolle's compiler/certification/target-profile core and treat generation as Layer 1 supply infrastructure. | 0526-1 executive answer; risk 1 | needed for proposal P0 | M2_boundary_or_wording | P0_blocker | Protects the project boundary against task-generator drift. | This is a claim-boundary rule, not implementation work. | Boundary text used by M5 related-work and architecture sections. | No. |
| Use a hybrid design: stronger internal repo-history supply plus external source adapters as candidate pools and design references. | 0526-1 executive answer | relevant but M3/M4 scoped | M3_evidence_package | P1_before_final_publication_or_broader_review | Supports source-supply status without making external generators authoritative. | M3 can summarize source-supply viability and caveats; broad implementation is deferred. | Concise Layer 1 source-supply status. | Indirectly. |
| Normalize candidates through a `TaskSourceAdapter v2` schema with provenance, license, source system, oracle source, environment, leakage, and raw-artifact hygiene fields. | 0526-1 Section 5.1 | relevant but M3/M4 scoped | M4_validation_or_candidate_hardening | P1_before_final_publication_or_broader_review | Informs release schema and future source eligibility gates. | Schema work belongs to validation/candidate hardening only where it affects release artifacts. | Release artifact schema inputs and source eligibility fields. | Yes. |
| Treat all external candidates as untrusted and require local certification before release inclusion. | 0526-1 Section 5.1 | needed for proposal P0 | M4_validation_or_candidate_hardening | P0_blocker | Protects benchmark-side artifact trust boundaries. | This directly affects release schema and future validation protocol. | Certification rule in release schema and validation checklist. | Yes. |
| Expand internal repo-history mining to PR/issue/commit/regression/synthetic/manual reservoirs. | 0526-1 Section 5.2 | deferred infrastructure | defer_post_proposal | P2_deferred | Useful for future supply, but not necessary to finish M2 proposal triage. | Broad generator implementation would exceed short-term proposal scope. | Deferred source-adapter backlog item. | Indirectly. |
| Track `source_reservoir` mix and prevent one source from dominating release supply. | 0526-1 Sections 5.2 and 5.6 | relevant but M3/M4 scoped | M4_validation_or_candidate_hardening | P1_before_final_publication_or_broader_review | Supports source-quality and fallback governance. | Source caps may become paid-readiness thresholds. | Source-mix threshold candidates in M4. | Yes. |
| Move historical environment synthesis and subgate labels earlier in certification. | 0526-1 Section 5.3 | relevant but M3/M4 scoped | M4_validation_or_candidate_hardening | P1_before_final_publication_or_broader_review | Improves auditability of certification failures and release schema. | It informs future release artifacts but should not be implemented during M2. | Environment subgate fields and certification-status wording. | Yes. |
| Add oracle-source labels and keep generated/synthetic oracles separate from real changed tests. | 0526-1 Section 5.4 | relevant but M3/M4 scoped | M4_validation_or_candidate_hardening | P1_before_final_publication_or_broader_review | Prevents source mixing from weakening predictive-validity claims. | Oracle-source labels belong in release schema and validation rules. | Oracle-source schema field and synthetic-source cap. | Yes. |
| Use endpoint-compliant LLM statement generation only as optional, with raw prompts/completions uncommitted. | 0526-1 Section 5.5 | deferred infrastructure | defer_post_proposal | P2_deferred | Reinforces artifact hygiene and endpoint policy without creating an M2 action. | M2 is no-paid and does not generate statements. | Deferred statement-review policy update if task-supply work resumes. | No. |
| Require per-repo supply gates such as certified count, independent reservoirs, source caps, commit-message limits, environment reproducibility, oracle validity, and statement quality. | 0526-1 Section 7 | relevant but M3/M4 scoped | M4_validation_or_candidate_hardening | P1_before_final_publication_or_broader_review | These gates can block paid readiness even when algorithm evidence improves. | M4 should decide which source-support thresholds are necessary for a future paid protocol. | Source-support gate table. | Yes. |
| Run a local generator/source bakeoff across attrs, boltons, humanize, toolz, and optional repos. | 0526-1 Sections 6 and 9 | deferred infrastructure | defer_post_proposal | P2_deferred | Valuable future work but not a proposal P0 placeholder and not a current runbook output. | The current runbook explicitly must not draft the next generator runbook. | Deferred candidate for later source-supply work. | Indirectly. |
| Adopt SWE-smith, SWE-Bench++, SWE-bench-Live, or R2E-style systems as default trusted supply. | 0526-1 comparison table and risks | rejected as short-term scope expansion | reject_short_term_scope_expansion | P2_deferred | Would recenter Barcarolle around task generation and external systems. | External systems can be references or reservoirs only after local certification. | Rejected short-term scope expansion. | No. |

## 7. Claim Boundary Updates Needed

M2 does not change the core claim boundary: predictive validity remains
unestablished and paid validation remains unauthorized. Supporting documents
only need route synchronization:

- mark M2 triage complete;
- route evidence-producing P0 gaps to M3;
- route validation/candidate-policy paid-readiness gaps to M4;
- route citation, figure, current-evidence caveat, and final prose work to M5;
- mark staffing, budget ceiling, owners, and approval format as user decisions
  before M6.

No guardrail is relaxed.

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
