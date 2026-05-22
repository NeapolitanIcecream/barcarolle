# Phase 1 Hardened Certification Overlay

Generated: `2026-05-22T06:02:33+00:00`.

| Repo | Benchmark candidates | Manual review | Diagnostic-only | Rejected | Main blocking gates |
| --- | ---: | ---: | ---: | ---: | --- |
| `toolz` | 6 | 0 | 0 | 0 | none |
| `humanize` | 0 | 0 | 16 | 0 | source_diagnostic_only=16, execution_gate_failed:no_op_fail=3, project_file_heavy=1, execution_gate_failed:reference_pass=1, solution_exposure_risk=1, changed_lines_over:250=1 |
| `boltons` | 7 | 5 | 10 | 10 | source_diagnostic_only=10, execution_gate_failed:ambiguity_review=8, oracle_alignment_reject=6, execution_gate_failed:reference_pass=5, solution_exposure_risk=5, execution_gate_failed:no_op_fail=3 |

Benchmark-grade eligibility requires passing execution gates, benchmark-grade source, aligned oracle, clean environment, candidate-filter acceptance, and no solution exposure risk.
