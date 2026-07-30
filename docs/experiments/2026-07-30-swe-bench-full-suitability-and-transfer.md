# SWE-bench Full Suitability and ALG-016U Transfer

Date: 2026-07-30.

Status: complete, reproduced, and independently audited. The source gate
rejected before algorithm execution. No paid call, new Agent run, Generator,
core-schema change, or exact Verified holdout-result read occurred.

## Decision

SWE-bench Full is informative but does not pass the frozen admission gate for
Stage C algorithm research. It clears the resolution, headroom, and
nontrivial-prediction gates. It fails the primary H5 chronology gate:
`p=0.126437 > 0.05`.

ALG-016U was therefore not run. There is no Full-panel ALG-016U MAE, and this
result neither supports nor refutes the algorithm. It refutes the narrower
route “normalize Full, then automatically use it as the next development
boundary.”

Do not delete an Agent, weaken the null, select H10, or add another algorithm
after seeing this result. The frozen terminal state is
`suitability_gate_rejects_before_algorithm`.

## Frozen Evidence

The committed plan is
[`plan.json`](../../examples/swe_bench_full_transfer/plan.json), digest
`1c37db6ebd2b65a4acdb81c4e75aec1fcab54a7db31e84558c7435d5dadc4b32`.
It was committed before the eleven bound result blobs were downloaded or
normalized for this study.

- source: exact 2,294-Task SWE-bench Full test split at dataset revision
  `7074ef12ea2a6f70a228943c1336553333c22786`;
- panel: eleven exact checked official submissions, seven legacy result
  schemas and four current schemas;
- frame: ten repositories with at least 20 history Tasks, 408 H5 Origins and
  201 H10 Origins;
- budget: ten Tasks;
- primary loss: direct future pass-rate MAE;
- aggregation: Agents inside Origin, Origins inside repository, then
  repositories equally;
- controls: always zero, always one, Full eligible history, 20,000
  equal-budget random samples, and an exact future-open budget-ten oracle;
- chronology null: permute complete future blocks jointly within repository,
  destroying their order and adjacency while preserving each block's internal
  Task order and eleven-Agent response vectors.

Task time is projected from pull-request `created_at`. Historical Result
availability is not source-attested. Full is retrospective development
evidence, not prospective or workload-validating evidence.

## Results

| Diagnostic | H5 | H10 |
| --- | ---: | ---: |
| Repositories / Origins | `10 / 408` | `10 / 201` |
| Future outcome density / zero MAE | `0.098671` | `0.099916` |
| Full-history MAE | `0.078554` | `0.062579` |
| Full gain over zero | `0.020117` | `0.037337` |
| Repository-bootstrap interval, Full minus zero | `[-0.029135, -0.010765]` | `[-0.047309, -0.027290]` |
| Equal-budget random MAE | `0.086606` | `0.073798` |
| Full gain over mean random | `0.008052` | `0.011219` |
| Exact budget-ten oracle MAE | `0.013093` | `0.007353` |
| Full-to-oracle headroom | `0.065460` | `0.055226` |
| Joint response patterns | `105` | `105` |
| Block-order null probability | `0.126437` | `0.326837` |

Full is better than the mean random budget-ten benchmark at both horizons.
The 95% ranges of random-minus-Full are `[0.003217, 0.013075]` at H5 and
`[0.004301, 0.018435]` at H10, so Full is better than more than 99.9% of the
frozen random draws. The oracle is much better again. The Task Pool therefore
has a dense, nontrivial selection landscape; the rejection is not caused by
the Multi-SWE always-zero pathology.

The aggregate Full-versus-zero gain is heterogeneous across Agents. It is
favorable for five of eleven Agent-specific rows at both horizons. All six
low-pass RAG submissions are zero-dominated, while the aggregate gain is
carried by AppMap, OpenHands, and the three newer SWE-agent submissions. The
panel average is meaningful, but it is not a universal per-Agent property.

The chronology statistic is Full-history MAE minus always-zero MAE, where a
lower value is favorable. The observed H5 statistic is `-0.020117`; the
permutation mean is `-0.019549`, with interval
`[-0.020563, -0.018580]`. The observed order is favorable, but the plus-one
probability is `253 / 2,001 = 0.126437`. That is not enough to meet the frozen
`0.05` gate. H10 is a required sensitivity, not a substitute primary result.

This null tests block-order persistence. It does not prove that Task content,
change points, or every temporal feature lacks signal. It does show that this
particular public panel does not supply the preregistered evidence needed to
open another algorithm-comparison round.

## Independent Verification

Two complete executions are byte-identical. The normalized outcome matrix
digest is
`24648a989b02b70c9fb06c6417adfdc1a67f473f8186326e9c7afa64f1ef06a8`;
the suitability result digest is
`2f66df63186a6113255ced65e155cce8350aeb9b01eb4c187619e456fccbddf8`;
the compact summary digest is
`b01b8bedc82f5311663a658cbf09ae226fd4895cf2c2171513ae1b68543d60d1`.

An adversarial audit independently rebuilt the source, normalizer, eleven
result vectors, all 609 Origins, Full and fixed controls, random expectations,
and temporal null. A separate expanded per-Task binary MILP—not the
implementation's response-pattern compression—reproduced every oracle and
both aggregate oracle MAEs. It also confirmed that no ALG-016U result artifact
exists.

The compact committed evidence is
[`summary.json`](../../examples/swe_bench_full_transfer/evidence/summary.json).
Raw official result files, Origin rows, random draws, and oracle memberships
remain under ignored output paths.

## Holdout Boundary Correction

The six exact Verified source/Check-specific result blobs remain byte-unread.
That does not mean all six Agent identities remain unseen.

The Full panel exposed per-Task outcomes for `rag-gpt35-20231010`,
`rag-swellama7b-20231010`, and `sweagent-gpt4o-20240728`. Full contains all
500 Verified instance IDs, although Full and Verified use distinct dataset
rows, Checks, and result blobs. Those three identities can no longer support a
pure unseen-Agent confirmation claim. Only `sweagent-gpt4-20240402`,
`sweagent-devstral-20250725`, and `openhands-kimi-k2-20250716` remain clean
under that stronger meaning.

This correction does not change the Full gate result. Removing exposed Agents
and rerunning after seeing the outcome would be post-hoc subset selection. The
append-only
[`evidence-boundary-amendment-1.json`](../../examples/swe_bench_full_transfer/evidence-boundary-amendment-1.json)
records the exact identities and future restriction.

## Consequence and Next Boundary

Stop replaying untested algorithms on the opened Multi-SWE, Verified, Full,
SymPy, and Boltons panels. More scores there would optimize research choices
against already-inspected outcomes without repairing the missing evidence.

The next useful zero-paid work is to specify the smallest new evidence source
that has:

1. repository-local Tasks in the intended coding-work regime;
2. native or defensibly reconstructed Task time;
3. Result availability time or a frozen replay policy;
4. enough independent H5/H10 Origins and repositories for the declared
   dependence unit;
5. a clean Agent panel whose identities are checked against every reserved
   holdout before outcomes are opened.

Keep ALG-016U frozen unchanged for that new boundary. Do not build a generic
source framework or make paid calls until a concrete source passes a
candidate-free feasibility preflight.
