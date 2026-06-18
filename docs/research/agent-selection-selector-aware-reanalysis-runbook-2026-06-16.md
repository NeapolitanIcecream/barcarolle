# Agent Selection Selector-Aware Reanalysis Runbook 2026-06-16

Status: execution runbook for the next Codex agent session.

This runbook fixes the current presentation-data mismatch in the boltons Agent
selection demo. The existing expanded `50 x 4` outcome matrix is valuable, but
the current rolling-origin and user-facing charts compare historical task
windows to future task windows directly. That is not the same as the demo story:
a selector should choose a budgeted benchmark from the historical task pool, and
that selected benchmark should be checked against later tasks.

Do not run new paid Agent cells unless the user explicitly updates this
runbook. This is a no-paid selector-aware reanalysis over committed sanitized
outcomes.

## Goal

Use the existing `mahmoud/boltons` expanded outcome matrix to rerun every
implemented selector in a leakage-safe, selector-aware rolling-origin setup.

The final package should answer:

- Given a historical task pool at an origin, which budgeted benchmark does each
  selector choose?
- Which Agent would a user pick from that selected benchmark?
- Does later/future data validate that choice, or at least keep it in the
  future top tier?
- Which selector best supports the presentation demo story?
- How does the chosen selector compare with same-budget random baselines?

The final presentation selector is not preselected. If HRD v3 `70/30` is not the
best selector under this reanalysis, switch the demo story and charts to the
better selector.

## Starting State

Use these committed inputs:

- `experiments/agent_selection_demo/results/boltons_small_expansion_final_matrix.csv`
- `experiments/agent_selection_demo/results/boltons_small_expansion_task_manifest.json`
- `experiments/agent_selection_demo/results/selector_algorithm_registry.json`
- `experiments/agent_selection_demo/results/selector_algorithm_bakeoff_eval.json`
- existing selector implementations in
  `experiments/agent_selection_demo/tools/agent_selection_demo.py`

Known caveat to fix:

- `experiments/agent_selection_demo/reports/boltons_strict_rolling_origin_zh.md`
  uses the latest fixed historical window, not a selector-selected benchmark.
  It is historical pass-rate drift evidence, not the final selector story.

Presentation chart script currently lives at:

```text
/Users/chenmohan/playground/barcarolle_ppt_assets/make_agent_selection_demo_charts.py
```

## Scoring Policy

For this presentation reanalysis, count non-scoreable user-visible attempts as
failures. In particular, `timeout`, `acut_harness_error`, `invalid_output`, and
`no meaningful change` should enter the denominator and count as failed cells.

Rationale: from a user selecting an Agent, an Agent that times out or produces no
meaningful change did not solve the task.

Keep a sensitivity note if the old scoreable-only denominator changes any
ranking, but the main charts and demo story should use fail-inclusive pass
rates.

## Selector-Aware Protocol

For each origin:

1. Sort tasks by real `task_time`.
2. Define the historical candidate pool as all tasks strictly before the origin.
3. Define future check tasks as all tasks at or after the origin.
4. Run a selector on the historical candidate pool only.
5. Join existing Agent outcomes for the selector-chosen task IDs.
6. Compute Selection pass rates/ranking from the selector-chosen task IDs.
7. Compute future pass rates/ranking from the future task IDs.
8. Compare Selection and future with MAE, top-tier agreement, recommendation
   regret, and pairwise/top-pair direction.

Primary origins:

- `origin_20`: first 20 tasks as history, last 30 as future.
- `origin_30`: first 30 tasks as history, last 20 as future.
- `origin_40`: first 40 tasks as history, last 10 as future.

Do not use `origin_10` as a primary selector-aware origin for `k=10`, because a
10-task history pool leaves no real selection problem. It may be reported only
as a degenerate diagnostic if useful.

Primary budget:

- `k=10` selected tasks per origin.

Sensitivity budgets:

- `k=15` for origins with at least 30 historical tasks.
- `k=20` for `origin_40`.

The main PPT user-view chart should use the final chosen selector on
`origin_40`, because that is closest to the user-facing story: all available
history so far, followed by later tasks.

## Leakage Boundary

Selectors must not use future outcomes or future task IDs while selecting.

Allowed selector inputs:

- task metadata visible before the origin;
- task source/type/module/change-size metadata;
- task time and recency inside the historical pool;
- certification/quality/flakiness metadata known before outcomes are joined.

Static selectors must not read Agent outcomes before choosing task IDs.

Adaptive selectors such as SAES-lite may be replayed only if they emulate a
real sequential budget: first choose an initial batch from metadata, observe
outcomes only for that selected batch, then choose the remaining tasks. They
must never look at outcomes for unselected candidate tasks or future tasks while
choosing.

If an existing selector implementation cannot be made leakage-safe under this
protocol, still run a clearly labeled diagnostic version if useful, but exclude
it from final-selector eligibility and explain why.

## Selector Set

Run every selector already implemented in the demo code. At minimum this must
include:

- `rsq_v2`
- `rsq_v2_no_recency`
- `rsq_v2_no_caps`
- `flc`
- `representative_only`
- `informativeness_only`
- `hrd_v3_70_30`
- `hrd_v3_60_40`
- `hrd_v3_50_50`
- `hrd_v3_70_30_no_recency`
- `hrd_v3_70_30_no_caps`
- `hrd_v3_70_30_flc_rep`
- `cod_lite`
- `ro_lsp`
- `saes_lite`

Also run same-budget random baselines:

- uniform random;
- quality-filtered random;
- source/recency stratified random;
- module-stratified random.

Use at least `500` random seeds per `(origin, budget, baseline)`; use `1000`
if runtime is still fast.

If the implemented selector registry contains additional selectors, include
them. If one of the minimum selectors above is unavailable or broken, repair it
or document the exact exclusion reason.

## Final Selector Choice Rule

Choose the presentation selector from the eligible selector set after all
selector-aware evaluations are complete.

Rank selectors by:

1. Latest-origin user story quality:
   - Selection produces a clear recommendation or useful top tier;
   - recommended/top-tier Agent remains future top tier;
   - latest-origin recommendation regret is preferably `0`, acceptable if
     `<= 0.05`.
2. Rolling-origin decision quality across primary origins:
   - higher top-tier/top-pair agreement;
   - lower mean and max recommendation regret;
   - lower MAE.
3. Same-budget random comparison:
   - lower MAE than the strongest random baseline is better;
   - lower regret than random is better;
   - strict statistical significance is not required for this demo.
4. Simplicity and presentability:
   - if two selectors are effectively tied, prefer the easier one to explain.

Do not force a recommendation if no selector supports the story. In that case,
write a negative closeout and explain whether more tasks, a different budget, or
new paid cells are needed.

## Package 1: Protocol Freeze And Audit

Acceptance:

- Write a short audit explaining why the previous charts were not
  selector-aware.
- Freeze the selector-aware protocol, origins, budgets, fail-inclusive scoring
  policy, selector list, random baseline list, and final selector choice rule.
- Produce:
  - `experiments/agent_selection_demo/results/boltons_selector_aware_protocol.json`
  - `experiments/agent_selection_demo/reports/boltons_selector_aware_protocol_zh.md`

## Package 2: Build Selector-Aware Dataset

Acceptance:

- Build a task table from the final matrix and task manifest.
- Attach or reconstruct the metadata needed by all implemented selectors.
- Ensure every selected task can be traced back to a `task_id`, `task_time`,
  source, module/file bucket, quality/certification metadata when available,
  and Agent outcomes.
- Mark each selector feature as:
  - leakage-safe and final-eligible;
  - diagnostic only; or
  - unavailable, with reason.
- Produce:
  - `experiments/agent_selection_demo/results/boltons_selector_aware_task_features.csv`
  - `experiments/agent_selection_demo/results/boltons_selector_aware_outcome_matrix.csv`
  - `experiments/agent_selection_demo/reports/boltons_selector_aware_dataset_zh.md`

## Package 3: Run All Selectors

Acceptance:

- Run every eligible selector for every primary origin and primary budget.
- Run sensitivity budgets where applicable.
- Record selected task IDs, rationale, selected-task feature summaries, and
  whether the selector is final-eligible.
- For random baselines, record seed-level summaries and distribution summaries;
  do not store huge unnecessary raw dumps.
- Produce:
  - `experiments/agent_selection_demo/results/boltons_selector_aware_selections.json`
  - `experiments/agent_selection_demo/results/boltons_selector_aware_random_baselines.json`
  - `experiments/agent_selection_demo/reports/boltons_selector_aware_selector_outputs_zh.md`

## Package 4: Evaluate Selector-Aware Prediction And Decisions

Acceptance:

- For every selector/origin/budget, compute:
  - Selection pass rate by Agent;
  - future pass rate by Agent;
  - Selection ranking and future ranking;
  - top-tier agreement;
  - top-rank agreement;
  - recommendation regret;
  - top-pair future margin;
  - MAE by Agent and mean MAE.
- Compare each selector with same-budget random baselines on MAE and regret.
- Use fail-inclusive pass rates as the main result.
- Produce:
  - `experiments/agent_selection_demo/results/boltons_selector_aware_eval.json`
  - `experiments/agent_selection_demo/results/boltons_selector_aware_eval_slices.csv`
  - `experiments/agent_selection_demo/reports/boltons_selector_aware_eval_zh.md`

## Package 5: Choose Final Presentation Selector

Acceptance:

- Apply the final selector choice rule.
- If HRD v3 `70/30` wins, keep it; if another selector wins, switch the demo
  story to that selector.
- Write the exact latest-origin matrix for the chosen selector:
  - selected task IDs;
  - Selection pass rates;
  - future pass rates;
  - recommendation/top-tier decision;
  - regret and MAE.
- Produce:
  - `experiments/agent_selection_demo/results/boltons_selector_aware_winner.json`
  - `experiments/agent_selection_demo/reports/boltons_selector_aware_winner_zh.md`

## Package 6: Regenerate PPT Charts And Prompts

Regenerate the final PPT assets in:

```text
/Users/chenmohan/playground/barcarolle_ppt_assets
```

Acceptance:

- `agent_selection_selection_vs_holdout.png`
  - must use the chosen selector on `origin_40`;
  - Selection means selector-chosen budgeted tasks from the first 40 historical
    tasks, not all 40 historical tasks;
  - Future check means the last 10 tasks.
- `boltons_selector_aware_rolling_origin_timeline.png`
  - must show selector-aware origins, not raw historical windows;
  - make clear that each point is selected benchmark vs future.
- `rolling_origin_mae_comparison.png`
  - must compare the chosen selector with same-budget random baselines under
    the selector-aware protocol.
- Update `agent_selection_demo_image_prompts.md` or create a new prompt file
  for the final algorithm schematic using the winning selector's real name and
  logic. If HRD is not the winner, do not keep HRD as the algorithm prompt.
- Keep the current clean PPT style: white background, black/deep blue only,
  no decorative gradients, no logos, no dense process text.

## Package 7: Final Story And Process Update

Acceptance:

- Write a concise Chinese final story:
  - what was wrong with the previous non-selector-aware chart;
  - which selector won;
  - what the latest-origin user story says;
  - what rolling-origin evidence says;
  - what random baseline comparison says;
  - what remains unsupported.
- Update `PROCESS.md` so future sessions do not keep treating the old
  fixed-window rolling-origin chart as selector evidence.
- Produce:
  - `experiments/agent_selection_demo/reports/boltons_selector_aware_reanalysis_closeout_zh.md`
  - `experiments/agent_selection_demo/results/boltons_selector_aware_reanalysis_closeout.json`

## Tests And Hygiene

Run at minimum:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
```

If you add or change selector-aware analysis code, add focused tests that check:

- selected task IDs are always a subset of the historical pool;
- future task IDs are never selected;
- non-scoreable cells count as failures in the presentation/eval path;
- random baselines use the same history pool and same budget as the selector;
- the latest-origin user chart is built from selector-chosen task IDs, not all
  historical task IDs.

Also run:

```text
git diff --check
git ls-files | rg '(\.venv|\.pytest_cache|\.DS_Store|raw|transcript|workspace|outputs/)'
```

The `git ls-files` scan should have no newly introduced prohibited tracked
artifacts. If it finds pre-existing historical matches, report them separately
and do not hide new issues.

## Closeout Requirements

Final response must include:

- whether new paid Agent cells were run; expected answer is `0`;
- selectors evaluated;
- final winning selector and budget;
- latest-origin Selection/Future matrix;
- rolling-origin selector-aware MAE/regret/top-tier metrics;
- random baseline comparison;
- regenerated chart paths;
- tests/hygiene checks run;
- exact claims supported and unsupported;
- commit hashes.
