# Patch Command Contract Revision 1 Review

status: issues_found
reviewed_patch_command_revision_commit: 870d5f5
updated: 2026-04-29T12:02:55+08:00

## Summary

Revision `870d5f5` closes the specific prior patch-command finding in the
refreshed patch-command artifacts: the executable adapter template now routes
through `acut_patch_adapter.py` and uses the active
`cheap-click-specialist` manifest; the refreshed patch-command dry-run/mock
adapter evidence records the active 2x2 core IDs, 2 `G_score` / 3 `RBench` /
2 `RWork`, one primary attempt per ACUT/task, and 28 pilot primary attempts.

`barcarolle_patch_command.py` remains a custom BARCAROLLE-env-only command path
for the adapter contract. Live LLM access is read through
`BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`; scoped scans over the
patch-command report/results/process artifacts did not find persisted
credential values, bearer values, provider-token values, resolved endpoint
values, or full URLs. I did not inspect any `cli.log` file and did not start
broad ACUT execution, execution-start preflight, live model calls, or live
patch-generation attempts.

One related command-contract issue remains: the earlier ACUT adapter smoke
report/results are still presented as current smoke evidence and still record
retired ACUT IDs and the retired default core profile.

## Findings

1. Medium - Current ACUT adapter smoke evidence still records retired ACUT IDs.
   The revision's refreshed `patch_command_contract*` evidence is clean, but
   the existing adapter smoke report remains labeled `Status: no-model smoke
   complete` and points at `acut_adapter_smoke_dry_run` as current smoke output
   (`experiments/core_narrative/reports/acut_adapter_smoke.md:6`,
   `experiments/core_narrative/reports/acut_adapter_smoke.md:31`). That raw
   smoke result records `acut_id: general-benchmark-optimized` and a default
   execution profile containing `general-benchmark-optimized`,
   `repo-context-heavy`, `retrieval-sparse-symbolic`, and
   `lower-budget-fast-path`
   (`experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/adapter_result.json:2`,
   `experiments/core_narrative/results/raw/acut_adapter_smoke_dry_run/adapter_result.json:36`).
   The normalized smoke result also records `general-benchmark-optimized`
   (`experiments/core_narrative/results/normalized/acut_adapter_smoke_dry_run.json:2`).
   Because these are not clearly marked as superseded historical artifacts,
   the review cannot confirm that retired ACUT IDs are absent from current
   smoke evidence.

## Required Closure

Refresh or clearly supersede the pre-redesign `acut_adapter_smoke*` report and
result artifacts so that current smoke evidence no longer advertises retired
ACUT IDs or the retired `budget-constrained-core-v1` default profile. Historical
references can remain if they are explicitly labeled historical/superseded and
are not used as executable templates, current smoke evidence, default core IDs,
or new-execution ACUT references.

Do not start broad ACUT execution, execution-start preflight, live model calls,
or live patch-generation attempts while making that closure.

## Checks Run

- Read previous focused review artifact and reviewer process; no `cli.log`
  files inspected.
- `git show --name-status --oneline --no-renames 870d5f5` in the patch-command
  worktree.
- Inspected patch-command report, worker process, `barcarolle_patch_command.py`,
  `acut_patch_adapter.py`, `_llm_budget.py`, `core_subset_run_manifest.yaml`,
  and the four active 2x2 ACUT manifests.
- `PYTHONPYCACHEPREFIX=/tmp/patch-command-r1-reviewer-pycache python3 experiments/core_narrative/tools/validate_acut_manifest.py experiments/core_narrative/configs/acuts --output /tmp/patch-command-r1-reviewer-validation.json`
  passed: 7 manifests valid, 0 invalid.
- `PYTHONPYCACHEPREFIX=/tmp/patch-command-r1-reviewer-pycache python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/_llm_budget.py`
  passed.
- Structured JSON/JSONL parse passed for 10 patch-command result JSON files and
  2 patch-command ledger JSONL files.
- Structured invariant check passed for refreshed patch-command adapter
  dry-run/mock evidence: `cheap-click-specialist`, active 2x2 core IDs, profile
  `budget-constrained-2x2-pilot-v2`, 2/3/2 pilot task limits, one primary
  attempt, and 28 pilot attempts.
- Scoped retired-ID scan over `patch_command_contract*` report/results/process
  artifacts found no retired ACUT IDs.
- Broader smoke-evidence scan found retired IDs in
  `experiments/core_narrative/reports/acut_adapter_smoke.md`,
  `experiments/core_narrative/results/raw/acut_adapter_smoke_*`, and
  `experiments/core_narrative/results/normalized/acut_adapter_smoke_*.json`;
  recorded as the finding above.
- Scoped `codex exec` scan found no bare `codex exec` in patch-generation
  templates or patch-command report/results; worker runner scripts contain
  `codex exec` only as worker launch commands.
- Scoped credential/full-URL scan over patch-command report/results/process
  artifacts passed with no matches for credential values, bearer values,
  provider-token values, resolved env assignments, or full URLs.
- `git diff --check 870d5f5^ 870d5f5 -- . ':(exclude)**/cli.log'` passed.
