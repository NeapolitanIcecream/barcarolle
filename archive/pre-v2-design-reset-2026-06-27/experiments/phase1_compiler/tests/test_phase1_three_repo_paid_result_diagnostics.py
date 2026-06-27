from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_three_repo_paid_result_diagnostics as diagnostics  # noqa: E402


def test_result_cube_uses_all_120_scoreable_paid_cells() -> None:
    config = diagnostics.load_config()

    rows = diagnostics.build_result_cube_rows(config)
    tasks = diagnostics.task_level_rows(rows)

    assert len(rows) == 120
    assert all(row["scoreable_flag"] for row in rows)
    assert sum(1 for row in rows if row["pass_flag"]) == 54
    assert len(tasks) == 60
    assert {task["adapter_count"] for task in tasks} == {2}
    assert {tuple(sorted(task["pass_by_adapter"])) for task in tasks} == {("codex_workspace", "kilo_workspace")}
    assert Counter(row["repo_id"] for row in rows) == {"attrs": 40, "boltons": 40, "click": 40}


def test_metric_reproduction_matches_committed_primary_gap() -> None:
    config = diagnostics.load_config()
    rows = diagnostics.build_result_cube_rows(config)

    payload = diagnostics.build_metric_reproduction_payload(config, rows)

    assert payload["overall"]["cell_count"] == 120
    assert payload["overall"]["pass_rate"] == 0.45
    assert payload["pooled_unweighted"] == {
        "B_eval_pass_rate": 0.4,
        "H_future_pass_rate": 0.5,
        "primary_absolute_gap": 0.1,
    }
    assert payload["comparison_to_committed"]["primary_pooled_absolute_gap_matches"] is True
    assert payload["explanation_status"]["bookkeeping_or_metric_error"] == "not_supported"


def test_adapter_effects_capture_paired_disagreement_direction() -> None:
    config = diagnostics.load_config()
    rows = diagnostics.build_result_cube_rows(config)
    tasks = diagnostics.task_level_rows(rows)

    paired_counts = Counter(task["paired_outcome"] for task in tasks)
    sign_test = diagnostics.exact_two_sided_sign_test(paired_counts["kilo_only_pass"], paired_counts["codex_only_pass"])

    assert paired_counts == {
        "both_fail": 22,
        "both_pass": 16,
        "kilo_only_pass": 16,
        "codex_only_pass": 6,
    }
    assert sign_test["n"] == 22
    assert sign_test["successes"] == 16
    assert sign_test["failures"] == 6
    assert sign_test["p_value"] == 0.052479


def test_split_balance_exposes_click_title_only_context() -> None:
    config = diagnostics.load_config()
    tasks = diagnostics.task_level_rows(diagnostics.build_result_cube_rows(config))

    click_tasks = [task for task in tasks if task["repo_id"] == "click"]
    title_only = [task for task in click_tasks if task["source_context_class"] == "pr_context_title_only"]

    assert len(click_tasks) == 20
    assert len(title_only) == 20
    assert Counter(task["split"] for task in title_only) == {"B_eval": 10, "H_future": 10}


def test_review_queue_is_bounded_and_includes_required_failure_shapes() -> None:
    tasks = diagnostics.task_level_rows(diagnostics.build_result_cube_rows(diagnostics.load_config()))

    queue = diagnostics.select_review_queue(tasks)
    reasons = Counter(reason for task in queue for reason in task["review_reasons"])

    assert len(queue) < len(tasks)
    assert reasons["both_adapters_fail"] == 22
    assert reasons["adapter_disagreement"] == 22
    assert reasons["matched_both_pass_contrast"] > 0
