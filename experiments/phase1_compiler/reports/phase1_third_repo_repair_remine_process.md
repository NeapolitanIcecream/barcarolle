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

## Step 5 Re-Certification

Ran:

`uv run --project experiments/phase0_headroom python experiments/phase0_headroom/tools/repo_history_pilot.py --root . --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml certify`

Certification result:

- certified tasks: `1`
- near/rejected tasks: `5`
- dominant first failing gate: `reference_pass`
- commit-fallback-only certified tasks: `0`

Certification funnel:

| Task | Status | First failing gate |
| --- | --- | --- |
| `itsdangerous__hist__001` | `near_certified` | `reference_pass` |
| `itsdangerous__hist__002` | `near_certified` | `reference_pass` |
| `itsdangerous__hist__003` | `near_certified` | `reference_pass` |
| `itsdangerous__hist__004` | `near_certified` | `reference_pass` |
| `itsdangerous__hist__005` | `near_certified` | `reference_pass` |
| `itsdangerous__hist__006` | `certified` |  |

Because reference failures dominated, a bounded environment variant probe was
run across the configured command and pytest 8, 7, and 6 variants. The probe
recorded only labels, return codes, durations, and tail hashes; no full command
output was stored.

| Variant | Task | No-op rc | Ref rc | No-op s | Ref s | No-op tail hashes | Ref tail hashes |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `configured_command` | `itsdangerous__hist__001` | 4 | 4 | 0.151 | 0.119 | `a6fc53a5cef0/aefaa0bb4fe3` | `a6fc53a5cef0/5bd0194bfa90` |
| `configured_command` | `itsdangerous__hist__002` | 2 | 2 | 0.163 | 0.159 | `c03b6a2d5167/e3b0c44298fc` | `1a03c63ceeb1/e3b0c44298fc` |
| `configured_command` | `itsdangerous__hist__003` | 2 | 2 | 0.173 | 0.180 | `27ad2064b1f1/e3b0c44298fc` | `b6e9df0ab2f2/e3b0c44298fc` |
| `configured_command` | `itsdangerous__hist__004` | 2 | 2 | 0.179 | 0.171 | `21e02a40d023/e3b0c44298fc` | `7fcff0ecaa43/e3b0c44298fc` |
| `configured_command` | `itsdangerous__hist__005` | 2 | 2 | 0.169 | 0.168 | `bc3747d579b7/e3b0c44298fc` | `ed95a715ce66/e3b0c44298fc` |
| `pytest_8_with_editable` | `itsdangerous__hist__001` | 4 | 4 | 0.270 | 0.261 | `a6fc53a5cef0/5681e2bb600d` | `a6fc53a5cef0/b0ccebbfcf2d` |
| `pytest_8_with_editable` | `itsdangerous__hist__002` | 2 | 2 | 0.297 | 0.302 | `c03b6a2d5167/ee6c06acf2a7` | `1a03c63ceeb1/d1e09688ba0e` |
| `pytest_8_with_editable` | `itsdangerous__hist__003` | 2 | 2 | 0.312 | 0.287 | `27ad2064b1f1/d1e09688ba0e` | `3e279d7def87/05dbee2e31f4` |
| `pytest_8_with_editable` | `itsdangerous__hist__004` | 2 | 2 | 0.291 | 0.294 | `feb3ad3acefb/05dbee2e31f4` | `7fcff0ecaa43/d1e09688ba0e` |
| `pytest_8_with_editable` | `itsdangerous__hist__005` | 2 | 2 | 0.296 | 0.319 | `fa3ae9b2d4f4/05dbee2e31f4` | `f78b4853829c/05dbee2e31f4` |
| `pytest_7_with_editable` | `itsdangerous__hist__001` | 4 | 4 | 0.217 | 0.219 | `a6fc53a5cef0/eceb16aa97e4` | `a6fc53a5cef0/a38c6e44cf36` |
| `pytest_7_with_editable` | `itsdangerous__hist__002` | 2 | 2 | 0.243 | 0.241 | `fa47cf73e8a2/c9dda898b814` | `87d08da80c14/c9dda898b814` |
| `pytest_7_with_editable` | `itsdangerous__hist__003` | 2 | 2 | 0.240 | 0.235 | `68e08319cdd3/e69aadcd12b9` | `ce25c0b7bba2/e69aadcd12b9` |
| `pytest_7_with_editable` | `itsdangerous__hist__004` | 2 | 2 | 0.240 | 0.253 | `17838d07178d/27450887330a` | `e8f48099cc87/e69aadcd12b9` |
| `pytest_7_with_editable` | `itsdangerous__hist__005` | 2 | 2 | 0.238 | 0.246 | `023fdc34a4df/e69aadcd12b9` | `b885f0712b34/e69aadcd12b9` |
| `pytest_6_with_editable` | `itsdangerous__hist__001` | 4 | 4 | 0.377 | 0.237 | `a6fc53a5cef0/47d9c5239f63` | `a6fc53a5cef0/cdca72c9301c` |
| `pytest_6_with_editable` | `itsdangerous__hist__002` | 2 | 2 | 0.247 | 0.245 | `fa47cf73e8a2/155c63192931` | `87d08da80c14/54d515b7b2ab` |
| `pytest_6_with_editable` | `itsdangerous__hist__003` | 2 | 2 | 0.243 | 0.246 | `68e08319cdd3/78574b5524a1` | `ce25c0b7bba2/78574b5524a1` |
| `pytest_6_with_editable` | `itsdangerous__hist__004` | 2 | 2 | 0.253 | 0.272 | `17838d07178d/54d515b7b2ab` | `87cb49de122c/2ba16d644295` |
| `pytest_6_with_editable` | `itsdangerous__hist__005` | 2 | 2 | 0.284 | 0.259 | `023fdc34a4df/78574b5524a1` | `530bafd547d6/2ba16d644295` |

All bounded variants had `target_reference_pass_count=0` for the five
reference-failing tasks while preserving no-op failures. No config variant was
adopted. Further repair would require broader environment archaeology, outside
this runbook's bounded probe.

No paid calls were made.

## Step 4 Source Context And Statements

`gh auth status` showed an authenticated GitHub CLI session, so the source
context regeneration used GitHub PR metadata. Raw API responses were not stored.

Ran:

`uv run --project experiments/phase0_headroom python experiments/phase0_headroom/tools/repo_history_pilot.py --root . --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml source-context`

Regenerated source-context checks:

- statements: `6`
- reviewed non-leaky PR-context statements: `6`
- context-missing statements: `0`
- reviewed statements with `commit:` refs: `0`
- source context rows: `6`
- PR rows: `6`
- commit fallback rows: `0`

The stale template bug is absent from regenerated source context and statements:
no regenerated Itsdangerous statement contains `Repair the humanize behavior`;
all regenerated statements contain `Repair the itsdangerous behavior`.

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
