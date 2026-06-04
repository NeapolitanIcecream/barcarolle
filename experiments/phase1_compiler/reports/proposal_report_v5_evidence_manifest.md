# Proposal Report V5 Evidence Manifest

Status: internal audit manifest, 2026-06-01.

Purpose: preserve path-level traceability for the reader-facing V5 proposal
without making raw internal artifact paths the proposal's dominant evidence
presentation.

This manifest is not a replacement for the proposal. It is an internal index
for audit and handoff work.

## Source Draft

| Label | Path |
| --- | --- |
| V4 source draft | `docs/research/phase-1-proposal-report-v4.md` |
| V4 integration decision | `experiments/phase1_compiler/reports/phase1_proposal_report_v4_agent_tuning_integration_decision.md` |

## Proposal Evidence Index References

| Reader-facing label | Path |
| --- | --- |
| Weighted design pilot | `experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md` |
| Local algorithm bakeoff | `experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md` |
| Three-repo workspace execution pilot | `experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md` |
| Click source-context repair | `experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md` |
| Adapter fairness diagnostics | `experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md` |
| Random-baseline comparison | `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md` |
| Baseline-envelope comparison | `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md` |
| Fallback-share accounting | `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_fallback_share.md` |
| Validation-protocol hardening | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_decision.md` |

## Data Layer References

| Data layer | Path |
| --- | --- |
| Three-repo paid cells manifest | `experiments/phase1_compiler/results/phase1_three_repo_paid_validation_score_tables_manifest.json` |
| Three-repo paid metrics | `experiments/phase1_compiler/results/phase1_three_repo_paid_validation_metrics.json` |
| Three-repo cost reconciliation | `experiments/phase1_compiler/results/phase1_three_repo_paid_validation_cost_reconciliation.json` |
| Three-repo diagnostics cube | `experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_result_cube.json` |
| Three-repo diagnostics CSV | `experiments/phase1_compiler/results/phase1_three_repo_paid_result_diagnostics_result_cube.csv` |
| Adapter-stratified summary | `experiments/phase1_compiler/results/phase1_adapter_stratified_reporting_three_repo_summary.json` |
| Weighted pilot score table | `experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_score_table.csv` |
| Weighted pilot metrics | `experiments/phase0_headroom/results/phase1_weighted_design_paid_pilot_metrics.json` |
| Supplement paid cells manifest | `experiments/phase1_compiler/results/phase1_blocked_split_missing_cell_supplement_paid_execution_combined_score_tables_manifest.json` |
| Random baseline distribution | `experiments/phase1_compiler/results/phase1_proposal_evidence_package_random_baseline_distribution.json` |
| Baseline envelope | `experiments/phase1_compiler/results/phase1_proposal_evidence_package_baseline_envelope.json` |
| Workspace usage ledger | `experiments/phase0_headroom/results/workspace_usage_ledger.jsonl` |

The three-repo manifest indexes `120` completed and scoreable paid cells. The
score tables themselves live under
`experiments/phase0_headroom/results/phase1_three_repo_paid_validation_*_score_table.csv`.

Raw Agent transcripts, raw prompts, raw completions, solver workspaces,
verifier workspaces, cloned repositories, and hidden-oracle streams are not
committed.

## Protocol Detail References

| Protocol artifact | Path |
| --- | --- |
| Claim modes | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_claim_modes.md` |
| Candidate policy | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_candidate_policy.md` |
| Adapter estimand | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_adapter_estimand.md` |
| Success gate | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md` |
| Support thresholds | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_support_thresholds.md` |
| Release schema | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_release_schema.md` |
| Power/budget note | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_power_budget_note.md` |

## Citation Reference

| Label | Path |
| --- | --- |
| Reviewer-ready citation matrix | `experiments/phase1_compiler/reports/phase1_proposal_report_reviewer_ready_revision_citation_matrix.md` |
