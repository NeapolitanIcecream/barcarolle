# Phase 1 Task Supply v2 Fresh Certification Process

## Step 0 - Preflight And Dirty-Tree Audit

What happened: the run started on branch `codex/restart-benchmark-compiler` at `18f5bec38fb951c307a4f08087f329f2fb0875a7`. The latest commit was `18f5bec38fb951c307a4f08087f329f2fb0875a7 2026-05-27T15:22:46+08:00 Add task supply v2 fresh certification runbook`. The raw v2 anchor inventory exists and contains `829` rows.

Why it matters: the certification run starts from a known Barcarolle commit and can account for all 829 raw candidates before any local certification work.

Readiness direction: this step is neutral. It supports auditability; it does not make paid validation ready by itself.

Paid-call statement: no paid ACUT calls, paid task-solving calls, paid replication, or paid LLM statement-generation calls were made or needed in preflight.

External repo paths:

| Repo | Path | Exists | Git Repo |
| --- | --- | --- | --- |
| attrs | `experiments/phase0_headroom/external_repos/attrs` | True | True |
| boltons | `experiments/phase0_headroom/external_repos/boltons` | True | True |
| toolz | `experiments/phase0_headroom/external_repos/toolz` | True | True |
| humanize | `experiments/phase0_headroom/external_repos/humanize` | True | True |

Raw inventory by repo:

```json
{
  "attrs": 300,
  "boltons": 233,
  "humanize": 92,
  "toolz": 204
}
```

Dirty/untracked tree entries at start:

| Status | Path | Classification |
| --- | --- | --- |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/MANIFEST.sha256` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/README_FOR_EXTERNAL_GPT55_PRO.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/TASK_GENERATOR_PROBLEM_BRIEF.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/background/AGENTS.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/background/README.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/background/research-plan-0526.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/background/research-proposal-0519.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/background/restart-consensus-20260520.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/background/system-design.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/attrs_supply_expansion_20260526_candidates.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/attrs_supply_expansion_20260526_certified_tasks.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/attrs_supply_expansion_20260526_review_records.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/attrs_supply_expansion_20260526_source_context.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/attrs_supply_expansion_20260526_task_statements.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/boltons_supply_expansion_20260526_candidates.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/boltons_supply_expansion_20260526_certified_tasks.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/boltons_supply_expansion_20260526_review_records.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/boltons_supply_expansion_20260526_source_context.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/boltons_supply_expansion_20260526_task_statements.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_candidates.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_certification_funnel.csv` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_certification_funnel.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_certified_tasks.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_history_anchors.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_mini_release.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_near_certified_tasks.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_phase0_pilot_release.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_phase0_task_table.csv` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_review_records.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_source_context.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_source_context_funnel.csv` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_supply_funnel.csv` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/humanize_task_statements.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_candidates.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_certification_funnel.csv` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_certified_tasks.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_history_anchors.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_near_certified_tasks.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_phase0_mini_release.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_phase0_task_table.csv` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_review_records.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_source_context.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_source_context_funnel.csv` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_supply_funnel.csv` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/candidate_artifacts/toolz_task_statements.jsonl` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/code/phase1_diff_assisted_codex_loop_statement_regeneration.py` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/code/phase1_historical_environment_synthesis_gate.py` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/code/phase1_reference_pass_failure_audit.py` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/code/phase1_two_repo_certified_supply_expansion.py` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/code/repo_history_pilot.py` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/code/statement_quality.py` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/configs/phase1_historical_environment_synthesis_gate.yaml` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/configs/phase1_reference_pass_failure_audit.yaml` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/configs/repositories.yaml` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_historical_environment_input_inventory.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_historical_environment_known_failure_replay_matrix.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_historical_environment_recovered_supply_projection.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_historical_environment_synthesis_decision.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_local_algorithm_bakeoff_decision.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_local_algorithm_bakeoff_paid_readiness_gate.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_reference_gate_subclassification.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_reference_pass_environment_drift_audit.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_reference_pass_failure_audit_decision.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_reference_pass_replay_matrix.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_third_repo_environment_gate_screen.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_third_repo_replacement_candidate_screen.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_third_repo_replacement_selection_decision.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_two_repo_supply_expansion_certification_attempts.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_two_repo_supply_expansion_decision.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_two_repo_supply_expansion_eligibility_audit.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_two_repo_supply_expansion_existing_inventory.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_two_repo_supply_expansion_mining_plan.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_two_repo_supply_expansion_raw_candidates.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_two_repo_supply_expansion_source_contexts.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_two_repo_supply_expansion_statement_generation_blocker.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/reports/phase1_two_repo_supply_expansion_statement_generation_review.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_historical_environment_input_inventory.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_historical_environment_known_failure_replay_matrix.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_historical_environment_profile_catalog.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_historical_environment_recovered_supply_projection.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_historical_environment_synthesis_decision.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_local_algorithm_bakeoff_decision.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_local_algorithm_bakeoff_paid_readiness_gate.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_reference_gate_subclassification.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_reference_pass_environment_drift_audit.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_reference_pass_failure_audit_decision.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_reference_pass_failure_inventory.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_reference_pass_replay_matrix.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_third_repo_environment_gate_screen.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_third_repo_replacement_candidate_screen.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_third_repo_replacement_selection_decision.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_two_repo_supply_expansion_certification_attempts.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_two_repo_supply_expansion_decision.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_two_repo_supply_expansion_eligibility_audit.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_two_repo_supply_expansion_existing_inventory.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_two_repo_supply_expansion_expanded_supply.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_two_repo_supply_expansion_mining_plan.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_two_repo_supply_expansion_raw_candidates.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_two_repo_supply_expansion_source_contexts.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_two_repo_supply_expansion_statement_generation_review.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/results/phase1_two_repo_supply_expansion_statement_packets.json` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/runbooks/phase-1-historical-environment-synthesis-and-third-repo-gate-runbook.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/runbooks/phase-1-reference-pass-failure-audit-runbook.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/runbooks/phase-1-third-repo-repair-remine-runbook.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/runbooks/phase-1-third-repo-replacement-selection-runbook.md` | unrelated_untracked_external_review_artifact_do_not_stage |
| `??` | `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/runbooks/phase-1-two-repo-certified-supply-expansion-runbook.md` | unrelated_untracked_external_review_artifact_do_not_stage |

Ignored workspace/tmp/cache paths staged: `False`.

Artifact hygiene: raw stdout/stderr logs, solver workspaces, verifier workspaces, target repo clones, caches, and `.venv` directories were not committed by this step.

## Step 5 - attrs First Wave

What happened: the attrs first wave attempted all 160 candidates selected by the configured first-wave cap. It produced 31 technical certifications and 28 release-eligible tasks.

Why it matters: attrs now has fresh local evidence, but the first wave still falls below the 30 release-eligible threshold. The gap is source-context plus certification quality, not raw candidate inventory.

Readiness direction: attrs argues for continued certification/source-context repair before paid validation. Failure subgates were specific: 63 `install_failed`, 44 `collect_failed`, 15 `reference_assert_failed`, and 7 `noop_assert_failed`.

Paid-call statement: no paid ACUT calls, paid task-solving calls, paid replication, or paid LLM statement-generation calls were made during the attrs wave.

Artifact hygiene: raw stdout/stderr logs and workspaces were written only under ignored scratch paths.

## Step 5 - humanize Wave

What happened: the humanize wave attempted all 84 oracle-usable candidates selected by the configured cap. It produced 9 technical certifications and 0 release-eligible tasks.

Why it matters: the broad v2 humanize pool did not preserve the high release-ready yield from the older narrow 16-candidate artifact. The technical passes are useful, but every humanize v2 candidate in this run has commit-message-only source context, so they require review before release counting.

Readiness direction: humanize argues for source-context repair, not paid readiness. Failure subgates were specific: 62 `collect_failed`, 12 `install_failed`, and 1 `noop_assert_failed`.

Paid-call statement: no paid ACUT calls, paid task-solving calls, paid replication, or paid LLM statement-generation calls were made during the humanize wave.

Artifact hygiene: raw stdout/stderr logs and workspaces were written only under ignored scratch paths.
