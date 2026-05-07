# ACUT Adapter Smoke

Worker: `codex-cli-worker-acut-adapter-smoke`
Branch: `codex/core-exp-patch-command-contract`
Worktree: `/Users/chenmohan/gits/barcarolle-wt-patch-command-contract`
Status: no-model smoke refreshed for active 2x2 pilot
Updated: `2026-04-29T12:12:40+08:00`

## Supersession

Revision 2 refreshes the `acut_adapter_smoke*` evidence in place for the active
2x2 pilot. The pre-redesign smoke outputs at these paths are superseded and are
not current smoke evidence, executable templates, default core IDs, or
new-execution ACUT references.

Current smoke evidence uses the active `cheap-click-specialist` ACUT manifest
and records the active pilot profile:

- profile: `budget-constrained-2x2-pilot-v2`
- active core IDs: `frontier-generic-swe`, `frontier-click-specialist`,
  `cheap-generic-swe`, `cheap-click-specialist`
- pilot split limits: 2 `G_score`, 3 `RBench`, 2 `RWork`
- attempts: one primary attempt per ACUT/task
- pilot primary patch-generation attempts: 28

## Adapter Path

`experiments/core_narrative/tools/acut_patch_adapter.py` remains the explicit
patch-generation adapter path. It is the budget gate, redaction gate, patch
artifact collector, and cost-ledger wrapper for later approved ACUT attempts.

The adapter:

- accepts task/ACUT/run metadata and a patch-generation command after `--`;
- reads live LLM access only from `BARCAROLLE_LLM_API_KEY` and
  `BARCAROLLE_LLM_BASE_URL`;
- does not accept credential values or endpoint URLs as CLI arguments;
- rejects secret-looking command arguments and full-URL command arguments before
  the budget gate;
- calls the existing `gate_payload` budget gate before any patch-generation
  command can run;
- preserves the USD `$240` soft stop and USD `$300` hard cap through the
  existing budget helper defaults;
- runs future commands with `llm_safe_subprocess_env`, which keeps only the
  experiment LLM env vars and scrubs other provider-like secret env vars;
- appends an `acut_patch_generation_attempt` ledger record for dry-run,
  command-completed, command-failed, timed-out, unsafe-patch, and gate-blocked
  paths when the ledger is appendable;
- writes redacted raw adapter artifacts and can write normalized no-model smoke
  result JSON.

No real model endpoint is contacted by `--dry-run`; it exercises the same gate,
ledger, and artifact paths with `model_call_made: false`.

## Current No-Model Evidence

- Dry-run adapter smoke:
  - ACUT manifest: `experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml`.
  - Command mode: adapter `--dry-run`.
  - Ledger: copied smoke ledger under
    `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/cost_ledger.jsonl`.
  - Result: exit `0`; appended a safe `dry_run_no_model` ledger record with
    zero tokens and zero estimated cost; wrote
    `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/adapter_result.json`
    and
    `experiments/core_narrative/results/normalized/acut_adapter_smoke_dry_run.json`.
  - Model calls: none.
- Missing-env gate probe:
  - ACUT manifest: `experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml`.
  - Command path: `barcarolle_patch_command.py --dry-run`, passed only after
    `--` to `acut_patch_adapter.py`.
  - LLM env names were unset for the process.
  - Result: exit `2`; gate status `blocked`; blocker
    `missing_required_llm_environment`; appended a safe `gate_blocked` ledger
    record with zero tokens and zero estimated cost; the wrapped command did not
    run.
  - Model calls: none.
- Summary:
  - `experiments/core_narrative/results/normalized/acut_adapter_smoke_summary.json`
    records the active 2x2 profile, artifact references, no-model status, and
    no broad execution.

## Checks Run

- `PYTHONPYCACHEPREFIX=/tmp/core-narrative-acut-adapter-smoke-r2-pycache python3 -m py_compile ...`
  - Scope: `acut_patch_adapter.py`, `_llm_budget.py`, `run_task.py`,
    `barcarolle_patch_command.py`.
  - Result: passed.
- Dry-run adapter smoke with active `cheap-click-specialist`: passed with
  `model_call_made: false`.
- Missing-env gate probe with active `cheap-click-specialist`: blocked before
  command execution with `model_call_made: false`.
- Unsafe CLI argument probes through `acut_patch_adapter.py`: credential-like
  command argument rejected; full-URL command argument rejected; neither probe
  ran a patch-generation command.
- JSON parse checks: raw adapter result JSON, normalized result JSON, normalized
  summary JSON, and smoke ledger JSONL parse successfully.
- Structured invariant check: current adapter smoke evidence records active 2x2
  core IDs, profile `budget-constrained-2x2-pilot-v2`, split limits 2
  `G_score` / 3 `RBench` / 2 `RWork`, one primary attempt per ACUT/task, and
  28 pilot primary attempts.
- Scoped retired-ID scan over current smoke report/results: clean.
- Scoped credential/full-URL scan over current smoke report/results: clean.
- `git diff --check` over owned paths: passed.

## Live ACUT Model Calls

None.

No broad ACUT execution, execution-start preflight, live model call, or live
patch-generation attempt was started.

## Next Coordinator Decision

Before execution start, the coordinator must explicitly record that ACUT
execution/model calls are allowed, confirm the concrete patch-generation command
to pass through `acut_patch_adapter.py`, and confirm that every live attempt
will use only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` with the
cost ledger append path enabled.
