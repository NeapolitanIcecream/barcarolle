# Research Ledger

Last reviewed: 2026-07-31.

Status: modern public Agent population admitted; all four unchanged
response-family methods failed portability. Full history remains the
development baseline and theory-driven work is next.

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

## Active Approach Registry

| Route | State | Reopening or exit condition |
| --- | --- | --- |
| Fixed mini-SWE-agent v2 public panel | active primary development | Replace only for a newer exact same-Harness cohort or an independent confirmation boundary |
| Modern Full complete-system panel | opened secondary diagnostic | It has now informed the portability decision; do not call it independent confirmation for a new method |
| Legacy Full eleven-Agent panel | archived stress/failure region | Use only to study historical or low-prevalence behavior |
| Ordinary recency, stationary match, ALG-015U, ALG-016U | retired unchanged | Reopen only under a new causal mechanism or independent evidence, not parameter tuning |
| Full history | active development baseline | A Selector must beat it directly at H5 and H10 |
| Forecast/materialization/transfer decomposition | next | Complete once on the modern primary panel before freezing a new family |
| Uncertainty-aware distributional coreset | leading theory route, not frozen | Freeze only after the decomposition specifies the information contract and falsification gate |
| Self-hosted recent open 7B | deferred | Reopen when exact public outcomes appear or public data no longer answers the next question |
| Six sealed Verified full-system Agents | unread confirmation boundary | Open only after an outcome-open candidate passes its development gate |
| New paid Agent outcomes | not needed | Reconsider only after public outcome-open development produces a candidate worth confirming and sealed/public evidence is insufficient |

## Next Cycle

First run a bounded, candidate-free decomposition on the primary panel:

1. compare each frozen method's visible-response forecast with the actual next
   block;
2. measure forecast-to-subset materialization error separately;
3. measure visible-response-to-target-pass-rate transfer by repository,
   Agent, and horizon;
4. identify which error dominates without tuning a method on the diagnostic.

Then freeze one theory-driven family. The leading route should:

- predict a repository-local distribution over other-Agent response patterns,
  rather than only coordinate-wise means;
- keep Full history as an uncertainty anchor;
- make the budget-ten decision against predictive uncertainty and
  target-transfer risk;
- test direct pass-rate MAE against both Full and 20,000 random subsets at H5
  and H10;
- require repository and Agent directional support, not only one pooled
  aggregate.

This route is a hypothesis, not yet `ALG-019` or a frozen plan. Task content,
Git, or repository observables may be added only through an explicit
pre-Origin theory and ablation. Do not perform an unrestricted feature or
constant search on the opened outcomes.

The public fixed-Harness panel remains development data. The modern Full panel
is also opened diagnostic data after the portability replay. Preserve the six
sealed Agents until a candidate passes the outcome-open gate.

No paid call, Generator development, generic source framework, trainer,
scheduler, or core-schema change is needed for this cycle.

## Engineering Triggers

- Optimize checkout only when checkout plus cleanup exceeds 5% of measured
  campaign time.
- Add Agent parallelism only for a measured campaign need, with exact
  attribution and one Result writer.
- Add source-specific certification only for a concrete runnable campaign.
- Structural audit scores alone do not justify splitting modules.
