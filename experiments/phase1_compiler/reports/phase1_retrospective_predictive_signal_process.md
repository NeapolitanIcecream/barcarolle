# Retrospective Predictive-Signal Process

Current step: `Step 2 - Window And Cutoff Plan`.

Completed artifacts:
- experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_window_plan.json
- experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_window_plan.md

Boundary:
- This is a no-paid retrospective analysis.
- New paid ACUT solver cells run: `false`.
- New paid LLM calls run: `false`.
- Score tables are joined only after `phase1_retrospective_predictive_signal_selection_freeze.json` exists.
- Predictive validity is not established by this run.

Notes:
- Window and cutoff choices are frozen before score-table terminal outcomes are loaded.
