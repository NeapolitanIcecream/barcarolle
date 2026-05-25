# Overnight Statement-Hardened Evidence Process

Status: `completed`.

## Boundary

- New paid ACUT calls made: `false`.
- New paid LLM calls made: `false`.
- Follow-up runbook written by worker: `false`.
- Raw artifacts committed: `false`.
- Generated statements are solver-visible task statements, not scoreable results.

## Environment

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `f74fcc423db4e0be7973fbd2808b2a3c4b44f74d`.
- Runbook: `docs/experiments/phase-1-overnight-statement-hardened-evidence-analysis-runbook.md`.
- UV: `uv 0.11.16 (Homebrew 2026-05-21 aarch64-apple-darwin)`.
- Python: `Python 3.11.13`.

## Work Queue

| Step | Status | Commit target | Outputs | Blockers |
| --- | --- | --- | --- | --- |
| 0 | completed | Record overnight statement-hardened analysis preflight |  |  |
| 1 | completed | Audit statement-hardened paid result integrity | experiments/phase1_compiler/results/phase1_overnight_statement_hardened_integrity_audit.json, experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_integrity_audit.md |  |
| 2 | completed | Build statement-hardened task outcome matrix | experiments/phase1_compiler/results/phase1_overnight_statement_hardened_task_outcome_matrix.json, experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_task_outcome_matrix.md |  |
| 3 | completed | Classify statement-hardened paid failures | experiments/phase1_compiler/results/phase1_overnight_statement_hardened_failure_taxonomy.json, experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_failure_taxonomy.md |  |
| 4 | completed | Analyze statement-hardened result strata | experiments/phase1_compiler/results/phase1_overnight_statement_hardened_strata_analysis.json, experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_strata_analysis.md |  |
| 5 | completed | Analyze predictive threshold and power | experiments/phase1_compiler/results/phase1_overnight_statement_hardened_threshold_analysis.json, experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_threshold_analysis.md, experiments/phase1_compiler/results/phase1_overnight_statement_hardened_power_analysis.json, experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_power_analysis.md |  |
| 6 | completed | Rank compiler calibration options | experiments/phase1_compiler/results/phase1_overnight_statement_hardened_calibration_options.json, experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_calibration_options.md |  |
| 7 | completed | Assess local supply for statement-hardened expansion | experiments/phase1_compiler/results/phase1_overnight_statement_hardened_local_supply_analysis.json, experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_local_supply_analysis.md |  |
| 8 | completed | Write proposal alignment memo for paid evidence | experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_proposal_alignment.md |  |
| 9 | completed | Decide next action from statement-hardened evidence | experiments/phase1_compiler/results/phase1_overnight_statement_hardened_next_action_decision.json, experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_next_action_decision.md |  |
| 10 | completed | Record overnight statement-hardened analysis closeout | experiments/phase1_compiler/reports/phase1_overnight_statement_hardened_evidence_process.md |  |

## Verification

| Command | Return code | Status | Seconds |
| --- | --- | --- | --- |
| git diff --check | 0 | pass | 0.021 |
| overnight evidence tests | 0 | pass | 0.12 |
| paid validation regression tests | 0 | pass | 0.195 |
| diff assisted codex loop regression tests | 0 | pass | 0.512 |

## Commits

- `7ced9b34 Record overnight statement-hardened analysis preflight`
- `ef472860 Audit statement-hardened paid result integrity`
- `8bb65216 Build statement-hardened task outcome matrix`
- `4bc4f3ea Classify statement-hardened paid failures`
- `bab9bdcd Analyze statement-hardened result strata`
- `866d238a Analyze predictive threshold and power`
- `cd2d5c29 Rank compiler calibration options`
- `8a1be614 Assess local supply for statement-hardened expansion`
- `06f4a398 Write proposal alignment memo for paid evidence`
- `b9cf6e2d Decide next action from statement-hardened evidence`

## Closeout

- Integrity audit status: `pass`.
- Primary decision: `design_new_predictive_threshold_before_more_paid_validation`.
- Recommended next action: Do not run more paid validation until a quantitative predictive-validity threshold and a better matched local design are preregistered.
- Predictive validity established: `False`.
