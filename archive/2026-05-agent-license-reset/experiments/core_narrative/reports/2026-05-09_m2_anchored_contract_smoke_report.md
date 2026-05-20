# M2 Anchored Contract Scoreability Smoke

Date: 2026-05-09

## Scope

- Contract: `anchored-search-replace-json-v3`.
- Fixture denominator: `5`; prior M2 denominator: `6`.
- Fixture replay made no model calls and ran no verifier.

## Fixture Matrix

| Fixture | Status | Owner | Class | Patch-ready | Clean replay | Intent |
| --- | --- | --- | --- | ---: | --- | --- |
| `exact_anchored_search_text` | `patch_ready` | `candidate_patch` | `None` | `True` | `applied_to_clean_workspace` | exact immediate anchor isolates repeated Click-shaped old text |
| `ambiguous_anchor` | `invalid_submission` | `model_output` | `search_replace_anchor_mismatch` | `False` | `not_attempted_after_invalid_submission` | non-isolating immediate anchor is a model-output invalid submission |
| `stale_anchor` | `invalid_submission` | `model_output` | `search_replace_anchor_mismatch` | `False` | `not_attempted_after_invalid_submission` | stale anchor beside otherwise unique old text is rejected with hashed diagnostics |
| `redacted_source_text` | `invalid_submission` | `model_output` | `unsafe_generated_text` | `False` | `not_attempted_unsafe_patch_artifact` | redacted source text can match raw source, but raw-URL patch artifacts stay blocked |
| `missing_raw_artifact` | `missing_replay_input` | `infrastructure` | `missing_raw_response_artifact` | `False` | `not_attempted_missing_input` | missing raw response artifact remains machine-readable missing input |

## Aggregate

- Patch-ready coverage: 20.0% (`1` of `5`).
- Status counts: `{'invalid_submission': 3, 'missing_replay_input': 1, 'patch_ready': 1}`.
- Failure classes: `{'missing_raw_response_artifact': 1, 'none': 1, 'search_replace_anchor_mismatch': 2, 'unsafe_generated_text': 1}`.

## Diagnostics

- Exact search-text diagnostic rows: `4`.
- Ambiguous-anchor diagnostic rows: `1`.
- Stale-anchor diagnostic rows: `1`.
- Redacted-source diagnostic rows: `1`.
- Missing raw artifact rows: `1`.
- Source content recorded in diagnostics: `False`.

## Live Smoke

Status: `completed`. Model call made: `True`. Total cells: `1`. Status counts: `{'invalid_submission': 1}`. Failure classes: `{'search_replace_old_occurrence_mismatch': 1}`. Contract: `anchored-search-replace-json-v3`.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_anchored_contract_smoke.py \
  --m2-summary experiments/core_narrative/results/m2_scoreability_summary_20260509.json \
  --run-prefix m2_anchored_contract_smoke_20260509 \
  --raw-root experiments/core_narrative/results/raw \
  --workspace-root experiments/core_narrative/workspaces \
  --live-smoke-batch experiments/core_narrative/results/m2_anchored_contract_live_smoke_20260509.json \
  --force \
  --output experiments/core_narrative/results/m2_anchored_contract_smoke_20260509.json \
  --report experiments/core_narrative/reports/2026-05-09_m2_anchored_contract_smoke_report.md
```

## Claim Boundaries

This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization. It only reports anchored-contract parser/applicator scoreability evidence and the separately attached bounded live-smoke status.
