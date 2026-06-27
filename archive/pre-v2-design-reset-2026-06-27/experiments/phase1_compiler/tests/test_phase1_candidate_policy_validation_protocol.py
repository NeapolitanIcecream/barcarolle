from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_candidate_policy_validation_protocol as protocol  # noqa: E402


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
    config = protocol.load_config()
    config.pop("_path", None)
    config["outputs"] = {
        key: str(tmp_path / "results" / Path(path).name)
        for key, path in config["outputs"].items()
    }
    config["reports"] = {
        key: str(tmp_path / "reports" / Path(path).name)
        for key, path in config["reports"].items()
    }
    config["external_review_packet"] = {
        key: str(tmp_path / "external_review" / Path(path).name)
        if key != "directory"
        else str(tmp_path / "external_review")
        for key, path in config["external_review_packet"].items()
    }
    path = tmp_path / "candidate_policy_validation_protocol.yaml"
    _write_yaml(path, config)
    return path


def synthetic_row(task_id: str, family: str = "family_a", time_bucket: str = "recent_2023_or_later") -> dict[str, object]:
    return {
        "task_id": task_id,
        "repo": "demo",
        "task_time": "",
        "time_bucket": time_bucket,
        "coarse_task_family": family,
        "editable_scope_bucket": "single_module",
        "source_context_type_bucket": "issue_or_pr",
        "source_quality_bucket": "clean",
        "statement_specificity_bucket": "acceptable",
        "context_length_bucket": "short",
        "ambiguity_risk_bucket": "low",
        "leakage_risk_bucket": "low",
        "certification_risk_bucket": "technical_certified_release_eligible",
        "rare_or_unknown_feature_flag": False,
        "source_reservoir": "fixture",
        "source_context_class": "issue_or_pr_context",
        "implementation_file_count": 1,
        "test_file_count": 1,
        "public_context_ref_count": 1,
        "release_eligibility_provenance": "fixture",
        "repair_overlay_status": "not_applicable",
        "statement_digest": "sha256:fixture",
        "eligible_for_policy_selection": True,
        "exclusion_reasons": [],
    }


def test_forbidden_outcome_fields_are_rejected() -> None:
    forbidden = {"terminal_status", "verified_pass"}
    with pytest.raises(ValueError, match="terminal_status"):
        protocol.validate_no_forbidden_fields({"rows": [{"task_id": "x", "terminal_status": "verified_pass"}]}, forbidden, "fixture")


def test_seeded_tiebreak_is_deterministic() -> None:
    rows = [
        synthetic_row("demo__001", "family_a"),
        synthetic_row("demo__002", "family_a"),
        synthetic_row("demo__003", "family_a"),
    ]
    features = ["coarse_task_family", "time_bucket"]
    first, _, _ = protocol.select_policy_rows(
        rows,
        repo="demo",
        budget=2,
        features=features,
        seed=2026053001,
        policy_id="coverage_constrained_unweighted_v1",
    )
    second, _, _ = protocol.select_policy_rows(
        rows,
        repo="demo",
        budget=2,
        features=features,
        seed=2026053001,
        policy_id="coverage_constrained_unweighted_v1",
    )

    assert [row["task_id"] for row in first] == [row["task_id"] for row in second]


def test_fallback_label_is_explicit_when_feature_support_is_sparse() -> None:
    rows = [synthetic_row(f"demo__{index:03d}") for index in range(1, 7)]
    fallback = protocol.selection_fallback_status(
        {
            "coverage_features": ["coarse_task_family", "time_bucket"],
            "policy": {
                "minimum_supported_feature_dimensions": 3,
                "fallback_insufficient_budget": "repo_unweighted_same_budget",
                "fallback_insufficient_feature_support": "repo_stratified_by_target_profile",
            },
        },
        rows,
        6,
    )

    assert fallback["fallback_applied"] is True
    assert fallback["fallback_reason"] == "insufficient_feature_support"
    assert fallback["fallback_design"] == "repo_stratified_by_target_profile"


def test_run_outputs_manifest_digests_and_no_score_tables(tmp_path: Path) -> None:
    config_path = temp_config_path(tmp_path)
    _, selection, audit = protocol.build_input_freeze_and_selection(config_path)

    assert selection["selected_task_ids"]
    assert selection["excluded_task_ids_with_reasons"]
    assert selection["input_artifact_digests"]
    assert selection["score_tables_read_for_selection"] == []
    assert selection["terminal_outcomes_loaded"] is False
    assert audit["outcome_blind"] is True
    assert audit["score_tables_read_for_selection"] == []
    assert audit["terminal_outcomes_loaded"] is False
