# Worker Task

You are the WORKER agent. Work in `/Users/chenmohan/gits/barcarolle`.

Run with autonomy. You may edit relevant files, create artifacts, and run commands or tests. Do not ask the user for confirmation unless blocked.

## Task

Repair the Codex NFL output contract / patch replay path that blocked Gate 1, keep Gate 1 clean-replay strict, add regression coverage for ambiguous search/replace on Click task 003 style failures, run a targeted frontier-click-specialist x click__rbench__003 rerun after the fix, and produce a PR-ready report explaining whether Gate 1 can now pass and whether Click 004-008 expansion is justified.

## Work Type

implementation+experiment

## Expected Deliverable

Focused code/tests/artifacts/report for the output-contract replay repair and targeted live rerun, with local reviewer closure and PR-ready evidence.

## Requirements

- Complete the task to the standard implied by the user request and repo conventions.
- Preserve user-approved assumptions, constraints, and existing ownership boundaries.
- Avoid unrelated refactors and do not overwrite user changes.
- For implementation tasks, add or update focused tests when risk justifies it and run relevant verification.
- For experiments or research, record method, inputs, results, limitations, and reproduction steps in the handoff or target artifact.
- Keep changed artifacts internally consistent.

## User-Approved Plan To Complete

The user explicitly approved continuing locally rather than escalating to an external research model. Complete these five steps end to end:

1. Keep Gate 1 strict. Do not weaken `all_runs_have_clean_patch_replay`; do not reclassify `invalid_submission` as passable clean replay without a new explicit artifact explaining and justifying such a policy. The default target is to make the output/patch path robust enough to satisfy the existing clean-replay gate.
2. Repair the runner/output contract path that caused `frontier-click-specialist` on `click__rbench__003` attempts 1 and 2 to fail as `search_replace_old_occurrence_mismatch`. Prefer a robust, auditable contract such as unified-diff/structured-edit parsing or exact context anchoring over broad ad hoc string matching. Ambiguous model output must produce clear machine-readable diagnostics and must never be applied unsafely.
3. Add regression tests before or alongside production fixes for the task-003-style repeated old-string ambiguity. Tests should document the intended behavior: repeated old strings cannot be silently applied, and the repaired path either yields a verifier-ready replayable patch or a precise invalid-submission diagnostic.
4. After local tests pass, run the smallest useful targeted live rerun: `frontier-click-specialist` on `click__rbench__003`, not the full Click 004-008 expansion. Reconcile ledger/provider-usage cost exactly as prior reports do. If API funds/quota/credentials are actually unavailable, mark `worker/process.md` as `blocked` with evidence; otherwise continue autonomously.
5. Produce PR-ready evidence: machine-readable result artifacts, normalized summaries if the repo pattern supports them, a Gate 1 re-decision artifact/report, and a concise experiment report explaining whether Gate 1 now passes and whether Click 004-008 expansion is justified.

Step 5 is not a stopping excuse. If steps 1-4 succeed and the report identifies a clear next local experiment step, continue executing that next step rather than blocking on documentation. Progress step by step for as long as local engineering or experiment work can safely advance the goal. Stop only for true hard blockers: API funds/quota exhaustion, missing LLM credentials, repo auth failure, or necessary user input.

## Existing Evidence To Use

- Prior follow-up report: `experiments/core_narrative/reports/2026-05-08_codex_nfl_followup_experiment_report.md`.
- Prior evidence package: `experiments/core_narrative/reports/2026-05-08_codex_nfl_followup_evidence_package.md`.
- Gate 1 stop artifact: `experiments/core_narrative/results/codex_nfl_followup_gate1_decision_20260508.json`.
- Normalized follow-up summary: `experiments/core_narrative/results/normalized/codex_nfl_followup_summary_20260508.json`.
- Prior PR #2 was merged; work from the current branch should build on `main`.

## Cost / Scope Guardrails

- Spend only what is needed for the targeted rerun. Do not run Click 004-008 unless the targeted rerun and Gate 1 re-decision explicitly justify it and the report records the decision.
- Keep raw provider responses redacted according to existing repo policy.
- Preserve the unrelated untracked file `docs/draft/barcarolle-leadership-report.md`.
- Do not read or depend on worker/reviewer CLI logs for coordination; update `worker/process.md`.

## Process File Contract

Maintain `.codex-workflows/barcarolle-nfl-output-contract-replay/worker/process.md`.

Update it before and after meaningful phases. Keep it compressed. It must include:

- current status: `working`, `blocked`, `delivered`, or `revising`;
- short summary;
- files changed or artifacts produced so far;
- verification performed or skipped;
- open questions or known risks;
- when delivered, concise handoff summary for reviewer.

The coordinator will not read CLI stdout/stderr. The process file is the only progress channel.

## Completion

When ready for review:

1. Save all intended edits or artifacts.
2. Update `worker/process.md` with `status: delivered`.
3. Include exact files changed, artifacts produced, verification, and a concise reviewer handoff.

If reviewer feedback appears later in `.codex-workflows/barcarolle-nfl-output-contract-replay/reviewer/review-to-worker.md`, revise and deliver again.
