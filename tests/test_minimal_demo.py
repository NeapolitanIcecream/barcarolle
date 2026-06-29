from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_minimal_demo_writes_reports_with_selected_and_future_evidence(tmp_path: Path) -> None:
    output_dir = tmp_path / "demo-out"

    completed = subprocess.run(
        [
            sys.executable,
            "examples/minimal/run_demo.py",
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    report_md = output_dir / "report.md"
    report_json = output_dir / "report.json"
    assert report_md.exists()
    assert report_json.exists()
    assert str(report_md) in completed.stdout
    assert str(report_json) in completed.stdout

    report_text = report_md.read_text(encoding="utf-8")
    assert "Claim Boundary" not in report_text
    assert str(tmp_path) not in report_text
    assert "Selector Performance" in report_text
    assert "future_holdout" in report_text
    assert "selected" in report_text

    report = json.loads(report_json.read_text(encoding="utf-8"))
    section_ids = [section["section_id"] for section in report]
    assert section_ids == ["task_pool", "agent_results", "selector_performance"]
    selector_section = next(section for section in report if section["section_id"] == "selector_performance")
    selection_summary = selector_section["summary"]["selections"][0]
    assert selection_summary["matrix_roles"] == ["future_holdout", "selected"]
    assert selection_summary["selected_task_check_count"] == 1
    assert selection_summary["metrics"]
