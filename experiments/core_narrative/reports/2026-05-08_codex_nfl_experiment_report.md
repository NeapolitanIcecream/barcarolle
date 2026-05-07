# 2026-05-08 Codex NFL Core-Narrative Experiment Report

status: `delivered`
updated: 2026-05-07T20:13:00+08:00
repo: `/Users/chenmohan/gits/barcarolle`
primary_runner: `codex-nfl-batch-v1` plus `codex-nfl-direct-search-replace-v1`

## Executive Summary

Codex resumed ownership of the Barcarolle core-narrative experiment and bypassed the brittle Codex CLI/OpenClaw control planes. The new Codex-owned direct runner produced 9 live scoreable RBench Click results across 3 tasks and 3 ACUTs:

- total live Codex-owned runs: 9
- scoreable verifier results: 9
- passed: 6
- failed: 3
- infra_failed: 0

The result supports the NFL-style Barcarolle story. The box score says every tested ACUT went 2/3. The film says more: task 001 and task 002 were solved after better context packaging and a verifier repair, while all task 003 runs produced plausible prompt-choice patches that failed repo-specific hidden verifier behavior.

## Facilities

Retained:

- reviewed task and ACUT manifests;
- historical base-tree workspace preparation;
- hidden verifier wrapper model;
- exact search/replace patch artifact contract;
- normalized run-result schema;
- cost ledgering, redaction, prompt snapshots, raw response artifacts.

Bypassed:

- old tmux work/review-loop execution as a control plane;
- Codex CLI streaming/output-contract path;
- OpenClaw as the primary route.

Rewritten or added:

- `experiments/core_narrative/tools/codex_nfl_direct_runner.py`
- `experiments/core_narrative/tools/codex_nfl_experiment_runner.py`
- `experiments/core_narrative/tools/test_codex_nfl_direct_runner.py`
- `experiments/core_narrative/tools/openclaw_direct_runner.py` historical Click layout guard and wrong-path classifier

Verifier repair:

- `click__rbench__002` referenced `test_catch_exceptions_cli_runner`, but the packaged hidden target file only contains `test_catch_exceptions`.
- Fixed `experiments/core_narrative/configs/tasks/rbench_click.yaml` and `experiments/core_narrative/tasks/click/rbench/click__rbench__002/verifier/run.sh`.
- Reran only the affected cheap-generic task-002 verifier. No extra model call or ledger append was made.

## Score Summary

Source of truth: `experiments/core_narrative/results/normalized/codex_nfl_live_summary_20260507.json`.

| ACUT | total | scoreable | passed | failed | pass rate |
|---|---:|---:|---:|---:|---:|
| `cheap-generic-swe` | 3 | 3 | 2 | 1 | 0.6667 |
| `frontier-generic-swe` | 3 | 3 | 2 | 1 | 0.6667 |
| `cheap-click-specialist` | 3 | 3 | 2 | 1 | 0.6667 |
| all | 9 | 9 | 6 | 3 | 0.6667 |

`experiments/core_narrative/results/codex_nfl_live_expand_20260507.json` has a stale in-memory aggregate for the first task-002 run because the verifier was repaired mid-batch. Use the normalized files and `codex_nfl_live_summary_20260507.json` for scoring.

## Run Matrix

| run_id | ACUT | task | status | verifier exit | provider usage cost |
|---|---|---|---|---:|---:|
| `codex_nfl_live_core_20260507__cheap-generic-swe__click__rbench__001__attempt1` | `cheap-generic-swe` | `click__rbench__001` | passed | 0 | 0.024981 |
| `codex_nfl_live_core_20260507__frontier-generic-swe__click__rbench__001__attempt1` | `frontier-generic-swe` | `click__rbench__001` | passed | 0 | 0.09868 |
| `codex_nfl_live_core_20260507__cheap-click-specialist__click__rbench__001__attempt1` | `cheap-click-specialist` | `click__rbench__001` | passed | 0 | 0.02495475 |
| `codex_nfl_live_expand_20260507__cheap-generic-swe__click__rbench__002__attempt1` | `cheap-generic-swe` | `click__rbench__002` | passed | 0 | 0.017181 |
| `codex_nfl_live_expand_20260507__frontier-generic-swe__click__rbench__002__attempt1` | `frontier-generic-swe` | `click__rbench__002` | passed | 0 | 0.11859 |
| `codex_nfl_live_expand_20260507__cheap-click-specialist__click__rbench__002__attempt1` | `cheap-click-specialist` | `click__rbench__002` | passed | 0 | 0.02143425 |
| `codex_nfl_live_expand_20260507__cheap-generic-swe__click__rbench__003__attempt1` | `cheap-generic-swe` | `click__rbench__003` | failed | 1 | 0.046389 |
| `codex_nfl_live_expand_20260507__frontier-generic-swe__click__rbench__003__attempt1` | `frontier-generic-swe` | `click__rbench__003` | failed | 1 | 0.14534 |
| `codex_nfl_live_expand_20260507__cheap-click-specialist__click__rbench__003__attempt1` | `cheap-click-specialist` | `click__rbench__003` | failed | 1 | 0.04125075 |

Each run has raw artifacts under `experiments/core_narrative/results/raw/<run_id>/`, including `prompt.txt`, `prompt_snapshot.json`, `provider_response.redacted.json`, `submission.patch`, `runner_result.json`, verifier stdout/stderr, and command summaries.

## Film Notes

`click__rbench__001`: all three live Codex-owned runs passed. This reversed the earlier OpenClaw failures on the same task by using a Codex-owned direct runner, source/test context, and a historical Click layout guard. The useful lesson is not that the task is easy; the old box score hid that output-contract and path-context plumbing were distorting the play.

`click__rbench__002`: all three corrected verifier outcomes passed. The batch exposed stale verifier plumbing first, then the same patches passed after the verifier was repaired to match the packaged hidden file. This is infrastructure film: the scorer has to match the actual target file before the model result can be interpreted.

`click__rbench__003`: all three runs failed despite plausible patches.

- Cheap generic and frontier generic both implemented choice text in prompt flow but missed the hidden test's repo expectation that `click._termui_impl` be exposed.
- Cheap specialist added prompt-choice rendering but did not plumb `show_choices=False` through `Option.__init__`, so the hidden test failed at option construction.

NFL interpretation: a patch can move the ball and still fail the play. The box score of equal 2/3 ACUT results hides whether a run failed by wrong path, stale verifier, missing repository export, or incomplete option API plumbing. Barcarolle's story is strongest when it shows that difference.

## Cost Ledger

Artifacts:

- ledger: `experiments/core_narrative/results/cost_ledger.jsonl`
- ledger calibration: `experiments/core_narrative/results/cost_ledger_alignment_2026-05-08.json`
- reconciliation: `experiments/core_narrative/results/codex_nfl_cost_reconciliation_2026-05-08.json`

Cost summary:

- latest cumulative estimated ledger cost after provider-usage calibration: USD 0.716208
- previous uncalibrated local projected ledger cost: USD 81.0008
- provider response usage cost for 9 Codex live runs: USD 0.53880075
- provider response usage cost in full reconciled ledger: USD 0.716208
- actual provider billed cost observed in repo artifacts: `null`

Provider usage cost is response metadata, not invoice proof. The ledger has been calibrated so future budget gates use provider-reported usage cost when available and zero out historical records that never reported provider usage cost; each rewritten record preserves its previous projected estimate in metadata.

## Limitations

- This is a 3-task, 3-ACUT RBench Click slice, not a full quantitative benchmark.
- No repeat attempts were run, so variance is unknown.
- The runner is direct search/replace, not the old interactive Codex CLI control plane.
- `frontier-click-specialist` was not run in this slice.
- Task 002 required a verifier repair during execution; corrected normalized outputs are valid, but the batch aggregate JSON from the in-flight process is stale.
- The hidden tests are focused probes, not full repository test suites.

## Reproduction

Prerequisites:

- `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` set in the environment.
- Do not print or record their values.

Commands:

```bash
python3 experiments/core_narrative/tools/materialize_task_pack.py \
  --split-manifest experiments/core_narrative/configs/tasks/rbench_click.yaml \
  --output-root experiments/core_narrative/tasks \
  --source-repo experiments/core_narrative/external_repos/click \
  --force \
  --output experiments/core_narrative/results/raw/codex_nfl_task_materialization_20260507.json

python3 -m py_compile \
  experiments/core_narrative/tools/codex_nfl_direct_runner.py \
  experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  experiments/core_narrative/tools/test_codex_nfl_direct_runner.py \
  experiments/core_narrative/tools/openclaw_direct_runner.py

cd experiments/core_narrative/tools && \
  python3 -m unittest test_codex_nfl_direct_runner.py test_openclaw_direct_runner.py

cd /Users/chenmohan/gits/barcarolle

python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  --run-prefix codex_nfl_mock_smoke_20260507 \
  --tasks click__rbench__001 \
  --acuts cheap-generic-swe \
  --mode mock \
  --mock-response experiments/core_narrative/results/raw/openclaw_direct_mock__cheap-generic-swe__click__rbench__001__attempt1/provider_response.redacted.json \
  --output experiments/core_narrative/results/codex_nfl_mock_smoke_20260507.json

python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  --run-prefix codex_nfl_live_core_20260507 \
  --tasks click__rbench__001 \
  --acuts cheap-generic-swe frontier-generic-swe cheap-click-specialist \
  --mode live \
  --output experiments/core_narrative/results/codex_nfl_live_core_20260507.json

python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  --run-prefix codex_nfl_live_expand_20260507 \
  --tasks click__rbench__002 click__rbench__003 \
  --acuts cheap-generic-swe frontier-generic-swe cheap-click-specialist \
  --mode live \
  --output experiments/core_narrative/results/codex_nfl_live_expand_20260507.json
```

Then regenerate the corrected score and cost summaries:

```bash
python3 experiments/core_narrative/tools/summarize_results.py \
  experiments/core_narrative/results/normalized/codex_nfl_live_core_20260507__cheap-generic-swe__click__rbench__001__attempt1.json \
  experiments/core_narrative/results/normalized/codex_nfl_live_core_20260507__frontier-generic-swe__click__rbench__001__attempt1.json \
  experiments/core_narrative/results/normalized/codex_nfl_live_core_20260507__cheap-click-specialist__click__rbench__001__attempt1.json \
  experiments/core_narrative/results/normalized/codex_nfl_live_expand_20260507__cheap-generic-swe__click__rbench__002__attempt1.json \
  experiments/core_narrative/results/normalized/codex_nfl_live_expand_20260507__frontier-generic-swe__click__rbench__002__attempt1.json \
  experiments/core_narrative/results/normalized/codex_nfl_live_expand_20260507__cheap-click-specialist__click__rbench__002__attempt1.json \
  experiments/core_narrative/results/normalized/codex_nfl_live_expand_20260507__cheap-generic-swe__click__rbench__003__attempt1.json \
  experiments/core_narrative/results/normalized/codex_nfl_live_expand_20260507__frontier-generic-swe__click__rbench__003__attempt1.json \
  experiments/core_narrative/results/normalized/codex_nfl_live_expand_20260507__cheap-click-specialist__click__rbench__003__attempt1.json \
  --output experiments/core_narrative/results/normalized/codex_nfl_live_summary_20260507.json

python3 experiments/core_narrative/tools/reconcile_cost_accounting.py \
  --ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --output experiments/core_narrative/results/codex_nfl_cost_reconciliation_2026-05-08.json
```

If the ledger has old projected estimates, calibrate it before future budget-gated runs:

```bash
python3 experiments/core_narrative/tools/calibrate_cost_ledger.py \
  --ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --unreported-policy zero \
  --output-summary experiments/core_narrative/results/cost_ledger_alignment_2026-05-08.json
```
