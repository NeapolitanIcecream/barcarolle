# Phase 1 Third Repo Repair Remine Process

Status: in progress.

Generated: 2026-05-22T03:42:45Z.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `b5e396bd52dcfb2441f1018c393b4a0566edc356`
- Git status before repair: clean
- Python: `Python 3.9.6` via `python3`; plain `python` was not present in this shell
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Paid LLM calls allowed: false
- Paid ACUT calls allowed: false

Previous hardening state matched the runbook:

- primary decision: `certification_implementation_bug_found`
- recommended next runbook: `fix_itsdangerous_statement_template_environment_and_candidate_filter_then_remine_certify_without_paid_acut`
- old Itsdangerous hardened benchmark candidates: `0`
- old Itsdangerous release status: `diagnostic_only`
- old Itsdangerous certified task count: `1`

The stale statement-template bug was observed before repair. Existing
Itsdangerous task statements, certified tasks, and near-certified tasks contained
`Repair the humanize behavior`.

Preflight checks passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `63 passed in 1.77s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `20 passed in 0.29s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

No raw result, workspace, external repo, venv, or cache paths named by the
runbook were tracked by Git.

No paid calls were made.

## Step 3 Re-Mine Candidates

Removed only the ignored workspace path
`experiments/phase0_headroom/workspaces/repo_history_pilot/itsdangerous`, then
ran:

`uv run --project experiments/phase0_headroom python experiments/phase0_headroom/tools/repo_history_pilot.py --root . --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml mine`

Repaired mining produced `6` selected candidates. This is below the runbook's
preferred `8` candidate threshold, so the third repo is supply-limited unless
later certification evidence justifies a narrow pilot.

Candidate checks:

- selected candidates with both code and test files: `6`
- selected candidates missing code or tests: `0`
- maximum selected changed-line count: `91`
- selected maintenance/project-churn subjects matching the repair blocklist: `0`
- accepted without manual review: `1`
- manual-review-required due to cross-module or docs/config touches: `5`

The regenerated supply funnel records filter status, reject reasons,
manual-review reasons, and changed-line counts for auditability.

No paid calls were made.

## Step 2 Versioned Repair Config

Created
`experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml`.
The original Itsdangerous config remains present and unchanged.

The repair config sets:

- `schema_version: barcarolle.third_repo_pilot.repair_v2.v1`
- `status: selected_for_repair_remine`
- `claim_scope: third_repo_local_repair_remine_not_predictive_validation`
- `paid_acut_calls: disabled`
- `paid_llm_calls: disabled`
- `certification_attempts: 32`
- `pilot_certified_min: 4`
- `benchmark_grade_min: 6`

The config records commit-message fallback as diagnostic-only and carries the
candidate-filter policy enforced by the repaired tool. Loading the config through
`repo_history_pilot.load_config` succeeded.

No paid calls were made.

## Step 1 Source Adapter Semantics

The Phase 0 repo-history adapter was repaired before regenerating artifacts.

- `solver_statement` uses the candidate `repo_id`; the Itsdangerous regression
  test requires `itsdangerous behavior` and excludes `humanize behavior`.
- Commit-message fallback is now diagnostic-only. It can still emit a sanitized
  commit summary and body summary, but it does not produce
  `allowed_context_refs` and cannot by itself mark a statement as `reviewed`.
- Candidate filtering now rejects deterministic maintenance and project churn:
  configured subject terms, no behavior code file, project-file-heavy changes,
  and changes above 250 added plus deleted lines.
- Cross-module changes above three modules and docs/config-touching changes are
  marked for manual review in the supply diagnostics.
- The supply funnel CSV now records filter status, reject reasons, manual-review
  reasons, and changed-line counts.

Regression check:

- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools/test_repo_history_pilot.py` -> `14 passed in 0.20s`

No paid calls were made.
