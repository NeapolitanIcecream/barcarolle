# Process

status: delivered
updated: 2026-04-29T11:24:00+08:00

## Summary

Delivered the pre-execution ACUT redesign requested after the GPT-5.5-Pro design
review. Active ACUTs are now the 2x2 core: `frontier-generic-swe`,
`frontier-click-specialist`, `cheap-generic-swe`, and
`cheap-click-specialist`. Broad ACUT execution, execution-start preflight, live
model calls, and live patch-generation attempts were not started.

## Owned Paths

- `experiments/core_narrative/configs/acuts/**`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `experiments/core_narrative/configs/llm_access.yaml`
- `experiments/core_narrative/tools/_llm_budget.py`
- `experiments/core_narrative/reports/acut_matrix_notes.md`
- `.codex-workflows/core-narrative-experiment/shared/llm-access-budget-contract.md`
- `.codex-workflows/core-narrative-experiment/workers/acut-2x2-redesign/process.md`

## Files Changed Or Inspected

Changed:

- Deleted retired active manifests:
  - `experiments/core_narrative/configs/acuts/general-benchmark-optimized.yaml`
  - `experiments/core_narrative/configs/acuts/repo-context-heavy.yaml`
  - `experiments/core_narrative/configs/acuts/retrieval-sparse-symbolic.yaml`
  - `experiments/core_narrative/configs/acuts/lower-budget-fast-path.yaml`
- Added active 2x2 manifests:
  - `experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml`
  - `experiments/core_narrative/configs/acuts/frontier-click-specialist.yaml`
  - `experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml`
  - `experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml`
- Updated:
  - `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
  - `experiments/core_narrative/configs/llm_access.yaml`
  - `experiments/core_narrative/tools/_llm_budget.py`
  - `experiments/core_narrative/reports/acut_matrix_notes.md`
  - `.codex-workflows/core-narrative-experiment/shared/llm-access-budget-contract.md`
  - `.codex-workflows/core-narrative-experiment/workers/acut-2x2-redesign/process.md`

Inspected:

- `.codex-workflows/core-narrative-experiment/coordinator.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
- `.codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke/process.md`
- `.codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke-reviewer/process.md`
- `.codex-workflows/core-narrative-experiment/workers/task-manifests-reviewer/process.md`
- existing ACUT manifests and ACUT schema/validator
- `experiments/core_narrative/configs/general_benchmark.yaml`

## Current Blockers

Focused review is required before the coordinator can treat the 2x2 redesign as
integrated for execution-start preflight. `patch_generation_command_gap` remains
open until the separate `patch-command-contract` worker delivers and passes
review.

## Checks Run

- `PYTHONPYCACHEPREFIX=/tmp/core-narrative-acut-2x2-pycache python3 experiments/core_narrative/tools/validate_acut_manifest.py experiments/core_narrative/configs/acuts --output /tmp/core-narrative-acut-2x2-validation.json`
  - Result: passed; 7 manifests valid, 0 invalid.
- Parsed `experiments/core_narrative/configs/core_subset_run_manifest.yaml` with Python YAML.
- Parsed `experiments/core_narrative/configs/llm_access.yaml` with Python YAML.

## Handoff

Ready for focused review. The reviewer should verify that the active core is a
clean 2x2 design, that same-tier pairs differ only by generic-vs-Click policy,
that pilot execution is 28 runs before any full-core decision, that deferred
ACUTs remain deferred, and that no execution/model-call gate has been opened.
