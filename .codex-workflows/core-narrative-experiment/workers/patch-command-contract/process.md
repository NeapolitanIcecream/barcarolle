# Process

status: delivered
updated: 2026-04-29T12:20:00+08:00

## Summary

Revision 2 refreshed the stale `acut_adapter_smoke*` current evidence in place
for the active 2x2 pilot, and validation passed. Current adapter smoke
report/results now use the active `cheap-click-specialist` manifest and record profile
`budget-constrained-2x2-pilot-v2`, active core IDs, 2 `G_score` / 3 `RBench` /
2 `RWork`, one primary attempt per ACUT/task, and 28 pilot primary attempts.

No broad ACUT execution, execution-start preflight, live ACUT model call, or
live patch-generation attempt was started. No `cli.log` file was inspected.

The coordinator resolved the Git metadata commit blocker after the worker wrote
the validated handoff.

## Owned Paths

- `experiments/core_narrative/reports/acut_adapter_smoke.md`
- `experiments/core_narrative/results/normalized/acut_adapter_smoke*.json`
- `experiments/core_narrative/results/raw/acut_adapter_smoke*/**`
- existing patch-command report/results if needed for supersession
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/**`

## Branch / Worktree

- Branch: `codex/core-exp-patch-command-contract`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-patch-command-contract`

## Files Changed

- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/prompt.md`
- `experiments/core_narrative/reports/acut_adapter_smoke.md`
- `experiments/core_narrative/results/normalized/acut_adapter_smoke_dry_run.json`
- `experiments/core_narrative/results/normalized/acut_adapter_smoke_missing_env.json`
- `experiments/core_narrative/results/normalized/acut_adapter_smoke_summary.json`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/adapter_result.json`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/cost_ledger.jsonl`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_missing_env/adapter_result.json`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_missing_env/cost_ledger.jsonl`

## Files Inspected

- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/review-feedback-2.md`
- `/Users/chenmohan/gits/barcarolle-wt-patch-command-r1-reviewer/.codex-workflows/core-narrative-experiment/reviews/patch-command-r1-review.md`
- `.codex-workflows/core-narrative-experiment/coordinator.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/prompt.md`
- `experiments/core_narrative/reports/acut_adapter_smoke.md`
- `experiments/core_narrative/reports/patch_command_contract.md`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml`
- `experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml`
- `experiments/core_narrative/configs/acuts/frontier-click-specialist.yaml`
- `experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml`
- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/_llm_budget.py`
- `experiments/core_narrative/tools/_common.py`
- `experiments/core_narrative/tools/barcarolle_patch_command.py`

## Checks Run

- `PYTHONPYCACHEPREFIX=/tmp/core-narrative-acut-adapter-smoke-r2-pycache python3 -m py_compile experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/_llm_budget.py experiments/core_narrative/tools/run_task.py experiments/core_narrative/tools/barcarolle_patch_command.py`
- Adapter `--dry-run` smoke through `experiments/core_narrative/tools/acut_patch_adapter.py` using active `cheap-click-specialist`, zero projected cost, and no model call: exit `0`.
- Adapter missing-env gate probe through `experiments/core_narrative/tools/acut_patch_adapter.py` using active `cheap-click-specialist` and wrapped `barcarolle_patch_command.py --dry-run`: exit `2`, blocked before command execution, no model call.
- Unsafe CLI probes through `experiments/core_narrative/tools/acut_patch_adapter.py`: credential-like command argument rejected; full-URL command argument rejected; neither probe ran a patch-generation command.
- Python JSON parse checks for both raw adapter result JSON files, both normalized run-result JSON files, and `acut_adapter_smoke_summary.json`.
- Python JSONL parse checks for both refreshed smoke ledger files.
- Structured invariant check passed for refreshed adapter smoke evidence: active 2x2 core IDs, profile `budget-constrained-2x2-pilot-v2`, 2/3/2 pilot task limits, one primary attempt per ACUT/task, and 28 pilot primary attempts.
- Scoped retired-ID scan over current `acut_adapter_smoke*` report/results found no pre-redesign ACUT IDs or pre-redesign profile ID.
- Broader retired-ID scan found only explicitly historical/superseded context in workflow prompts/feedback and ACUT redesign notes, not current smoke evidence, default core IDs, executable templates, or new-execution ACUT references.
- Scoped scan over current `acut_adapter_smoke*` report/results found no credential values, bearer values, provider-token values, resolved env assignments, or full URLs.
- `git diff --check` over owned paths passed.

Live model calls: none.

## Current Adapter Smoke Evidence

- `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/adapter_result.json`
  - `acut_id`: `cheap-click-specialist`
  - `status`: `dry_run_completed`
  - `model_call_made`: `false`
  - profile: `budget-constrained-2x2-pilot-v2`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_missing_env/adapter_result.json`
  - `acut_id`: `cheap-click-specialist`
  - `status`: `gate_blocked`
  - `model_call_made`: `false`
  - blocker: `missing_required_llm_environment`
- `experiments/core_narrative/results/normalized/acut_adapter_smoke_summary.json`
  - records the active 2x2 profile and no-model/no-execution status.

## Handoff

Revision 2 content is delivered and ready for focused follow-up review. The
refreshed adapter smoke evidence no longer presents pre-redesign IDs or the
pre-redesign default profile as current evidence. Do not integrate, re-run
execution-start preflight, or start model calls until focused follow-up review
passes.
