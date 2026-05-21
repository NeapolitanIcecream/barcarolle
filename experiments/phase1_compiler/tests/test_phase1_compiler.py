from __future__ import annotations

from pathlib import Path

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
