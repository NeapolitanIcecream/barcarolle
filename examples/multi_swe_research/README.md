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

The contract pins the dataset tree and its declared 1.60 GB path set; this
sprint did not download or certify those JSONL bytes. The committed import is
for response-and-time algorithm research. A runnable Task Pool must still
full-byte verify the 39 files and pass source-specific certification.

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

Validate all committed evidence without network access:

```sh
uv run python examples/multi_swe_research/prepare.py verify-evidence
```
