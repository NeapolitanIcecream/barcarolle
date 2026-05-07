# Wave 0 Revision Review

status: issues_found

## Summary

I inspected the plan, coordinator file, worker contract, prior Wave 0 review, the revised worker process files, and the revised schema/tool and ACUT artifacts at the requested commits. I did not inspect any `cli.log` files.

Two prior findings are closed. `prepare_workspace.py` now exports only the base commit tree into a fresh synthetic Git repo, omits `target_commit` from the ACUT-visible task package, and checks that the target commit is not present in the prepared workspace object database (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/tools/prepare_workspace.py:100`, `:115`, `:133`, `:145`). The delivered leakage self-check also checks refs, object database, reachable commits, and task package text (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/tools/check_workspace_leakage.py:134`, `:147`, `:154`, `:164`), and my run of `python3 experiments/core_narrative/tools/check_workspace_leakage.py` passed. `run_result.schema.json` now supports the 0-to-3 W-score mergeability rubric as integer/null enum values (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/schemas/run_result.schema.json:113`).

The ACUT schema/manifest contract mismatch is not closed. It is narrower than before, but the revised schema and validator still reject all seven revised ACUT manifests.

## Findings

1. High - `schema-toolsmith` and `acut-matrix`: all seven revised ACUT manifests still fail the delivered ACUT contract validator. The schema and validator require `execution_mode` and `adapter_or_harness_basis` to be objects (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/schemas/acut.schema.json:78`, `:81`; `/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/tools/validate_acut_manifest.py:50`). The revised manifests encode both fields as scalar strings; for example, `general-benchmark-optimized.yaml` has `execution_mode: codex_cli` and a scalar `adapter_or_harness_basis` (`/Users/chenmohan/gits/barcarolle-wt-acut-matrix/experiments/core_narrative/configs/acuts/general-benchmark-optimized.yaml:37`). The ACUT notes also document `adapter_or_harness_basis` as scalar (`/Users/chenmohan/gits/barcarolle-wt-acut-matrix/experiments/core_narrative/reports/acut_matrix_notes.md:25`), contradicting the schema/tool contract. I ran `PYTHONPYCACHEPREFIX=/tmp/barcarolle-wave0-r1-review-pycache python3 experiments/core_narrative/tools/validate_acut_manifest.py /Users/chenmohan/gits/barcarolle-wt-acut-matrix/experiments/core_narrative/configs/acuts` from the schema-toolsmith worktree; it returned exit code 1 with `invalid_count: 7`, and every manifest failed on `execution_mode must be an object when present` and `adapter_or_harness_basis must be an object when present`. This keeps the prior ACUT schema/manifest contract finding open and blocks treating the revised Wave 0 scaffold as integrated.

## Integration Recommendation

Do not integrate the revised branches as accepted Wave 0 scaffold work yet. The clean-room workspace leakage fix and W-score numeric rubric support are acceptable, and I saw no obvious regression in those areas, but the ACUT manifests still do not validate against the revised schema/tool contract.

Once the ACUT contract is aligned and the delivered validator passes all seven manifests, the coordinator can re-review only that narrow closure unless new changes expand the scope.

## Required Closure

- Align `execution_mode` and `adapter_or_harness_basis` across `acut.schema.json`, `validate_acut_manifest.py`, all seven ACUT manifests, and `acut_matrix_notes.md`. Either make those fields objects everywhere or intentionally allow/document scalar strings everywhere.
- Re-run the schema-toolsmith validator against the ACUT matrix worktree and record a passing result for all seven manifests in the relevant worker handoff.
- Keep the prior pre-run gates from Wave 0 review in force: local target repository smoke/timing lock and concrete general-benchmark instance lock are still required before task-pack construction or ACUT runs.
