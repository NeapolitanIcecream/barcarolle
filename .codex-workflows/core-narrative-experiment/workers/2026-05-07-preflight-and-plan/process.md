# 2026-05-07 Preflight and Plan Worker

status: delivered_no_model_hardening
updated: 2026-05-07T13:10:00+08:00
stage: preflight-and-plan
repo: `/Users/chenmohan/gits/barcarolle`
branch: `codex/core-narrative-experiment`

## Scope

Inventory the repo after restart, preserve the pre-existing dirty plan file, and perform one bounded no-model hardening step on the pilot 009 direct-output/patch-extraction failure path. No external actions and no live model calls.

## Inventory

- HEAD at start: `249bdd5` (`Add 2026-05-07 lab handoff`).
- Current branch: `codex/core-narrative-experiment`.
- Pre-existing dirty file inspected and preserved: `docs/experiments/core-narrative-experiment-plan.md`.
- Ledger: `experiments/core_narrative/results/cost_ledger.jsonl`, 12 records, cumulative estimated cost USD `41.0008`.
- Latest blocker: pilot 009 direct live response failed patch validation with zero-byte `submission.patch`; no verifier-ready patch and no scoreable ACUT result.

## Changes

- Added `--output-contract structured-files-json-v1` to `barcarolle_patch_command.py` for a strict JSON `files` direct-output path.
- Added direct patch command failure classes, including `invalid_unified_diff` and `output_contract_violation`.
- Updated `acut_patch_adapter.py` to preserve direct `barcarolle_patch_command` failure classes and model-response receipt metadata.
- Added no-model regression tests for strict structured-files contract behavior and adapter preservation of direct invalid-diff failure class.
- Added report: `experiments/core_narrative/reports/2026-05-07_preflight_direct_output_contract.md`.

## Verification

- `python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/test_barcarolle_patch_command.py experiments/core_narrative/tools/test_acut_patch_adapter.py` passed.
- `cd experiments/core_narrative/tools && python3 -m unittest test_barcarolle_patch_command.py test_acut_patch_adapter.py test_codex_cli_patch_command.py` passed: 20 tests.
- `git diff --check` passed.
- Ledger parse passed: 12 records, latest cumulative estimated cost USD `41.0008`.
- Scoped changed-file no-secret scan passed: 8 files scanned, 0 required env value/full URL/bearer secret/secret-like/IPv4 hits.

## Budget / External Actions

- Live model/API calls made: 0.
- Cost ledger appended: no.
- Estimated new spend: USD `0`.
- External actions: none. No push, PR, email, publication, or external mutation.

## Next Action

Review this no-model hardening. If accepted and ledger/env preflight remains clean, the next bounded stage can run exactly one paid `structured-files-json-v1` direct probe under a new run id and stop on scoreable evidence or a classified blocker.
