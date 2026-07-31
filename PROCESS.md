# Barcarolle Cross-Session Handoff

Last updated: 2026-07-31.

Current ledger: `docs/research-improvement-backlog.md`.

## Research Question

For one target Agent and one repository, choose ten historical Tasks so that
the Agent's pass rate on those Tasks is close to its pass rate on the next
Tasks.

Direct future pass-rate MAE is primary. H5 and H10 are separate horizons. Full
history is the no-Selection baseline; random ten-Task subsets calibrate the
sampling space; future-open Oracles measure capacity only.

Runtime remains one Agent, one repository, one Task Pool, and one Selection.
Repositories are separate offline evidence units.

## Active Population

The legacy eleven-Agent SWE-bench Full panel is no longer the primary
development population. Its six early RAG submissions and other old systems
made failures dominant, compressed MAE, and biased algorithm design toward
near-zero prediction.

Primary outcome-open development now uses thirteen models evaluated on all 500
SWE-bench Verified Tasks with the same mini-SWE-agent v2.0.0 Harness:

- Agent pass-rate range `0.562–0.768`, pooled `0.713077`;
- five repositories with minimum history 20;
- 61 H5 Origins and 30 H10 Origins;
- no duplicate Agent vectors.

A secondary diagnostic uses three modern complete systems on all 2,294
SWE-bench Full Tasks: SWE-agent Claude 3.7, Salesforce SAGE, and Sonar
Foundation Agent Claude Opus 4.5. Their pooled pass rate is `0.435629`.

The six project-sealed Verified full-system holdout Agents remain unread.

## Current Evidence

| Fixed mini-SWE-agent v2 | H5 | H10 |
| --- | ---: | ---: |
| Full-history MAE | `0.179527` | `0.129700` |
| Mean random-ten MAE | `0.196332` | `0.155752` |
| Reference-future Oracle MAE | `0.120285` | `0.105282` |
| Target-future Oracle MAE | `0.014755` | `0.013846` |

The unchanged portability replay compared ordinary recency, stationary
response matching, ALG-015U, and ALG-016U. Every candidate is worse than Full
at both horizons:

| Fixed mini-SWE-agent v2 | H5 candidate − Full | H10 candidate − Full |
| --- | ---: | ---: |
| Ordinary recency | `+0.009522` | `+0.035875` |
| Stationary response match | `+0.006449` | `+0.013267` |
| ALG-015U | `+0.012734` | `+0.024607` |
| ALG-016U | `+0.001537` | `+0.011208` |

All four also lose at both horizons on the three-system modern Full panel. No
old response method is retained. Full history is the current development
incumbent.

The replay is byte-identical across two executions. Evidence:

- `docs/experiments/2026-07-31-modern-agent-selector-portability.md`;
- `examples/modern_agent_panel/portability-plan.json`;
- `examples/modern_agent_panel/evidence/portability-summary.json`.

## Claim Boundary

No Selector is nominated. The future-open Oracles show subset capacity, not
pre-Origin forecastability. The Tasks end by 2023 and may be memorized or unlike
current workloads. Both public panels are now outcome-open development
evidence. The six project-sealed Verified full-system Agents remain unread.

## Next Action

Run one bounded decomposition before proposing a new algorithm:

1. separate visible-response forecast error, exact materialization error, and
   target-transfer error for the frozen old methods;
2. preserve repository and horizon directions instead of pooling them away;
3. use the result to freeze one uncertainty-aware distributional coreset that
   predicts response-pattern distributions and anchors uncertainty to Full
   history;
4. gate it on direct MAE versus both Full and random at H5 and H10.

Do not tune the retired methods or open the sealed Agents. No paid Agent call,
Generator work, generic source framework, or core-schema change is needed.
