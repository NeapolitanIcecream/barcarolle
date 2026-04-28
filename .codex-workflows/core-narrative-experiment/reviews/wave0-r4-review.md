# Wave 0 Revision 4 Review

status: issues_found

## Summary

I inspected the plan, coordinator state, worker contract, LLM access/budget contract, prior reviews, schema-toolsmith and acut-matrix process files, revised schema/tool artifacts, ACUT manifests, and coordinator LLM budget artifacts. I did not inspect any `cli.log` files.

The narrow revision 4 command-argument fix works: an unsafe `run_task.py` probe with a provider-token-looking argument and a full URL exited before command execution, created no stdout/stderr artifacts, and did not leak the probe values. A harmless env-printing probe also kept dummy required LLM env values out of structured output and stdout/stderr artifacts. The ACUT validator still passes all seven manifests, the clean-room leakage self-check still passes, W-score mergeability grade remains numeric/null `0..3`, and the pre-execution budget gate still blocks missing env, missing ledger, unwritable ledger, hard-cap projection, and soft-stop-without-approval before the ACUT command runs.

One credential-boundary issue remains. `run_task.py` still writes raw workspace diffs into `submission.patch`, so a command that writes the allowed `BARCAROLLE_LLM_API_KEY` or `BARCAROLLE_LLM_BASE_URL` values into a tracked file causes the patch result artifact to contain those resolved values.

## Findings

1. High - `schema-toolsmith`: patch artifacts can still persist resolved required LLM env values. The LLM contract forbids writing credential values, resolved API keys, or full base URL values into run results (`/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/shared/llm-access-budget-contract.md:9`), and `llm_access.yaml` repeats that run-result/base-URL prohibition (`/Users/chenmohan/gits/barcarolle/experiments/core_narrative/configs/llm_access.yaml:12`, `:21`). The runner intentionally keeps `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` in the child environment (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/tools/_llm_budget.py:306`), redacts only captured stdout/stderr (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/tools/_llm_budget.py:489`), and then writes `git diff --binary --no-ext-diff` directly to `submission.patch` (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/tools/run_task.py:83`, `:154`). My tracked-file probe ran a safe command that appended its environment to `README.md`; `run_task.py` exited successfully, stdout/stderr stayed clean, but `submission.patch` contained both dummy required env values. This keeps the broader "result artifacts and repository files do not contain dummy BARCAROLLE values" gate open.

## Integration Recommendation

Do not accept revision 4 as execution-ready and do not start ACUT execution workers. The command-argument leak from revision 3 is closed, and the earlier ACUT validator, clean-room leakage, W-score rubric, and pre-execution budget gates remain green, but patch/result artifact credential scanning is still missing.

It is safe to continue treating the ACUT matrix delivery as valid scaffold work. The remaining required revision is owned by `schema-toolsmith` in `run_task.py` / `_llm_budget.py`.

## Required Closure

- Before `run_task.py` writes or retains `submission.patch`, scan the diff and workspace-relevant result artifacts for resolved required LLM env values, provider-secret-looking values, bearer tokens, and full URLs. Fail closed or write only redacted artifacts.
- Ensure a failed secret scan does not leave stdout/stderr, patch, structured output, or workspace files containing dummy required env values in retained result locations.
- Add a regression probe where an otherwise safe ACUT command writes the required env values into a tracked file, and verify the run is rejected or fully redacted without leaking those values.
