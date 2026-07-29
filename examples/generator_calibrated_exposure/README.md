# Generator-Calibrated Module Exposure

This direct research layer runs the frozen, outcome-free `THY-002` Task-mix
test. It asks whether a fixed Generator's historical Task yield per unit of Git
module exposure, applied to current Git pressure, predicts the Generator's next
H5/H10 Task mix better than:

- full Task history;
- current Git pressure without Generator calibration;
- Generator yield without current exposure;
- the latest `h` Tasks; and
- uniform mass.

The plan is digest-bound at
[`plan.json`](plan.json), digest `0fe42fc1…1c69`. It pins SWE-rebench V2 file
identity, 41 source aliases collapsed into 40 canonical Git repositories,
5,365 unique Tasks, exact default refs and HEAD commits, implementation bytes,
the formula, nested Origins, row-integrity rules, Brier score, controls, and
pass/retire gate.

The evidence is counterfactual. SWE-rebench V2 `created_at` values are
timezone-naive and are explicitly treated as UTC. Historical and future Task
module attributes come from reference patches. This is allowed for the
projected experiment but is not native Task-arrival evidence. Agent outcomes,
the sealed holdout, embeddings, and paid calls are prohibited.

Task `base_commit` object presence is recorded and digest-bound as a lineage
diagnostic, not used as an admission gate: this study never checks out a Task
base or derives its inputs from that object. Unknown repositories, unexpected
horizons, missing or extra planned Origins, duplicate rows, and incomplete
H5/H10 Origin pairs are rejected before aggregation. Verification also
enforces the frozen zero-use boundary for paid calls, embeddings, Agent
outcomes, and the sealed holdout.

The loader also recomputes the complete `>=75`-row source-alias census before
opening patches. Because projected Task time and Git commit time are distinct
clocks, the result tests a generator-conditional association on the declared
projection, not native event-time causality.

Prepare the pinned blobless repositories:

```bash
uv run python examples/generator_calibrated_exposure/study.py \
  prepare-repositories \
  --repository-cache \
  outputs/research/2026-07-29-generator-calibrated-exposure/repositories
```

Run the frozen source replay:

```bash
uv run --with duckdb \
  python examples/generator_calibrated_exposure/study.py run \
  --repository-cache \
  outputs/research/2026-07-29-generator-calibrated-exposure/repositories \
  --output \
  outputs/research/2026-07-29-generator-calibrated-exposure/task-mix-results.json
```

Verify raw evidence, create the compact projection, and bind the two:

```bash
uv run python examples/generator_calibrated_exposure/study.py verify \
  --result \
  outputs/research/2026-07-29-generator-calibrated-exposure/task-mix-results.json

uv run python examples/generator_calibrated_exposure/study.py compact \
  --result \
  outputs/research/2026-07-29-generator-calibrated-exposure/task-mix-results.json \
  --summary \
  examples/generator_calibrated_exposure/evidence/task-mix-summary.json

uv run python examples/generator_calibrated_exposure/study.py verify \
  --result \
  outputs/research/2026-07-29-generator-calibrated-exposure/task-mix-results.json \
  --summary \
  examples/generator_calibrated_exposure/evidence/task-mix-summary.json
```

A pass remains a Task-mix result. It does not nominate a Selector or authorize
an Agent-outcome replay without a separate frozen plan.

## Result

The two frozen runs are byte-identical at raw SHA-256
`449e10c1…6ac8`. The compact evidence is
[`evidence/task-mix-summary.json`](evidence/task-mix-summary.json), digest
`26233a42…aa31`.

THY-002 passes both horizons:

- H5 candidate-minus-full-history Brier:
  `-0.006562`, interval `[-0.010743, -0.002855]`, 27/40 repositories;
- H10: `-0.006107`, interval `[-0.009734, -0.002796]`, 28/40 repositories.

Both current-Git-only and yield-only ablations lose with bootstrap upper bounds
below zero. The decision retains the mechanism for a separately frozen
absolute-budget Selection study; `agent_outcome_replay_authorized` remains
false.
