# Overnight Statement-Hardened Evidence Process

Status: `pass`.

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
| 8 | pending | Write proposal alignment memo for paid evidence |  |  |
| 9 | pending | Decide next action from statement-hardened evidence |  |  |
| 10 | pending | Record overnight statement-hardened analysis closeout |  |  |
