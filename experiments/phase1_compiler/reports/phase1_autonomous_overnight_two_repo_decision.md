# Phase 1 Autonomous Overnight Two-Repo Decision

Generated: `2026-05-22T16:37:47Z`.

Primary decision: `two_repo_paid_validation_complete_insufficient_evidence`.

- Selected repos: `boltons`, `attrs`.
- Selected second repo: `attrs`.
- Paid second-repo ACUT calls made: `true`.
- B_eval scoreable cells: `16`.
- H_future scoreable cells: `15`.
- Policy violations: `1`.
- Observed-or-conservative cost USD: `$62.182946`.
- Predictive validity established: `false`.
- Production ranking: `not_produced`.
- Recommended next runbook: `repair_workspace_acut_scoreability_or_policy_violation_then_rerun_preregistered_two_repo_validation`.

The two-repo paid validation run completed and the metrics were computed from
the frozen design. The run does not meet the predictive-validity threshold
because the preregistered policy gate requires `0` policy violations and the
attrs H_future Kilo cell for `attrs__hist__027` produced a policy violation.
