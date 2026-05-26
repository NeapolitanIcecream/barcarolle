from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
PHASE0_TOOLS = REPO_ROOT / "experiments" / "phase0_headroom" / "tools"
for path in [PHASE1_TOOLS, PHASE0_TOOLS]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import phase1_weighted_design_paid_pilot as pilot  # noqa: E402
import workspace_acut_run  # noqa: E402


def test_frozen_union_contains_only_new_local_candidates() -> None:
    task_ids = pilot.frozen_union_task_ids()
    historical = set(pilot.candidate_task_ids(pilot.candidate_by_id()[pilot.HISTORICAL_REFERENCE_ID]))

    assert len(task_ids) == 22
    assert task_ids[:3] == ["attrs__hist__009", "attrs__hist__010", "attrs__hist__032"]
    assert task_ids[-3:] == ["boltons__hist__026", "boltons__hist__028", "boltons__hist__031"]
    assert not set(task_ids).intersection(historical)


def test_workspace_matrix_records_44_cells_and_preserves_order() -> None:
    matrix = pilot.workspace_matrix_payload()

    assert matrix["phase1_weighted_design_paid_pilot"] is True
    assert matrix["historical_reference_rerun"] is False
    assert len(matrix["task_ids"]) * len(pilot.PLANNED_ADAPTERS) == 44
    assert workspace_acut_run.matrix_task_ids(matrix) == pilot.frozen_union_task_ids()
    assert set().union(*[set(values) for values in matrix["repo_splits"].values()]) == set(matrix["task_ids"])


def test_paid_pilot_package_loader_matches_frozen_statement_digests(tmp_path: Path) -> None:
    matrix_path = tmp_path / "phase1_weighted_design_paid_pilot_workspace_matrix.yaml"
    pilot.write_simple_yaml(matrix_path, pilot.workspace_matrix_payload())

    packages = workspace_acut_run.load_phase0_packages(pilot.REPO_ROOT, matrix_path)

    assert len(packages) == 22
    assert [package.task_id for package in packages] == pilot.frozen_union_task_ids()
    for package in packages:
        assert package.metadata["statement_digest"] == f"sha256:{workspace_acut_run.sha256_text(package.solver_facing_statement)}"
        assert package.allowed_code_paths
        assert package.test_paths
        assert package.repo_id in {"attrs", "boltons"}


def test_preflight_records_ready_gates_without_paid_calls(monkeypatch) -> None:
    monkeypatch.setattr(pilot, "existing_paid_outputs", lambda: [])

    payload = pilot.build_preflight(write=False)

    assert payload["status"] == "ready_for_local_entry_steps"
    assert payload["paid_pilot_approval_granted_by_runbook"] is True
    assert payload["planned_cells"] == 44
    assert payload["historical_reference_rerun"] is False
    assert payload["checks"]["new_paid_acut_cells_for_this_release_not_already_run"] is True
