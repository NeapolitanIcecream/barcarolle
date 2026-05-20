# Next Experiment Decision Gates

status: `draft_gate_for_next_live_runs`
scope: Barcarolle core-narrative Click stabilization
source_advice: `experiments/core_narrative/reports/2026-05-08_gpt55pro_next_experiment_advice.md`

Use these gates before spending more live API budget.

## Gate 0: Preflight Before Live API

All selected tasks must pass these checks:

```text
selected_tasks_count >= 3
no_op_probe == fail
reference_probe == pass
known_bad_probe == fail
flakiness_probe == stable
verifier_runtime_p95 < verifier.timeout_seconds
oracle_log_leakage == false
mock_runner_smoke == pass
clean_patch_replay == pass
```

Failure action: fix the task pack or runner. Do not run live API.

## Gate 1: Expand From 4x3 Stabilization To Click 004-008

Run this gate after:

- `frontier-click-specialist` completes attempt 1 on tasks 001-003.
- all four core ACUTs complete attempt 2 on tasks 001-003.
- every scoreable result is produced by clean patch replay.

Expansion conditions:

```text
infra_failed_rate == 0
verifier_repair_after_live == false
unclassified_failure_rate <= 20%
all_runs_have_clean_patch_replay == true
frontier_click_specialist_attempt1_completed == true
meaningful_film_contrast_exists == true
```

Revise the task pack instead of expanding when:

```text
same_task_fails_across_all_4_acuts_in_both_attempts == true
AND primary_film_label in {"verifier_oracle_misaligned", "hidden_test_overconstraint"}
```

Pause when:

```text
infra_failed_rate > 5%
OR verifier_repair_after_live == true
OR clean_patch_replay_disagrees_with_mutated_workspace_verification == true
```

## Gate 2: Expand From Click Slice To New Repository Or Family

Run this gate after a 4 ACUT by 8 Click task by 2 attempt slice exists.

Expansion conditions:

```text
scoreable_trials >= 64
core_acut_matrix_complete == true
task_family_count >= 5
infra_failed_rate <= 2%
verifier_repair_after_live == false
classifier_coverage >= 90%
specialist_context_inclusion_assertions == pass
film_labels_not_dominated_by_one_task_quirk == true
```

Revise before expanding when:

```text
failure_share_from_one_task_family > 50%
OR verifier_oracle_misaligned_failure_share > 30%
OR generic_specialist_distinction_missing_from_prompt_snapshots == true
OR all_acuts_tie_on_box_score_and_film_distribution == true
```

Stop or pivot when:

```text
repeated_verifier_instability == true
OR api_or_runner_cost_increases_without_scoreable_evidence == true
OR task_pack_cannot_pass_no_op_reference_known_bad_probes == true
OR evidence_identity_cannot_distinguish_acut_runner_context_verifier == true
```
