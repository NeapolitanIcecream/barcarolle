# Blocked Split Missing-Cell Supplement Adapter-Stratified Metrics

Status: `complete`.

What happened: combined 72 reused plus new supplement cells were summarized by adapter before pooled summaries.
Why it matters: Codex and Kilo behavior is not interchangeable, so adapter-level results are the primary view.
Next paid batch should continue or stop: `complete`.

## Adapter Results

- `codex_workspace`: cells `60`, scoreable `59`, pass rate `0.2881`, B_eval `0.3448`, H_future `0.2333`, gap `0.1115`.
- `kilo_workspace`: cells `60`, scoreable `60`, pass rate `0.5833`, B_eval `0.6333`, H_future `0.5333`, gap `0.1`.

## Paired Disagreement

- Paired task count: `59`.
- Disagreement rate: `0.4068`.

## Pooled Secondary Summary

- B_eval pass rate: `0.4912`.
- H_future pass rate: `0.3833`.
- Absolute gap: `0.1079`.
- Exploratory <= 0.15 diagnostic: `True`.

Claim boundary: exploratory evidence only. This is not formal preregistered predictive validity.
Click caveat: `visible_title_only_minor_risk`.
