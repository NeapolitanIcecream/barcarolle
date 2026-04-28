# LLM Access And Budget Contract

This contract applies to every ACUT execution, smoke run, execution shard, and patch-generation worker.

## Credential Boundary

- LLM access must use only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`.
- Workers may record the environment variable names and boolean presence checks.
- Workers must never write credential values, bearer tokens, provider secrets, resolved API keys, or full base URL values into Git, `process.md`, CLI logs, run results, reports, prompts, or review files.
- If either required environment variable is absent, the execution worker must mark `status: blocked` before any model call or patch-generation attempt.

## Budget Boundary

- The experiment hard cap is USD `$300`.
- The soft stop is USD `$240`.
- No new ACUT patch-generation run may start when the cost ledger is at or projected to exceed `$300`.
- At or above `$240`, new ACUT patch-generation runs require an explicit coordinator decision recorded in `coordinator.md`.
- Use conservative estimated cost when actual provider billing is unavailable.

## Cost Ledger

The required ledger is:

```text
experiments/core_narrative/results/cost_ledger.jsonl
```

Before ACUT execution starts, the worker must verify that the ledger exists and is writable. If cost ledgering is missing or unavailable, mark `status: blocked` before making a model call.

Every ACUT model call or patch-generation attempt must append a JSONL record with at least:

- `record_type`
- `run_id`
- `acut_id`
- `task_id`
- `split`
- `attempt`
- `event`
- `started_at`
- `finished_at`
- `input_tokens`
- `output_tokens`
- `estimated_cost_usd`
- `actual_cost_usd`
- `cumulative_estimated_cost_usd`

Do not write secrets into ledger records.

## Default Execution Profile

The default executable experiment is budget-constrained:

- core ACUTs: `general-benchmark-optimized`, `repo-context-heavy`, `retrieval-sparse-symbolic`, `lower-budget-fast-path`;
- task counts: 6 `G_score`, 8 `RBench`, and 6 `RWork`;
- one primary attempt per ACUT/task.

Defer `higher-budget-repo-depth`, `retrieval-history-augmented`, and `minimal-context-baseline` unless the core subset finishes below the soft stop and the coordinator records spare budget.

## Coordinator Rule

Do not start broad execution workers until both are true:

- `experiments/core_narrative/configs/llm_access.yaml` is present and reviewed;
- cost ledgering is implemented and the execution worker can prove the ledger gate blocks missing env vars, missing/unwritable ledger, and projected hard-cap overflow.
