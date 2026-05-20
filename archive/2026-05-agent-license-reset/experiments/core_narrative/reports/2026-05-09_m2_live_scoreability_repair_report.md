# M2 Live Scoreability Repair Report

Date: 2026-05-09

## Scope

This is a bounded scoreability repair attempt. It does not claim capability uplift, task-solving improvement, ranking reversal, G_score predictivity, license, admission, or authorization outcomes.

## Prior Live Gate

| Path | Gate | Patch-ready | Invalid rate | Status counts | Failure owners | Failure classes |
| --- | --- | ---: | ---: | --- | --- | --- |
| `patch_or_files_v1_live` | `failed` | 0.0% | 83.3% | `{'infra_failed': 1, 'invalid_submission': 5}` | `{'infrastructure': 1, 'model_output': 5}` | `{'invalid_unified_diff': 2, 'none': 1, 'unsupported_patch_response': 3}` |
| `structured_files_json_v1_live` | `failed` | 33.3% | 66.7% | `{'failed': 2, 'invalid_submission': 4}` | `{'candidate_patch': 2, 'model_output': 4}` | `{'none': 2, 'unsafe_generated_text': 4}` |

## Local Repair

- `patch-or-files-v1` now accepts Codex `*** Begin Patch` transcripts when hunks match the prepared workspace exactly.
- Failed apply-patch transcript replays are classified as model-output `invalid_submission`, not infrastructure failures.
- Malformed unified diffs, provider HTTP failures, and structured full-file artifact-safety blockers remain residual blockers.

## Failure Modes

| Path | Failure class | Concrete mode | Cells | Local status | Residual blocker or limit |
| --- | --- | --- | ---: | --- | --- |
| `patch_or_files_v1_live` | `invalid_unified_diff` | `malformed_unified_diff` | 2 | `not_auto_repaired` | Malformed hunk headers or line counts remain invalid; no semantic auto-rewrite is claimed. |
| `patch_or_files_v1_live` | `none` | `provider_or_runner_infrastructure_failure` | 1 | `not_locally_repaired` | Requires provider/tooling retry evidence; not a parser/applicator repair. |
| `patch_or_files_v1_live` | `unsupported_patch_response` | `codex_apply_patch_transcript_previously_unsupported` | 3 | `locally_repaired_by_parser_applicator_tests` | Future equivalent transcripts are accepted under patch-or-files-v1 when hunks match exactly. |
| `structured_files_json_v1_live` | `unsafe_generated_text` | `structured_full_file_patch_artifact_full_url_overbreadth` | 4 | `classified_not_repaired` | No safe verifier-ready patch artifact was produced; preserve no-raw-URL/no-secret artifact policy. |

## Live Smoke

Status: `completed`. Model call made: `True`. Total cells: `1`. Status counts: `{'invalid_submission': 1}`.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_live_scoreability_repair.py \
  --m2-summary experiments/core_narrative/results/m2_scoreability_summary_20260509.json \
  --unsafe-triage experiments/core_narrative/results/unsafe_generated_text_triage_20260509.json \
  --live-smoke-batch experiments/core_narrative/results/codex_nfl_m2_live_scoreability_repair_smoke_20260509.json \
  --output experiments/core_narrative/results/m2_live_scoreability_repair_20260509.json \
  --report experiments/core_narrative/reports/2026-05-09_m2_live_scoreability_repair_report.md
```

## Limitations

The audit consumes existing redacted artifacts and optional bounded live-smoke evidence. It does not reinterpret no-model evidence as live scoreability and does not turn prior failed cells into capability evidence.
