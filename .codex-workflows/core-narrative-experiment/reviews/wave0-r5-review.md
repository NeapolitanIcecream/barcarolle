# Wave 0 Revision 5 Review

status: no_issues

## Summary

I inspected the required coordinator, worker, contract, and plan files; the delivered schema-toolsmith branch `codex/core-exp-schema-toolsmith` at commit `11ce367`; the revision 5 implementation commit `df16bdb`; the current LLM access config and initialized cost ledger; and the relevant schema-toolsmith tools. I did not inspect any `cli.log` files and did not make real model calls.

The revision 5 patch-artifact credential boundary is closed for the reviewed tooling. `run_task.py` now rejects unsafe diffs before retaining `submission.patch`, records only value-free unsafe-content reason counts, removes any pre-existing patch at the target path, and restores tracked workspace changes after unsafe patch rejection. Focused dummy-value probes confirmed that required LLM env values, bearer/provider-token-looking text, credential-literal-looking text, and full URLs were not retained in patch, runner JSON, stdout/stderr, or tracked workspace files after rejection.

The prior revision 4 command-argument protection and stdout/stderr redaction still hold. The LLM access config remains value-free, the cost ledger exists, the budget gate still blocks missing env, missing/unwritable ledger, projected hard-cap overflow, and soft-stop-without-approval, the default core profile remains constrained to the four required ACUTs and task counts, and the append-cost tool records safe cost fields while rejecting unsafe metadata without echoing matched values.

## Findings

None.

## Required Closure

None.

## Self-Checks

- Verified `experiments/core_narrative/configs/llm_access.yaml` contains required env var names, redaction policy, budget caps, default core ACUT profile, deferred ACUT policy, and no full URL values.
- Verified `experiments/core_narrative/results/cost_ledger.jsonl` exists and is tracked.
- Ran the schema-toolsmith ACUT validator against all seven ACUT manifests: `manifest_count: 7`, `invalid_count: 0`.
- Ran dummy-value budget-gate probes for missing env, missing ledger, unwritable ledger, projected hard cap, soft stop, and deferred non-core ACUT approval requirements.
- Ran `append_cost_record.py` safe append and unsafe metadata rejection probes; the unsafe rejection did not echo the generated unsafe value and did not modify the ledger.
- Ran an r5 tracked-file mutation probe where the ACUT command wrote generated dummy required LLM env values to a tracked file and stdout/stderr. Result: exit `2`, `status: unsafe_patch_rejected`, no retained `submission.patch`, tracked changes restored, and no generated dummy values retained in runner JSON, stdout/stderr artifacts, or tracked files.
- Ran an r5 unsafe-pattern patch probe for bearer/provider-token-looking text, credential-literal-looking text, and full URL text. Result: exit `2`, `status: unsafe_patch_rejected`, no retained `submission.patch`, tracked changes restored, value-free reason counts present, and generated unsafe values absent from retained artifacts.
- Re-ran the r4 unsafe command-argument probe. Result: exit `2` before ACUT execution, no structured output file, no stdout/stderr artifacts, and no retained patch artifact.
- Re-ran harmless required-env stdout/stderr redaction. Result: exit `0`, redaction markers present, generated dummy values absent from runner JSON and stdout/stderr artifacts.
- Verified `run_task.py` blocks before command execution for missing env and missing ledger.
- Ran `git diff --check` in the reviewer worktree and `git diff --check HEAD` in the schema-toolsmith worktree.
