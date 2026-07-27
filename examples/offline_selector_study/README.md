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

After restoring the ignored source artifacts, run both analyses:

```bash
uv run python examples/offline_selector_study/study.py
uv run python examples/offline_selector_study/public_replay.py
```

Both commands verify the plan, amendment chain, Task Pool, Agent, schedule, and
Result bindings. They write self-digested sanitized results and do not copy raw
per-Task outcomes, prompts, completions, transcripts, or workspaces.

Current conclusion:

- the public replay produces 12 scoreable Origins, 72 Selections, and 150 exact
  cached Result bindings;
- coverage MAE is `0.1833`, versus `0.2250` for random seed 5 and `0.2042` for
  recency, within this configured counterfactual scenario;
- the predeclared weighted stratified rule is not supported on this source;
- ALG-001 and ALG-004 safely retain the coverage fallback;
- ALG-003 is seed-unstable;
- coverage remains a candidate for a new preregistered prospective comparison,
  not a production default.

See `docs/experiments/2026-07-27-offline-selector-study.md` for the complete
interpretation and claim boundary.
