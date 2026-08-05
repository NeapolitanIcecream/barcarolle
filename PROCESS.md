# Barcarolle Cross-Session Handoff

Last updated: 2026-08-05.

Current ledger: `docs/research-improvement-backlog.md`.

Phase summary: `docs/experiments/2026-08-05-research-phase-summary.md`.

## Research Question

For one target Agent and one repository, choose ten historical Tasks so that
the Agent's pass rate on those Tasks is close to its pass rate on the next
Tasks.

Direct future pass-rate MAE is primary. H5 and H10 are separate. Full history
is the no-Selection baseline; uniform random ten-Task subsets calibrate the
sampling space. Runtime never pools Tasks across repositories.

## Active Data

Primary outcome-open development uses thirteen models evaluated on all 500
SWE-bench Verified Tasks with the same mini-SWE-agent v2.0.0 Harness:

- pass-rate range `0.562–0.768`;
- five repositories;
- 61 H5 Origins and 30 H10 Origins.

An opened secondary diagnostic contains three modern complete systems on all
2,294 SWE-bench Full Tasks. The six project-sealed Verified full-system Agents
remain unread, but their legacy population is not a clean modern confirmation
boundary.

## Current Result

`consensus_rate_match` is the first pre-Origin budget-ten development candidate
to beat Full at both horizons on the frozen repository-equal estimand:

| Fixed mini-SWE-agent v2 | H5 | H10 |
| --- | ---: | ---: |
| Full-history MAE | `0.179527` | `0.129700` |
| Candidate MAE | `0.173387` | `0.115927` |
| Candidate − Full | `-0.006140` | `-0.013774` |
| Favorable repositories | 3/5 | 4/5 |
| Favorable Agents | 10/13 | 11/13 |
| Favorable Origins | 23/61 | 13/30 |

The rule matches the selected Tasks' pooled reference-Agent pass rate to Full
history, then breaks exact matches toward low reference-Agent disagreement.
The target column and current future block are excluded. Two complete runs are
byte-identical; both component ablations lose to Full.

Important limits:

- Origin-weighted delta reverses to `+0.004284` at H5 and `+0.001864` at H10;
- opened three-system internal LOO loses by `+0.014960` and `+0.024006`;
- thirteen primary references predicting those three external systems on the
  common Verified Tasks loses by `+0.017513` and `+0.007707`;
- the candidate was selected after bounded multi-route search on opened
  primary outcomes.

This is a same-Harness, repository-equal development incumbent, not a
production Selector or a general cross-Harness result.

Evidence:

- `docs/experiments/2026-07-31-consensus-rate-selector.md`;
- `examples/modern_agent_panel/consensus-rate-plan.json`;
- `examples/modern_agent_panel/evidence/consensus-rate-summary.json`;
- `examples/modern_agent_panel/evidence/consensus-rate-transfer-diagnostic.json`.

## Next Action

Do not tune the same five-repository score again. Use existing public outcomes
to study reference-to-target population shift:

1. map sensitivity to reference-panel size, target ability, model family, and
   Harness change;
2. separate cold start with no target outcomes from warm start with cached
   target Results;
3. freeze a support/abstention rule or a target-robust mechanism before
   scoring it;
4. seek a new same-Harness target boundary before production nomination.

Importance weighting or AIPW is a research lead, not yet a schema decision,
because it would change the meaning of the raw benchmark pass rate.

No paid Agent call, Generator work, generic source framework, or core-schema
change is needed for the next bounded cycle.
