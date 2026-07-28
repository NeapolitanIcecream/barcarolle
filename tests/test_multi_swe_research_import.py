from __future__ import annotations

import json
import inspect
from pathlib import Path
import subprocess
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from barcarolle.records import canonical_digest  # noqa: E402
from examples.multi_swe_research.hindsight_diagnostic import (  # noqa: E402
    build_hindsight_evidence_summary,
    load_hindsight_plan,
    solve_exact_hindsight_subset,
)
from examples.multi_swe_research.prepare import (  # noqa: E402
    _graphql_query,
    _line_digest,
    _project_issue_text,
    _task_identity,
    load_contract,
    main,
    normalize_public_panel,
    project_task_content,
    project_task_times,
    validate_evidence,
)
from examples.multi_swe_research.semantic_selector import (  # noqa: E402
    build_embedding_artifact,
    kernel_mmd_squared,
    load_embedding_artifact,
    load_embedding_manifest,
    load_public_outcomes,
    load_selector_plan,
    outcome_pass_rate_mae,
    select_kernel_mean_herding,
    select_minimax_temporal_semantic_herding,
)
from examples.multi_repository_study.semantic import (  # noqa: E402
    SimilarityIndex,
    select_centroid_recent,
)


def test_committed_contract_is_digest_bound() -> None:
    contract = load_contract()
    assert contract["dataset"]["task_count"] == 1632
    assert len(contract["dataset"]["paths"]) == 39
    assert len(contract["results"]["configurations"]) == 36


def test_selector_plan_freezes_one_outcome_free_candidate() -> None:
    path = (
        REPOSITORY_ROOT
        / "examples"
        / "multi_swe_research"
        / "selector-plan.json"
    )
    plan = json.loads(path.read_text(encoding="utf-8"))
    digest = plan.pop("selector_plan_digest")

    assert canonical_digest(plan) == digest
    assert plan["source"]["contract_digest"] == load_contract()["contract_digest"]
    assert plan["candidate"]["algorithm_id"] == "ALG-012"
    assert plan["candidate"]["fitting"] == "none"
    assert plan["rolling_origin"]["selection_budget_tasks"] == 10
    assert plan["rolling_origin"]["primary_future_tasks"] == 5
    assert plan["rolling_origin"]["sensitivity_future_tasks"] == 10
    assert len(plan["rolling_origin"]["primary_repository_ids"]) == 13
    assert len(plan["rolling_origin"]["sensitivity_common_repository_ids"]) == 11
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["agent_groups"]["transfer_semantics"].startswith(
        "Selection is outcome-free"
    )
    assert load_selector_plan()["selector_plan_digest"] == digest


def test_committed_evidence_is_self_consistent() -> None:
    report = validate_evidence(
        load_contract(),
        REPOSITORY_ROOT / "examples" / "multi_swe_research" / "evidence",
    )
    assert report["task_count"] == 1632
    assert report["configuration_count"] == 36
    assert report["resolved_cell_count"] == 2913
    assert (
        report["content_manifest_digest"]
        == "9b47e946daf2e982e49e552f9a6976315787ae45b3923edda4a5aff9b53e78cb"
    )
    assert (
        report["task_text_digest"]
        == "c40c8b3f6c200020a1e961a54fe7d70392c8e3a7933687a2b4714654601b21cb"
    )
    assert (
        report["embedding_manifest_digest"]
        == "458a9375af9a079126b2a64b0ed115387d5602aad4b0c6439572d0b9a5a40f0d"
    )
    assert (
        report["selector_study_summary_digest"]
        == "c91459da16d42bb2c0a3ebb20a0c0df10fa441ae15037d736c9615c35cef6e61"
    )
    assert (
        report["hindsight_summary_digest"]
        == "cf6bee9578773068440c4ba73514488f7d8adccfb9157714a4077a2291f5d7d6"
    )
    assert report["paid_api_calls"] == 0
    supply = {
        row["future_block_tasks"]: row for row in report["origin_supply"]
    }
    assert supply[5]["origin_count"] == 221
    assert supply[5]["wide_repository_count"] == 13
    h5_training = supply[5]["source_time_training"]
    assert h5_training["median_origin_count"] == 75
    assert h5_training["median_repository_count"] == 5
    assert h5_training["targets_without_training_origin"] == 4
    assert (
        h5_training["targets_with_fewer_than_three_training_repositories"]
        == 17
    )
    assert supply[10]["origin_count"] == 107
    assert supply[10]["wide_repository_count"] == 11


def test_selector_study_summary_binds_failed_gates_and_raw_results() -> None:
    path = (
        REPOSITORY_ROOT
        / "examples"
        / "multi_swe_research"
        / "evidence"
        / "selector-study-summary.json"
    )
    summary = json.loads(path.read_text(encoding="utf-8"))
    digest = summary.pop("selector_study_summary_digest")

    assert canonical_digest(summary) == digest
    assert summary["algorithm_id"] == "ALG-012"
    assert summary["identities"]["selector_plan_digest"] == (
        load_selector_plan()["selector_plan_digest"]
    )
    assert summary["task_space"]["gate_met"] is False
    assert summary["agent_outcomes"]["gate_met"] is False
    assert summary["decision"]["nominated"] is False
    assert summary["agent_outcomes"]["h5"]["candidate_minus_full_history"] == (
        pytest.approx(-0.00027360585516431177)
    )
    assert summary["agent_outcomes"]["h10"]["candidate_minus_full_history"] == (
        pytest.approx(0.0024083334210041147)
    )
    assert summary["resource_use"]["paid_api_calls"] == 0


def test_hindsight_plan_is_descriptive_and_self_digested() -> None:
    plan = dict(load_hindsight_plan())
    digest = plan.pop("hindsight_plan_digest")

    assert canonical_digest(plan) == digest
    assert plan["diagnostic"]["diagnostic_id"] == (
        "exact_hindsight_response_milp"
    )
    assert plan["protocol"]["selection_budget_tasks"] == 10
    assert plan["motivation"]["claim_boundary"].startswith(
        "Future outcomes are deliberately exposed"
    )
    assert plan["authority"]["paid_api_calls"] == 0
    assert plan["authority"]["sealed_swe_bench_holdout_agents_opened"] == 0


def test_hindsight_summary_binds_exact_capacity_result() -> None:
    path = (
        REPOSITORY_ROOT
        / "examples"
        / "multi_swe_research"
        / "evidence"
        / "hindsight-summary.json"
    )
    summary = json.loads(path.read_text(encoding="utf-8"))
    digest = summary.pop("hindsight_summary_digest")

    assert canonical_digest(summary) == digest
    assert summary["identities"]["hindsight_plan_digest"] == (
        load_hindsight_plan()["hindsight_plan_digest"]
    )
    assert summary["solver_evidence"]["certified_optimum_count"] == 328
    assert summary["results"]["h5"][
        "exact_hindsight_minus_full_history"
    ] == pytest.approx(-0.03263868522024368)
    assert summary["results"]["h10"][
        "exact_hindsight_minus_full_history"
    ] == pytest.approx(-0.025616170421681548)
    assert summary["decision"]["capacity_supported"] is True
    assert summary["decision"]["predictive_selector_nominated"] is False
    assert summary["resource_use"]["paid_api_calls"] == 0


def test_hindsight_summary_rejects_resigned_source_dimension_drift() -> None:
    plan = load_hindsight_plan()
    source = plan["source"]
    horizon = {
        "membership_digest": "membership",
        "solver_rows": {
            "origin": {
                "success": True,
                "status": 0,
                "mip_gap": 0.0,
                "mip_node_count": 0,
                "objective_error": 0.0,
            }
        },
        "solver_summary": {
            "response_pattern_count": {
                "minimum": 2,
                "median": 2.0,
                "maximum": 2,
            }
        },
        "exact_hindsight": {
            view: {
                "repository_count": 1,
                "origin_count": 1,
                "macro_repository_loss": 0.1,
                "macro_repository_baseline_loss": 0.2,
                "macro_repository_difference": -0.1,
                "favorable_repository_count": 1,
            }
            for view in ("wide", "deep")
        },
    }
    result = {
        "schema_version": "barcarolle_multi_swe_hindsight_results_v1",
        "study_id": plan["study_id"],
        "epistemic_status": plan["epistemic_status"],
        "hindsight_plan_digest": plan["hindsight_plan_digest"],
        "selector_plan_digest": source["selector_plan_digest"],
        "task_space_results_digest": source["task_space_results_digest"],
        "outcome_results_digest": source["outcome_results_digest"],
        "task_count": 2,
        "configuration_count": 36,
        "origin_count": 2,
        "horizons": {"5": horizon, "10": horizon},
        "capacity_decision": {
            "all_requirements_met": True,
            "decision": "capacity",
            "interpretation": "fixture",
        },
        "nomination": {
            "selector_nominated": False,
            "independent_confirmation_authorized": False,
            "production_promotion_allowed": False,
        },
        "resource_use": {
            "paid_api_calls": 0,
            "embedding_api_calls": 0,
            "sealed_swe_bench_holdout_agents_opened": 0,
        },
        "claim_boundary": "fixture boundary",
    }
    result["hindsight_results_digest"] = canonical_digest(result)

    with pytest.raises(ValueError, match="source dimensions"):
        build_hindsight_evidence_summary(result, plan, dict(result))


def test_exact_hindsight_milp_recovers_zero_loss_response_mix() -> None:
    pytest.importorskip("scipy")
    outcomes = {
        "agent-a": {
            "a": 1,
            "b": 1,
            "c": 0,
            "d": 0,
            "future-a": 1,
            "future-b": 0,
        },
        "agent-b": {
            "a": 0,
            "b": 0,
            "c": 1,
            "d": 1,
            "future-a": 0,
            "future-b": 1,
        },
    }

    selected, solver = solve_exact_hindsight_subset(
        ("a", "b", "c", "d"),
        ("future-a", "future-b"),
        outcomes,
        ("agent-a", "agent-b"),
        budget=2,
    )

    assert len(selected) == len(set(selected)) == 2
    assert sum(outcomes["agent-a"][task_id] for task_id in selected) == 1
    assert sum(outcomes["agent-b"][task_id] for task_id in selected) == 1
    assert solver["status"] == 0
    assert solver["recomputed_objective"] == pytest.approx(0.0)


def test_normalizer_rejects_overlapping_terminal_partitions(
    tmp_path: Path,
) -> None:
    contract = _fixture_contract()
    root = _write_panel_fixture(tmp_path, contract)
    path = next(root.glob("evaluation/*/verified/*/results/results.json"))
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["empty_error_patch_ids"] = [payload["completed_ids"][0]]
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="terminal partitions overlap"):
        normalize_public_panel(contract, root)


def test_normalizer_preserves_terminal_failures_and_scalar_warnings(
    tmp_path: Path,
) -> None:
    contract = _fixture_contract()
    root = _write_panel_fixture(tmp_path, contract)

    summary, outcomes, tasks = normalize_public_panel(contract, root)

    assert summary["task_count"] == 4
    assert summary["configuration_count"] == 2
    assert len(summary["source_warnings"]) == 1
    assert len(outcomes) == 8
    assert len(tasks) == 4
    assert {
        row["terminal_state"]
        for row in outcomes
        if row["configuration_id"] == "20250101_Harness_Model-A"
    } == {"completed", "empty_error_patch", "incomplete"}


def test_time_projection_requires_exact_task_coverage() -> None:
    contract = _fixture_contract()
    tasks = (
        {
            "instance_id": "owner__repo-1",
            "language": "one",
            "repository": "owner/repo",
        },
        {
            "instance_id": "owner__repo-2",
            "language": "one",
            "repository": "owner/repo",
        },
        {
            "instance_id": "other__repo-3",
            "language": "two",
            "repository": "other/repo",
        },
        {
            "instance_id": "other__repo-4",
            "language": "two",
            "repository": "other/repo",
        },
    )

    def query(graphql: str) -> dict[str, object]:
        repository = "owner" if 'owner: \"owner\"' in graphql else "other"
        return {
            "data": {
                "repository": {
                    "p0": {"createdAt": "2020-01-01T00:00:00Z"},
                    "p1": {"createdAt": "2020-01-02T00:00:00Z"},
                }
            },
            "repository": repository,
        }

    summary, rows = project_task_times(
        contract,
        tasks,
        "2026-07-28T00:00:00Z",
        query=query,
        batch_size=2,
    )
    assert summary["task_count"] == 4
    assert len(rows) == 4
    assert rows[0]["created_at"].endswith("Z")


def test_cli_refuses_existing_time_output_before_external_reads(
    tmp_path: Path,
) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        main(
            (
                "project-times",
                "--task-universe",
                str(tmp_path / "missing.jsonl"),
                "--observed-at",
                "2026-07-28T00:00:00Z",
                "--output",
                str(output),
            )
        )


def test_task_identity_and_graphql_are_explicit() -> None:
    assert _task_identity("owner__repo-name-123") == ("owner/repo-name", 123)
    query, aliases = _graphql_query(
        "owner",
        "repo-name",
        (("owner__repo-name-123", 123),),
    )
    assert 'owner: "owner"' in query
    assert "p0: pullRequest(number: 123)" in query
    assert aliases == {"p0": ("owner__repo-name-123", 123)}


def test_issue_text_projection_uses_only_sorted_public_issue_fields() -> None:
    text, count, has_content = _project_issue_text(
        {
            "title": "excluded pull request title",
            "fix_patch": "excluded patch",
            "resolved_issues": [
                {"number": 9, "title": "Later", "body": "Second"},
                {"number": 3, "title": "Earlier", "body": "First"},
            ],
        }
    )

    assert count == 2
    assert has_content is True
    assert text == (
        "Issue #3\nEarlier\n\nFirst\n\n---\n\n"
        "Issue #9\nLater\n\nSecond"
    )
    assert "excluded" not in text


def test_issue_text_projection_stably_retains_duplicate_issue_numbers() -> None:
    text, count, has_content = _project_issue_text(
        {
            "resolved_issues": [
                {"number": 3, "title": "First copy", "body": ""},
                {"number": 3, "title": "Second copy", "body": ""},
            ]
        }
    )

    assert count == 2
    assert has_content is True
    assert text.index("First copy") < text.index("Second copy")


def test_content_projection_binds_git_bytes_and_exact_task_universe(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    rows = (
        {
            "instance_id": "owner__repo-1",
            "resolved_issues": [
                {"number": 1, "title": "One", "body": "Body one"}
            ],
        },
        {
            "instance_id": "owner__repo-2",
            "resolved_issues": [
                {"number": 2, "title": "Two", "body": "Body two"}
            ],
        },
    )
    dataset = source / "tasks.jsonl"
    dataset.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    subprocess.run(("git", "init", "-q", str(source)), check=True)
    subprocess.run(("git", "-C", str(source), "add", "tasks.jsonl"), check=True)
    subprocess.run(
        (
            "git",
            "-C",
            str(source),
            "-c",
            "user.name=Barcarolle Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ),
        check=True,
    )
    revision = subprocess.run(
        ("git", "-C", str(source), "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    contract = {
        "study_id": "content-fixture",
        "contract_digest": "fixture",
        "dataset": {
            "revision": revision,
            "paths": ["tasks.jsonl"],
            "declared_path_bytes": dataset.stat().st_size,
        },
    }
    tasks = (
        {
            "instance_id": "owner__repo-1",
            "language": "fixture",
            "repository": "owner/repo",
        },
        {
            "instance_id": "owner__repo-2",
            "language": "fixture",
            "repository": "owner/repo",
        },
    )

    summary, projected = project_task_content(contract, tasks, source)

    assert summary["task_count"] == 2
    assert summary["source_file_count"] == 1
    assert summary["nonempty_fraction"] == 1.0
    assert tuple(row["instance_id"] for row in projected) == (
        "owner__repo-1",
        "owner__repo-2",
    )
    assert all("fix_patch" not in row["text"] for row in projected)


def test_embedding_artifact_binds_plan_content_and_vectors(
    tmp_path: Path,
) -> None:
    plan = load_selector_plan()
    task_ids = ("task-a", "task-b")
    texts = ("alpha", "beta")
    content_manifest = {
        "content_manifest_digest": "content",
        "task_text_digest": canonical_digest(
            tuple(zip(task_ids, texts, strict=True))
        ),
    }
    artifact = build_embedding_artifact(
        task_ids,
        texts,
        ((1.0, 0.0), (0.0, 1.0)),
        plan=plan,
        content_manifest=content_manifest,
        package_version="5.1.2",
    )
    path = tmp_path / "embeddings.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")

    vectors, manifest = load_embedding_artifact(
        path,
        plan,
        content_manifest,
        task_ids,
    )

    assert vectors == {"task-a": (1.0, 0.0), "task-b": (0.0, 1.0)}
    assert manifest["vector_values_digest"] == artifact["vector_values_digest"]
    assert (
        manifest["embedding_artifact_digest"]
        == artifact["embedding_artifact_digest"]
    )
    committed = load_embedding_manifest()
    assert (
        committed["embedding_artifact_digest"]
        == "cc6f791d2770f1e265240e73e47ccd517ed6bae26b1ed3abc78d17cad14e8a23"
    )


def test_alg_007_control_matches_the_previously_frozen_implementation() -> None:
    task_ids = ("a", "b", "c", "d", "e", "f")
    vectors = {
        "a": (1.0, 0.0),
        "b": (0.8, 0.6),
        "c": (0.6, 0.8),
        "d": (0.0, 1.0),
        "e": (-0.6, 0.8),
        "f": (-0.8, 0.6),
    }

    selected = select_kernel_mean_herding(
        task_ids,
        task_ids[-min(15, len(task_ids)) :],
        SimilarityIndex(vectors),
        budget=3,
        swap_pass_limit=20,
    )

    assert selected == select_centroid_recent(
        task_ids,
        vectors,
        recent_window=15,
        budget=3,
    )


def test_alg_012_is_deterministic_and_accepts_no_agent_outcomes() -> None:
    task_ids = ("a", "b", "c", "d")
    vectors = {
        "a": (1.0, 0.0),
        "b": (0.0, 1.0),
        "c": (-1.0, 0.0),
        "d": (0.0, -1.0),
    }
    index = SimilarityIndex(vectors)

    first = select_minimax_temporal_semantic_herding(
        task_ids,
        index,
        horizon=2,
        budget=2,
    )
    second = select_minimax_temporal_semantic_herding(
        task_ids,
        SimilarityIndex(vectors),
        horizon=2,
        budget=2,
    )

    assert first == second
    assert len(first) == len(set(first)) == 2
    assert "outcomes" not in inspect.signature(
        select_minimax_temporal_semantic_herding
    ).parameters
    assert kernel_mmd_squared(first, first, index) == pytest.approx(0.0)


def test_sparse_public_outcomes_expand_to_the_exact_binary_panel() -> None:
    evidence = (
        REPOSITORY_ROOT / "examples" / "multi_swe_research" / "evidence"
    )
    task_ids = tuple(
        json.loads(line)["instance_id"]
        for line in (evidence / "task-universe.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    outcomes, metadata, diagnostics = load_public_outcomes(
        evidence / "panel-summary.json",
        evidence / "resolved-outcomes.jsonl",
        task_ids,
        load_selector_plan(),
    )

    assert len(metadata) == 36
    assert diagnostics["resolved_cell_count"] == 2913
    assert all(set(values) == set(task_ids) for values in outcomes.values())
    assert sum(sum(values.values()) for values in outcomes.values()) == 2913


def test_outcome_loss_uses_full_history_as_an_uncompressed_baseline() -> None:
    outcomes = {
        "agent-a": {"a": 1, "b": 0, "c": 1},
        "agent-b": {"a": 0, "b": 0, "c": 1},
    }

    loss = outcome_pass_rate_mae(
        ("a", "b"),
        ("c",),
        outcomes,
        ("agent-a", "agent-b"),
    )

    assert loss == pytest.approx(0.75)


def test_outcome_coverage_rejects_missing_id_even_with_extra_id() -> None:
    outcomes = {
        "agent": {
            "history": 1,
            "unrelated": 0,
        }
    }

    with pytest.raises(ValueError, match="does not cover"):
        outcome_pass_rate_mae(
            ("history",),
            ("missing-future",),
            outcomes,
            ("agent",),
        )

    pytest.importorskip("scipy")
    with pytest.raises(ValueError, match="cover"):
        solve_exact_hindsight_subset(
            ("history",),
            ("missing-future",),
            outcomes,
            ("agent",),
            budget=1,
        )


def _fixture_contract() -> dict[str, object]:
    configurations = (
        "20250101_Harness_Model-A",
        "20250101_Harness_Model-B",
    )
    language_ids = {
        "one": ("owner__repo-1", "owner__repo-2"),
        "two": ("other__repo-3", "other__repo-4"),
    }
    all_ids = tuple(sorted(item for values in language_ids.values() for item in values))
    contract: dict[str, object] = {
        "schema_version": "barcarolle_multi_swe_research_contract_v1",
        "study_id": "fixture",
        "dataset": {
            "task_count": 4,
            "task_id_line_digest": _line_digest(all_ids),
            "paths": [f"path-{index}" for index in range(39)],
            "path_list_sha256": _line_digest(
                f"path-{index}" for index in range(39)
            ),
        },
        "results": {
            "split": "verified",
            "configurations": list(configurations),
            "configuration_list_sha256": _line_digest(configurations),
            "languages": [
                {
                    "dataset_directory": language,
                    "result_directory": language,
                    "task_count": len(ids),
                    "task_id_line_digest": _line_digest(ids),
                }
                for language, ids in language_ids.items()
            ],
        },
        "time_projection": {
            "evidence": "github_graphql_pull_request_created_at"
        },
    }
    contract["contract_digest"] = canonical_digest(contract)
    return contract


def _write_panel_fixture(
    root: Path,
    contract: dict[str, object],
) -> Path:
    configurations = contract["results"]["configurations"]
    language_ids = {
        "one": ("owner__repo-1", "owner__repo-2"),
        "two": ("other__repo-3", "other__repo-4"),
    }
    for configuration_index, configuration in enumerate(configurations):
        for language, ids in language_ids.items():
            result_dir = (
                root
                / "evaluation"
                / language
                / "verified"
                / configuration
                / "results"
            )
            result_dir.mkdir(parents=True)
            (result_dir.parent / "metadata.yaml").write_text(
                "name: fixture\nverified: true\n",
                encoding="utf-8",
            )
            completed = [ids[configuration_index]]
            payload = {
                "total_instances": (
                    len(ids) - 1
                    if configuration_index == 0 and language == "one"
                    else len(ids)
                ),
                "completed_ids": completed,
                "empty_error_patch_ids": (
                    [ids[1]]
                    if configuration_index == 0 and language == "one"
                    else []
                ),
                "incomplete_ids": (
                    [ids[1]]
                    if configuration_index == 0 and language == "two"
                    else ([ids[0]] if configuration_index == 1 else [])
                ),
                "resolved": completed,
            }
            (result_dir / "results.json").write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
    return root
