# Phase 1 Historical Environment Synthesis Decision

Primary decision label: `integrate_subgates_and_move_to_third_repo`.

Plain-language summary: Historical environments improved diagnosis or recovered some tasks, but the existing third-repo local artifacts do not yet meet the 30-task gate.

## Required Fields

- known_failure_sample_size: 36
- profiles_tried: py310_pytest7_editable, py311_current_editable, py37_pytest4_pythonpath, py38_pytest_lt4_pythonpath, py39_pytest_lt5_pythonpath
- confirmed_recovered_eligible_attrs: 2
- confirmed_recovered_eligible_boltons: 4
- same_signature_projected_recoverable_attrs: 0
- same_signature_projected_recoverable_boltons: 0
- third_repo_screened: toolz, humanize
- third_repo_certified_candidate_count: 12
- recommended_next_action_category: third_repo_screening_needs_broader_local_candidate_supply
- paid_acut_calls_made: False
- paid_llm_calls_made: False

## Research Questions

- RQ1: uv isolated historical commands ran outside the Barcarolle project where uv could provide the requested Python and dependency profile.
- RQ2: 8 sampled attrs/boltons known reference_pass failures recovered reference_pass under bounded historical profiles.
- RQ3: Remaining failures were subclassified as {'reference_collect_failed': 10, 'reference_import_failed': 8, 'reference_install_failed': 10, 'reference_pass': 8}.
- RQ4: Projected attrs/boltons 30-task feasibility: False.
- RQ5: Third repo screen result: no_third_repo_passed_local_gate.
- RQ6: third_repo_screening_needs_broader_local_candidate_supply

## Claims

- `historical_environment_synthesis_completed`
- `historical_environment_profile_inference_completed`
- `uv_historical_environment_probe_completed`
- `reference_gate_subclassification_completed`
- `known_reference_failures_replayed_under_historical_envs`
- `paid_replication_not_run`
- `new_paid_acut_cells_not_run`
- `new_paid_llm_calls_not_run`
- `historical_environment_recovered_reference_pass_sample`
- `attrs_boltons_still_below_supply_threshold`
- `third_repo_gate_screen_completed`
- `toolz_local_gate_failed`
- `humanize_local_gate_failed`

## Verification

- focused_historical_environment_tests: uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_historical_environment_synthesis_gate.py -q (6 passed)
- related_reference_pass_audit_tests: uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_reference_pass_failure_audit.py -q (6 passed)
- phase1_compiler_tests: uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q (184 passed)
- git_diff_check: git diff --check (passed)
- verified_at: 2026-05-26T09:10:43Z
