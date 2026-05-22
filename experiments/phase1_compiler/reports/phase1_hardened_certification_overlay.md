# Phase 1 Hardened Certification Overlay

Generated: `2026-05-22T03:54:32+00:00`.

| Repo | Benchmark candidates | Manual review | Diagnostic-only | Rejected | Main blocking gates |
| --- | ---: | ---: | ---: | ---: | --- |
| `toolz` | 6 | 0 | 0 | 0 | none |
| `humanize` | 0 | 0 | 16 | 0 | source_diagnostic_only=16, execution_gate_failed:no_op_fail=3, project_file_heavy=1, execution_gate_failed:reference_pass=1, solution_exposure_risk=1, changed_lines_over:250=1 |
| `itsdangerous` | 0 | 2 | 0 | 4 | solution_exposure_risk=4, oracle_alignment_reject=2, execution_gate_failed:reference_pass=1, execution_gate_failed:no_op_fail=1 |

Benchmark-grade eligibility requires passing execution gates, benchmark-grade source, aligned oracle, clean environment, candidate-filter acceptance, and no solution exposure risk.
