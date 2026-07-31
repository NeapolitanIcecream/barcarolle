# Modern Agent Panel Refresh

Date: 2026-07-31.

Status: complete and reproduced. The fixed-Harness panel is admitted for
outcome-open algorithm development. No Selector was run or nominated.

## Decision

The previous low-MAE regime was substantially a legacy-Agent population
artifact.

Barcarolle can continue algorithm research without a paid call. The official
SWE-bench leaderboard exposes complete per-Task outcomes for thirteen current
models evaluated with the same mini-SWE-agent v2.0.0 Harness. A separate
three-Agent SWE-bench Full lane supplies a larger, heterogeneous complete-system
diagnostic.

The fixed-Harness panel becomes the primary outcome-open development
population. The modern Full systems are a secondary transfer screen. The old
eleven-Agent Full panel remains historical stress evidence and must no longer
rank general-current-Agent Selectors.

## Research Contract

The target was an exact modern public population that can support
repository-local rolling-Origin direct pass-rate MAE. Success required:

1. exact per-Task binary outcomes, not aggregate leaderboard scores;
2. one fixed Harness version in the primary lane;
3. Full history beating both constant estimators at H5 and H10;
4. a future-open budget-ten Oracle beating Full at both horizons;
5. no score-based Agent selection, paid call, sealed holdout read, or Selector
   tuning.

The study does not test a Selector. It cannot establish future workload
validity, prospective causality, or production readiness.

The frozen plan is
[`plan.json`](../../examples/modern_agent_panel/plan.json), digest
`9f2a7004480280638dd250e8e956ace9ab14f4b3512862b188458d52e01b9806`.

## Source And Cohorts

### Fixed Harness

The primary source is the official
[SWE-bench leaderboard data](https://github.com/SWE-bench/swe-bench.github.io/blob/master/data/leaderboards.json)
at commit `15491f17ea8274f55686338291d7da27df4d1bd7`.
The source contains a 500-entry `per_instance_details` map for each selected
row.

The cohort contains every complete unique row whose Harness version is
mini-SWE-agent `2.0.0`: thirteen configurations evaluated from 2026-02-17
through 2026-02-26. One duplicated GPT-5.2 Codex leaderboard folder has one
empty row and one complete row; the frozen completeness rule selects the sole
500-Task row and does not inspect score.

This is a legitimate fixed-Harness comparison because SWE-bench states that its
bash-only lane uses the same mini-SWE-agent configuration for all models and
also warns that v1 and v2 are not necessarily comparable. The study therefore
does not mix versions. See the official
[Verified methodology](https://www.swebench.com/verified.html).

### Complete Systems

The secondary source is the official
[SWE-bench experiments repository](https://github.com/SWE-bench/experiments)
at commit `2f15350cd32becc4569e0d826361048555b605c0`.
The metadata-only rule selected all SWE-bench Full submissions dated 2025 or
later with an explicit model tag and public result blob:

- SWE-agent 1.0 with Claude 3.7 Sonnet, one attempt and checked;
- Salesforce SAGE with Claude Sonnet 4.5 plus GPT-5, two-plus attempts and
  unchecked;
- Sonar Foundation Agent with Claude Opus 4.5, one attempt and unchecked.

This lane deliberately preserves complete system identities. It is not a
fixed-model or fixed-attempt comparison.

### Deferred Open 7B Route

LoopCoder-v2 reports `64.4%` on SWE-bench Verified and `31.0%` on Multi-SWE,
but the project release did not expose a compatible per-Task outcome artifact
in the bounded search. Its checkpoint is about 15 GB and requires a custom
runtime. Reproducing it now would provide less information per unit effort than
the ready official matrix, so this route is deferred rather than treated as
evidence. See the [paper](https://arxiv.org/abs/2606.18023) and
[model card](https://huggingface.co/Multilingual-Multimodal-NLP/LoopCoder-V2).

## Frame And Metric

Both lanes use:

- minimum history: 20 Tasks;
- Selection budget: 10 Tasks;
- complete non-overlapping H5 and H10 future blocks;
- Task order: pull-request `created_at`, then instance ID;
- direct target-Agent absolute pass-rate error before aggregation;
- target Agents and Origins inside repository, then equal repository weight.

The fixed-Harness lane has five common repositories, 61 H5 Origins, and 30 H10
Origins. The Full-system lane has ten repositories, 408 H5 Origins, and 201 H10
Origins.

Full history is the no-Selection baseline. Random uses 20,000 independent
ten-Task draws per Origin. The reference Oracle hides the target Agent and
matches the other Agents' future rates. The target Oracle directly matches the
target Agent's future rate. Both Oracles are future-open diagnostics.

## Results

### Fixed mini-SWE-agent v2

The thirteen Agents have pooled pass rate `0.713077`, ranging from `0.562` to
`0.768`.

| Direct MAE | H5 | H10 |
| --- | ---: | ---: |
| Always zero | `0.680839` | `0.677231` |
| Always one | `0.319161` | `0.322769` |
| Full history | `0.179527` | `0.129700` |
| Mean random ten | `0.196332` | `0.155752` |
| Reference-future Oracle | `0.120285` | `0.105282` |
| Target-future Oracle | `0.014755` | `0.013846` |

Reference-future headroom is `0.059242` at H5 and `0.024418` at H10. The
reference Oracle is favorable in all five repositories at both horizons, for
all thirteen Agents at H5 and ten of thirteen at H10.

Random ten-Task Selections are as good as or better than Full in `9.630%` of
H5 draws and `6.495%` of H10 draws. Full is therefore a meaningful baseline,
but it is not near an extreme sampling-space optimum.

The result is not caused by duplicated model vectors:

- 151 distinct thirteen-Agent response patterns over 500 Tasks;
- zero exactly duplicated Agent pairs;
- mean pairwise disagreement `0.148154`, range `0.088–0.258`;
- unanimous fail Task share `0.114`;
- unanimous pass Task share `0.390`.

All-zero future Agent blocks are `0.50%` at H5 and `0.26%` at H10. The
zero-prediction pathology is absent. All-one blocks are `24.84%` at H5 and
`5.13%` at H10, so always-one must still remain a required diagnostic.

### Modern Full Systems

The three complete systems have pooled pass rate `0.435629`, ranging from
`0.338274` to `0.526155`.

| Direct MAE | H5 | H10 |
| --- | ---: | ---: |
| Always zero | `0.398542` | `0.401729` |
| Always one | `0.601458` | `0.598271` |
| Full history | `0.191961` | `0.150453` |
| Mean random ten | `0.217781` | `0.183394` |
| Reference-future Oracle | `0.155680` | `0.133069` |
| Target-future Oracle | `0.002175` | `0.003542` |

The reference Oracle is favorable for all three Agents and eight of ten
repositories at both horizons. Random matches or beats Full in `0%` of H5
draws and `0.01%` of H10 draws.

### Comparison With The Legacy Panel

On the exact same SWE-bench Full Task frame, the legacy eleven-Agent panel had
future density about `0.10` and Full MAE `0.078554/0.062579`. Replacing only
the Agent population with the three modern systems raises future density to
about `0.446` and Full MAE to `0.191961/0.150453`.

This comparison does not prove that the three modern systems represent every
user. It does establish the causal diagnosis needed for research planning:
the old panel made direct MAE mechanically small and changed which errors were
rewarded. Existing algorithm rankings are conditional on that obsolete
population.

## What The Result Establishes

1. Public data is sufficient for the next outcome-open algorithm cycle; no paid
   Agent run is currently justified.
2. Direct pass-rate MAE on modern Agents has substantial resolution at H5 and
   H10.
3. Full history beats both constant estimators and the mean random ten-Task
   Selection.
4. The Task Pools contain large target-specific subset capacity.
5. Other modern Agents' same-future outcomes contain shared response structure
   that can reduce target-Agent MAE after the future is opened.

## What It Does Not Establish

The reference Oracle uses future outcomes. It proves response geometry, not
that Barcarolle can forecast the correct subset before an Origin. No current
Selector has yet been measured on this population.

SWE-bench Verified and Full mostly contain Tasks created by 2023. Modern models
may have memorized repositories or issues, and the workloads may not resemble a
user's current repository. Recent work explicitly questions how much old
SWE-bench Verified scores measure model memory rather than general repair
ability; this study therefore treats the source as outcome-open development,
not current-workload confirmation. See
[the memory audit](https://arxiv.org/abs/2512.10218).

The Full secondary lane has only three systems, mixes one- and multi-attempt
policies, and includes two unchecked submissions. Agreement with it is a
transfer diagnostic, not confirmation.

## Next Decision

Freeze one unchanged, no-tuning portability replay of ordinary recency,
stationary response matching, ALG-015U, and ALG-016U. Run direct MAE on the
fixed-Harness primary lane first, then use the Full-system lane only as a
secondary reversal check.

This replay establishes the modern incumbent; it does not rehabilitate a method
merely because it beats its obsolete-panel score. If no existing method beats
Full at both horizons, begin theory-driven Selector research on the modern
panel.

## Reproduction

The two complete executions are byte-identical. The compact summary is
[`summary.json`](../../examples/modern_agent_panel/evidence/summary.json).
Raw source files and run outputs remain under ignored `outputs/`.

Verification commands are recorded in
[`README.md`](../../examples/modern_agent_panel/README.md).
