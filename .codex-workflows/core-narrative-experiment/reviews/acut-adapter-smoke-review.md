# ACUT Adapter Smoke Review

status: no_issues
reviewed_worker_commit: 3b2f820
updated: 2026-04-29T10:25:05+08:00

## Summary

Reviewed delivered worker branch `codex/core-exp-acut-adapter-smoke` at commit
`3b2f820`. The changed-file scope is limited to the ACUT adapter smoke worker
process file, the new adapter entrypoint, and its smoke report/result artifacts.

`experiments/core_narrative/tools/acut_patch_adapter.py` uses the existing LLM
budget helpers to require `BARCAROLLE_LLM_API_KEY` and
`BARCAROLLE_LLM_BASE_URL`, reject unsafe credential-like or full-URL command
arguments before persistence, evaluate the budget/ledger gate before command
execution, run future commands with the scrubbed LLM subprocess environment, and
append `acut_patch_generation_attempt` ledger records for the reviewed dry-run,
gate-blocked, and command-result paths. Captured stdout/stderr and patch
artifacts use the existing redaction and unsafe-patch rejection helpers.

The delivered smoke checks and reviewer probes were no-model-call checks only.
Broad ACUT execution, live model calls, and live patch-generation attempts remain
not started.

## Findings

None.

## Required Closure

None.

## Checks Run

- Verified delivered worker worktree is clean, on branch
  `codex/core-exp-acut-adapter-smoke`, and HEAD is
  `3b2f8205bae791d16d43524f57139ec9198a36f7`.
- Verified `git diff-tree --no-commit-id --name-status -r 3b2f820` changed only
  the worker process file, `experiments/core_narrative/tools/acut_patch_adapter.py`,
  the smoke report, and `acut_adapter_smoke` raw/normalized result artifacts.
- Inspected `acut_patch_adapter.py`, `_llm_budget.py`, `run_task.py`,
  `append_cost_record.py`, `llm_budget_gate.py`, `llm_access.yaml`, the worker
  process file, the smoke report, and prior LLM-budget review context.
- Ran `git diff --check 3b2f820^ 3b2f820`: passed.
- Ran `PYTHONPYCACHEPREFIX=/tmp/acut-adapter-review-pycache python3 -m py_compile`
  for `acut_patch_adapter.py`, `_llm_budget.py`, `run_task.py`,
  `append_cost_record.py`, and `llm_budget_gate.py`: passed.
- Parsed delivered raw and normalized smoke JSON artifacts and both smoke ledger
  files; appended smoke ledger records contain the required attempt fields for
  `dry_run_no_model` and `gate_blocked`.
- Ran an isolated `/tmp` adapter dry-run probe with placeholder env presence:
  exit `0`, gate `passed`, ledger append `appended`, `model_call_made: false`.
- Ran an isolated `/tmp` missing-env gate probe with a marker command:
  exit `2`, gate `blocked`, ledger append `appended`, marker absent.
- Ran isolated `/tmp` unsafe command-argument probes for a credential-like flag
  and a synthesized full URL argument: both exited `2` before result files were
  written.
- Scanned delivered changed files for full URLs, bearer/provider-token-looking
  values, credential literal values, and common cloud/token prefixes with
  value-only patterns: clean.
