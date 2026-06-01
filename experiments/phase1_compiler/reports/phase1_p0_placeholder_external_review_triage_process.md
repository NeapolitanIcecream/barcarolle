# Phase 1 P0 Placeholder And External Review Triage Process

Status: in progress, no-paid M2 triage, 2026-06-01.

This process report records step-level evidence for
`docs/experiments/phase-1-p0-placeholder-and-external-review-triage-runbook.md`.
It is not a new roadmap, runbook, validation protocol, or paid-run
authorization.

## Step 0: Preflight And Inventory

Timestamp: `2026-06-01T11:39:22+08:00`.

Repository state:

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `c86d1f51f9f610a65eee0065fd0a7a593889c93d`.
- Active report confirmed:
  `docs/research/phase-1-proposal-report-v1.md`.
- Required inputs: all present.
- Existing worktree state included prior uncommitted handoff files and a
  modified `PROCESS.md`; these were recorded in the preflight artifact and not
  treated as new M2 output.

Inventory:

- P0 placeholders in Appendix D: `17`.
- P1 placeholders in Appendix D: `4`.
- Machine-readable preflight:
  `experiments/phase1_compiler/results/phase1_p0_placeholder_external_review_triage_preflight.json`.

Acceptance evidence:

- Paid ACUT solver calls made: `0`.
- Paid LLM calls made: `0`.
- External reviewer calls made: `0`.
- Public citation browsing made: `false`.
- All P0 placeholders from v1 Appendix D inventoried: `true`.
- Missing inputs recorded: `true`; missing input count: `0`.
- Later runbook drafted: `false`.

## Running Notes

M2 will route placeholders and recommendations only. It will not fill
citations, figures, result tables, power notes, validation thresholds, or
release schemas, and it will not authorize paid validation.

## Step 1: P0/P1 Placeholder Routing Table

Output created:

- `docs/research/phase-1-proposal-p0-placeholder-triage.md`.

Routing evidence:

- Every P0 placeholder from proposal report v1 Appendix D appears once in the
  P0 routing table.
- P1 placeholders are routed separately.
- Items requiring user approval are marked `needs_user_decision`.
- Evidence-producing items are routed to later milestones rather than filled
  during M2.

Route counts after Step 1:

| Route | P0 count | P1 count |
| --- | ---: | ---: |
| M2_boundary_or_wording | 0 | 1 |
| M3_evidence_package | 4 | 1 |
| M4_validation_or_candidate_hardening | 8 | 0 |
| M5_reviewer_ready_report_revision | 2 | 1 |
| needs_user_decision | 3 | 1 |

Acceptance evidence:

- Paid ACUT solver calls made: `0`.
- Paid LLM calls made: `0`.
- External reviewer calls made: `0`.
- Evidence-producing work performed: `false`.
- Paid validation authorized: `false`.

## Step 2: External Review And Task-Supply Guidance Triage

Inputs read:

- `/Users/chenmohan/Downloads/barcarolle-research-0530.md`.
- `/Users/chenmohan/Downloads/barcarolle-research-0526-1.md`.

Output updated:

- `docs/research/phase-1-proposal-p0-placeholder-triage.md` sections 5 and 6.

External-review routing summary:

- Accepted now as boundary or wording: candidate naming with labeled
  fallbacks, pseudo-future claim boundary, adapter-stratified reporting, and
  softened "best promoted research candidate" wording.
- Routed to M3: coverage ablation, many-seed random baseline, baseline
  envelope, and fallback-share accounting.
- Routed to M4: paid-readiness gate, frozen validation inputs, baseline
  registry hardening, joint success gate, adapter estimand, fallback
  threshold, quantitative support thresholds, and immutable artifact-set
  hygiene.
- Routed to M5: reviewer-facing box showing current evidence would not pass
  future paid criteria.
- Deferred or rejected: independent outcome-blindness reproduction as optional
  later review; broad modeling/product/task-generator expansion as short-term
  non-scope.

Task-supply routing summary:

- Kept Layer 1 supply infrastructure subordinate to Barcarolle's compiler and
  validation claim.
- Routed source schema, local certification, source-reservoir caps,
  environment subgates, oracle-source labels, and source-support gates to M4
  only where they affect release schema or paid-readiness boundaries.
- Deferred broad generator/source bakeoff implementation.
- Rejected adopting external task systems as trusted default short-term supply.

Acceptance evidence:

- GPT-5.5-Pro advice classified as input, not controlling scope: `true`.
- Task-supply guidance kept inside source-adapter/supply layer: `true`.
- Broad task-generator expansion promoted to core proposal scope: `false`.
- Paid validation authorized: `false`.
- Paid ACUT solver calls made: `0`.
- Paid LLM calls made: `0`.
- External reviewer calls made: `0`.

## Step 3: Claim Boundary And Milestone Map Alignment

Supporting documents updated:

- `docs/research/phase-1-proposal-claim-boundary.md`.
- `docs/research/phase-1-proposal-evidence-todo-matrix.md`.
- `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`.
- `docs/research/phase-1-proposal-p0-placeholder-triage.md`.

Alignment decisions:

- M2 is marked complete in the roadmap and claim-boundary milestone sync.
- M3 owns the next evidence-package work category.
- M4 owns validation and candidate-policy paid-readiness hardening.
- M5 owns reviewer-ready citations, figures, caveats, and final report prose.
- M6 remains blocked on user decisions for format, no-paid staffing/duration,
  conditional paid-validation budget ceiling, and owner categories.

Acceptance evidence:

- Roadmap ownership remains:
  `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`.
- New roadmap file created: `false`.
- Later runbook drafted: `false`.
- Paid validation authorized: `false`.

## Step 4: Triage Quality Gate

Checks run:

```text
rg -n "NEEDS " docs/research/phase-1-proposal-report-v1.md
rg -n "P0_blocker|M3_evidence_package|M4_validation_or_candidate_hardening|M5_reviewer_ready_report_revision|defer_post_proposal|reject_short_term_scope_expansion|needs_user_decision" docs/research/phase-1-proposal-p0-placeholder-triage.md
rg -n "proves predictive validity|established predictive validity|authorizes paid|validated predictive benchmark compiler|model-only superiority" docs/research/phase-1-proposal-p0-placeholder-triage.md docs/research/phase-1-proposal-claim-boundary.md docs/research/phase-1-proposal-evidence-todo-matrix.md docs/research/phase-1-proposal-roadmap-and-claim-planning.md
python3 -m json.tool experiments/phase1_compiler/results/phase1_p0_placeholder_external_review_triage_preflight.json
git diff --check
```

Additional exact-match check:

```text
P0 placeholders from preflight: 17
Missing in triage table: []
Duplicates in triage table: []
```

Results:

- Proposal report v1 still contains `[NEEDS ...]` placeholders as expected;
  M2 routed them but did not fill them.
- Route and priority values are present in the triage document.
- Prohibited-claim phrase matches occur only in prohibited-claim examples or
  negating guardrails, such as "not model-only superiority evidence".
- Preflight JSON validates with `python3 -m json.tool`.
- `git diff --check` passes.

Acceptance evidence:

- All P0 placeholders are routed: `true`.
- All relevant review recommendations are classified: `true`.
- Paid validation authorized: `false`.
- JSON preflight validates: `true`.
- `git diff --check` passes: `true`.
