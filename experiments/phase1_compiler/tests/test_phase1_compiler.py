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


def test_import_cli_writes_release_and_weighted_summary(tmp_path: Path) -> None:
    args = type("Args", (), {"phase0_root": str(compiler.PHASE0_ROOT), "output_dir": str(tmp_path)})()

    compiler.run_import_phase0(args)

    assert (tmp_path / "toolz_phase1_draft_release.json").exists()
    assert (tmp_path / "toolz_phase1_weighted_score.json").exists()
