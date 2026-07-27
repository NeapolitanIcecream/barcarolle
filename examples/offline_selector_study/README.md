# Offline Selector Study

This example reuses the completed 75-Task SymPy model/Agent study without
making a model, network, or paid call.

The published Task Pool records every Check as observed in 2026, so its
historical source-time Origins are fully censored. That view remains the
negative control.

A third append-only amendment defines a separate
`label_at_task_arrival` scenario. It keeps the published Task Pool and Results
unchanged, projects each Check material time to its bound Task material time,
and labels the result `user_configured_counterfactual`. This exercises
user-configured algorithm-visible metadata without claiming that the projected
times are source-attested or strict-prospective.

After restoring the ignored source artifacts, run all analyses:

```bash
uv run python examples/offline_selector_study/study.py
uv run python examples/offline_selector_study/public_replay.py
uv run python examples/offline_selector_study/landscape.py
```

The commands verify their plan, amendment chain, Task Pool, Agent, schedule,
Result, and embedding bindings. They write self-digested sanitized results and
do not copy raw per-Task outcomes, embeddings, prompts, completions,
transcripts, or workspaces.

Current conclusion:

- the public replay produces 12 scoreable Origins, 72 Selections, and 150 exact
  cached Result bindings;
- coverage MAE is `0.1833`, versus `0.2250` for random seed 5 and `0.2042` for
  recency, within this configured counterfactual scenario;
- the correct primary baseline, all eligible historical Tasks without
  Selection, has MAE `0.1933`; coverage improves it by only `0.0100`, with a
  descriptive paired interval of `[-0.0363, +0.0152]`;
- the exact equal-budget random landscape has expected MAE `0.2150`; coverage
  beats `88.68%` of its mass by midrank, while a random draw is as good or
  better with probability `12.91%`; coverage nevertheless falls below random
  midrank in Origins 6–9;
- continuous historical support and the hindsight ten-Task oracle have MAE
  `0.0250` and `0.0375`, so representability is not the main observed limit;
- coverage versus full history changes sign across future block sizes; a
  first-Task-per-dependency-cluster view improves the point gain to `0.0167`
  but still misses the point and interval gates; 5,000 preselected repeat-noise
  views average a `0.0071` gain and none reaches `0.02`;
- outcome-forecast matching, semantic embedding coresets,
  semantic-conditioned outcome forecasts, and a two-Agent mid-difficulty
  filter produced no rule that clears the `0.02` practical-improvement gate
  over full history;
- the predeclared weighted stratified rule is not supported on this source;
- ALG-001 and ALG-004 safely retain the coverage fallback;
- ALG-003 is seed-unstable;
- coverage remains a candidate for a new preregistered prospective comparison,
  not a production default.

See `docs/experiments/2026-07-27-offline-selector-study.md` for the original
replay and `docs/experiments/2026-07-27-selection-landscape-study.md` for the
full-baseline, exact-random, support, null-control, and candidate analysis.
