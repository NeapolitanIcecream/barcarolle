# Agent Tuning Demo Phase 2b report

Generated at: `2026-06-15T03:39:32+00:00`.

## Why Phase 2a was not enough

Phase 2a proved action-level artifact injection and an end-to-end before/after validation loop, but it did not prove tuning improvement. Selection-dev stayed `1/4 -> 1/4`, Holdout stayed `5/6 -> 5/6`, paired net wins were `0` on both splits, and the proposer was a deterministic local GEPA-shaped proposer with no reflection LM.

## Result

- Terminal state: `phase2b_dev_negative`
- Phase 2a relabeled correctly: `True`
- Target Agent/surface: `kilo_gpt_5_4_mini` / `repo_AGENTS_md`
- LLM proposer status/calls: `llm_proposer_complete` / `2`
- Paid Agent cells: `18`
- Estimated cost: `$0.8974602`

## Rolling-origin design and task supply

| Window | Mode | Train | Dev | Future | Dev baseline | Future baseline |
| --- | --- | --- | --- | --- | --- | --- |
| boltons_time_ordered_w1_train2015_2018_dev2019_2020_future2022_2023 | single_time_ordered_future_validation | 10 | 6 | 10 | 0.6667 | 0.6 |

Current supply supports one strong time-ordered future-validation window, not a two-window rolling-origin claim. Future task IDs stayed hidden because no artifact passed the dev gate.

## Target Agent and artifact surface

The frozen target was `kilo_gpt_5_4_mini` through Kilo with one repo-local `AGENTS.md` appendix. The surface was chosen because Kilo `AGENTS.md` action-level preflight passed in Phase 2.

## LLM proposer and artifacts

The proposer used `2` LLM calls, including one reflection/revision iteration. It produced two candidate `AGENTS.md` appendices from train-only evidence; raw prompt and completion content stayed under ignored raw paths.

## Dev matrix

| Candidate | Pass | Scoreable | Net wins | Gate |
| --- | --- | --- | --- | --- |
| tuned_candidate_1 | 4 | 6 | 0 | False |
| tuned_candidate_2 | 4 | 6 | 0 | False |

Both candidates were non-regressing on dev but failed the preregistered improvement gate because paired net wins were `0` rather than positive.

## Future matrix

_Future validation was not run._

## Cost, latency, and invalid runs

| Candidate | Baseline cost | Tuned cost | Cost ratio | Baseline latency | Tuned latency | Invalid baseline/tuned |
| --- | --- | --- | --- | --- | --- | --- |
| tuned_candidate_1 | 0.29861655 | 0.32377995 | 1.0843 | 49.363 | 49.333 | 0/0 |
| tuned_candidate_2 | 0.29861655 | 0.2750637 | 0.9211 | 49.363 | 44.99 | 0/0 |

No tuned candidate increased invalid or unscoreable dev cells. Candidate 1 cost was `1.0843x` baseline per task; candidate 2 cost was `0.9211x` baseline per task.

## Case studies

- Improved task: none observed on dev.
- Unchanged task: `boltons__clean_ext__001` passed under baseline and both tuned candidates.
- Remaining failure: `boltons__hist__006` and `boltons__supply_expansion_20260526__107` failed under baseline and both tuned candidates.
- Regression: none observed on dev.

## Behavior and failure-label changes

No terminal-status or failure-label shift was observed on dev: both candidates reproduced the baseline pass/fail matrix exactly.

## Supported claims

- Phase 2a is correctly relabeled as an action-level artifact-validation pilot, not tuned improvement.
- The current boltons/Kilo-low-cost supply supports one no-paid-gated time-ordered future-validation window.
- A real LLM-driven proposer produced deployable Kilo AGENTS.md candidate artifacts from train-only evidence.

## Unsupported claims

- multi-window rolling-origin improvement
- statistical significance
- cross-repo generalization
- model fine-tuning
- full opaque-Agent tuning
- production-ready Agent tuning
- predictive validity beyond this frozen task window

## Recommended next work

- Add a second prepared repo or more Kilo-low-cost boltons rows before claiming multi-window rolling-origin improvement.
- Keep the LLM-proposer path, but add stronger train failure summaries if dev remains negative.
- Do not spend future-validation cells unless the frozen dev gate remains positive.
