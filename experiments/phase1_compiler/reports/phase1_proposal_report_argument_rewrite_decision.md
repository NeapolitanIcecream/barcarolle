# Phase 1 Proposal Report Argument Rewrite Decision

Decision label: `proposal_report_argument_rewrite_complete`.

What happened: `docs/research/phase-1-proposal-report-v0.md` was rewritten as
a reader-facing proposal argument. The report now leads with the reader
problem, research question, qualified claim, reasons, evidence, warrants,
objections, responses, limitations, and a scoped no-paid next phase.

Why it matters: the proposal report now answers why Barcarolle should continue
toward repo-specific predictive validity instead of exposing the internal
milestone plan. The roadmap remains in
`docs/research/phase-1-proposal-roadmap-and-claim-planning.md`.

Action suggested next: run no-paid external-review triage first, then use the
accepted findings to consolidate proposal-critical evidence and harden the
validation protocol. Do not draft a follow-up runbook from this closeout.

## Boundary

- No paid ACUT solver cells were run.
- No paid LLM calls were made.
- No external reviewer call was made.
- No new roadmap file was created.
- Completed paid outcomes, score tables, selected task IDs, split labels,
  source-eligibility artifacts, task statements, and completed decisions were
  not changed.
- Predictive validity is not established.
- Paid validation is not authorized.

## Report Outcome

The report now reads as a proposal argument rather than a roadmap. It keeps
predictive validity as the long-term north star while limiting the current
claim to Phase 1 traction evidence and a credible no-paid hardening path.

The rewritten report explicitly includes:

- a reader-facing problem and consequence;
- the north-star predictive-validity question;
- a qualified short-term proposal claim;
- evidence from the weighted failure, local bakeoff, three-repo paid pilot,
  adapter diagnostics, click source repair, retrospective signal, and frozen
  candidate policy;
- warrants connecting evidence to the claim;
- objections and responses;
- limitations near the claims they qualify;
- a scoped next phase that does not authorize paid validation.

## Updated Artifacts

- `docs/research/phase-1-proposal-report-v0.md`
- `docs/research/phase-1-proposal-argument-map.md`
- `docs/research/phase-1-proposal-evidence-todo-matrix.md`
- `docs/research/phase-1-proposal-claim-boundary.md`
- `PROCESS.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_argument_rewrite_process.md`
- `experiments/phase1_compiler/results/phase1_proposal_report_argument_rewrite_decision.json`

## Verification

- Report scan for `M2` through `M6` roadmap labels in
  `docs/research/phase-1-proposal-report-v0.md`: passed.
- Prohibited claim scan in the rewritten report: passed.
- `git diff --check`: passed.
