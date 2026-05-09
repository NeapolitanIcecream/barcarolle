# M2 Anchored Contract Scoreability Smoke

Date: 2026-05-10

## Scope

- Contract: `anchored-search-replace-json-v3`.
- Repair focus: `anchored_old_occurrence_repair`.
- Fixture denominator: `7`; prior M2 denominator: `6`.
- Fixture replay made no model calls and ran no verifier.

## Fixture Matrix

| Fixture | Status | Owner | Class | Patch-ready | Clean replay | Intent |
| --- | --- | --- | --- | ---: | --- | --- |
| `exact_anchored_search_text` | `patch_ready` | `candidate_patch` | `None` | `True` | `applied_to_clean_workspace` | exact immediate anchor isolates repeated Click-shaped old text |
| `repeated_old_missing_anchors` | `invalid_submission` | `model_output` | `search_replace_old_occurrence_mismatch` | `False` | `not_attempted_after_invalid_submission` | repeated old text without immediate anchors is a model-output invalid submission |
| `stale_old_text` | `invalid_submission` | `model_output` | `search_replace_old_occurrence_mismatch` | `False` | `not_attempted_after_invalid_submission` | old text copied from a stale Click variant is diagnosed as zero-occurrence model output |
| `ambiguous_anchor` | `invalid_submission` | `model_output` | `search_replace_anchor_mismatch` | `False` | `not_attempted_after_invalid_submission` | non-isolating immediate anchor is a model-output invalid submission |
| `stale_anchor` | `invalid_submission` | `model_output` | `search_replace_anchor_mismatch` | `False` | `not_attempted_after_invalid_submission` | stale anchor beside otherwise unique old text is rejected with hashed diagnostics |
| `redacted_source_text` | `invalid_submission` | `model_output` | `unsafe_generated_text` | `False` | `not_attempted_unsafe_patch_artifact` | redacted source text can match raw source, but raw-URL patch artifacts stay blocked |
| `missing_raw_artifact` | `missing_replay_input` | `infrastructure` | `missing_raw_response_artifact` | `False` | `not_attempted_missing_input` | missing raw response artifact remains machine-readable missing input |

## Aggregate

- Patch-ready coverage: 14.3% (`1` of `7`).
- Status counts: `{'invalid_submission': 5, 'missing_replay_input': 1, 'patch_ready': 1}`.
- Failure classes: `{'missing_raw_response_artifact': 1, 'none': 1, 'search_replace_anchor_mismatch': 2, 'search_replace_old_occurrence_mismatch': 2, 'unsafe_generated_text': 1}`.

## Diagnostics

- Exact search-text diagnostic rows: `6`.
- Ambiguous-anchor diagnostic rows: `1`.
- Stale-anchor diagnostic rows: `1`.
- Repeated-old missing-anchor rows: `1`.
- Stale-old-text rows: `1`.
- Old-occurrence mismatch rows: `2`.
- Old-occurrence rows with hashes: `2`.
- Redacted-source diagnostic rows: `1`.
- Missing raw artifact rows: `1`.
- Source content recorded in diagnostics: `False`.

## Live Smoke

Status: `completed`. Model call made: `True`. Total cells: `1`. Status counts: `{'invalid_submission': 1}`. Failure classes: `{'search_replace_old_occurrence_mismatch': 1}`. Contract: `anchored-search-replace-json-v3`.
Old-occurrence diagnostic summary: `{'row_count': 1, 'diagnostic_code_counts': {'old_text_not_found': 1}, 'failure_class_counts': {'search_replace_old_occurrence_mismatch': 1}, 'old_occurrence_count_buckets': {'0': 1}, 'rows_with_old_text_hash': 1, 'source_content_recorded': False}`.

| ACUT | Task | Class | Code | Old occurrences | Anchor matches | Old hash | Content recorded |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| `cheap-generic-swe` | `click__rwork__006` | `search_replace_old_occurrence_mismatch` | `old_text_not_found` | `0` | `0` | `89a723bdef6ef0ba0019f250f732eaf6cfdadfe983ddffc414a0cabb5cccf382` | `False` |

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_anchored_contract_smoke.py \
  --m2-summary experiments/core_narrative/results/m2_scoreability_summary_20260509.json \
  --run-prefix m2_anchored_occurrence_repair_20260510 \
  --raw-root experiments/core_narrative/results/raw \
  --workspace-root experiments/core_narrative/workspaces \
  --live-smoke-batch experiments/core_narrative/results/m2_anchored_contract_live_smoke_20260509.json \
  --force \
  --output experiments/core_narrative/results/m2_anchored_occurrence_repair_20260510.json \
  --report experiments/core_narrative/reports/2026-05-10_m2_anchored_occurrence_repair_report.md
```

## Claim Boundaries

This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization. It only reports anchored-contract parser/applicator scoreability evidence and the separately attached bounded live-smoke status.
