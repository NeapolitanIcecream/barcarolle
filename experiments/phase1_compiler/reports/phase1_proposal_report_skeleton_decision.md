# Proposal Report Skeleton Decision

Decision label: `proposal_report_skeleton_complete`.

What happened: the M1 proposal report skeleton, argument map, evidence/TODO
matrix, and claim boundary were written.

Why it matters: future work is now pulled by proposal evidence gaps instead of
unrelated experimental branches. The skeleton keeps predictive validity as the
long-term north star while limiting the short-term proposal claim to Phase 1
traction evidence and a credible validation path.

Action suggested next: execute M2 external-review triage or M3 proposal
evidence consolidation, depending on whether reviewer objections or missing
proposal tables are the higher-priority blocker. Do not run paid ACUT cells by
default.

## Boundary

- No paid ACUT solver cells were run.
- No paid LLM calls were run.
- No external GPT-5.5-Pro or reviewer calls were run.
- Predictive validity is not established.
- Paid validation is not authorized.
- M2-M6 remain draft milestone roles; no follow-up runbook was drafted.

## Outputs

- `docs/research/phase-1-proposal-report-v0.md`
- `docs/research/phase-1-proposal-argument-map.md`
- `docs/research/phase-1-proposal-evidence-todo-matrix.md`
- `docs/research/phase-1-proposal-claim-boundary.md`
- `experiments/phase1_compiler/results/phase1_proposal_report_skeleton_preflight.json`
- `experiments/phase1_compiler/results/phase1_proposal_report_skeleton_evidence_todo_matrix.json`
- `experiments/phase1_compiler/results/phase1_proposal_report_skeleton_decision.json`
- `experiments/phase1_compiler/reports/phase1_proposal_report_skeleton_process.md`
- `experiments/phase1_compiler/reports/phase1_proposal_report_skeleton_decision.md`

## Claim Boundary

Allowed short-term claim:

```text
Phase 1 does not prove predictive validity, but it establishes that the
problem is real, measurable, and technically tractable: construction choices
materially affect repo-specific estimates, naive weighting fails in diagnosable
ways, and early retrospective evidence plus policy hardening define a credible
path toward future validation.
```

Prohibited current claims:

- Barcarolle is already a validated predictive benchmark compiler.
- `coverage_constrained_unweighted_v1` has proven predictive validity.
- The current evidence authorizes paid validation.
- Codex/Kilo differences prove model-only superiority.
- Pseudo-future replay establishes predictive validity.

## Evidence Gaps

Highest-priority proposal gaps:

- final short-term proposal claim wording;
- one-page Phase 1 evidence summary table;
- retrospective baseline table with adapter/repo fragility labels;
- fallback-share accounting and `boltons` fallback wording;
- pseudo-future versus predictive-validity boundary wording;
- baseline strengthening plan;
- paid-validation non-authorization statement;
- external review triage of GPT-5.5-Pro recommendations.

## Verification

- `jq` validation for preflight, evidence/TODO matrix, and decision JSON:
  passed.
- Required M1 output path check: passed.
- `git diff --check`: passed.
