# Three-Repo Paid Result Diagnostics Decision

Primary decision label: `three_repo_paid_diagnostics_adapter_stratification_needed`.

What happened: the diagnostic reproduced the paid pilot metrics and found no bookkeeping bug.
Why it matters: the pooled result passed, but adapter behavior, small-sample uncertainty, and some split/source-context weaknesses explain why per-repo gaps are unstable.
Action suggested next: `stratify_or_separate_adapter_reporting` as no-paid follow-up work; paid precision replication should wait until that is addressed.

- New paid cells run: `0`.
- Completed paid decision changed: `False`.
- Predictive validity established: `False`.
- Raw artifacts committed: `False`.

## Research Questions

- RQ1 metrics reproduced: `True`.
- RQ2 bookkeeping error: `not_supported`.
- RQ3 adapter behavior: `supported`.
- RQ4 split imbalance: `partially_supported`.
- RQ5 small-sample uncertainty: `supported`.
- RQ6 task statement quality: `inconclusive`.
- RQ6 source context thinness: `partially_supported`.
- RQ7 verifier/environment: `not_supported`.
- RQ8 next action: `stratify_or_separate_adapter_reporting` (`no_paid`).

No follow-up runbook was drafted or created by this diagnostic run.
