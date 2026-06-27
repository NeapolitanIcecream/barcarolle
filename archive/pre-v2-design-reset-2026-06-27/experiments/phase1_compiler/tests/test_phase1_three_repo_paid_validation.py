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

import phase1_three_repo_paid_validation as paid_validation  # noqa: E402
import workspace_acut_run as workspace_acut  # noqa: E402


def test_primary_pilot_task_ids_are_frozen_to_sixty_three_repo_tasks() -> None:
    ids = paid_validation.PRIMARY_PILOT_TASK_IDS
    counts = Counter(task_id.split("__", 1)[0] for task_id in ids)

    assert len(ids) == 60
    assert len(set(ids)) == 60
    assert counts == {"attrs": 20, "boltons": 20, "click": 20}
    assert ids[:3] == ["attrs__v2__207", "attrs__v2__264", "attrs__v2__187"]
    assert ids[-3:] == ["click__third__050", "click__third__205", "click__third__238"]


def test_batch_plan_matches_runbook_cell_schedule() -> None:
    batches = paid_validation.planned_batches()

    assert [batch["batch_id"] for batch in batches] == [1, 2, 3, 4, 5]
    assert [len(batch["task_ids"]) for batch in batches] == [3, 15, 14, 14, 14]
    assert batches[0]["task_ids"] == ["attrs__v2__207", "boltons__v2__135", "click__third__275"]
    assert sum(len(batch["task_ids"]) for batch in batches) == 60


def test_workspace_loader_loads_all_primary_pilot_packages_from_frozen_artifacts(tmp_path: Path) -> None:
    config = paid_validation.load_config()
    matrix = tmp_path / "phase1_three_repo_paid_validation_workspace_matrix.yaml"
    lines = [
        "schema_version: barcarolle.workspace_acut_matrix_config.v1",
        "status: test",
        "phase1_three_repo_paid_validation: true",
        f"task_table: {paid_validation.rel(paid_validation.source_path(config, 'task_table'))}",
        f"split_plan: {paid_validation.rel(paid_validation.source_path(config, 'split_plan'))}",
        f"fresh_certification_attempts: {paid_validation.rel(paid_validation.source_path(config, 'fresh_certification_attempts'))}",
        f"third_repo_certification_attempts: {paid_validation.rel(paid_validation.source_path(config, 'third_repo_certification_attempts'))}",
        f"task_supply_raw_anchor_inventory: {paid_validation.rel(paid_validation.source_path(config, 'task_supply_raw_anchor_inventory'))}",
        f"third_repo_raw_anchor_inventory: {paid_validation.rel(paid_validation.source_path(config, 'third_repo_raw_anchor_inventory'))}",
        f"attrs_source_repair_statement_packets: {paid_validation.rel(paid_validation.source_path(config, 'attrs_source_repair_statement_packets'))}",
        "task_ids:",
        *[f"  - {task_id}" for task_id in paid_validation.PRIMARY_PILOT_TASK_IDS],
        "",
    ]
    matrix.write_text("\n".join(lines), encoding="utf-8")

    packages = workspace_acut.load_phase0_packages(REPO_ROOT, matrix_config_path=matrix)
    by_id = {package.task_id: package for package in packages}
    task_rows = paid_validation.rows_from_task_table(config)
    split_map = paid_validation.split_by_id(config)

    assert list(by_id) == paid_validation.PRIMARY_PILOT_TASK_IDS
    for task_id, package in by_id.items():
        assert package.repo_id == task_id.split("__", 1)[0]
        assert package.split == split_map[task_id]
        assert package.source_repo.name == package.repo_id
        assert "external_repos" in package.source_repo.parts
        assert package.base_commit == task_rows[task_id]["base_commit"]
        assert package.target_commit == task_rows[task_id]["target_commit"]
        assert package.solver_facing_statement.strip()
        assert task_rows[task_id]["target_commit"] not in workspace_acut.render_statement(package)
        assert package.allowed_code_paths == task_rows[task_id]["implementation_files"]
        assert package.test_paths == task_rows[task_id]["test_files"]
        assert not set(package.allowed_code_paths).intersection(package.test_paths)
        assert package.verifier_command


def test_batch_plan_payload_has_120_cells_and_result_prefixes(monkeypatch, tmp_path: Path) -> None:
    config = copy.deepcopy(paid_validation.load_config())
    config["outputs"] = {key: str(tmp_path / "results" / Path(path).name) for key, path in config["outputs"].items()}
    config["reports"] = {key: str(tmp_path / "reports" / Path(path).name) for key, path in config["reports"].items()}
    config["workspace_runner"]["matrix_config"] = str(tmp_path / "matrix.yaml")
    config_path = tmp_path / "config.yaml"
    config_path.write_text("schema_version: barcarolle.phase1_three_repo_paid_validation.v1\n", encoding="utf-8")
    monkeypatch.setattr(paid_validation, "load_config", lambda _path=paid_validation.DEFAULT_CONFIG: config)

    payload = paid_validation.build_batch_plan(config_path)

    assert payload["planned_cells"] == 120
    assert len(payload["matrix_rows"]) == 120
    assert {row["adapter_id"] for row in payload["matrix_rows"]} == {"codex_workspace", "kilo_workspace"}
    assert payload["matrix_rows"][0]["result_prefix"] == "phase1_three_repo_paid_validation_batch_1_smoke_codex_workspace"


def test_adapter_config_keeps_endpoint_env_requirements() -> None:
    config = paid_validation.load_config()
    adapters = workspace_acut.load_adapter_configs(paid_validation.adapter_config_path(config))

    assert sorted(adapters) == ["codex_workspace", "kilo_workspace"]
    for adapter in adapters.values():
        assert adapter.requires_env == ["LLM_BASE_URL", "LLM_API_KEY"]
