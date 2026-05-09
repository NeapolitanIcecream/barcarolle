# M2 Repaired Parser Historical Replay Report

Date: 2026-05-09

## Scope

- Source path: `patch_or_files_v1_live`.
- Fixed denominator: `6` rows; matrix rows: `6`.
- Replay model calls: `False`; replay model spend USD: `0.0`.
- Verifier execution was not run; this measures local parser/applicator scoreability only.

## Old vs Repaired

| Metric | Old | Repaired |
| --- | --- | --- |
| Patch-ready count | `0` | `0` |
| Patch-ready coverage | 0.0% | 0.0% |
| Status counts | `{'infra_failed': 1, 'invalid_submission': 5}` | `{'invalid_submission': 5, 'missing_replay_input': 1}` |
| Failure owners | `{'infrastructure': 1, 'model_output': 5}` | `{'infrastructure': 1, 'model_output': 5}` |
| Failure classes | `{'invalid_unified_diff': 2, 'none': 1, 'unsupported_patch_response': 3}` | `{'apply_patch_context_mismatch': 2, 'invalid_unified_diff': 2, 'missing_raw_response_artifact': 1, 'unsafe_generated_text': 1}` |

## Replay Matrix

| ACUT | Task | Old class | Repaired status | Repaired owner | Repaired class | Patch-ready | Clean replay |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| `cheap-generic-swe` | `click__rwork__003` | `invalid_unified_diff` | `invalid_submission` | `model_output` | `invalid_unified_diff` | `False` | `not_attempted_after_replay_failure` |
| `cheap-generic-swe` | `click__rwork__004` | `invalid_unified_diff` | `invalid_submission` | `model_output` | `invalid_unified_diff` | `False` | `not_attempted_after_replay_failure` |
| `cheap-generic-swe` | `click__rwork__006` | `unsupported_patch_response` | `invalid_submission` | `model_output` | `apply_patch_context_mismatch` | `False` | `not_attempted_after_replay_failure` |
| `cheap-click-specialist` | `click__rwork__003` | `unsupported_patch_response` | `invalid_submission` | `model_output` | `unsafe_generated_text` | `False` | `not_attempted_after_replay_failure` |
| `cheap-click-specialist` | `click__rwork__004` | `unsupported_patch_response` | `invalid_submission` | `model_output` | `apply_patch_context_mismatch` | `False` | `not_attempted_after_replay_failure` |
| `cheap-click-specialist` | `click__rwork__006` | `None` | `missing_replay_input` | `infrastructure` | `missing_raw_response_artifact` | `False` | `not_attempted_missing_input` |

## Context Anchor Diagnostics

- Redacted URL source-context matches: `1`.
- Apply-patch context mismatch rows with line-anchor diagnostics: `2`.
- Diagnostics record file paths, hunk indexes, hashes, line-anchor occurrence counts, and redacted-URL match counts; source content is not recorded in the JSON summary.

## Missing Artifacts

- Raw response artifacts missing: `1`.
- Normalized results missing: `0`.
- Prompt snapshots missing: `0`.
- Batch run results missing: `0`.
- Missing replay inputs: `1`.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_repaired_parser_replay.py \
  --m2-summary experiments/core_narrative/results/m2_scoreability_summary_20260509.json \
  --path-id patch_or_files_v1_live \
  --run-prefix m2_context_anchor_repair_replay_20260509 \
  --force \
  --output experiments/core_narrative/results/m2_context_anchor_repair_replay_20260509.json \
  --report experiments/core_narrative/reports/2026-05-09_m2_context_anchor_repair_replay_report.md
```

## Claim Boundaries

This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization. It only reports whether stored historical outputs are locally patch-ready under the repaired parser/applicator.
