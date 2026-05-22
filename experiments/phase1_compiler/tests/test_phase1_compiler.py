from __future__ import annotations

import json
from pathlib import Path

import pytest

import phase1_compiler as compiler


def test_import_phase0_release_validates_draft_release() -> None:
    release = compiler.import_phase0_release()

    assert release.schema_version == "barcarolle.phase1.release_manifest.v1"
    assert release.status == "draft_imported_from_phase0"
    assert len(release.tasks) == 10
    assert release.splits["B_real"] == ["toolz__hist__001", "toolz__hist__002", "toolz__hist__003"]


def test_weighted_score_is_computed_when_all_profile_strata_are_compatible() -> None:
    scorecard = compiler.Scorecard(
        run_id="unit",
        cells=[
            compiler.ScorecardCell("a", "B_real", "verified_pass", True, ["functoolz"]),
            compiler.ScorecardCell("b", "W_real", "verified_fail", True, ["itertoolz"]),
        ],
    )
    target = compiler.TargetProfile(repo_id="toolz", strata={"module_or_package": {"functoolz": 0.75, "itertoolz": 0.25}})

    summary = compiler.compute_weighted_score(scorecard, target)

    assert summary.evidence_status == "compatible"
    assert summary.weighted_score == 0.75
    assert summary.insufficient_evidence == []


def test_weighted_score_marks_incompatible_outcomes_as_insufficient_evidence() -> None:
    scorecard = compiler.Scorecard(
        run_id="unit",
        cells=[
            compiler.ScorecardCell("a", "B_real", "invalid_output", False, ["functoolz"]),
        ],
    )
    target = compiler.TargetProfile(repo_id="toolz", strata={"module_or_package": {"functoolz": 1.0}})

    summary = compiler.compute_weighted_score(scorecard, target)

    assert summary.evidence_status == "insufficient_evidence"
    assert summary.weighted_score is None
    assert summary.insufficient_evidence == ["functoolz"]


def test_scorecard_import_records_acut_source_metadata(tmp_path: Path) -> None:
    score_table = tmp_path / "score_table.csv"
    score_table.write_text(
        "\n".join(
            [
                "adapter_id,acut_id,harness_name,model_or_agent_name,task_id,split,attempt,submission_status,terminal_status,verifier_exit_code,scoreable_cell,agent_failure,harness_error",
                "codex_workspace,codex_acut,codex,gpt,toolz__hist__001,B_real,1,submitted,verified_pass,0,True,False,False",
                "kilo_workspace,kilo_acut,kilo,gpt,toolz__hist__002,B_real,1,submitted,verified_fail,1,True,True,False",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    release = compiler.import_phase0_release()

    scorecard = compiler.scorecard_from_phase0(release, score_table_path=score_table, run_id="followup")
    summary = compiler.compute_weighted_score(
        scorecard,
        compiler.TargetProfile(repo_id="toolz", strata={"module_or_package": {"functoolz": 1.0}}),
    )

    assert scorecard.run_id == "followup"
    assert summary.source_score_table == str(score_table)
    assert summary.acut_ids == ["codex_acut", "kilo_acut"]
    assert summary.cell_count == 2
    assert summary.compatible_cell_count == 2


def test_import_cli_writes_release_and_weighted_summary(tmp_path: Path) -> None:
    args = type("Args", (), {"phase0_root": str(compiler.PHASE0_ROOT), "output_dir": str(tmp_path)})()

    compiler.run_import_phase0(args)

    assert (tmp_path / "toolz_phase1_draft_release.json").exists()
    assert (tmp_path / "toolz_phase1_weighted_score.json").exists()


def test_inventory_generation_records_targets_and_comparator(tmp_path: Path) -> None:
    args = type("Args", (), {"config": str(compiler.DEFAULT_CONFIG), "output_root": str(tmp_path)})()

    payload = compiler.run_inventory(args)

    assert payload["predictive_validity_established"] is False
    assert {repo["repo_id"] for repo in payload["target_repos"]} == {"toolz", "humanize"}
    assert payload["generic_comparators"] == [
        {"repo_id": "click", "role": "generic_comparator", "source_provenance": "generic_comparator_archived_click_r0"}
    ]
    assert (tmp_path / "results" / "phase1_input_inventory.json").exists()
    assert (tmp_path / "reports" / "phase1_input_inventory.md").exists()


def test_inventory_fails_closed_on_missing_artifact(tmp_path: Path) -> None:
    config_text = compiler.DEFAULT_CONFIG.read_text(encoding="utf-8")
    config_path = tmp_path / "phase1_mvp.yaml"
    config_path.write_text(
        config_text.replace(
            "experiments/phase0_headroom/results/pre_phase1_gate.json",
            "experiments/phase0_headroom/results/does_not_exist.json",
        ),
        encoding="utf-8",
    )
    args = type("Args", (), {"config": str(config_path), "output_root": str(tmp_path)})()

    with pytest.raises(FileNotFoundError):
        compiler.run_inventory(args)


def test_schema_files_are_json_and_phase1_release_validates() -> None:
    for name in [
        "phase1_release.schema.json",
        "phase1_scorecard.schema.json",
        "phase1_certification_rollup.schema.json",
    ]:
        payload = json.loads((compiler.ROOT / "schemas" / name).read_text(encoding="utf-8"))
        assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    release = compiler.build_release_payload(compiler.load_mvp_config())

    compiler.validate_phase1_release_payload(release)
    assert release["status"] == "pilot_grade"
    assert len([task for task in release["tasks"] if task["repo_id"] == "toolz"]) == 6
    assert len([task for task in release["tasks"] if task["repo_id"] == "humanize"]) == 12
    assert release["generic_comparators"][0]["repo_id"] == "click"
    assert len(release["generic_comparators"][0]["tasks"]) == 4


def test_invalid_predictive_validity_claim_is_rejected() -> None:
    release = compiler.build_release_payload(compiler.load_mvp_config())
    release["predictive_validity_established"] = True

    with pytest.raises(compiler.ValidationError):
        compiler.validate_phase1_release_payload(release)


def test_invalid_repo_role_is_rejected() -> None:
    release = compiler.build_release_payload(compiler.load_mvp_config())
    release["repos"][0]["role"] = "production_benchmark_repo"

    with pytest.raises(compiler.ValidationError):
        compiler.validate_phase1_release_payload(release)


def test_humanize_legacy_benchmark_grade_does_not_override_pilot_status() -> None:
    release = compiler.build_release_payload(compiler.load_mvp_config())
    humanize = next(repo for repo in release["repos"] if repo["repo_id"] == "humanize")

    assert humanize["legacy_benchmark_grade"] is True
    assert humanize["source_release_status"] == "pilot_grade"
    assert release["status"] == "pilot_grade"


def test_closeout_reuses_hardening_next_runbook_recommendation() -> None:
    recommendation = compiler.closeout_next_runbook_recommendation(
        {
            "primary_decision_label": "replace_third_repo_before_paid_acut",
            "recommended_next_runbook": "select_replacement_third_repo_and_locally_certify_without_paid_acut",
        }
    )

    assert recommendation == "select_replacement_third_repo_and_locally_certify_without_paid_acut"


def test_scorecard_import_preserves_humanize_cells_and_result_prefixes(tmp_path: Path) -> None:
    args = type("Args", (), {"config": str(compiler.DEFAULT_CONFIG), "output_root": str(tmp_path)})()

    payload = compiler.run_import_scorecards(args)

    assert payload["summary"]["humanize_cell_count"] == 8
    assert set(payload["summary"]["by_result_prefix"]) == {
        "codex_kilo_workspace_followup",
        "codex_kilo_workspace_stability",
        "humanize_pre_phase1_workspace",
    }
    assert any(cell["policy_violation"] for cell in payload["cells"])
    assert all(cell["comparison_label"] == "same_endpoint_model_different_cli_harnesses" for cell in payload["cells"])


def test_build_mvp_orchestration_writes_all_outputs(tmp_path: Path) -> None:
    args = type("Args", (), {"config": str(compiler.DEFAULT_CONFIG), "output_root": str(tmp_path)})()

    result = compiler.run_build_mvp(args)

    assert result["commands"] == compiler.BUILD_MVP_COMMANDS
    for name in [
        "phase1_input_inventory.json",
        "phase1_certification_rollup.json",
        "phase1_mvp_release.json",
        "phase1_split_plan.json",
        "phase1_workspace_scorecard.json",
        "phase1_cost_summary.json",
        "phase1_weighted_score.json",
        "phase1_uncertainty_summary.json",
        "phase1_mvp_closeout.json",
    ]:
        assert (tmp_path / "results" / name).exists()
