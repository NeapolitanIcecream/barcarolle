# m2-5-scoreability-recovery Work Loop Coordinator

STATUS: LOCAL_REVIEW_CLOSED
UPDATED_AT: 2026-05-10 18:49 CST

RULES:
- Do not read worker or reviewer CLI stdout/stderr logs.
- Use `worker/process.md` and `reviewer/process.md` as progress sources.
- Worker tmux session: `m2-5-scoreability-recovery-worker`.
- Reviewer tmux session: `m2-5-scoreability-recovery-reviewer` once needed.
- Requested Codex CLI configuration: `gpt-5.5`, `model_reasoning_effort=xhigh`, YOLO mode.

TASK:
- Work type: experiment
- Statement: Implement the next Barcarolle core-narrative experiment milestones from the May 10 research report and GPT-5.5-Pro advice: M2.5 workspace-diff-v1 scoreability recovery, R0 Click release hygiene, and S1 Scorecard v1-before-predictivity.
- Deliverable: tested tools, machine-readable experiment results, concise reports, and a worker handoff that states whether live scoreability is passed or blocked
- Review focus: milestone completeness, evidence hygiene, test coverage, reproducibility, truthful claims, and preservation of unrelated changes

CURRENT:
- Worker prompt: `.codex-workflows/m2-5-scoreability-recovery/worker/prompt.md`
- Worker process: `.codex-workflows/m2-5-scoreability-recovery/worker/process.md`
- Worker launcher: `.codex-workflows/m2-5-scoreability-recovery/worker/run_worker.sh`
- Reviewer starts only after worker first reports `status: delivered`.

MILESTONES:
- M2.5 `workspace-diff-v1` scoreability recovery on fixed 2 ACUT x 3 RWork smoke, including no-model/fixture validation and live run when env/budget gates permit.
- R0 Click mini-release hygiene with ACUT-visible statements separated from provenance and leakage notes.
- S1 Scorecard v1-before-predictivity with fixed denominator, digests, trial policy, attemptability, and distinct outcome classes.

CLAIM BOUNDARY:
- This workflow must not claim ranking reversal, R_score/G_score predictivity, task-solving uplift, G0-G5 admission, license, or authorization unless new evidence actually proves it.

NEXT:
- Read worker/process.md on the next heartbeat.
- If worker reports `status: delivered`, start reviewer.
- If worker reports `status: blocked`, classify blocker and decide whether zero-model milestones can continue.
- Keep a compact status signature on each heartbeat: worker status/mtime, reviewer status/mtime, tmux session state, branch, latest commit, PR state if any, and CI/review state if any.

STATUS_SIGNATURE:
- 2026-05-10 17:29 CST: branch `codex/m2-5-scoreability-recovery`; worker session `m2-5-scoreability-recovery-worker` exists; worker/process.md status `working`; reviewer not started; PR not created; CI/review not applicable.
- 2026-05-10 17:38 CST: branch `codex/m2-5-scoreability-recovery`; HEAD `ae055f7`; worker session `m2-5-scoreability-recovery-worker` exists; worker/process.md status `working`, mtime `2026-05-10 17:29:38 CST`, content updated_at `2026-05-10 17:40 CST`; reviewer/process.md status `blocked` waiting for worker, mtime `2026-05-10 17:26:15 CST`; untracked work artifacts observed for M2.5 tool/tests plus pre-existing `.wrangler/` and research report; PR not created; CI/review not applicable.
- 2026-05-10 17:48 CST: branch `codex/m2-5-scoreability-recovery`; HEAD `ae055f7`; worker session `m2-5-scoreability-recovery-worker` exists; worker/process.md still `working`, mtime `2026-05-10 17:29:38 CST`, content updated_at `2026-05-10 17:40 CST`; reviewer/process.md `blocked` waiting for worker; git status shows active worker artifacts for M2.5 synthetic/noop/live partial outputs, R0 release hygiene task metadata/statements, S1 scorecard tool/tests, and one cost ledger modification; PR not created; CI/review not applicable.
- 2026-05-10 17:58 CST: branch `codex/m2-5-scoreability-recovery`; HEAD `ae055f7`; worker session `m2-5-scoreability-recovery-worker` still exists; worker/process.md remains `working` with mtime `2026-05-10 17:29:38 CST`, but M2.5 live artifacts changed as recently as `2026-05-10 17:57:06 CST`; live raw dirs observed `4`, normalized live JSON files observed `3`; reviewer/process.md still `blocked` waiting for delivery; PR not created; CI/review not applicable.
- 2026-05-10 18:08 CST: branch `codex/m2-5-scoreability-recovery`; HEAD `ae055f7`; worker session `m2-5-scoreability-recovery-worker` still exists; worker/process.md remains `working`, mtime `2026-05-10 17:29:38 CST`; M2.5 live raw dirs observed `5`, normalized live JSON files observed `4`, latest raw dir mtime `2026-05-10 18:00:23 CST`; reviewer/process.md still `blocked` waiting for worker delivery; PR not created; CI/review not applicable.
- 2026-05-10 18:18 CST: branch `codex/m2-5-scoreability-recovery`; HEAD `ae055f7`; worker/process.md status `delivered`, mtime `2026-05-10 18:18:03 CST`; worker reports M2.5 live completed and failed scoreability gate with fixed denominator `6`, attemptability `0.666667`, invalid submission rate `1.0`, clean replay disagreements `4`; reviewer/process.md still old `blocked` before start; started reviewer tmux session `m2-5-scoreability-recovery-reviewer`; worker tmux session still listed; PR not created; CI/review not applicable.
- 2026-05-10 18:29 CST: branch `codex/m2-5-scoreability-recovery`; HEAD `ae055f7`; reviewer/process.md status `delivered`, mtime `2026-05-10 18:23:37 CST`; reviewer found `issues_found` with 2 closure issues: M2.5 normalized metadata consistency and exact reproduction commands; copied handoff to `worker/review-feedback-1.md`; created executable `worker/run_worker_revision_1.sh` and started tmux session `m2-5-scoreability-recovery-worker`; PR not created; CI/review not applicable.
- 2026-05-10 18:38 CST: branch `codex/m2-5-scoreability-recovery`; HEAD `ae055f7`; worker/process.md status `delivered`, mtime `2026-05-10 18:37:11 CST`; worker Revision 1 reports both reviewer findings fixed and no new live adapter/model calls; old reviewer/process.md still `delivered` with issues_found; created executable `reviewer/run_recheck_1.sh` and started tmux session `m2-5-scoreability-recovery-reviewer`; unrelated active tmux session `fix-migration-review-findings-recheck-1` observed; PR not created; CI/review not applicable.
- 2026-05-10 18:49 CST: branch `codex/m2-5-scoreability-recovery`; HEAD `ae055f7`; worker/process.md status `delivered`, mtime `2026-05-10 18:37:11 CST`; reviewer/process.md status `delivered`, mtime `2026-05-10 18:41:32 CST`; reviewer handoff status `no_issues`; coordinator verification passed: focused M2.5/R0/S1 unittest, adjacent M2/scorecard/run_task/prepare/acut/unsafe unittest, `py_compile`, and `git diff --check`; raw live artifacts checked for file-size risk with no files over 10 MB; preparing branch stage/commit/push/PR; CI/review not applicable until PR exists.

LOCAL_VERIFICATION:
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/core_narrative/tools python3 -B -m unittest experiments.core_narrative.tools.test_m2_5_workspace_diff_runner experiments.core_narrative.tools.test_click_r0_release_hygiene experiments.core_narrative.tools.test_scorecard_v1_before_predictivity`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/core_narrative/tools python3 -B -m unittest experiments.core_narrative.tools.test_m2_scoreability_summary experiments.core_narrative.tools.test_scorecard_v0_from_existing_matrices experiments.core_narrative.tools.test_run_task experiments.core_narrative.tools.test_prepare_workspace experiments.core_narrative.tools.test_acut_patch_adapter experiments.core_narrative.tools.test_m2_unsafe_artifact_repair`
- PASS: `python3 -m py_compile experiments/core_narrative/tools/m2_5_workspace_diff_runner.py experiments/core_narrative/tools/test_m2_5_workspace_diff_runner.py experiments/core_narrative/tools/click_r0_release_hygiene.py experiments/core_narrative/tools/scorecard_v1_before_predictivity.py`
- PASS: `git diff --check`
