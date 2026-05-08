# barcarolle-nfl-followup-experiments Work Loop Coordinator

STATUS: PR_READY_WAITING_CLOUD_REVIEW
UPDATED_AT: 2026-05-08 10:45 CST
PR: https://github.com/NeapolitanIcecream/barcarolle/pull/2

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
- Committed local review closure and experiment artifacts as `7393019 Run Codex NFL follow-up experiments`.
- Pushed branch `codex/nfl-followup-experiments`.
- Created ready PR #2 using `experiments/core_narrative/reports/2026-05-08_codex_nfl_followup_evidence_package.md` as PR body.
- Initial PR state: open, not draft, mergeable, merge state clean, no checks, no review threads yet.

NEXT:
- Wait for cloud Codex review and CI/check state on PR #2. Fix valid findings or merge only after review/checks are clean.
- Do not read worker or reviewer CLI logs unless the user explicitly asks for debugging.
