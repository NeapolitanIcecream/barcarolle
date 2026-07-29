# Prequential Response Assembly

Date: 2026-07-29.

## Result

The sprint found two useful but different results on the outcome-open
Multi-SWE development panel.

1. `ALG-016U Shared-Change-Point Response Assembly` is the best executed
   unseen-target candidate at H5. It lowers repository-first pass-rate MAE
   from `0.067348` to `0.064013`, a difference of `-0.003335` and a `4.95%`
   relative reduction. Its aggregate point estimate beats the previous
   standard-frame ALG-007 result, it remains favorable versus full history
   after every leave-one-repository-out omission, and it ranks above `99.25%`
   of equal-budget random Selections. The ALG-007 comparison is not itself
   repository-robust. It reverses at H10: `+0.001105` versus full history.
2. The frozen cached-target stationary exact control is simpler and stronger.
   It lowers H5/H10 MAE by `-0.004365`/`-0.003774`, with repository-bootstrap
   intervals entirely below zero, 13/13 and 10/11 repositories favorable, and
   random midranks `0.9986` and `0.99995`. It uses the exact target Agent's
   cached historical Results and therefore does not support an unseen-Agent
   claim.

No preregistered portfolio candidate meets the combined H5/H10 numeric-progress
rule. No method is nominated as a production Selector. The cached-target
control was frozen before outcome scoring but was not an eligible portfolio
winner; its promotion is a post-result KISS decision that needs an independently
frozen follow-up before a confirmation claim.

## Question And Evidence Boundary

The study asks whether a cutoff-safe forecast of historical Agent responses,
followed by exact assembly of ten Tasks, predicts the next repository-local
Task cohort better than all eligible local history.

“Current Task Pool” means the Multi-SWE research projection:

- 1,632 Tasks in 39 repositories;
- 36 complete public Agent configurations and 2,913 positive outcome cells;
- H5: 221 Origins in 13 repositories;
- H10: 107 Origins in 11 repositories;
- minimum history 20 Tasks and Selection budget 10.

Task availability is projected from GitHub pull-request `createdAt`. The study
is source-time-safe counterfactual development evidence, not native Task
arrival or prospective evidence. It does not certify a runnable Task Pool.

For Agent \(a\), Origin \(o\), future horizon \(h\), and selected membership
\(S\), the primary loss is

\[
L_{a,o,h}(S)=
\left|
\operatorname{mean}_{t\in S} y_{a,t}
-
\operatorname{mean}_{t\in F_{o,h}} y_{a,t}
\right|.
\]

Configurations and Origins are averaged within each repository; repositories
then receive equal weight. Candidate-minus-full-history differences are
negative when Selection helps. Full history is the primary baseline.
Equal-budget random Selection measures location in the available sampling
landscape and never replaces that baseline.

Two information contracts remain separate:

- `cached_target`: the exact target Agent has reusable Results on every
  eligible historical Task;
- `unseen_target`: the target Agent column is absent from forecasting and
  materialization; only the other 35 public response columns are visible.

The first contract can compress or report already-cached evidence. It cannot
establish performance for a new Agent or a changed Agent identity.

## Literature And Candidate Choice

The finite portfolio used three established ideas without importing their
surrounding systems:

- Luo and Schapire's
  [AdaNormalHedge](https://proceedings.mlr.press/v40/Luo15.html) motivated
  parameter-free prequential aggregation of full, recent, and linear-drift
  experts.
- Adams and MacKay's
  [Bayesian online change-point detection](https://arxiv.org/abs/0710.3742)
  motivated a shared run-length posterior over visible Agent-response streams.
- Deville and Tillé's
  [cube method](https://doc.rero.ch/record/296198/files/914893.pdf) motivated
  treating finite benchmark construction as a balancing problem. The study
  used a smaller exact L1 mixed-integer program because inclusion-probability
  estimation and a general survey-sampling layer had no justified caller.

The frozen portfolio was:

| ID | Information | Mechanism |
| --- | --- | --- |
| ALG-015C | cached target | AdaNormalHedge scalar forecast, then exact feasible success-count assembly |
| ALG-015U | unseen target | coordinate-wise AdaNormalHedge on the other 35 Agents, then exact L1 response assembly |
| ALG-016U | unseen target | shared-run-length empirical-Bayes BOCPD forecast, then the same exact L1 assembly |

`ALG-016U_greedy` is a diagnostic materializer ablation, not a fourth eligible
candidate. `ALG-017U` repository-held-out LAD drift was deferred before any new
candidate score because the frozen reserve rule did not leave ninety safe
minutes after implementation, dual execution, and audit. No observed result
caused that deferral.

## Pre-Score Contract And Execution

Plan digest:
`f1517fd04a97fc584b8df0f3c3d6be59bd3569a52bbad91694835de15558c84b`.
Semantic addendum:
`8f782ce6421de09064459a13a268689908f88014084dd6e6641d0c7785a0ba2c`.

Independent pre-execution reviews checked:

- standard H5/H10 frame identity and repository-first aggregation;
- complete exclusion of the held-out target column in unseen-target
  memberships;
- delayed prequential update order;
- AdaNormalHedge numerical stability and golden weights;
- BOCPD recursion against enumeration;
- exact L1 assembly against brute force;
- deterministic ties, controls, random seeds, and result vocabulary.

The first attempted materialization stopped before writing a membership or
reading a score. HiGHS reported primary objective
`0.019958536261866413`; direct replay of its integral membership was
`0.01995856483329498`. Binary integrality error and reported MIP gap were zero.
The difference came from auxiliary-slack feasibility tolerance, not membership
rounding.

Execution amendment
`20e25fe7b21f2f95732a131082d54f330aafe90d12c1868b16043bac675ee5bd`
changed only the replay acceptance tolerance to `1e-7` and made the directly
replayed integral-membership objective the strict secondary upper bound. It
did not add a semantic relaxation or change a candidate, forecast, frame,
metric, baseline, or gate.

The fresh execution lock is
`f4dcec2e0c08cc2e1cf8e862a40b4a7ebc1e741326d3f9d02c462d501a81a91d`.
It supersedes the pre-amendment lock and binds the plan, addendum, amendment,
runner, tests, source inputs, runtime, and exact H5/H10 frames.

## Preregistered Candidate Results

| Method | Contract | H5 MAE | H5 − full | H10 MAE | H10 − full |
| --- | --- | ---: | ---: | ---: | ---: |
| Full history | local history | `0.067348` | `0` | `0.052807` | `0` |
| ALG-007 | unseen target | `0.065094` | `-0.002254` | `0.054964` | `+0.002157` |
| ALG-015C | cached target | `0.065113` | `-0.002235` | `0.052561` | `-0.000246` |
| ALG-015U | unseen target | `0.066817` | `-0.000530` | `0.053661` | `+0.000854` |
| ALG-016U | unseen target | `0.064013` | `-0.003335` | `0.053912` | `+0.001105` |
| ALG-016U greedy | unseen diagnostic | `0.064166` | `-0.003181` | `0.054373` | `+0.001567` |

The preregistered numeric-progress rule required H5 to beat ALG-007 on the
same standard frame and H10 to be no worse than full history. None passes:

- ALG-015C improves both horizons but misses ALG-007 at H5 by `0.000019`;
- ALG-015U does not beat ALG-007 at H5 and loses to full history at H10;
- ALG-016U beats ALG-007 at H5 but loses to full history at H10.

The methods remain `bounded_inconclusive`, not refuted by an invented
post-result gate. Development nomination is unavailable because no temporal
null was frozen. The reported nomination-compatibility thresholds are
diagnostics only.

### Robustness And Random Landscape

| Method | Horizon | Repositories favorable | Deep difference | Repository bootstrap 95% | Random midrank |
| --- | ---: | ---: | ---: | ---: | ---: |
| ALG-015C | 5 | 9/13 | `-0.003750` | `[-0.007705, +0.003932]` | `0.96900` |
| ALG-015C | 10 | 5/11 | `-0.001744` | `[-0.005110, +0.004696]` | `0.98405` |
| ALG-015U | 5 | 8/13 | `-0.003874` | `[-0.006163, +0.005980]` | `0.84385` |
| ALG-015U | 10 | 5/11 | `-0.000064` | `[-0.004645, +0.006216]` | `0.95185` |
| ALG-016U | 5 | 9/13 | `-0.005393` | `[-0.007081, +0.000586]` | `0.99250` |
| ALG-016U | 10 | 5/11 | `-0.001920` | `[-0.003372, +0.005552]` | `0.93970` |

Every H5 leave-one-repository-out ALG-016U aggregate remains favorable. Its
bootstrap upper bound is nevertheless slightly above zero, and the H10 wide
direction reverses. The H10 random midrank is still high because random
Selection is usually much worse than full history. This is direct evidence
that random rank describes Task Pool opportunity but cannot establish
algorithm validity by itself.

ALG-016U's H5 candidate-minus-ALG-007 aggregate is `-0.001081`. A post-result
paired repository audit gives only 7/13 favorable repositories and an
approximate 95% interval `[-0.003445, +0.001156]`. “Beats ALG-007” therefore
means the fixed aggregate point estimate, not a stable repository-level
superiority claim.

## Frozen Controls And The KISS Result

The exact full-target controls were frozen before scores:

- cached target: select a feasible success count \(q\) whose \(q/10\) is
  closest to the target Agent's full-history pass rate, then prefer newer Tasks
  within success and failure cells;
- unseen target: select ten Tasks whose other-35-Agent response mean is closest
  in L1 to their full-history response mean.

| Control | Contract | H5 MAE | H5 − full | H10 MAE | H10 − full |
| --- | --- | ---: | ---: | ---: | ---: |
| Stationary exact | cached target | `0.062983` | `-0.004365` | `0.049033` | `-0.003774` |
| Stationary exact | unseen target | `0.065563` | `-0.001785` | `0.055803` | `+0.002996` |
| Ordinary recency | local history | `0.067164` | `-0.000184` | `0.053018` | `+0.000211` |

The cached-target stationary control has:

| Horizon | Favorable repositories | Deep difference | Repository bootstrap 95% | Random midrank | Favorable configurations |
| --- | ---: | ---: | ---: | ---: | ---: |
| H5 | 13/13 | `-0.004868` | `[-0.005984, -0.002773]` | `0.99860` | 32/36 |
| H10 | 10/11 | `-0.004505` | `[-0.005533, -0.001932]` | `0.99995` | 31/36 |

Every leave-one-repository-out aggregate is favorable. H5 is favorable in all
12 model, three harness, and seven language groups; H10 is favorable in 11/12
models and every harness and language group.

This is the strongest observed non-hindsight method in this study, but its
claim is narrow:

- exact Agent identity and historical Result identity must match;
- complete target Results must already exist for the eligible history;
- it says nothing about a new Agent before lazy execution;
- selecting from already-cached Results is primarily benchmark compression and
  reporting, not new evidence acquisition.

The method's target pass rate depends only on the selected historical success
count \(q\). Task identity and the recency tie-break do not change this study's
target-Agent pass-rate MAE. Sparse histories make the quantization substantial:
5,335/7,956 H5 cells and 2,594/3,852 H10 cells select \(q=0\).

The method aligns two finite grids: a ten-Task Selection has pass rates in
tenths, while H5/H10 future cohorts have pass rates in fifths or tenths. Its
gain is therefore a quantized-full estimator under finite-cohort
absolute-loss geometry, not evidence that Task content or recency predicts the
future. A separately frozen finite-horizon predictive-median test should
distinguish stationary quantization from temporal prediction. The current
post-hoc control audit must not be relabeled as preregistered confirmation.

## Mechanism Diagnosis

The adaptive forecast layers did not explain the strongest gains.

- ALG-015C continuous forecasts worsen the full-history scalar forecast by
  `+0.002086` at H5 and `+0.001132` at H10. Its final Selection is worse than
  the cached stationary exact control by `+0.002130` and `+0.003528`.
- ALG-015U has the same aggregate continuous-forecast differences and weak
  direct MAE.
- ALG-016U continuous visible-response forecasts worsen full history by
  `+0.001411` at H5 and `+0.002516` at H10. Despite that, exact response
  assembly improves held-out-Agent H5 MAE. The Selection beats the stationary
  unseen response control by `-0.001551` at H5 and `-0.001891` at H10, but the
  H10 stationary control is itself worse than full history.
- The ALG-016U exact materializer beats greedy-plus-one-swap by `0.000154` at
  H5 and `0.000462` at H10. Exact solving adds measurable but small direct-MAE
  value; the dominant uncertainty is the response target, not optimizer
  optimality.

The evidence supports three conclusions:

1. response-vector assembly contains usable H5 signal for an unseen target;
2. the current BOCPD forecast does not transfer that gain across H10;
3. cached-target stationary compression is stronger than the adaptive
   machinery and should be the KISS reference for that information contract.

It does not support a general change-point claim, a cross-horizon default, or
an unseen-target production Selector.

## Reproduction

Both complete membership runs passed the verifier and are byte-identical:

- logical membership digest:
  `9c5d90dd3c16bc8d82843ee6370e4eba64e68e7d28cf12ff556a06ce6d4d942a`;
- raw SHA-256:
  `a7c0a394efe2a6a95dc62e18e8ea443aa04dadfe5dea699cdd7b9310a2d25dd8`;
- raw size: 67,516,778 bytes.

Both score runs are byte-identical:

- logical result digest:
  `393a8ccdf504aa3495bd0099624935ae36b4afb84d20990d0ad3ff26cfd4c08b`;
- raw SHA-256:
  `04a2475d1b96b53d155f52cb937f7f2c6323fe81e68f216f2d3783f841186487`;
- raw size: 77,645 bytes.

Raw outputs remain ignored under
`outputs/research/2026-07-29-prequential-response-assembly/`. The committed
compact evidence is
[`examples/prequential_response_assembly/evidence/summary.json`](../../examples/prequential_response_assembly/evidence/summary.json).

The reproduction environment is CPython 3.14.0, NumPy 2.5.1, and SciPy 1.16.3.
The principal commands are:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run \
  --with 'numpy==2.5.1' --with 'scipy==1.16.3' \
  python examples/prequential_response_assembly/study.py materialize \
  --output outputs/research/2026-07-29-prequential-response-assembly/memberships.json

PYTHONDONTWRITEBYTECODE=1 uv run \
  --with 'numpy==2.5.1' --with 'scipy==1.16.3' \
  python examples/prequential_response_assembly/study.py verify-memberships \
  --input outputs/research/2026-07-29-prequential-response-assembly/memberships.json

PYTHONDONTWRITEBYTECODE=1 uv run \
  --with 'numpy==2.5.1' --with 'scipy==1.16.3' \
  python examples/prequential_response_assembly/study.py score \
  --memberships outputs/research/2026-07-29-prequential-response-assembly/memberships.json \
  --output outputs/research/2026-07-29-prequential-response-assembly/results.json
```

The sprint used no paid API calls, new Agent-outcome calls, embeddings, or
sealed holdout reads. It changed no core schema or runtime service.

## Decision And Next Work

1. Preserve `ALG-016U` as the best H5 unseen-target development challenger. Do
   not tune its hazard, anchor mass, or horizon after seeing this panel.
2. Retire the AdaNormalHedge layer for cached-target use on this frame. The
   stationary exact control is simpler and better.
3. Freeze one finite-horizon predictive-median cached-target rule before
   another outcome replay. Its primary comparison is the stationary exact
   control, not only full history.
4. Keep cached-target compression and unseen-target pre-execution Selection as
   separate product and research modes.
5. Do not open the six sealed SWE-bench Agents. A confirmation attempt needs a
   separately frozen candidate, temporal or finite-cohort null appropriate to
   its claim, and an independent evidence boundary.
6. Keep exact L1 materialization for evidence runs. A bounded greedy path is
   justified only after a measured runtime requirement and with the observed
   MAE delta reported.
