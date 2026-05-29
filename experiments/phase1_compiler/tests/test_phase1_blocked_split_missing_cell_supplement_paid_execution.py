from __future__ import annotations

import copy
import json
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE0_TOOLS = REPO_ROOT / "experiments" / "phase0_headroom" / "tools"
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
for path in [PHASE0_TOOLS, PHASE1_TOOLS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import phase1_blocked_split_missing_cell_supplement_paid_execution as supplement  # noqa: E402
import workspace_acut_run as workspace_acut  # noqa: E402


def temp_config(tmp_path: Path) -> dict[str, object]:
    config = copy.deepcopy(supplement.load_config())
    config["outputs"] = {
        key: str(tmp_path / "results" / Path(path).name)
        for key, path in config["outputs"].items()
    }
    config["reports"] = {
        key: str(tmp_path / "reports" / Path(path).name)
        for key, path in config["reports"].items()
    }
    config["workspace_runner"]["matrix_config"] = str(tmp_path / "phase1_blocked_split_missing_cell_supplement_matrix.yaml")
    return config


def load_ready() -> dict[str, object]:
    config = supplement.load_config()
    return json.loads(supplement.source_path(config, "ready_package").read_text(encoding="utf-8"))


def test_missing_task_manifest_is_frozen_to_24_tasks_and_48_cells() -> None:
    task_ids = supplement.expected_missing_task_ids()
    cells = supplement.expected_missing_cells()
    counts = Counter(task_id.split("__", 1)[0] for task_id in task_ids)

    assert len(task_ids) == 24
    assert len(set(task_ids)) == 24
    assert len(cells) == 48
    assert counts == {"attrs": 6, "boltons": 10, "click": 8}
    assert cells[0] == {
        "task_id": "attrs__v2__157",
        "repo": "attrs",
        "split": "B_eval",
        "adapter_id": "codex_workspace",
    }


def test_batch_plan_matches_runbook_schedule() -> None:
    batches = supplement.planned_batches()

    assert [batch["batch_id"] for batch in batches] == [1, 2, 3, 4]
    assert [len(batch["task_ids"]) for batch in batches] == [3, 5, 9, 7]
    assert batches[0]["task_ids"] == ["attrs__v2__157", "boltons__v2__008", "click__third__091"]
    assert sum(len(batch["task_ids"]) for batch in batches) == 24


def test_ready_package_manifest_matches_runbook_missing_cells() -> None:
    ready = load_ready()
    validation = supplement.validate_manifest_cells(ready)

    assert ready["status"] == "ready"
    assert ready["selected_protocol_option"] == "B"
    assert ready["selected_protocol_name"] == "same_budget_missing_cell_supplement"
    assert ready["selected_split_id"] == supplement.SELECTED_SPLIT_ID
    assert ready["adapters"] == ["codex_workspace", "kilo_workspace"]
    assert len(ready["selected_task_ids"]) == 60
    assert len(ready["known_reusable_cells"]) == 72
    assert len(ready["missing_paid_cells_to_run"]) == 48
    assert validation["matches"] is True


def test_workspace_loader_can_load_missing_tasks_with_selected_split_labels(tmp_path: Path) -> None:
    config = temp_config(tmp_path)
    ready = load_ready()
    matrix = supplement.write_workspace_matrix_config(config, ready)

    packages = workspace_acut.load_phase0_packages(REPO_ROOT, matrix_config_path=matrix)
    by_id = {package.task_id: package for package in packages}
    selected_split = supplement.ready_split_by_task(ready)

    for task_id in supplement.expected_missing_task_ids():
        package = by_id[task_id]
        rendered = workspace_acut.render_statement(package)
        assert package.repo_id == task_id.split("__", 1)[0]
        assert package.split == selected_split[task_id]
        assert package.source_repo.exists()
        assert supplement.commit_exists(package.source_repo, package.base_commit)
        assert package.solver_facing_statement.strip()
        assert package.target_commit not in rendered
        assert "diff --git" not in rendered
        assert package.allowed_code_paths
        assert package.test_paths
        assert not set(package.allowed_code_paths).intersection(package.test_paths)
        assert package.verifier_command


def test_batch_plan_payload_contains_only_ready_package_missing_cells(tmp_path: Path) -> None:
    config = temp_config(tmp_path)
    ready = load_ready()
    payload, blockers = supplement.build_batch_plan_payload(config, ready)

    assert blockers == []
    assert payload["status"] == "frozen"
    assert payload["planned_unique_tasks"] == 24
    assert payload["planned_cells"] == 48
    assert {row["adapter_id"] for row in payload["matrix_rows"]} == {"codex_workspace", "kilo_workspace"}
    assert payload["matrix_rows"][0]["result_prefix"].startswith(
        "phase1_blocked_split_missing_cell_supplement_paid_execution_batch_1_smoke_"
    )


def test_reuse_manifest_traces_72_cells_to_committed_score_tables(tmp_path: Path) -> None:
    config = temp_config(tmp_path)
    ready = load_ready()
    payload, blockers = supplement.build_reuse_manifest(config, ready)

    assert blockers == []
    assert payload["status"] == "verified"
    assert payload["reused_cell_count"] == 72
    assert payload["scoreable_reused_cell_count"] == 72
    assert all((REPO_ROOT / row["old_score_table_source_path"]).exists() for row in payload["reused_cells"])
    assert all(row["terminal_outcome_changed"] is False for row in payload["reused_cells"])


def test_adapter_config_keeps_required_endpoint_variables() -> None:
    config = supplement.load_config()
    adapters = workspace_acut.load_adapter_configs(supplement.adapter_config_path(config))

    assert sorted(adapters) == ["codex_workspace", "kilo_workspace"]
    for adapter in adapters.values():
        assert adapter.requires_env == ["LLM_BASE_URL", "LLM_API_KEY"]
