# Wave 0 Review

status: issues_found

## Summary

All four delivered worker worktrees are at the coordinator-recorded commits and are clean. I did not inspect any `cli.log` files. Comparing each worker delivery commit against the shared bootstrap commit shows no write-ownership violations inside the worker commits.

The coordinator should not treat Wave 0 as execution-ready. The delivered artifacts expose one direct leakage failure in clean-room workspace preparation and one cross-worker schema/manifest contract mismatch that would prevent reproducible ACUT validation. The target repository and general benchmark outputs are usable as planning inputs, but both still need pre-run locks before Phase 1/2 execution.

## Findings

1. High - `schema-toolsmith`: `prepare_workspace.py` leaks future Git history into ACUT workspaces. The plan requires ACUT workspaces to be checked out at the base commit with future history unavailable (`docs/experiments/core-narrative-experiment-plan.md:693`). The delivered tool clones the full local source repository and then detaches to `base_commit` (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/tools/prepare_workspace.py:107` and `:111`). A synthetic `/tmp` reproduction confirmed that the target commit remains visible via `git log --all` after preparation. Any ACUT with shell or git access could inspect post-base commits, including the solution-bearing target commit for historical tasks. Action: build ACUT workspaces from only the base commit and allowed pre-cutoff history, or remove `.git` and provide a controlled history bundle; add a regression self-check that `target_commit` is absent from refs and the object database.

2. High - `acut-matrix` and `schema-toolsmith`: the ACUT manifests do not satisfy the delivered ACUT schema. The schema requires top-level `provider`, string `model`, `prompt_policy_digest`, `frozen_at`, and string `operator` fields (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/schemas/acut.schema.json:7`). The delivered ACUT files nest provider/name under `model`, use `prompt_or_policy_digest`, use `frozen_date`, use an object `operator`, and use richer nested tool/network/budget shapes (`/Users/chenmohan/gits/barcarolle-wt-acut-matrix/experiments/core_narrative/configs/acuts/general-benchmark-optimized.yaml:4`, `:10`, `:14`, `:58`, `:64`). A required-key check shows all seven ACUT YAML files missing at least `provider`, `prompt_policy_digest`, and `frozen_at`, with additional type/key mismatches. Action: either revise `acut.schema.json` to match the richer manifests or normalize all seven manifests to the schema, then add a manifest validation command to the handoff.

3. Medium - `schema-toolsmith`: the normalized run-result schema cannot encode the planned blinded `W_score` review rubric. The plan defines `W_score` as verifier success plus a normalized 0-to-3 mergeability grade (`docs/experiments/core-narrative-experiment-plan.md:637` through `:644`). The delivered schema only allows string labels for `review.mergeability_grade` (`/Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/experiments/core_narrative/schemas/run_result.schema.json:113` through `:124`). That leaves the W-score formula ambiguous and risks non-comparable analysis later. Action: store the 0-to-3 grade directly, or define and document an explicit numeric mapping before any held-out work review.

4. Medium - `repo-scout` and `general-benchmark`: two acceptance locks remain unresolved and must not be silently treated as complete. `repo-scout` records that the primary target could not be cloned or timed locally because DNS resolution failed (`/Users/chenmohan/gits/barcarolle-wt-repo-scout/experiments/core_narrative/configs/target_repositories.yaml:21` through `:32`), while the Phase 1 gate requires the target repository to be cloned and tested locally (`docs/experiments/core-narrative-experiment-plan.md:543` through `:547`). `general-benchmark` freezes a deterministic selection rule but not concrete SWE-Bench Pro instance IDs; its own limitations require materialization and lock before ACUT runs (`/Users/chenmohan/gits/barcarolle-wt-general-benchmark/experiments/core_narrative/configs/general_benchmark.yaml:36` through `:53`, `:136` through `:139`). Action: record local target smoke timing and concrete `G_score` IDs before starting task-pack construction or ACUT runs.

## Integration Recommendation

Do not integrate Wave 0 as a ready execution baseline. It is safe to integrate the delivered branches only as reviewed planning/scaffold work if the coordinator immediately opens targeted revisions for `schema-toolsmith` and `acut-matrix` and records the repo/general-benchmark locks as required pre-run gates.

Do not start task-builder, leakage-auditor, verifier-auditor, or ACUT execution workers until the clean-room workspace leakage and ACUT schema/manifest mismatch are closed.

## Required Closure

- `schema-toolsmith`: fix workspace preparation so future history and target commits are unavailable to ACUTs; add a reproducible self-check for this condition.
- `schema-toolsmith` plus `acut-matrix`: align `acut.schema.json` and all seven ACUT manifests, then validate every manifest in the delivery handoff.
- `schema-toolsmith`: update run-result review fields to support the 0-to-3 blinded mergeability rubric or document an explicit numeric mapping.
- `repo-scout` or coordinator: clone and run a local `pallets/click` smoke/full-suite timing check, or select a fallback if the local runtime is not viable.
- `general-benchmark` or coordinator: materialize and record the locked SWE-Bench Pro instance IDs and any pre-run global-infra replacements before any ACUT patch-generation run.
