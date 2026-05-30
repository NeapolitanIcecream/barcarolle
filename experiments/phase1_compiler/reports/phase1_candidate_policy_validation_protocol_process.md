# Candidate Policy Validation Protocol Process

Current step: `Step 3 - Freeze Validation Protocol And Success Criteria`.

Completed artifacts:
- `experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_validation_protocol.json`
- `experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_success_criteria.json`
- `experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_baseline_registry.json`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_validation_protocol.md`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_success_criteria.md`

Boundary:
- This runbook is no-paid.
- New paid ACUT solver cells run: `false`.
- New paid LLM calls run: `false`.
- External adversarial review submitted: `false`.
- Score tables are not read by the policy selection command.

Notes:
- The validation protocol is frozen before future paid calls.
- Adapter-stratified MAE and catastrophic miss rate are primary; pooled summaries are secondary only.
- No paid run is authorized by this runbook.
