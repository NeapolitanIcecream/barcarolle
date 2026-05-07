# 2026-05-07 Preflight and Direct Output Contract Hardening

status: no_model_hardening_completed_no_live_probe
updated: 2026-05-07T13:10:00+08:00
stage: preflight-and-plan
repo: `/Users/chenmohan/gits/barcarolle`
branch: `codex/core-narrative-experiment`
start_head: `249bdd5` (`Add 2026-05-07 lab handoff`)

## Inventory

- Branch matched expected `codex/core-narrative-experiment`.
- Starting HEAD was `249bdd5`.
- Pre-existing dirty file inspected and preserved: `docs/experiments/core-narrative-experiment-plan.md`.
  - It adds/repeats the LLM access and budget contract, `llm_access.yaml`, cost ledger references, and budget-constrained acceptance gates.
  - This stage did not overwrite or commit that pre-existing dirty plan diff.
- Coordinator state: pilot 009 integrated; no active worker recorded; next allowed step was no-model direct-output-contract hardening/review only.
- Latest scoreable state: pilots 001-009 still produced no scoreable ACUT result.
- Latest blocker: pilot 009 reached a live model response through direct `barcarolle_patch_command.py`, but the generated unified diff failed `git apply --check` with `corrupt patch at line 12`; no verifier-ready patch existed.
- Ledger path: `experiments/core_narrative/results/cost_ledger.jsonl`.
- Ledger state at preflight: 12 records, cumulative estimated cost USD `41.0008`; soft stop USD `240`, hard cap USD `300`.

## No-Model Hardening Completed

This stage did not make any live BARCAROLLE model/API calls. It hardened the path implicated by pilot 009 in two ways:

1. Added an explicit direct-output contract switch to `barcarolle_patch_command.py`:
   - default remains `patch-or-files-v1` for compatibility;
   - new `structured-files-json-v1` asks chat-completions-style routes for JSON object output and prompts for `{"files":[...]}` only;
   - strict mode rejects unified-diff fallback responses before workspace mutation, giving a materially different candidate path for the next direct probe.
2. Added machine-readable failure classification:
   - direct invalid diffs now emit `failure_class: invalid_unified_diff`;
   - structured-contract drift emits `failure_class: output_contract_violation`;
   - unsupported patch responses and unsafe generated content also receive distinct classes;
   - the outer `acut_patch_adapter.py` now preserves direct `barcarolle_patch_command` failure classes and model-response receipt metadata instead of collapsing them to generic `nonzero_exit`.

## Verification

Commands run from `/Users/chenmohan/gits/barcarolle` unless noted:

```bash
python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/test_barcarolle_patch_command.py experiments/core_narrative/tools/test_acut_patch_adapter.py
cd experiments/core_narrative/tools && python3 -m unittest test_barcarolle_patch_command.py test_acut_patch_adapter.py test_codex_cli_patch_command.py
git diff --check
python3 - <<'PY'  # parse cost ledger and assert latest cumulative
# output: {'ledger_records': 12, 'latest_cumulative_estimated_cost_usd': 41.0008}
PY
python3 - <<'PY'  # scoped changed-file no-secret scan
# output: {'files_scanned': 8, 'required_env_value_hits': 0, 'full_url_hits': 0, 'bearer_secret_hits': 0, 'secret_like_hits': 0, 'ipv4_hits': 0}
PY
```

Result: `Ran 20 tests in 4.477s`, `OK`; diff check, ledger parse, and scoped no-secret scan passed.

## Readiness Assessment

Readiness improved, but this stage did not authorize or run a paid probe. A next paid probe would be materially different from pilot 009 only if it uses the new strict contract, for example:

- run id candidate: `pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1`;
- direct command path: `acut_patch_adapter.py` + `barcarolle_patch_command.py --output-contract structured-files-json-v1`;
- same budget/ledger/env preflight gates as prior pilots;
- projected cost capped before execution;
- no retry if it fails before verifier.

Before that probe, run one review/readiness worker or coordinator review over this local hardening to confirm the strict structured-files contract does not weaken ACUT controls and that patch application still excludes `.git`, `.core_narrative`, path traversal, unsafe content, and secret/full-URL persistence.

## Current Blockers and Risks

- Blocker to flow objective: no verifier-ready ACUT patch and no scoreable ACUT result yet.
- Risk: structured-files JSON may produce full-file rewrites, which can be more verbose than diffs; keep the next probe bounded and ledgered.
- Risk: chat-completions `response_format` compatibility depends on the BARCAROLLE endpoint; if unsupported, the failure should be classified before any retry decision.
- Risk: existing dirty plan file remains uncommitted and should be preserved by the next stage unless explicitly accepted into a coherent docs commit.

## Recommended Next Stage

`review-and-probe-direct-structured-contract`: review the no-model contract hardening, rerun focused tests plus `git diff --check` and a scoped no-secret scan, then if gates pass and budget preflight remains under cap, run exactly one paid structured-files-json direct probe. Stop at the first scoreable verifier result, classified blocker, or ledger/preflight failure.
