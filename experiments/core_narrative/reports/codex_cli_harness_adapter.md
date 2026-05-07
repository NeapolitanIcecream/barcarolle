# Codex CLI Harness Adapter

Status: delivered for focused review

## Summary

Added `experiments/core_narrative/tools/codex_cli_patch_command.py` as a
reviewed-ready inner patch-generation command path for `codex exec`.

The outer `acut_patch_adapter.py` still owns task materialization, budget gate,
cost ledger, captured-artifact redaction, patch artifact collection, verifier
handoff, and normalized artifacts. The new command only prepares the prompt,
temporary Codex CLI home, temporary project trust config, temporary model
catalog, and generated `codex exec` invocation.

No live BARCAROLLE model call was made.

## Command Shape

Adapter template for a later reviewed single attempt:

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

Generated inner command shape:

```bash
CODEX_HOME=<run-local-codex-home> \
codex -a never exec \
  --json \
  --ephemeral \
  --ignore-rules \
  --skip-git-repo-check \
  --full-auto \
  --cd <prepared-task-workspace> \
  --model <openai/gpt-5.4-mini|openai/gpt-5.5> \
  -c 'model_provider="barcarolle"' \
  -c 'model_providers.barcarolle={name="Barcarolle", base_url="<from BARCAROLLE_LLM_BASE_URL at runtime>", env_key="BARCAROLLE_LLM_API_KEY", wire_api="responses"}' \
  -c 'model_catalog_json="<run-local-model-catalog.json>"' \
  -o <artifact-dir>/codex_final.txt \
  -
```

The prompt is passed on stdin. The resolved endpoint value and credential value
are not recorded.

## Harness Properties

- Uses a run-local temporary `CODEX_HOME`.
- Writes `CODEX_HOME/config.toml` that trusts only the prepared task workspace.
- Reads `BARCAROLLE_LLM_BASE_URL` only in live mode, at runtime, for the in-memory Codex CLI config override.
- Uses `BARCAROLLE_LLM_API_KEY` only as the provider `env_key`; the command checks presence but does not store the value.
- Builds a temporary `model_catalog_json` with provider-prefixed active routes:
  `openai/gpt-5.4-mini` and `openai/gpt-5.5`.
- Inherits shell/edit tool metadata from the bundled Codex model catalog and
  overrides base instructions for non-interactive evaluation: complete the task
  using tools, do not stop at progress-only final answers, verify changed files,
  and keep the final answer brief.
- Treats provider catalog refresh warnings as non-fatal when the explicit route
  and temporary catalog are present.

## Smoke Artifacts

- Direct no-model construction smoke:
  `experiments/core_narrative/results/normalized/codex_cli_harness_adapter_direct_dry_run.json`
- Adapter-wrapped no-model command smoke:
  `experiments/core_narrative/results/raw/codex_cli_harness_adapter_adapter_dry_run/adapter_result.json`
- Inner command summary from the adapter-wrapped smoke:
  `experiments/core_narrative/results/raw/codex_cli_harness_adapter_adapter_dry_run/command_result.json`
- Temporary model catalogs and trust configs:
  `experiments/core_narrative/results/raw/codex_cli_harness_adapter_direct_dry_run/**`
  and `experiments/core_narrative/results/raw/codex_cli_harness_adapter_adapter_dry_run/inner/**`

The adapter-wrapped smoke used `--command-no-model` with projected cost `0`.
It appended one zero-cost record to the smoke-local ledger at
`experiments/core_narrative/results/raw/codex_cli_harness_adapter_adapter_dry_run/cost_ledger.jsonl`.
No event was appended to the main experiment cost ledger.

## Execution Guard

This delivery did not start broad ACUT execution, a retry, a second attempt, a
specialist ACUT run, an additional pilot attempt, or a large model-call batch.
