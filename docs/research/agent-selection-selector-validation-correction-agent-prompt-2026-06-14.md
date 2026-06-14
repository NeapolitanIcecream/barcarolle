# Prompt For Selector Validation Correction Agent

Please execute this correction runbook end to end:

```text
/Users/chenmohan/gits/barcarolle/docs/research/agent-selection-selector-validation-correction-runbook-2026-06-14.md
```

The previous selector-evolution result is not enough: it made the story look
good on the existing boltons Holdout, but it was effectively
hypothesis-generating because selector/variant choice and validation used the
same evidence. Your job is to correct that, not to defend the old result.

Work autonomously through the runbook:

1. Relabel the previous `hrd_70_30` result as development evidence unless you
   independently validate it.
2. Inventory independent no-paid rolling-origin or fresh final-validation
   sources.
3. Freeze a corrected selector protocol before final outcome join or paid
   cells.
4. Run no-paid independent replay if possible.
5. If no-paid replay is insufficient only because cells are missing, run the
   smallest preregistered fresh paid final grid inside the 90-cell cap.
6. Produce a final story and closeout that clearly says whether the corrected
   validation supports the Agent-selection demo story.

Do not stop after a diagnosis. Do not ask for manual intervention. If you face
task-supply sparsity, missing cells, or adapter trouble, choose the conservative
fallback allowed by the runbook and keep going. Do not retune on final
later/Holdout outcomes. Do not claim full predictive validity or global Agent
ranking.

Paid calls, if needed, must use `LLM_BASE_URL` plus `LLM_API_KEY`; never use
fallback auth. Make focused commits after each package. The final closeout must
include exact Selection and later/Holdout pass rates, decision state,
recommendation regret, MAE versus strong random baselines, paid cells/cost,
validation commands, and the exact claim now supported.

