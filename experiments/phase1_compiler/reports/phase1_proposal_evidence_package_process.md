# Phase 1 Proposal Evidence Package Process

Current step: `Step 0 - Preflight And Artifact Plan`.

Completed artifacts:

- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_preflight.json`
- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_process.md`

Boundary:

- New paid ACUT solver cells run: `false`.
- New paid LLM calls run: `false`.
- External reviewer calls run: `false`.
- Public citation browsing run: `false`.
- Score tables, selected task IDs, split labels, source eligibility artifacts, task statements, and completed decisions changed: `false`.
- Predictive validity established: `false`.
- Paid validation authorized: `false`.
- Later M4/M5/M6 runbook drafted: `false`.

Preflight evidence:

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `3ca073a874c1f74e4c2d240504ac742783244986`.
- Date UTC: `2026-06-01`.
- Missing required inputs: `0`.
- `git diff --check` return code at preflight: `0`.

Artifact plan:

A narrow proposal-evidence tool is needed. The existing retrospective signal tool produced the outcome-blind universe, selection freeze, score join, adapter metrics, five-seed random baseline, baseline comparison, and uncertainty labels. It does not emit the M3 package requested by the runbook: many-seed random distribution, baseline envelope by slice, coverage-objective ablation, fallback-share accounting, source-supply status, one-page preliminary evidence summary, and compact report evidence index.

Planned new files:

- `experiments/phase1_compiler/configs/phase1_proposal_evidence_package.yaml`
- `experiments/phase1_compiler/tools/phase1_proposal_evidence_package.py`
- `experiments/phase1_compiler/tests/test_phase1_proposal_evidence_package.py`

Planned outputs remain limited to `phase1_proposal_evidence_package_*` results/reports and `docs/research/phase-1-proposal-evidence-package.md`.
