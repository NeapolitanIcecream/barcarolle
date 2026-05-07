# Wave 0 Revision 3 Review

status: issues_found

## Summary

I inspected the plan, coordinator state, worker contract, LLM access/budget contract, prior reviews, schema-toolsmith and acut-matrix process files, revised schema/tool artifacts, ACUT manifests, and coordinator LLM budget artifacts. I did not inspect any `cli.log` files.

Most revision gates are closed. The delivered ACUT validator passes all seven manifests, the clean-room workspace leakage fix still passes its synthetic regression check, and `run_result.schema.json` still stores the blinded W-score mergeability grade as `null` or integer `0` through `3`. The coordinator `llm_access.yaml` and initialized `cost_ledger.jsonl` are value-free and match the required default execution profile. My gate probes confirmed missing env vars, missing/unwritable ledger, hard-cap projection, and soft-stop projection are enforced before `run_task.py` executes an ACUT command, and `append_cost_record.py` records tokens, estimated/actual cost, and cumulative estimated cost.

One credential-boundary issue remains: the new runner can still write literal provider credentials or full base URLs supplied as ACUT command arguments into result artifacts, so the "LLM access only through `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`" and "do not write resolved secrets/full base URLs" gates are not fully closed.

## Findings

1. High - `schema-toolsmith`: `run_task.py` persists raw ACUT command arguments without applying the generic secret/full-URL guard. The LLM access contract forbids writing credential values, bearer tokens, provider secrets, resolved API keys, or full base URL values into run results and other artifacts (`/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/shared/llm-access-budget-contract.md:7`, `:9`), and the coordinator config repeats the same forbidden values (`/Users/chenmohan/gits/barcarolle/experiments/core_narrative/configs/llm_access.yaml:21`). The helper has secret-looking field/value checks for API-key patterns and URL-looking values (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/tools/_llm_budget.py:42`, `:50`, `:366`), but `run_task.py` only checks whether the command contains the exact two required environment variable values (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/tools/run_task.py:120`) and then writes `"command": command` to the structured result payload (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/tools/run_task.py:159`). A `/tmp` probe with a synthetic provider-style token and full URL in command arguments exited successfully and wrote both raw values to the run output JSON. That means an execution worker could accidentally pass `--api-key` or `--base-url` style literals, and the new tooling would persist them instead of rejecting or redacting them.

## Integration Recommendation

Do not accept the revised Wave 0 scaffold as execution-ready yet, and do not start ACUT execution workers. The ACUT schema/manifest mismatch from revision 1 is closed, and the leakage/W-score/default-profile/budget-ledger mechanics are acceptable, but schema-toolsmith needs one targeted revision for the remaining credential/result-artifact boundary.

After that fix, a narrow re-review can focus on `run_task.py`, `_llm_budget.py`, and the credential-redaction self-checks.

## Required Closure

- Update `run_task.py` so ACUT command arguments cannot write provider secrets or full base URLs to result artifacts. Either reject secret-looking command arguments before execution or store only a redacted command/digest in structured output.
- Apply the generic secret/full-URL checks or equivalent redaction to all `run_task.py` result payloads and captured artifacts, not only to exact `BARCAROLLE_*` environment values and bearer-token text.
- Add a regression self-check proving a synthetic `--api-key`/`--base-url` command argument is rejected or fully redacted from stdout, stderr, structured run output, patch/result artifacts, and ledger records.
