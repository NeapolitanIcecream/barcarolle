# Phase 1 Statement-Hardened After Canonical Repair Preregistration

Release ID: `statement_hardened_after_canonical_split_repair_20260525`.
Created: `2026-05-25T08:11:58Z`.

## Research Question

Can a canonical-split, statement-hardened two-repo release support a future paid validation of target-repository predictive behavior without reusing the old statement-risk-confounded score tables?

## Gate

- Paid validation has not started.
- Predictive validity has not been established.
- Old paid results are not repaired or overwritten.
- `attrs__hist__027` old policy violation is not repaired by this local preregistration.
- Future paid validation requires explicit user approval and a separate runbook.
- Future paid validation must use `LLM_BASE_URL` and `LLM_API_KEY`.

## Claims Disallowed

- `predictive_validity_established`
- `production_benchmark_ranking`
- `paid_validation_completed`
- `old_paid_result_repaired`
- `attrs_policy_violation_repaired`
- `generated_statement_is_scoreable_result`
- `hidden_oracle_informed_statement_rewrite`
- `next_runbook_written_by_worker`
