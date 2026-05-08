# barcarolle-nfl-followup-experiments Work Loop Coordinator

STATUS: LOCAL_REVIEW_CLOSED
UPDATED_AT: 2026-05-08 10:42 CST

RULES:
- Do not read worker or reviewer CLI stdout/stderr logs.
- Use `worker/process.md` and `reviewer/process.md` as progress sources.
- Worker tmux session: `barcarolle-nfl-followup-experiments-worker`.
- Reviewer tmux session: `barcarolle-nfl-followup-experiments-reviewer` once needed.
- Requested Codex CLI configuration: `gpt-5.5`, `model_reasoning_effort=xhigh`, YOLO mode.

TASK:
- Work type: experiment
- Statement: Run the next Barcarolle Codex NFL follow-up experiments: fill frontier-click-specialist attempt 1 on Click 001-003, run attempt 2 for the four-ACUT 2x2 on Click 001-003, gate on stability, then expand to Click 004-008 when justified; produce an experiment report and PR-ready evidence.
- Deliverable: Experiment artifacts, normalized summaries, evidence package/report, local review closure, and a PR-ready branch.
- Review focus: Check that the paid live experiment plan was executed or defensibly gated, results are reproducible, cost accounting is accurate, and the report supports the NFL story without overclaiming.

CURRENT:
- Worker prompt: `.codex-workflows/barcarolle-nfl-followup-experiments/worker/prompt.md`
- Worker process: `.codex-workflows/barcarolle-nfl-followup-experiments/worker/process.md`
- Worker launcher: `.codex-workflows/barcarolle-nfl-followup-experiments/worker/run_worker.sh`
- Worker reported `status: delivered`.
- Reviewer launched in tmux session `barcarolle-nfl-followup-experiments-reviewer`.
- Reviewer reported `issues_found`.
- Revision files:
  - `worker/review-feedback-1.md`
  - `worker/revision-prompt-1.md`
  - `worker/run_worker_revision_1.sh`
- Worker revision 1 reported `status: delivered`.
- Reviewer recheck files:
  - `reviewer/recheck-prompt-1.md`
  - `reviewer/run_recheck_1.sh`
- Reviewer recheck 1 reported `no_issues`.

NEXT:
- Commit and push PR-scope experiment artifacts, create or update a ready PR, then continue cloud Codex/CI review loop.
- Do not read worker or reviewer CLI logs unless the user explicitly asks for debugging.
