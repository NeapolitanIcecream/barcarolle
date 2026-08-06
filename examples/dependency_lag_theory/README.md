# Registry-Dated Dependency-Lag Theory

This directory contains the frozen design and reproducibly retired Stage-A
execution for `THY-003`. It contains no Agent outcomes or paid campaign.

`plan.json` defines the completed outcome-free falsification study and its
conditional downstream Agent-outcome contract. Its canonical digest (with
`plan_digest` omitted) is `0126c44a…3d5d`. Stage A failed, so Agent-outcome
replay is prohibited.

`execution-addendum.json` closes mechanical ambiguities in that plan before
Stage A executes. It fixes the source-frame projection, coverage denominator,
lockfile parsing, binary Brier scale, exact distance arithmetic, lock-only
comparison, bootstrap, temporal null, execution order, and terminal-state
semantics. It does not change the candidate or any scientific gate.

`source-feasibility.json` records bounded design evidence from the ignored
SWE-rebench and repository caches. Its npm registry sample is exploratory:
publication times were filtered by historical Origin cutoffs, but the raw
packument responses were not retained and the registry can mutate. The frozen
study replaced that sample with 595 retained and digested raw responses.

`study.py` is the direct example-layer Stage-A runner. Its accepted workflow is:

1. `discover` verifies the parent source and projects all historical
   manifest/lock snapshots without labels;
2. `fetch-registry` retains one full raw packument response for every discovered
   direct package;
3. execution lock `4774fbfe…df673` binds the corrected committed runner,
   dependencies, repository heads, and raw response manifest;
4. `run` executes offline twice from that lock; and
5. `verify` reconstructs the result from frozen raw inputs, while `compact`
   accepts only byte-identical verified results.

Run source commands with `uv run --with duckdb python
examples/dependency_lag_theory/study.py ...`. Discovery and acquisition do not
load reference-patch labels. The run builds and digests every candidate,
lock-only, and circular-null membership before opening the scoring-only labels.

The accepted runs are byte-identical at SHA-256 `02c18c81…01a7`. Compact
evidence is in [`evidence/stage-a-summary.json`](evidence/stage-a-summary.json),
digest `90456efc…1c17`. Source admission passed, but the budget-ten candidate
worsened full-history Brier by `0.009057` at H5 and `0.000879` at H10; the
temporal-null rate was `0.9496`. The route is retired without Agent replay.

An independent audit invalidated the first execution because its reused source
loader read reference patches before membership freeze. The accepted loader
reads only Task identity, time, and base-commit fields. The correction left the
discovery, membership, Origin-row, state, metric, null, and decision payloads
unchanged; only execution/result identities changed.

The cited rationale, collision audit, claim boundary, and recommendation are in
[`docs/experiments/2026-07-29-controlled-cold-start-pre-origin-theory.md`](../../docs/experiments/2026-07-29-controlled-cold-start-pre-origin-theory.md).
