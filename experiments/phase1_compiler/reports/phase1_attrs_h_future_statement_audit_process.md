# Phase 1 Attrs H_future Statement-Quality Audit Process

Generated: `2026-05-25T01:34:18Z`.

## Step 0 Preflight

This runbook is local-only. It explicitly disables paid ACUT calls, paid LLM
calls, reruns of existing scoreable cells, and reruns of the confirmed
`attrs__hist__027` policy violation.

Repository state was recorded at branch `codex/restart-benchmark-compiler`,
HEAD `58f25b620d64504c87dd7d5fb196dfcf4c2d2bcb`. `uv` is available as
`uv 0.11.16`; `uv run --project experiments/phase1_compiler python --version`
reports `Python 3.11.13`.

Existing untracked paths were recorded and not touched by this preflight:

- `docs/experiments/phase-1-attrs-generalization-third-repo-decision-runbook.md`
- `docs/experiments/phase-1-attrs-h-future-statement-quality-audit-runbook.md`
- `docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`
- `docs/experiments/phase-1-policy-violation-triage-bounded-rerun-runbook.md`

The current paid score tables and derived score artifacts are immutable inputs
for this audit. This runbook may add sidecar audit, sensitivity, preview, and
decision artifacts, but it must not rewrite, rescore, rerun, or relabel paid
cells.

The four `attrs` H_future task IDs under audit are:

- `attrs__hist__012`
- `attrs__hist__013`
- `attrs__hist__023`
- `attrs__hist__027`

Input evidence was locked by digest in
`experiments/phase1_compiler/results/phase1_attrs_h_future_statement_audit_preflight.json`.
The locked evidence says:

- `attrs` B_eval remains `7/8` scoreable pass.
- `attrs` H_future remains `1/7` scoreable pass with one non-scoreable policy
  violation.
- Predictive validity remains `false`.
- Production ranking remains `not_produced`.
- The current two-repo decision remains
  `report_two_repo_negative_or_underpowered_pilot`.

Proposal alignment was checked against
`/Users/chenmohan/Downloads/barcarolle-research-0519.md`. The relevant
governing direction is that Barcarolle is a repo-specific benchmark compiler:
its research value is task selection, calibration, quality control, and
predictive validity, not task production yield, ACUT internals, or public
leaderboard ranking.

No paid calls were made. No raw prompts, completions, ACUT transcripts, public
issue/PR bodies, solver workspaces, verifier workspaces, raw patches, or hidden
oracle material were committed.

## Step 1 Durable Task-Design Audit Tool

Added `experiments/phase1_compiler/tools/phase1_attrs_statement_quality_audit.py`
and focused tests in
`experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py`.

The tool loads only sanitized committed artifacts: attrs certified tasks, attrs
source context, and the Phase 1 two-repo task outcome matrix. It computes
machine-readable statement-quality flags, keeps policy violations out of
scoreable fail counts, and emits deterministic JSON and Markdown.

Test run:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py`

Commit: `28377d73 Add attrs H_future statement quality audit`.

## Step 2 Task-Design Audit Sidecar

Generated:

- `experiments/phase1_compiler/results/phase1_attrs_h_future_task_design_audit.json`
- `experiments/phase1_compiler/reports/phase1_attrs_h_future_task_design_audit.md`

Result: all four audited tasks have plausible mechanism/scope metadata from
sanitized certification gates, but all four also have material
statement-quality risk. The report distinguishes this statement confound from
verifier/oracle machinery and does not overwrite previous failure-taxonomy or
score artifacts.

Commit: `0804acc0 Generate attrs H_future task design audit`.

## Step 3 Statement-Risk Sensitivity

Generated:

- `experiments/phase1_compiler/results/phase1_attrs_h_future_statement_sensitivity.json`
- `experiments/phase1_compiler/reports/phase1_attrs_h_future_statement_sensitivity.md`

Key result: the original attrs H_future metric remains `1/7` scoreable pass.
Excluding the highest-risk task or tasks is reported only as sensitivity
analysis. The strict clean-statement view has zero scoreable cells and reports
`insufficient_clean_attrs_h_future_evidence`.

Test run:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py`

Commit: `dea0c115 Quantify attrs H_future statement-risk sensitivity`.

## Step 4 Statement-Quality Hardening

Added shared helper:

- `experiments/phase0_headroom/tools/statement_quality.py`

Wired it into:

- `experiments/phase0_headroom/tools/repo_history_pilot.py`
- `experiments/phase0_headroom/tools/workspace_acut_run.py`
- `experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py`
- `experiments/phase1_compiler/tools/phase1_attrs_statement_quality_audit.py`

The helper detects old 240-character truncation, unclosed code fences, trailing
incomplete sentences, empty problem summaries, PR-context risk, and missing
editable implementation scope. Future clean-supply candidates with severe
statement risk now carry explicit `statement_quality` diagnostics and are not
silently promoted as clean.

Required test run passed:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py experiments/phase0_headroom/tools/test_workspace_acut_run.py`
- Result: `40 passed`.

Commit: `4ee2924a Harden clean supply statement quality checks`.

## Step 5 Statement Preview Sidecars

Generated:

- `experiments/phase1_compiler/results/phase1_attrs_h_future_statement_preview.json`
- `experiments/phase1_compiler/reports/phase1_attrs_h_future_statement_preview.md`

The previews are diagnostic only. They use short sanitized public excerpts,
implementation-only editable paths, known non-editable test paths, verifier
command metadata, and statement-quality flags. They are not scoreable results
and do not change previous paid outcomes.

Test run:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py`

Commit: `7b4aebe0 Generate attrs H_future statement preview sidecars`.

## Step 6 Evidence Status

Generated:

- `experiments/phase1_compiler/results/phase1_attrs_h_future_evidence_status.json`
- `experiments/phase1_compiler/reports/phase1_attrs_h_future_evidence_status.md`
- `docs/experiments/phase-1-statement-hardened-holdout-preregistration-runbook.md`

Primary status:
`not_clean_enough_for_predictive_validity_claim`.

Next branch:
`prepare_statement_hardened_preregistration`.

Interpretation: the original paid attrs H_future result remains directionally
bad, but every audited task has material statement-quality risk and the strict
clean-statement view has no scoreable cells. The attrs H_future collapse should
not be used as a clean holdout signal for the proposal's predictive-validity
claim.

Commit: `72cce7e2 Decide attrs H_future evidence status`.

## Step 7 Closeout

Steps completed: `0` through `6`; this closeout records the final process
state.

Paid calls made: `false`.

Raw artifacts committed: `false`.

Current evidence status:
`not_clean_enough_for_predictive_validity_claim`.

Recommended next runbook:
`docs/experiments/phase-1-statement-hardened-holdout-preregistration-runbook.md`.

Stop condition before future paid work: require a new frozen release or
preregistration, and explicit user approval for any paid ACUT or LLM calls.

