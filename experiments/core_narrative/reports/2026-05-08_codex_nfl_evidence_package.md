# 2026-05-08 Codex NFL Evidence Package

status: `ready_for_pr`
branch: `codex/core-narrative-experiment`
prepared: 2026-05-07 Asia/Shanghai
scope: Barcarolle core-narrative RBench Click slice

## Current State

Codex resumed ownership of the Barcarolle core-narrative experiment and replaced the brittle Codex CLI/OpenClaw execution path with a Codex-owned direct runner. The current live slice is complete and scoreable:

- 9 live Codex-owned RBench Click runs.
- 3 ACUTs: `cheap-generic-swe`, `frontier-generic-swe`, `cheap-click-specialist`.
- 3 tasks: `click__rbench__001`, `click__rbench__002`, `click__rbench__003`.
- 6 passed, 3 failed, 0 infra-failed.
- Every ACUT finished 2/3, for a 66.7% pass rate.

The experimental story is usable for Barcarolle's NFL framing: the box score is tied, but the film separates infrastructure problems from model-patch behavior.

## Final Score Table

Source of truth: `experiments/core_narrative/results/normalized/codex_nfl_live_summary_20260507.json`.

| ACUT | `click__rbench__001` | `click__rbench__002` | `click__rbench__003` | Total | Pass rate |
|---|---|---|---|---:|---:|
| `cheap-generic-swe` | passed | passed | failed | 2/3 | 66.7% |
| `frontier-generic-swe` | passed | passed | failed | 2/3 | 66.7% |
| `cheap-click-specialist` | passed | passed | failed | 2/3 | 66.7% |
| all | 3/3 passed | 3/3 passed | 0/3 passed | 6/9 | 66.7% |

## Why Three Runs Failed

All three failures are on `click__rbench__003`.

- `cheap-generic-swe` and `frontier-generic-swe` both produced plausible prompt-choice patches, but the hidden verifier expected `click._termui_impl` to be exposed at the top level. Both failed with `AttributeError: module 'click' has no attribute '_termui_impl'`.
- `cheap-click-specialist` implemented prompt-choice rendering but did not correctly plumb `show_choices=False` through `Option.__init__`. The hidden verifier failed with `TypeError: __init__() got an unexpected keyword argument 'show_choices'`.

Interpretation: the 3 failures are model/patch failures under the hidden verifier, not experiment infrastructure failures.

## Evidence Manifest

| Purpose | Path |
|---|---|
| Experiment report | `experiments/core_narrative/reports/2026-05-08_codex_nfl_experiment_report.md` |
| Evidence package | `experiments/core_narrative/reports/2026-05-08_codex_nfl_evidence_package.md` |
| Live score summary | `experiments/core_narrative/results/normalized/codex_nfl_live_summary_20260507.json` |
| Per-run normalized results | `experiments/core_narrative/results/normalized/codex_nfl_live_*__attempt1.json` |
| Raw live artifacts | `experiments/core_narrative/results/raw/codex_nfl_live_*__attempt1/` |
| Task materialization record | `experiments/core_narrative/results/raw/codex_nfl_task_materialization_20260507.json` |
| Cost ledger | `experiments/core_narrative/results/cost_ledger.jsonl` |
| Cost reconciliation | `experiments/core_narrative/results/codex_nfl_cost_reconciliation_2026-05-08.json` |
| Ledger calibration summary | `experiments/core_narrative/results/cost_ledger_alignment_2026-05-08.json` |
| Direct runner | `experiments/core_narrative/tools/codex_nfl_direct_runner.py` |
| Batch runner | `experiments/core_narrative/tools/codex_nfl_experiment_runner.py` |
| Cost calibration tool | `experiments/core_narrative/tools/calibrate_cost_ledger.py` |

Each raw run directory includes the prompt snapshot, redacted provider response, submission patch, runner result, verifier stdout/stderr, and command summaries.

## Cost State

The local ledger has been aligned to provider-reported usage cost where provider metadata exists:

- previous cumulative projected ledger estimate: USD 81.0008.
- calibrated cumulative estimated ledger cost: USD 0.716208.
- provider-reported usage cost across the full reconciled ledger: USD 0.716208.
- provider-reported usage cost for the 9 Codex live runs: USD 0.53880075.
- actual provider billed or invoiced cost observed in repo artifacts: unknown.

`estimated_cost_usd` is now suitable for local budget gates because it uses provider response usage cost when available. It is still not invoice proof.

## Facilities Changed

Added or materially updated:

- `experiments/core_narrative/tools/codex_nfl_direct_runner.py`
- `experiments/core_narrative/tools/codex_nfl_experiment_runner.py`
- `experiments/core_narrative/tools/calibrate_cost_ledger.py`
- `experiments/core_narrative/tools/openclaw_direct_runner.py`
- `experiments/core_narrative/tools/reconcile_cost_accounting.py`
- focused unit tests for direct runner, OpenClaw runner guardrails, reconciliation, and ledger calibration.

Verifier repair:

- `click__rbench__002` referenced a stale hidden test name.
- Fixed `experiments/core_narrative/configs/tasks/rbench_click.yaml`.
- Fixed `experiments/core_narrative/tasks/click/rbench/click__rbench__002/verifier/run.sh`.
- Corrected normalized scoring shows all three task-002 runs pass.

## Current Limits

- This is a 3-task, 3-ACUT Click slice, not a full benchmark.
- No repeat attempts were run, so variance is unknown.
- `frontier-click-specialist` was not included in the live slice.
- The runner is direct search/replace, not the old interactive Codex CLI path.
- Task 002 required verifier repair; use normalized outputs and `codex_nfl_live_summary_20260507.json` for scoring, not the stale in-flight aggregate.

## Prompt For GPT-5.5-Pro

```text
You are GPT-5.5-Pro advising the next Barcarolle core-narrative experiment.

Context:
- Repository: Barcarolle.
- Current experiment: Codex-owned NFL-style RBench Click slice.
- Goal: support the Barcarolle story from an NFL angle: a benchmark should distinguish box-score outcomes from film-level explanations of how a coding agent won or lost.
- Previous control planes were brittle. Codex replaced the Codex CLI/OpenClaw execution path with a direct search/replace runner to prioritize completing scoreable experiments.
- The experiment now has 9 live scoreable runs across 3 tasks and 3 ACUTs.

Current score table:
| ACUT | click__rbench__001 | click__rbench__002 | click__rbench__003 | Total | Pass rate |
| cheap-generic-swe | passed | passed | failed | 2/3 | 66.7% |
| frontier-generic-swe | passed | passed | failed | 2/3 | 66.7% |
| cheap-click-specialist | passed | passed | failed | 2/3 | 66.7% |
| all | 3/3 passed | 3/3 passed | 0/3 passed | 6/9 | 66.7% |

Failure notes:
- All three failures are on click__rbench__003.
- cheap-generic-swe and frontier-generic-swe produced plausible prompt-choice patches but missed the repo-specific hidden verifier expectation that click._termui_impl be exposed at top level.
- cheap-click-specialist implemented prompt-choice rendering but failed to plumb show_choices=False through Option.__init__.
- There are no infra_failed runs in the final 9-run slice.

Key artifacts:
- Final report: experiments/core_narrative/reports/2026-05-08_codex_nfl_experiment_report.md
- Evidence package: experiments/core_narrative/reports/2026-05-08_codex_nfl_evidence_package.md
- Score summary: experiments/core_narrative/results/normalized/codex_nfl_live_summary_20260507.json
- Raw artifacts: experiments/core_narrative/results/raw/codex_nfl_live_*__attempt1/
- Cost reconciliation: experiments/core_narrative/results/codex_nfl_cost_reconciliation_2026-05-08.json
- Ledger calibration: experiments/core_narrative/results/cost_ledger_alignment_2026-05-08.json

Cost state:
- Provider-reported usage cost for the 9 live Codex runs: USD 0.53880075.
- Calibrated cumulative ledger estimate: USD 0.716208.
- Actual billed/invoiced provider cost is unknown from repo artifacts.

Please recommend the next experiment step. I want advice that is directly actionable for a coding agent, not generic benchmark commentary. Cover:
1. Whether to extend this Click slice, repeat the same 9 cells for variance, or add new task families first.
2. Which ACUT matrix should be run next, including whether to add frontier-click-specialist or controls.
3. How to turn the "box score vs film" story into measurable labels without overfitting to this slice.
4. What runner/verifier changes are required before spending more API budget.
5. How to classify task-003 failures so the narrative separates missing repository affordance, API plumbing, hidden-test inference, and generic incorrect patches.
6. Minimum sample size or replication plan that would make the NFL framing defensible.
7. Concrete decision gates: what result would make us expand, revise the task pack, or stop.

Assume the priority order is: runnable experiment, reliable data, narrative support, then infrastructure elegance.
```
