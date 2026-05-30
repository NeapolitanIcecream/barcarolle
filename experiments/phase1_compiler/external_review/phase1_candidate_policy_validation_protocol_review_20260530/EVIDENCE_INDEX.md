# Evidence Index

The packet links to canonical repository artifacts instead of copying large evidence.

| Item | Path | Description | SHA-256 |
| --- | --- | --- | --- |
| Policy spec | experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_policy_spec.json | Frozen coverage_constrained_unweighted_v1 rule. | sha256:68d32d465d5e8799861d6127986264cd755040ce036c7742ecb4260e4c64ebd8 |
| Selection manifest | experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_selection_manifest.json | Selected and excluded task IDs with coverage diagnostics. | sha256:f1fe8794d3d3a3f7ea2bf4ebf30e89d53250351f1144b61461c34d3170519d91 |
| Outcome-blindness audit | experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_outcome_blindness_audit.json | Audit that the selector did not use outcomes or score tables. | sha256:614bc224aed9ae7a49686f0bbba0cd345b69756a6bb6675fd8c814f9b0f04999 |
| Validation protocol | experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_validation_protocol.json | Frozen future validation protocol and adapter reporting policy. | sha256:00d8dbefccf7c07a9afa227bbfb7289e827b09d142faaa8fee23708984b84bbe |
| Success criteria | experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_success_criteria.json | Frozen traction, predictive-validity, and blocker criteria. | sha256:bf09ecd69206cb58ea871a0730e9b7dccd39a3bffad6b6db2d2dd82ab9e57dc8 |
| Retrospective signal decision | experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_decision.json | Latest no-paid retrospective signal decision. | sha256:bf9bdee818baa2428fef34a0e81f2a8c58de1d156e4d30334c9f29942aaceb30 |
| Retrospective baseline comparison | experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_baseline_comparison.json | Candidate versus simple baseline comparison. | sha256:60171cec8056f1d0f3b1eff18b50ba205d96711604305afffc022996cf504f50 |
| Adapter metrics | experiments/phase1_compiler/results/phase1_retrospective_predictive_signal_adapter_metrics.json | Adapter-stratified retrospective metrics. | sha256:5d68932f8106109d45d9ad88807ac3014afdfb7125b1d88cf83ff5a29ee3613b |
| Click repair decision | experiments/phase1_compiler/results/phase1_click_llm_source_context_repair_decision.json | Source-quality boundary for repaired click tasks. | sha256:fb9fa0f75406c3044d047ce91ed6e7c29e196fc54c7416d157ffba2f13c5cc66 |
| Blocked split supplement fairness decision | experiments/phase1_compiler/results/phase1_blocked_split_supplement_fairness_gap_diagnostics_decision.json | Adapter fairness and gap diagnostic decision. | sha256:c06144cb412e6c8c14550e039d745bdbc0dc74b4e93a253017d31f87f8a3f799 |

Known weaknesses:
- Retrospective signal is weak and underpowered.
- Codex did not improve uniformly across slices.
- Improvement is not uniform across repos.
- Blocked and shrinkage candidates failed the latest comparison.
- The completed blocked split supplement is post-hoc and diagnostic only.
