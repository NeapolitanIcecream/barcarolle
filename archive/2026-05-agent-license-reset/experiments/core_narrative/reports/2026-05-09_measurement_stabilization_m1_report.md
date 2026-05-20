# M1 Measurement Stabilization Report

Date: 2026-05-09

## Research Question

Does the current RWork invalid-submission-heavy result mostly reflect fragility in the anchored search/replace submission contract, and can a direct file-level `structured-files-json-v1` contract raise patch-ready coverage enough to make later G/R/W predictivity experiments meaningful?

The scoped repository-admission story remains: benchmark-to-work mismatch and submission/adapter fragility are first-class admission risks. This step does not claim ranking reversal and does not invent or substitute any G score.

## Preregistered Criteria

Minimum smoke shape: 2 ACUTs x 3 RWork tasks for `structured-files-json-v1`, or a structured blocker artifact if live execution is blocked.

M1 support threshold: compared with the selected anchored baseline cells, the structured contract should reduce `invalid_submission` by at least 25 percentage points and increase patch-ready coverage by at least 25 percentage points. Patch-ready means a verifier-ready patch reached clean replay and produced `passed`, `failed`, or `timeout`.

## Method

Inputs reviewed:

- `/Users/chenmohan/Documents/barcarolle_research_report.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0509-0.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0509-1.md`
- `docs/experiments/core-narrative-experiment-plan.md`
- `experiments/core_narrative/reports/2026-05-08_codex_nfl_predictivity_step7_report.md`
- `experiments/core_narrative/results/codex_nfl_rbench_canonical_matrix_20260508.json`
- `experiments/core_narrative/results/codex_nfl_rwork_canonical_matrix_20260508.json`

Selected RWork cells:

- ACUTs: `cheap-generic-swe`, `cheap-click-specialist`
- Tasks: `click__rwork__003`, `click__rwork__004`, `click__rwork__006`
- Anchored baseline: existing canonical RWork matrix, `anchored-search-replace-json-v3`
- New smoke: live run, `structured-files-json-v1`, attempt 1

Implementation added contract selection to the direct and batch experiment runner paths, preserving separate fresh generation, no-op, and clean verification workspaces. Normalized metadata now carries `submission_contract`, runner identity, failure class, failure owner, patch readiness, prompt/raw-response artifact pointers, clean replay evidence, and `model_call_made`. The summary tool compares an existing anchored canonical matrix subset with a structured-files batch run.

Budget gate:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/llm_budget_gate.py \
  --ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --projected-cost-usd 6 \
  --acut-id cheap-generic-swe \
  --split rwork \
  --attempt 1 \
  --output experiments/core_narrative/results/measurement_stabilization_m1_gate_20260509.json
```

Live structured smoke:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  --run-prefix codex_nfl_m1_structured_20260509 \
  --task-split rwork \
  --tasks click__rwork__003 click__rwork__004 click__rwork__006 \
  --acuts cheap-generic-swe cheap-click-specialist \
  --attempt 1 \
  --mode live \
  --submission-contract structured-files-json-v1 \
  --llm-ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --output experiments/core_narrative/results/codex_nfl_m1_structured_20260509.json \
  --runner-timeout-seconds 900 \
  --install-timeout-seconds 240
```

Summary generation:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/measurement_stabilization_summary.py \
  --anchored-baseline experiments/core_narrative/results/codex_nfl_rwork_canonical_matrix_20260508.json \
  --structured-batch experiments/core_narrative/results/codex_nfl_m1_structured_20260509.json \
  --tasks click__rwork__003 click__rwork__004 click__rwork__006 \
  --acuts cheap-generic-swe cheap-click-specialist \
  --output experiments/core_narrative/results/measurement_stabilization_m1_summary_20260509.json
```

## Data Collected

Artifacts:

- Gate: `experiments/core_narrative/results/measurement_stabilization_m1_gate_20260509.json`
- Structured batch: `experiments/core_narrative/results/codex_nfl_m1_structured_20260509.json`
- M1 summary: `experiments/core_narrative/results/measurement_stabilization_m1_summary_20260509.json`
- Per-cell normalized results: `experiments/core_narrative/results/normalized/codex_nfl_m1_structured_20260509__*__attempt1.json`
- Per-cell raw audit directories: `experiments/core_narrative/results/raw/codex_nfl_m1_structured_20260509__*__attempt1/`

Live execution was not blocked. Six model calls were made under the existing ledger. The gate saw pre-run cumulative estimated cost USD `34.574307` and allowed a projected 6-call run. The ledger cumulative estimate after the live smoke was USD `35.327775`; this is provider-usage-based and not invoice-verified.

One implementation note matters for interpretation: the live batch was run before the direct runner was hardened to classify unsafe generated patch content as `invalid_submission`. The raw batch therefore records three cells as `infra_failed`. The M1 summary reclassifies those cells from their raw patch artifact evidence as `invalid_submission` / `unsafe_generated_text` / `model_output`, and the direct runner now performs that classification at source for future runs.

## Results

| Contract | Total | Status distribution | Failure owner distribution | Failure classes | Invalid rate | Patch-ready coverage |
| --- | ---: | --- | --- | --- | ---: | ---: |
| `anchored-search-replace-json-v3` | 6 | `invalid_submission`: 6 | `model_output`: 6 | `search_replace_old_occurrence_mismatch`: 6 | 1.000000 | 0.000000 |
| `structured-files-json-v1` | 6 | `failed`: 1, `invalid_submission`: 5 | `candidate_patch`: 1, `model_output`: 5 | `none`: 1, `unsafe_generated_text`: 3, `unsupported_patch_response`: 2 | 0.833333 | 0.166667 |

Effect on selected cells:

- `invalid_submission` rate changed by `-0.166667` for structured minus anchored.
- Patch-ready coverage changed by `+0.166667` for structured minus anchored.
- The single patch-ready structured cell reached clean replay and verifier execution, but failed the task verifier.
- No structured cell passed.

## Claim Status

M1 success criterion: not yet testable. The structured contract improved both invalid-submission rate and patch-ready coverage directionally, but by 16.7 percentage points each, below the preregistered 25 percentage point threshold.

Broader repository-admission risk story: supported. The baseline anchored cells all failed on `search_replace_old_occurrence_mismatch`, and the alternate structured contract exposed different adapter/model-output failure modes rather than eliminating fragility. The evidence supports treating submission/adapter stability as a first-class risk before interpreting RWork model quality or running larger predictivity experiments.

## Decision Gate

Do not proceed to larger G/R/W predictivity experiments from this smoke alone. The next gate should first stabilize structured submission enough to make coverage meaningful:

- Future runs should use the hardened direct runner classification for `unsafe_generated_text`.
- Tighten the structured prompt or adapter diagnostics to reduce `unsupported_patch_response` and unsafe generated content.
- Re-run the same 2 x 3 structured smoke with a new run prefix.
- Proceed only if patch-ready coverage rises materially, preferably meeting or exceeding the preregistered 25 percentage point improvement threshold over the anchored baseline.

## Verification

Focused verification passed:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest \
  experiments.core_narrative.tools.test_openclaw_direct_runner \
  experiments.core_narrative.tools.test_codex_nfl_experiment_runner \
  experiments.core_narrative.tools.test_measurement_stabilization_summary

PYTHONPATH=experiments/core_narrative/tools python3 -m unittest \
  experiments.core_narrative.tools.test_barcarolle_patch_command \
  experiments.core_narrative.tools.test_acut_patch_adapter

PYTHONPATH=experiments/core_narrative/tools python3 -m py_compile \
  experiments/core_narrative/tools/openclaw_direct_runner.py \
  experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  experiments/core_narrative/tools/measurement_stabilization_summary.py \
  experiments/core_narrative/tools/codex_nfl_direct_runner.py
```
