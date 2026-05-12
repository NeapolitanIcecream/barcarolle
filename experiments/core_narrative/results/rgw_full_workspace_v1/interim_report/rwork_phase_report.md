# RGW-full-workspace-v1 Interim RBench/RWork Report

Generated 2026-05-12. This is an interim report for the completed RBench and completed RWork portions of RGW-full-workspace-v1.

G is not run or scored in this interim report. The bundle contains G-related global-infrastructure placeholder records from the worker's pre-run G6 checks, but this report treats those as out of scope for the RBench/RWork interim scores. No new G attempt was run for this report.

Old M2, M3, and M2.5 artifacts are historical only. They are not used in the primary denominators, primary scores, normalized matrix tables, or cost summaries below.

## Design Freeze

The frozen design is `RGW-full-workspace-v1`, with `schema_version` `core-narrative.rgw-full-workspace-v1`, `status` `frozen`, and `frozen_at` `2026-05-12T00:00:00+08:00`. The primary execution path is `experiments/core_narrative/tools/workspace_mode_runner.py`. The run uses one primary attempt per ACUT/task cell, no best-of-n selection, and fixed denominators.

The ACUT set is fixed at four systems:

| ACUT id | Short label |
|---|---:|
| `cheap-generic-swe` | CG |
| `cheap-click-specialist` | CC |
| `frontier-generic-swe` | FG |
| `frontier-click-specialist` | FC |

The primary matrix order is RBench, RWork, then G. The full frozen matrix expected 80 cells: 32 RBench, 24 RWork, and 24 G. This interim report covers the 56 completed RBench/RWork cells only.

| Split | Manifest | Task count | ACUTs | Covered cells | Included here |
|---|---|---:|---:|---:|---|
| RBench | `configs/tasks/rbench_click.yaml` | 8 | 4 | 32 | yes |
| RWork | `configs/tasks/rwork_click.yaml` | 6 | 4 | 24 | yes |
| G | `configs/general_benchmark.yaml` / G6 | 6 | 4 | 0 scored here | no |

## Task Matrix Covered

RBench uses historical Click behavior tasks. The eight covered task families are:

| Task | Family |
|---|---|
| `click__rbench__001` | option help/default rendering |
| `click__rbench__002` | CliRunner exception handling |
| `click__rbench__003` | prompt choice rendering |
| `click__rbench__004` | CliRunner stdout/stderr stream separation |
| `click__rbench__005` | Choice type case sensitivity |
| `click__rbench__006` | DateTime parameter parsing |
| `click__rbench__007` | CliRunner return value capture |
| `click__rbench__008` | optional value prompts |

RWork uses recent Click maintainer-style behavior tasks. The six covered task families are:

| Task | Family |
|---|---|
| `click__rwork__001` | flag envvar/default/type reconciliation |
| `click__rwork__002` | CliRunner EOF and stdin file handling |
| `click__rwork__003` | default handling for shared flag parameters |
| `click__rwork__004` | callable flag_value default handling |
| `click__rwork__005` | CliRunner debugger stream isolation |
| `click__rwork__006` | default value passing and flag activation |

## Status Semantics

The status semantics are fixed by the RGW status helper and configuration:

| Status | Primary treatment |
|---|---|
| `verified_pass` | pass; contributes 1 to the fixed denominator score |
| `verified_fail` | ACUT failure; contributes 0 |
| `no_diff` | ACUT failure; contributes 0 |
| `timeout` with `timeout_owner` `acut` | ACUT failure; contributes 0 |
| `unsafe_or_scope_violation` | ACUT failure; contributes 0 |
| `acut_command_error` | ACUT failure; contributes 0 |
| `timeout` with verifier or unknown owner | infrastructure status requiring rerun or recorded global exclusion |
| `verifier_infra_error` | infrastructure status requiring rerun or recorded global exclusion |
| `base_tree_mismatch` | infrastructure status requiring rerun or recorded global exclusion |
| `candidate_patch_extraction_error` | infrastructure status requiring rerun or recorded global exclusion |
| `patch_apply_error` | triage-paused status before primary scoring; not counted as an ACUT failure without triage |

In the completed primary RBench/RWork cells, the observed statuses are `verified_pass`, `verified_fail`, `no_diff`, and `unsafe_or_scope_violation`. There are no primary RBench/RWork cells with `timeout`, `patch_apply_error`, `verifier_infra_error`, `base_tree_mismatch`, `candidate_patch_extraction_error`, or `acut_command_error`.

## RBench Summary

RBench is complete with 32 primary cells: 15 `verified_pass` and 17 `verified_fail`. The fixed denominator is 32 and the effective denominator after recorded global infrastructure exclusions remains 32.

| ACUT | Passes | Denominator | Score | Status counts |
|---|---:|---:|---:|---|
| `cheap-generic-swe` | 2 | 8 | 25.0% | `verified_pass`: 2; `verified_fail`: 6 |
| `cheap-click-specialist` | 3 | 8 | 37.5% | `verified_pass`: 3; `verified_fail`: 5 |
| `frontier-generic-swe` | 5 | 8 | 62.5% | `verified_pass`: 5; `verified_fail`: 3 |
| `frontier-click-specialist` | 5 | 8 | 62.5% | `verified_pass`: 5; `verified_fail`: 3 |

## RWork Summary

RWork is complete with 24 primary cells: 8 `verified_pass`, 4 `verified_fail`, 3 `no_diff`, and 9 `unsafe_or_scope_violation`. The fixed denominator is 24 and the effective denominator after recorded global infrastructure exclusions remains 24.

| ACUT | Passes | Denominator | Score | Status counts |
|---|---:|---:|---:|---|
| `cheap-generic-swe` | 2 | 6 | 33.3333% | `verified_pass`: 2; `no_diff`: 1; `unsafe_or_scope_violation`: 3 |
| `cheap-click-specialist` | 2 | 6 | 33.3333% | `verified_pass`: 2; `verified_fail`: 2; `unsafe_or_scope_violation`: 2 |
| `frontier-generic-swe` | 2 | 6 | 33.3333% | `verified_pass`: 2; `verified_fail`: 1; `unsafe_or_scope_violation`: 3 |
| `frontier-click-specialist` | 2 | 6 | 33.3333% | `verified_pass`: 2; `verified_fail`: 1; `no_diff`: 2; `unsafe_or_scope_violation`: 1 |

## Normalized Matrix Excerpt

The table below is the complete RBench/RWork normalized status matrix. `P` means `verified_pass`; `F` means `verified_fail`; `ND` means `no_diff`; `USV` means `unsafe_or_scope_violation`.

| Split | Task | CG | CC | FG | FC |
|---|---|---|---|---|---|
| RBench | `click__rbench__001` | F | F | F | F |
| RBench | `click__rbench__002` | P | P | P | P |
| RBench | `click__rbench__003` | F | F | P | P |
| RBench | `click__rbench__004` | F | F | F | F |
| RBench | `click__rbench__005` | P | P | P | P |
| RBench | `click__rbench__006` | F | F | P | P |
| RBench | `click__rbench__007` | F | P | P | P |
| RBench | `click__rbench__008` | F | F | F | F |
| RWork | `click__rwork__001` | ND | F | F | ND |
| RWork | `click__rwork__002` | P | P | P | P |
| RWork | `click__rwork__003` | USV | P | USV | P |
| RWork | `click__rwork__004` | USV | USV | USV | USV |
| RWork | `click__rwork__005` | P | F | P | F |
| RWork | `click__rwork__006` | USV | USV | USV | ND |

The normalized matrix source is `results/rgw_full_workspace_v1/normalized_result_matrix.json`, with 80 total records in the full bundle and 56 records used here. The raw artifacts manifest reports 80 normalized results, 80 run ids, and 150,795 raw artifact files in the full run bundle.

## Infra Reruns And Exclusions

The primary RBench/RWork cells listed above do not include infrastructure statuses. Two archived RWork infra rerun groups are present and should be treated as audit context rather than primary scored cells:

| Archived rerun group | Cells | Observed blocker | Treatment |
|---|---:|---|---|
| `20260512_python39_click_install_failure` | 2 | Click editable install failed under Python 3.9.6 with `Package 'click' requires a different Python: 3.9.6 not in '>=3.10'` | archived infra rerun; excluded from primary scores |
| `20260512_uv_python314_ensurepip_failure` | 2 | uv-selected Python 3.14 failed while creating `.venv`; `ensurepip --upgrade --default-pip` exited non-zero | archived infra rerun; excluded from primary scores |

The full result bundle also records 24 G-axis `verifier_infra_error` cells because the G6 gold-patch smoke was blocked before ACUT patch generation by missing SWE-Bench Pro dataset cache and missing evaluator checkout. Those records are not included in the interim RBench/RWork scores. This report does not zero-fill G and does not use the G fixed denominator as a score input.

## Cost Metadata

Cost metadata is estimated because the Codex CLI patch command summaries do not expose provider token usage. Actual token-level cost is not available in the artifacts.

| Scope | Rows | Model-call rows | Estimated cost |
|---|---:|---:|---:|
| RBench | 32 | 32 | $64 |
| RWork | 24 | 24 | $48 |
| RBench + RWork | 56 | 56 | $112 |
| Full bundle including unrun G placeholders | 80 | 56 | $112 |

By ACUT across RBench/RWork:

| ACUT | Rows | Model-call rows | Estimated cost |
|---|---:|---:|---:|
| `cheap-generic-swe` | 14 | 14 | $14 |
| `cheap-click-specialist` | 14 | 14 | $14 |
| `frontier-generic-swe` | 14 | 14 | $42 |
| `frontier-click-specialist` | 14 | 14 | $42 |

The 24 G placeholder rows have `model_call_made: false`, estimated cost `$0`, and cost source `not_run_due_to_global_infrastructure_blocker`.

## Interpretation Limits

The RBench/RWork result pattern is descriptive, not a final ranking claim. RBench separates the frontier ACUTs from the cheap ACUTs in this Click task pack. RWork ties all four ACUTs at 2/6, and any rank order inside RWork is therefore tie-ordering rather than a substantive score difference.

No ranking-reversal claim should be overstated at this stage for four reasons. First, G is not run or scored here. Second, RWork has identical headline scores for all four ACUTs. Third, the report covers one repository family, Click, for RBench/RWork. Fourth, each ACUT/task cell has one attempt, so variance is not estimated.

## Reproducibility Notes

The primary command result records `results_written: 80`, `phase: primary`, `mode: live`, and `summary_status: primary_incomplete_or_infra_blocked` for the full bundle. For this interim report, the reproducible score inputs are:

| Artifact | Use in this report |
|---|---|
| `summary.json` | split-level status counts and denominator readiness |
| `grw_table.json` | per-ACUT RBench/RWork scores and status counts |
| `normalized_result_matrix.json` | cell-level RBench/RWork status matrix |
| `cost_ledger.jsonl` | estimated cost metadata |
| `infra_reruns_exclusions.json` | G-axis global infra exclusion records, not R/W score inputs |
| `infra_reruns/` | archived RWork infra rerun attempts, not primary score inputs |
| `reports/threats_to_validity.md` | artifact-level limitations |

The report intentionally avoids mixing historical M2, M3, or M2.5 artifacts into these tables.
