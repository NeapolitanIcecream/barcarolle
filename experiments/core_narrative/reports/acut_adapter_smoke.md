# ACUT Adapter Smoke

Worker: `codex-cli-worker-acut-adapter-smoke`
Branch: `codex/core-exp-acut-adapter-smoke`
Worktree: `/Users/chenmohan/gits/barcarolle-wt-acut-adapter-smoke`
Status: no-model smoke complete

## Adapter Path

Created `experiments/core_narrative/tools/acut_patch_adapter.py`.

The adapter is the explicit future patch-generation entrypoint for the experiment. It:

- accepts task/ACUT/run metadata and a patch-generation command after `--`;
- reads LLM access only from `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`;
- does not accept credential values or endpoint URLs as CLI arguments;
- rejects secret-looking command arguments and full-URL command arguments before the budget gate;
- calls the existing `gate_payload` budget gate before any patch-generation command can run;
- preserves the USD `$240` soft stop and USD `$300` hard cap through the existing budget helper defaults;
- runs future commands with `llm_safe_subprocess_env`, which keeps only the experiment LLM env vars and scrubs other provider-like secret env vars;
- appends an `acut_patch_generation_attempt` ledger record for dry-run, command-completed, command-failed, timed-out, unsafe-patch, and gate-blocked paths when the ledger is appendable;
- writes redacted raw adapter artifacts and can write a normalized no-model smoke result.

No real model endpoint is contacted by `--dry-run`; it exercises the same gate, ledger, and artifact paths with `model_call_made: false`.

## No-Model Checks Run

- `PYTHONPYCACHEPREFIX=/tmp/core-narrative-acut-adapter-pycache python3 -m py_compile ...`
  - Scope: `acut_patch_adapter.py`, `_llm_budget.py`, `run_task.py`, `append_cost_record.py`, `llm_budget_gate.py`.
  - Result: passed. An initial compile without `PYTHONPYCACHEPREFIX` hit the macOS cache path outside the writable sandbox, so the compile was rerun with the cache redirected under `/tmp`.
- Dry-run adapter smoke:
  - Command mode: `--dry-run`.
  - Ledger: copied smoke ledger under `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/cost_ledger.jsonl`.
  - Result: exit `0`; appended a safe `dry_run_no_model` ledger record with zero tokens and zero estimated cost; wrote `experiments/core_narrative/results/normalized/acut_adapter_smoke_dry_run.json`.
- Missing-env gate probe:
  - LLM env names were unset for the process.
  - Result: exit `2`; gate status `blocked`; blocker `missing_required_llm_environment`; appended a safe `gate_blocked` ledger record with zero tokens and zero estimated cost; the probe command marker file was absent afterward, proving the command did not run.
- Unsafe CLI argument probes:
  - Secret-looking flag probe: exit `2`, reason `credential_like_key`.
  - Full-URL argument probe: exit `2`, reason `full_url`.
  - Neither unsafe probe ran a model command.
- JSON parse checks:
  - Parsed both raw adapter result JSON files and both normalized smoke result JSON files with `python3 -m json.tool`.
  - Result: passed.
- Scoped changed-file scan:
  - Scanned this worker's changed files for full URLs, bearer tokens, common provider token patterns, and cloud/token prefixes.
  - Result: clean.
- `git diff --check` over the owned paths.
  - Result: passed.

## Live ACUT Model Calls

None.

No broad ACUT execution, live model call, or live patch-generation attempt was started.

## Next Coordinator Decision

Before execution start, the coordinator must explicitly record that ACUT execution/model calls are allowed, confirm the concrete patch-generation command to pass through `acut_patch_adapter.py`, and confirm that every live attempt will use only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` with the cost ledger append path enabled.
