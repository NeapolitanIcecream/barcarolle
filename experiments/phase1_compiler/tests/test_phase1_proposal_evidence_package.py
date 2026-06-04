from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PHASE1_TOOLS = REPO_ROOT / "experiments" / "phase1_compiler" / "tools"
if str(PHASE1_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE1_TOOLS))

import phase1_proposal_evidence_package as package  # noqa: E402


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
    config = package.load_config()
    config.pop("_path", None)
    config["settings"]["random_seed_count"] = 12
    config["settings"]["random_seed_start"] = 2026060190
    config["outputs"] = {
        key: str(tmp_path / "results" / Path(path).name)
        for key, path in config["outputs"].items()
    }
    config["reports"] = {
        key: str(tmp_path / "reports" / Path(path).name)
        for key, path in config["reports"].items()
    }
    config["docs"] = {
        key: str(tmp_path / "docs" / Path(path).name)
        for key, path in config["docs"].items()
    }
    path = tmp_path / "proposal_evidence_package.yaml"
    _write_yaml(path, config)
    return path


def test_config_forbids_paid_calls_external_review_and_browsing() -> None:
    config = package.load_config()

    assert config["paid_calls_allowed"] is False
    assert config["external_review_allowed"] is False
    assert config["public_citation_browsing_allowed"] is False


def test_many_seed_random_distribution_is_deterministic_and_adapter_stratified(tmp_path: Path) -> None:
    config_path = temp_config_path(tmp_path)
    first = package.build_random_baseline_distribution(config_path)
    first_digest = package.digest_payload(first)
    second = package.build_random_baseline_distribution(config_path)

    assert package.digest_payload(second) == first_digest
    assert first["seed_count"] == 12
    assert first["primary_reporting"] == "adapter_stratified"
    assert {row["group_id"] for row in first["group_distributions"] if row["group_type"] == "adapter"} == set(package.signal.ADAPTERS)
    overall = next(row for row in first["group_distributions"] if row["group_type"] == "overall")
    assert overall["candidate_MAE_percentile"]["beats_random_share"] is not None


def test_all_required_outputs_are_created_with_guardrail_flags(tmp_path: Path) -> None:
    config_path = temp_config_path(tmp_path)
    package.build_all(config_path)
    config = package.load_config(config_path)

    required_output_keys = {
        "preflight",
        "preliminary_evidence_summary",
        "random_baseline_distribution",
        "baseline_envelope",
        "coverage_ablation",
        "fallback_share",
        "source_supply_status",
        "report_evidence_index",
        "decision",
    }
    assert required_output_keys <= set(config["outputs"])
    for key in required_output_keys:
        assert package.output_path(config, key).exists()
    for key in config["reports"]:
        assert package.report_path(config, key).exists()
    assert package.doc_path(config, "proposal_evidence_package").exists()

    decision = package.read_json(package.output_path(config, "decision"))
    assert decision["predictive_validity_established"] is False
    assert decision["paid_validation_authorized"] is False
    assert decision["paid_ACUT_cells"] == 0
    assert decision["paid_LLM_calls"] == 0


def test_baseline_envelope_keeps_adapter_primary_and_no_success_gate(tmp_path: Path) -> None:
    config_path = temp_config_path(tmp_path)
    envelope = package.build_baseline_envelope(config_path)

    assert envelope["primary_reporting"] == "adapter_stratified"
    adapter_rows = [row for row in envelope["rows"] if row["group_type"] == "adapter"]
    assert adapter_rows
    assert all(row["candidate_relation_to_best_baseline"] in {"candidate_better", "candidate_worse", "tied", "insufficient_support"} for row in adapter_rows)
    assert "success_threshold" not in envelope


def test_fallback_share_quantifies_boltons_without_setting_threshold(tmp_path: Path) -> None:
    config_path = temp_config_path(tmp_path)
    fallback = package.build_fallback_share(config_path)

    assert fallback["fallback_selected_count_by_repo"]["boltons"] == 6
    assert fallback["fallback_share_by_repo"]["boltons"] == 1.0
    assert fallback["fallback_threshold_set_by_M3"] is False
    assert fallback["claim_label"] == "needs_M4_protocol_decision"
