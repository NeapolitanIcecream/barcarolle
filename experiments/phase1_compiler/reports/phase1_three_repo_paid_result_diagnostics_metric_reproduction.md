# Three-Repo Paid Result Diagnostics Metric Reproduction

Status: `complete`.

What happened: all 120 score-table rows were joined into a sanitized result cube and the primary metrics were recomputed.
Why it matters: the pooled gap and per-repo gaps are not explained by a simple counting or aggregation mistake.
Action suggested next: analyze adapter, split, and sample-size effects instead of changing the completed paid decision.

- Cells: `120`.
- Scoreable cells: `120`.
- Overall pass rate: `0.45`.
- Recomputed pooled B_eval: `0.4`.
- Recomputed pooled H_future: `0.5`.
- Recomputed primary absolute gap: `0.1`.
- Committed primary absolute gap: `0.1`.
- Primary gap matches committed metrics: `True`.

## Per Repo

- `attrs`: B_eval `0.7`, H_future `0.35`, abs gap `0.35`.
- `boltons`: B_eval `0.15`, H_future `0.4`, abs gap `0.25`.
- `click`: B_eval `0.35`, H_future `0.75`, abs gap `0.4`.

## Adapter Pass Rates

- `codex_workspace`: `22/60` = `0.3667`.
- `kilo_workspace`: `32/60` = `0.5333`.
