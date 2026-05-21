from __future__ import annotations

import json
from pathlib import Path

import repo_history_pilot as pilot


def test_stable_task_id_generation() -> None:
    assert pilot.stable_task_id("humanize", 1) == "humanize__hist__001"
    assert pilot.stable_task_id("humanize", 16) == "humanize__hist__016"


def test_code_test_path_classification_for_src_and_flat_layouts() -> None:
    code, tests = pilot.classify_paths(
        [
            "src/humanize/time.py",
            "src/humanize/py.typed",
            "tests/test_time.py",
            "docs/index.md",
            "humanize/filesize.py",
            "test_filesize.py",
            "setup.py",
        ]
    )

    assert code == ["humanize/filesize.py", "src/humanize/time.py"]
    assert tests == ["test_filesize.py", "tests/test_time.py"]


def test_first_failing_gate_selection() -> None:
    gates = {gate: "pass" for gate in pilot.GATE_ORDER}
    gates["reference_pass"] = "fail"
    gates["solution_leakage_review"] = "fail"

    assert pilot.first_failing_gate(gates) == "reference_pass"
    assert pilot.task_status(gates) == "near_certified"


def test_release_split_generation() -> None:
    rows = [
        {"task_id": "humanize__hist__004", "task_time": "2023-01-01T00:00:00+00:00"},
        {"task_id": "humanize__hist__001", "task_time": "2020-01-01T00:00:00+00:00"},
        {"task_id": "humanize__hist__003", "task_time": "2022-01-01T00:00:00+00:00"},
        {"task_id": "humanize__hist__002", "task_time": "2021-01-01T00:00:00+00:00"},
    ]

    assert pilot.split_release_tasks(rows) == {
        "B_real": ["humanize__hist__001", "humanize__hist__002"],
        "W_real": ["humanize__hist__003", "humanize__hist__004"],
    }


def test_release_payload_marks_pilot_and_benchmark_grade(tmp_path: Path) -> None:
    config = pilot.PilotConfig(
        repo_id="humanize",
        repo_url="https://example.invalid/humanize.git",
        local_repo=tmp_path,
        command_template="python -m pytest -q {test_files}",
        certification_attempts=6,
        pilot_certified_min=4,
        benchmark_grade_min=6,
        result_prefix="humanize_pre_phase1_workspace",
    )
    rows = [
        {"task_id": f"humanize__hist__{i:03d}", "task_time": f"202{i}-01-01T00:00:00+00:00"}
        for i in range(1, 7)
    ]

    payload = pilot.release_payload(config, rows)

    assert payload["pilot_grade"] is True
    assert payload["benchmark_grade"] is True
    assert payload["splits"]["B_real"] == ["humanize__hist__001", "humanize__hist__002", "humanize__hist__003"]
    assert payload["splits"]["W_real"] == ["humanize__hist__004", "humanize__hist__005", "humanize__hist__006"]


def test_committed_json_rows_do_not_copy_raw_source_text(tmp_path: Path) -> None:
    path = tmp_path / "rows.jsonl"
    rows = [
        {
            "task_id": "humanize__hist__001",
            "changed_files": ["src/humanize/time.py", "tests/test_time.py"],
            "summary_hash": "abc123",
        }
    ]
    pilot.write_jsonl(path, rows)

    serialized = path.read_text(encoding="utf-8")
    assert "def naturaltime" not in serialized
    assert "diff --git" not in serialized
    assert json.loads(serialized)["task_id"] == "humanize__hist__001"
