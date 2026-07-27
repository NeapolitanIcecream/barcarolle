# Offline Selector Study

This example reuses the completed 75-Task SymPy model/Agent study without
making a model, network, or paid call.

The frozen plan originally attempted a counterfactual rolling-origin replay.
The first source-contract check falsified that path: every certified Check was
materialized on 2026-07-25, after the Tasks' 2016–2023 source times. A valid
historical `RollingOriginRecord` therefore contains only censored Task/Check
refs. The two append-only amendments retain that finding and forbid rewriting
timestamps.

The remaining analysis is explicitly a historical Task-order diagnostic. It
uses source time to create twelve non-overlapping five-Task blocks, but it does
not persist projected Origins, Selections, matrices, or metrics as core
evidence. Its valid uses are algorithm triage, noise and dependency
sensitivity, hindsight headroom, and prospective campaign sizing.

Run it from the repository root after restoring the ignored source artifacts:

```bash
uv run python examples/offline_selector_study/study.py
```

The command verifies the plan, amendment chain, Task Pool, Agent, schedule, and
Result SHA-256 bindings before analysis. It writes the sanitized,
self-digested `study-results.json`. Raw per-Task outcomes, prompts,
completions, transcripts, and workspaces are neither copied nor committed.

Current conclusion:

- the predeclared weighted stratified rule is not supported on this source;
- ALG-001 and ALG-004 safely retain the coverage fallback;
- ALG-003 is seed-unstable;
- coverage is only a candidate for a new preregistered prospective comparison,
  not a production default or a result established by valid rolling-origin
  evidence.

See `docs/experiments/2026-07-27-offline-selector-study.md` for the complete
interpretation and claim boundary.
