# Phase 1 Proposal Report Final-Shape Rewrite Decision

Decision label: `proposal_report_final_shape_rewrite_complete`.

What happened: `docs/research/phase-1-proposal-report-v1.md` was created as a
final-shape proposal report with explicit placeholders for missing evidence,
figures, pseudocode, citations, decisions, numbers, and result-dependent
paragraphs. Supporting proposal documents were aligned so v0 is source material
and v1 is the active proposal-report draft.

Why it matters: remaining pre-proposal work can now be pulled by report blanks
rather than by process drift, chronology, or local curiosity. The report keeps
predictive validity as the north star while separating Phase 1 traction
evidence from formal validation.

Action suggested next: fill the highest-priority placeholders that block
reviewer readiness, especially related-work citations, validation diagrams,
candidate-policy pseudocode, baseline-strengthening results, fallback
thresholds, adapter estimand wording, success gates, and power/budget notes.
Do not authorize paid ACUT validation unless a later decision finds that the
protocol and evidence gates have been hardened.

## Boundary

- Paid ACUT solver cells made: `0`.
- Paid LLM calls made: `0`.
- GPT-5.5-Pro or external-review calls made: `0`.
- Predictive validity established: `false`.
- Paid validation authorized: `false`.
- New roadmap file created: `false`.
- Later runbook drafted: `false`.

## Report State

- Active proposal report: `docs/research/phase-1-proposal-report-v1.md`.
- Superseded source draft: `docs/research/phase-1-proposal-report-v0.md`.
- Roadmap owner:
  `docs/research/phase-1-proposal-roadmap-and-claim-planning.md`.
- Process report:
  `experiments/phase1_compiler/reports/phase1_proposal_report_final_shape_rewrite_process.md`.
- Machine-readable decision:
  `experiments/phase1_compiler/results/phase1_proposal_report_final_shape_rewrite_decision.json`.

## P0 Placeholders Remaining

- Related-work citations for SWE-bench-family, generated-task, and live
  benchmark systems.
- North-star validation figure and compiler architecture figure.
- Candidate benchmark assembly pseudocode.
- Release artifact schema table.
- One-page preliminary evidence summary.
- Many-seed random baseline distribution and candidate percentile.
- Baseline-envelope comparison against the best preregistered simple baseline.
- Coverage-objective ablation.
- Fallback-share threshold and `boltons` fallback treatment.
- Adapter estimand and claim wording.
- Catastrophic-miss threshold and invalid-cell sensitivity rule.
- Joint success gate.
- Power and budget note.
- No-paid staffing and duration.
- Conditional paid-validation budget ceiling, if later gates authorize a paid
  decision.
- Deliverable acceptance criteria and owners.

## Verification

```text
rg -n "M[0-9]|runbook|roadmap|current state|completed cells|score table" docs/research/phase-1-proposal-report-v1.md
  no matches

rg -n "proves predictive validity|established predictive validity|authorizes paid" docs/research/phase-1-proposal-report-v1.md
  no matches

rg -n "predictive validity is established|paid validation is authorized|validated predictive benchmark compiler|model-only superiority" docs/research/phase-1-proposal-report-v1.md
  no matches

git diff --check
  passed

python3 -m json.tool experiments/phase1_compiler/results/phase1_proposal_report_final_shape_rewrite_decision.json
  passed
```
