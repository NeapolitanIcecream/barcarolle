# Patch Command Contract

Worker: `patch-command-contract`
Branch: `codex/core-exp-patch-command-contract`
Status: reviewed-ready command path delivered

## Command Path

Added `experiments/core_narrative/tools/barcarolle_patch_command.py`.

The command:

- reads live LLM access only from `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`;
- does not define CLI arguments for credential values, bearer tokens, or endpoint values;
- rejects secret-looking CLI arguments, resolved required env values in CLI arguments, and full URL CLI arguments before parsing;
- prepares a concise prompt from `.core_narrative/task.json`, the packaged statement, and the ACUT manifest;
- redacts full URLs from prompt inputs before prompt hashing or any optional summary output;
- records prompt digest and size only, not prompt content;
- supports `--dry-run`, `--mock-response`, and `--mock-response-text` no-model modes;
- in live mode, posts to the configured endpoint using only the allowed env vars;
- applies returned unified diffs, JSON `{ "unified_diff": ... }` style responses, or simple structured file patches;
- rejects generated patch content containing resolved env values, bearer tokens, provider-token patterns, or full URLs before applying.

The adapter remains the budget gate, redaction gate, patch artifact collector,
and cost ledger wrapper. The new command is intended to run after `--` in
`experiments/core_narrative/tools/acut_patch_adapter.py`.

## Review Command Template

Template for a later single ACUT/task live attempt after coordinator approval:

```bash
python3 /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/tools/acut_patch_adapter.py \
  --workspace <prepared-task-workspace> \
  --task /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml \
  --acut /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/configs/acuts/lower-budget-fast-path.yaml \
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
    --acut /Users/chenmohan/gits/barcarolle-wt-patch-command-contract/experiments/core_narrative/configs/acuts/lower-budget-fast-path.yaml
```

Before running this template live, set only the approved env var names for LLM
access: `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`. Do not add
credential values or endpoint values to the command line.

## No-Model Checks

- Compile: `barcarolle_patch_command.py` passed `py_compile` with pycache redirected under `/tmp`.
- Direct dry run with both required env vars unset: exit `0`, prompt prepared, no model call.
- Direct live-mode missing-env probe: exit `2`, `network_attempted: false`, no model call.
- Unsafe CLI probe for credential-like argument: exit `2`, rejected before parsing.
- Unsafe CLI probe for full URL argument: exit `2`, rejected before parsing.
- Direct mock-response probe with both required env vars unset: exit `0`, patch applied to a synthetic `/tmp` workspace, no model call.
- Adapter `--dry-run` wrap: exit `0`, zero-cost ledger append, no command execution, no model call.
- Adapter no-model mock probe: exit `0`, command ran in `mock_response` mode, adapter wrote a safe patch artifact and appended a zero-cost ledger record.
- JSON parse checks passed for command result artifacts, adapter result artifacts, and ledger JSONL files.
- Scoped artifact scan found no credential values, bearer token values, endpoint values, or full URLs in committed patch-command smoke artifacts.
- `git diff --check` passed over owned paths.

No broad ACUT execution, live ACUT model call, or live patch-generation attempt
was started.

## Artifacts

- `experiments/core_narrative/results/normalized/patch_command_contract_summary.json`
- `experiments/core_narrative/results/normalized/patch_command_contract_adapter_dry_run.json`
- `experiments/core_narrative/results/raw/patch_command_contract_missing_env/command_result.json`
- `experiments/core_narrative/results/raw/patch_command_contract_unsafe_cli/api_key_result.json`
- `experiments/core_narrative/results/raw/patch_command_contract_unsafe_cli/full_url_result.json`
- `experiments/core_narrative/results/raw/patch_command_contract_mock_response/command_result.json`
- `experiments/core_narrative/results/raw/patch_command_contract_adapter_dry_run/adapter_result.json`
- `experiments/core_narrative/results/raw/patch_command_contract_adapter_mock_probe/adapter_result.json`
- `experiments/core_narrative/results/raw/patch_command_contract_adapter_mock_probe/submission.patch`

Note: the adapter currently marks command-mode executions as `model_call_made:
true` by convention. In the adapter mock probe, the wrapped command artifact
records `mode: mock_response` and `model_call_made: false`; no live endpoint was
contacted.
