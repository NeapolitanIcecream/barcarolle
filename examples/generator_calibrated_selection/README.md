# Generator-Calibrated Selection

This example runs the outcome-free `THY-002S-A` front gate. It maps the frozen
`THY-002` module forecast to one deterministic ten-Task Selection, then asks
whether that Selection is structurally closer to the next Task cohort than
full history, a stationary coreset, and equal-budget random sampling.

The frozen contract is [`plan.json`](plan.json), digest
`cb83d866…b1b9a`. Stage A may read Task metadata, projected Task times,
reference patches, and cutoff-safe Git history. It must not read Agent
outcomes, embeddings, the sealed holdout, or a paid endpoint.

## Run

The source tree and bare Git repositories are ignored research artifacts:

- `outputs/research/2026-07-28-multi-swe-source/repository`;
- `outputs/research/2026-07-29-pre-origin-task-mix/repositories`.

Run the frozen front gate twice:

```bash
uv run --with 'numpy==2.5.1' \
  python examples/generator_calibrated_selection/study.py \
  run-task-space

cp \
  outputs/research/2026-07-29-generator-calibrated-selection/task-space-results.json \
  outputs/research/2026-07-29-generator-calibrated-selection/task-space-results-reproduction.json

uv run --with 'numpy==2.5.1' \
  python examples/generator_calibrated_selection/study.py \
  run-task-space \
  --output \
  outputs/research/2026-07-29-generator-calibrated-selection/task-space-results-second.json

cmp \
  outputs/research/2026-07-29-generator-calibrated-selection/task-space-results-reproduction.json \
  outputs/research/2026-07-29-generator-calibrated-selection/task-space-results-second.json
```

Verify and produce the small committed projection:

```bash
uv run --with 'numpy==2.5.1' \
  python examples/generator_calibrated_selection/study.py \
  compact

uv run --with 'numpy==2.5.1' \
  python examples/generator_calibrated_selection/study.py \
  verify \
  --summary \
  examples/generator_calibrated_selection/evidence/task-space-summary.json
```

Raw Origin rows, exact memberships, and 20,000-draw random distributions stay
under ignored `outputs/research`. The committed summary contains their digests,
repository-first contrasts, random position, zero-resource ledger, and
decision.

## Stop Boundary

If Stage A fails, retire only this Brier-projection mapping. Do not inspect
Agent outcomes or tune the forecast, mapping, budget, source, horizon, or
gate.

If Stage A passes, the plan permits one focused executor amendment. That
amendment must bind the Stage A result and membership digests plus the exact
already-open Multi-SWE outcome bytes. It may add the outcome join and
predeclared aggregation only; it may not change memberships or any decision
rule. A later outcome pass would be development nomination, not confirmation
or permission to open the six sealed SWE-bench Verified Agents.

## Recorded Decision

The accepted A1 replay returned `retire_mapping`: H10 passed, while both H5
gates missed only their repository-bootstrap-upper-bound condition. The
outcome executor is therefore not authorized. See the
[experiment report](../../docs/experiments/2026-07-29-generator-calibrated-selection.md)
and committed
[`task-space-summary.json`](evidence/task-space-summary.json).
