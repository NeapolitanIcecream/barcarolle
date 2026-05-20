# M1.1 Measurement Stabilization Report

Date: 2026-05-09

## Research Question

After hardening the `structured-files-json-v1` submission path, is structured submission stable enough on the selected RWork smoke cells to justify later G/R/W predictivity work?

This is a measurement-stabilization check only. It does not introduce a G score, run direct G_score tasks, or run SWE-Bench Pro ACUT calls.

## Method

Inputs reviewed before changes:

- `experiments/core_narrative/reports/2026-05-09_measurement_stabilization_m1_report.md`
- `experiments/core_narrative/results/measurement_stabilization_m1_summary_20260509.json`
- `experiments/core_narrative/results/codex_nfl_m1_structured_20260509.json`

Selected cells were unchanged from M1:

- ACUTs: `cheap-generic-swe`, `cheap-click-specialist`
- Tasks: `click__rwork__003`, `click__rwork__004`, `click__rwork__006`
- Anchored baseline: `anchored-search-replace-json-v3` rows from `codex_nfl_rwork_canonical_matrix_20260508.json`
- Structured contract: `structured-files-json-v1`

Implementation changes kept the public contract id unchanged. The structured prompt now explicitly requires raw single-object JSON, rejects prose/markdown/legacy edit keys, warns against URLs/endpoints/credentials, and requires complete final file content. The shared structured-file applicator now rejects obvious incomplete-content placeholders such as `[truncated]`, `<unchanged>`, and "rest of file unchanged" before workspace mutation. Summary generation now requires present `submission_contract` and `output_contract` markers to agree with `structured-files-json-v1`, ignores wrong-contract rows, and caps structured evidence at one record per selected cell.

Budget gate:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/llm_budget_gate.py \
  --ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --projected-cost-usd 6 \
  --acut-id cheap-generic-swe \
  --split rwork \
  --attempt 1 \
  --output experiments/core_narrative/results/measurement_stabilization_m1_1_gate_20260509.json
```

Live structured smoke:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  --run-prefix codex_nfl_m1_1_structured_20260509 \
  --task-split rwork \
  --tasks click__rwork__003 click__rwork__004 click__rwork__006 \
  --acuts cheap-generic-swe cheap-click-specialist \
  --attempt 1 \
  --mode live \
  --submission-contract structured-files-json-v1 \
  --llm-ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --output experiments/core_narrative/results/codex_nfl_m1_1_structured_20260509.json \
  --runner-timeout-seconds 900 \
  --install-timeout-seconds 240
```

Summary generation:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/measurement_stabilization_summary.py \
  --anchored-baseline experiments/core_narrative/results/codex_nfl_rwork_canonical_matrix_20260508.json \
  --structured-batch experiments/core_narrative/results/codex_nfl_m1_1_structured_20260509.json \
  --tasks click__rwork__003 click__rwork__004 click__rwork__006 \
  --acuts cheap-generic-swe cheap-click-specialist \
  --output experiments/core_narrative/results/measurement_stabilization_m1_1_summary_20260509.json
```

## Data Collected

Artifacts:

- Gate: `experiments/core_narrative/results/measurement_stabilization_m1_1_gate_20260509.json`
- Structured batch: `experiments/core_narrative/results/codex_nfl_m1_1_structured_20260509.json`
- M1.1 summary: `experiments/core_narrative/results/measurement_stabilization_m1_1_summary_20260509.json`
- Per-cell normalized results: `experiments/core_narrative/results/normalized/codex_nfl_m1_1_structured_20260509__*__attempt1.json`
- Per-cell raw audit directories: `experiments/core_narrative/results/raw/codex_nfl_m1_1_structured_20260509__*__attempt1/`

The live run was not blocked. The gate saw pre-run cumulative estimated cost USD `35.327775` and allowed the projected USD `6` smoke. Six model calls were made. The ledger cumulative estimate after the run was USD `36.006081`, so the M1.1 run added USD `0.678306` by provider-usage-based estimates. These are provider response usage estimates, not invoice-verified costs.

## Results

| Evidence set | Contract | Total | Status distribution | Failure classes | Invalid rate | Patch-ready coverage |
| --- | --- | ---: | --- | --- | ---: | ---: |
| Anchored baseline | `anchored-search-replace-json-v3` | 6 | `invalid_submission`: 6 | `search_replace_old_occurrence_mismatch`: 6 | 1.000000 | 0.000000 |
| M1 structured | `structured-files-json-v1` | 6 | `failed`: 1, `invalid_submission`: 5 | `none`: 1, `unsafe_generated_text`: 3, `unsupported_patch_response`: 2 | 0.833333 | 0.166667 |
| M1.1 structured | `structured-files-json-v1` | 6 | `failed`: 2, `invalid_submission`: 4 | `none`: 2, `unsafe_generated_text`: 4 | 0.666667 | 0.333333 |

M1.1 cell outcomes:

| Task | ACUT | Status | Patch-ready | Failure owner/class |
| --- | --- | --- | --- | --- |
| `click__rwork__003` | `cheap-generic-swe` | `failed` | yes | `candidate_patch` / `none` |
| `click__rwork__003` | `cheap-click-specialist` | `failed` | yes | `candidate_patch` / `none` |
| `click__rwork__004` | `cheap-generic-swe` | `invalid_submission` | no | `model_output` / `unsafe_generated_text` |
| `click__rwork__004` | `cheap-click-specialist` | `invalid_submission` | no | `model_output` / `unsafe_generated_text` |
| `click__rwork__006` | `cheap-generic-swe` | `invalid_submission` | no | `model_output` / `unsafe_generated_text` |
| `click__rwork__006` | `cheap-click-specialist` | `invalid_submission` | no | `model_output` / `unsafe_generated_text` |

Effect versus anchored baseline:

- Invalid-submission rate changed from `1.000000` to `0.666667`, an improvement of `33.3333` percentage points.
- Patch-ready coverage changed from `0.000000` to `0.333333`, an improvement of `33.3333` percentage points.
- Canonical scoreable coverage was `6/6`; there were no `infra_failed` cells.
- No cell passed the task verifier. The two patch-ready cells reached clean replay and verifier execution, then failed.

## Claim Status

M1.1 claim status: `supported`.

The preregistered support rule required both:

- invalid-submission rate improvement of at least 25 percentage points over anchored baseline;
- patch-ready coverage improvement of at least 25 percentage points over anchored baseline.

M1.1 met both thresholds at `33.3333` percentage points each. The result upgrades the M1 measurement-stabilization claim from directionally improved but below threshold to supported on the fixed 2 x 3 smoke.

## Decision Gate

Structured submission is now stable enough to justify later G/R/W predictivity work under the existing budget and authorization gates. The justification is measurement stability, not task-solving success: the run produced a complete fixed-denominator batch, zero infrastructure failures, correct unsafe-content classification as `invalid_submission` / `unsafe_generated_text`, and enough patch-ready coverage to clear the preregistered threshold.

Proceeding should still preserve the hardened diagnostics and denominator rules. Larger predictivity runs should treat remaining `unsafe_generated_text` prevalence as an active measurement risk, not as solved model quality evidence.

## Verification

Focused verification passed:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/core_narrative/tools python3 -B -m unittest \
  experiments.core_narrative.tools.test_openclaw_direct_runner \
  experiments.core_narrative.tools.test_codex_nfl_experiment_runner \
  experiments.core_narrative.tools.test_measurement_stabilization_summary \
  experiments.core_narrative.tools.test_barcarolle_patch_command \
  experiments.core_narrative.tools.test_acut_patch_adapter
```

Result: `Ran 77 tests ... OK`.

Compile check passed:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 -m py_compile \
  experiments/core_narrative/tools/openclaw_direct_runner.py \
  experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  experiments/core_narrative/tools/measurement_stabilization_summary.py
```

Whitespace check passed:

```bash
git diff --check
```

## Limitations

This is still a 6-cell smoke, not a broad predictivity estimate. The structured contract improved measurement stability but did not produce any passing task outcomes. Four of six M1.1 cells still failed at unsafe generated content, so structured submission is stable enough for the next measurement stage but not free of adapter/model-output fragility. Costs are provider-usage estimates from response metadata and ledger accumulation, not invoice-verified billing.
