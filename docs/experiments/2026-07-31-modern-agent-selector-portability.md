# Modern-Agent Selector Portability Replay

Date: 2026-07-31.

Status: complete and reproduced. All four unchanged response-family methods are
retired on the modern Agent population. Full history remains the development
baseline; no Selector is nominated.

## Decision

Ordinary recency, stationary response matching, ALG-015U, and ALG-016U do not
transfer from the legacy low-pass-rate Agent population.

Every method has higher direct future pass-rate MAE than Full history at both
H5 and H10 on the fixed-Harness primary panel. Every method is also worse than
Full at both horizons on the modern complete-system panel. The failure is
therefore not a marginal threshold decision.

This does not show that Selection is impossible. The future-open reference
Oracle still beats Full by `0.059242` at H5 and `0.024418` at H10 on the
primary panel. It shows that these pre-Origin response forecasts do not recover
that available structure.

## Frozen Contract

The plan was committed before candidate execution:
[`portability-plan.json`](../../examples/modern_agent_panel/portability-plan.json),
digest
`88288ee7a27249d60a69a1d7038bc95b3078cc20b49af8d6976bd4d16fe75f02`.

The primary outcome is direct target-Agent future pass-rate MAE. Target Agents
and Origins are averaged inside repository, then repositories receive equal
weight. H5 and H10 remain separate. Full eligible repository-local history is
the no-Selection baseline.

For each target Agent, the complete target outcome column is excluded from
membership construction. The candidates may use only:

- repository-local historical Task order;
- the other Agents' historical outcomes available at the Origin;
- a previous future block after it has entered history.

No constant, window, prior, hazard, expert, tie break, horizon, aggregation, or
candidate was changed after a score was read. The six project-sealed Verified
full-system holdout Agents remained unread.

## Candidates

| Candidate | Frozen mechanism |
| --- | --- |
| Ordinary recency | Select the latest ten historical Tasks. |
| Stationary response match | Match the full-history mean response of the other Agents. |
| ALG-015U | Combine full, recent, recent-two-block, and linear other-Agent forecasts with coordinate-wise AdaNormalHedge, then exactly match the forecast. |
| ALG-016U | Use the frozen shared BOCPD change-point forecast for the other Agents, then exactly match the forecast. |

ALG-010 was excluded before execution because it had already lost to Full at
both legacy horizons and adds cross-repository state machinery.

## Primary Results

The primary panel contains thirteen model configurations evaluated on all 500
SWE-bench Verified Tasks with the same mini-SWE-agent v2.0.0 Harness.

### H5

Full-history MAE is `0.179527`.

| Candidate | MAE | Candidate − Full | Repositories better than Full | Agents better than Full | Random as good or better |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary recency | `0.189049` | `+0.009522` | 2/5 | 3/13 | `30.595%` |
| Stationary response match | `0.185976` | `+0.006449` | 3/5 | 4/13 | `22.690%` |
| ALG-015U | `0.192261` | `+0.012734` | 2/5 | 3/13 | `39.510%` |
| ALG-016U | `0.181064` | `+0.001537` | 2/5 | 7/13 | `12.165%` |

### H10

Full-history MAE is `0.129700`.

| Candidate | MAE | Candidate − Full | Repositories better than Full | Agents better than Full | Random as good or better |
| --- | ---: | ---: | ---: | ---: | ---: |
| Ordinary recency | `0.165575` | `+0.035875` | 2/5 | 0/13 | `71.275%` |
| Stationary response match | `0.142967` | `+0.013267` | 1/5 | 2/13 | `26.510%` |
| ALG-015U | `0.154308` | `+0.024607` | 2/5 | 1/13 | `50.560%` |
| ALG-016U | `0.140908` | `+0.011208` | 2/5 | 4/13 | `22.780%` |

ALG-016U is the closest old method, but it is not an incumbent. At H5 it helps
seven of thirteen Agents while losing in three of five repositories; its
repository-equal aggregate remains worse. At H10 it loses by more than one MAE
point and helps only four Agents.

The largest primary instability is repository-specific. At H10, for example,
ALG-016U improves scikit-learn by `0.020280` and SymPy by `0.016260`, but harms
Matplotlib by `0.046795`, Django by `0.024084`, and Sphinx by `0.021701`.
Pooling these directions into one global response trend would hide the failure.

## Secondary Results

The secondary panel contains three modern complete Agent systems on all 2,294
SWE-bench Full Tasks.

| Candidate | H5 MAE | H5 − Full | H10 MAE | H10 − Full |
| --- | ---: | ---: | ---: | ---: |
| Full history | `0.191961` | — | `0.150453` | — |
| Ordinary recency | `0.216691` | `+0.024730` | `0.192096` | `+0.041643` |
| Stationary response match | `0.203244` | `+0.011283` | `0.173601` | `+0.023148` |
| ALG-015U | `0.208195` | `+0.016234` | `0.183287` | `+0.032834` |
| ALG-016U | `0.205867` | `+0.013906` | `0.173103` | `+0.022650` |

No candidate helps any of the three Agents in the repository-equal aggregate.
Only zero or one of ten repositories is favorable per candidate and horizon.

Stationary response matching at H5 is better than `98.785%` of random ten-Task
draws and still loses to Full. Random rank is therefore useful sampling-space
context, but it cannot replace the Full-history gate.

## Interpretation

The replay separates three facts:

1. A budget-ten subset can be much better than Full after future outcomes are
   opened; the reference and target Oracles establish capacity.
2. The old methods often choose subsets better than a typical random subset.
3. Their pre-Origin forecasts are not accurate or stable enough to beat the
   lower-variance Full-history estimator.

The old methods compress the other Agents to coordinate-wise response means.
They do not preserve the joint response-pattern distribution, quantify enough
forecast uncertainty, or protect against repository-specific reversals. The
result does not prove that all three omissions are causal. It identifies them
as the next decomposition targets.

The modern primary panel is outcome-open development data. The secondary panel
has now also been read for this reversal decision and cannot independently
confirm a future method designed in response to these results. Independent
confirmation remains the role of the six unread project-sealed Agents or a new
external evidence boundary.

## Next Research Boundary

Do not tune ALG-015U or ALG-016U on the opened scores. First run a bounded
diagnostic decomposition on the modern primary panel:

1. score each frozen method's visible-response forecast against the actual
   next-block visible response;
2. measure exact materialization error from forecast to selected subset;
3. measure how visible-response error transfers to target-Agent pass-rate
   error by repository and horizon.

Then freeze one theory-driven family, rather than another constant search. The
leading route is an uncertainty-aware distributional coreset:

- forecast a repository-local distribution over historical other-Agent
  response patterns, not only their coordinate means;
- retain a Full-history predictive distribution as the uncertainty anchor;
- choose ten Tasks by a decision rule that controls expected or worst-case
  target pass-rate error under that forecast;
- test direct MAE against both Full and random at H5 and H10.

Task content or repository observables may enter only through an explicit
pre-Origin theory and ablation. They should not be added as an unrestricted
feature search on the opened outcomes.

No paid Agent run is justified before an outcome-open candidate beats Full at
both horizons with repository and Agent directional support.

## Reproduction

Two complete official executions are byte-identical:

- result digest:
  `faef25e163922077b7a1edbd5990d0a47f65e0ac0638a50bf6fdf0807b31bc28`;
- compact summary digest:
  `101e4c3a5992c7a72416a2b30984ed13ae60ff22abf675270c5aea199336eb96`;
- implementation SHA-256:
  `710888e9408b5fca9f4473d141dc0f5b8f3c780829a3399716c3a3f0d421dbb1`.

The first attempted execution stopped before candidate scoring because a
validation check looked for Agent count in the horizon frame instead of using
the bound Agent identities. The correction changed only evidence validation,
was formatted and tested, and preceded both official runs.

A later repository-wide Pyright check required an explicit mixed-JSON type
annotation. One complete pair had already produced the same metrics, but its
source hash was discarded rather than copied forward. The final pair and all
digests above were regenerated after that annotation.

The committed compact evidence is
[`portability-summary.json`](../../examples/modern_agent_panel/evidence/portability-summary.json).
Raw memberships and results remain under ignored `outputs/`.

Resource use: zero paid API calls, zero new Agent runs, zero sealed holdout
reads, and no Generator or core-schema change.
