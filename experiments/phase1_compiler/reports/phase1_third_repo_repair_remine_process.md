# Phase 1 Third Repo Repair Remine Process

Status: local repair/remine completed and verified.

Generated: 2026-05-22.

No paid LLM calls were made. No paid ACUT calls were made.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `b5e396bd52dcfb2441f1018c393b4a0566edc356`
- Python: `Python 3.9.6` via `python3`; plain `python` was not present
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Previous hardening decision: `certification_implementation_bug_found`
- Previous recommended runbook: `fix_itsdangerous_statement_template_environment_and_candidate_filter_then_remine_certify_without_paid_acut`
- Previous Itsdangerous release: `diagnostic_only`, certified count `1`
- Previous hardened Itsdangerous benchmark candidates: `0`

The old Itsdangerous artifacts contained `Repair the humanize behavior` before
repair. Preflight checks passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `63 passed`
- `uv run --project experiments/phase1_compiler pytest -q` -> `20 passed`
- Phase 1 compiler validate -> `status=valid`

No raw, workspace, external repo, venv, or cache path named by the runbook was
tracked by Git.

## Step 1 Source Adapter Repair

The repo-history adapter now generates solver statements from the candidate
`repo_id`, so Itsdangerous statements say `Repair the itsdangerous behavior`.
Commit-message fallback remains diagnostic-only and does not produce
`allowed_context_refs`.

The repaired deterministic candidate filter rejects maintenance/project churn,
project-file-heavy changes, missing behavior code, and changes above 250 lines.
Manual-review diagnostics are emitted for cross-module and docs/config touches.

Regression check:

- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools/test_repo_history_pilot.py` -> `14 passed`

## Step 2 Repair Config

Created `experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml`.
The original Itsdangerous config remains unchanged. The repair config sets
local-only claim scope, disables paid LLM/ACUT calls, requests 32 certification
attempts, and requires at least 4 certified tasks for pilot grade and 6 for
benchmark grade.

## Step 3 Re-Mine

The ignored workspace `experiments/phase0_headroom/workspaces/repo_history_pilot/itsdangerous`
was removed before mining. Repaired mining produced `6` selected candidates:

- selected candidates with both code and test files: `6`
- selected candidates missing code or tests: `0`
- maximum selected changed-line count: `91`
- selected maintenance/project-churn subjects matching the blocklist: `0`
- accepted without manual review: `1`
- manual-review-required: `5`

This is below the preferred `8` candidate target, so Itsdangerous remains
supply-limited.

## Step 4 Source Context

`gh auth status` showed an authenticated GitHub CLI session. Source-context
regeneration used PR metadata and stored no raw API responses.

Regenerated artifacts:

- statements: `6`
- reviewed non-leaky PR-context statements: `6`
- context-missing statements: `0`
- reviewed statements with `commit:` refs: `0`
- commit fallback source rows: `0`

The regenerated source context and task statements contain no
`Repair the humanize behavior` text.

## Step 5 Certification And Bounded Environment Repair

The first repaired certification run produced `1` certified task and `5`
`reference_pass` near-certified tasks. The configured command plus pytest 8, 7,
and 6 variants all had `target_reference_pass_count=0` for those five tasks.
Only sanitized return codes, durations, and tail hashes were inspected.

The hardening probe and local `pyproject.toml` inspection showed that
Itsdangerous declares `freezegun` in its test dependencies. A bounded
`repo_declared_test_extra_if_present` probe using `pytest<8`, `setuptools<81`,
and `freezegun` found:

| Task | No-op rc | Ref1 rc | Ref2 rc | No-op tail hashes | Ref tail hashes |
| --- | ---: | ---: | ---: | --- | --- |
| `itsdangerous__hist__001` | 4 | 4 | 4 | `a6fc53a5cef0/0ccfdeae4ac8` | `a6fc53a5cef0/5bd0194bfa90` |
| `itsdangerous__hist__002` | 1 | 0 | 0 | `1661fa3560ce/2ba16d644295` | `b55450c43668/e3b0c44298fc` |
| `itsdangerous__hist__003` | 1 | 0 | 0 | `e2caec848c56/54d515b7b2ab` | `de33389ada30/e3b0c44298fc` |
| `itsdangerous__hist__004` | 1 | 0 | 0 | `25f45716742b/2ba16d644295` | `01b20c961178/e3b0c44298fc` |
| `itsdangerous__hist__005` | 0 | 0 | 0 | `25b8b83a808d/2ba16d644295` | `adaa952ac538/e3b0c44298fc` |

The repair config was updated only to use that repo-declared test extra. The
rerun certified `4` tasks. Remaining near-certified tasks were one
`reference_pass` failure and one `no_op_fail` failure.

## Step 6 Release Assembly

The repaired release is local pilot-grade but not benchmark-grade:

- release status: `pilot_grade`
- certified tasks: `4`
- B_real tasks: `2`
- W_real tasks: `2`
- benchmark grade: `false`
- claim scope: `third_repo_local_repair_remine_not_predictive_validation`

The certified task and release manifest contain no stale `humanize` statement.

## Step 7 Phase 1 Hardening Overlay

Phase 1 hardening overlays were refreshed after the local repair:

- Itsdangerous source rows: `6`; benchmark-grade source rows: `2`
- Itsdangerous oracle alignment: `0` aligned, `4` manual review, `2` reject
- Itsdangerous hardened benchmark candidates: `0`
- Itsdangerous hardened manual-review tasks: `2`
- Itsdangerous hardened rejected tasks: `4`
- `statement_source_mismatch`: absent
- predictive validity: `false`

The stale `certification_implementation_bug_found` decision wording was fixed.
Current hardening decision: `replace_third_repo_before_paid_acut`.

## Step 8 Replacement Decision

Itsdangerous is a local pilot-grade candidate but not suitable for paid third-repo
ACUT smoke because hardening accepts zero benchmark-grade candidates. The
smallest next useful runbook is replacement-repo local certification.

Preferred replacement candidates from `repositories.yaml`:

- `boltons`: low external-service risk, simple Python test surface, broader
  behavior surface than Itsdangerous.
- `attrs`: high candidate-anchor estimate and low external-service risk, but a
  broader hatch/test dependency surface than `boltons`.

## Step 9 Final Decision Artifact

Wrote:

- `experiments/phase1_compiler/results/phase1_third_repo_repair_remine_decision.json`
- `experiments/phase1_compiler/reports/phase1_third_repo_repair_remine_decision.md`

Final decision: `replace_third_repo_before_paid_acut`.

## Step 10 Compiler Boundary Refresh

Ran:

- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py build-mvp --config experiments/phase1_compiler/configs/phase1_mvp.yaml`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml`

Validation returned `status=valid`.

Closeout boundary checks:

- release status: `pilot_grade`
- predictive validity established: `false`
- production ranking status: `not_produced`
- hardening sidecar status: `available_as_sidecar_evidence`
- hardening primary decision: `replace_third_repo_before_paid_acut`
- next runbook recommendation: `select_replacement_third_repo_and_locally_certify_without_paid_acut`

The compiler closeout now reuses the hardening sidecar's current next-runbook
recommendation instead of stale local-repair wording.

## Step 11 Final Verification

Final verification passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `67 passed in 1.60s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `22 passed in 0.28s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`
- `git ls-files` for raw, workspace, external repo, venv, and cache paths named
  by the runbook returned no tracked files
- `git status --short` was clean after the verification commit inputs were
  inspected; `git status --short --ignored` showed only ignored cache, venv,
  external repo, raw result, and workspace paths

No paid calls were made in this runbook.
