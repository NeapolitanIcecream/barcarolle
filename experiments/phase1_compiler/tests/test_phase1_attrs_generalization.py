from __future__ import annotations

from pathlib import Path

import phase1_attrs_generalization as attrs_gen


REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG = REPO_ROOT / "experiments" / "phase1_compiler" / "configs" / "phase1_attrs_generalization_third_repo_decision.yaml"


def test_two_repo_task_outcome_matrix_preserves_scoreability_boundaries() -> None:
    config = attrs_gen.load_config(CONFIG)

    payload = attrs_gen.build_task_outcome_matrix(config)

    assert payload["status"] == "valid"
    assert payload["summary"]["planned_cell_count"] == 32
    assert payload["summary"]["scoreable_cell_count"] == 31
    assert payload["summary"]["policy_violation_count"] == 1
    assert payload["summary"]["verified_pass_count"] == 22
    assert payload["summary"]["verified_fail_count"] == 9
    assert payload["frozen_design_match"]["status"] == "matched"

    violation = [
        cell
        for cell in payload["cells"]
        if cell["repo_id"] == "attrs"
        and cell["split"] == "H_future"
        and cell["task_id"] == "attrs__hist__027"
        and cell["adapter_id"] == "kilo_workspace"
    ]

    assert len(violation) == 1
    assert violation[0]["terminal_status"] == "policy_violation"
    assert violation[0]["policy_violation"] is True
    assert violation[0]["scoreable_cell"] is False
    assert violation[0]["verified_fail"] is False

    boltons_hist = [
        cell
        for cell in payload["cells"]
        if cell["repo_id"] == "boltons"
        and cell["task_id"] == "boltons__hist__027"
        and cell["adapter_id"] == "kilo_workspace"
    ]

    assert len(boltons_hist) == 1
    assert boltons_hist[0]["module_or_package_label"] == "cacheutils"
    assert boltons_hist[0]["source_context_ref"] == "pr:349"


def test_task_outcome_matrix_reports_missing_planned_score_rows() -> None:
    config = {
        "adapters": ["codex_workspace"],
        "frozen_design": {"demo": {"b_eval": ["demo__001"], "h_future": []}},
        "score_tables": {"demo": {"b_eval": "missing_score_table.csv", "h_future": "missing_score_table.csv"}},
        "task_metadata": {},
    }

    payload = attrs_gen.build_task_outcome_matrix(config)

    assert payload["status"] == "invalid"
    assert payload["summary"]["planned_cell_count"] == 1
    assert payload["diagnostics"]["missing_score_tables"] == ["missing_score_table.csv"]
    assert payload["diagnostics"]["missing_planned_cells"] == [
        {"adapter_id": "codex_workspace", "repo_id": "demo", "split": "B_eval", "task_id": "demo__001"}
    ]
