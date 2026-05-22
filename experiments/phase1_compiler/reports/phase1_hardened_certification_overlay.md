# Phase 1 Hardened Certification Overlay

Generated: `2026-05-22T03:29:58+00:00`.

| Repo | Benchmark candidates | Manual review | Diagnostic-only | Rejected | Main blocking gates |
| --- | ---: | ---: | ---: | ---: | --- |
| `toolz` | 6 | 0 | 0 | 0 | none |
| `humanize` | 0 | 0 | 16 | 0 | source_diagnostic_only=16, execution_gate_failed:no_op_fail=3, project_file_heavy=1, execution_gate_failed:reference_pass=1, solution_exposure_risk=1, changed_lines_over:250=1 |
| `itsdangerous` | 0 | 0 | 1 | 10 | oracle_alignment_reject=9, execution_gate_failed:reference_pass=7, solution_exposure_risk=5, project_file_heavy=4, changed_lines_over:250=3, execution_gate_failed:no_op_fail=3, reject_subject_term:deprecate=1, reject_subject_term:remove deprecated=1 |

Benchmark-grade eligibility requires passing execution gates, benchmark-grade source, aligned oracle, clean environment, candidate-filter acceptance, and no solution exposure risk.
