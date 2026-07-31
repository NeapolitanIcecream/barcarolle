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

Full beats both constant estimators. The reference Oracle hides the target
Agent and is favorable in all five repositories at both horizons. This proves
shared same-future response structure, not pre-Origin forecastability.

On the exact SWE-bench Full frame, changing from the legacy panel to the three
modern systems raises Full MAE from `0.078554/0.062579` to
`0.191961/0.150453`. The previous low-MAE regime was therefore substantially
an Agent-population artifact.

Two complete executions are byte-identical. Evidence:

- `docs/experiments/2026-07-31-modern-agent-panel-refresh.md`;
- `examples/modern_agent_panel/plan.json`;
- `examples/modern_agent_panel/evidence/summary.json`.

## Claim Boundary

No Selector was tested or nominated. Oracles use future outcomes. The Tasks end
by 2023 and may be memorized or unlike current workloads. The fixed-Harness
panel is suitable for outcome-open algorithm development, not production or
prospective confirmation.

## Next Action

Freeze one unchanged, no-tuning replay of ordinary recency, stationary response
matching, ALG-015U, and ALG-016U:

1. run primary fixed-Harness direct MAE first;
2. keep each target Agent's entire outcome column out of membership decisions;
3. report candidate-minus-Full, random percentile, repository and Agent
   directions, and reference-Oracle headroom captured;
4. use the modern Full-system lane only as a secondary reversal check;
5. retain a mechanism only if it beats Full at both horizons on primary and
   does not reverse on secondary.

If none survives, begin theory-driven Selector work on the modern panel. No
paid Agent call, Generator work, generic source framework, or core-schema
change is needed.
