# Proposal Evidence Package Report Evidence Index

What happened: created an appendix-friendly index of canonical Phase 1 reports.

Why it matters: reviewer-facing claims can point to report evidence without turning the proposal into a chronological ledger.

Action suggested next: M5 can integrate selected rows into the proposal appendix.

| Report | Evidence type | Claim function | Key result/status | Limitation | Main text? |
| --- | --- | --- | --- | --- | --- |
| experiments/phase1_compiler/reports/phase1_weighted_design_paid_pilot_decision.md | diagnostic_negative | Shows naive weighting can fail materially. | Weighted gaps: attrs 0.3148, boltons 0.7481; simple same-budget baselines 0.25 and 0.125. | Two-repo paid pilot; negative evidence for one design, not a validation result. | yes |
| experiments/phase1_compiler/reports/phase1_local_algorithm_bakeoff_decision.md | diagnostic_negative | Diagnoses why the old weighted objective is underidentified. | Old weighted target-profile design not promoted; repo-stratified/simple baselines remain conservative. | Local no-paid analysis only. | yes |
| experiments/phase1_compiler/reports/phase1_three_repo_paid_validation_decision.md | technical_tractability | Shows workspace ACUT protocol, endpoint accounting, and policy checks can run end to end. | 120 planned cells, 120 completed, scoreability 1.0, endpoint compliance pass, cost $51.267333. | Exploratory pilot evidence; predictive validity not established. | yes |
| experiments/phase1_compiler/reports/phase1_click_llm_source_context_repair_decision.md | source_quality | Repairs the click source-context caveat for source-quality narrative use. | 30/30 click tasks repaired with public context; 0 paid LLM calls; 0 paid ACUT cells. | Does not rewrite paid outcomes or prove predictive validity. | yes |
| experiments/phase1_compiler/reports/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.md | adapter_reporting | Justifies adapter-stratified reporting as primary. | Supplement fair enough to interpret as ACUT-configuration evidence; model-only claim disallowed. | Post-hoc diagnostic supplement, not primary predictive-validity evidence. | yes |
| experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md | retrospective_traction | Compares candidate against simple baselines before M3 strengthening. | Coverage candidate MAE 0.209 vs temporal baseline MAE 0.2149. | Pseudo-future and underpowered; needs many-seed random and baseline envelope. | yes |
| experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_adapter_metrics.md | adapter_fragility | Shows the candidate signal is not uniform across ACUT adapters. | Candidate worse than temporal baseline on Codex and better on Kilo in the proposal report summary. | Retrospective slices are sparse. | yes |
| experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_uncertainty.md | uncertainty | Keeps retrospective signal in traction-only scope. | Claim strength: traction_evidence_only; sample size too sparse for formal predictive validity. | No formal interval estimated. | yes |
| experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_selection_manifest.md | candidate_policy | Freezes the outcome-blind candidate policy and exposes fallback behavior. | 18 selected tasks; 6 per repo; boltons uses insufficient-feature-support fallback. | M4 still owns fallback threshold and candidate-policy hardening. | yes |
| experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md | source_supply | Keeps task supply work in Layer 1 infrastructure rather than core claim. | Paid-ready false; internal repo-history v2 should continue; external systems are future references/adapters only. | Does not make broad generator expansion part of M3. | no |
