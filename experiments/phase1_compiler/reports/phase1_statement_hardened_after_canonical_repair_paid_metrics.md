# Statement-Hardened Paid Metrics

Status: `complete`.

- Total cells: `32` of `32`.
- Scoreable cells: `32`.
- Policy violations: `0`.
- Observed-or-conservative cost: `$9.9235152`.
- Adapter disagreement rate: `0.0625`.
- Old score tables merged: `false`.

## Repo Splits

- `attrs/B_eval`: scoreable `8/8`, pass rate `0.75`, statuses `{'verified_fail': 2, 'verified_pass': 6}`.
- `attrs/H_future`: scoreable `8/8`, pass rate `0.5`, statuses `{'verified_fail': 4, 'verified_pass': 4}`.
- `boltons/B_eval`: scoreable `8/8`, pass rate `0.875`, statuses `{'verified_fail': 1, 'verified_pass': 7}`.
- `boltons/H_future`: scoreable `8/8`, pass rate `0.5`, statuses `{'verified_fail': 4, 'verified_pass': 4}`.

## Adapters

- `codex_workspace`: scoreable `16/16`, pass rate `0.6875`, observed-or-conservative cost `$5.7123912`, median latency `81.075` seconds.
- `kilo_workspace`: scoreable `16/16`, pass rate `0.625`, observed-or-conservative cost `$4.211124`, median latency `40.722` seconds.
