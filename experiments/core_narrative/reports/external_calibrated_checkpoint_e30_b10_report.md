# External Calibrated Checkpoint E30 B10

Status: `paused_after_modified_plan_checkpoint`
Protocol: `external-calibrated-repo-benchmark-v1`
Generated at: `2026-05-16T17:05:38.653831Z`

## Modified Plan

- E tasks completed through ordinal `30`: `180` ACUT-task cells.
- B tasks completed through ordinal `10`: `60` ACUT-task cells.
- The original full-E spread gate remains incomplete; B10 was run under the user-authorized modified plan.
- Experiment is paused at this checkpoint; no additional cells were started after B10.

## E First30

- Resolved: `101` / `180` (`0.561111`)
- Empty patches: `9`
- External verifier infra errors: `0`
- E spread gate ready: `false` (`only_180_of_288_phase2_cells_scored`)

| ACUT | Resolved | Rate | Empty patches | Infra errors |
| --- | ---: | ---: | ---: | ---: |
| `A0` | `16` / `30` | `0.533333` | `1` | `0` |
| `A1` | `15` / `30` | `0.5` | `2` | `0` |
| `A2` | `16` / `30` | `0.533333` | `2` | `0` |
| `A3` | `19` / `30` | `0.633333` | `0` | `0` |
| `A4` | `18` / `30` | `0.6` | `1` | `0` |
| `A5` | `17` / `30` | `0.566667` | `3` | `0` |

## B First10

- Resolved: `14` / `60` (`0.233333`)
- External verifier infra errors: `0`
- Status counts: `verified_pass=14`, `verified_fail=46`

| ACUT | Resolved | Rate | Infra errors |
| --- | ---: | ---: | ---: |
| `A0` | `2` / `10` | `0.2` | `0` |
| `A1` | `3` / `10` | `0.3` | `0` |
| `A2` | `3` / `10` | `0.3` | `0` |
| `A3` | `2` / `10` | `0.2` | `0` |
| `A4` | `2` / `10` | `0.2` | `0` |
| `A5` | `2` / `10` | `0.2` | `0` |

## Validation

- Public marker scan: `passed`, no raw private path or private filename markers.
- Private content scan: `passed`, `0` hits across statement snippets, raw commits, and private patch/log snippets.
- Focused pytest: `52 passed`, `1` warning from system Python LibreSSL/urllib3 compatibility.
- Process cleanup: `passed`, `0` residual experiment processes.

## Public Artifacts

- `e_first30_summary_json`: `experiments/core_narrative/results/external_e_primary/external_calibrated_e_phase2_first30_score_summary_20260516.json`
- `e_first30_summary_report`: `experiments/core_narrative/reports/external_e_phase2_first30_score_summary_report.md`
- `b_first10_summary_json`: `experiments/core_narrative/results/external_b_pilot/external_calibrated_b_pilot_first10_summary_20260516.json`
- `b_first10_summary_report`: `experiments/core_narrative/reports/external_b_pilot_first10_summary_report.md`
- `checkpoint_json`: `experiments/core_narrative/results/external_checkpoint/external_calibrated_checkpoint_e30_b10_20260516.json`
- `checkpoint_report`: `experiments/core_narrative/reports/external_calibrated_checkpoint_e30_b10_report.md`

## Privacy Boundary

Public artifacts record status, counts, scores, and digests only. Raw statements, base commits, reference or gold material, candidate patches, hidden verifier material, and verifier outputs are not recorded publicly.
