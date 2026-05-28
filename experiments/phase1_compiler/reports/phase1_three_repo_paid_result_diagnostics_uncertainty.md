# Three-Repo Paid Result Diagnostics Uncertainty

Status: `complete`.

What happened: bootstrap intervals and leave-one-out checks show wide uncertainty at the repo level.
Why it matters: the big per-repo gaps can be partly explained by only 10 tasks per repo/split.
Action suggested next: treat the run as pilot evidence and buy precision-target replication only after design/reporting issues are fixed.

- Pooled gap bootstrap 95% interval: `0.0` to `0.2667`.
- Pooled bootstrap share at or below 0.15: `0.7096`.
- Small-sample noise status: `supported`.
- Outlier task/family status: `partially_supported`.
- Leave-one-task pooled gap range: `0.0741` to `0.1278`.
- Leave-one-family pooled gap range: `0.0333` to `0.15`.

## Per Repo Bootstrap Gap Intervals

- `attrs`: `0.05` to `0.65`; median `0.35`.
- `boltons`: `0.0` to `0.5`; median `0.25`.
- `click`: `0.1` to `0.7`; median `0.4`.

## Top Influential Families

- `attrs:_make`: gap without family `0.0333`, delta `0.0667`.
- `click:core`: gap without family `0.15`, delta `0.05`.
- `click:shell_completion`: gap without family `0.0662`, delta `0.0338`.
- `boltons:funcutils`: gap without family `0.1333`, delta `0.0333`.
- `boltons:queueutils`: gap without family `0.0778`, delta `0.0222`.
