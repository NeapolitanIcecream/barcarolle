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

