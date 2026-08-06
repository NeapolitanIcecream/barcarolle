# Multi-SWE Research Import

This is one source-specific research import, not a dataset framework. It keeps
each repository as a separate Task Pool while exposing a fixed public outcome
panel to the offline multi-repository experiment layer.

[`contract.json`](contract.json) fixes:

- the original seven-language, 39-file, 1,632-Task dataset universe;
- the exact dataset and experiment revisions;
- the 36 configurations present in every language;
- per-language and global Task-ID digests;
- H5/H10 research schedules, baselines, and transfer audits.

The contract pins the dataset tree and its declared 1.60 GB path set. The
ALG-012 study downloaded the exact revision and verified all 39 Git or Git LFS
objects before projecting issue text. This source verification supports the
research projection only; a runnable Task Pool must still prepare solver and
verifier material and pass source-specific certification.

Normalize the public panel from a checkout of the pinned experiments revision:

```sh
uv run python examples/multi_swe_research/prepare.py panel \
  --experiments-root /path/to/multi-swe-bench-experiments \
  --output outputs/research/multi-swe-public-panel
```

The command rejects denominator drift, duplicate or overlapping terminal
states, unverified metadata, missing resolved membership, changed Task IDs, and
duplicate outcome vectors. It writes a small summary plus Task and outcome
JSONL files. The committed `evidence/` directory keeps only the Task index,
sparse positive outcomes, summaries, and projected times; the 58,752-cell
terminal-state table stays ignored.

The source dataset has no native Task timestamp. After panel normalization,
project GitHub pull-request creation times with the authenticated `gh` CLI:

```sh
uv run python examples/multi_swe_research/prepare.py project-times \
  --task-universe outputs/research/multi-swe-public-panel/task-universe.jsonl \
  --observed-at 2026-07-28T00:00:00Z \
  --output outputs/research/multi-swe-task-times
```

Projected `createdAt` values support source-time-safe counterfactual research
only. They do not prove that historical Agent outcomes were available at those
cutoffs. Public terminal partitions are development evidence, not Results
independently replayed under Barcarolle verification.

The frozen ALG-012 study needs Task text but not patches or tests. From a
checkout of the pinned dataset revision with all 39 contract paths
materialized:

```sh
uv run python examples/multi_swe_research/prepare.py project-content \
  --dataset-root /path/to/Multi-SWE-bench \
  --task-universe examples/multi_swe_research/evidence/task-universe.jsonl \
  --output outputs/research/2026-07-28-multi-swe-task-content
```

This command verifies Git blobs and Git LFS SHA-256 identities before retaining
only sorted `resolved_issues` numbers, titles, and bodies. The 1.60 GB checkout
and text rows remain ignored. The committed
`evidence/task-content-manifest.json` binds the 39-file manifest, 1,632 Task
texts, exclusions, and zero-paid resource boundary.

Build the ignored, pinned local embeddings without network model access:

```sh
uv run --with 'sentence-transformers==5.1.2' \
  python examples/multi_swe_research/semantic_selector.py embed \
  --task-content outputs/research/2026-07-28-multi-swe-task-content/task-content.jsonl \
  --model-snapshot /path/to/c004d8e3e901237d8fa7e9fff12774962e391ce5 \
  --output outputs/research/2026-07-28-multi-swe-task-embeddings.json
```

The committed `evidence/embedding-manifest.json` binds the complete ignored
artifact and vector values. It reuses the frozen local ALG-007 model rather
than adding a representation search.

Materialize the outcome-free memberships and task-space audit:

```sh
uv run --with 'numpy==2.5.1' \
  python examples/multi_swe_research/semantic_selector.py task-space \
  --task-content outputs/research/2026-07-28-multi-swe-task-content/task-content.jsonl \
  --task-times examples/multi_swe_research/evidence/task-times.jsonl \
  --embeddings outputs/research/2026-07-28-multi-swe-task-embeddings.json \
  --output outputs/research/2026-07-28-multi-swe-task-space-results.json
```

Only after the plan and memberships are frozen, join the opened public outcome
panel:

```sh
uv run --with 'numpy==2.5.1' \
  python examples/multi_swe_research/semantic_selector.py outcome \
  --task-content outputs/research/2026-07-28-multi-swe-task-content/task-content.jsonl \
  --task-times examples/multi_swe_research/evidence/task-times.jsonl \
  --task-space-results outputs/research/2026-07-28-multi-swe-task-space-results.json \
  --panel-summary examples/multi_swe_research/evidence/panel-summary.json \
  --resolved-outcomes examples/multi_swe_research/evidence/resolved-outcomes.jsonl \
  --output outputs/research/2026-07-28-multi-swe-semantic-outcome-results.json
```

The raw memberships and replay rows remain ignored. The committed
`evidence/selector-study-summary.json` binds both raw artifacts and records the
failed task-space and outcome gates. It is development evidence, not
independent confirmation.

After ALG-012 was closed, a separate plan froze an exact budget-ten hindsight
support diagnostic. Reproduce it with:

```sh
uv run --with 'scipy==1.16.3' \
  python examples/multi_swe_research/hindsight_diagnostic.py run \
  --task-content outputs/research/2026-07-28-multi-swe-task-content/task-content.jsonl \
  --task-times examples/multi_swe_research/evidence/task-times.jsonl \
  --task-space-results outputs/research/2026-07-28-multi-swe-task-space-results.json \
  --outcome-results outputs/research/2026-07-28-multi-swe-semantic-outcome-results.json \
  --panel-summary examples/multi_swe_research/evidence/panel-summary.json \
  --resolved-outcomes examples/multi_swe_research/evidence/resolved-outcomes.jsonl \
  --output outputs/research/2026-07-28-multi-swe-hindsight-results.json
```

The command solves one exact response-pattern MILP per Origin and verifies the
result against the selected Task identities. The raw solutions stay ignored;
`evidence/hindsight-summary.json` binds their digest. This is leaked hindsight
support for capacity diagnosis, never a runnable Selector or training target.
After producing a second raw result at a different ignored path, mechanically
rebuild and verify the committed summary:

```sh
uv run python examples/multi_swe_research/hindsight_diagnostic.py \
  verify-summary \
  --results outputs/research/2026-07-28-multi-swe-hindsight-results.json \
  --reproduction-results outputs/research/2026-07-28-multi-swe-hindsight-reproduction.json \
  --summary examples/multi_swe_research/evidence/hindsight-summary.json
```

ALG-013 tests whether other repositories can make the frozen sentence
embedding response-relevant. Its main gate stops before forecasting when the
repository-held-out response AUC is not stable:

```sh
uv run --with 'numpy==2.5.1' \
  python examples/multi_swe_research/response_signal.py \
  --task-content outputs/research/2026-07-28-multi-swe-task-content/task-content.jsonl \
  --task-times examples/multi_swe_research/evidence/task-times.jsonl \
  --embeddings outputs/research/2026-07-28-multi-swe-task-embeddings.json \
  --panel-summary examples/multi_swe_research/evidence/panel-summary.json \
  --resolved-outcomes examples/multi_swe_research/evidence/resolved-outcomes.jsonl \
  --output outputs/research/2026-07-28-multi-swe-response-signal-results.json
```

The separately frozen history diagnostic cannot reopen ALG-013. Its corrected
negative control circularly shifts each complete 36-dimensional Task response
vector inside its repository:

```sh
uv run --with 'numpy==2.5.1' \
  python examples/multi_swe_research/response_signal.py \
  --mode diagnose-history \
  --task-content outputs/research/2026-07-28-multi-swe-task-content/task-content.jsonl \
  --task-times examples/multi_swe_research/evidence/task-times.jsonl \
  --embeddings outputs/research/2026-07-28-multi-swe-task-embeddings.json \
  --panel-summary examples/multi_swe_research/evidence/panel-summary.json \
  --resolved-outcomes examples/multi_swe_research/evidence/resolved-outcomes.jsonl \
  --rejected-results outputs/research/2026-07-28-multi-swe-response-signal-results.json \
  --output outputs/research/2026-07-28-multi-swe-response-history-diagnostic-corrected.json
```

ALG-014 then removes Task text and tests whether leave-one-configuration
response difficulty plus a prequential full/recent expert predicts the next
cohort:

```sh
uv run --with 'numpy==2.5.1' \
  python examples/multi_swe_research/response_composition.py \
  --task-content outputs/research/2026-07-28-multi-swe-task-content/task-content.jsonl \
  --task-times examples/multi_swe_research/evidence/task-times.jsonl \
  --panel-summary examples/multi_swe_research/evidence/panel-summary.json \
  --resolved-outcomes examples/multi_swe_research/evidence/resolved-outcomes.jsonl \
  --output outputs/research/2026-07-28-multi-swe-response-composition-results.json
```

Run each command twice at distinct ignored paths, then rebuild and verify the
compact evidence summary:

```sh
uv run python examples/multi_swe_research/pre_origin_evidence.py verify \
  --response-results outputs/research/2026-07-28-multi-swe-response-signal-results.json \
  --response-reproduction outputs/research/2026-07-28-multi-swe-response-signal-reproduction.json \
  --history-diagnostic outputs/research/2026-07-28-multi-swe-response-history-diagnostic-corrected.json \
  --history-reproduction outputs/research/2026-07-28-multi-swe-response-history-diagnostic-corrected-reproduction.json \
  --composition-results outputs/research/2026-07-28-multi-swe-response-composition-results.json \
  --composition-reproduction outputs/research/2026-07-28-multi-swe-response-composition-reproduction.json \
  --summary examples/multi_swe_research/evidence/pre-origin-signal-summary.json
```

Validate all committed evidence without network access:

```sh
uv run python examples/multi_swe_research/prepare.py verify-evidence
```
