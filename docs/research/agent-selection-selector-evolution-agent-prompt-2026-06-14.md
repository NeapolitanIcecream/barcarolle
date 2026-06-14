# Prompt For Selector Evolution Agent

Please execute this mandatory runbook end to end:

```text
/Users/chenmohan/gits/barcarolle/docs/research/agent-selection-selector-evolution-runbook-2026-06-14.md
```

The goal is not another diagnostic summary. The goal is to evolve the task
selection algorithm until the demo can support the user-facing Agent-selection
story:

> Selection recommends an Agent, and later/Holdout validates that choice.

Implement and evaluate the selector work needed for that story. Start with
no-paid replay from committed sanitized artifacts. Build strong random
baselines, RSQ, HRD or an equivalent decision-aware selector, and a shared
recommend/abstain/need-more-evidence decision wrapper. Use rolling-origin or
frozen pseudo-future evaluation with leakage masks. Compare MAE, pairwise
ranking, top-1 agreement, recommendation regret, and random-baseline
percentiles.

Do not stop after finding that the current selector is insufficient. Fix the
selector, add tests, rerun evaluation, and continue through every mandatory
package. If the no-paid result is inconclusive only because required cells are
missing, use the paid boundary in the runbook to fill the smallest necessary
frozen grid. Paid calls are capped at 80 new cells and must use `LLM_BASE_URL`
plus `LLM_API_KEY`.

Make focused commits after each package. The final closeout must state whether
the preferred terminal state was achieved, list exact Selection and
later/Holdout pass rates, report MAE versus strong random baselines, report
recommendation regret, state new paid cells and cost, and say exactly what claim
is now supported. Do not ask for manual intervention; choose conservative
fallbacks within the runbook boundaries and document them.

