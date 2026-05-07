# 2026-05-07 Review and Probe Direct Structured Contract

status: live_probe_infra_failed_timeout_no_scoreable_result
updated: 2026-05-07T13:11:29+08:00
stage: review-and-probe-direct-structured-contract
repo: `/Users/chenmohan/gits/barcarolle`
branch: `codex/core-narrative-experiment`
start_head: `ab97157` (`Harden direct output contract preflight`)
run_id: `pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1`

## Inventory

- Branch matched expected `codex/core-narrative-experiment`.
- Starting HEAD for this recovery pass was `ab97157`, after prior no-model structured-output hardening.
- Pre-existing dirty file inspected and preserved: `docs/experiments/core-narrative-experiment-plan.md`.
  - The dirty diff still adds the LLM access/budget contract, `llm_access.yaml`, cost-ledger references, and budget-constrained acceptance gates.
  - This stage did not overwrite or stage that pre-existing plan diff.
- Latest integrated pilot before this stage was pilot 009: live direct transport reached a model response but failed before verifier because the generated unified diff failed `git apply --check` with corrupt-patch symptoms.
- Pilots 001-009 produced no scoreable ACUT result.
- Ledger before pilot 010: `experiments/core_narrative/results/cost_ledger.jsonl`, 12 records, cumulative estimated cost USD `41.0008`.

## No-Model Hardening Completed

This stage added direct structured-output hardening before and after the live probe:

1. `barcarolle_patch_command.py` now rejects unsafe generated path strings before applying structured-file output or validating diff-declared paths. This closes a structured-output leakage gap where a model could put a full URL, resolved required env value, authorization-token-looking value or provider-token-looking value into a generated file path even if file content was clean.
2. `test_barcarolle_patch_command.py` now specifies that strict `structured-files-json-v1` responses with URL-like generated paths are rejected before workspace mutation and without persisting the URL in the summary.
3. `test_barcarolle_patch_command.py` now specifies that `acut_patch_adapter.py --command-no-model` can wrap the strict `structured-files-json-v1` direct command and collect a non-empty patch artifact after structured file application.
4. After pilot 010 exposed a provider timeout shape, `barcarolle_patch_command.py` now classifies timeout-shaped `LLM request failed` details as `llm_request_timed_out`, treats `network_attempted: true` as `model_call_made: true` for conservative ledger semantics, and records the requested `output_contract` in error summaries.
5. `test_barcarolle_patch_command.py` now specifies this no-model timeout classification behavior.

## Candidate Pilot 010 Readiness Artifacts

Artifacts were written under:

- `experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/budget_preflight.json`
- `experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/prepare_workspace.json`
- `experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/direct_structured_dry_run_summary.json`

Budget preflight passed:

- required BARCAROLLE env: present by name only; values not recorded;
- ledger: present, writable, parseable;
- projected pilot cost: USD `10.00`;
- projected cumulative estimated cost: USD `51.0008`;
- soft stop: USD `240`, not reached;
- hard cap: USD `300`, not reached.

The candidate direct command dry run prepared the actual `frontier-generic-swe` / `click__rbench__001` prompt under `structured-files-json-v1` without a model call:

- status: `dry_run_completed`
- model route: `openai/gpt-5.5`
- prompt content recorded: `false`
- prompt char count: `3507`
- output contract: `structured-files-json-v1`
- model_call_made: `false`

## Paid Probe Result

The next paid probe was materially different from pilot 009 because it used the strict `structured-files-json-v1` direct contract instead of accepting a unified diff. It was run once, with no retry:

- Run id: `pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1`
- ACUT/task/split: `frontier-generic-swe` / `click__rbench__001` / `rbench`
- Attempt: `1`
- Adapter output: `experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/adapter_result.json`
- Normalized output: `experiments/core_narrative/results/normalized/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1.json`
- Adapter status: `command_failed`
- Command exit code: `2`
- Command duration: `120.869s`
- Inner direct summary: `status: error`, `error: LLM request failed`, details `error_type: timeout`, `network_attempted: true`
- Verifier-ready patch available: `false`
- Patch artifact: `submission.patch`, `size_bytes: 0`
- Normalized status: `infra_failed`

No verifier ran because there was no patch to apply. The flow still has no scoreable ACUT result.

The raw `patch_command_summary.json` was generated before the post-probe timeout classification hardening, so its `failure_class` is `llm_request_failed`; the structured details identify the failure as a timeout. Future equivalent failures are now tested as `llm_request_timed_out`.

## Ledger Status

`experiments/core_narrative/results/cost_ledger.jsonl` now has 13 records. The pilot 010 record appended:

- record_type: `acut_patch_generation_attempt`
- event: `command_failed`
- estimated_cost_usd: `10.0`
- actual_cost_usd: `null`
- input_tokens: `877`
- output_tokens: `64000`
- cumulative_estimated_cost_usd: `51.0008`
- metadata failure_class: `llm_request_failed`
- metadata model_call_made: `true`
- metadata patch_size_bytes: `0`

## Verification

Commands run from `/Users/chenmohan/gits/barcarolle` unless noted:

```bash
python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/test_barcarolle_patch_command.py experiments/core_narrative/tools/test_acut_patch_adapter.py
cd experiments/core_narrative/tools && python3 -m unittest test_barcarolle_patch_command.BarcarollePatchCommandTests.test_live_transport_timeout_records_attempted_model_call test_barcarolle_patch_command.BarcarollePatchCommandTests.test_structured_files_contract_rejects_url_like_generated_paths test_barcarolle_patch_command.BarcarollePatchCommandTests.test_adapter_command_no_model_wraps_structured_files_contract_with_patch_artifact
cd experiments/core_narrative/tools && python3 -m unittest test_barcarolle_patch_command.py test_acut_patch_adapter.py test_codex_cli_patch_command.py
python3 experiments/core_narrative/tools/llm_budget_gate.py --ledger experiments/core_narrative/results/cost_ledger.jsonl --projected-cost-usd 10 --acut-id frontier-generic-swe --split rbench --attempt 1 --output experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/budget_preflight.json
python3 experiments/core_narrative/tools/prepare_workspace.py --task experiments/core_narrative/tasks/click/rbench/click__rbench__001/task.yaml --source-repo experiments/core_narrative/external_repos/click --workspace experiments/core_narrative/workspaces/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1 --force --output experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/prepare_workspace.json
python3 experiments/core_narrative/tools/barcarolle_patch_command.py --workspace experiments/core_narrative/workspaces/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1 --acut experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml --dry-run --output-contract structured-files-json-v1 --summary-output experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/direct_structured_dry_run_summary.json
python3 experiments/core_narrative/tools/acut_patch_adapter.py --workspace experiments/core_narrative/workspaces/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1 --task experiments/core_narrative/workspaces/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/.core_narrative/task.json --acut experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml --attempt 1 --run-id pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1 --artifact-dir experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1 --output experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/adapter_result.json --normalized-output experiments/core_narrative/results/normalized/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1.json --llm-ledger experiments/core_narrative/results/cost_ledger.jsonl --projected-cost-usd 10 --input-tokens 877 --output-tokens 64000 --timeout-seconds 300 -- python3 /Users/chenmohan/gits/barcarolle/experiments/core_narrative/tools/barcarolle_patch_command.py --workspace /Users/chenmohan/gits/barcarolle/experiments/core_narrative/workspaces/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1 --task-package .core_narrative/task.json --acut /Users/chenmohan/gits/barcarolle/experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml --output-contract structured-files-json-v1 --summary-output /Users/chenmohan/gits/barcarolle/experiments/core_narrative/results/raw/pilot_010__frontier-generic-swe__click__rbench__001__structured-files-json__attempt1/patch_command_summary.json
```

Focused regression result: `Ran 3 tests in 0.338s`, `OK`.
Related unit result: `Ran 23 tests in 6.549s`, `OK`.

## Current Blocker

The flow still has no scoreable ACUT result. The verified blocker is now a strict direct HTTP timeout before model response on the structured-files path, not a malformed unified diff or patch extraction failure. No retry should repeat pilot 010 unchanged.

## Recommended Next Stage

Do no-model transport/readiness triage before any more spend. A next paid probe should only run after a materially different preflight signal or contract change, such as explicit timeout classification/endpoint behavior validation, a reviewed timeout adjustment, or a reviewed alternate transport path. Keep the next live probe single-attempt, ledgered, and bounded below the USD `240` soft stop.
