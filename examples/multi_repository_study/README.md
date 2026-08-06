# Multi-repository offline study

This directory answers one research question without changing Barcarolle's
runtime model: can a Selector learned or chosen across projects improve future
prediction when every Task Pool, Origin, and Selection still belongs to exactly
one repository?

Multiple repositories are evidence units only. A normal Barcarolle campaign
continues to compile and select one repository-local Task Pool.

## Frozen inputs

- `portfolio-plan.json` pins the 500-Task SWE-bench Verified source, local
  rolling-Origin rule, repository lineage, and zero-paid-call authority.
- `portfolio.json` is the self-digested 12-repository inventory derived from
  that source. Seven repositories have at least one complete Origin; three
  have at least five.
- `public-panel-plan.json` was committed before opening the selected outcome
  blobs. It pins three official Agent results, two fixed candidate Selectors,
  the no-selection baseline, random calibration, permutation control, and the
  exploratory decision rule.
- `development-plan.json` bounds three direct response-vector probes on the
  opened panel. These are development results, not confirmation.
- `semantic-plan.json` pins the two previously specified ALG-007 rules and one
  already-cached embedding model before the local semantic replay.
- `theory-plan.json` and `theory-audit-plan.json` freeze four mechanism
  families and the post-nomination adversarial audit.
- `agent-panel-extension-plan.json` allocates eight project-sealed public
  Agents to development and preserves six as holdout without reading their
  result blobs.
- `agent-panel-schema-amendment.json` narrowly admits one exact official legacy
  result schema for three exact development blobs without changing the binary
  endpoint.
- `agent-invariant-plan.json` and `adaptive-difficulty-plan.json` freeze the
  cutoff-aware difficulty-state and prequential adaptive mechanisms.
- `scale-sensitivity-plan.json` freezes one common-Origin response surface for
  budgets 5/10/15 and task-count horizons 3/5/10. It preserves the six-Agent
  holdout and forbids choosing the best observed cell.
- `suitability-audit-plan.json` freezes the candidate-free eleven-Agent H5
  source-transfer check. `suitability-audit-summary.json` is its compact
  reproduced evidence; the six-Agent holdout remains sealed.

The portfolio is useful but unbalanced: 68 Origins are possible, while Django
contributes 43. The primary summary therefore averages Origins inside each
repository and then weights repositories equally. Origin-weighted results are
diagnostic only.

## Implementation boundary

- `portfolio.py` validates and derives the repository inventory.
- `aggregate.py` computes repository-first summaries, a repository-cluster
  bootstrap interval, and leave-one-cluster-out diagnostics.
- `public_replay.py` constructs repository-local Origins, normalizes pinned
  public binary results against the full dataset denominator, evaluates the
  fixed Selectors, and runs the random and permutation controls.
- `development.py` screens one compression control and two small
  cross-repository forecast corrections with outer repository folds.
- `embed_local.py` creates an ignored, self-digested embedding artifact from a
  pinned local model snapshot; `semantic.py` evaluates the two frozen semantic
  rules.
- `theory.py` evaluates robust local, joint-response, repository-analog, and
  semantic-trend mechanisms; `theory_audit.py` runs the temporal-null and
  leave-one-Agent audit.
- `panel_extension.py` evaluates the frozen Joint Markov Selection once on the
  outcome-independent eight-Agent allocation.
- `agent_invariant.py` enforces cross-repository source-time cutoffs and
  evaluates the five-state difficulty Markov.
- `adaptive_difficulty.py` makes an Origin-local prequential choice between the
  Markov and stationary difficulty forecasts and records the completed
  cross-repository Origins available at each target cutoff.
- `scale_sensitivity.py` keeps one 56-Origin cohort fixed while varying
  Selection budget and task-count horizon, rematerializes leave-one-Agent
  Selections, and records calendar-span and source-capacity diagnostics.
- `suitability_audit.py` reports full, fixed-trivial, random, exact-oracle,
  repository uncertainty, and circular phase-alignment diagnostics without
  evaluating a candidate Selector.

These are experiment-layer scripts, not a registry, service, Runner extension,
or general multi-repository abstraction. The only reusable contract is the
small `ContrastRow` consumed by the aggregator.

## Replay

The raw parquet and official result files stay under ignored `outputs/`
directories. With those inputs present:

```bash
env PYTHONPATH=src:. \
  outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/harness-env/bin/python \
  examples/multi_repository_study/portfolio.py \
  --dataset outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/source/swe-bench-verified-test-91aa3ed.parquet \
  --output /tmp/barcarolle-portfolio.json
```

```bash
env PYTHONPATH=src:. \
  outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/harness-env/bin/python \
  examples/multi_repository_study/public_replay.py \
  --dataset outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/source/swe-bench-verified-test-91aa3ed.parquet \
  --result-dir outputs/research/2026-07-28-public-multi-repository/official-results \
  --output /tmp/barcarolle-public-panel-results.json
```

Both commands verify pinned file identities and refuse to overwrite an
existing output. The public replay can nominate a fixed route for a later
independent test; it cannot promote a production Selector or establish a
strict-prospective claim.

The completed candidate-free audit reuses only the eleven opened Agent files:

```bash
uv run \
  --with numpy==2.5.1 \
  --with scipy==1.16.3 \
  --with pyarrow==25.0.0 \
  python examples/multi_repository_study/suitability_audit.py run \
  --output outputs/research/2026-07-30-verified-suitability-audit/run.json
```

It verifies every input identity and the zero-authority boundary. Its result is
descriptive because the frozen phase-alignment gate failed; see
[`docs/experiments/2026-07-30-verified-suitability-audit.md`](../../docs/experiments/2026-07-30-verified-suitability-audit.md).

The opened-outcome development replay reuses the same exact local files:

```bash
env PYTHONPATH=src:. \
  outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/harness-env/bin/python \
  examples/multi_repository_study/development.py \
  --dataset outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/source/swe-bench-verified-test-91aa3ed.parquet \
  --result-dir outputs/research/2026-07-28-public-multi-repository/official-results \
  --output /tmp/barcarolle-development-results.json
```

The semantic extractor additionally requires the pinned local model snapshot
and `sentence-transformers==5.1.2`. It makes no network or API call:

```bash
uv run --isolated --python 3.11 \
  --with sentence-transformers==5.1.2 --with pyarrow \
  python examples/multi_repository_study/embed_local.py \
  --dataset outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/source/swe-bench-verified-test-91aa3ed.parquet \
  --dataset-sha256 43ed5a3d1d98da36472c1ade65ddd2085d7b4ff694fcaf6a023a07c5c1f32f21 \
  --model-snapshot path/to/models--sentence-transformers--all-MiniLM-L12-v2/snapshots/c004d8e3e901237d8fa7e9fff12774962e391ce5 \
  --output outputs/research/2026-07-28-public-multi-repository/task-text-embeddings-local.json
```

```bash
env PYTHONPATH=src:. \
  outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/harness-env/bin/python \
  examples/multi_repository_study/semantic.py \
  --dataset outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/source/swe-bench-verified-test-91aa3ed.parquet \
  --result-dir outputs/research/2026-07-28-public-multi-repository/official-results \
  --embeddings outputs/research/2026-07-28-public-multi-repository/task-text-embeddings-local.json \
  --output /tmp/barcarolle-semantic-results.json
```

The completed results and stop decision are interpreted in
[`docs/experiments/2026-07-28-multi-repository-public-study.md`](../../docs/experiments/2026-07-28-multi-repository-public-study.md)
and
[`docs/experiments/2026-07-28-theory-driven-selector-sprint.md`](../../docs/experiments/2026-07-28-theory-driven-selector-sprint.md).

## Sealed-panel and adaptive replay

The eight development result files named by
`agent-panel-extension-plan.json` must be present in the same ignored result
directory as the original three. Do not download the six entries under
`holdout_allocation`.

```bash
env PYTHONPATH=src:. \
  outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/harness-env/bin/python \
  examples/multi_repository_study/panel_extension.py \
  --dataset outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/source/swe-bench-verified-test-91aa3ed.parquet \
  --result-dir outputs/research/2026-07-28-public-multi-repository/official-results \
  --output /tmp/barcarolle-agent-panel-replication.json
```

```bash
env PYTHONPATH=src:. \
  outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/harness-env/bin/python \
  examples/multi_repository_study/agent_invariant.py \
  --dataset outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/source/swe-bench-verified-test-91aa3ed.parquet \
  --result-dir outputs/research/2026-07-28-public-multi-repository/official-results \
  --output /tmp/barcarolle-agent-invariant.json
```

```bash
env PYTHONPATH=src:. \
  outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/harness-env/bin/python \
  examples/multi_repository_study/adaptive_difficulty.py \
  --dataset outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/source/swe-bench-verified-test-91aa3ed.parquet \
  --result-dir outputs/research/2026-07-28-public-multi-repository/official-results \
  --output /tmp/barcarolle-adaptive-difficulty.json
```

Every command refuses overwrite, verifies source and result identities, and
writes a self-digested compact result. Neither difficulty candidate passed all
gates, so the committed decisions forbid opening the holdout.

The final scale audit reuses only the same eleven opened Agent files:

```bash
env PYTHONPATH=src:. \
  outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/harness-env/bin/python \
  examples/multi_repository_study/scale_sensitivity.py \
  --dataset outputs/user-journeys/2026-07-17-swe-bench-verified-pylint-pilot/source/swe-bench-verified-test-91aa3ed.parquet \
  --result-dir outputs/research/2026-07-28-public-multi-repository/official-results \
  --output /tmp/barcarolle-scale-sensitivity.json
```

No budget–horizon cell passed. The interpretation and time-semantics decision
are in
[`docs/experiments/2026-07-28-budget-horizon-sensitivity.md`](../../docs/experiments/2026-07-28-budget-horizon-sensitivity.md).
