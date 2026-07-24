from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import cast

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from examples.pylint_swe_bench_verified import pilot  # noqa: E402


def _dependency_evidence(changed_path: str):
    patch_text = (
        f"diff --git a/{changed_path} b/{changed_path}\n"
        f"--- a/{changed_path}\n"
        f"+++ b/{changed_path}\n"
    )
    patch = pilot.CapturedDiff(
        diff_text=patch_text,
        diff_digest=hashlib.sha256(patch_text.encode("utf-8")).hexdigest(),
    )
    return pilot.build_dependency_evidence(
        pilot.REPOSITORY_ID,
        {"source-event": patch},
    )


def _unbound_task_pool():
    return pilot.record_with_digest(
        pilot.TaskPoolRecord(
            task_pool_id="task-pool",
            task_pool_digest="",
            repository_id=pilot.REPOSITORY_ID,
            task_ids=("task",),
            check_ids=("check",),
            task_records_ref="records/tasks.jsonl",
            task_records_digest="tasks",
            check_records_ref="records/checks.jsonl",
            check_records_digest="checks",
            certification_evidence_ref="records/certification-evidence.jsonl",
            source_event_records_ref="records/source-events.jsonl",
            source_event_records_digest="source-events",
            rejected_candidate_ids=(),
            rejection_summary_digest="rejections",
            certification_evidence_digest="certification",
            generation_provenance_ref=None,
            generation_provenance_digest=None,
            generator_config_digest=None,
            source_protocol_digest=None,
            certification_config_digest="certification-config",
            created_at="2026-07-17T00:00:02.000000Z",
        )
    )


def _certification_status_by_candidate_id():
    return {
        "candidate": {
            "base_check": {"state": "scored"},
            "reference_patch_check": {"state": "scored"},
        }
    }


def test_fixed_task_sources_replace_the_uncertifiable_verified_instance() -> None:
    configured = pilot._task_source_by_instance()

    assert len(configured) == 10
    assert "pylint-dev__pylint-8898" not in configured
    assert configured["pylint-dev__pylint-5859"]["dataset_family"] == ("swe_bench_lite")


def test_candidate_separates_task_source_time_from_check_time(
    tmp_path: Path,
) -> None:
    instance_id = "pylint-dev__pylint-4551"
    bundle = tmp_path / "hidden-checks" / instance_id
    bundle.mkdir(parents=True)
    (bundle / "spec.json").write_text("{}", encoding="utf-8")
    paths = pilot.PilotPaths(
        output_dir=tmp_path,
        target_repo=tmp_path / "target",
        dataset=tmp_path / "dataset",
        supplemental_dataset=tmp_path / "supplemental-dataset",
        harness_python=tmp_path / "python",
    )

    candidate = pilot._candidate(
        paths,
        {
            "instance_id": instance_id,
            "base_commit": "a" * 40,
            "problem_statement": "Fix the bug.",
            "difficulty": "<15 min fix",
        },
        {
            "instance_id": instance_id,
            "issue_url": "https://example.invalid/issues/1",
            "task_material_available_at": "2021-01-01T00:00:00Z",
            "check_material_available_at": "2021-02-01T00:00:00Z",
            "image_digest": f"sha256:{'b' * 64}",
        },
        dependency_cluster_id="dependency-cluster-test",
    )

    assert candidate.source_resolved_at == "2021-01-01T00:00:00Z"
    assert candidate.task_material_available_at == "2021-01-01T00:00:00Z"
    assert candidate.check_material_available_at == "2021-02-01T00:00:00Z"
    assert candidate.dependency_cluster_id == "dependency-cluster-test"


def test_candidate_check_identity_ignores_local_execution_paths(
    tmp_path: Path,
) -> None:
    instance_id = "pylint-dev__pylint-4551"
    configured = pilot._task_source_by_instance()[instance_id]
    source = {
        "instance_id": instance_id,
        "base_commit": "a" * 40,
        "problem_statement": "Fix the bug.",
        "difficulty": "<15 min fix",
    }
    paths = tuple(
        pilot.PilotPaths(
            output_dir=tmp_path / name,
            target_repo=tmp_path / name / "target",
            dataset=tmp_path / name / "dataset",
            supplemental_dataset=tmp_path / name / "supplemental-dataset",
            harness_python=tmp_path / name / "harness-env/bin/python",
        )
        for name in ("first-run", "second-run")
    )
    for item in paths:
        bundle = item.output_dir / "hidden-checks" / instance_id
        bundle.mkdir(parents=True)
        (bundle / "spec.json").write_text("{}", encoding="utf-8")

    commands = tuple(pilot._check_command(item, configured) for item in paths)
    candidates = tuple(
        pilot._candidate(
            item,
            source,
            configured,
            dependency_cluster_id="dependency-cluster-test",
        )
        for item in paths
    )

    assert commands[0] != commands[1]
    assert candidates[0].check_manifest_digest == candidates[1].check_manifest_digest
    assert (
        pilot.build_check_candidate(candidates[0]).check_id
        == pilot.build_check_candidate(candidates[1]).check_id
    )


def test_check_binding_keeps_existing_paid_command_identity(tmp_path: Path) -> None:
    instance_id = "pylint-dev__pylint-4551"
    configured = pilot._task_source_by_instance()[instance_id]
    paths = pilot.PilotPaths(
        output_dir=tmp_path,
        target_repo=tmp_path / "target",
        dataset=tmp_path / "dataset",
        supplemental_dataset=tmp_path / "supplemental-dataset",
        harness_python=tmp_path / "harness-env/bin/python",
    )
    bundle = paths.output_dir / "hidden-checks" / instance_id
    bundle.mkdir(parents=True)
    (bundle / "spec.json").write_text("{}", encoding="utf-8")
    candidate = pilot._candidate(
        paths,
        {
            "instance_id": instance_id,
            "base_commit": "a" * 40,
            "problem_statement": "Fix the bug.",
            "difficulty": "<15 min fix",
        },
        configured,
        dependency_cluster_id="dependency-cluster-test",
    )
    command = pilot._check_command(paths, configured)
    existing_candidate = replace(
        candidate,
        check_manifest_digest=pilot.canonical_digest({"check_command": command}),
    )

    pilot._bind_check(
        pilot.WorkspaceRunContext(),
        paths,
        pilot.build_check_candidate(existing_candidate),
        configured,
    )


def test_dependency_evidence_is_bound_as_run_specific_adapter_evidence() -> None:
    task_pool = _unbound_task_pool()
    first = _dependency_evidence("first.py")
    second = _dependency_evidence("second.py")

    first_pool, first_manifest, first_adapter = (
        pilot._bind_dependency_generation_provenance(
            task_pool,
            first,
            _certification_status_by_candidate_id(),
            prepared_candidate_records_digest="candidates",
            input_snapshot_digest="inputs",
            started_at="2026-07-17T00:00:00.000000Z",
            finished_at="2026-07-17T00:00:01.000000Z",
        )
    )
    second_pool, second_manifest, second_adapter = (
        pilot._bind_dependency_generation_provenance(
            task_pool,
            second,
            _certification_status_by_candidate_id(),
            prepared_candidate_records_digest="candidates",
            input_snapshot_digest="inputs",
            started_at="2026-07-17T00:00:00.000000Z",
            finished_at="2026-07-17T00:00:01.000000Z",
        )
    )

    assert first_pool.generator_config_digest == (
        first_manifest.generator_behavior_digest
    )
    assert first_manifest.generator_behavior_digest == (
        second_manifest.generator_behavior_digest
    )
    assert first_manifest.outputs["adapter_evidence_digest"] == (
        pilot.canonical_digest(first_adapter)
    )
    assert pilot.dependency_evidence_from_mapping(
        first_adapter["dependency_evidence"]
    ) == first
    assert set(first_adapter["certification_status_by_candidate_id"]) == {
        "candidate"
    }
    assert first_manifest.outputs["adapter_evidence_digest"] != (
        second_manifest.outputs["adapter_evidence_digest"]
    )
    assert first_pool.generation_provenance_digest != (
        second_pool.generation_provenance_digest
    )
    assert first_pool.task_pool_id != second_pool.task_pool_id
    unidentified_pool = replace(
        first_pool,
        task_pool_id="",
        task_pool_digest="",
    )
    assert first_pool.task_pool_id == (
        f"task_pool_{pilot.canonical_digest(unidentified_pool)}"
    )


def test_build_context_rejects_invalid_complete_task_pool_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = pilot.PilotPaths(
        output_dir=tmp_path,
        target_repo=tmp_path / "target",
        dataset=tmp_path / "dataset",
        supplemental_dataset=tmp_path / "supplemental-dataset",
        harness_python=tmp_path / "harness-env/bin/python",
    )
    monkeypatch.setattr(pilot, "_require_harness_revision", lambda *_: None)

    def reject_bundle(manifest_path: Path):
        assert manifest_path == tmp_path / "records/task-pool.jsonl"
        raise ValueError("adapter evidence digest does not match content")

    monkeypatch.setattr(pilot, "open_task_pool_bundle", reject_bundle)

    with pytest.raises(
        RuntimeError,
        match="prepared Task Pool bundle is invalid: adapter evidence digest",
    ):
        pilot.build_context(paths)


def test_certification_counts_require_base_negative_and_reference_positive() -> None:
    base = {
        "tests": {
            "FAIL_TO_PASS": {"success_count": 0, "failure_count": 3},
            "PASS_TO_PASS": {"success_count": 5, "failure_count": 0},
        }
    }
    reference = {
        "tests": {
            "FAIL_TO_PASS": {"success_count": 3, "failure_count": 0},
            "PASS_TO_PASS": {"success_count": 5, "failure_count": 0},
        }
    }

    pilot._require_test_counts(base, 3, 5, reference=False)
    pilot._require_test_counts(reference, 3, 5, reference=True)

    with pytest.raises(RuntimeError, match="test counts differ"):
        pilot._require_test_counts(reference, 3, 5, reference=False)


def test_started_cell_without_exact_result_is_never_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_path = tmp_path / "resource-ledger.json"
    pilot._write_json(ledger_path, pilot._new_ledger())
    pilot._append_ledger_event(
        pilot._ledger_events_path(ledger_path),
        {
            "event_type": "reservation",
            "recorded_at": "2026-07-17T00:00:00Z",
            "call_id": "cell-01",
            "state": "started",
        },
    )
    context = cast(pilot.PilotContext, SimpleNamespace(ledger_path=ledger_path))
    monkeypatch.setattr(pilot, "_exact_result_for_call", lambda *_: None)

    with pytest.raises(RuntimeError, match="automatic retry is forbidden"):
        pilot._reconcile_ledger(context)


def test_started_cell_recovers_an_exact_scoreable_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_path = tmp_path / "resource-ledger.json"
    pilot._write_json(ledger_path, pilot._new_ledger())
    pilot._append_ledger_event(
        pilot._ledger_events_path(ledger_path),
        {
            "event_type": "reservation",
            "recorded_at": "2026-07-17T00:00:00Z",
            "call_id": "cell-01",
            "state": "started",
        },
    )
    result = SimpleNamespace(
        result_id="result-1",
        result_digest="digest-1",
        terminal_status="failed",
        scoreable_state="scoreable",
        outcome="fail",
        usage={
            "input_tokens": 10,
            "uncached_input_tokens": 8,
            "cached_input_tokens": 2,
            "output_tokens": 3,
        },
        cost={"total_cost": 0.01},
        pricing_version=pilot.PRICING_VERSION,
    )
    context = cast(pilot.PilotContext, SimpleNamespace(ledger_path=ledger_path))
    monkeypatch.setattr(pilot, "_exact_result_for_call", lambda *_: result)
    monkeypatch.setattr(pilot, "_paid_result_count", lambda _: 1)

    ledger = pilot._reconcile_ledger(context)

    calls = ledger["calls"]
    assert isinstance(calls, list)
    assert len(calls) == 1
    assert calls[0] == {
        **calls[0],
        "call_id": "cell-01",
        "state": "completed",
        "recovered_after_interruption": True,
        "result_id": "result-1",
        "result_digest": "digest-1",
        "terminal_status": "failed",
        "scoreable_state": "scoreable",
        "outcome": "fail",
        "usage": {
            "uncached_input_tokens": 8,
            "cached_input_tokens": 2,
            "output_tokens": 3,
        },
        "estimated_cost_usd": 0.01,
        "pricing_version": pilot.PRICING_VERSION,
    }


def test_paid_results_include_only_the_exact_pilot_execution_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = SimpleNamespace(
        agent_id="agent-low",
        task_id="task-1",
        check_id="check-1",
        cache_identity=SimpleNamespace(identity_digest="expected-identity"),
    )
    unrelated = SimpleNamespace(
        agent_id="agent-low",
        task_id="task-1",
        check_id="check-1",
        cache_identity=SimpleNamespace(identity_digest="other-runtime-identity"),
    )
    context = cast(
        pilot.PilotContext,
        SimpleNamespace(
            agents=(SimpleNamespace(agent_id="agent-low"),),
            tasks=(SimpleNamespace(task_id="task-1", check_ids=("check-1",)),),
            checks={"check-1": SimpleNamespace(check_id="check-1")},
            workspace_config=object(),
            runtime_config=object(),
            result_store=object(),
        ),
    )
    monkeypatch.setattr(
        pilot,
        "compute_result_cache_identity",
        lambda *_: SimpleNamespace(identity_digest="expected-identity"),
    )
    monkeypatch.setattr(pilot, "load_results", lambda *_: (expected, unrelated))

    assert pilot._paid_results(context) == (expected,)


def test_pilot_summary_complete_requires_a_completed_resource_ledger() -> None:
    results = cast(
        tuple[pilot.ResultRecord, ...],
        tuple(object() for _ in range(pilot.MAXIMUM_PAID_CALLS)),
    )
    completed_calls = tuple(
        {"state": "completed"} for _ in range(pilot.MAXIMUM_PAID_CALLS)
    )

    assert pilot._pilot_summary_stage(results, completed_calls) == "complete"
    assert pilot._pilot_summary_stage(results, completed_calls[:-1]) == "incomplete"
    assert (
        pilot._pilot_summary_stage(
            results,
            (*completed_calls[:-1], {"state": "stopped"}),
        )
        == "incomplete"
    )


def test_pilot_cli_only_exposes_single_cell_paid_stages() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "examples/pylint_swe_bench_verified/pilot.py",
            "--help",
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    assert "at most one cell" in completed.stdout
    assert "--canary" in completed.stdout
    assert "--next-cell" in completed.stdout
    assert "--all" not in completed.stdout


def test_paid_check_rejects_a_stale_summary(tmp_path: Path) -> None:
    instance_id = "pylint-dev__pylint-4551"
    task_id = "task-1"
    diff_digest = "a" * 64
    summary_path = tmp_path / "raw/checks" / instance_id / diff_digest / "summary.json"
    summary_path.parent.mkdir(parents=True)
    summary_path.write_text(
        json.dumps(
            {
                "state": "scored",
                "instance_id": instance_id,
                "patch_digest": diff_digest,
                "resolved": False,
            }
        ),
        encoding="utf-8",
    )
    os.utime(summary_path, (1_577_836_800, 1_577_836_800))
    context = cast(
        pilot.PilotContext,
        SimpleNamespace(
            instance_by_task_id={task_id: instance_id},
            paths=SimpleNamespace(output_dir=tmp_path),
        ),
    )
    task = SimpleNamespace(task_id=task_id)
    workspace_run = SimpleNamespace(
        diff_digest=diff_digest,
        started_at="2026-07-17T00:00:00Z",
        check_outcome="fail",
    )

    with pytest.raises(RuntimeError, match="summary is stale"):
        pilot._require_paid_check_summary(context, task, workspace_run)  # type: ignore[arg-type]


def test_pilot_resource_ledger_pins_authorized_limits_and_official_rates() -> None:
    ledger = pilot._new_ledger()

    assert ledger["authorization"] == {
        "approved_at": "2026-07-17",
        "budget_usd": 30.0,
        "credential_variables": ["OPENAI_API_KEY", "OPENAI_BASE_URL"],
        "scope": "fixed 10-task x low/high SWE-bench Pylint pilot",
    }
    assert ledger["limits"] == {
        "maximum_estimated_cost_usd": 30.0,
        "maximum_paid_calls": 20,
        "retry_policy": {
            "cell_retries": 0,
            "codex_request_retries": "default",
            "codex_stream_retries": "default",
        },
    }
    pricing = cast(dict[str, object], ledger["pricing"])
    models = cast(dict[str, object], pricing["models"])
    rates = cast(dict[str, float], models["gpt-5.4-mini"])
    assert rates == {
        "input_usd_per_token": 0.75 / 1_000_000,
        "cached_input_usd_per_token": 0.075 / 1_000_000,
        "output_usd_per_token": 4.5 / 1_000_000,
    }
    assert json.dumps(ledger)
