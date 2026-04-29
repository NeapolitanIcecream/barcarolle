# Process

status: delivered
updated: 2026-04-29T16:26:37+08:00

## Summary

Focused worker is starting from the parent-session Codex CLI harness handoff.
The goal is to implement or spike replacing only the inner ACUT
patch-generation agent with `codex exec`, while keeping the outer Barcarolle
adapter responsible for task materialization, budget gate, cost ledger,
redaction, normalized result, verifier, and reviewer handoff.

No broad ACUT execution, retry, second attempt, specialist ACUT run, additional
pilot attempt, or large model-call batch is authorized.

## Owned Paths

- `experiments/core_narrative/tools/**` for the Codex CLI inner patch command
  and any minimal adapter integration needed to call it
- `experiments/core_narrative/reports/codex_cli_harness_adapter.md`
- `experiments/core_narrative/results/normalized/codex_cli_harness_adapter*.json`
- `experiments/core_narrative/results/raw/codex_cli_harness_adapter*/**`
- `experiments/core_narrative/results/cost_ledger.jsonl` only if a live
  BARCAROLLE model-call smoke is performed and ledgered
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-harness-adapter/**`

## Branch / Worktree

- Branch: `codex/core-exp-codex-cli-harness-adapter`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-codex-cli-harness-adapter`

## Current Blockers

None.

## Activity Log

- 2026-04-29T16:09:45+08:00: Started focused implementation pass. Read the
  Codex CLI harness handoff and confirmed the delivery remains limited to a
  no-secret Codex CLI inner patch command path and bounded dry-run smoke.
- 2026-04-29T16:20:51+08:00: Added the new Codex CLI inner command and
  completed temporary no-model validation of command construction, temporary
  `CODEX_HOME`, trusted project config, provider-prefixed model catalog, prompt
  hashing, and redacted summary output. No live BARCAROLLE model call occurred.
- 2026-04-29T16:26:37+08:00: Delivered the focused implementation and bounded
  no-model smoke artifacts. The adapter-wrapped smoke invoked
  `codex_cli_patch_command.py --dry-run` through `acut_patch_adapter.py` with
  `--command-no-model`, appended one zero-cost record to a smoke-local ledger,
  and made no live BARCAROLLE model call.

## Changed Files

- `experiments/core_narrative/tools/codex_cli_patch_command.py`
- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/reports/codex_cli_harness_adapter.md`
- `experiments/core_narrative/results/normalized/codex_cli_harness_adapter_direct_dry_run.json`
- `experiments/core_narrative/results/raw/codex_cli_harness_adapter_direct_dry_run/**`
- `experiments/core_narrative/results/raw/codex_cli_harness_adapter_adapter_dry_run/**`
- `experiments/core_narrative/results/raw/codex_cli_harness_adapter_smoke_task/task.json`
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-harness-adapter/process.md`

## Inspected Files

- `.codex-workflows/core-narrative-experiment/coordinator.md`
- `.codex-workflows/core-narrative-experiment/shared/codex-cli-harness-handoff.md`
- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/barcarolle_patch_command.py`
- `experiments/core_narrative/tools/_llm_budget.py`
- `experiments/core_narrative/tools/_common.py`
- `experiments/core_narrative/tools/prepare_workspace.py`
- `experiments/core_narrative/tools/run_task.py`
- `experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml`
- `experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml`
- `experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml`

## Checks Run

- `PYTHONPYCACHEPREFIX=/tmp/codex-cli-harness-pycache python3 -m py_compile experiments/core_narrative/tools/codex_cli_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/_llm_budget.py experiments/core_narrative/tools/barcarolle_patch_command.py`
- Direct no-model smoke of `codex_cli_patch_command.py --dry-run`: passed.
- Adapter-wrapped no-model smoke through `acut_patch_adapter.py --command-no-model -- ... codex_cli_patch_command.py --dry-run`: passed.
- JSON/JSONL parse check for `codex_cli_harness_adapter*.json` and smoke-local JSONL artifacts: parsed 7 files.
- Temporary model catalog check: both catalogs contain exactly `openai/gpt-5.4-mini` and `openai/gpt-5.5`, shell tool metadata, edit tool metadata, and non-interactive base instructions.
- Adapter invocation check: adapter payload, inner command payload, and smoke-local ledger all record `model_call_made: false`.
- Scoped no-secret scan over this process file, report, raw artifacts, and normalized artifacts: no matches for full URL, bearer-token, common provider-token, or IPv4 patterns.
- Guard check over new `codex_cli_harness_adapter*` result paths: no retry, second attempt, specialist ACUT, broad execution, pilot, or large batch artifact names.
- `git diff --check`

## Live Call And Ledger

- live BARCAROLLE model call occurred: no
- main experiment cost ledger appended: no
- smoke-local ledger appended: yes, one zero-cost `command_completed` record at `experiments/core_narrative/results/raw/codex_cli_harness_adapter_adapter_dry_run/cost_ledger.jsonl`

## Reviewed-Ready Command Template

```bash
python3 experiments/core_narrative/tools/acut_patch_adapter.py \
  --workspace <prepared-task-workspace> \
  --task experiments/core_narrative/tasks/<task>/task.yaml \
  --acut experiments/core_narrative/configs/acuts/<active-2x2-acut>.yaml \
  --attempt 1 \
  --run-id <approved-run-id> \
  --artifact-dir experiments/core_narrative/results/raw/<approved-run-id> \
  --output experiments/core_narrative/results/raw/<approved-run-id>/adapter_result.json \
  --normalized-output experiments/core_narrative/results/normalized/<approved-run-id>.json \
  --llm-ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --projected-cost-usd <approved-projected-cost> \
  --coordinator-decision-ref <coordinator-approval-ref> \
  --timeout-seconds <approved-timeout-seconds> \
  -- \
  python3 experiments/core_narrative/tools/codex_cli_patch_command.py \
    --acut experiments/core_narrative/configs/acuts/<same-active-2x2-acut>.yaml \
    --artifact-dir experiments/core_narrative/results/raw/<approved-run-id>/inner \
    --summary-output experiments/core_narrative/results/raw/<approved-run-id>/codex_cli_patch_command.json
```

## Handoff

Read `.codex-workflows/core-narrative-experiment/coordinator.md` and
`.codex-workflows/core-narrative-experiment/shared/codex-cli-harness-handoff.md`
first. Do not inspect any `cli.log` file. Deliver only after a minimal
no-secret smoke is recorded and the process file lists changed files, checks,
whether any live BARCAROLLE model call occurred, and the reviewed-ready command
template with no secret values or full endpoint values.
