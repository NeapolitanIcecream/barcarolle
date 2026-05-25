# Phase 1 Statement-Hardened After Canonical Repair Process

Generated: `2026-05-25T08:11:58Z`.

## Step 0 Preflight

- Status: `completed`.
- Source runbook: `docs/experiments/phase-1-statement-hardened-preregistration-after-canonical-split-repair-runbook.md`.
- Canonical repair decision: `canonical_split_repair_complete_retry_preregistration`.
- Canonical selected task count: `16`.
- Canonical review/QA pass count: `16`.
- Statement-hardened preregistration ready after split repair: `true`.
- Targeted replacement supply still needed: `false`.
- Paid ACUT calls made: `false`.
- Paid solver cells run: `false`.
- Paid LLM calls made: `false`.
- Codex generator/reviewer sessions started by this runbook: `false`.
- Follow-up runbook written by worker: `false`.

## Pre-Existing Dirty Files

The worker recorded these files and did not revert or stage them:

- `AGENTS.md`
- `docs/experiments/phase-1-statement-hardened-holdout-preregistration-runbook.md`
- `docs/experiments/phase-1-statement-hardened-preregistration-after-canonical-split-repair-runbook.md`
- `docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md`
- `docs/experiments/phase-1-attrs-generalization-third-repo-decision-runbook.md`
- `docs/experiments/phase-1-attrs-h-future-statement-quality-audit-runbook.md`
- `docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`
- `docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md`
- `docs/experiments/phase-1-policy-violation-triage-bounded-rerun-runbook.md`

## Step Log

- Step 0: preflight recorded required artifact digests and run boundaries.
- Step 1: added canonical-repair-specific config, tooling, and focused tests.
- Step 2: generated canonical inventory and screen artifacts. All 16 selected tasks had full visible statements, stable digests, review pass, deterministic QA pass, implementation-only editable paths, and separate non-editable test paths.
- Step 3: wrote release preview and froze release manifest `statement_hardened_after_canonical_split_repair_20260525`.
- Step 4: wrote preregistration JSON and Markdown from the frozen manifest.
- Step 5: wrote validation decision and blocker artifacts. The decision is `ready_for_user_approved_paid_validation`, with paid validation still blocked until explicit user approval.
- Step 6: ran required verification commands and recorded closeout.

## Commits

- `cd65edea` - `Record canonical preregistration preflight`
- `9e90851f` - `Add canonical statement-hardened preregistration tooling`
- `34bec9fd` - `Verify canonical statement-hardened inputs`
- `bde4693d` - `Freeze canonical statement-hardened release manifest`
- `5c8af396` - `Write canonical statement-hardened preregistration`
- `2cc62810` - `Decide canonical statement-hardened validation gate`
- Current closeout commit - `Record canonical preregistration closeout`

## Verification

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_preregistration.py`
  - Result: `9 passed in 0.01s`.
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_canonical_split_statement_repair.py experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py experiments/phase0_headroom/tools/test_workspace_acut_run.py`
  - Result: `64 passed in 2.24s`.
- `git diff --check`
  - Result: passed.
- Final completion audit script over required artifacts and JSON invariants
  - Result: `completion-audit-pass`.

## Final State

- Paid ACUT calls made: `false`.
- Paid LLM calls made: `false`.
- Paid solver cells run: `false`.
- Codex generator/reviewer sessions started: `false`.
- Raw artifacts committed: `false`.
- Release frozen: `true`.
- Preregistration written: `true`.
- Primary decision: `ready_for_user_approved_paid_validation`.
- Paid validation blocked until user approval: `true`.
- Recommended next action: `ask user whether to authorize paid validation runbook`.
- Suggested follow-up runbook path: `docs/experiments/phase-1-statement-hardened-paid-validation-runbook.md`.
- Follow-up runbook written by worker: `false`.
- Predictive validity established: `false`.
- Historical paid results repaired or overwritten: `false`.
- `attrs__hist__027` old policy violation repaired by this preregistration: `false`.

## Worktree Note

The pre-existing dirty runbook files recorded in Step 0 remained outside this runbook's commits. The existing tracked `docs/experiments/phase-1-statement-hardened-replacement-supply-runbook.md` predated this run and was not modified. No `docs/experiments/phase-1-statement-hardened-paid-validation-runbook.md` file was created.
