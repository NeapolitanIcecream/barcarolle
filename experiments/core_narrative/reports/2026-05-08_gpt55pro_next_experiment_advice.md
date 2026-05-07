# 2026-05-08 GPT-5.5-Pro Next Experiment Advice

status: `accepted_as_next_plan`
source: `/Users/chenmohan/Downloads/barcarolle-research-0.md`
related_pr: `https://github.com/NeapolitanIcecream/barcarolle/pull/1`

## Recommendation

Do not move to a new repository yet, and do not only repeat the original 9 cells. The next experiment should be a Click core matrix stabilization pass:

1. Harden runner and verifier trust without spending model budget.
2. Add the missing `frontier-click-specialist` ACUT on `click__rbench__001` through `click__rbench__003`.
3. Repeat the complete 4 ACUT by 3 task matrix as attempt 2.
4. Expand to `click__rbench__004` through `click__rbench__008` only after the stabilization gates pass.

This keeps the Barcarolle NFL story focused: the current box score is tied, but the film explains different failure modes. The next pass should make that film review machine-readable and reproducible.

## Progress After Import

Step 0 has started. The batch runner now verifies a generated `submission.patch` in a fresh `__verify` workspace instead of using `--skip-apply` on the runner-mutated workspace.

Evidence:

- Code: `experiments/core_narrative/tools/codex_nfl_experiment_runner.py`
- Regression tests: `experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py`
- Mock smoke output: `experiments/core_narrative/results/codex_nfl_clean_verify_mock_20260508.json`
- Mock normalized result: `experiments/core_narrative/results/normalized/codex_nfl_clean_verify_mock_20260508__cheap-generic-swe__click__rbench__001__attempt1.json`
- Mock raw artifacts: `experiments/core_narrative/results/raw/codex_nfl_clean_verify_mock_20260508__cheap-generic-swe__click__rbench__001__attempt1/`

The mock normalized result records `metadata.skip_apply: false`, and its batch result records separate `runner_workspace` and `verify_workspace` paths.

## Accepted Run Order

| Step | Model budget | Work |
|---|---:|---|
| 0 | no live API | Clean verification replay, task-pack preflight, score schema and film labels |
| 1 | 3 live runs | Fill `frontier-click-specialist` attempt 1 on tasks 001-003 |
| 2 | 12 live runs | Run attempt 2 for 4 ACUTs on tasks 001-003 |
| 3 | gated | Expand to Click tasks 004-008 |

The next live step is small but should not run until Step 0 passes.

## Core ACUT Matrix

| ACUT | Role | Main matrix |
|---|---|---|
| `cheap-generic-swe` | cheap model plus generic SWE policy | yes |
| `frontier-generic-swe` | frontier model plus generic SWE policy | yes |
| `cheap-click-specialist` | cheap model plus Click task-agnostic context | yes |
| `frontier-click-specialist` | frontier model plus Click task-agnostic context | yes |

Do not mix `minimal-context-baseline`, `retrieval-history-augmented`, or `higher-budget-repo-depth` into the main matrix yet. They are diagnostic sidecars because they change too many factors at once.

## Required Runner Changes Before Live Runs

- Verify on a fresh workspace prepared from the same task base, then apply `submission.patch` and run the verifier.
- Preserve the runner-mutated workspace only as an artifact source, not as the correctness root.
- Record runner identity, direct runner identity, ACUT manifest digest, task manifest digest, verifier digest, prompt snapshot digest, and context-pack digest in normalized results.
- Add idempotency checks so an existing `run_id` in raw, normalized, or ledger paths is not overwritten by default.
- Assert specialist context inclusion for specialist ACUTs and exclusion for generic ACUTs.

## Film Labels V0.1

Film labels must explain results without changing correctness.

| Label | Meaning | Current example |
|---|---|---|
| `missing_repository_affordance` | Patch touches the right behavior area but misses repo layout, export, import, or internal affordance | generic task-003 failures missed `click._termui_impl` top-level exposure |
| `api_plumbing_incomplete` | Patch implements local behavior but misses constructor, signature, or parameter propagation | cheap specialist task-003 missed `show_choices=False` through `Option.__init__` |
| `hidden_test_inference_miss` | Plausible patch likely addresses visible behavior but fails a hidden contract | secondary label for all task-003 failures |
| `generic_incorrect_patch` | Wrong file, syntax break, unrelated patch, test-only change, or clearly wrong semantics | not used for current task-003 failures |
| `verifier_oracle_misaligned` | The oracle, task pack, no-op, reference, or hidden target is wrong or unstable | task-002 stale verifier repair |
| `runner_or_artifact_contract_failed` | Patch generation, patch apply, clean replay, redaction, or output contract failed | no final 9-run example |

## Task-003 Classification

| ACUT | Box score | Primary film label | Secondary film label |
|---|---|---|---|
| `cheap-generic-swe` | failed | `missing_repository_affordance` | `hidden_test_inference_miss` |
| `frontier-generic-swe` | failed | `missing_repository_affordance` | `hidden_test_inference_miss` |
| `cheap-click-specialist` | failed | `api_plumbing_incomplete` | `hidden_test_inference_miss` |

This is stronger than saying "all agents failed task 003." The failures are score-equivalent but not behavior-equivalent.

## Budget Note

The current 9 live Codex runs report USD 0.53880075 of provider response usage cost. A naive 15-run average estimate is about USD 0.90. A tier-adjusted estimate that treats `frontier-click-specialist` like the current frontier runs is closer to USD 1.25-1.35. The budget gate should use calibrated provider usage cost where available and keep projected upper bounds as a guardrail.

## PR-Sized Work Items

| Task | Output |
|---|---|
| A. Clean verification path | Batch runner verifies `submission.patch` in a fresh workspace |
| B. Task-pack validator | JSON preflight for no-op, reference, known-bad, flakiness, runtime, and leakage probes |
| C. Score schema v0.2 | Normalized results include outcome class, owner, evidence digests, and film fields |
| D. Film classifier v0.1 | Deterministic labels for current task-003 failures and verifier/task-pack issues |
| E. Core 2x2 completion | `frontier-click-specialist` attempt 1 plus 4x3 attempt 2 |
| F. Click 004-008 expansion | Run only after Gate 1 passes |

## Next Live Commands

Run these only after the no-budget gates pass:

```bash
python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  --run-prefix codex_nfl_core4_fill_20260508 \
  --tasks click__rbench__001 click__rbench__002 click__rbench__003 \
  --acuts frontier-click-specialist \
  --attempt 1 \
  --mode live \
  --output experiments/core_narrative/results/codex_nfl_core4_fill_20260508.json

python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  --run-prefix codex_nfl_core4_rep1_20260508 \
  --tasks click__rbench__001 click__rbench__002 click__rbench__003 \
  --acuts cheap-generic-swe frontier-generic-swe cheap-click-specialist frontier-click-specialist \
  --attempt 2 \
  --mode live \
  --output experiments/core_narrative/results/codex_nfl_core4_rep1_20260508.json
```
