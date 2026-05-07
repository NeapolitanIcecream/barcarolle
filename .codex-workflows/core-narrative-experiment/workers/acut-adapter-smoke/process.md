# Process

status: delivered
updated: 2026-04-29T10:06:30+08:00

## Summary

Focused ACUT adapter smoke worker is active. Scope: implement and no-model-test the adapter command path needed before any live ACUT model call, ensuring every future patch-generation attempt uses only the experiment LLM env vars, passes the budget gate, and appends a cost ledger record.

## Owned Paths

- `experiments/core_narrative/tools/**` limited to ACUT adapter or run orchestration additions
- `experiments/core_narrative/reports/acut_adapter_smoke.md`
- `experiments/core_narrative/results/normalized/acut_adapter_smoke*.json`
- `experiments/core_narrative/results/raw/acut_adapter_smoke*/**`
- `.codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke/process.md`

## Branch / Worktree

- Branch: `codex/core-exp-acut-adapter-smoke`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-acut-adapter-smoke`

## Files Changed Or Inspected

Changed:

- `.codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke/process.md`
- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/reports/acut_adapter_smoke.md`
- `experiments/core_narrative/results/normalized/acut_adapter_smoke_dry_run.json`
- `experiments/core_narrative/results/normalized/acut_adapter_smoke_missing_env.json`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/adapter.stdout.txt`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/adapter.stderr.txt`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/adapter_result.json`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/cost_ledger.jsonl`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/submission.patch`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_missing_env/adapter.stdout.txt`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_missing_env/adapter.stderr.txt`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_missing_env/adapter_result.json`
- `experiments/core_narrative/results/raw/acut_adapter_smoke_missing_env/cost_ledger.jsonl`

Inspected:

- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/coordinator.md`
- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/workers/task-manifests/process.md`
- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/workers/task-manifests-reviewer/process.md`
- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/workers/execution-planner/process.md`
- `/Users/chenmohan/.codex/skills/tests-as-specs/SKILL.md`
- `/Users/chenmohan/.codex/skills/observability/SKILL.md`
- `experiments/core_narrative/tools/_llm_budget.py`
- `experiments/core_narrative/tools/_common.py`
- `experiments/core_narrative/tools/run_task.py`
- `experiments/core_narrative/tools/append_cost_record.py`
- `experiments/core_narrative/tools/llm_budget_gate.py`
- `experiments/core_narrative/tools/apply_and_verify.py`
- `experiments/core_narrative/configs/llm_access.yaml`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `experiments/core_narrative/schemas/run_result.schema.json`
- `experiments/core_narrative/results/normalized/no-op-smoke__click__rbench__001.json`
- `experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml`

## Current Blockers

None.

## Checks Run

- Syntax compile with `PYTHONPYCACHEPREFIX=/tmp/core-narrative-acut-adapter-pycache python3 -m py_compile` for the touched/new adapter and existing budget/ledger tools: passed after redirecting the bytecode cache under `/tmp`.
- Dry-run adapter smoke with no model command: exit `0`; appended `dry_run_no_model` to the smoke ledger and wrote normalized smoke result.
- Missing-env gate probe: exit `2`; gate blocked with `missing_required_llm_environment`; appended `gate_blocked` to the smoke ledger; marker file absent afterward.
- Unsafe CLI argument probes: secret-looking flag rejected with `credential_like_key`; full-URL argument rejected with `full_url`.
- JSON parse checks for raw and normalized smoke JSON artifacts: passed.
- Scoped changed-file scan for full URLs, bearer tokens, provider token patterns, and cloud/token prefixes: clean.
- `git diff --check` over owned paths: passed.

## Handoff

Delivered. Use `experiments/core_narrative/tools/acut_patch_adapter.py` as the future ACUT patch-generation entrypoint after the coordinator records explicit execution start. No live ACUT model calls were made by this worker. The next coordinator decision is to authorize execution/model calls and confirm the concrete command that will be passed through the adapter.
