# Retrospective Predictive-Signal Process

Current step: `Step 4 - Score Join Manifest`.

Completed artifacts:
- experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_score_join_manifest.json

Boundary:
- This is a no-paid retrospective analysis.
- New paid ACUT solver cells run: `false`.
- New paid LLM calls run: `false`.
- Score tables are joined only after `phase1_retrospective_predictive_signal_selection_freeze.json` exists.
- Predictive validity is not established by this run.

Notes:
- Committed score tables were joined only after the selection freeze artifact existed.
