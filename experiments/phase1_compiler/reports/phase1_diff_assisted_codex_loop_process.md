# Phase 1 Diff-Assisted Codex Loop Statement Regeneration Process

Generated: `2026-05-25T04:55:14Z`.
Closeout updated: `2026-05-25T05:10:29Z`.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `448b25a56b2eac1e62a6004bf599428cf10b95b4`.
- Python: `Python 3.11.13`.
- uv: `uv 0.11.16 (Homebrew 2026-05-21 aarch64-apple-darwin)`.
- Codex CLI available: `True`.
- tmux available: `True`.
- Local Codex Subscription generation/review conditionally enabled: `True`.
- LLM API endpoint used for generator/reviewer: `False`.
- LLM API calls made for generator/reviewer: `False`.
- Paid ACUT calls: `disabled`.
- Paid solver cells: `disabled`.
- Raw prompts, completions, CLI logs, target diffs, solver workspaces, and verifier workspaces committed: `false`.

## Prior Deterministic Result Reinterpretation

The previous `phase1_diff_assisted_statement_*` artifacts are historical dry-run context only. They are valid as deterministic tooling prototype evidence and as evidence that the old 240-character statement renderer over-penalized some candidates. They are not valid as independent Codex CLI generated statement evidence, independent Codex CLI review evidence, a basis for freezing a statement-hardened release, or a basis for paid validation.

## Existing Unrelated Worktree Paths

- `docs/experiments/phase-1-statement-hardened-holdout-preregistration-runbook.md`
- `docs/experiments/phase-1-attrs-generalization-third-repo-decision-runbook.md`
- `docs/experiments/phase-1-attrs-h-future-statement-quality-audit-runbook.md`
- `docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`
- `docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md`
- `docs/experiments/phase-1-policy-violation-triage-bounded-rerun-runbook.md`

## Step Status

- Step 0 preflight: `completed`.
- Step 1 candidate packets: `completed`.
- Step 2 workflow files and prompt templates: `completed`.
- Step 3 generator session: `delivered`.
- Step 4 reviewer session: `delivered`.
- Step 5 deterministic QA: `completed`.
- Step 6 statement-hardened screen: `completed`.
- Step 7 recovery decision: `partial_recovery_mine_targeted_replacement_supply`.
- Step 8 closeout: `completed`.

## Recent Commits

```text
dccbed35 Decide diff-assisted Codex loop recovery branch
c2cc94ba Screen Codex-reviewed regenerated statements
89edacae Run deterministic QA for Codex-reviewed statements
00de1c8c Run real Codex statement reviewer session
63a87ec0 Run real Codex statement generator session
31b332ef Create diff-assisted Codex generator reviewer workflow
f1af76d8 Build diff-assisted Codex loop candidate packets
96645387 Record diff-assisted Codex loop preflight
```

## Results

- Candidate packets built: `22`.
- Generated statements delivered: `22`.
- Review pass/revise/reject counts: `{'pass': 22}`.
- Deterministic QA pass/reject counts: `{'pass': 22}`.
- Eligible before regeneration: `4`.
- Eligible after regeneration: `22`.
- Old candidate pool recovered: `partial`.
- Replacement supply still needed: `True`.
- Primary decision: `partial_recovery_mine_targeted_replacement_supply`.
- Next runbook path: `docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md`.

## Non-Negotiable Evidence

- Real generator Codex CLI session started: `True`.
- Real reviewer Codex CLI session started: `True`.
- Generator/reviewer used local Codex Subscription: `True`.
- Generator/reviewer did not use LLM API endpoint: `True`.
- Generator process file present: `True`.
- Reviewer process file present: `True`.
- Generator output not deterministic override: `True`.
- Reviewer output not deterministic rules only: `True`.
- Raw CLI logs committed: `False`.
- Paid ACUT solver cells run: `False`.
- Historical paid outcomes used for generation or review: `False`.

## Artifact Hygiene

- LLM API calls made for generator/reviewer: `false`.
- Codex Subscription sessions used: `True`.
- LLM API endpoint used for generator/reviewer: `false`.
- Paid ACUT calls made: `false`.
- Paid solver cells run: `false`.
- Raw prompts committed: `false`.
- Raw completions committed: `false`.
- Raw Codex CLI logs committed: `false`.
- Raw target diffs committed: `false`.
- Solver or verifier workspaces committed: `false`.
- Historical score tables rewritten: `false`.

## Verification

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py` -> `9 passed`.
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_diff_assisted_statement_regeneration.py experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py experiments/phase0_headroom/tools/test_workspace_acut_run.py` -> `64 passed`.
- `git diff --check` -> passed.
