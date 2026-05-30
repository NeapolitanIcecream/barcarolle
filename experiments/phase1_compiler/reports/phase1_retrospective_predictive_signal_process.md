# Retrospective Predictive-Signal Process

Current step: `Step 3 - Design Registry And Selection Freeze`.

Completed artifacts:
- experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_design_registry.json
- experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_selection_freeze.json
- experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_design_registry.md

Boundary:
- This is a no-paid retrospective analysis.
- New paid ACUT solver cells run: `false`.
- New paid LLM calls run: `false`.
- Score tables are joined only after `phase1_retrospective_predictive_signal_selection_freeze.json` exists.
- Predictive validity is not established by this run.

Notes:
- Designs, seeds, weights, windows, and selections are frozen before score-table outcomes are joined.
