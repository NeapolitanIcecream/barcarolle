# Blocked Split Missing-Cell Supplement Decision

Decision label: `blocked_split_missing_cell_supplement_completed_with_non_scoreable_cells`.

What happened: the selected same-budget blocked split was evaluated as a mixed exploratory table using reused prior cells plus newly run missing cells.
Why it matters: this fills the selected 120-cell table without rerunning cells whose committed prior outcomes already matched the selected task/adapter pairs.
Next paid batch should continue or stop: `complete`.

- Planned new cells: `48`.
- Completed new cells: `48`.
- Reused cells: `72`.
- Combined selected cells: `120 / 120`.
- Scoreable cells: `119`.
- Scoreability rate: `0.9917`.
- Policy violations: `0`.
- Raw oracle exposure: `false`.
- Endpoint compliance: `pass`.
- New token-estimated cost: `USD 26.3480964`.
- Exact provider bill: `unavailable`.

Adapter-stratified results:
- `codex_workspace`: B_eval `0.3448`, H_future `0.2333`, gap `0.1115`.
- `kilo_workspace`: B_eval `0.6333`, H_future `0.5333`, gap `0.1`.

Codex/Kilo disagreement rate: `0.4068`.
Pooled secondary gap: `0.1079`.
Exploratory <= 0.15 diagnostic: `True`.

Interpretation: this is exploratory evidence. The selected split was designed after earlier paid results existed, so this cannot be described as formal preregistered predictive validity or clean pre-outcome validation.
Click caveat: `visible_title_only_minor_risk`.
No raw logs, raw prompts, raw completions, solver workspaces, verifier workspaces, raw diffs, raw test patches, or secrets are committed by this report.
Provider-billed exact cost is not claimed because no bill artifact is available.
