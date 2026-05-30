# Retrospective Predictive-Signal Process

Current step: `Step 0 - Preflight And Scope Check`.

Completed artifacts:
- experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_preflight.json

Boundary:
- This is a no-paid retrospective analysis.
- New paid ACUT solver cells run: `false`.
- New paid LLM calls run: `false`.
- Score tables are joined only after `phase1_retrospective_predictive_signal_selection_freeze.json` exists.
- Predictive validity is not established by this run.

Notes:
- The current runbook input is untracked in this worktree and is classified separately from generated outputs.
- Existing score tables are treated as read-only inputs and terminal outcomes are deferred until after selection freeze.
