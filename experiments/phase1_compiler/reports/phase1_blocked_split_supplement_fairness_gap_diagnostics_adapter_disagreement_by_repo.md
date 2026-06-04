# Blocked Split Supplement Adapter Disagreement By Repo

What happened: scoreable Codex/Kilo outcomes were paired by task ID.
Why it matters: disagreement is benchmark evidence about ACUT configurations, not automatically an error.
Action suggested next: focus no-paid review on click and boltons disagreements while keeping attrs denominator limits visible.

- Paired task count: `59`.
- Disagreement rate: `0.4068`.
- Both pass: `14`.
- Both fail: `21`.
- Codex-only pass: `3`.
- Kilo-only pass: `21`.

## By Repo

- `attrs`: paired `19`, disagreement `0.2632`, Kilo minus Codex delta `0.1579`.
- `boltons`: paired `20`, disagreement `0.45`, Kilo minus Codex delta `0.35`.
- `click`: paired `20`, disagreement `0.5`, Kilo minus Codex delta `0.4`.

## Unpaired

- `attrs__v2__157`: one_or_more_adapter_cells_non_scoreable_or_missing.
