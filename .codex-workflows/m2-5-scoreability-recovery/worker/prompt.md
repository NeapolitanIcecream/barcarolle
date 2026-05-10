# Worker Task

You are the WORKER agent. Work in `/Users/chenmohan/gits/barcarolle`.

Run with autonomy. You may edit relevant files, create artifacts, and run commands or tests. Do not ask the user for confirmation unless blocked.

## Task

Implement the next Barcarolle core-narrative experiment milestones from the May 10 research report and GPT-5.5-Pro advice: M2.5 workspace-diff-v1 scoreability recovery, R0 Click release hygiene, and S1 Scorecard v1-before-predictivity.

## Work Type

experiment

## Expected Deliverable

tested tools, machine-readable experiment results, concise reports, and a worker handoff that states whether live scoreability is passed or blocked

## Requirements

- Complete the task to the standard implied by the user request and repo conventions.
- Preserve user-approved assumptions, constraints, and existing ownership boundaries.
- Avoid unrelated refactors and do not overwrite user changes.
- For implementation tasks, add or update focused tests when risk justifies it and run relevant verification.
- For experiments or research, record method, inputs, results, limitations, and reproduction steps in the handoff or target artifact.
- Keep changed artifacts internally consistent.

## Source Inputs To Read First

- `docs/research/barcarolle-research-report-2026-05-10.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0510.md`
- `docs/experiments/core-narrative-experiment-plan.md`
- Existing M2 reports under `experiments/core_narrative/reports/2026-05-09_m2_*` and `experiments/core_narrative/reports/2026-05-10_m2_*`
- Existing tools and tests in `experiments/core_narrative/tools`

## Milestone M2.5: workspace-diff-v1 Scoreability Recovery

Implement a new scoreability path whose core contract is:

> the ACUT edits an isolated prepared task workspace; the Barcarolle runner extracts `git diff --binary` from that workspace; the clean-room verifier consumes that diff through the existing replay/verification path.

Required behavior:

- Keep the fixed denominator at exactly 2 ACUT x 3 RWork smoke unless the live path is blocked:
  - ACUTs: `cheap-generic-swe`, `cheap-click-specialist`.
  - Tasks: `click__rwork__003`, `click__rwork__004`, `click__rwork__006`.
- Add focused tests before implementation for the new behavior:
  - a no-model/synthetic workspace modification becomes a non-empty candidate patch;
  - a no-op workspace modification is classified separately from infrastructure failure;
  - untracked/unsafe generated artifacts such as files under `.core_narrative` or `.git` do not become verifier-ready source patches;
  - the resulting summary carries machine-readable failure owner/class, attemptability, clean replay status, and digest fields.
- Implement the smallest compatible runner/tooling changes. Prefer a new dedicated script if that fits local patterns better than overloading `barcarolle_patch_command.py`.
- Produce JSON under `experiments/core_narrative/results/` and a concise report under `experiments/core_narrative/reports/`.
- Preserve the M2 gate semantics:
  - `patch_ready` / verifier-attemptable >= `0.70`;
  - `invalid_submission_rate` <= `0.25`;
  - clean replay disagreement == `0`.
- Run fixture/no-model/synthetic validation first. Only then run the 6 live cells if the repo's existing LLM environment and budget gates permit it. The user explicitly authorized autonomous execution, so do not ask for approval; use existing budget gate/coordinator-decision mechanisms where required.
- If live model execution is blocked by missing environment, provider failure, or quota/budget exhaustion, record that as the blocker with evidence and continue the zero-model R0/S1 work. Do not broaden live spend after a failed M2.5 gate.

## Milestone R0: Click Benchmark Release Hygiene

Turn the current Click smoke slice into an auditable mini release without claiming final benchmark authority.

Required behavior:

- Separate ACUT-visible task statements from audit/provenance material for the M2.5 RWork tasks at minimum; prefer all Click RWork/RBench tasks if the change is mechanical and safe.
- Keep existing `public/statement.md` compatibility if tools depend on it, but add a clearly named ACUT-visible statement artifact that excludes target commit URLs, target SHAs, compare links, and reference patch material.
- Add per-task or release-level machine-readable metadata for task family tags, risk/permission tags, oracle grade, leakage notes, allowed context, and release digest.
- Provide a report explaining what changed, what remains provisional, and why this reduces leakage concerns without deleting provenance.

## Milestone S1: Scorecard v1-before-predictivity

Add a Scorecard v1 artifact that is explicitly pre-predictivity and admission-safe.

Required behavior:

- Separate at least these outcome classes in aggregation: `verified_pass`, `verified_fail`, `invalid_submission`, `infra_failed`, `missing_coverage`, and `policy_invalid`.
- Add an `attemptability_score` or equivalent alongside verified correctness; an ACUT that cannot produce a verifier-attemptable patch must be visible as an admission risk.
- Record fixed denominator, score input set digest, trial policy, coverage policy, and whether G_score is unavailable rather than zero.
- Consume existing matrices plus any M2.5 result available; do not reinterpret failed scoreability cells as capability failures.
- Produce JSON and a concise report.

## Claim Boundaries

Do not claim ranking reversal, R_score > G_score predictivity, task-solving improvement, capability uplift, G0-G5 admission, license, or authorization outcome unless the new evidence actually proves it. The likely narrative is measurement recovery and evidence hygiene, not final predictivity.

## Verification Expectations

- Run targeted unit tests for any new or changed scripts.
- Run relevant existing M2/scorecard tests that cover touched behavior.
- Run the new scripts on fixture/no-model inputs and, if possible, the live 6-cell smoke.
- Include exact commands in reports and process handoff.

## Git Hygiene

- Do not revert or modify unrelated user changes, including untracked `.wrangler/` and `docs/research/barcarolle-research-report-2026-05-10.md` unless directly needed.
- Do not commit unless the coordinator later asks for PR publication.

## Process File Contract

Maintain `.codex-workflows/m2-5-scoreability-recovery/worker/process.md`.

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

If reviewer feedback appears later in `.codex-workflows/m2-5-scoreability-recovery/reviewer/review-to-worker.md`, revise and deliver again.
