# Phase 1 Future Holdout Decision

Primary decision: `boltons_clean_future_holdout_pilot_complete_insufficient_sample`.

- Paid ACUT calls made: `true`.
- Selected repos: `boltons`.
- Cutoff primary axis: `repo_task_time`.
- B_eval tasks: `boltons__clean_ext__001, boltons__clean_ext__008, boltons__clean_ext__010, boltons__hist__011`.
- H_future tasks: `boltons__clean_ext__017, boltons__hist__022, boltons__hist__023, boltons__hist__027`.
- B_eval scoreable cells: `8`.
- H_future scoreable cells: `8`.
- Policy violations: `0`.
- Observed-or-conservative cost USD: `46.9875638`.
- Incremental observed-or-conservative cost USD: `9.3403206`.
- Predictive validity established: `false`.
- Production ranking: `not_produced`.
- Recommended next runbook: `mine_second_repo_clean_outcome_unseen_supply_for_two_repo_validation`.

## Blockers

- `predictive_validity_min_target_repos_not_met`
- `predictive_validity_min_holdout_scoreable_cells_not_met`
