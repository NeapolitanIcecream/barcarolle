from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_blocked_split_supplement_fairness_gap_diagnostics as diagnostics  # noqa: E402


def _yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    lines: list[str] = []

    def emit(key: str, value: object, indent: int) -> None:
        prefix = " " * indent
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            for child_key, child_value in value.items():
                emit(str(child_key), child_value, indent + 2)
        elif isinstance(value, list):
            lines.append(f"{prefix}{key}:")
            for item in value:
                lines.append(f"{prefix}  - {_yaml_scalar(item)}")
        else:
            lines.append(f"{prefix}{key}: {_yaml_scalar(value)}")

    for key, value in payload.items():
        emit(key, value, 0)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def temp_config_path(tmp_path: Path) -> Path:
    config = diagnostics.load_config()
    config.pop("_path", None)
    config["outputs"] = {
        key: str(tmp_path / "results" / Path(path).name)
        for key, path in config["outputs"].items()
    }
    config["reports"] = {
        key: str(tmp_path / "reports" / Path(path).name)
        for key, path in config["reports"].items()
    }
    path = tmp_path / "diagnostics.yaml"
    _write_yaml(path, config)
    return path


def test_combined_rows_preserve_one_non_scoreable_invalid_output() -> None:
    rows = diagnostics.combined_rows()
    invalid_rows = [row for row in rows if row["terminal_status"] == "invalid_output"]

    assert len(rows) == 120
    assert sum(1 for row in rows if row["scoreable_cell"]) == 119
    assert len(invalid_rows) == 1
    assert invalid_rows[0]["adapter_id"] == "codex_workspace"
    assert invalid_rows[0]["task_id"] == "attrs__v2__157"


def test_repo_gap_matrix_identifies_expected_drivers(tmp_path: Path) -> None:
    payload = diagnostics.build_repo_gap_matrix(temp_config_path(tmp_path))

    assert payload["by_adapter"]["codex_workspace"]["by_repo"]["click"]["absolute_gap"] == 0.3
    assert "high_gap" in payload["by_adapter"]["codex_workspace"]["by_repo"]["click"]["gap_driver_labels"]
    assert payload["by_adapter"]["kilo_workspace"]["by_repo"]["boltons"]["absolute_gap"] == 0.2
    assert "non_scoreable_sensitive" in payload["by_adapter"]["codex_workspace"]["by_repo"]["attrs"]["gap_driver_labels"]


def test_adapter_disagreement_reconciles_known_overall_rate(tmp_path: Path) -> None:
    payload = diagnostics.build_adapter_disagreement(temp_config_path(tmp_path))

    assert payload["overall"]["paired_task_count"] == 59
    assert payload["overall"]["disagreement_rate"] == 0.4068
    assert payload["overall"]["both_fail"] == 21
    assert payload["overall"]["both_pass"] == 14
    assert payload["overall"]["codex_only_pass"] == 3
    assert payload["overall"]["kilo_only_pass"] == 21
    assert payload["by_repo"]["click"]["disagreement_rate"] == 0.5


def test_invalid_output_triage_uses_sanitized_score_table_only(tmp_path: Path) -> None:
    payload = diagnostics.build_invalid_output_triage(temp_config_path(tmp_path))

    assert payload["classification"] == "adapter_output_contract_violation"
    assert payload["invalid_cell"]["score_table"].endswith("_batch_1_smoke_codex_workspace_score_table.csv")
    assert payload["same_task_other_adapter"][0]["adapter_id"] == "kilo_workspace"
    assert payload["same_task_other_adapter"][0]["terminal_status"] == "verified_fail"
    assert payload["threat_assessment"]["threatens_supplement_conclusion"] is False


def test_previous_split_comparison_keeps_claim_boundary_exploratory(tmp_path: Path) -> None:
    payload = diagnostics.build_previous_split_comparison(temp_config_path(tmp_path))

    assert payload["comparison"]["pooled_gap"]["previous_three_repo_primary_pooled_gap"] == 0.1
    assert payload["comparison"]["pooled_gap"]["supplement_pooled_gap"] == 0.1079
    assert payload["overall_diagnostic_label"] == "about_the_same_or_slightly_worse"
    assert payload["claim_boundary"]["predictive_validity_established"] is False
