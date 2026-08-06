# Budget And Future-Horizon Sensitivity

Date: 2026-07-28.

Status: completed zero-paid-call estimand audit. No cell passed the frozen
development gate. The six-Agent holdout remains unread.

## Outcome

The fixed ten-Task Selection budget is not the cause of the failed difficulty
Markov result. The algorithm has no stable favorable region across budgets
`5`, `10`, and `15` and task-count horizons `3`, `5`, and `10`.

The only negative wide result is budget `5`, horizon `10`, at `-0.00379`
candidate-minus-full-history MAE. It is better than 99.97% of equal-budget
random draws, but only two of five repositories improve. All three deep
repositories are harmed at `+0.02550`, and leave-one-Agent rematerialization is
harmful at `+0.01553` with only 3/11 Agents favorable. This cell does not
support choosing budget `5` or horizon `10`.

The experiment therefore closes scale tuning for the current mechanism and
opened outcomes. It does not open the holdout, set a Runner default, or support
the project prediction claim.

## Frozen Design

The plan was frozen before running the grid:

- 500 SWE-bench Verified Tasks and the same eleven opened Agent vectors;
- zero paid, coding-Agent, embedding, and holdout calls;
- one common cohort of 56 Origins from five repositories;
- history begins at 20 Tasks and advances by five Tasks;
- every horizon is a prefix of the same next-ten-Task sequence after the same
  cutoff;
- full local history is the primary baseline;
- 10,000 repository-first equal-budget random draws per cell;
- recency and stationary difficulty matching are controls;
- response-derived Selections are rebuilt while leaving each evaluated Agent
  out;
- repository-first wide and deep summaries use 10,000 cluster-bootstrap
  resamples.

The common cohort prevents a larger horizon from changing the repository or
Origin population. It contains 41 Django Origins, ten SymPy Origins, three
Sphinx Origins, and one Origin each for Matplotlib and scikit-learn.

## Response Surface

Negative values favor Selection.

| Budget | Future Tasks | Markov wide | Stationary wide | Recency wide | Deep | Favorable repositories | Random percentile | LOO-Agent wide | Favorable Agents |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 3 | `+0.02911` | `+0.02583` | `+0.03335` | `+0.02074` | 0/5 | 70.95% | `+0.03946` | 3/11 |
| 5 | 5 | `+0.00113` | `+0.01428` | `+0.02726` | `+0.01552` | 2/5 | 96.58% | `+0.02914` | 4/11 |
| 5 | 10 | `-0.00379` | `+0.02958` | `+0.04438` | `+0.02550` | 2/5 | 99.97% | `+0.01553` | 3/11 |
| 10 | 3 | `+0.01226` | `+0.00193` | `+0.02093` | `+0.01387` | 1/5 | 67.39% | `+0.00855` | 5/11 |
| 10 | 5 | `+0.01287` | `+0.00107` | `+0.02270` | `+0.00782` | 0/5 | 53.97% | `+0.00845` | 3/11 |
| 10 | 10 | `+0.00412` | `+0.00292` | `+0.02231` | `+0.01142` | 1/5 | 89.64% | `+0.00893` | 4/11 |
| 15 | 3 | `+0.00509` | `+0.00107` | `+0.00412` | `+0.00697` | 2/5 | 60.62% | `-0.00025` | 5/11 |
| 15 | 5 | `+0.00777` | `+0.00105` | `+0.00655` | `+0.00638` | 0/5 | 46.71% | `+0.00395` | 4/11 |
| 15 | 10 | `+0.01052` | `+0.00867` | `+0.01171` | `+0.00894` | 0/5 | 50.67% | `-0.00117` | 7/11 |

Every Markov cell has a positive deep result. No cell reaches four favorable
repositories, a `-0.01` wide effect, or 8/11 favorable leave-one-Agent
directions. No adjacent four-cell rectangle passes the gate.

The negative budget-5, horizon-10 macro is driven by the two repositories with
one Origin each: Matplotlib is `-0.02273` and scikit-learn is `-0.07273`.
Django is `+0.02138`, Sphinx `+0.00343`, and SymPy `+0.05168`. Its
origin-weighted result is `+0.02336`, confirming that the negative macro does
not describe the deep histories.

The stationary difficulty control beats Markov in seven of nine cells. The
dynamic transition model adds value only at budget 5 with horizons 5 and 10,
where the deep and Agent-transfer results still fail.

The random comparison answers a different question from the full-history
baseline. Budget `5`, horizon `10` is near the top of the sampled five-Task
space, but full history remains better on three repositories and every deep
repository. The Task Pool contains exploitable sampling structure, while the
current Markov rule does not use it consistently enough to justify
compression.

## Selection Budget

A fixed budget has two meanings:

1. it fixes benchmark execution cost;
2. its compression ratio changes with available history.

The 56 histories range from 20 to 220 Tasks, with median 82.5. The tested
budget-to-history fractions are:

| Budget | Minimum | Median | Maximum |
| ---: | ---: | ---: | ---: |
| 5 | 2.27% | 6.07% | 25% |
| 10 | 4.55% | 12.13% | 50% |
| 15 | 6.82% | 18.20% | 75% |

This variation is a research diagnostic, not a reason to add a percentage
budget type. Users pay for an absolute number of Agent runs, and the existing
`SelectionBudget.max_task_checks` is the direct contract. Future studies must
report compression fractions and test history-depth stability. A ratio-based
algorithm requires an independently specified mechanism or new data; it must
not be fitted by extending this opened grid.

## Future Horizon

Task count controls target sample size but does not control elapsed time. On the
common cohort:

| Future Tasks | Median elapsed days | Minimum | Maximum |
| ---: | ---: | ---: | ---: |
| 3 | 25.7 | 5.0 | 137.4 |
| 5 | 39.5 | 14.2 | 210.5 |
| 10 | 75.6 | 38.1 | 1,336.0 |

The mean absolute Agent pass-rate target difference is `0.0969` between
horizons 3 and 5, `0.0980` between 5 and 10, and `0.1407` between 3 and 10.
The horizon changes the target more than the `0.01` development effect gate.

Longer non-overlapping blocks also reduce source supply:

| Future Tasks | Origins | Eligible repositories |
| ---: | ---: | ---: |
| 3 | 116 | 7 |
| 5 | 68 | 7 |
| 10 | 31 | 5 |
| 15 | 21 | 5 |
| 20 | 14 | 3 |
| 30 | 9 | 2 |

A global calendar duration does not equalize target size. A 30-day window has
median three future Tasks and seven empty Origins. A 90-day window has median
11, but repository medians range from 2.5 for SymPy to 12 for Django. A
180-day window has median 21, while SymPy still has median five.

The runtime already accepts an explicit `TimeRange` for the future window and
retains censored refs. Keep that contract. Do not add a second future-horizon
framework. Research protocols may use task-count blocks to control target
sample size, but must report their realized calendar spans. User-facing
campaigns choose the time range from their evaluation need and report the
resulting Task count; a sparse window is insufficient evidence, not a reason
to invent Tasks.

No algorithm-valid horizon range is established. Horizons `3` through `10`
are the only range examined on a common cohort, and all cells fail. Horizons
above `10` are also source-limited in this dataset. A new source must choose
its horizon from a user-relevant time range and a blinded supply inventory
before outcomes are opened.

## Time And Evidence Semantics

The earlier phrase “calendar-valid” combined different claims. Use these
labels:

- `source-time-cutoff-safe counterfactual`: Task arrival time filters fitting
  data, while public Agent labels are projected to each Task's arrival;
- `strict historical replay`: every Task and Result was available by the
  target cutoff;
- `strict prospective`: Selection is frozen before the future cohort and its
  Results exist.

This study is source-time-cutoff-safe counterfactual evidence. It prevents
later-created Tasks from entering a fit but does not prove that the public
Agent labels existed at the historical cutoff.

User imports are not required to satisfy strict historical replay. A user or
adapter may supply Task availability times and derivation lineage, then run
counterfactual replay. Strict modes are stronger evidence labels used when
their timestamps exist. The Selection algorithm consumes the materialized
history and future boundary; it does not decide whether imported timestamps
are producer-attested or projected.

Changing Task availability times can change history membership,
cross-repository fitting cutoffs, and the resulting Selection. Changing Result
availability can also change response-derived states when strict replay hides
labels that were projected in a counterfactual run. These are intended scenario
changes and must produce new bound identities. This public panel has no
historical Result-availability record, so it cannot measure the strict-replay
counterfactual without new evidence.

## Decision And Next Work

1. Keep Selection budget configurable as an absolute positive integer. Do not
   set `10` as an algorithm-valid default.
2. Keep the existing future `TimeRange`; add no count-or-duration policy
   hierarchy.
3. Report budget-to-history fraction, future Task count, realized calendar
   span, and evidence mode in research results.
4. Retire scale tuning of the difficulty Markov mechanism on this opened
   panel. Its best random percentile does not overcome full-history,
   repository, deep, or Agent-transfer failures.
5. Keep the six-Agent holdout sealed. A new temporal candidate must come from
   an independently derived mechanism or a new source with more independent
   repositories and predeclared horizon demand.
6. Do not request paid calls. Current cached results answered the budget and
   horizon questions.

## Artifacts

- plan:
  `examples/multi_repository_study/scale-sensitivity-plan.json`;
- implementation:
  `examples/multi_repository_study/scale_sensitivity.py`;
- result:
  `examples/multi_repository_study/scale-sensitivity-results.json`;
- plan digest:
  `dd499a18a8bf5270c9c474a26331e32f4bc1e5831cacb9592a85c7d4f2969459`;
- pre-grid plan and algorithm commit: `b26f13a5`;
- result digest:
  `45628a07d327d205a5cca06edfb9e1ac6ca4a13b3e4b2a4b453be878fb65fc2f`;
- cost: zero paid API calls, zero coding-Agent calls, zero embedding calls,
  zero holdout result reads.

The result stores the complete cell summaries, repository rows, random
calibration, leave-one-Agent rematerialization identities, source-capacity
diagnostics, and time-semantics boundary.
