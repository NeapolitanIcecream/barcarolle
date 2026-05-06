# Pilot 009 Response Metadata Hardening Process

status: delivered
updated: 2026-05-07T01:24:00+08:00

## Scope

No-model hardening after pilot 009 exposed that `barcarolle_patch_command.py`
reported `model_call_made: false` in its own error summary when a live model
response was received but rejected during patch validation. The adapter/ledger
correctly recorded the live model call; this fix aligns the inner summary for
future runs.

No live BARCAROLLE model/API calls were made by this hardening step.

## Files Changed

- `experiments/core_narrative/tools/barcarolle_patch_command.py`
- `experiments/core_narrative/tools/test_barcarolle_patch_command.py`
- `.codex-workflows/core-narrative-experiment/workers/pilot-009-response-metadata-hardening/process.md`

## Verification

- Regression test first failed on the pre-fix code: `test_live_response_apply_failure_records_model_call_made` saw `model_call_made: false` after a mocked live response failed `git apply` validation.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_barcarolle_patch_command.py` passed: 7 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_acut_patch_adapter.py` passed: 4 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py` passed: 5 tests.
- `PYTHONPYCACHEPREFIX=/tmp/barcarolle_post_pilot009_pycache_<pid> python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py` passed.
- `git diff --check` passed.

## Handoff

Future direct live runs that receive a model response and then fail patch safety,
parse, or `git apply` validation now include `model_call_made: true` and
`model_response_received: true` in the inner summary error path. This does not
change pilot 009 artifacts already recorded under the old behavior.
