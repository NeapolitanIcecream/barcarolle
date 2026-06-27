# Headroom Entry Gate

Generated UTC: `2026-05-20T08:50:32+00:00`.
Can continue Phase 0: `True`.
Decision: `can_continue_phase0`.

## Gates

| Gate | Status | Evidence | Notes |
|---|---:|---|---|
| `source_adapter_decision` | `pass` | `experiments/phase0_headroom/reports/phase0_source_adapter_followup_decision.md` | `{"decision": "ready_for_headroom_matrix"}` |
| `matrix_status` | `pass` | `experiments/phase0_headroom/results/headroom_matrix.json` | `{"status": "ready_not_run_after_source_adapter_repair"}` |
| `certified_count` | `pass` | `experiments/phase0_headroom/certified_tasks/toolz_certification_funnel.csv` | `{"certified_count": 6, "near_certified_count": 0}` |
| `release_status` | `pass` | `experiments/phase0_headroom/releases/toolz_phase0_mini_release.json` | `{"benchmark_grade": true, "release_status": "benchmark_grade_candidate"}` |
| `split_minimum` | `pass` | `experiments/phase0_headroom/releases/toolz_phase0_task_table.csv` | `{"B_real": ["toolz__hist__001", "toolz__hist__002", "toolz__hist__003"], "W_real": ["toolz__hist__004", "toolz__hist__010", "toolz__hist__016"], "duplicates": []}` |
| `statement_status` | `pass` | `experiments/phase0_headroom/certified_tasks/toolz_task_statements.jsonl` | `{"draft_tasks": [], "not_final_reviewed_tasks": []}` |
| `review_consistency` | `pass` | `experiments/phase0_headroom/certified_tasks/ and experiments/phase0_headroom/releases/` | `{"inconsistencies": []}` |
| `leakage_policy` | `pass` | `experiments/phase0_headroom/certified_tasks/toolz_task_statements.jsonl` | `{"forbidden_text_task_ids": []}` |
| `mechanical_gates` | `pass` | `experiments/phase0_headroom/certified_tasks/toolz_certified_tasks.jsonl` | `{"certified_jsonl_count": 6, "missing_or_nonpass": []}` |
| `budget` | `pass` | `experiments/phase0_headroom/results/cost_ledger.jsonl` | `{"current_cumulative_estimated_cost_usd": 0.0, "hard_stop_usd": 200.0, "projected_cumulative_cost_usd": 60.0, "projected_default_matrix_cost_usd": 60.0, "soft_stop_usd": 160.0}` |
| `tooling` | `pass` | `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` | `{"command": "uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools", "duration_seconds": 0.122, "passed": true, "returncode": 0, "stderr_tail": "", "stdout_tail": "................  ...` |
| `artifact_hygiene` | `pass` | `git status --short --ignored experiments/phase0_headroom docs/experiments .gitignore` | `{"staged_ignored_paths": [], "tracked_ignored_paths": []}` |

## Hygiene Repair

- Statements marked reviewed: `0`.
- Manual review minute rows corrected: `0`.
- Certified task source labels repaired: `0`.
