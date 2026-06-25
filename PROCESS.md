# Barcarolle Process Notes

Last updated: 2026-06-25.

This file records current process decisions for future Barcarolle sessions. It
is not a lab notebook, prompt archive, or report index.

## Current Mode

The project is in proposal review. Until there is budget for broader paid
experiments, prioritize:

- a clean v2 rewrite with low abstraction cost;
- learned task-selector research using existing results and bounded new data;
- task-generator reuse from SWE-bench-style related work;
- concise state documentation over process archaeology.

Experiment code is evidence and provenance, not the v2 architecture.

## Current Architecture Direction

Barcarolle should be a target-repository benchmark compiler with a small set of
core objects:

- `Task`: solver-visible problem and repository metadata.
- `Check`: task acceptance method or oracle.
- `Workspace`: isolated solver and verifier execution.
- `Result`: one Agent on one task, including status, cost, latency, and failure
  labels.
- `Selector`: chooses benchmark tasks from historical supply under a budget.
- `RollingOrigin`: evaluates whether selected tasks predict later work.

Task generators should output `Task + Check`. Built-in task supply should reuse
related-work patterns where possible: history mining, quality filtering,
live/future refresh, large-supply synthetic generation, and user-provided task
pools.

Keep `Task Pool`, `Benchmark Selection`, and `Agent Results` decoupled. Paid
`Agent x Task` results are reusable assets: selector research should be able to
iterate over cached result tables without rerunning identical paid cells, while
operational runs may still select a benchmark first and then execute only
missing cells.

Canonical v2 architecture draft:

- `docs/architecture/v2-system-architecture-2026-06-25.md`

## Selector Research Direction

The selector is the core research claim. The next research track is learned task
selection under rolling-origin evaluation.

Use simple rule-based selectors as baselines and fallbacks: random, recency,
coverage, stratified coverage, difficulty balance, Agent disagreement,
failure-mode coverage, and cost-bounded variants.

Start learned selectors with data-efficient methods: learned mixtures over
rule-based selectors, calibrated weighting, pairwise/ranking models, simple
linear or tree models when data supports them, and uncertainty-aware online
updates.

Primary metric:

- future pass-rate prediction error, initially MAE.

Supporting metrics:

- top-rank agreement;
- recommendation regret;
- calibration bias;
- catastrophic miss rate;
- robustness across origins, repositories, Agent subsets, and budgets;
- scoreable/invalid rate;
- cost and latency;
- task diversity and coverage.

External-roadmap prompt:

- `docs/research/learned-selector-roadmap-gpt-5-5-pro-prompt-2026-06-25.md`

## Claim Boundary

Predictive validity is the north star, not an established result.

Current safe claims:

- complete-Agent workspace evaluation is feasible;
- task supply and task selection materially affect benchmark usefulness;
- existing evidence provides traction, not final proof.

Do not claim:

- proven predictive validity;
- a generally superior selector;
- cross-repository Agent rankings;
- production-ready tuning improvement;
- public leaderboard significance.

## Paid-Run Boundary

Do not run new paid Agent cells by default.

Future paid validation needs a frozen protocol, preregistered baselines,
score-join rules, invalid-cell policy, cost accounting, uncertainty reporting,
and explicit success criteria.

All paid LLM or Agent calls must use:

```text
LLM_BASE_URL
LLM_API_KEY
```

No fallback endpoint is allowed unless the user updates `AGENTS.md`.

Agent tuning remains paused unless a dedicated budget and protocol are provided.
Before resuming, use outcome caching, a cost smoke gate, neutral instruction
controls, flipped-task repeats, and workspace leakage checks.

## Goodhart Boundary

Keep benchmark predictive validity separate from tuning utility.

Benchmark predictive validity asks whether a benchmark generated at time `t`
predicts future performance of Agents available at time `t`.

Tuning utility asks whether benchmark feedback can improve a later tuned Agent.
That measures the combined effect of benchmark, tuner, and tuned artifact; it
does not by itself prove benchmark predictive validity.

Canonical note:

- `docs/research/goodhart-law-note-2026-06-23.md`
