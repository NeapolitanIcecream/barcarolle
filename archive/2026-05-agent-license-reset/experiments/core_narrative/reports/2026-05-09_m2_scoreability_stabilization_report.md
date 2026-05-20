# M2 Scoreability Stabilization Report

Date: 2026-05-09

## Research Question

Can the fixed 2 ACUT x 3 Click RWork smoke become scoreable across multiple submission paths before returning to G/R/W predictivity claims?

This report is scoreability-first measurement evidence only. It makes no capability uplift claim, no task-solving improvement claim, no G_score claim, and no ranking reversal claim.

## Method

Inputs reviewed:

- `/Users/chenmohan/Documents/barcarolle-agent-license-research-report-2026-05-09-v4.md`
- `/Users/chenmohan/Downloads/barcarolle-research-0509-2.md`
- `experiments/core_narrative/reports/2026-05-09_measurement_stabilization_m1_report.md`
- `experiments/core_narrative/reports/2026-05-09_measurement_stabilization_m1_1_report.md`
- `experiments/core_narrative/results/codex_nfl_m1_1_structured_20260509.json`
- `experiments/core_narrative/results/measurement_stabilization_m1_1_summary_20260509.json`

Selected cells:

- ACUTs: `cheap-generic-swe`, `cheap-click-specialist`
- Tasks: `click__rwork__003`, `click__rwork__004`, `click__rwork__006`
- Fixed denominator per path: 6 cells

Compared paths:

1. Reused M1.1 live `structured-files-json-v1`.
2. New live `patch-or-files-v1`, accepting raw unified diff, JSON diff keys, or structured files.
3. New no-model `patch-or-files-v1` mock baseline using a synthetic unified diff. This is not a model result and is used only to test patch/replay readiness because a true live tool-native controller path is not part of this PR.

M2 gate thresholds:

- `patch_ready_coverage >= 0.70`
- `invalid_submission_rate <= 0.25`
- `clean_replay_disagreement_count == 0`

## Commands

Budget gate:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/llm_budget_gate.py \
  --ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --projected-cost-usd 6 \
  --acut-id cheap-generic-swe \
  --split rwork \
  --attempt 1 \
  --output experiments/core_narrative/results/m2_scoreability_patch_or_files_gate_20260509.json
```

Live patch-or-files run:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  --run-prefix codex_nfl_m2_patch_or_files_20260509 \
  --task-split rwork \
  --tasks click__rwork__003 click__rwork__004 click__rwork__006 \
  --acuts cheap-generic-swe cheap-click-specialist \
  --attempt 1 \
  --mode live \
  --submission-contract patch-or-files-v1 \
  --llm-ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --output experiments/core_narrative/results/codex_nfl_m2_patch_or_files_20260509.json \
  --runner-timeout-seconds 900 \
  --install-timeout-seconds 240
```

No-model replay baseline:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  --run-prefix codex_nfl_m2_patch_or_files_no_model_20260509 \
  --task-split rwork \
  --tasks click__rwork__003 click__rwork__004 click__rwork__006 \
  --acuts cheap-generic-swe cheap-click-specialist \
  --attempt 1 \
  --mode mock \
  --submission-contract patch-or-files-v1 \
  --llm-ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --output experiments/core_narrative/results/codex_nfl_m2_patch_or_files_no_model_20260509.json \
  --runner-timeout-seconds 360 \
  --install-timeout-seconds 240
```

Summary:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_scoreability_summary.py \
  --tasks click__rwork__003 click__rwork__004 click__rwork__006 \
  --acuts cheap-generic-swe cheap-click-specialist \
  --evidence structured_files_json_v1_live structured-files-json-v1 batch experiments/core_narrative/results/codex_nfl_m1_1_structured_20260509.json \
  --evidence patch_or_files_v1_live patch-or-files-v1 batch experiments/core_narrative/results/codex_nfl_m2_patch_or_files_20260509.json \
  --evidence patch_or_files_v1_no_model patch-or-files-v1 batch experiments/core_narrative/results/codex_nfl_m2_patch_or_files_no_model_20260509.json \
  --output experiments/core_narrative/results/m2_scoreability_summary_20260509.json
```

## Artifacts

- Gate: `experiments/core_narrative/results/m2_scoreability_patch_or_files_gate_20260509.json`
- Live patch-or-files batch: `experiments/core_narrative/results/codex_nfl_m2_patch_or_files_20260509.json`
- No-model baseline batch: `experiments/core_narrative/results/codex_nfl_m2_patch_or_files_no_model_20260509.json`
- M2 summary: `experiments/core_narrative/results/m2_scoreability_summary_20260509.json`
- Per-cell normalized results: `experiments/core_narrative/results/normalized/codex_nfl_m2_patch_or_files*_20260509__*__attempt1.json`
- Per-cell raw audit directories: `experiments/core_narrative/results/raw/codex_nfl_m2_patch_or_files*_20260509__*__attempt1/`

The live budget gate passed with no blockers and no approvals required. The pre-run cumulative estimate was USD `36.006081`; after the live patch-or-files run it was USD `37.441666`, a provider-usage/local-projected estimate delta of USD `1.435585`. The no-model baseline added six zero-cost ledger records.

## Results

| Path | Model calls | Status counts | Failure owner/classes | Patch-ready | Invalid rate | Clean replay success | Gate |
| --- | ---: | --- | --- | ---: | ---: | ---: | --- |
| `structured_files_json_v1_live` | 6 | `failed`: 2, `invalid_submission`: 4 | owner `candidate_patch`: 2, `model_output`: 4; class `unsafe_generated_text`: 4 | 0.333333 | 0.666667 | 0.333333 | failed |
| `patch_or_files_v1_live` | 6 | `invalid_submission`: 5, `infra_failed`: 1 | owner `model_output`: 5, `infrastructure`: 1; classes `invalid_unified_diff`: 2, `unsupported_patch_response`: 3, `none`: 1 | 0.000000 | 0.833333 | 0.000000 | failed |
| `patch_or_files_v1_no_model` | 0 | `failed`: 6 | owner `candidate_patch`: 6 | 1.000000 | 0.000000 | 1.000000 | passed |

All three paths had zero missing cells and zero clean replay disagreements. Wrong-contract exclusions were zero in the delivered summary.

## Interpretation

M2 did not pass the scoreability readiness gate for live model submissions. `structured-files-json-v1` remains below the patch-ready threshold and above the invalid threshold. The new live `patch-or-files-v1` path performed worse on scoreability than the reused structured path, producing no verifier-ready patches and one provider/infrastructure failure.

The no-model `patch-or-files-v1` baseline passed the gate because all six synthetic patches applied in clean replay and reached verifier execution. Those six verifier failures are expected and do not measure ACUT capability. They show that the patch collection, clean replay, and verifier plumbing can score a valid patch artifact on the fixed smoke when the model-output layer is removed.

The most specific M2 conclusion is therefore:

> Scoreability is not yet restored for live model submissions on the selected RWork smoke. The current limiting factor is live output/provider behavior, not the clean replay/verifier path.

## Claim Status

M2 claim status: `scoreability_gate_not_met`.

Supported:

- Fixed-denominator multi-path summary tooling exists and reports patch-ready coverage, invalid-submission rate, clean replay success/readiness, failure owner/class distributions, missing cells, model-call counts, and gate status.
- The selected 2 x 3 smoke now has three comparable submission-path evidence sets.
- Blocker and wrong-contract handling are executable-tested.
- No-model replay evidence shows the verifier/replay path can score patch-ready artifacts.

Not supported:

- No capability uplift claim.
- No task-solving improvement claim.
- No ranking reversal claim.
- No G/R/W predictivity claim.
- No claim that `patch-or-files-v1` is better than `structured-files-json-v1`.

## Limitations

This remains a 6-cell Click RWork smoke. The no-model baseline uses synthetic comments and is an instrumentation baseline only. One live `patch-or-files-v1` cell hit an HTTP 500/provider failure and is classified as infrastructure-owned. Provider costs are response-usage or local projected estimates, not invoice-verified billing.

## Next Steps

1. Triage the five live `patch-or-files-v1` model-output failures by inspecting redacted raw response shape only enough to separate corrupt unified diffs, prose/no patch, and files-contract drift.
2. Decide whether to harden `patch-or-files-v1` prompting/parsing or prefer structured-files as the next live path.
3. Add a true tool-native controller path only if it can preserve the same fixed denominator, clean replay boundary, and no-secret artifact policy.
4. Re-run the 2 x 3 smoke only after a concrete output-contract fix, and proceed to predictivity work only when a live path meets the M2 gate.

## Verification

Focused verification was run after implementation and artifact generation:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/core_narrative/tools python3 -B -m unittest experiments.core_narrative.tools.test_m2_scoreability_summary
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/core_narrative/tools python3 -B -m unittest experiments.core_narrative.tools.test_codex_nfl_experiment_runner.CodexNflExperimentRunnerTests.test_patch_or_files_mock_response_uses_unified_diff_contract
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/core_narrative/tools python3 -B -m unittest experiments.core_narrative.tools.test_openclaw_direct_runner.OpenClawDirectRunnerTests.test_patch_or_files_contract_accepts_unified_diff_mock_response
PYTHONPATH=experiments/core_narrative/tools python3 -m py_compile experiments/core_narrative/tools/m2_scoreability_summary.py experiments/core_narrative/tools/openclaw_direct_runner.py experiments/core_narrative/tools/codex_nfl_experiment_runner.py
```

Final verification commands and `git diff --check` are recorded in the worker handoff.
