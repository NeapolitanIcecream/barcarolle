# Three-Repo Paid Result Diagnostics Adapter Effects

Status: `complete`.

What happened: Kilo passed more cells than Codex and won most adapter-disagreement tasks.
Why it matters: a single pooled adapter headline hides a meaningful harness effect in this pilot.
Action suggested next: stratify or report adapters separately in future paid summaries.

- Codex pass rate: `22/60` = `0.3667`.
- Kilo pass rate: `32/60` = `0.5333`.
- Kilo minus Codex pass-rate delta: `0.1666`.
- Paired outcomes: `{'both_fail': 22, 'both_pass': 16, 'codex_only_pass': 6, 'kilo_only_pass': 16}`.
- Adapter disagreement rate: `0.3667`.
- Paired sign-test p-value: `0.052479`.
- Explanation status: `supported`.

## Largest Visible Cells

- `codex_workspace`:
  - `attrs` B_eval `0.7`, H_future `0.3`.
  - `boltons` B_eval `0.0`, H_future `0.4`.
  - `click` B_eval `0.1`, H_future `0.7`.
- `kilo_workspace`:
  - `attrs` B_eval `0.7`, H_future `0.4`.
  - `boltons` B_eval `0.3`, H_future `0.4`.
  - `click` B_eval `0.6`, H_future `0.8`.
