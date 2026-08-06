# External Benchmark Source Audit

Date: 2026-07-28.

## Decision

Public benchmark data removes the immediate need for paid Agent runs:

1. Use Multi-SWE-bench as the next zero-paid temporal algorithm development
   source. Its original 1,632-Task, 39-repository universe has 36 complete
   public Agent-by-Task outcome vectors.
2. Use SWE-bench Full as a second development source for deeper histories in
   the existing 12 repositories. It has 22 clean public outcome vectors, 11
   with the official `checked` flag. It is not independent confirmation of
   SWE-bench Verified.
3. Pin SWE-rebench V2 for future Task supply and outcome-free research. It has
   hundreds of repositories with usable histories but no complete public
   Agent-result panel.
4. Keep SWE-PolyBench Full at Task-supply status until its gold checks are
   certified and a multi-Agent outcome panel exists. Its Verified split may be
   used as a small confirmation source.
5. Keep SWE-bench Multilingual and SWE-bench-Live as breadth and freshness
   sources. Their repository histories are too sparse for the current
   rolling-Origin protocol.

These decisions supersede the pre-audit ordering that placed SWE-bench Full
first and Multi-SWE-bench behind a metadata inventory. The Multi-SWE-bench
official result repository changed the decision.

## Contract And Scope

The audit tested whether an exact public source supplies:

- repository-local Task histories with explicit time evidence;
- non-overlapping future blocks after at least 20 history Tasks;
- multiple repositories rather than one dominant repository;
- instance-level public Agent results on one exact Task denominator;
- fixed dataset, evaluator, result, license, and lineage identities.

Task totals, repository totals, leaderboard scores, and aggregate model scores
do not satisfy this contract. The audit made no paid API, coding-Agent, or
embedding calls. It did not open the six-Agent SWE-bench holdout or modify the
runtime single-repository model.

The committed
[`inventory-plan.json`](../../examples/external_benchmark_inventory/inventory-plan.json)
freezes four directly executable sources before the row audit.
[`inventory-results.json`](../../examples/external_benchmark_inventory/inventory-results.json)
contains the self-digested result. Its digest is
`f4436fd642f6a229cfbf5dfd0a20e4d5175def8dfaa9a46cd830a41d0e335df8`.

## Task And Origin Supply

The table uses the frozen `research-h3`, `research-h5`, and `research-h10`
protocols: at least 20 history Tasks followed by complete non-overlapping
future blocks. `Origins/repos` reports total Origins and repositories with at
least one Origin.

| Source | Tasks | Raw repositories | H3 Origins/repos | H5 | H10 | Largest H5 share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SWE-bench Verified reference | 500 | 12 | 104/5 | 61/5 | 30/5 | 68.85% |
| SWE-bench Full | 2,294 | 12 | 684/10 | 408/10 | 201/10 | 40.69% |
| SWE-PolyBench Full | 2,110 | 21 | 592/11 | 355/11 | 173/11 | 26.76% |
| Multi-SWE-bench | 1,632 | 39 | 373/13 | 221/13 | 107/11 | 33.94% |
| SWE-rebench V2 | 32,079 | 3,617 | 2,662/265 | 1,534/235 | 695/176 | 5.08% |

The first, second, third, and fifth rows were derived from full-byte verified
source files. The Multi-SWE row uses a pinned 39-file tree manifest, the
official 1,632-Task image manifest, exact terminal-result IDs, and its committed
Task/time index. The 1.60 GB of source JSONL bytes were not downloaded or
certified in this sprint. The current Hugging Face revision also contains later
Python and Kotlin files; they are outside the result denominator and must be
excluded.

SWE-bench Full increases the existing legacy H5 portfolio from 68 to 419
Origins, wide repositories from 7 to 11, deep repositories from 3 to 10, and
reduces Django's Origin share from 63.24% to 39.86%. It adds temporal depth,
not repository independence.

SWE-rebench V2's median repository has four Tasks, so the headline 3,617
repositories overstates usable depth. Its long tail remains useful: 235
repositories have an H5 Origin under the frozen 20-history protocol. The raw
repository count is still an upper bound because renamed and case-variant
slugs require lineage clustering.

## Source-Time Supply

A training Origin is source-time eligible only when its complete future block
ends no later than the target Origin cutoff.

- SWE-bench Full legacy H5: median 142 eligible training Origins from seven
  other repositories. Thirty-nine of 419 target Origins have fewer than three
  training repositories; four have no training Origin.
- Multi-SWE H5: median 75 eligible training Origins from five repositories.
  Seventeen of 221 have fewer than three training repositories; four have none.
- Multi-SWE H10: median 34 eligible training Origins from five repositories.
  Seventeen of 107 have fewer than three training repositories; two have none.
- SWE-rebench V2 legacy H5: median 798 eligible training Origins from 159
  repositories. Twenty-three of 1,871 have fewer than three training
  repositories; three have none.

The Multi-SWE figures above supersede the preliminary inline audit. They are
recomputed from the committed 1,632-row sidecar using the project's existing
definition: a non-target training Origin is available only when its final
future Task is no later than the target's final history Task.

SWE-bench and PolyBench contain native `created_at`. SWE-rebench V2 stores all
32,079 timestamps as timezone-naive strings despite inconsistent data-card
typing; this audit assumed UTC only for capacity calculations. Multi-SWE-bench
has no Task-time field. Its 1,632 GitHub pull-request creation times were
projected from canonical Task IDs and must be labeled
`github_pr_created_at_projected`.

All four sources support source-time-cutoff-safe counterfactual capacity only.
They do not record when historical Agent Results became available.

## Public Agent Results

### Multi-SWE-bench

The pinned
[`multi-swe-bench/experiments`](https://github.com/multi-swe-bench/experiments/tree/6a7d5566f62fa76f4192302cf763051b98e4facc)
revision supplies 36 common configurations:

- three harness families: MSWE-agent, MagentLess, and MopenHands;
- twelve models;
- terminal ID partitions over all seven original languages.

For each configuration,
`completed_ids`, `empty_error_patch_ids`, and `incomplete_ids` are disjoint and
their union equals the fixed 1,632-Task universe. Every `resolved` ID is in
`completed_ids`. All 36 binary vectors are distinct; pairwise disagreement
ranges from 1.41% to 14.46%, with median 6.62%.

Twelve MopenHands language/configuration summaries across nine configurations
underreport `total_instances` by one to three Tasks, while their terminal ID
partitions cover all 1,632 Tasks. The importer validates the fixed Task
manifest and ID partitions, retains every mismatch as a source warning, and
does not trust the scalar total alone.

The case-preserving, sorted-line Task-ID digest is
`cfbe75888d4eb3ff1062debcbc85c1b9f4ac5dcfe1a2fce48f34d116e2a45a21`.
The committed panel digest is
`f2658d12451bdab4108a71cfae5cd5044a5bd312633239c09425378b4b682deb`;
it binds the Task universe, 252 result-file identities, 36 configuration
summaries, 2,913 sparse positive cells, warnings, and disagreement statistics.
An earlier audit checksum, `1310bad…`, lowercased image-derived IDs and used
literal `\n` characters; it is not the Task identity contract.

The
[`Multi-SWE contract`](../../examples/multi_swe_research/contract.json),
[`normalizer`](../../examples/multi_swe_research/prepare.py), and
[`committed evidence`](../../examples/multi_swe_research/evidence/panel-summary.json)
provide the reproducible import boundary. The projected-time digest is
`56eb7dda0d7fd9787b1e77c432572f212726b92abc189df18ab2a4fe6bb815e5`.

Official `verified: true` metadata is weaker than Barcarolle verification.
Older submissions lack complete per-instance verifier logs. Use these results
for counterfactual development, not as independently replayed evidence.

### SWE-bench Full

The pinned
[`SWE-bench/experiments`](https://github.com/SWE-bench/experiments/tree/2f15350cd32becc4569e0d826361048555b605c0/evaluation/test)
revision has 24 Full submissions:

- 22 normalize to complete 2,294-Task binary vectors;
- 11 of the 22 have `checked: true` and form the primary development view;
- two legacy submissions contain duplicate IDs and are excluded.

The checked panel pass rates range from 0.17% to 33.83%, produces 105 response
patterns, and solves 964 Tasks at least once. The 22-vector sensitivity panel
produces 752 response patterns and solves 1,423 Tasks at least once.

All 500 Verified instance IDs occur in Full. Sixteen submission names occur in
both result trees; two disagree on overlapping outcomes. One overlapping Task
also has a different `PASS_TO_PASS` contract. Result reuse must remain bound to
source revision and Check identity.

The Full outcome tree was inspected during this audit, so it is outcome-open.
It can support development and transfer diagnostics, not a newly sealed test.

### Other sources

- SWE-rebench V2 provides no complete 32,079-Task instance-level Agent result
  matrix. Its paper reports only a 300-Task aggregate experiment.
- SWE-PolyBench Full has two 2,110-row terminal vectors, but one actually ran
  only Java and the other only Python; the other languages are padded with
  failures. They are not a crossed two-Agent panel.
- SWE-PolyBench Verified has four result vectors on a 381-Task intersection,
  but only 13 H10 Origins from four repositories.
- SWE-bench Multilingual has public instance-level results but no repository
  reaches the 20-history threshold.

## Source Identity And Quality

| Source | Dataset identity | Main limitation |
| --- | --- | --- |
| SWE-bench Full | [`SWE-bench/SWE-bench@7074ef1`](https://huggingface.co/datasets/SWE-bench/SWE-bench/tree/7074ef12ea2a6f70a228943c1336553333c22786), file SHA-256 `0996c4bd…8df2` | Same source family and repositories as Verified; not human-verified at the Verified level. |
| SWE-PolyBench Full | [`AmazonScience/SWE-PolyBench@d56445f`](https://huggingface.co/datasets/AmazonScience/SWE-PolyBench/tree/d56445f9940eae4e9d2974ec66820c2f1d7754e6), file SHA-256 `17ad661b…08b7` | Full split lacks the Verified split's 100% gold guarantee and lacks a crossed Agent panel. |
| Multi-SWE-bench | [`ByteDance-Seed/Multi-SWE-bench@56ff018`](https://huggingface.co/datasets/ByteDance-Seed/Multi-SWE-bench/tree/56ff018c04a38e27ada1e9d0a6d5839a51f88f0d), original 39 files only | No native Task time; Hugging Face's merged viewer currently fails; image and evaluator provenance vary by submission. |
| SWE-rebench V2 | [`nebius/SWE-rebench-V2@475dd5e`](https://huggingface.co/datasets/nebius/SWE-rebench-V2/tree/475dd5e8703bb5fb22dd3c60b5d038b019eba1e0), file SHA-256 `0e0bf935…d3ad` | Automated certification, naive timestamps, incomplete repository lineage, and no outcome matrix. |

Cross-source independence also requires explicit exclusions:

- PolyBench and Multi-SWE share four repositories and 109 exact Tasks.
- PolyBench and SWE-rebench V2 share five repository slugs and 224 instance
  IDs in the committed inventory.
- SWE-rebench V2 contains 1,243 excess rows in repeated
  repository-plus-base-commit groups.
- 630 SWE-rebench Tasks with a PR URL use a current repository slug different
  from the stored slug; most Tasks do not provide a PR URL, so observed merges
  are a lower bound.

Dataset-level licenses do not replace upstream repository licenses.
SWE-rebench V2 has 348 Tasks with a missing license value and 5,038 marked
`custom-check-github`.

## Infrastructure Decision

The runtime needs no new abstraction:

- each imported repository remains one Task Pool;
- cross-repository fitting and aggregation remain in the experiment layer;
- each source gets one explicit plan, adapter, timestamp evidence mode, result
  normalizer, and exact allowlist;
- lineage and overlap are source sidecars, not a global repository registry;
- complete source files are verified before a prepared package is built;
- public result vectors remain imported Results bound to exact Task and Check
  identity.

This sprint added a direct external-source capacity audit with digest-bound
plans, resumable ignored metadata projections, full-byte source verification,
cross-source overlap checks, and four Origin protocols. It also removed one
static-adapter false assumption: `oracle_source` is now derived from the fixed
source family, preserving the existing SWE-bench Verified value while allowing
SWE-bench Full.

It also implemented the source-specific Multi-SWE research import:

1. fixes the original 39 data paths and the 1,632-Task manifest;
2. stores all 1,632 GitHub PR times as projected provenance;
3. imports the 36 terminal-partition result vectors as 2,913 sparse positive
   cells over an explicit denominator;
4. validates denominator, disjoint terminal states, result membership, and
   source warnings without network access.

This is enough for response-and-time algorithm research. It is not a prepared
or certified Task Pool. Download and full-byte verify the 39 source files only
when a mechanism needs Task content or a runnable Multi-SWE pool.

The next algorithm study must freeze its Multi-SWE gate before replaying
outcomes, run unchanged ALG-007 once as a transfer control, and nominate a new
theory-driven mechanism. It then runs repository-first H5/H10 development with
full history and equal-budget random as separate baselines plus
leave-one-language, leave-one-model-family, and leave-one-harness-family
audits.

No registry, trainer service, generic dataset layer, or multi-repository Runner
is justified.

## Claim Boundary And Exit

The audit establishes that authoritative public sources can supply the next
zero-paid algorithm study. It does not establish that any Selector predicts
future Tasks better than full history.

Multi-SWE and Full outcomes were inspected while choosing them. Algorithms
developed from now on use outcome-open development evidence. Promotion still
requires an independently fixed later source or strict-prospective campaign.
The existing six-Agent SWE-bench holdout remains sealed.

Observed resource use was zero paid calls, about 469 MB of local source
downloads for the four executable inventory sources, and an ignored 2.1 GB
Multi-SWE experiments checkout. The final time projection requires 50 GitHub
GraphQL reads. This sprint issued those reads twice after an output-race rerun;
the importer now refuses an existing output before querying. Raw source files,
complete outcome tables, and external repositories remain ignored. The
committed evidence consists only of digests, summaries, Task/time indexes, and
sparse positive outcomes.
