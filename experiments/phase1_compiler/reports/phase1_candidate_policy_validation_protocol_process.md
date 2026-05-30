# Candidate Policy Validation Protocol Process

Current step: `Step 1 - Freeze Candidate Policy Spec`.

Completed artifacts:
- `experiments/phase1_compiler/results/phase1_candidate_policy_validation_protocol_policy_spec.json`
- `experiments/phase1_compiler/reports/phase1_candidate_policy_validation_protocol_policy_spec.md`

Boundary:
- This runbook is no-paid.
- New paid ACUT solver cells run: `false`.
- New paid LLM calls run: `false`.
- External adversarial review submitted: `false`.
- Score tables are not read by the policy selection command.

Notes:
- Policy spec can be read without consulting score tables.
- Forbidden inputs include terminal outcomes, pass/fail labels, adapter outcomes, score-table rows, raw transcripts, and hidden verifier output.
