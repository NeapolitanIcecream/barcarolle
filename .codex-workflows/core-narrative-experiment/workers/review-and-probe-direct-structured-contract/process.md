# Review and Probe Direct Structured Contract Process

status: delivered_live_probe_infra_blocked
updated: 2026-05-07T13:11:29+08:00
stage: review-and-probe-direct-structured-contract
run_id: `pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1`

## Summary

Recovered the interrupted stage, preserved the pre-existing dirty plan file, completed no-model direct structured-output hardening, ran focused regression tests, then ran exactly one bounded paid pilot 010 probe after the BARCAROLLE LLM env and budget gate were present. The live probe was materially different from pilot 009 because it used `structured-files-json-v1` instead of accepting a generated unified diff. It did not produce a scoreable result: the live request timed out after the 120s direct HTTP timeout before a model response, so no verifier-ready patch existed.

## Owned Paths

- `experiments/core_narrative/tools/barcarolle_patch_command.py`
- `experiments/core_narrative/tools/test_barcarolle_patch_command.py`
- `experiments/core_narrative/results/cost_ledger.jsonl`
- `experiments/core_narrative/results/normalized/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1.json`
- `experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/**`
- `experiments/core_narrative/reports/2026-05-07_review_probe_direct_structured_contract.md`
- `.codex-workflows/core-narrative-experiment/workers/review-and-probe-direct-structured-contract/process.md`

## Inventory

- Branch: `codex/core-narrative-experiment`
- Start HEAD for this recovery pass: `ab97157` (`Harden direct output contract preflight`)
- Pre-existing dirty file inspected and preserved/not staged: `docs/experiments/core-narrative-experiment-plan.md`
- Ledger before pilot 010: 12 records, cumulative estimated cost USD `41.0008`
- Latest blocker before this stage: pilot 009 reached live direct model output but failed `git apply --check`; no verifier-ready patch existed.

## Work Completed

- Added generated patch-path unsafe-content rejection to the direct patch command.
- Added no-model regression coverage for URL-like structured file paths.
- Added no-model adapter regression coverage for strict structured-files output producing a non-empty patch artifact.
- After pilot 010 timed out, added no-model regression coverage and direct-command classification hardening so future provider timeout details classify as `llm_request_timed_out`, mark `model_call_made: true` when `network_attempted: true`, and preserve the requested `output_contract` in error summaries.
- Prepared a fresh base-tree-only Click workspace for `click__rbench__001`.
- Ran a strict structured-files direct dry run against `frontier-generic-swe` and `click__rbench__001`; prompt metadata only, no model call.
- Ran exactly one bounded paid probe with run id `pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1`.

## Verification

- `python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/test_barcarolle_patch_command.py experiments/core_narrative/tools/test_acut_patch_adapter.py` passed.
- Focused regression subset passed: `Ran 3 tests in 0.338s`, `OK`.
- Related unit suite passed: `cd experiments/core_narrative/tools && python3 -m unittest test_barcarolle_patch_command.py test_acut_patch_adapter.py test_codex_cli_patch_command.py`; `Ran 23 tests in 6.549s`, `OK`.
- Budget preflight passed: ledger parseable/writable, env present, projected USD `10.00`, projected cumulative USD `51.0008`, below soft/hard caps.
- Direct structured dry run wrote `direct_structured_dry_run_summary.json` with `model_call_made: false`.

## Live Probe Result

- Run id: `pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1`
- ACUT/task: `frontier-generic-swe` / `click__rbench__001` / `rbench` / attempt `1`
- Adapter status: `command_failed`
- Command exit code: `2`
- Command duration: `120.869s`
- Inner direct summary: `status: error`, `error: LLM request failed`, details `error_type: timeout`, `network_attempted: true`
- Verifier-ready patch: `false`
- Patch artifact: `submission.patch`, `size_bytes: 0`
- Normalized status: `infra_failed`
- Ledger append: record 13 appended, estimated USD `10.00`, cumulative estimated USD `51.0008`, actual cost unknown/null.

The raw pilot 010 `patch_command_summary.json` was produced before the post-probe classification hardening, so it records `failure_class: llm_request_failed`; the details identify the timeout. Future equivalent direct-command timeout summaries are now covered by regression as `llm_request_timed_out`.

## Handoff

The flow still has no scoreable ACUT result. The immediate blocker is not patch extraction anymore; it is a direct live HTTP timeout before model response on the strict structured-files path. Next work should do no-model transport/readiness triage first, then either run one materially changed bounded probe (for example a timeout/endpoint behavior probe with the improved timeout classification) or switch to a reviewed alternate transport. Do not retry pilot 010 unchanged.
