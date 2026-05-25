# Phase 1 Diff-Assisted Statement Regeneration Process

Generated: `2026-05-25T02:52:58Z`.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `a3f0834cd8a7550f1267d38b4c9cbe0311b057fa`.
- Python: `Python 3.9.6`.
- uv: `uv 0.11.16 (Homebrew 2026-05-21 aarch64-apple-darwin)`.
- Paid ACUT calls: `disabled`.
- Paid solver cells: `disabled`.
- Paid LLM generation/review: `enabled by endpoint proof`.
- Endpoint proof: `LLM_BASE_URL` present, `LLM_API_KEY` present, sanitized host `apirx.boyuerichdata.com`.
- Historical paid outcomes available to generator/reviewer: `false`.
- Raw prompts, completions, logs, target diffs, solver workspaces, and verifier workspaces committed: `false`.

## Alignment

- Proposal alignment: `/Users/chenmohan/Downloads/barcarolle-research-0519.md` frames Barcarolle as a target-repository benchmark compiler that compiles candidate task pools from repository history into calibrated benchmark releases. This permits compiler-side use of repository history while preserving the solver-visible no-answer-leakage boundary.
- Statement-hardened screen alignment: the current screen found too few eligible tasks and required replacement supply, but its rejection counts are dominated by old statement-quality flags.
- Validation decision alignment: future paid validation remains blocked until a frozen preregistration exists.
- Attrs H_future evidence alignment: old paid observations remain statement-quality-confounded and do not establish predictive validity.

## Design Correction

The old 240-character `body_summary` truncation is treated as a statement-renderer defect, not as task invalidity. Old candidates are not rejected merely for old 240-character truncation. The runbook question is whether diff-assisted regenerated statements can recover the old candidate pool safely without exposing target diffs, hidden verifier material, paid outcomes, or exact implementation recipes.

## Existing Unrelated Worktree Paths

- `docs/experiments/phase-1-statement-hardened-holdout-preregistration-runbook.md`
- `docs/experiments/phase-1-attrs-generalization-third-repo-decision-runbook.md`
- `docs/experiments/phase-1-attrs-h-future-statement-quality-audit-runbook.md`
- `docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`
- `docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md`
- `docs/experiments/phase-1-policy-violation-triage-bounded-rerun-runbook.md`

## Step Status

- Step 0 preflight: `completed`.
- Step 1 candidate source packets: `completed`.
- Step 2 generator/reviewer prompt templates: `completed`.
- Step 3 generation/review loop: `completed`.
- Step 4 deterministic QA: `completed`.
- Step 5 regenerated statement screen: `completed`.
- Step 6 recovery decision: `completed`.
- Step 7 closeout: `completed`.

## Commits Created

- `d02bc5b3` Record diff-assisted statement regeneration preflight
- `b2b03533` Build diff-assisted candidate source packets
- `a7a27bde` Add diff-assisted statement generator reviewer prompts
- `4f0f2ad5` Run diff-assisted statement generation review loop
- `479dd6c9` Add deterministic QA for regenerated statements
- `eb1437a4` Rerun statement-hardened screen with regenerated statements
- `a7014e08` Decide diff-assisted statement recovery branch
- `Record diff-assisted statement regeneration closeout` updates this report.

## Results

- Candidate packets built: `22`.
- Regenerated statements reviewed: `22`.
- Review pass/revise/reject counts: `19` / `0` / `3`.
- Deterministic QA pass/reject counts: `19` / `3`.
- Eligible before regeneration: `4`.
- Eligible after regeneration: `19`.
- Selected counts after regeneration: `{'attrs/B_eval': 4, 'attrs/H_future': 4, 'boltons/B_eval': 4, 'boltons/H_future': 0}`.
- Old candidate pool recovered: `partial`.
- Replacement supply still needed: `true`.
- Remaining hole: `boltons/H_future`.
- Primary decision: `partial_recovery_mine_targeted_replacement_supply`.
- Next runbook path: `docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md`.

## Artifact Hygiene

- Paid LLM calls made: `false`.
- Paid ACUT calls made: `false`.
- Paid solver cells run: `false`.
- Raw prompts committed: `false`.
- Raw completions committed: `false`.
- Raw Codex CLI logs committed: `false`.
- Raw target diffs committed: `false`.
- Solver or verifier workspaces committed: `false`.
- Historical score tables rewritten: `false`.

## Worktree Closeout

`git status --short` after verification shows only pre-existing unrelated runbook-doc changes:

- ` M docs/experiments/phase-1-statement-hardened-holdout-preregistration-runbook.md`
- `?? docs/experiments/phase-1-attrs-generalization-third-repo-decision-runbook.md`
- `?? docs/experiments/phase-1-attrs-h-future-statement-quality-audit-runbook.md`
- `?? docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`
- `?? docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md`
- `?? docs/experiments/phase-1-policy-violation-triage-bounded-rerun-runbook.md`

## Verification

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_diff_assisted_statement_regeneration.py` -> `15 passed`.
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py experiments/phase0_headroom/tools/test_workspace_acut_run.py` -> `49 passed`.
- `git diff --check` -> passed.
