# Worker Task

You are the WORKER agent for the Barcarolle follow-up NFL experiment. Work in `/Users/chenmohan/gits/barcarolle` on branch `codex/nfl-followup-experiments`.

Run with high autonomy. You may edit relevant experiment configs, tooling, result artifacts, reports, and workflow files. Do not ask the user for confirmation unless blocked by missing credentials, API quota/funds, repository auth, or a truly ambiguous destructive action. Do not read or depend on coordinator CLI logs.

## Goal

Complete the next paid live experiment sequence that follows the merged Codex NFL evidence PR:

1. Fill the missing team: run `frontier-click-specialist` on `click__rbench__001`, `click__rbench__002`, and `click__rbench__003` for attempt 1.
2. Run a full four-ACUT attempt 2 repeat on the same three tasks:
   - `cheap-generic-swe`
   - `frontier-generic-swe`
   - `cheap-click-specialist`
   - `frontier-click-specialist`
3. Apply the existing decision gates. If the gate passes, expand to Click `004`-`008` across the same four ACUTs. If the gate fails, do not spend the expansion calls; write the stop reason and best-effort report.
4. Produce a clear experiment report that explains what happened, what it means for the NFL-style Barcarolle story, and what should happen next.

The priority is runnable, auditable experimental evidence, not preserving old facilities for their own sake. If a small facility issue blocks the run, fix it with focused tests and keep going. The explicit hard blockers are API funds/quota exhaustion, missing required LLM credentials, or GitHub/repository auth failures.

## Context To Read First

Read only what you need, but start with:

- `experiments/core_narrative/reports/2026-05-08_codex_nfl_evidence_package.md`
- `experiments/core_narrative/reports/2026-05-08_codex_nfl_experiment_report.md`
- `experiments/core_narrative/reports/2026-05-08_gpt55pro_next_experiment_advice.md`
- `experiments/core_narrative/reports/next_experiment_decision_gates.md`
- `experiments/core_narrative/tools/codex_nfl_experiment_runner.py`
- `experiments/core_narrative/tools/summarize_results.py`
- `experiments/core_narrative/results/normalized/codex_nfl_live_summary_20260507.json`

Use existing repo patterns, run IDs, summaries, and cost accounting. Keep artifacts deterministic and named with `20260508` where appropriate.

## Required Execution Shape

Prefer the existing batch runner and live mode unless you find a concrete reason to adjust:

- Step 2 output target suggestion: `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_20260508.json`
- Step 3 output target suggestion: `experiments/core_narrative/results/codex_nfl_live_2x2_attempt2_20260508.json`
- Step 4 output target suggestion, only if gates pass: `experiments/core_narrative/results/codex_nfl_live_click_004_008_20260508.json`
- Normalized summary target suggestion: `experiments/core_narrative/results/normalized/codex_nfl_followup_summary_20260508.json`
- Final report target suggestion: `experiments/core_narrative/reports/2026-05-08_codex_nfl_followup_experiment_report.md`
- Evidence package or PR-ready summary target suggestion: `experiments/core_narrative/reports/2026-05-08_codex_nfl_followup_evidence_package.md`

Before spending live calls:

- Confirm the runner can load manifests and the selected tasks/ACUTs exist.
- Check budget/cost gate behavior and current ledger state.
- Run a no-model smoke or narrowly scoped unit tests if you change any runner/tooling.

During live calls:

- Preserve raw and normalized artifacts according to existing conventions.
- Do not redact away provider-reported usage/cost metadata needed for accounting.
- If a run fails, classify it clearly as model/task failure versus infra failure.
- If a live call is blocked by quota/funds/credentials, stop spending attempts and mark `worker/process.md` as `blocked` with concrete evidence.

After live calls:

- Reconcile and summarize cost: ledger estimated cost, provider-reported usage cost, observed actual/provider cost status, and any unknown billed-cost caveat.
- Produce a final table covering the old baseline plus follow-up runs, including task, ACUT, attempt, status, scoreable, pass/fail/infra, and key failure class.
- Explain whether the 2x2 is now complete, whether attempt 2 confirms stability, whether the expansion gate passed, and whether Click 004-008 was run.
- Explain how the evidence supports or weakens the NFL story line. Avoid overclaiming from small samples.

## If You Need To Fix Facilities

Make focused changes only. Add or update regression tests when changing behavior. Run relevant verification, normally:

- `python3 -m py_compile` for changed Python files.
- Focused `python3 -m unittest ...` for changed tool tests.
- `git diff --check -- . ':(exclude)experiments/core_narrative/results/raw/**'`
- JSON/YAML parse checks for new summary artifacts when practical.

Do not rewrite unrelated tools, reports, or workflow history unless necessary to complete this run.

## Process File Contract

Maintain `.codex-workflows/barcarolle-nfl-followup-experiments/worker/process.md`.

Update it before and after meaningful phases. Keep it compressed. It must include:

- current status: `working`, `blocked`, `delivered`, or `revising`;
- short summary;
- files changed or artifacts produced so far;
- live calls started/completed and cost status;
- verification performed or skipped;
- open questions or known risks;
- when delivered, concise handoff summary for reviewer.

The supervisor will not read CLI stdout/stderr. `process.md` is the progress channel.

## Completion

When ready for review:

1. Save all intended edits and artifacts.
2. Ensure the branch is PR-ready and the report is complete.
3. Update `worker/process.md` with `status: delivered`.
4. Include exact files changed, artifacts produced, verification, cost summary, and a concise reviewer handoff.

If reviewer feedback appears later in `.codex-workflows/barcarolle-nfl-followup-experiments/reviewer/review-to-worker.md`, revise and deliver again.
