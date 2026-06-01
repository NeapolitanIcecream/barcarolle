# Phase 1 Proposal Report Reviewer-Ready Revision Process

Status: M5 execution process report, 2026-06-01.

## Step 0: Preflight And Reader Contract

Current Git commit at preflight:
`368525cb3ec7b930f0c3a3b4128eb3df3f44232d`.

Boundary flags:

| Flag | Value | Evidence |
| --- | --- | --- |
| M4 stop label | `validation_protocol_hardened_candidate_not_paid_ready` | `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md`; `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md`; `PROCESS.md` |
| Paid ACUT cells allowed in M5 | `false` | M5 runbook boundary |
| Paid LLM calls allowed in M5 | `false` | M5 runbook boundary |
| External reviewer calls allowed in M5 | `false` | M5 runbook boundary |
| Public citation browsing allowed | `true_for_related_work_only` | M5 runbook boundary |
| Score table edits allowed | `false` | M5 runbook boundary |
| Selected task ID or split-label edits allowed | `false` | M5 runbook boundary |
| Paid validation authorized | `false` | M4 decision and M5 runbook |
| Predictive validity established | `false` | M4 decision and M5 runbook |

Input artifacts read or inspected:

- `AGENTS.md`
- `PROCESS.md`
- `docs/experiments/phase-1-proposal-report-reviewer-ready-revision-runbook.md`
- `docs/research/phase-1-proposal-report-v1.md`
- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`
- `docs/research/phase-1-proposal-evidence-todo-matrix.md`
- `docs/research/phase-1-proposal-p0-placeholder-triage.md`
- `docs/research/phase-1-proposal-claim-boundary.md`
- `docs/research/phase-1-proposal-evidence-package.md`
- `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_coverage_ablation.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_report_evidence_index.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_claim_modes.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_candidate_policy.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_adapter_estimand.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_support_thresholds.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_release_schema.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_power_budget_note.md`
- `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md`

Reader contract for `docs/research/phase-1-proposal-report-v2.md`:

| Item | Contract |
| --- | --- |
| Target reader | Project/proposal reviewer deciding whether the next research phase is worth approving. |
| Decision requested | Approve the next no-paid research phase and allow M6 approval-artifact preparation after user-owned resource and format decisions. |
| Current claim | Phase 1 shows traction and a credible validation path: the target-repo prediction problem is real, benchmark construction changes MAE, clean benchmark-side ACUT execution is feasible, and the current candidate beats/ties most same-budget random selections. |
| Explicit non-claim | Predictive validity is not established; paid validation is not authorized; M4 gates are future project-stage standards, not proof that the current candidate is already valid or paid-ready. |

Acceptance evidence:

- The M4 stop label was found in the M4 hardening summary, M4 decision report, and `PROCESS.md`.
- `git status --short -- docs/research/phase-1-proposal-report-v1.md` returned no changes at preflight.
- No paid ACUT cells, paid LLM calls, or external reviewer calls were made in this step.

## Step 1: Reviewer-Facing Argument Map

Claim: approve the next research phase for Barcarolle as a repo-specific
benchmark compiler.

| Reason | Evidence | Warrant | Limit |
| --- | --- | --- | --- |
| The target-repo prediction problem is real and consequential. | Public SWE benchmarks evaluate real coding tasks, but Barcarolle's Phase 1 weighted pilot and local bakeoff show that benchmark construction choices can move target-repo MAE materially. | If teams use coding agents on future work in their own repositories, benchmark scores need to estimate that future target-repo performance rather than only broad benchmark rank. | The old weighted design failure is diagnostic negative evidence, not a successful compiler result. |
| The benchmark-side protocol is technically tractable. | The three-repo paid pilot completed 120/120 cells with scoreability 1.0; click source context was repaired for 30/30 tasks with zero paid calls; artifact hygiene and endpoint accounting were reported. | A proposal is credible only if the benchmark compiler can prepare solver workspaces, preserve hidden-oracle boundaries, invoke ACUT harnesses, and capture/replay diffs without taking over ACUT internals. | Technical tractability does not prove predictive validity. |
| The optimization target is meaningful and shows signal. | M3 reports candidate MAE `0.209` versus best simple aggregate baseline `0.2149`, a `0.0059` MAE edge; the candidate beats/ties `93.4%` of 1000 same-budget random selections. | MAE is an average prediction-error metric. If task selection changes MAE and usually beats same-budget random selections, selection is not pure noise and is worth optimizing. | The simple-baseline edge is small, below M4's future `0.02` margin, and adapter/repo/fallback diagnostics are fragile. |
| The path to predictive validity is concrete. | M4 defines study modes, per-named-ACUT estimand, mandatory baselines, fallback caps, support thresholds, joint success gate, release schema, and no-paid power/budget scenarios. | A proposal can justify the next phase when the success standard is explicit and prevents post-hoc validation claims. | M4 gates are future standards; the current M3 candidate does not pass them and paid validation remains unauthorized. |

Argument boundary:

- Random-baseline evidence is used as optimization traction, not as a validated-predictor claim.
- M4 gate failures are used to define next-phase work, not as a reason to reject the proposal.
- Codex/Kilo differences are ACUT-configuration evidence, not model-only superiority.
- The candidate is named `coverage_constrained_unweighted_v1_with_labeled_fallbacks` and remains composite because of boltons fallback behavior.

## Step 2: Citation And Related-Work Matrix

Output:
`experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md`.

Public citation browsing was limited to related-work and benchmark-validity
verification. Sources recorded:

- SWE-bench ICLR 2024 paper.
- OpenAI SWE-bench Verified launch page.
- OpenAI 2026 SWE-bench Verified quality and contamination audit.
- SWE-bench-Live project page.
- SWE-smith project page.
- R2E-Gym official repository.
- UC Berkeley `Validity Challenges in Machine Learning Benchmarks`.

Acceptance evidence:

- The citation matrix records label, URL, date, supported claim, prohibited
  overuse, and v2 location for each public source.
- Public sources support external related-work framing only.
- Local planning files are not used as reviewer-facing literature citations in
  v2.

## Steps 3-9: V2 Report Draft, Evidence, Validation Path, Figures, Risks, And Decisions

Output:
`docs/research/phase-1-proposal-report-v2.md`.

Accepted structure:

1. Executive Summary
2. Problem And Stakes
3. Barcarolle Thesis And Boundary
4. Proposed Compiler Design
5. Evidence For Project Approval
6. Validation Path And Success Standards
7. Risks, Limits, And Mitigations
8. Proposed Next Phase
9. Deliverables And Decision Points
10. Appendices

M3 integration evidence:

- Current candidate MAE: `0.209`.
- Best simple aggregate baseline: `temporal_recent_baseline`, MAE `0.2149`.
- Best-simple-baseline edge: `0.0059` MAE.
- 1000-seed same-budget random comparison: candidate beats/ties `93.4%`.
- Fallback caveat: `6/18` selected slots use fallback; boltons is `6/6`
  fallback.
- Adapter caveat: Codex fails while Kilo passes under current diagnostics.

M4 integration evidence:

- Study-mode table included.
- Primary adapter estimand recorded as per named ACUT configuration.
- Mandatory baselines listed.
- Fallback caps and current M3 failures included.
- Joint success gate and support thresholds included.
- Release schema summarized with pointer to the full M4 schema.
- No-paid power/budget note included without setting a budget ceiling.

Figures and tables included:

- Compiler architecture Mermaid figure.
- North-star validation design Mermaid figure.
- One-page evidence summary.
- Release artifact schema summary.
- Report evidence index.
- Risk summary and standalone risk-register pointer.
- User-owned decision table.

Risk-register output:
`experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_risk_register.md`.

Acceptance evidence:

- V2 no longer reads as a roadmap, lab notebook, or placeholder register.
- M4 gates are framed as future project-stage standards, not pre-proposal proof
  requirements.
- V2 does not invent no-paid staffing, duration, owner categories, approval
  format, or paid budget ceiling.

## Step 10: Reviewer-Readiness Audit

Output:
`docs/research/phase-1-proposal-report-reviewer-ready-checklist.md`.

Required audit commands:

```text
rg -n "\[NEEDS" docs/research/phase-1-proposal-report-v2.md
rg -n "validated predictive benchmark compiler|proves predictive validity|established predictive validity|paid validation authorized|model-only superiority" docs/research/phase-1-proposal-report-v2.md
rg -n "/Users/chenmohan/Downloads" docs/research/phase-1-proposal-report-v2.md
```

Recorded result: all three commands returned no matches.

Acceptance evidence:

- The checklist covers claim boundary, evidence support, citation coverage,
  related-work distinction, M3 evidence integration, M4 validation-path
  integration, prohibited claims, remaining user decisions, artifact hygiene,
  paid/no-paid boundary, and readability.
- Remaining unresolved items are user-owned M6 or later paid-discussion
  decisions, not evidence placeholders.

## Step 11: Handoff Synchronization

Updated handoff files:

- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`
- `docs/research/phase-1-proposal-evidence-todo-matrix.md`
- `PROCESS.md`

Recorded handoff state:

- M5 is complete.
- Active report path: `docs/research/phase-1-proposal-report-v2.md`.
- Technical review can proceed from v2.
- M6 can proceed only after user decisions on artifact format, staffing and
  duration, owner categories, and any conditional paid budget ceiling.
- Paid validation remains unauthorized.
- Predictive validity remains future work.
- No M6 runbook was drafted during M5 execution.

## Step 12: Closeout

Closeout outputs:

- `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_decision.md`
- `experiments/phase1_compiler/results/phase1_proposal_report_reviewer_ready_revision_decision.json`

Closeout decision:

- Stop label: `proposal_report_reviewer_ready_for_technical_review`.
- V2 report path: `docs/research/phase-1-proposal-report-v2.md`.
- V2 is reviewer-ready for technical proposal review.
- Predictive validity is not established.
- Paid validation is not authorized.
- M6 can proceed only after user decisions.
- Remaining placeholders in v2: `0`.
- Remaining open items are user-owned M6 or later budget-bearing decisions.
