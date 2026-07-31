# Research Ledger

Last reviewed: 2026-07-31.

Status: modern public Agent population admitted; one unchanged portability
replay is next before new algorithm design.

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

## Active Approach Registry

| Route | State | Reopening or exit condition |
| --- | --- | --- |
| Fixed mini-SWE-agent v2 public panel | active primary development | Replace only for a newer exact same-Harness cohort or an independent confirmation boundary |
| Modern Full complete-system panel | active secondary diagnostic | Do not tune on it after primary results are visible |
| Legacy Full eleven-Agent panel | archived stress/failure region | Use only to study historical or low-prevalence behavior |
| Existing Selectors | unchanged portability replay next | Run once without parameter search; retain only mechanisms that beat Full directly |
| New theory-driven Selectors | pending | Open after the unchanged replay establishes the modern incumbent |
| Self-hosted recent open 7B | deferred | Reopen when exact public outcomes appear or public data no longer answers the next question |
| New paid Agent outcomes | not needed | Reconsider only after public outcome-open development produces a candidate worth confirming |

## Next Cycle

Freeze one no-tuning portability replay on the primary panel:

1. compare Full, ordinary recency, stationary response matching, ALG-015U, and
   ALG-016U;
2. keep the target Agent's complete outcome column out of every membership;
3. report direct MAE, candidate-minus-Full, random percentile, repository and
   Agent directions, and reference-Oracle headroom captured;
4. evaluate the unchanged mechanism on the secondary Full-system lane without
   using its outcomes to choose constants;
5. retain an existing mechanism only if it beats Full at both H5 and H10 on the
   primary panel and does not reverse on the secondary lane.

If no existing method clears that screen, use the modern fixed-Harness panel to
develop new theory-driven methods. Do not return to Brier loss or another
surrogate as the selection gate.

No paid call, Generator development, generic source framework, trainer,
scheduler, or core-schema change is needed for this cycle.

## Engineering Triggers

- Optimize checkout only when checkout plus cleanup exceeds 5% of measured
  campaign time.
- Add Agent parallelism only for a measured campaign need, with exact
  attribution and one Result writer.
- Add source-specific certification only for a concrete runnable campaign.
- Structural audit scores alone do not justify splitting modules.
