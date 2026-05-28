# Three-Repo Paid Validation Decision

Decision label: `three_repo_paid_pilot_threshold_met`.

What happened: the frozen attrs/boltons/click primary_pilot paid validation was evaluated up to the recorded terminal state.
Why it matters: this records pilot evidence and gates without changing the preregistered primary design after outcomes.
Next paid batch should continue or stop: `complete`.

- Planned cells: `120`.
- Completed cells: `120`.
- Scoreable cells: `120`.
- Scoreability rate: `1.0`.
- Policy violations: `0`.
- Raw oracle exposure: `false`.
- Endpoint compliance: `pass`.
- Cost: `$51.267333` observed/conservative.
- Primary design: `repo_stratified`.
- Primary gap: `0.1`.
- Threshold <= 0.15: `True`.

Predictive validity: not established. This run can only support pilot evidence or a blocker.
Old weighted design: diagnostic only; not promoted to primary.
No raw logs, raw prompts, raw completions, solver workspaces, verifier workspaces, or secrets are committed by this report.
