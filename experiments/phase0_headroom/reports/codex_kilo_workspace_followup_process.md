# Codex Kilo Workspace Follow-Up Process

## 2026-05-21

- Starting point: branch `codex/restart-benchmark-compiler`, after completed
  Codex/Kilo matrix and runbook commit `fcdb28fe`.
- Step 0 preflight passed: endpoint env was present, completed matrix artifacts
  existed, `git diff --check` passed, Phase 0 tools tests passed, Phase 1
  compiler tests passed, and only ignored raw/workspace/cache/venv artifacts
  appeared under ignored status.
- Commit `758fbef0` added the local Kilo completion and policy diagnosis.
- Commit `d1467049` clarified solver-visible editable/non-editable path policy
  and preserved the benchmark-side test-edit rejection gate.
- Commit `83f6a67d` added Kilo `strict-final` completion mode, bounded task-id
  runner selection, timeout override support, and the follow-up matrix config.

## Step 1 Diagnosis

- Kilo ACUT harness errors from the completed matrix: `6`.
- Kilo classification: all `6/6` were
  `adapter_timeout_nonempty_diff_nonexit`.
- Policy violations from the completed matrix: `5`.
- Policy rejection classes: `3` test edits and `2` out-of-scope edits.
- Statement-policy finding: old solver-visible statements had no explicit
  editable/non-editable sections; Click statements could mention
  `tests/test_*.py` regression coverage while policy rejected test edits.

## Step 2 Policy Repair

Solver-visible statements now render:

- `Editable Paths`: only implementation files from `allowed_code_paths` or
  `prompt_code_files`.
- `Non-Editable Paths`: a direct prohibition on tests, hidden verifier files,
  generated caches, lockfiles, and files outside editable paths.
- Test/regression scope lines that were previously under `Scope Boundary` are
  moved to a verifier-only non-editable note.

The policy gate remains unchanged: `tests/**` edits are still rejected as
`submission_edited_tests`, and out-of-scope edits are still rejected as
`submission_edited_out_of_scope_paths`.

## Step 3 Kilo Completion Probe

Probe command used `kilo_workspace` with `strict-final`, timeout override
`300`, result prefix `kilo_completion_probe`, and these task ids:

- `toolz__hist__002`
- `toolz__hist__001`
- `click__rbench__004`

Results:

- Non-timeout outcomes: `3/3`.
- Scoreable outcomes: `3/3`.
- Terminal statuses: `verified_pass=2`, `verified_fail=1`.
- Captured diffs: all `3/3`.
- Estimated cost: `USD 1.50`.
- Usage observed: `false`; conservative per-cell estimate retained.
- Hidden verifier material: no tracked hidden verifier file was present in the
  checked solver workspaces.

Step 3 continuation gate passed. The next runbook step is the 6-cell policy
smoke.

## Step 4 Policy Smoke

Smoke command used result prefix `codex_kilo_workspace_followup_smoke` and task
ids:

- `click__rbench__002`
- `click__rbench__003`
- `toolz__hist__010`

Results:

- Scheduled cells: `6`.
- Scoreable outcomes: `6/6`.
- Terminal statuses: `verified_pass=2`, `verified_fail=4`.
- Codex: `3/3` scoreable.
- Kilo: `3/3` scoreable and `3/3` non-timeout.
- Click test-edit policy violations: `0/4`.
- Captured diffs stayed inside editable paths for all six solver workspaces.
- Estimated smoke cost: `USD 3.00`.

Step 5 continuation gates passed. The repaired matrix is projected at
`20 * USD 0.50 = USD 10.00`; it will be run as two sequential `USD 5.00`
batches so no single paid batch exceeds the `USD 8` stop-before-batch rule.

## Step 6 Repaired Matrix

The repaired 20-cell matrix used result prefix `codex_kilo_workspace_followup`
and was run in two sequential paid batches:

- Codex batch: `10` cells, projected `USD 5.00`.
- Kilo batch: `10` cells, projected `USD 5.00`.

Results:

- Scheduled cells: `20`.
- Scoreable cells: `19/20`.
- Terminal statuses: `verified_pass=7`, `verified_fail=12`,
  `policy_violation=1`.
- Codex scoreable cells: `10/10`.
- Kilo scoreable cells: `9/10`.
- `G_mini` scoreable cells: `8/8`.
- Kilo timeout rows: `0/10`.
- Test-edit policy violations: `0`.
- Remaining policy violation: Kilo edited out-of-scope exports for
  `toolz__hist__010` (`toolz/__init__.py`, `toolz/curried/__init__.py`).
- Estimated repaired matrix cost: `USD 10.00`.

Step 6 thresholds passed. MAE, RMSE, Brier, and ordering accuracy remain
`not_applicable_underpowered`.

## Step 7 Phase 1 Refresh

The Phase 1 compiler was refreshed from:

```text
experiments/phase0_headroom/results/codex_kilo_workspace_followup_score_table.csv
```

Outputs:

- `experiments/phase1_compiler/results/toolz_phase1_draft_release.json`
- `experiments/phase1_compiler/results/toolz_phase1_weighted_score.json`

The weighted summary identifies both ACUTs:

- `codex_workspace_gpt_5_4_mini`
- `kilo_workspace_gpt_5_4_mini`

It imports `20` cells, treats `19` as compatible, keeps the one policy
violation incompatible, and preserves overall `insufficient_evidence` instead
of introducing a predictive-validity claim.
