# Process

status: revising
updated: 2026-04-29T12:08:00+08:00

## Summary

Revision 2 is starting after focused re-review found one remaining related
command-contract issue: older `acut_adapter_smoke*` report/results are still
presented as current smoke evidence and still record retired ACUT IDs/default
profile values.

This revision remains no-model-call only. Do not inspect `cli.log`, start broad
ACUT execution, live ACUT model calls, execution-start preflight, or live
patch-generation attempts.

## Owned Paths

- `experiments/core_narrative/tools/barcarolle_patch_command.py`
- `experiments/core_narrative/reports/patch_command_contract.md`
- `experiments/core_narrative/results/normalized/patch_command_contract*.json`
- `experiments/core_narrative/results/raw/patch_command_contract*/**`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/review-feedback-1.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/revision-prompt-1.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/run_revision_1.sh`
- `experiments/core_narrative/reports/acut_adapter_smoke.md`
- `experiments/core_narrative/results/normalized/acut_adapter_smoke*.json`
- `experiments/core_narrative/results/raw/acut_adapter_smoke*/**`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/review-feedback-2.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/revision-prompt-2.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/run_revision_2.sh`

## Branch / Worktree

- Branch: `codex/core-exp-patch-command-contract`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-patch-command-contract`

## Files Changed Or Inspected

Changed:

- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
- `experiments/core_narrative/reports/patch_command_contract.md`
- `experiments/core_narrative/results/normalized/patch_command_contract_adapter_dry_run.json`
- `experiments/core_narrative/results/normalized/patch_command_contract_summary.json`
- `experiments/core_narrative/results/raw/patch_command_contract_adapter_dry_run/**`
- `experiments/core_narrative/results/raw/patch_command_contract_adapter_mock_probe/**`
- `experiments/core_narrative/results/raw/patch_command_contract_mock_response/**`
- `experiments/core_narrative/results/raw/patch_command_contract_unsafe_cli/**`

Inspected:

- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/review-feedback-1.md`
- `.codex-workflows/core-narrative-experiment/coordinator.md`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml`
- `experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml`
- `experiments/core_narrative/configs/acuts/frontier-click-specialist.yaml`
- `experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml`
- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/_llm_budget.py`
- `experiments/core_narrative/tools/_common.py`
- `experiments/core_narrative/tools/barcarolle_patch_command.py`
- `experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml`
- `experiments/core_narrative/tasks/click/rbench/click__rbench__001/public/statement.md`

## Current Blockers

Focused re-review requires refreshing or clearly superseding stale
`acut_adapter_smoke*` current smoke evidence before integration or
execution-start promotion.

## Checks Run

- `PYTHONPYCACHEPREFIX=/tmp/core-narrative-patch-command-pycache python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py`
- Direct command `--dry-run` with both required env vars unset and
  `cheap-click-specialist`: exit `0`, no model call.
- Direct command live-mode missing-env probe with both required env vars unset: exit `2`, `network_attempted: false`.
- Direct unsafe CLI probes: credential-like argument rejected; full URL argument rejected.
- Direct command `--mock-response` with both required env vars unset and
  `cheap-click-specialist`: exit `0`, patch applied in a synthetic `/tmp`
  workspace, no model call.
- Adapter `--dry-run` wrap with `cheap-click-specialist` and zero projected
  cost: exit `0`, zero-cost ledger append, no model call.
- Adapter no-model mock probe with `cheap-click-specialist` and zero projected
  cost: exit `0`, command artifact records `mode: mock_response` and
  `model_call_made: false`; adapter wrote a safe patch artifact and appended a
  zero-cost ledger record.
- Structured adapter evidence records active default core IDs
  `frontier-generic-swe`, `frontier-click-specialist`, `cheap-generic-swe`,
  `cheap-click-specialist`, profile `budget-constrained-2x2-pilot-v2`, split
  task limits 2 `G_score` / 3 `RBench` / 2 `RWork`, one primary attempt per
  ACUT/task, and 28 pilot primary patch-generation attempts.
- Python JSON parse checks for command result JSON, adapter result JSON,
  normalized JSON, and ledger JSONL artifacts.
- Scoped artifact scan for credential values, bearer token values, endpoint values, and full URLs: clean.
- `git diff --check` over owned paths: passed.

Live model calls: none.

## Review Command Template

```bash
python3 /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/tools/acut_patch_adapter.py \
  --workspace <prepared-task-workspace> \
  --task /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml \
  --acut /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml \
  --attempt 1 \
  --run-id <approved-run-id> \
  --artifact-dir /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/results/raw/<approved-run-id> \
  --output /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/results/raw/<approved-run-id>/adapter_result.json \
  --normalized-output /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/results/normalized/<approved-run-id>.json \
  --llm-ledger /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/results/cost_ledger.jsonl \
  --projected-cost-usd <approved-projected-cost> \
  --timeout-seconds 1200 \
  -- \
  python3 /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/tools/barcarolle_patch_command.py \
    --acut /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml
```

## Handoff

Revision 2 is running in tmux session `bcx-patch-command-contract-r2`.
Coordinator should read this `process.md` on the next heartbeat. Do not
integrate, re-run execution-start preflight, or start model calls until this
process reports `status: delivered` and a focused follow-up review passes.
