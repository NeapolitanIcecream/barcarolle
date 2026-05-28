from __future__ import annotations

from pathlib import Path

import phase1_third_repo_release_supply_screen as screen


def test_shortlist_labels_every_seed_and_respects_raw_mining_cap(monkeypatch) -> None:
    config = {
        "run_id": "test",
        "seed_candidate_repos": ["a", "b", "c", "d"],
        "caps": {"repos_advanced_to_raw_mining": 2, "candidate_repos_in_cheap_screen": 4},
    }
    fake_rows = {
        "a": repo_row("a", impl_tests=200, refs=80, score=28),
        "b": repo_row("b", impl_tests=100, refs=60, score=25),
        "c": repo_row("c", impl_tests=150, refs=10, score=22),
        "d": repo_row("d", impl_tests=10, refs=5, score=12),
    }
    monkeypatch.setattr(screen, "cheap_repo_row", lambda _config, repo_id: dict(fake_rows[repo_id]))

    payload = screen.build_repo_shortlist(config)

    assert payload["repos_advanced_to_raw_mining"] == ["a", "b"]
    assert len(payload["repos_advanced_to_raw_mining"]) == 2
    assert {row["overall_screen_label"] for row in payload["rows"]} <= {
        "advance_to_raw_mining",
        "backup_only",
        "reject_for_this_run",
    }
    assert {row["repo_id"] for row in payload["rows"]} == {"a", "b", "c", "d"}


def test_raw_inventory_status_distinguishes_oracle_missing_duplicates_and_scope() -> None:
    base = {
        "base_commit": "a" * 40,
        "target_commit_optional": "b" * 40,
        "implementation_files": ["pkg/core.py"],
        "test_files": ["tests/test_core.py"],
        "source_context_quality": "pr_title_only_context",
    }

    assert screen.raw_inventory_status(base, duplicate=False) == "oracle_usable"
    assert screen.raw_inventory_status({**base, "test_files": []}, duplicate=False) == "oracle_missing_inventory_only"
    assert screen.raw_inventory_status({**base, "implementation_files": []}, duplicate=False) == "candidate_outside_scope"
    assert screen.raw_inventory_status({**base, "source_context_quality": "material_leakage_risk"}, duplicate=False) == "material_leakage_risk"
    assert screen.raw_inventory_status(base, duplicate=True) == "duplicate_candidate"


def test_source_and_oracle_screens_keep_release_ready_separate_from_review_upper_bound() -> None:
    config = {"run_id": "test"}
    raw = {
        "rows": [
            raw_row("repo", "a", "pr_title_only_context", ["tests/test_a.py"], "oracle_usable"),
            raw_row("repo", "b", "commit_message_only_context", ["tests/test_b.py"], "oracle_usable"),
            raw_row("repo", "c", "pr_title_only_context", [], "oracle_missing_inventory_only"),
            raw_row("repo", "d", "material_leakage_risk", ["tests/test_d.py"], "material_leakage_risk"),
        ]
    }

    source = screen.build_source_context_inventory(config, raw)
    oracle = screen.build_oracle_matrix(config, raw)

    assert source["release_ready_before_certification_count_by_repo"] == {"repo": 1}
    assert source["technical_plus_review_upper_bound_count_by_repo"] == {"repo": 2}
    assert oracle["oracle_classification_counts_by_repo"]["repo"] == {
        "changed_test_oracle_available": 2,
        "material_leakage_risk": 1,
        "oracle_missing_inventory_only": 1,
    }


def test_environment_selection_requires_release_ready_or_bounded_source_repair_path() -> None:
    config = {
        "caps": {"repos_advanced_to_certification_wave": 3},
        "selection_policy": {
            "release_ready_min_before_certification": 45,
            "source_repair_upper_bound_min": 90,
            "source_repair_release_ready_floor": 30,
        },
    }
    source = {
        "release_ready_before_certification_count_by_repo": {
            "packaging": 120,
            "cachetools": 53,
            "click": 38,
            "tiny": 12,
        },
        "technical_plus_review_upper_bound_count_by_repo": {
            "packaging": 200,
            "cachetools": 88,
            "click": 180,
            "tiny": 200,
        },
    }

    assert screen.selected_repos_for_environment(config, source) == ["packaging", "cachetools", "click"]


def test_release_gate_requires_attrs_boltons_and_a_third_repo(tmp_path: Path) -> None:
    attrs_gate = tmp_path / "attrs_gate.json"
    attempts_path = tmp_path / "attempts.json"
    release_gate_path = tmp_path / "release_gate.json"
    attrs_gate.write_text(
        '{"release_eligible_count_by_repo":{"attrs":31,"boltons":35}}',
        encoding="utf-8",
    )
    attempts_path.write_text(
        '{"unattempted_selected_count":18,"rows":['
        + ",".join(
            '{"candidate_id":"p%03d","repo_id":"packaging","technical_certified":true,"release_eligible":true}' % index
            for index in range(30)
        )
        + "]}",
        encoding="utf-8",
    )
    config = {
        "run_id": "test",
        "inputs": {"attrs_source_repair_gate": str(attrs_gate)},
        "outputs": {"certification_attempts": str(attempts_path), "release_gate": str(release_gate_path)},
        "selection_policy": {"release_eligible_min_per_repo": 30, "repos_required_at_min": 3},
    }

    gate = screen.build_release_gate(config)

    assert gate["paid_ready"] is True
    assert gate["repos_meeting_30_release_eligible"] == ["attrs", "boltons", "packaging"]
    assert "selected_candidates_still_unattempted" not in gate["blocking_reasons"]


def test_probe_sampling_is_capped_per_repo() -> None:
    config = {"caps": {"environment_probe_sample_per_repo": 2}}
    raw = {
        "rows": [
            raw_row("repo", "a", "pr_title_only_context", ["tests/test_a.py"], "oracle_usable", task_time="2015-01-01T00:00:00+00:00"),
            raw_row("repo", "b", "pr_title_only_context", ["tests/test_b.py"], "oracle_usable", task_time="2019-01-01T00:00:00+00:00"),
            raw_row("repo", "c", "pr_title_only_context", ["tests/test_c.py"], "oracle_usable", task_time="2024-01-01T00:00:00+00:00"),
        ]
    }

    selected = screen.sample_probe_rows(config, raw, ["repo"])

    assert len(selected) == 2
    assert {row["candidate_id"] for row in selected} == {"repo__third__a", "repo__third__b"}


def repo_row(repo_id: str, *, impl_tests: int, refs: int, score: int) -> dict[str, object]:
    return {
        "repo_id": repo_id,
        "present": True,
        "commit_count_with_both_implementation_and_test_changes": impl_tests,
        "commit_count_with_both_implementation_and_test_changes_and_public_refs": refs,
        "overall_score": score,
        "rejection_reasons": [] if impl_tests >= 45 else ["too_few_implementation_plus_test_commits"],
    }


def raw_row(
    repo_id: str,
    suffix: str,
    quality: str,
    test_files: list[str],
    inventory_status: str,
    *,
    task_time: str = "2020-01-01T00:00:00+00:00",
) -> dict[str, object]:
    return {
        "candidate_id": f"{repo_id}__third__{suffix}",
        "repo_id": repo_id,
        "source_reservoir": "repo_history_v2_pr_issue_with_tests",
        "base_commit": "a" * 40,
        "target_commit_optional": "b" * 40,
        "implementation_files": ["pkg/core.py"],
        "test_files": test_files,
        "source_context_quality": quality,
        "public_context_refs": ["pr:1"] if quality == "pr_title_only_context" else [],
        "leakage_flags": [],
        "ambiguity_flags": [],
        "inventory_status": inventory_status,
        "task_time": task_time,
    }
