from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE0_TOOLS = REPO_ROOT / "experiments" / "phase0_headroom" / "tools"
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
for path in [PHASE0_TOOLS, PHASE1_TOOLS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import phase1_statement_hardened_after_canonical_repair_paid_validation as paid_validation  # noqa: E402
import workspace_acut_run as workspace_acut  # noqa: E402


MATRIX = REPO_ROOT / "experiments" / "phase0_headroom" / "configs" / "phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml"
MANIFEST = REPO_ROOT / "experiments" / "phase1_compiler" / "results" / "phase1_statement_hardened_after_canonical_repair_release_manifest.json"
INVENTORY = REPO_ROOT / "experiments" / "phase1_compiler" / "results" / "phase1_statement_hardened_after_canonical_repair_inventory.json"


def package_by_id() -> dict[str, workspace_acut.TaskPackage]:
    return {package.task_id: package for package in workspace_acut.load_phase0_packages(REPO_ROOT, matrix_config_path=MATRIX)}


def test_all_16_canonical_tasks_are_selectable() -> None:
    packages = package_by_id()

    assert list(packages) == paid_validation.expected_task_ids()


def test_boltons_clean_ext_017_remains_boltons_h_future() -> None:
    package = package_by_id()["boltons__clean_ext__017"]

    assert package.repo_id == "boltons"
    assert package.split == "H_future"
    assert package.metadata["canonical_repo_split"] == "boltons/H_future"


def test_statement_text_digest_matches_frozen_digest() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for task_id, package in package_by_id().items():
        assert paid_validation.digest_text(package.solver_facing_statement) == manifest["statement_digests"][task_id]
        assert package.metadata["statement_digest"] == manifest["statement_digests"][task_id]


def test_tests_are_non_editable_for_statement_hardened_packages() -> None:
    for package in package_by_id().values():
        assert package.test_paths
        assert all(workspace_acut.is_test_path(path) for path in package.test_paths)
        assert not set(package.allowed_code_paths).intersection(package.test_paths)
        rendered = workspace_acut.render_statement(package)
        for path in package.test_paths:
            assert path not in rendered.split("## Editable Paths", 1)[1].split("## Non-Editable Paths", 1)[0]
            assert path in rendered.split("## Non-Editable Paths", 1)[1]


def test_current_inventory_split_is_not_used_for_selection() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    packages = package_by_id()

    assert inventory["summary"]["current_inventory_split_used_for_selection"] is False
    actual = {}
    for package in packages.values():
        actual.setdefault(f"{package.repo_id}/{package.split}", []).append(package.task_id)
    assert {key: sorted(value) for key, value in actual.items()} == {
        key: sorted(value) for key, value in manifest["canonical_selected_task_ids_by_repo_split"].items()
    }


def test_paid_outcomes_do_not_affect_package_loading() -> None:
    source = inspect.getsource(workspace_acut.load_statement_hardened_after_canonical_repair_packages)

    assert "score_table" not in source
    assert "verifier_results" not in source
    assert "submissions" not in source
    assert "cost_ledger" not in source


def test_solver_visible_statements_do_not_contain_forbidden_material() -> None:
    for package in package_by_id().values():
        assert paid_validation.statement_findings(package.solver_facing_statement) == []


def test_no_followup_runbook_file_is_created() -> None:
    forbidden = REPO_ROOT / "docs" / "experiments" / "phase-1-statement-hardened-paid-validation-followup-runbook.md"

    assert not forbidden.exists()
