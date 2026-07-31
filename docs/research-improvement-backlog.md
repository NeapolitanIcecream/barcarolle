# Research Ledger

Last reviewed: 2026-07-31.

Status: the first modern-panel outcome-open candidate beats Full at H5 and H10
under the frozen repository-equal estimand, but reverses under Origin weighting
and fails opened cross-system transfer. Reference-to-target population shift is
the next research question.

`PROCESS.md` is the short handoff. The legacy-panel research record is
preserved in
[`research-improvement-backlog-2026-07-31-legacy-panel.md`](research-improvement-backlog-2026-07-31-legacy-panel.md).
Do not amend archived evidence.

## Goal

For one target Agent and one repository, select ten historical Tasks whose
target-Agent pass rate is closer than Full history to the Agent's pass rate on
the next Tasks.

Direct future pass-rate MAE is primary. H5 and H10 are reported separately.
Full history is the no-Selection baseline. Uniform random ten-Task subsets
calibrate the sampling space. Future-open Oracles measure capacity and are not
Selectors.

The deployment unit remains one Agent and one repository. Multiple repositories
are offline evidence units; Barcarolle does not combine their Tasks at runtime.

## Methodology Correction

The earlier development population was dominated by six 2023–2024 RAG
submissions and other early Agent systems. Its low outcome prevalence compressed
direct MAE and rewarded near-zero prediction. Algorithms optimized on that
population are historical candidates, not evidence about current Agents.

Agent identity now includes model, Harness and version, inference policy,
attempt count, and other material runtime settings. Parameter count or model
name alone does not define a comparable Agent.

The primary research population must use exact public per-Task outcomes. An
aggregate leaderboard score is insufficient for rolling-Origin research.

## Active Data

### Primary: fixed Harness

Thirteen model configurations use the same mini-SWE-agent v2.0.0 Harness on all
500 SWE-bench Verified Tasks:

- pooled pass rate `0.713077`; Agent range `0.562–0.768`;
- five repositories on the common minimum-history-20 frame;
- 61 H5 Origins and 30 H10 Origins;
- 151 distinct response patterns, no duplicate Agent vectors, and mean pairwise
  disagreement `0.148154`.

This is the active outcome-open algorithm-development population. It isolates
model differences better than arbitrary full-system submissions, but its Tasks
end in 2023 and may be memorized or otherwise unrepresentative of a current
workload.

### Secondary: complete systems

Three modern SWE-bench Full submissions provide 2,294-Task vectors:

- SWE-agent 1.0 with Claude 3.7 Sonnet;
- Salesforce SAGE with Claude Sonnet 4.5 and GPT-5, two-plus attempts;
- Sonar Foundation Agent with Claude Opus 4.5.

Their pooled pass rate is `0.435629`, with Agent range `0.338274–0.526155`.
The frame has ten repositories, 408 H5 Origins, and 201 H10 Origins. This lane
tests transfer to heterogeneous realistic systems. Two submissions are not
officially checked, and the lane is not an apples-to-apples model comparison.

The six project-sealed Verified full-system holdout Agents remain unread.

## Current Measurements

| Fixed mini-SWE-agent v2 panel | H5 | H10 |
| --- | ---: | ---: |
| Always-one MAE | `0.319161` | `0.322769` |
| Full-history MAE | `0.179527` | `0.129700` |
| Mean random-ten MAE | `0.196332` | `0.155752` |
| Random as good as Full | `9.630%` | `6.495%` |
| Reference-future Oracle MAE | `0.120285` | `0.105282` |
| Target-future Oracle MAE | `0.014755` | `0.013846` |

The reference Oracle hides each target Agent and selects against the other
twelve Agents' future response rates. It is favorable in all five repositories
at both horizons, for all thirteen target Agents at H5 and ten of thirteen at
H10. This establishes shared same-future response structure, not a pre-Origin
forecast.

| Modern Full-system panel | H5 | H10 |
| --- | ---: | ---: |
| Best fixed-constant MAE | `0.398542` | `0.401729` |
| Full-history MAE | `0.191961` | `0.150453` |
| Mean random-ten MAE | `0.217781` | `0.183394` |
| Reference-future Oracle MAE | `0.155680` | `0.133069` |
| Target-future Oracle MAE | `0.002175` | `0.003542` |

The two complete executions are byte-identical. Evidence:

- [`experiments/2026-07-31-modern-agent-panel-refresh.md`](experiments/2026-07-31-modern-agent-panel-refresh.md);
- `examples/modern_agent_panel/plan.json`;
- `examples/modern_agent_panel/evidence/summary.json`.

### Unchanged Selector portability

| Fixed mini-SWE-agent v2 | H5 MAE | H5 − Full | H10 MAE | H10 − Full |
| --- | ---: | ---: | ---: | ---: |
| Full history | `0.179527` | — | `0.129700` | — |
| Ordinary recency | `0.189049` | `+0.009522` | `0.165575` | `+0.035875` |
| Stationary response match | `0.185976` | `+0.006449` | `0.142967` | `+0.013267` |
| ALG-015U | `0.192261` | `+0.012734` | `0.154308` | `+0.024607` |
| ALG-016U | `0.181064` | `+0.001537` | `0.140908` | `+0.011208` |

All four methods are also worse than Full at both horizons on the modern
three-system Full panel. No method clears the frozen retention rule.

ALG-016U is closest on the primary panel, but its direction is not stable: it
helps 7/13 Agents and only 2/5 repositories at H5, then 4/13 Agents and 2/5
repositories at H10. It is retired unchanged, not retained as an incumbent.

Random rank does not rescue a method that loses to Full. For example,
stationary response matching at secondary H5 beats `98.785%` of random subsets
while its MAE remains `0.011283` worse than Full.

Two complete executions are byte-identical. Evidence:

- [`experiments/2026-07-31-modern-agent-selector-portability.md`](experiments/2026-07-31-modern-agent-selector-portability.md);
- `examples/modern_agent_panel/portability-plan.json`;
- `examples/modern_agent_panel/evidence/portability-summary.json`.

### Consensus-rate development candidate

`consensus_rate_match` matches the selected Tasks' pooled reference-Agent pass
rate to Full history, then breaks exact matches toward low reference-Agent
disagreement. It excludes the target Agent before aggregation and uses the same
rule at H5 and H10.

| Fixed mini-SWE-agent v2 | H5 | H10 |
| --- | ---: | ---: |
| Full-history MAE | `0.179527` | `0.129700` |
| Candidate MAE | `0.173387` | `0.115927` |
| Candidate − Full | `-0.006140` | `-0.013774` |
| Favorable repositories | 3/5 | 4/5 |
| Favorable Agents | 10/13 | 11/13 |
| Favorable Origins | 23/61 | 13/30 |
| Origin-weighted candidate − Full | `+0.004284` | `+0.001864` |

Every repository leave-one-out result stays favorable. Both component
ablations lose to Full. Two complete primary runs are byte-identical and all
target/future information audits pass.

The result remains outcome-open development evidence. The candidate was chosen
after a bounded multi-route search; the local META family alone had 72 experts
and 68 distinct trajectories. It must not be treated as an independent
discovery.

Opened transfer diagnostics fail:

| Transfer diagnostic candidate − Full | H5 | H10 |
| --- | ---: | ---: |
| Three Full systems, internal LOO | `+0.014960` | `+0.024006` |
| Thirteen primary references → three external targets on common Verified Tasks | `+0.017513` | `+0.007707` |

This is consistent with reference-target non-exchangeability or Harness shift.
It does not erase the repository-equal primary result; it prevents promotion to
a general or production Selector.

Evidence:

- [`experiments/2026-07-31-consensus-rate-selector.md`](experiments/2026-07-31-consensus-rate-selector.md);
- `examples/modern_agent_panel/consensus-rate-plan.json`;
- `examples/modern_agent_panel/evidence/consensus-rate-summary.json`;
- `examples/modern_agent_panel/evidence/consensus-rate-transfer-diagnostic.json`.

## Active Approach Registry

| Route | State | Reopening or exit condition |
| --- | --- | --- |
| Fixed mini-SWE-agent v2 public panel | active primary development | Replace only for a newer exact same-Harness cohort or an independent confirmation boundary |
| Modern Full complete-system panel | opened secondary diagnostic | It has now informed the portability decision; do not call it independent confirmation for a new method |
| Legacy Full eleven-Agent panel | archived stress/failure region | Use only to study historical or low-prevalence behavior |
| Ordinary recency, stationary match, ALG-015U, ALG-016U | retired unchanged | Reopen only under a new causal mechanism or independent evidence, not parameter tuning |
| Full history | active no-Selection baseline | Every Selector must still beat it directly; random rank is diagnostic only |
| Forecast/materialization/transfer decomposition | completed | Transfer dominated; exact materialization was not the limiting error |
| Distributional, MMD, semantic, and IRT routes | closed for this opened panel | Reopen only under a new mechanism or evidence boundary |
| `consensus_rate_match` | outcome-open development candidate | Retain as the primary-panel incumbent; do not deploy or tune on the same five-repository score |
| Reference-to-target population shift | next | Map cold-start support and freeze one robust or abstaining mechanism |
| Warm-start target calibration | research option | Use only cached target outcomes; do not assume they exist in cold start |
| Self-hosted recent open 7B | deferred | Reopen when exact public outcomes appear or public data no longer answers the next question |
| Six sealed Verified full-system Agents | unread but population-mismatched | Do not call them clean modern confirmation; open only for a prespecified question they can answer |
| New paid Agent outcomes | not needed yet | Reconsider only after existing outcomes identify a candidate and a compatible confirmation population |

## Next Cycle

Stop optimizing the same primary repository-equal score. Use the paid-free
public outcomes to answer the transfer question:

1. map candidate and Full error against reference-panel cardinality, held-out
   target ability, model family, and Harness change;
2. distinguish cold start, where no target outcomes exist, from warm start,
   where the Result Store already contains target outcomes on historical
   Tasks;
3. define a support or abstention rule for cold-start targets that are not
   represented by the reference panel;
4. freeze one robust cold-start mechanism or one explicitly warm-start
   mechanism before scoring it;
5. seek an independent same-Harness target boundary before any production
   nomination.

Importance weighting or AIPW is a literature-backed lead, not an automatic
engineering change. A weighted estimator would change the semantics of the
reported benchmark score and must first be reconciled with the raw pass-rate
contract.

The public fixed-Harness panel and modern Full panel are both opened development
or diagnostic data. The six sealed Agents remain unread, but their legacy
population is not a clean answer to the modern target-shift question.

No paid call, Generator development, generic source framework, trainer,
scheduler, or core-schema change is needed for this cycle.

## Engineering Triggers

- Optimize checkout only when checkout plus cleanup exceeds 5% of measured
  campaign time.
- Add Agent parallelism only for a measured campaign need, with exact
  attribution and one Result writer.
- Add source-specific certification only for a concrete runnable campaign.
- Structural audit scores alone do not justify splitting modules.
