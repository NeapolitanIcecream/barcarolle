# Blocked Split Supplement Repo Gap Matrix

What happened: B_eval/H_future pass-rate gaps were recomputed by adapter and repo.
Why it matters: the overall gap hides different repo-level shapes for Codex and Kilo.
Action suggested next: use repo-level no-paid analysis for Codex click, Kilo boltons, and Codex attrs denominator sensitivity.

## codex_workspace

- `attrs`: B_eval `0.4444`, H_future `0.3`, gap `0.1444`, labels `moderate_gap, non_scoreable_sensitive`.
- `boltons`: B_eval `0.0`, H_future `0.1`, gap `0.1`, labels `moderate_gap`.
- `click`: B_eval `0.6`, H_future `0.3`, gap `0.3`, labels `high_gap, click_source_caveat_applies`.

## kilo_workspace

- `attrs`: B_eval `0.5`, H_future `0.5`, gap `0.0`, labels `low_gap`.
- `boltons`: B_eval `0.5`, H_future `0.3`, gap `0.2`, labels `moderate_gap`.
- `click`: B_eval `0.9`, H_future `0.8`, gap `0.1`, labels `moderate_gap, click_source_caveat_applies`.

## Driver Summary

- codex_workspace click has the largest adapter/repo gap at 0.3000 and carries the click title-only caveat.
- kilo_workspace boltons has the largest Kilo repo gap at 0.2000.
- codex_workspace attrs has one non-scoreable B_eval cell, so the attrs gap is denominator-sensitive.
