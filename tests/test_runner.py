from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from threading import Barrier, Event, Lock
import hashlib
import json
import os
import subprocess
import sys
from typing import Any

import pytest

from barcarolle import runner as runner_module
from barcarolle import task_pool as task_pool_module
from barcarolle.cli import main as cli_main
from barcarolle.records import (
    AgentRecord,
    BenchmarkSelectionRecord,
    CheckRecord,
    EvaluationCellSet,
    FeatureSnapshotRecord,
    GenerationProvenanceManifest,
    MetricRecord,
    ObservedFrameEventRecord,
    PreparedCandidateMaterialRecord,
    PreparedCandidatePackageManifest,
    ResultCellRef,
    ResultImportDecision,
    ResultImportReceipt,
    ResultMatrix,
    ResultRecord,
    ResultSourceManifest,
    RollingOriginRecord,
    RuntimeConfig,
    SourceEventRecord,
    SelectorInput,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
    canonical_json,
    format_utc_timestamp,
    load_jsonl_records,
    make_feature_snapshot_id,
    make_rolling_origin_id,
    make_rolling_origin_policy_digest,
    make_result_id,
    make_selector_input_id,
    make_source_event_id,
    make_solver_material_digest,
    parse_utc_timestamp,
    record_with_digest,
    task_check_ref_key,
    write_jsonl_records,
)
from barcarolle.result_store import (
    ResultCacheConfig,
    ResultJoinConfig,
    ResultQuery,
    ResultStore,
    ScoringConfig,
    build_result_record,
    compute_result_cache_identity,
    load_results,
    store_result,
)
from barcarolle.runner import (
    ReportConfig,
    TaskPoolConfig,
    build_task_pool,
    build_task_pool_from_package,
    evaluate_selector,
    evaluate_selectors,
    fill_results,
    import_result_bundle,
    prepare_evaluation_cells,
    run_agents,
    score_selection,
    select_benchmark,
    train_selector,
    write_report,
)
from barcarolle.selection import (
    FeatureConfig,
    RollingOriginPolicy,
    SelectionBudget,
    SelectorEvaluationConfig,
    build_rule_selector,
)
from barcarolle.verification import VERIFICATION_ADAPTER_DIGEST, hidden_material_digest
from barcarolle.task_pool import TaskSourceConfig, TimeRange
from barcarolle.workspace import CapturedDiff, WorkspaceRunContext


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("markdown_filename", "../report.md"),
        ("markdown_filename", "nested/report.md"),
        ("markdown_filename", "report.json"),
        ("json_filename", "/tmp/report.json"),
        ("json_filename", "report.md"),
        ("json_filename", "..\\report.json"),
    ),
)
def test_report_config_requires_direct_typed_output_filenames(
    tmp_path: Path,
    field_name: str,
    value: str,
) -> None:
    config_type: Any = ReportConfig

    with pytest.raises(ValueError, match=field_name):
        config_type(output_dir=tmp_path, **{field_name: value})


@pytest.fixture(autouse=True)
def _stub_workspace_binding_preflight(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runner_module.workspace_module,
        "preflight_run_bindings",
        lambda run_context, plans, workspace_config, runtime_config: None,
    )


@pytest.mark.parametrize(
    ("config_name", "changes", "expected_error"),
    (
        (
            "workspace_config",
            {"workspace_config_id": 7},
            "workspace_config is invalid: "
            "WorkspaceConfig.workspace_config_id must be a string",
        ),
        (
            "runtime_config",
            {"runtime_config_id": 7},
            "runtime_config is invalid: "
            "RuntimeConfig.runtime_config_id must be a string",
        ),
    ),
)
def test_build_task_pool_validates_configs_before_candidate_resolution(
    tmp_path: Path,
    config_name: str,
    changes: dict[str, object],
    expected_error: str,
) -> None:
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    if config_name == "workspace_config":
        workspace_config = replace(workspace_config, **changes)
    else:
        runtime_config = replace(runtime_config, **changes)
    config = TaskPoolConfig(
        repository_id="repo",
        repository_path=tmp_path / "repository",
        artifact_root=tmp_path / "artifacts",
        workspace_config=workspace_config,
        runtime_config=runtime_config,
        reference_patches={},
        check_commands={},
        hidden_material_paths={},
        import_path=tmp_path / "must-not-be-read.jsonl",
    )

    with pytest.raises(ValueError, match=expected_error):
        build_task_pool(config)
    assert not config.artifact_root.exists()


def test_build_task_pool_accepts_semantic_manifest_and_writes_resolvable_records(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "--quiet")
    _git(repository, "config", "user.email", "tests@example.invalid")
    _git(repository, "config", "user.name", "Tests")
    (repository / "value.txt").write_text("broken\n", encoding="utf-8")
    _git(repository, "add", "value.txt")
    _git(repository, "commit", "--quiet", "-m", "base")
    base_commit = _git(repository, "rev-parse", "HEAD").stdout.strip()
    hidden_material = tmp_path / "private-check.txt"
    hidden_material.write_text("private\n", encoding="utf-8")
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "ok = Path('value.txt').read_text() == 'fixed\\n'; "
        "private = Path('.barcarolle/check_bundle').read_text() == 'private\\n'; "
        "raise SystemExit(0 if ok and private else 1)",
    )
    patch_text = (
        "diff --git a/value.txt b/value.txt\n"
        "--- a/value.txt\n"
        "+++ b/value.txt\n"
        "@@ -1 +1 @@\n"
        "-broken\n"
        "+fixed\n"
    )
    reference_patch = CapturedDiff(
        patch_text, hashlib.sha256(patch_text.encode()).hexdigest()
    )
    workspace_config = WorkspaceConfig(
        "workspace",
        canonical_digest({"repository": str(repository)}),
        "submodules",
        "image",
        "deps",
    )
    check_manifest = {"implementation": "test-check-v1"}
    candidate = _candidate_event(
        base_commit="HEAD",
        solver_material_refs=(),
        check_manifest_digest=canonical_digest(check_manifest),
        hidden_check_bundle_digest=hidden_material_digest(hidden_material),
    )
    config = TaskPoolConfig(
        repository_id="repo",
        repository_path=repository,
        artifact_root=tmp_path,
        workspace_config=workspace_config,
        runtime_config=_runtime_config(),
        reference_patches={"candidate": reference_patch},
        check_commands={"candidate": check_command},
        hidden_material_paths={"candidate": hidden_material},
        check_manifests={"candidate": check_manifest},
        time_range=TimeRange("2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"),
        task_source_config=TaskSourceConfig(
            "user_import",
            (
                candidate,
                {
                    "repository_id": "repo",
                    "source_family": "user_import",
                    "source_ref": "unmatured",
                    "source_resolved_at": "2026-01-15T00:00:00Z",
                    "task_material_available_at": "2026-01-16T00:00:00Z",
                },
            ),
        ),
        metadata={
            "created_at": "2026-02-01T00:00:00Z",
        },
    )

    task_pool = build_task_pool(config)
    task_ref = tmp_path / task_pool.task_records_ref
    check_ref = tmp_path / task_pool.check_records_ref
    evidence_ref = tmp_path / task_pool.certification_evidence_ref
    source_event_ref = tmp_path / task_pool.source_event_records_ref
    tasks = tuple(load_jsonl_records(task_ref, TaskRecord))
    checks = tuple(load_jsonl_records(check_ref, CheckRecord))
    source_events = tuple(load_jsonl_records(source_event_ref, SourceEventRecord))

    assert task_pool.task_ids == tuple(task.task_id for task in tasks)
    assert task_pool.check_ids == tuple(check.check_id for check in checks)
    assert task_pool.task_records_digest == canonical_digest(tasks)
    assert task_pool.check_records_digest == canonical_digest(checks)
    assert task_pool.rejected_candidate_ids == ()
    assert tasks[0].base_commit == base_commit
    assert task_pool.task_records_ref.startswith("task-pools/")
    assert (task_ref.parent / "task-pool.jsonl").exists()
    evidence = tuple(
        json.loads(line)
        for line in evidence_ref.read_text(encoding="utf-8").splitlines()
    )
    assert evidence[0]["accepted"] is True
    assert task_pool.certification_evidence_digest == canonical_digest(evidence)
    assert task_pool.source_event_records_digest == canonical_digest(source_events)
    assert task_pool.generator_config_digest is None
    assert task_pool.generation_provenance_ref is None
    assert task_pool.source_window_start == "2026-01-01T00:00:00.000000Z"
    assert task_pool.source_window_end == "2026-01-31T00:00:00.000000Z"
    source_events_by_ref = {event.source_ref: event for event in source_events}
    assert source_events_by_ref[candidate["source_ref"]].disposition == "accepted"
    assert source_events_by_ref["unmatured"].label_mature_at is None
    assert source_events_by_ref["unmatured"].rejection_reasons == (
        "check_material_unavailable",
    )


def test_build_task_pool_from_prepared_package_publishes_complete_provenance(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "--quiet")
    _git(repository, "config", "user.email", "tests@example.invalid")
    _git(repository, "config", "user.name", "Tests")
    (repository / "value.txt").write_text("broken\n", encoding="utf-8")
    _git(repository, "add", "value.txt")
    _git(repository, "commit", "--quiet", "-m", "base")
    base_commit = _git(repository, "rev-parse", "HEAD").stdout.strip()
    hidden_material = tmp_path / "private-check.txt"
    hidden_material.write_text("private\n", encoding="utf-8")
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "ok = Path('value.txt').read_text() == 'fixed\\n'; "
        "private = Path('.barcarolle/check_bundle').read_text() == 'private\\n'; "
        "raise SystemExit(0 if ok and private else 1)",
    )
    check_manifest = {"check_command": check_command}
    patch_text = (
        "diff --git a/value.txt b/value.txt\n"
        "--- a/value.txt\n"
        "+++ b/value.txt\n"
        "@@ -1 +1 @@\n"
        "-broken\n"
        "+fixed\n"
    )
    reference_patch = CapturedDiff(
        patch_text,
        hashlib.sha256(patch_text.encode("utf-8")).hexdigest(),
    )
    candidate = task_pool_module.TaskCandidate(
        candidate_id="candidate",
        repository_id="repo",
        base_commit=base_commit,
        source_family="issue",
        source_ref="issue-1",
        source_resolved_at="2026-01-10T00:00:00.000000Z",
        task_material_available_at="2026-01-11T00:00:00.000000Z",
        check_material_available_at="2026-01-12T00:00:00.000000Z",
        task_text="Fix the issue.",
        solver_material_refs=(),
        dependency_cluster_id="cluster",
        sampling_stratum="stratum",
        check_manifest_digest=canonical_digest(check_manifest),
        hidden_check_bundle_digest=hidden_material_digest(hidden_material),
        resource_limits={"timeout_seconds": 30},
        oracle_source="private",
        check_type="pytest",
    )
    package_manifest = _write_runner_prepared_package(
        tmp_path / "prepared",
        candidate,
        reference_patch,
        check_command,
        check_manifest,
        hidden_material,
    )
    package = task_pool_module.load_prepared_candidate_package(package_manifest)
    workspace_config = WorkspaceConfig(
        "workspace",
        canonical_digest({"repository": str(repository)}),
        "submodules",
        "image",
        "deps",
    )

    task_pool = build_task_pool_from_package(
        package,
        TaskPoolConfig(
            repository_id="repo",
            repository_path=repository,
            artifact_root=tmp_path / "published",
            workspace_config=workspace_config,
            runtime_config=_runtime_config(),
            reference_patches={},
            check_commands={},
            hidden_material_paths={},
            metadata={"created_at": "2026-02-01T00:00:00Z"},
        ),
    )
    bundle = task_pool_module.open_task_pool_bundle(
        tmp_path
        / "published"
        / Path(task_pool.task_records_ref).parent
        / "task-pool.jsonl"
    )

    assert bundle.task_pool == task_pool
    unidentified_pool = replace(
        task_pool,
        task_pool_id="",
        task_pool_digest="",
    )
    assert task_pool.task_pool_id == (
        f"task_pool_{canonical_digest(unidentified_pool)}"
    )
    assert bundle.generation_provenance is not None
    assert bundle.generation_provenance.generator_behavior_digest == (
        package.manifest.generator_behavior_digest
    )
    assert (
        bundle.generation_provenance.outputs["prepared_candidate_records_digest"]
        == package.manifest.candidate_records_digest
    )
    assert bundle.observed_frame_events == package.observed_frame_events
    assert bundle.adapter_evidence == package.adapter_evidence


def test_import_result_bundle_applies_import_time_floor_and_is_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    source_result = _redigest_result(
        _result(
            task,
            check,
            agent,
            workspace_config,
            runtime_config,
            _scoring_config(),
        ),
        source_result_available_at="2026-01-10T00:00:05.000000Z",
        result_available_at="2026-01-10T00:00:05.000000Z",
    )
    source_manifest = _write_result_source_bundle(
        tmp_path / "source",
        (source_result,),
        availability_semantics="import_time_floor_v1",
    )
    source_bytes = {
        path.name: path.read_bytes()
        for path in (source_manifest, source_manifest.parent / "results.jsonl")
    }
    store = ResultStore(tmp_path / "local" / "results.jsonl")
    receipt_path = tmp_path / "local" / "import-receipt.jsonl"
    bundle = _task_pool_bundle((task,), (check,))
    monkeypatch.setattr(
        runner_module,
        "_now",
        lambda: "2026-01-20T00:00:00Z",
    )

    receipt = import_result_bundle(
        source_manifest,
        bundle,
        (agent,),
        workspace_config,
        runtime_config,
        store,
        receipt_path,
        accepted_authority_digest="trusted-authority",
        availability_policy="import_time_floor_v1",
    )
    monkeypatch.setattr(
        runner_module,
        "_now",
        lambda: "2026-01-21T00:00:00Z",
    )
    resumed = import_result_bundle(
        source_manifest,
        bundle,
        (agent,),
        workspace_config,
        runtime_config,
        store,
        receipt_path,
        accepted_authority_digest="trusted-authority",
        availability_policy="import_time_floor_v1",
    )

    (imported,) = load_results(store, ResultQuery())
    assert resumed == receipt
    assert receipt.decisions[0].status == "admitted"
    assert imported.evidence_source_kind == "external_attested"
    assert imported.evidence_source_manifest_digest == receipt.source_manifest_digest
    assert imported.source_result_available_at == "2026-01-10T00:00:05.000000Z"
    assert imported.result_available_at == "2026-01-20T00:00:00.000000Z"
    assert imported.cache_identity == source_result.cache_identity
    assert runner_module.result_store_module.result_execution_digest(
        imported
    ) == runner_module.result_store_module.result_execution_digest(source_result)
    assert (
        load_results(
            store,
            ResultQuery(result_available_before="2026-01-15T00:00:00Z"),
        )
        == ()
    )
    (resolved,) = runner_module.result_store_module.resolve_result_cells(
        (TaskCheckRef(task.task_id, check.check_id),),
        (task,),
        {check.check_id: check},
        (agent,),
        workspace_config,
        runtime_config,
        store,
        ResultCacheConfig(),
    )
    assert resolved.result_id == imported.result_id
    assert {
        path.name: path.read_bytes()
        for path in (source_manifest, source_manifest.parent / "results.jsonl")
    } == source_bytes


def test_concurrent_result_imports_share_one_observation_and_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    source_manifest = _write_result_source_bundle(
        tmp_path / "source",
        (
            _result(
                task,
                check,
                agent,
                workspace_config,
                runtime_config,
                _scoring_config(),
            ),
        ),
        availability_semantics="import_time_floor_v1",
    )
    bundle = _task_pool_bundle((task,), (check,))
    store = ResultStore(tmp_path / "local" / "results.jsonl")
    receipt_path = tmp_path / "local" / "receipt.jsonl"
    start = Barrier(2)
    second_observation = Event()
    observation_lock = Lock()
    observation_count = 0

    def concurrent_now() -> str:
        nonlocal observation_count
        with observation_lock:
            observation_count += 1
            observation_number = observation_count
        if observation_number == 1:
            second_observation.wait(timeout=1)
            return "2026-01-20T00:00:00Z"
        second_observation.set()
        return "2026-01-21T00:00:00Z"

    monkeypatch.setattr(runner_module, "_now", concurrent_now)

    def run_import() -> ResultImportReceipt:
        start.wait()
        return import_result_bundle(
            source_manifest,
            bundle,
            (agent,),
            workspace_config,
            runtime_config,
            store,
            receipt_path,
            accepted_authority_digest="trusted-authority",
            availability_policy="import_time_floor_v1",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        receipts = tuple(executor.map(lambda _: run_import(), range(2)))

    assert receipts[0] == receipts[1]
    assert receipts[0].imported_at == "2026-01-20T00:00:00.000000Z"
    imported = tuple(load_results(store, ResultQuery()))
    assert len(imported) == 1
    assert imported[0].evidence_imported_at == receipts[0].imported_at


def test_import_result_bundle_rejects_ambiguous_incoming_executions_as_a_group(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    source_results = tuple(
        _redigest_result(
            _result(
                task,
                check,
                agent,
                workspace_config,
                runtime_config,
                _scoring_config(),
                outcome=outcome,
            ),
            source_result_available_at="2026-01-10T00:00:05.000000Z",
            result_available_at="2026-01-10T00:00:05.000000Z",
        )
        for outcome in ("pass", "fail")
    )
    source_manifest = _write_result_source_bundle(
        tmp_path / "source",
        source_results,
        availability_semantics="import_time_floor_v1",
    )
    store = ResultStore(tmp_path / "local" / "results.jsonl")
    monkeypatch.setattr(
        runner_module,
        "_now",
        lambda: "2026-01-20T00:00:00Z",
    )

    receipt = import_result_bundle(
        source_manifest,
        _task_pool_bundle((task,), (check,)),
        (agent,),
        workspace_config,
        runtime_config,
        store,
        tmp_path / "local" / "receipt.jsonl",
        accepted_authority_digest="trusted-authority",
        availability_policy="import_time_floor_v1",
    )

    assert {decision.status for decision in receipt.decisions} == {"rejected"}
    assert {decision.rejection_reasons for decision in receipt.decisions} == {
        ("ambiguous_incoming_execution",)
    }
    assert not store.path.exists()


def test_import_result_bundle_durably_publishes_and_replays_rejected_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    source_agent = _agent()
    accepted_agent = _agent("accepted-agent", "accepted-manifest")
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    source_manifest = _write_result_source_bundle(
        tmp_path / "source",
        (
            _result(
                task,
                check,
                source_agent,
                workspace_config,
                runtime_config,
                _scoring_config(),
            ),
        ),
        availability_semantics="import_time_floor_v1",
    )
    store = ResultStore(tmp_path / "store" / "results.jsonl")
    receipt_path = tmp_path / "receipts" / "receipt.jsonl"
    result_store_module = runner_module.result_store_module
    file_calls: list[Path] = []
    directory_calls: list[Path] = []
    original_fsync_directory = result_store_module._fsync_directory

    def track_file(path: Path) -> None:
        file_calls.append(path)
        with path.open("rb") as handle:
            os.fsync(handle.fileno())

    def track_directory(path: Path) -> None:
        directory_calls.append(path)
        original_fsync_directory(path)

    monkeypatch.setattr(runner_module, "_now", lambda: "2026-01-20T00:00:00Z")
    monkeypatch.setattr(
        result_store_module,
        "_fsync_file",
        track_file,
        raising=False,
    )
    monkeypatch.setattr(
        result_store_module,
        "_fsync_directory",
        track_directory,
    )

    receipt = import_result_bundle(
        source_manifest,
        _task_pool_bundle((task,), (check,)),
        (accepted_agent,),
        workspace_config,
        runtime_config,
        store,
        receipt_path,
        accepted_authority_digest="trusted-authority",
        availability_policy="import_time_floor_v1",
    )
    replayed = import_result_bundle(
        source_manifest,
        _task_pool_bundle((task,), (check,)),
        (accepted_agent,),
        workspace_config,
        runtime_config,
        store,
        receipt_path,
        accepted_authority_digest="trusted-authority",
        availability_policy="import_time_floor_v1",
    )

    assert replayed == receipt
    assert receipt.decisions[0].status == "rejected"
    assert not store.path.exists()
    assert file_calls == [receipt_path, receipt_path]
    assert directory_calls == [receipt_path.parent, receipt_path.parent]


def test_import_result_bundle_rejects_authority_before_local_writes(
    tmp_path: Path,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    source_result = _result(
        task,
        check,
        agent,
        _workspace_config(),
        _runtime_config(),
        _scoring_config(),
    )
    source_manifest = _write_result_source_bundle(
        tmp_path / "source",
        (source_result,),
        availability_semantics="import_time_floor_v1",
    )
    store = ResultStore(tmp_path / "local" / "results.jsonl")
    receipt_path = tmp_path / "local" / "receipt.jsonl"

    with pytest.raises(ValueError, match="authority is not accepted"):
        import_result_bundle(
            source_manifest,
            _task_pool_bundle((task,), (check,)),
            (agent,),
            _workspace_config(),
            _runtime_config(),
            store,
            receipt_path,
            accepted_authority_digest="other-authority",
            availability_policy="import_time_floor_v1",
        )

    assert not store.path.exists()
    assert not receipt_path.exists()


@pytest.mark.parametrize("receipt_kind", ("missing_decisions", "false_rejection"))
def test_import_result_bundle_replays_existing_receipt_decisions(
    tmp_path: Path,
    receipt_kind: str,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    source_result = _result(
        task,
        check,
        agent,
        workspace_config,
        runtime_config,
        _scoring_config(),
    )
    source_manifest_path = _write_result_source_bundle(
        tmp_path / "source",
        (source_result,),
        availability_semantics="import_time_floor_v1",
    )
    source_manifest = load_jsonl_records(
        source_manifest_path,
        ResultSourceManifest,
    )[0]
    bundle = _task_pool_bundle((task,), (check,))
    imported_at = "2026-01-20T00:00:00.000000Z"
    decisions = (
        ()
        if receipt_kind == "missing_decisions"
        else (
            ResultImportDecision(
                source_result_id=source_result.result_id,
                source_result_digest=source_result.result_digest,
                status="rejected",
                local_result_id=None,
                local_result_digest=None,
                rejection_reasons=("made_up_rejection",),
            ),
        )
    )
    receipt_identity = {
        "source_manifest_digest": source_manifest.manifest_digest,
        "target_task_pool_digest": bundle.task_pool.task_pool_digest,
        "imported_at": imported_at,
        "availability_policy": "import_time_floor_v1",
    }
    forged = record_with_digest(
        ResultImportReceipt(
            receipt_id=f"result_import_{canonical_digest(receipt_identity)}",
            source_manifest_digest=source_manifest.manifest_digest,
            source_result_records_digest=source_manifest.result_records_digest,
            target_task_pool_id=bundle.task_pool.task_pool_id,
            target_task_pool_digest=bundle.task_pool.task_pool_digest,
            accepted_authority_digest="trusted-authority",
            imported_at=imported_at,
            availability_policy="import_time_floor_v1",
            agent_record_digests=(canonical_digest(agent),),
            workspace_config_digest=canonical_digest(workspace_config),
            runtime_config_digest=canonical_digest(runtime_config),
            decisions=decisions,
            receipt_digest="",
        )
    )
    receipt_path = tmp_path / "local" / "receipt.jsonl"
    write_jsonl_records(receipt_path, (forged,))
    store = ResultStore(tmp_path / "local" / "results.jsonl")

    with pytest.raises(
        ValueError,
        match="receipt decisions do not (cover source Results|replay)",
    ):
        import_result_bundle(
            source_manifest_path,
            bundle,
            (agent,),
            workspace_config,
            runtime_config,
            store,
            receipt_path,
            accepted_authority_digest="trusted-authority",
            availability_policy="import_time_floor_v1",
        )

    assert not store.path.exists()


def test_import_result_bundle_rejects_clock_before_source_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    source_manifest = _write_result_source_bundle(
        tmp_path / "source",
        (
            _result(
                task,
                check,
                agent,
                workspace_config,
                runtime_config,
                _scoring_config(),
            ),
        ),
        availability_semantics="import_time_floor_v1",
    )
    store = ResultStore(tmp_path / "local" / "results.jsonl")
    receipt_path = tmp_path / "local" / "import-receipt.jsonl"
    monkeypatch.setattr(
        runner_module,
        "_now",
        lambda: "2026-01-09T23:59:59Z",
    )

    with pytest.raises(
        ValueError,
        match="import observation precedes source manifest creation",
    ):
        import_result_bundle(
            source_manifest,
            _task_pool_bundle((task,), (check,)),
            (agent,),
            workspace_config,
            runtime_config,
            store,
            receipt_path,
            accepted_authority_digest="trusted-authority",
            availability_policy="import_time_floor_v1",
        )

    assert not store.path.exists()
    assert not receipt_path.exists()


def test_import_result_bundle_rejects_hardlink_to_source_results(
    tmp_path: Path,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    source_manifest = _write_result_source_bundle(
        tmp_path / "source",
        (
            _result(
                task,
                check,
                agent,
                workspace_config,
                runtime_config,
                _scoring_config(),
            ),
        ),
        availability_semantics="import_time_floor_v1",
    )
    source_results = source_manifest.parent / "results.jsonl"
    source_bytes = source_results.read_bytes()
    aliased_store_path = tmp_path / "local" / "results.jsonl"
    aliased_store_path.parent.mkdir(parents=True)
    os.link(source_results, aliased_store_path)

    with pytest.raises(
        ValueError,
        match="local Result Store must not alias source Results",
    ):
        import_result_bundle(
            source_manifest,
            _task_pool_bundle((task,), (check,)),
            (agent,),
            workspace_config,
            runtime_config,
            ResultStore(aliased_store_path),
            tmp_path / "local" / "receipt.jsonl",
            accepted_authority_digest="trusted-authority",
            availability_policy="import_time_floor_v1",
        )

    assert source_results.read_bytes() == source_bytes


@pytest.mark.parametrize("write_kind", ("store", "receipt"))
def test_import_result_bundle_keeps_source_root_read_only(
    tmp_path: Path,
    write_kind: str,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    source_root = tmp_path / "source"
    source_manifest = _write_result_source_bundle(
        source_root,
        (
            _result(
                task,
                check,
                agent,
                workspace_config,
                runtime_config,
                _scoring_config(),
            ),
        ),
        availability_semantics="import_time_floor_v1",
    )
    store_path = (
        source_root / "local-results.jsonl"
        if write_kind == "store"
        else tmp_path / "local" / "results.jsonl"
    )
    receipt_path = (
        source_root / "receipt.jsonl"
        if write_kind == "receipt"
        else tmp_path / "local" / "receipt.jsonl"
    )

    with pytest.raises(ValueError, match="must be outside the Result source root"):
        import_result_bundle(
            source_manifest,
            _task_pool_bundle((task,), (check,)),
            (agent,),
            workspace_config,
            runtime_config,
            ResultStore(store_path),
            receipt_path,
            accepted_authority_digest="trusted-authority",
            availability_policy="import_time_floor_v1",
        )

    assert not store_path.exists()
    assert not receipt_path.exists()


def test_import_result_bundle_rejects_duplicate_source_result_ids(
    tmp_path: Path,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    source_result = _result(
        task,
        check,
        agent,
        workspace_config,
        runtime_config,
        _scoring_config(),
    )
    source_manifest = _write_result_source_bundle(
        tmp_path / "source",
        (source_result, source_result),
        availability_semantics="import_time_floor_v1",
    )
    store = ResultStore(tmp_path / "local" / "results.jsonl")

    with pytest.raises(ValueError, match="duplicate result IDs"):
        import_result_bundle(
            source_manifest,
            _task_pool_bundle((task,), (check,)),
            (agent,),
            workspace_config,
            runtime_config,
            store,
            tmp_path / "local" / "receipt.jsonl",
            accepted_authority_digest="trusted-authority",
            availability_policy="import_time_floor_v1",
        )

    assert not store.path.exists()


def test_import_result_bundle_preserves_explicit_historical_attestation_and_reports_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    monkeypatch.setattr(
        runner_module,
        "_now",
        lambda: "2026-01-20T00:00:00Z",
    )
    monkeypatch.setattr(
        runner_module.result_store_module,
        "_now",
        lambda: "2026-01-12T00:00:00Z",
    )
    source_result = _result(
        task,
        check,
        agent,
        workspace_config,
        runtime_config,
        _scoring_config(),
    )
    source_manifest = _write_result_source_bundle(
        tmp_path / "source",
        (source_result,),
        availability_semantics="producer_attested_historical_v1",
    )
    store = ResultStore(tmp_path / "local" / "results.jsonl")

    receipt = import_result_bundle(
        source_manifest,
        _task_pool_bundle((task,), (check,)),
        (agent,),
        workspace_config,
        runtime_config,
        store,
        tmp_path / "local" / "receipt.jsonl",
        accepted_authority_digest="trusted-authority",
        availability_policy="producer_attested_historical_v1",
    )

    (imported,) = load_results(store, ResultQuery())
    assert imported.evidence_imported_at == "2026-01-20T00:00:00.000000Z"
    assert imported.result_available_at == source_result.source_result_available_at
    assert load_results(
        store,
        ResultQuery(result_available_before="2026-01-15T00:00:00Z"),
    ) == (imported,)
    section = runner_module.reporting_module.build_result_report(
        (imported,),
        (agent,),
    )
    evidence = section.summary["result_evidence"]
    assert evidence["historical_attestation_execution_count"] == 1
    assert "not a Barcarolle observation-time claim" in evidence["notes"][0]
    assert section.source_digests["external_source_manifest_digests"] == (
        receipt.source_manifest_digest,
    )
    assert "result_evidence_provenance_summary" in section.supported_claims


def test_import_result_bundle_rejects_conflict_with_local_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    monkeypatch.setattr(
        runner_module,
        "_now",
        lambda: "2026-01-20T00:00:00Z",
    )
    existing = _result(
        task,
        check,
        agent,
        workspace_config,
        runtime_config,
        scoring_config,
        outcome="pass",
    )
    source_result = _result(
        task,
        check,
        agent,
        workspace_config,
        runtime_config,
        scoring_config,
        outcome="fail",
    )
    store = ResultStore(tmp_path / "local" / "results.jsonl")
    store_result(existing, store)
    source_manifest = _write_result_source_bundle(
        tmp_path / "source",
        (source_result,),
        availability_semantics="import_time_floor_v1",
    )

    receipt = import_result_bundle(
        source_manifest,
        _task_pool_bundle((task,), (check,)),
        (agent,),
        workspace_config,
        runtime_config,
        store,
        tmp_path / "local" / "receipt.jsonl",
        accepted_authority_digest="trusted-authority",
        availability_policy="import_time_floor_v1",
    )

    assert receipt.decisions[0].status == "rejected"
    assert receipt.decisions[0].rejection_reasons == ("ambiguous_local_execution",)
    assert load_results(store, ResultQuery()) == (existing,)


@pytest.mark.parametrize(
    ("missing_field", "message"),
    (
        ("reference_patches", "reference patch is missing"),
        ("check_commands", "check command is missing"),
        ("hidden_material_paths", "hidden check material is missing"),
    ),
)
def test_build_task_pool_preflights_candidate_resources_before_workspace_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    missing_field: str,
    message: str,
) -> None:
    monkeypatch.setattr(
        runner_module.workspace_module,
        "resolve_repository_commit",
        lambda repository_path, commit: "a" * 40,
    )

    def fail_if_bound(*args: object, **kwargs: object) -> None:
        raise AssertionError(
            "workspace binding must follow candidate resource preflight"
        )

    monkeypatch.setattr(
        runner_module.workspace_module,
        "bind_repository_source",
        fail_if_bound,
    )
    resources: dict[str, object] = {
        "reference_patches": {
            "candidate": CapturedDiff("", hashlib.sha256(b"").hexdigest())
        },
        "check_commands": {"candidate": ("true",)},
        "hidden_material_paths": {"candidate": tmp_path / "hidden-check"},
    }
    resources[missing_field] = {}
    config = TaskPoolConfig(
        repository_id="repo",
        repository_path=tmp_path / "repository",
        artifact_root=tmp_path / "artifacts",
        workspace_config=_workspace_config(),
        runtime_config=_runtime_config(),
        time_range=TimeRange("2026-01-01T00:00:00Z", "2026-01-31T00:00:00Z"),
        task_source_config=TaskSourceConfig(
            "user_import",
            (_candidate_event(solver_material_refs=()),),
        ),
        **resources,
    )

    with pytest.raises(ValueError, match=message):
        build_task_pool(config)


def test_fill_results_runs_only_missing_agent_task_check_cells(
    tmp_path: Path, monkeypatch
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    other_agent = _agent(agent_id="other-agent", manifest="other-manifest")
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    store = ResultStore(tmp_path / "results.jsonl")
    store_result(
        _result(task, check, agent, workspace_config, runtime_config, scoring_config),
        store,
    )
    task_pool_bundle = _task_pool_bundle((task,), (check,))
    selection, _ = _persist_replayable_selection(
        task_pool_bundle,
        TaskCheckRef(task.task_id, check.check_id),
        (agent, other_agent),
        store,
    )
    calls: list[str] = []

    def fake_run_agent_on_task(
        task_arg,
        check_arg,
        agent_arg,
        workspace_config_arg,
        runtime_config_arg,
        run_context_arg,
    ):
        calls.append(agent_arg.agent_id)
        return _workspace_run(task_arg, check_arg, agent_arg)

    monkeypatch.setattr(
        "barcarolle.runner.workspace_module.run_agent_on_task", fake_run_agent_on_task
    )

    cell_set = fill_results(
        selection,
        task_pool_bundle,
        (agent, other_agent),
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(),
        store,
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )

    assert calls == ("other-agent",) or calls == ["other-agent"]
    assert tuple(cell.agent_id for cell in cell_set.cells) == (
        "agent",
        "other-agent",
    )
    assert all(cell.cell_state == "result" for cell in cell_set.cells)
    assert {result.agent_id for result in load_results(store, ResultQuery())} == {
        "agent",
        "other-agent",
    }


@pytest.mark.parametrize("entrypoint", ("fill", "prepare"))
def test_lazy_result_entrypoints_require_persisted_selection_evidence_before_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entrypoint: str,
) -> None:
    task = _task()
    check = _check()
    bundle = _task_pool_bundle((task,), (check,))
    ref = TaskCheckRef(task.task_id, check.check_id)
    origin = _origin(bundle.task_pool, ref, ref)
    selection = record_with_digest(
        replace(
            _selection(bundle.task_pool, ref),
            origin_id=origin.origin_id,
            selection_digest="",
        )
    )
    store = ResultStore(tmp_path / "results.jsonl")
    calls: list[str] = []

    def fail_if_cache_opens(*args, **kwargs):
        calls.append("cache")
        raise AssertionError("cache must not open before Selection replay")

    monkeypatch.setattr(
        runner_module.result_store_module,
        "open_result_store_session",
        fail_if_cache_opens,
    )

    with pytest.raises(ValueError, match="persisted Selection log does not exist"):
        if entrypoint == "fill":
            fill_results(
                selection,
                bundle,
                (_agent(),),
                _workspace_config(),
                _runtime_config(),
                _scoring_config(),
                ResultCacheConfig(),
                store,
                ResultJoinConfig(),
                WorkspaceRunContext(),
            )
        else:
            prepare_evaluation_cells(
                selection,
                origin,
                bundle,
                (_agent(),),
                _workspace_config(),
                _runtime_config(),
                _scoring_config(),
                ResultCacheConfig(),
                store,
                ResultJoinConfig(),
                WorkspaceRunContext(),
            )

    assert calls == []
    assert not store.path.exists()


@pytest.mark.parametrize(
    ("field_name", "invalid_value", "error"),
    (
        ("pricing_version", "", "pricing_version"),
        ("cost_rates", {"input_tokens": -0.01}, "finite and nonnegative"),
    ),
)
def test_fill_results_rejects_tampered_scoring_before_agent_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field_name: str,
    invalid_value: object,
    error: str,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    task_pool_bundle = _task_pool_bundle((task,), (check,))
    store = ResultStore(tmp_path / "results.jsonl")
    selection, _ = _persist_replayable_selection(
        task_pool_bundle,
        TaskCheckRef(task.task_id, check.check_id),
        (agent,),
        store,
    )
    scoring_config = ScoringConfig("valid-pricing", {})
    object.__setattr__(scoring_config, field_name, invalid_value)
    calls: list[str] = []

    def fake_run_agent_on_task(*args, **kwargs):
        calls.append("called")
        return _workspace_run(task, check, agent)

    monkeypatch.setattr(
        "barcarolle.runner.workspace_module.run_agent_on_task", fake_run_agent_on_task
    )

    with pytest.raises(ValueError, match=error):
        fill_results(
            selection,
            task_pool_bundle,
            (agent,),
            _workspace_config(),
            _runtime_config(),
            scoring_config,
            ResultCacheConfig(),
            store,
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert calls == []


def test_run_agents_rejects_duplicate_agent_ids_before_execution(
    tmp_path: Path, monkeypatch
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    task_pool_bundle = _task_pool_bundle((task,), (check,))
    calls: list[str] = []

    def fake_run_agent_on_task(*args, **kwargs):
        calls.append("called")
        return _workspace_run(task, check, agent)

    monkeypatch.setattr(
        "barcarolle.runner.workspace_module.run_agent_on_task", fake_run_agent_on_task
    )

    with pytest.raises(ValueError, match="duplicate Agent IDs"):
        run_agents(
            task_pool_bundle,
            (TaskCheckRef(task.task_id, check.check_id),),
            (agent, agent),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultStore(tmp_path / "results.jsonl"),
            WorkspaceRunContext(),
        )

    assert calls == []


def test_run_agent_cells_preflights_every_plan_before_first_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    agents = (_agent(), _agent("other-agent", "other-manifest"))
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    cells = tuple(
        ResultCellRef(
            agent_id=agent.agent_id,
            task_id=task.task_id,
            check_id=check.check_id,
            required_identity_digest=compute_result_cache_identity(
                task,
                check,
                agent,
                workspace_config,
                runtime_config,
            ).identity_digest,
            result_id=None,
            result_digest=None,
            cell_state="missing",
            exclusion_reason=None,
            outcome=None,
        )
        for agent in agents
    )
    agent_calls: list[str] = []

    def reject_preflight(
        run_context_arg, plans, workspace_config_arg, runtime_config_arg
    ):
        assert tuple(agent.agent_id for _, _, agent in plans) == (
            "agent",
            "other-agent",
        )
        raise ValueError("endpoint proof mismatch")

    monkeypatch.setattr(
        runner_module.workspace_module,
        "preflight_run_bindings",
        reject_preflight,
    )
    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        lambda task_arg, check_arg, agent_arg, workspace_arg, runtime_arg, run_context: (
            agent_calls.append(agent_arg.agent_id)
        ),
    )

    with pytest.raises(ValueError, match="endpoint proof mismatch"):
        runner_module._run_agent_cells(
            cells,
            (task,),
            {check.check_id: check},
            agents,
            workspace_config,
            runtime_config,
            _scoring_config(),
            ResultStore(tmp_path / "results.jsonl"),
            WorkspaceRunContext(),
        )

    assert agent_calls == []


def test_run_agent_cells_does_not_require_endpoint_preflight_for_cache_only_operation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected_preflight(*args) -> None:
        raise AssertionError(
            "cache-only operation must not require endpoint credentials"
        )

    monkeypatch.setattr(
        runner_module.workspace_module,
        "preflight_run_bindings",
        unexpected_preflight,
    )

    assert (
        runner_module._run_agent_cells(
            (),
            (),
            {},
            (),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultStore(tmp_path / "results.jsonl"),
            WorkspaceRunContext(),
        )
        == ()
    )


def test_run_agents_rejects_nonpositive_timeout_before_execution(
    tmp_path: Path, monkeypatch
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    task_pool_bundle = _task_pool_bundle((task,), (check,))
    calls: list[str] = []

    def fake_run_agent_on_task(*args, **kwargs):
        calls.append("called")
        return _workspace_run(task, check, agent)

    monkeypatch.setattr(
        "barcarolle.runner.workspace_module.run_agent_on_task", fake_run_agent_on_task
    )

    with pytest.raises(ValueError, match="timeout_seconds must be a positive integer"):
        run_agents(
            task_pool_bundle,
            (TaskCheckRef(task.task_id, check.check_id),),
            (agent,),
            _workspace_config(),
            replace(_runtime_config(), timeout_seconds=0),
            _scoring_config(),
            ResultStore(tmp_path / "results.jsonl"),
            WorkspaceRunContext(),
        )

    assert calls == []


def test_run_agents_rejects_invalid_later_task_before_any_workspace_run(
    tmp_path: Path,
    monkeypatch,
) -> None:
    first_task = _task(task_id="first-task", check_id="first-check")
    first_check = _check(check_id="first-check", task_id="first-task")
    second_task = replace(
        _task(task_id="second-task", check_id="second-check"),
        solver_material_digest="invalid-solver-material",
    )
    second_check = _check(check_id="second-check", task_id="second-task")
    tasks = (first_task, second_task)
    agent = _agent()
    calls: list[str] = []

    def fake_run_agent_on_task(*args, **kwargs):
        calls.append("called")
        return _workspace_run(first_task, first_check, agent)

    monkeypatch.setattr(
        "barcarolle.runner.workspace_module.run_agent_on_task",
        fake_run_agent_on_task,
    )

    with pytest.raises(ValueError, match="failed validation"):
        run_agents(
            _task_pool_bundle(tasks, (first_check, second_check)),
            (
                TaskCheckRef(first_task.task_id, first_check.check_id),
                TaskCheckRef(second_task.task_id, second_check.check_id),
            ),
            (agent,),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultStore(tmp_path / "results.jsonl"),
            WorkspaceRunContext(),
        )

    assert calls == []


@pytest.mark.parametrize(
    ("drifted_member", "expected_error"),
    (
        ("task", "task records digest"),
        ("check", "check records digest"),
        ("certification", "certification evidence digest"),
        ("source_event", "source event records digest"),
    ),
)
def test_run_agents_rejects_frozen_task_pool_member_drift_before_execution(
    tmp_path: Path,
    monkeypatch,
    drifted_member: str,
    expected_error: str,
) -> None:
    task = _task()
    check = _check()
    valid_bundle = _task_pool_bundle((task,), (check,))
    task_pool = valid_bundle.task_pool
    tasks = (
        (replace(task, source_ref="changed-with-same-task-id"),)
        if drifted_member == "task"
        else (task,)
    )
    checks = {
        check.check_id: (
            replace(check, resource_limits={"timeout_seconds": 99})
            if drifted_member == "check"
            else check
        )
    }
    certification_evidence = valid_bundle.certification_evidence
    if drifted_member == "certification":
        certification_evidence = (
            {
                **certification_evidence[0],
                "reference_patch_digest": "changed-reference-patch",
            },
        )
    source_events = valid_bundle.source_events
    if drifted_member == "source_event":
        source_events = (
            record_with_digest(
                replace(
                    source_events[0],
                    source_ref="changed-source-ref",
                    source_event_digest="",
                )
            ),
        )
    calls: list[str] = []
    monkeypatch.setattr(
        "barcarolle.runner.workspace_module.run_agent_on_task",
        lambda *args, **kwargs: calls.append("called"),
    )
    drifted_bundle = task_pool_module.TaskPoolBundle(
        task_pool=task_pool,
        source_events=source_events,
        tasks=tasks,
        checks=tuple(checks.values()),
        certification_evidence=certification_evidence,
    )

    with pytest.raises(ValueError, match=expected_error):
        run_agents(
            drifted_bundle,
            (TaskCheckRef(task.task_id, check.check_id),),
            (_agent(),),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultStore(tmp_path / "results.jsonl"),
            WorkspaceRunContext(),
        )

    assert calls == []


def test_fill_results_rejects_source_event_drift_before_opening_result_store(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    bundle = _task_pool_bundle((task,), (check,))
    drifted_event = record_with_digest(
        replace(
            bundle.source_events[0],
            source_ref="changed-source-ref",
            source_event_digest="",
        )
    )
    drifted_bundle = replace(bundle, source_events=(drifted_event,))
    result_path = tmp_path / "results.jsonl"
    store = ResultStore(result_path)
    selection, _ = _persist_replayable_selection(
        bundle,
        TaskCheckRef(task.task_id, check.check_id),
        (_agent(),),
        store,
    )

    def fail_if_store_opens(*args, **kwargs):
        raise AssertionError("invalid Task Pool must fail before opening Result Store")

    monkeypatch.setattr(
        runner_module.result_store_module,
        "open_result_store_session",
        fail_if_store_opens,
    )

    with pytest.raises(ValueError, match="source event records digest"):
        fill_results(
            selection,
            drifted_bundle,
            (_agent(),),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            store,
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert not result_path.exists()


@pytest.mark.parametrize("entrypoint", ("prepare", "score"))
def test_evaluation_entrypoints_reject_certification_drift_before_cache_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entrypoint: str,
) -> None:
    task = _task()
    check = _check()
    bundle = _task_pool_bundle((task,), (check,))
    drifted_evidence = (
        {
            **bundle.certification_evidence[0],
            "reference_patch_digest": "changed-reference-patch",
        },
    )
    drifted_bundle = replace(bundle, certification_evidence=drifted_evidence)
    ref = TaskCheckRef(task.task_id, check.check_id)
    selection = _selection(bundle.task_pool, ref)
    origin = _origin(bundle.task_pool, ref, ref)

    def fail_if_cache_is_touched(*args, **kwargs):
        raise AssertionError("invalid Task Pool must fail before cache access")

    monkeypatch.setattr(
        runner_module,
        (
            "_prepare_evaluation_cell_sets"
            if entrypoint == "prepare"
            else "_score_evaluation_cell_set"
        ),
        fail_if_cache_is_touched,
    )

    with pytest.raises(ValueError, match="certification evidence digest"):
        if entrypoint == "prepare":
            prepare_evaluation_cells(
                selection,
                origin,
                drifted_bundle,
                (_agent(),),
                _workspace_config(),
                _runtime_config(),
                _scoring_config(),
                ResultCacheConfig(),
                ResultStore(tmp_path / "results.jsonl"),
                ResultJoinConfig(),
                WorkspaceRunContext(),
            )
        else:
            score_selection(
                selection,
                origin,
                drifted_bundle,
                (_agent(),),
                None,  # type: ignore[arg-type]
                ResultStore(tmp_path / "results.jsonl"),
                ResultJoinConfig(),
            )


def test_fill_results_reprices_cached_execution_without_rerunning_agent(
    tmp_path: Path, monkeypatch
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    old_pricing = ScoringConfig("old-pricing", {"input_tokens": 0.01})
    current_pricing = ScoringConfig("current-pricing", {"input_tokens": 0.02})
    store = ResultStore(tmp_path / "results.jsonl")
    monkeypatch.setattr(
        runner_module.result_store_module, "_now", lambda: "2026-01-15T00:00:00Z"
    )
    old_result = _result(
        task, check, agent, workspace_config, runtime_config, old_pricing
    )
    store_result(old_result, store)
    task_pool_bundle = _task_pool_bundle((task,), (check,))
    selection, _ = _persist_replayable_selection(
        task_pool_bundle,
        TaskCheckRef(task.task_id, check.check_id),
        (agent,),
        store,
    )
    old_cell_set = fill_results(
        selection,
        task_pool_bundle,
        (agent,),
        workspace_config,
        runtime_config,
        old_pricing,
        ResultCacheConfig(),
        store,
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )
    assert old_cell_set.cells[0].result_id == old_result.result_id

    def fail_if_agent_runs(*args, **kwargs):
        raise AssertionError("a pricing change must not rerun paid execution")

    monkeypatch.setattr(
        "barcarolle.runner.workspace_module.run_agent_on_task", fail_if_agent_runs
    )
    monkeypatch.setattr(
        runner_module.result_store_module, "_now", lambda: "2026-02-01T00:00:00Z"
    )

    cell_set = fill_results(
        selection,
        task_pool_bundle,
        (agent,),
        workspace_config,
        runtime_config,
        current_pricing,
        ResultCacheConfig(),
        store,
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )

    assert cell_set.cell_set_id != old_cell_set.cell_set_id
    assert cell_set.cells[0].result_id != old_result.result_id
    current_result = next(
        result
        for result in load_results(store, ResultQuery())
        if result.scoring_config_digest == current_pricing.scoring_config_digest
    )
    assert current_result.result_id != old_result.result_id
    assert current_result.scoring_config_digest == current_pricing.scoring_config_digest
    assert current_result.pricing_version == "current-pricing"
    assert current_result.cost == {"input_tokens_cost": 0.2, "total_cost": 0.2}
    assert current_result.usage == old_result.usage
    assert current_result.outcome == old_result.outcome
    assert current_result.diff_digest == old_result.diff_digest
    assert (
        current_result.verifier_metadata_digest == old_result.verifier_metadata_digest
    )
    assert current_result.result_available_at == old_result.result_available_at

    cells = runner_module.result_store_module.resolve_result_cells(
        (TaskCheckRef(task.task_id, check.check_id),),
        (task,),
        {check.check_id: check},
        (agent,),
        workspace_config,
        runtime_config,
        store,
        ResultCacheConfig(),
        current_pricing,
    )
    assert cells[0].result_id == current_result.result_id
    assert cells[0].result_digest == current_result.result_digest
    assert cell_set.cells[0].result_id == current_result.result_id

    assert (
        fill_results(
            selection,
            task_pool_bundle,
            (agent,),
            workspace_config,
            runtime_config,
            current_pricing,
            ResultCacheConfig(),
            store,
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )
        == cell_set
    )
    assert load_results(store, ResultQuery()) == (old_result, current_result)


def test_fill_results_honors_stricter_cache_policy_after_persisted_cell_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    store = ResultStore(tmp_path / "results.jsonl")
    invalid_run = replace(
        _workspace_run(task, check, agent),
        workspace_run_id="workspace-run-benchmark-invalid",
        terminal_status="invalid",
        check_outcome="invalid",
        invalid_owner="benchmark",
        failure_label="verifier_preparation_failed",
    )
    invalid_result = build_result_record(
        task,
        check,
        agent,
        invalid_run,
        compute_result_cache_identity(
            task,
            check,
            agent,
            workspace_config,
            runtime_config,
        ),
        scoring_config,
    )
    store_result(invalid_result, store)
    task_pool_bundle = _task_pool_bundle((task,), (check,))
    selection, _ = _persist_replayable_selection(
        task_pool_bundle,
        TaskCheckRef(task.task_id, check.check_id),
        (agent,),
        store,
    )
    permissive_cell_set = fill_results(
        selection,
        task_pool_bundle,
        (agent,),
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(reuse_benchmark_invalid=True),
        store,
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )
    assert permissive_cell_set.cells[0].result_id == invalid_result.result_id
    calls: list[str] = []

    def repeat_invalid_run(*args, **kwargs):
        calls.append("run")
        return invalid_run

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        repeat_invalid_run,
    )

    strict_cell_set = fill_results(
        selection,
        task_pool_bundle,
        (agent,),
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(),
        store,
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )

    assert calls == ["run"]
    assert strict_cell_set.cell_set_id != permissive_cell_set.cell_set_id
    assert strict_cell_set.cells[0].cell_state == "missing"
    assert strict_cell_set.cells[0].result_id is None


def test_result_id_is_stable_when_repricing_from_a_repriced_result(monkeypatch) -> None:
    original = _result(
        _task(),
        _check(),
        _agent(),
        _workspace_config(),
        _runtime_config(),
        ScoringConfig("old-pricing", {"input_tokens": 0.01}),
    )
    middle_pricing = ScoringConfig("middle-pricing", {"input_tokens": 0.02})
    final_pricing = ScoringConfig("final-pricing", {"input_tokens": 0.03})
    monkeypatch.setattr(
        runner_module.result_store_module, "_now", lambda: "2026-02-01T00:00:00Z"
    )
    middle = runner_module.result_store_module._reprice_result(original, middle_pricing)
    direct_final = runner_module.result_store_module._reprice_result(
        original, final_pricing
    )
    chained_final = runner_module.result_store_module._reprice_result(
        middle, final_pricing
    )

    assert direct_final.result_id == chained_final.result_id


def test_pre_origin_results_dedupe_repricing_and_reject_ambiguous_executions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    old_pricing = ScoringConfig("old-pricing", {"input_tokens": 0.01})
    current_pricing = ScoringConfig("current-pricing", {"input_tokens": 0.02})
    store = ResultStore(tmp_path / "results.jsonl")
    monkeypatch.setattr(
        runner_module.result_store_module, "_now", lambda: "2026-01-12T00:00:00Z"
    )
    identity = compute_result_cache_identity(
        task, check, agent, workspace_config, runtime_config
    )
    original = build_result_record(
        task,
        check,
        agent,
        _workspace_run(task, check, agent),
        identity,
        old_pricing,
    )
    store_result(original, store)
    repriced = runner_module.result_store_module.reprice_cached_results(
        (TaskCheckRef(task.task_id, check.check_id),),
        (task,),
        {check.check_id: check},
        (agent,),
        workspace_config,
        runtime_config,
        store,
        ResultCacheConfig(),
        current_pricing,
    )[0]
    pre_origin_results = runner_module._load_results_for_refs(
        store,
        (TaskCheckRef(task.task_id, check.check_id),),
        (agent,),
        result_available_after="2026-01-01T00:00:00Z",
        result_available_before="2026-01-20T00:00:00Z",
    )
    canonical_view = min((original, repriced), key=lambda result: result.result_id)
    assert pre_origin_results == (canonical_view,)
    assert runner_module._distinct_unambiguous_results(
        (repriced, original),
        {(task.task_id, check.check_id)},
    ) == (canonical_view,)
    discarded_view = max((original, repriced), key=lambda result: result.result_id)
    assert discarded_view.result_id not in {
        result.result_id for result in pre_origin_results
    }
    assert runner_module.result_store_module.result_execution_digest(original) == (
        runner_module.result_store_module.result_execution_digest(repriced)
    )

    distinct_workspace_run = replace(
        _workspace_run(task, check, agent),
        workspace_run_id="workspace-run-distinct",
    )
    distinct_result = build_result_record(
        task,
        check,
        agent,
        distinct_workspace_run,
        identity,
        current_pricing,
    )
    store_result(distinct_result, store)

    with pytest.raises(ValueError, match="conflicting Result executions"):
        runner_module._load_results_for_refs(
            store,
            (TaskCheckRef(task.task_id, check.check_id),),
            (agent,),
            result_available_after="2026-01-01T00:00:00Z",
            result_available_before="2026-01-20T00:00:00Z",
        )
    assert runner_module.result_store_module.result_execution_digest(original) != (
        runner_module.result_store_module.result_execution_digest(distinct_result)
    )
    assert original.verifier_metadata_digest != distinct_result.verifier_metadata_digest
    assert (
        runner_module._load_results_for_refs(
            store,
            (TaskCheckRef(task.task_id, check.check_id),),
            (agent,),
            result_available_after="2026-01-13T00:00:00Z",
            result_available_before="2026-01-20T00:00:00Z",
        )
        == ()
    )


def test_select_benchmark_loads_only_allowed_pre_origin_results_and_appends_selection(
    tmp_path: Path, monkeypatch
) -> None:
    task = _task()
    check = _check()
    task_pool = _task_pool_with_refs(tmp_path, (task,), (check,))
    agent = _agent()
    pre_origin_result = _redigest_result(
        _result(
            task,
            check,
            agent,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
        ),
        started_at="2026-01-03T00:00:00Z",
        finished_at="2026-01-03T00:00:05Z",
        source_result_available_at="2026-01-04T00:00:00Z",
        result_available_at="2026-01-04T00:00:00Z",
    )
    queries = []

    def fake_load_results(store, query):
        queries.append(query)
        return (pre_origin_result,)

    monkeypatch.setattr(
        runner_module.result_store_module, "load_results", fake_load_results
    )

    selection = select_benchmark(
        task_pool,
        (agent,),
        datetime(2026, 1, 5, tzinfo=UTC),
        SelectionBudget(1),
        build_rule_selector(
            "recency",
            allowed_feature_classes=(
                "task_metadata",
                "pre_origin_result",
            ),
        ),
        RollingOriginPolicy(
            "origin_time",
            "strict_prospective",
            "allow_cluster_overlap",
            False,
        ),
        FeatureConfig(("pre_origin_result_count",)),
        ResultStore(tmp_path / "results.jsonl"),
    )
    resumed = select_benchmark(
        task_pool,
        (agent,),
        datetime(2026, 1, 5, tzinfo=UTC),
        SelectionBudget(1),
        build_rule_selector(
            "recency",
            allowed_feature_classes=(
                "task_metadata",
                "pre_origin_result",
            ),
        ),
        RollingOriginPolicy(
            "origin_time",
            "strict_prospective",
            "allow_cluster_overlap",
            False,
        ),
        FeatureConfig(("pre_origin_result_count",)),
        ResultStore(tmp_path / "results.jsonl"),
    )
    logged = load_jsonl_records(tmp_path / "selections.jsonl", BenchmarkSelectionRecord)
    logged_origins = load_jsonl_records(tmp_path / "origins.jsonl", RollingOriginRecord)
    logged_snapshots = load_jsonl_records(
        tmp_path / "feature-snapshots.jsonl",
        FeatureSnapshotRecord,
    )
    logged_inputs = load_jsonl_records(
        tmp_path / "selector-inputs.jsonl", SelectorInput
    )
    logged_selectors = load_jsonl_records(tmp_path / "selectors.jsonl", SelectorRecord)
    assert queries[0].task_ids == ("task",)
    assert queries[0].check_ids == ("check",)
    assert queries[0].agent_ids == ("agent",)
    assert queries[0].result_available_after is None
    assert queries[0].result_available_before.startswith("2026-01-05T00:00:00")
    assert logged == [selection]
    assert resumed == selection
    assert logged_selectors[0].selector_digest == selection.selector_digest
    assert logged_origins[0].origin_id == selection.origin_id
    assert logged_snapshots[0].feature_snapshot_id == selection.feature_snapshot_id
    assert logged_inputs[0].selector_input_digest == selection.selection_input_digest


def test_select_benchmark_rejects_cutoff_after_origin_before_loading_results(
    tmp_path: Path, monkeypatch
) -> None:
    task = _task()
    check = _check()
    task_pool = _task_pool_with_refs(tmp_path, (task,), (check,))

    def fail_if_results_are_loaded(*args, **kwargs):
        raise AssertionError("future cutoff must be rejected before loading results")

    monkeypatch.setattr(
        runner_module.result_store_module, "load_results", fail_if_results_are_loaded
    )

    with pytest.raises(ValueError, match="must not be after origin_time"):
        select_benchmark(
            task_pool,
            (_agent(),),
            datetime(2026, 1, 5, tzinfo=UTC),
            SelectionBudget(1),
            _selector(),
            RollingOriginPolicy(
                "2026-01-06T00:00:00Z",
                "strict_prospective",
                "allow_cluster_overlap",
                False,
            ),
            FeatureConfig(("task_count",)),
            ResultStore(tmp_path / "results.jsonl"),
        )


def test_prepare_evaluation_cells_and_score_selection_keep_selected_future_linkage(
    tmp_path: Path, monkeypatch
) -> None:
    selected_task = _task(
        "selected-task", "selected-check", available_at="2026-01-02T00:00:00Z"
    )
    future_task = _task(
        "future-task", "future-check", available_at="2026-01-07T00:00:00Z"
    )
    selected_check = _check(
        "selected-check", "selected-task", available_at="2026-01-02T00:00:00Z"
    )
    future_check = _check(
        "future-check", "future-task", available_at="2026-01-07T00:00:00Z"
    )
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    old_pricing = ScoringConfig("old-pricing", {"input_tokens": 0.005})
    store = ResultStore(tmp_path / "results.jsonl")
    for task, check in ((selected_task, selected_check), (future_task, future_check)):
        store_result(
            _result(task, check, agent, workspace_config, runtime_config, old_pricing),
            store,
        )
    task_pool_bundle = _task_pool_bundle(
        (selected_task, future_task), (selected_check, future_check)
    )
    task_pool = task_pool_bundle.task_pool
    selected_ref = TaskCheckRef("selected-task", "selected-check")
    future_ref = TaskCheckRef("future-task", "future-check")
    origin = _origin(task_pool, selected_ref, future_ref)
    selection, _ = _persist_replayable_selection(
        task_pool_bundle,
        selected_ref,
        (agent,),
        store,
        origin=origin,
    )

    def fail_if_workspace_runs(*args, **kwargs):
        raise AssertionError("all selected and future cells should come from cache")

    monkeypatch.setattr(
        "barcarolle.runner.workspace_module.run_agent_on_task", fail_if_workspace_runs
    )

    cell_set = prepare_evaluation_cells(
        selection,
        origin,
        task_pool_bundle,
        (agent,),
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(),
        store,
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )
    scored_cell_set, selected_matrix, future_matrix, metrics = score_selection(
        selection,
        origin,
        task_pool_bundle,
        (agent,),
        cell_set,
        store,
        ResultJoinConfig(),
    )
    resumed = score_selection(
        selection,
        origin,
        task_pool_bundle,
        (agent,),
        cell_set,
        store,
        ResultJoinConfig(),
    )

    assert scored_cell_set == cell_set
    assert selected_matrix.matrix_role == "selected"
    assert future_matrix.matrix_role == "future_holdout"
    assert selected_matrix.task_check_refs == (selected_ref,)
    assert future_matrix.task_check_refs == (future_ref,)
    bound_results = load_results(
        store,
        ResultQuery(
            result_ids=tuple(
                cell.result_id for cell in cell_set.cells if cell.result_id is not None
            )
        ),
    )
    assert {result.scoring_config_digest for result in bound_results} == {
        scoring_config.scoring_config_digest
    }
    assert {metric.selected_matrix_digest for metric in metrics} == {
        selected_matrix.matrix_digest
    }
    assert {metric.future_matrix_digest for metric in metrics} == {
        future_matrix.matrix_digest
    }
    assert resumed == (scored_cell_set, selected_matrix, future_matrix, metrics)
    logged_metrics = load_jsonl_records(
        store.path.with_name("metrics.jsonl"), MetricRecord
    )
    assert tuple(metric.metric_id for metric in logged_metrics) == tuple(
        metric.metric_id for metric in metrics
    )


def test_evaluate_selectors_rejects_strict_mode_without_future_pool_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task(available_at="2026-01-02T00:00:00Z")
    check = _check(available_at="2026-01-02T00:00:00Z")
    task_pool = _task_pool_with_refs(tmp_path, (task,), (check,))

    def fail_if_agent_runs(*args, **kwargs):
        raise AssertionError("unsupported evaluation must stop before Agent execution")

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        fail_if_agent_runs,
    )

    with pytest.raises(ValueError, match="separately linked future Task Pool"):
        evaluate_selectors(
            (
                build_rule_selector(
                    "recency",
                    allowed_feature_classes=("task_metadata",),
                ),
            ),
            task_pool,
            (_agent(),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
            SelectorEvaluationConfig(
                origin_times=("2026-01-05T00:00:00Z",),
                budget=SelectionBudget(1),
            ),
            RollingOriginPolicy(
                "origin_time",
                "strict_prospective",
                "allow_cluster_overlap",
                False,
            ),
            FeatureConfig(("task_count",)),
            ResultStore(tmp_path / "results.jsonl"),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert not (tmp_path / "selectors.jsonl").exists()
    assert not (tmp_path / "origins.jsonl").exists()
    assert not (tmp_path / "results.jsonl").exists()


def test_evaluate_prospective_selection_links_later_pool_and_retains_censoring(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected_task = _task(
        "selected-task", "selected-check", available_at="2026-01-02T00:00:00Z"
    )
    future_task = _task(
        "future-task", "future-check", available_at="2026-01-07T00:00:00Z"
    )
    censored_task = _task(
        "censored-task", "censored-check", available_at="2026-01-08T00:00:00Z"
    )
    selected_check = _check(
        "selected-check", "selected-task", available_at="2026-01-02T00:00:00Z"
    )
    future_check = _check(
        "future-check", "future-task", available_at="2026-01-08T00:00:00Z"
    )
    censored_check = _check(
        "censored-check", "censored-task", available_at="2026-01-20T00:00:00Z"
    )
    selection_pool = _task_pool_with_refs(
        tmp_path,
        (selected_task,),
        (selected_check,),
        bundle_name="selection-pool",
        task_pool_id="selection-pool",
        created_at="2026-01-04T00:00:00Z",
        source_window=TimeRange("2026-01-01T00:00:00Z", "2026-01-04T00:00:00Z"),
        generation_evidence=True,
    )
    future_pool = _task_pool_with_refs(
        tmp_path,
        (future_task, censored_task),
        (future_check, censored_check),
        bundle_name="future-pool",
        task_pool_id="future-pool",
        created_at="2026-01-21T00:00:00Z",
        source_window=TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
        generation_evidence=True,
    )
    monkeypatch.setattr(
        "barcarolle.selection.algorithms._now",
        lambda: "2026-01-05T00:00:01.000000Z",
    )
    store = ResultStore(tmp_path / "results.jsonl")
    agent = _agent()
    selection = select_benchmark(
        selection_pool,
        (agent,),
        datetime(2026, 1, 5, tzinfo=UTC),
        SelectionBudget(1),
        build_rule_selector("recency", allowed_feature_classes=("task_metadata",)),
        RollingOriginPolicy(
            "origin_time",
            "strict_prospective",
            "allow_cluster_overlap",
            False,
            maturity_lag_seconds=86400,
        ),
        FeatureConfig(("task_count",)),
        store,
        future_window=TimeRange("2026-01-06T00:00:00Z", "2026-01-10T00:00:00Z"),
    )
    executed: list[tuple[str, str]] = []

    def fake_run_agent_on_task(task, check, agent, *args, **kwargs):
        executed.append((task.task_id, check.check_id))
        return replace(
            _workspace_run(task, check, agent),
            started_at="2026-01-22T00:00:00Z",
            finished_at="2026-01-22T00:00:05Z",
        )

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        fake_run_agent_on_task,
    )
    monkeypatch.setattr(
        runner_module.result_store_module,
        "_now",
        lambda: "2026-01-22T00:00:05.000000Z",
    )
    monkeypatch.setattr(
        "barcarolle.selection.evaluation._now",
        lambda: "2026-01-22T00:00:06.000000Z",
    )

    cell_set, selected_matrix, future_matrix, metrics = (
        runner_module.evaluate_prospective_selection(
            selection.selection_id,
            selection_pool,
            future_pool,
            (agent,),
            store,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )
    )

    assert cell_set.future_task_pool_id == future_pool.task_pool_id
    assert cell_set.future_task_pool_digest == future_pool.task_pool_digest
    assert cell_set.future_task_check_refs == (
        TaskCheckRef("future-task", "future-check"),
    )
    assert cell_set.future_censored_task_check_refs == (
        TaskCheckRef("censored-task", "censored-check"),
    )
    assert selected_matrix.task_check_refs == selection.selected_task_check_refs
    assert future_matrix.task_check_refs == cell_set.future_task_check_refs
    assert metrics
    assert executed == [
        ("selected-task", "selected-check"),
        ("future-task", "future-check"),
    ]
    origins = load_jsonl_records(tmp_path / "origins.jsonl", RollingOriginRecord)
    snapshots = load_jsonl_records(
        tmp_path / "feature-snapshots.jsonl", FeatureSnapshotRecord
    )
    inputs = load_jsonl_records(tmp_path / "selector-inputs.jsonl", SelectorInput)
    selectors = load_jsonl_records(tmp_path / "selectors.jsonl", SelectorRecord)
    results = load_results(store, ResultQuery())
    missing_future_pool_report = runner_module.reporting_module.build_selector_report(
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        metrics,
        origins=origins,
        feature_snapshots=snapshots,
        selector_inputs=inputs,
        selectors=selectors,
        agents=(agent,),
        results=results,
        task_pool=selection_pool,
    )
    linked_report = runner_module.reporting_module.build_selector_report(
        (selection,),
        (cell_set,),
        (selected_matrix, future_matrix),
        metrics,
        origins=origins,
        feature_snapshots=snapshots,
        selector_inputs=inputs,
        selectors=selectors,
        agents=(agent,),
        results=results,
        task_pool=selection_pool,
        future_task_pools=(future_pool,),
    )

    assert missing_future_pool_report.supported_claims == ()
    assert any(
        "references missing future Task Pool" in limitation
        for limitation in missing_future_pool_report.limitations
    )
    assert linked_report.supported_claims == (
        "strict_prospective_selector_performance_summary",
    )


def test_evaluate_prospective_selection_rejects_agent_drift_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task(available_at="2026-01-02T00:00:00Z")
    check = _check(available_at="2026-01-02T00:00:00Z")
    task_pool = _task_pool_with_refs(
        tmp_path,
        (task,),
        (check,),
        task_pool_id="selection-pool",
        created_at="2026-01-04T00:00:00Z",
        source_window=TimeRange("2026-01-01T00:00:00Z", "2026-01-04T00:00:00Z"),
    )
    monkeypatch.setattr(
        "barcarolle.selection.algorithms._now",
        lambda: "2026-01-05T00:00:01.000000Z",
    )
    store = ResultStore(tmp_path / "results.jsonl")
    selection = select_benchmark(
        task_pool,
        (_agent(),),
        datetime(2026, 1, 5, tzinfo=UTC),
        SelectionBudget(1),
        build_rule_selector("recency", allowed_feature_classes=("task_metadata",)),
        RollingOriginPolicy(
            "origin_time",
            "strict_prospective",
            "allow_cluster_overlap",
            False,
        ),
        FeatureConfig(("task_count",)),
        store,
        future_window=TimeRange("2026-01-06T00:00:00Z", "2026-01-07T00:00:00Z"),
    )

    with pytest.raises(ValueError, match="Agent identities do not match"):
        runner_module.evaluate_prospective_selection(
            selection.selection_id,
            task_pool,
            task_pool,
            (_agent(manifest="other-manifest"),),
            store,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert not store.path.exists()


def test_evaluate_prospective_selection_replays_frozen_selection_before_pool_reads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_task = _task("first-task", "first-check", available_at="2026-01-02T00:00:00Z")
    second_task = _task(
        "second-task", "second-check", available_at="2026-01-03T00:00:00Z"
    )
    first_check = _check(
        "first-check", "first-task", available_at="2026-01-02T00:00:00Z"
    )
    second_check = _check(
        "second-check", "second-task", available_at="2026-01-03T00:00:00Z"
    )
    task_pool = _task_pool_with_refs(
        tmp_path,
        (first_task, second_task),
        (first_check, second_check),
        task_pool_id="selection-pool",
        created_at="2026-01-04T00:00:00Z",
        source_window=TimeRange("2026-01-01T00:00:00Z", "2026-01-04T00:00:00Z"),
    )
    monkeypatch.setattr(
        "barcarolle.selection.algorithms._now",
        lambda: "2026-01-05T00:00:01.000000Z",
    )
    store = ResultStore(tmp_path / "results.jsonl")
    agent = _agent()
    selection = select_benchmark(
        task_pool,
        (agent,),
        datetime(2026, 1, 5, tzinfo=UTC),
        SelectionBudget(1),
        build_rule_selector("recency", allowed_feature_classes=("task_metadata",)),
        RollingOriginPolicy(
            "origin_time",
            "strict_prospective",
            "allow_cluster_overlap",
            False,
        ),
        FeatureConfig(("task_count",)),
        store,
        future_window=TimeRange("2026-01-06T00:00:00Z", "2026-01-07T00:00:00Z"),
    )
    tampered_ref = TaskCheckRef("first-task", "first-check")
    tampered = record_with_digest(
        replace(
            selection,
            selected_task_check_refs=(tampered_ref,),
            selected_weights={task_check_ref_key(tampered_ref): 1.0},
            selection_digest="",
        )
    )
    write_jsonl_records(tmp_path / "selections.jsonl", (tampered,))

    def fail_on_pool_read(*args, **kwargs):
        raise AssertionError("Selection replay must precede Task Pool reads")

    monkeypatch.setattr(runner_module, "_load_task_pool_records", fail_on_pool_read)

    with pytest.raises(ValueError, match="does not replay deterministically"):
        runner_module.evaluate_prospective_selection(
            selection.selection_id,
            task_pool,
            task_pool,
            (agent,),
            store,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert not store.path.exists()


def test_evaluate_prospective_selection_resolves_pre_origin_results_before_pool_reads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task(available_at="2026-01-02T00:00:00Z")
    check = _check(available_at="2026-01-02T00:00:00Z")
    task_pool = _task_pool_with_refs(
        tmp_path,
        (task,),
        (check,),
        task_pool_id="selection-pool",
        created_at="2026-01-04T00:00:00Z",
        source_window=TimeRange("2026-01-01T00:00:00Z", "2026-01-04T00:00:00Z"),
    )
    agent = _agent()
    store = ResultStore(tmp_path / "results.jsonl")
    monkeypatch.setattr(
        runner_module.result_store_module,
        "_now",
        lambda: "2026-01-04T00:00:05.000000Z",
    )
    pre_origin_result = build_result_record(
        task,
        check,
        agent,
        replace(
            _workspace_run(task, check, agent),
            started_at="2026-01-04T00:00:00Z",
            finished_at="2026-01-04T00:00:05Z",
        ),
        compute_result_cache_identity(
            task,
            check,
            agent,
            _workspace_config(),
            _runtime_config(),
        ),
        _scoring_config(),
    )
    store_result(pre_origin_result, store)
    monkeypatch.setattr(
        "barcarolle.selection.algorithms._now",
        lambda: "2026-01-05T00:00:01.000000Z",
    )
    selection = select_benchmark(
        task_pool,
        (agent,),
        datetime(2026, 1, 5, tzinfo=UTC),
        SelectionBudget(1),
        build_rule_selector(
            "recency",
            allowed_feature_classes=("pre_origin_result",),
        ),
        RollingOriginPolicy(
            "origin_time",
            "strict_prospective",
            "allow_cluster_overlap",
            False,
        ),
        FeatureConfig(
            ("pre_origin_result_count",),
        ),
        store,
        future_window=TimeRange("2026-01-06T00:00:00Z", "2026-01-07T00:00:00Z"),
    )
    store.path.unlink()

    def fail_on_pool_read(*args, **kwargs):
        raise AssertionError("Result evidence replay must precede Task Pool reads")

    monkeypatch.setattr(runner_module, "_load_task_pool_records", fail_on_pool_read)

    with pytest.raises(ValueError, match="missing from pre_origin_results"):
        runner_module.evaluate_prospective_selection(
            selection.selection_id,
            task_pool,
            task_pool,
            (agent,),
            store,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert not store.path.exists()


def test_evaluate_prospective_selection_replays_task_metadata_before_future_pool(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tasks = tuple(
        _task(
            f"task-{index}",
            f"check-{index}",
            available_at=f"2026-01-0{index + 1}T00:00:00Z",
            sampling_stratum=stratum,
        )
        for index, stratum in enumerate(("a", "a", "b", "b"))
    )
    checks = tuple(
        _check(
            task.check_ids[0],
            task.task_id,
            available_at=task.task_material_available_at,
        )
        for task in tasks
    )
    task_pool = _task_pool_with_refs(
        tmp_path,
        tasks,
        checks,
        task_pool_id="selection-pool",
        created_at="2026-01-04T00:00:00Z",
        source_window=TimeRange("2026-01-01T00:00:00Z", "2026-01-04T00:00:00Z"),
    )
    monkeypatch.setattr(
        "barcarolle.selection.algorithms._now",
        lambda: "2026-01-05T00:00:01.000000Z",
    )
    agent = _agent()
    store = ResultStore(tmp_path / "results.jsonl")
    selector = build_rule_selector(
        "stratified_forecast",
        {
            "dirichlet_alpha": 1.0,
            "trailing_ref_count": 2,
            "seed": 7,
            "weight_cap": 1.0,
        },
        allowed_feature_classes=("task_metadata",),
    )
    selection = select_benchmark(
        task_pool,
        (agent,),
        datetime(2026, 1, 5, tzinfo=UTC),
        SelectionBudget(3),
        selector,
        RollingOriginPolicy(
            "origin_time",
            "strict_prospective",
            "allow_cluster_overlap",
            False,
        ),
        FeatureConfig(("task_stratum",)),
        store,
        future_window=TimeRange("2026-01-06T00:00:00Z", "2026-01-07T00:00:00Z"),
    )
    (selector_input,) = load_jsonl_records(
        tmp_path / "selector-inputs.jsonl",
        SelectorInput,
    )
    (snapshot,) = load_jsonl_records(
        tmp_path / "feature-snapshots.jsonl",
        FeatureSnapshotRecord,
    )
    tampered_records = tuple(
        replace(record, value="0")
        if record.feature_name == "task_stratum" and record.task_id == "task-0"
        else record
        for record in snapshot.feature_records
    )
    tampered_snapshot = replace(
        snapshot,
        feature_snapshot_id="",
        feature_records=tampered_records,
        feature_records_digest=canonical_digest(tampered_records),
        feature_snapshot_digest="",
    )
    tampered_snapshot = replace(
        tampered_snapshot,
        feature_snapshot_id=make_feature_snapshot_id(tampered_snapshot),
    )
    tampered_snapshot = record_with_digest(tampered_snapshot)
    tampered_input = replace(
        selector_input,
        selector_input_id="",
        feature_snapshot_id=tampered_snapshot.feature_snapshot_id,
        feature_records_digest=tampered_snapshot.feature_records_digest,
        selector_input_digest="",
    )
    tampered_input = replace(
        tampered_input,
        selector_input_id=make_selector_input_id(tampered_input),
    )
    tampered_input = record_with_digest(tampered_input)
    tampered_selection = runner_module.selection_module.select_with_selector(
        tampered_input,
        tampered_snapshot,
        selector,
    )
    write_jsonl_records(
        tmp_path / "feature-snapshots.jsonl",
        (tampered_snapshot,),
    )
    write_jsonl_records(tmp_path / "selector-inputs.jsonl", (tampered_input,))
    write_jsonl_records(tmp_path / "selections.jsonl", (tampered_selection,))

    original_pool_loader = runner_module._load_task_pool_records
    pool_reads = 0

    def guarded_pool_read(*args, **kwargs):
        nonlocal pool_reads
        pool_reads += 1
        if pool_reads > 1:
            raise AssertionError(
                "Feature provenance replay must precede future Task Pool reads"
            )
        return original_pool_loader(*args, **kwargs)

    monkeypatch.setattr(runner_module, "_load_task_pool_records", guarded_pool_read)

    with pytest.raises(ValueError, match="task_stratum.*Task record"):
        runner_module.evaluate_prospective_selection(
            tampered_selection.selection_id,
            task_pool,
            task_pool,
            (agent,),
            store,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert (
        selection.selected_task_check_refs
        != tampered_selection.selected_task_check_refs
    )
    assert pool_reads == 1


@pytest.mark.parametrize(
    ("drift_kind", "expected_error", "allowed_pool_reads"),
    (
        ("agent", "cache identity.*frozen Agent", 0),
        ("task", "cache identity.*selection Task/Check", 1),
    ),
)
def test_evaluate_prospective_selection_replays_pre_origin_cache_identity_before_execution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    drift_kind: str,
    expected_error: str,
    allowed_pool_reads: int,
) -> None:
    task = _task(available_at="2026-01-02T00:00:00Z")
    check = _check(available_at="2026-01-02T00:00:00Z")
    task_pool = _task_pool_with_refs(
        tmp_path,
        (task,),
        (check,),
        task_pool_id="selection-pool",
        created_at="2026-01-04T00:00:00Z",
        source_window=TimeRange("2026-01-01T00:00:00Z", "2026-01-04T00:00:00Z"),
    )
    agent = _agent()
    store = ResultStore(tmp_path / "results.jsonl")
    monkeypatch.setattr(
        runner_module.result_store_module,
        "_now",
        lambda: "2026-01-04T00:00:05.000000Z",
    )
    pre_origin_result = build_result_record(
        task,
        check,
        agent,
        replace(
            _workspace_run(task, check, agent),
            started_at="2026-01-04T00:00:00Z",
            finished_at="2026-01-04T00:00:05Z",
        ),
        compute_result_cache_identity(
            task,
            check,
            agent,
            _workspace_config(),
            _runtime_config(),
        ),
        _scoring_config(),
    )
    store_result(pre_origin_result, store)
    monkeypatch.setattr(
        "barcarolle.selection.algorithms._now",
        lambda: "2026-01-05T00:00:01.000000Z",
    )
    selection = select_benchmark(
        task_pool,
        (agent,),
        datetime(2026, 1, 5, tzinfo=UTC),
        SelectionBudget(1),
        build_rule_selector("recency", allowed_feature_classes=("task_metadata",)),
        RollingOriginPolicy(
            "origin_time",
            "strict_prospective",
            "allow_cluster_overlap",
            False,
        ),
        FeatureConfig(("task_count",)),
        store,
        future_window=TimeRange("2026-01-06T00:00:00Z", "2026-01-07T00:00:00Z"),
    )
    (origin,) = load_jsonl_records(tmp_path / "origins.jsonl", RollingOriginRecord)
    (selector_input,) = load_jsonl_records(
        tmp_path / "selector-inputs.jsonl",
        SelectorInput,
    )
    (snapshot,) = load_jsonl_records(
        tmp_path / "feature-snapshots.jsonl",
        FeatureSnapshotRecord,
    )
    (selector,) = load_jsonl_records(tmp_path / "selectors.jsonl", SelectorRecord)
    identity_updates = (
        {"prompt_digest": "drifted-prompt"}
        if drift_kind == "agent"
        else {"base_commit": "b" * 40}
    )
    tampered_identity = record_with_digest(
        replace(
            pre_origin_result.cache_identity,
            identity_digest="",
            **identity_updates,
        )
    )
    tampered_result = _redigest_result(
        pre_origin_result,
        cache_identity=tampered_identity,
    )
    tampered_snapshot = replace(
        snapshot,
        feature_snapshot_id="",
        result_view_digest=canonical_digest(
            (
                (
                    tampered_result.result_id,
                    tampered_result.result_digest,
                    tampered_result.cache_identity.identity_digest,
                ),
            )
        ),
        feature_snapshot_digest="",
    )
    tampered_snapshot = replace(
        tampered_snapshot,
        feature_snapshot_id=make_feature_snapshot_id(tampered_snapshot),
    )
    tampered_snapshot = record_with_digest(tampered_snapshot)
    tampered_input = replace(
        selector_input,
        selector_input_id="",
        feature_snapshot_id=tampered_snapshot.feature_snapshot_id,
        pre_origin_result_ids=(tampered_result.result_id,),
        pre_origin_result_digests=(tampered_result.result_digest,),
        leakage_policy_digest=tampered_snapshot.leakage_policy_digest,
        feature_records_digest=tampered_snapshot.feature_records_digest,
        feature_snapshot_lint_status=tampered_snapshot.leakage_lint_status,
        selector_input_digest="",
    )
    tampered_input = replace(
        tampered_input,
        selector_input_id=make_selector_input_id(tampered_input),
    )
    tampered_input = record_with_digest(tampered_input)
    tampered_selection = runner_module.selection_module.select_with_selector(
        tampered_input,
        tampered_snapshot,
        selector,
    )
    write_jsonl_records(store.path, (tampered_result,))
    write_jsonl_records(
        tmp_path / "feature-snapshots.jsonl",
        (tampered_snapshot,),
    )
    write_jsonl_records(tmp_path / "selector-inputs.jsonl", (tampered_input,))
    write_jsonl_records(tmp_path / "selections.jsonl", (tampered_selection,))

    original_pool_loader = runner_module._load_task_pool_records
    pool_reads = 0

    def guarded_pool_read(*args, **kwargs):
        nonlocal pool_reads
        pool_reads += 1
        if pool_reads > allowed_pool_reads:
            raise AssertionError(
                "Result cache identity replay must precede later supply reads"
            )
        return original_pool_loader(*args, **kwargs)

    monkeypatch.setattr(runner_module, "_load_task_pool_records", guarded_pool_read)

    with pytest.raises(ValueError, match=expected_error):
        runner_module.evaluate_prospective_selection(
            tampered_selection.selection_id,
            task_pool,
            task_pool,
            (agent,),
            store,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert selection.selection_id != tampered_selection.selection_id
    assert pool_reads == allowed_pool_reads


def test_evaluate_selectors_freezes_all_selections_then_executes_union_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_task = _task("first-task", "first-check", available_at="2026-01-02T00:00:00Z")
    second_task = _task(
        "second-task", "second-check", available_at="2026-01-03T00:00:00Z"
    )
    future_task = _task(
        "future-task", "future-check", available_at="2026-01-07T00:00:00Z"
    )
    tasks = (first_task, second_task, future_task)
    checks = tuple(
        _check(
            task.check_ids[0],
            task.task_id,
            available_at=task.task_material_available_at,
        )
        for task in tasks
    )
    task_pool = _task_pool_with_refs(tmp_path, tasks, checks)
    selectors = (
        build_rule_selector(
            "coverage",
            {"group_by_ref_key": {}},
            allowed_feature_classes=("task_metadata",),
        ),
        build_rule_selector(
            "recency",
            allowed_feature_classes=("task_metadata",),
        ),
    )
    store = ResultStore(tmp_path / "results.jsonl")
    executed_cells: list[tuple[str, str, str]] = []

    def fake_run(task, check, agent, workspace_config, runtime_config, run_context):
        logged = load_jsonl_records(
            tmp_path / "selections.jsonl", BenchmarkSelectionRecord
        )
        assert len(logged) == 2
        assert not (tmp_path / "evaluation-cell-sets.jsonl").exists()
        executed_cells.append((agent.agent_id, task.task_id, check.check_id))
        return _workspace_run(task, check, agent)

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        fake_run,
    )
    arguments = (
        selectors,
        task_pool,
        (_agent(),),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
        SelectorEvaluationConfig(
            origin_times=("2026-01-05T00:00:00Z",),
            budget=SelectionBudget(2),
        ),
        RollingOriginPolicy(
            "origin_time",
            "counterfactual_replay",
            "allow_cluster_overlap",
            True,
        ),
        FeatureConfig(("task_count",)),
        store,
        _workspace_config(),
        _runtime_config(),
        _scoring_config(),
        ResultCacheConfig(),
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )

    first_run = evaluate_selectors(*arguments)
    selections, cell_sets, matrices, _ = first_run

    assert tuple(selection.selector_id for selection in selections) == tuple(
        selector.selector_id for selector in selectors
    )
    assert tuple(selection.selected_task_check_refs for selection in selections) == (
        (
            TaskCheckRef("first-task", "first-check"),
            TaskCheckRef("second-task", "second-check"),
        ),
        (
            TaskCheckRef("second-task", "second-check"),
            TaskCheckRef("first-task", "first-check"),
        ),
    )
    assert Counter(executed_cells) == Counter(
        {
            ("agent", "first-task", "first-check"): 1,
            ("agent", "second-task", "second-check"): 1,
            ("agent", "future-task", "future-check"): 1,
        }
    )
    assert tuple((cell.task_id, cell.check_id) for cell in cell_sets[0].cells) == (
        ("first-task", "first-check"),
        ("second-task", "second-check"),
        ("future-task", "future-check"),
    )
    assert tuple((cell.task_id, cell.check_id) for cell in cell_sets[1].cells) == (
        ("second-task", "second-check"),
        ("first-task", "first-check"),
        ("future-task", "future-check"),
    )
    future_matrices = tuple(
        matrix for matrix in matrices if matrix.matrix_role == "future_holdout"
    )
    assert len(future_matrices) == 2
    assert future_matrices[0].cells[0].result_digest == (
        future_matrices[1].cells[0].result_digest
    )

    resumed = evaluate_selectors(*arguments)

    assert resumed == first_run
    assert len(executed_cells) == 3


def test_evaluate_selectors_uses_late_observed_history_result_in_counterfactual_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history_task = _task(
        "history-task",
        "history-check",
        available_at="2026-01-02T00:00:00Z",
    )
    future_task = _task(
        "future-task",
        "future-check",
        available_at="2026-01-07T00:00:00Z",
    )
    tasks = (history_task, future_task)
    checks = tuple(
        _check(
            task.check_ids[0],
            task.task_id,
            available_at=task.task_material_available_at,
        )
        for task in tasks
    )
    task_pool = _task_pool_with_refs(tmp_path, tasks, checks)
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    store = ResultStore(tmp_path / "results.jsonl")
    history_result = _result(
        history_task,
        checks[0],
        agent,
        workspace_config,
        runtime_config,
        scoring_config,
    )
    assert parse_utc_timestamp(history_result.result_available_at) > parse_utc_timestamp(
        "2026-01-05T00:00:00Z"
    )
    store_result(history_result, store)
    executed_task_ids: list[str] = []

    def fake_run(task, check, selected_agent, workspace, runtime, run_context):
        executed_task_ids.append(task.task_id)
        return _workspace_run(task, check, selected_agent)

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        fake_run,
    )

    evaluate_selectors(
        (
            build_rule_selector(
                "recency",
                allowed_feature_classes=(
                    "task_metadata",
                    "pre_origin_result",
                ),
            ),
        ),
        task_pool,
        (agent,),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
        SelectorEvaluationConfig(
            origin_times=("2026-01-05T00:00:00Z",),
            budget=SelectionBudget(1),
        ),
        RollingOriginPolicy(
            "origin_time",
            "counterfactual_replay",
            "allow_cluster_overlap",
            True,
        ),
        FeatureConfig(("pre_origin_result_count",)),
        store,
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(),
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )

    (selector_input,) = load_jsonl_records(
        tmp_path / "selector-inputs.jsonl",
        SelectorInput,
    )
    assert selector_input.pre_origin_result_ids == (history_result.result_id,)
    assert executed_task_ids == [future_task.task_id]


def test_evaluate_selectors_reuses_frozen_input_after_lazy_counterfactual_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_task = _task(
        "first-task",
        "first-check",
        available_at="2026-01-02T00:00:00Z",
    )
    selected_task = _task(
        "selected-task",
        "selected-check",
        available_at="2026-01-03T00:00:00Z",
    )
    future_task = _task(
        "future-task",
        "future-check",
        available_at="2026-01-07T00:00:00Z",
    )
    tasks = (first_task, selected_task, future_task)
    checks = tuple(
        _check(
            task.check_ids[0],
            task.task_id,
            available_at=task.task_material_available_at,
        )
        for task in tasks
    )
    task_pool = _task_pool_with_refs(tmp_path, tasks, checks)
    executed_task_ids: list[str] = []

    def fake_run(task, check, agent, workspace, runtime, run_context):
        executed_task_ids.append(task.task_id)
        return _workspace_run(task, check, agent)

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        fake_run,
    )
    arguments = (
        (
            build_rule_selector(
                "recency",
                allowed_feature_classes=(
                    "task_metadata",
                    "pre_origin_result",
                ),
            ),
        ),
        task_pool,
        (_agent(),),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
        SelectorEvaluationConfig(
            origin_times=("2026-01-05T00:00:00Z",),
            budget=SelectionBudget(1),
        ),
        RollingOriginPolicy(
            "origin_time",
            "counterfactual_replay",
            "allow_cluster_overlap",
            True,
        ),
        FeatureConfig(("pre_origin_result_count",)),
        ResultStore(tmp_path / "results.jsonl"),
        _workspace_config(),
        _runtime_config(),
        _scoring_config(),
        ResultCacheConfig(),
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )

    first_run = evaluate_selectors(*arguments)
    (frozen_input,) = load_jsonl_records(
        tmp_path / "selector-inputs.jsonl",
        SelectorInput,
    )
    resumed = evaluate_selectors(*arguments)

    assert frozen_input.pre_origin_result_ids == ()
    assert resumed == first_run
    assert len(
        load_jsonl_records(tmp_path / "selector-inputs.jsonl", SelectorInput)
    ) == 1
    assert executed_task_ids == [selected_task.task_id, future_task.task_id]


def test_evaluation_cell_set_plan_duplicates_fail_before_store_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task(available_at="2026-01-02T00:00:00Z")
    check = _check(available_at="2026-01-02T00:00:00Z")
    task_pool = _task_pool((task,), (check,))
    ref = TaskCheckRef(task.task_id, check.check_id)
    origin = _origin(task_pool, ref, ref)
    selection = record_with_digest(
        replace(
            _selection(task_pool, ref),
            origin_id=origin.origin_id,
            selection_digest="",
        )
    )
    plan = runner_module._EvaluationCellSetPlan(
        selection=selection,
        origin=origin,
        future_task_pool_id=task_pool.task_pool_id,
        future_task_pool_digest=task_pool.task_pool_digest,
        future_task_check_refs=origin.future_holdout_task_check_refs,
        future_censored_task_check_refs=origin.future_censored_task_check_refs,
        tasks=(task,),
        checks={check.check_id: check},
    )

    def fail_if_store_is_read(*_args, **_kwargs):
        raise AssertionError("duplicate plans must fail before Result Store reads")

    monkeypatch.setattr(
        runner_module,
        "_load_existing_evaluation_cell_sets",
        fail_if_store_is_read,
    )

    with pytest.raises(ValueError, match="duplicate evaluation cell-set identity"):
        runner_module._resolve_evaluation_cell_sets(
            (plan, plan),
            (_agent(),),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultStore(tmp_path / "results.jsonl"),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )


@pytest.mark.parametrize("conflicting_digest", (False, True))
def test_evidence_append_rejects_duplicate_existing_ids(
    tmp_path: Path,
    conflicting_digest: bool,
) -> None:
    task = _task()
    check = _check()
    task_pool = _task_pool((task,), (check,))
    selection = _selection(
        task_pool,
        TaskCheckRef(task.task_id, check.check_id),
    )
    duplicate = (
        record_with_digest(
            replace(
                selection,
                budget_digest="conflicting-budget",
                selection_digest="",
            )
        )
        if conflicting_digest
        else selection
    )
    store = ResultStore(tmp_path / "results.jsonl")
    write_jsonl_records(tmp_path / "selections.jsonl", (selection, duplicate))

    with pytest.raises(
        ValueError,
        match=f"contains duplicate selection_id: {selection.selection_id}",
    ):
        runner_module._append_selection_record(selection, store)


def test_evaluate_selectors_preflights_reused_result_bindings_before_agent_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_task = _task("first-task", "first-check", available_at="2026-01-02T00:00:00Z")
    second_task = _task(
        "second-task", "second-check", available_at="2026-01-03T00:00:00Z"
    )
    future_task = _task(
        "future-task", "future-check", available_at="2026-01-07T00:00:00Z"
    )
    tasks = (first_task, second_task, future_task)
    checks = tuple(
        _check(
            task.check_ids[0],
            task.task_id,
            available_at=task.task_material_available_at,
        )
        for task in tasks
    )
    task_pool = _task_pool_with_refs(tmp_path, tasks, checks)
    coverage = build_rule_selector(
        "coverage",
        {"group_by_ref_key": {}},
        allowed_feature_classes=("task_metadata",),
    )
    recency = build_rule_selector(
        "recency",
        allowed_feature_classes=("task_metadata",),
    )
    store = ResultStore(tmp_path / "results.jsonl")
    executed_cells: list[tuple[str, str, str]] = []

    def fake_run(task, check, agent, workspace_config, runtime_config, run_context):
        executed_cells.append((agent.agent_id, task.task_id, check.check_id))
        return _workspace_run(task, check, agent)

    monkeypatch.setattr(runner_module.workspace_module, "run_agent_on_task", fake_run)

    def evaluate(selectors):
        return evaluate_selectors(
            selectors,
            task_pool,
            (_agent(),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
            SelectorEvaluationConfig(
                origin_times=("2026-01-05T00:00:00Z",),
                budget=SelectionBudget(1),
            ),
            RollingOriginPolicy(
                "origin_time",
                "counterfactual_replay",
                "allow_cluster_overlap",
                True,
            ),
            FeatureConfig(("task_count",)),
            store,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    _, (cell_set,), _, _ = evaluate((recency,))
    assert ("agent", "first-task", "first-check") not in executed_cells
    drifted = record_with_digest(
        replace(
            cell_set,
            cells=(replace(cell_set.cells[0], outcome="fail"), *cell_set.cells[1:]),
            cell_set_digest="",
        )
    )
    write_jsonl_records(tmp_path / "evaluation-cell-sets.jsonl", (drifted,))
    executed_cells.clear()

    with pytest.raises(ValueError, match="outcome"):
        evaluate((recency, coverage))

    assert executed_cells == []


def test_evaluate_selectors_matches_cached_sequential_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tasks = (
        _task("first-task", "first-check", available_at="2026-01-02T00:00:00Z"),
        _task("second-task", "second-check", available_at="2026-01-03T00:00:00Z"),
        _task("future-task", "future-check", available_at="2026-01-07T00:00:00Z"),
    )
    checks = tuple(
        _check(
            task.check_ids[0],
            task.task_id,
            available_at=task.task_material_available_at,
        )
        for task in tasks
    )
    task_pool = _task_pool_with_refs(tmp_path, tasks, checks)
    monkeypatch.setattr(
        "barcarolle.selection.algorithms._now",
        lambda: "2026-01-20T00:00:00Z",
    )
    monkeypatch.setattr(
        "barcarolle.selection.evaluation._now",
        lambda: "2026-01-20T00:00:00Z",
    )
    monkeypatch.setattr(
        runner_module.result_store_module,
        "_now",
        lambda: "2026-01-20T00:00:00Z",
    )
    selectors = (
        build_rule_selector(
            "coverage",
            {"group_by_ref_key": {}},
            allowed_feature_classes=("task_metadata",),
        ),
        build_rule_selector(
            "recency",
            allowed_feature_classes=("task_metadata",),
        ),
    )
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    agent = _agent()
    cached_results = tuple(
        _result(
            task,
            check,
            agent,
            workspace_config,
            runtime_config,
            scoring_config,
        )
        for task, check in zip(tasks, checks, strict=True)
    )
    stores = tuple(
        ResultStore(tmp_path / label / "results.jsonl")
        for label in ("plural", "coverage", "recency")
    )
    for store in stores:
        for result in cached_results:
            store_result(result, store)

    def fail_if_workspace_runs(*args, **kwargs):
        raise AssertionError("the sequential equivalence test is cache-only")

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        fail_if_workspace_runs,
    )

    def shared_arguments(store: ResultStore):
        return (
            task_pool,
            (agent,),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
            SelectorEvaluationConfig(
                origin_times=("2026-01-05T00:00:00Z",),
                budget=SelectionBudget(2),
            ),
            RollingOriginPolicy(
                "origin_time",
                "counterfactual_replay",
                "allow_cluster_overlap",
                True,
            ),
            FeatureConfig(("task_count",)),
            store,
            workspace_config,
            runtime_config,
            scoring_config,
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    plural = evaluate_selectors(selectors, *shared_arguments(stores[0]))
    sequential = tuple(
        evaluate_selector(selector, *shared_arguments(store))
        for selector, store in zip(selectors, stores[1:], strict=True)
    )

    selection_offset = 0
    cell_offset = 0
    matrix_offset = 0
    metric_offset = 0
    for singleton in sequential:
        singleton_selections, singleton_cells, singleton_matrices, singleton_metrics = (
            singleton
        )
        assert (
            plural[0][selection_offset : selection_offset + len(singleton_selections)]
            == singleton_selections
        )
        assert plural[1][cell_offset : cell_offset + len(singleton_cells)] == (
            singleton_cells
        )
        assert (
            plural[2][matrix_offset : matrix_offset + len(singleton_matrices)]
            == singleton_matrices
        )
        assert (
            plural[3][metric_offset : metric_offset + len(singleton_metrics)]
            == singleton_metrics
        )
        selection_offset += len(singleton_selections)
        cell_offset += len(singleton_cells)
        matrix_offset += len(singleton_matrices)
        metric_offset += len(singleton_metrics)


def test_evaluate_selectors_resumes_union_after_partial_execution_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history_task = _task(available_at="2026-01-02T00:00:00Z")
    future_task = _task(
        "future-task", "future-check", available_at="2026-01-07T00:00:00Z"
    )
    history_check = _check(available_at="2026-01-02T00:00:00Z")
    future_check = _check(
        "future-check", "future-task", available_at="2026-01-07T00:00:00Z"
    )
    task_pool = _task_pool_with_refs(
        tmp_path,
        (history_task, future_task),
        (history_check, future_check),
    )
    store = ResultStore(tmp_path / "results.jsonl")
    attempts: Counter[tuple[str, str]] = Counter()

    def flaky_run(task, check, agent, workspace_config, runtime_config, run_context):
        key = (task.task_id, check.check_id)
        attempts[key] += 1
        if task.task_id == "future-task" and attempts[key] == 1:
            raise RuntimeError("injected execution interruption")
        return _workspace_run(task, check, agent)

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        flaky_run,
    )
    arguments = (
        (build_rule_selector("recency", allowed_feature_classes=("task_metadata",)),),
        task_pool,
        (_agent(),),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
        SelectorEvaluationConfig(
            origin_times=("2026-01-05T00:00:00Z",),
            budget=SelectionBudget(1),
        ),
        RollingOriginPolicy(
            "origin_time",
            "counterfactual_replay",
            "allow_cluster_overlap",
            True,
        ),
        FeatureConfig(("task_count",)),
        store,
        _workspace_config(),
        _runtime_config(),
        _scoring_config(),
        ResultCacheConfig(),
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )

    with pytest.raises(RuntimeError, match="injected execution interruption"):
        evaluate_selectors(*arguments)

    assert len(load_results(store, ResultQuery())) == 1
    assert not (tmp_path / "evaluation-cell-sets.jsonl").exists()
    completed = evaluate_selectors(*arguments)

    assert len(completed[1]) == 1
    assert attempts[("task", "check")] == 1
    assert attempts[("future-task", "future-check")] == 2


def test_runner_trains_and_reloads_fitted_selector_from_persisted_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tasks = (
        _task("first-task", "first-check", available_at="2026-01-02T00:00:00Z"),
        _task("second-task", "second-check", available_at="2026-01-03T00:00:00Z"),
        _task("future-task", "future-check", available_at="2026-01-07T00:00:00Z"),
    )
    checks = tuple(
        _check(
            task.check_ids[0],
            task.task_id,
            available_at=task.task_material_available_at,
        )
        for task in tasks
    )
    task_pool = _task_pool_with_refs(tmp_path, tasks, checks)
    experts = (
        build_rule_selector(
            "coverage",
            {"group_by_ref_key": {}},
            allowed_feature_classes=("task_metadata",),
        ),
        build_rule_selector(
            "random",
            {"seed": 7},
            allowed_feature_classes=("task_metadata",),
        ),
        build_rule_selector(
            "recency",
            allowed_feature_classes=("task_metadata",),
        ),
    )
    store = ResultStore(tmp_path / "results.jsonl")
    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        lambda task, check, agent, workspace_config, runtime_config, run_context: (
            _workspace_run(task, check, agent)
        ),
    )
    selections, _, _, _ = evaluate_selectors(
        experts,
        task_pool,
        (_agent(),),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
        SelectorEvaluationConfig(
            origin_times=("2026-01-05T00:00:00Z",),
            budget=SelectionBudget(1),
        ),
        RollingOriginPolicy(
            "origin_time",
            "counterfactual_replay",
            "allow_cluster_overlap",
            True,
        ),
        FeatureConfig(("task_count",)),
        store,
        _workspace_config(),
        _runtime_config(),
        _scoring_config(),
        ResultCacheConfig(),
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )
    deployment_origin = runner_module.selection_module.build_rolling_origin(
        task_pool,
        tasks,
        {check.check_id: check for check in checks},
        datetime(2026, 1, 11, tzinfo=UTC),
        TimeRange("2026-01-11T00:00:00Z", "2026-01-12T00:00:00Z"),
        RollingOriginPolicy(
            "origin_time",
            "counterfactual_replay",
            "allow_cluster_overlap",
            True,
        ),
    )
    selection_ids = tuple(selection.selection_id for selection in selections)

    fitted = train_selector(
        "rule_mixture",
        deployment_origin=deployment_origin,
        task_pool=task_pool,
        expert_selectors=experts,
        training_selection_ids=selection_ids,
        result_store=store,
    )
    resumed = train_selector(
        "rule_mixture",
        deployment_origin=deployment_origin,
        task_pool=task_pool,
        expert_selectors=experts,
        training_selection_ids=selection_ids,
        result_store=store,
    )

    assert fitted.selector_family == "rule_mixture"
    assert resumed == fitted
    logged = load_jsonl_records(tmp_path / "selectors.jsonl", SelectorRecord)
    assert tuple(selector.selector_id for selector in logged) == (
        *(expert.selector_id for expert in experts),
        fitted.selector_id,
    )
    (snapshot,) = load_jsonl_records(
        tmp_path / "feature-snapshots.jsonl", FeatureSnapshotRecord
    )
    (selector_input,) = load_jsonl_records(
        tmp_path / "selector-inputs.jsonl", SelectorInput
    )
    replayed = runner_module.selection_module.select_with_selector(
        selector_input,
        snapshot,
        logged[-1],
    )
    assert replayed.selector_digest == fitted.selector_digest
    assert (
        load_jsonl_records(tmp_path / "origins.jsonl", RollingOriginRecord)[-1]
        == deployment_origin
    )


def test_prepare_evaluation_cells_reuses_persisted_missing_cell_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    selected_task = _task(
        "selected-task", "selected-check", available_at="2026-01-02T00:00:00Z"
    )
    future_task = _task(
        "future-task", "future-check", available_at="2026-01-07T00:00:00Z"
    )
    selected_check = _check(
        "selected-check", "selected-task", available_at="2026-01-02T00:00:00Z"
    )
    future_check = _check(
        "future-check", "future-task", available_at="2026-01-07T00:00:00Z"
    )
    task_pool_bundle = _task_pool_bundle(
        (selected_task, future_task), (selected_check, future_check)
    )
    task_pool = task_pool_bundle.task_pool
    selected_ref = TaskCheckRef("selected-task", "selected-check")
    origin = _origin(
        task_pool,
        selected_ref,
        TaskCheckRef("future-task", "future-check"),
    )
    store = ResultStore(tmp_path / "results.jsonl")
    selection, _ = _persist_replayable_selection(
        task_pool_bundle,
        selected_ref,
        (_agent(),),
        store,
        origin=origin,
    )
    monkeypatch.setattr(
        runner_module.result_store_module,
        "find_missing_results",
        lambda *args, **kwargs: (),
    )

    first = prepare_evaluation_cells(
        selection,
        origin,
        task_pool_bundle,
        (_agent(),),
        _workspace_config(),
        _runtime_config(),
        _scoring_config(),
        ResultCacheConfig(),
        store,
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )
    assert first.abstention_reason == "missing_required_results"

    def fail_if_resolved_again(*args, **kwargs):
        raise AssertionError("persisted missing cell set must be reused")

    monkeypatch.setattr(
        runner_module.result_store_module,
        "find_missing_results",
        fail_if_resolved_again,
    )

    resumed = prepare_evaluation_cells(
        selection,
        origin,
        task_pool_bundle,
        (_agent(),),
        _workspace_config(),
        _runtime_config(),
        _scoring_config(),
        ResultCacheConfig(),
        store,
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )

    assert resumed == first


def test_evaluate_selectors_preflights_later_selector_before_agent_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history_task = _task(available_at="2026-01-02T00:00:00Z")
    future_task = _task(
        "future-task", "future-check", available_at="2026-01-07T00:00:00Z"
    )
    history_check = _check(available_at="2026-01-02T00:00:00Z")
    future_check = _check(
        "future-check", "future-task", available_at="2026-01-07T00:00:00Z"
    )
    task_pool = _task_pool_with_refs(
        tmp_path,
        (history_task, future_task),
        (history_check, future_check),
    )
    invalid_parameters: dict[str, object] = {}
    invalid_selector = record_with_digest(
        SelectorRecord(
            selector_id="invalid-random-selector",
            selector_family="random",
            selector_version="1",
            training_source_digests=(),
            allowed_feature_classes=("task_metadata",),
            parameters=invalid_parameters,
            config_digest=canonical_digest(
                {
                    "selector_family": "random",
                    "parameters": invalid_parameters,
                }
            ),
            created_at="2026-01-04T00:00:00Z",
            selector_digest="",
        )
    )

    def fail_if_agent_runs(*args, **kwargs):
        raise AssertionError("all selectors must be frozen before Agent execution")

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        fail_if_agent_runs,
    )

    with pytest.raises(ValueError, match="seed"):
        evaluate_selectors(
            (
                build_rule_selector(
                    "recency", allowed_feature_classes=("task_metadata",)
                ),
                invalid_selector,
            ),
            task_pool,
            (_agent(),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
            SelectorEvaluationConfig(
                origin_times=("2026-01-05T00:00:00Z",),
                budget=SelectionBudget(1),
            ),
            RollingOriginPolicy(
                "origin_time",
                "counterfactual_replay",
                "allow_cluster_overlap",
                True,
            ),
            FeatureConfig(("task_count",)),
            ResultStore(tmp_path / "results.jsonl"),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert not (tmp_path / "selections.jsonl").exists()
    assert not (tmp_path / "selectors.jsonl").exists()
    assert not (tmp_path / "origins.jsonl").exists()


def test_score_selection_uses_exact_result_binding_frozen_in_evaluation_cells(
    tmp_path: Path,
) -> None:
    selected_task = _task(
        "selected-task", "selected-check", available_at="2026-01-02T00:00:00Z"
    )
    future_task = _task(
        "future-task", "future-check", available_at="2026-01-07T00:00:00Z"
    )
    selected_check = _check(
        "selected-check", "selected-task", available_at="2026-01-02T00:00:00Z"
    )
    future_check = _check(
        "future-check", "future-task", available_at="2026-01-07T00:00:00Z"
    )
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    store = ResultStore(tmp_path / "results.jsonl")
    selected_pass = _result(
        selected_task,
        selected_check,
        agent,
        workspace_config,
        runtime_config,
        scoring_config,
    )
    future_pass = _result(
        future_task,
        future_check,
        agent,
        workspace_config,
        runtime_config,
        scoring_config,
    )
    store_result(selected_pass, store)
    store_result(future_pass, store)
    task_pool_bundle = _task_pool_bundle(
        (selected_task, future_task), (selected_check, future_check)
    )
    task_pool = task_pool_bundle.task_pool
    selected_ref = TaskCheckRef("selected-task", "selected-check")
    future_ref = TaskCheckRef("future-task", "future-check")
    origin = _origin(task_pool, selected_ref, future_ref)
    selection, _ = _persist_replayable_selection(
        task_pool_bundle,
        selected_ref,
        (agent,),
        store,
        origin=origin,
    )
    cell_set = prepare_evaluation_cells(
        selection,
        origin,
        task_pool_bundle,
        (agent,),
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(),
        store,
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )
    selected_fail = _result(
        selected_task,
        selected_check,
        agent,
        workspace_config,
        runtime_config,
        scoring_config,
        outcome="fail",
    )
    store_result(selected_fail, store)

    drifted_cell_set = record_with_digest(
        replace(
            cell_set,
            cells=(replace(cell_set.cells[0], outcome="fail"), *cell_set.cells[1:]),
            cell_set_digest="",
        )
    )
    with pytest.raises(ValueError, match="outcome"):
        score_selection(
            selection,
            origin,
            task_pool_bundle,
            (agent,),
            drifted_cell_set,
            store,
            ResultJoinConfig(),
        )

    _, selected_matrix, _, _ = score_selection(
        selection,
        origin,
        task_pool_bundle,
        (agent,),
        cell_set,
        store,
        ResultJoinConfig(),
    )

    assert selected_pass.result_id != selected_fail.result_id
    assert selected_matrix.cells[0].result_id == selected_pass.result_id
    assert selected_matrix.cells[0].result_digest == selected_pass.result_digest
    assert selected_matrix.cells[0].outcome == "pass"


@pytest.mark.parametrize(
    ("origin_times", "message"),
    (
        ((), "must not be empty"),
        (
            ("2026-01-05T00:00:00",),
            "timezone-aware ISO datetime strings",
        ),
        (
            ("2026-01-05T00:00:00Z", "2026-01-04T19:00:00-05:00"),
            "must be strictly increasing UTC instants",
        ),
        (
            ("2026-01-06T00:00:00Z", "2026-01-05T00:00:00Z"),
            "must be strictly increasing UTC instants",
        ),
    ),
)
def test_evaluate_selector_rejects_invalid_origin_schedule_before_writes(
    tmp_path: Path,
    monkeypatch,
    origin_times: tuple[str, ...],
    message: str,
) -> None:
    task = _task()
    check = _check()
    task_pool = _task_pool_with_refs(tmp_path, (task,), (check,))
    result_store = ResultStore(tmp_path / "results.jsonl")

    def fail_if_results_are_loaded(*args, **kwargs):
        raise AssertionError(
            "invalid origin schedules must be rejected before result queries"
        )

    monkeypatch.setattr(
        runner_module.result_store_module, "load_results", fail_if_results_are_loaded
    )

    with pytest.raises(ValueError, match=message):
        evaluate_selector(
            _selector(),
            task_pool,
            (_agent(),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
            SelectorEvaluationConfig(
                origin_times=origin_times,
                budget=SelectionBudget(1),
            ),
            RollingOriginPolicy(
                "origin_time",
                "counterfactual_replay",
                "allow_cluster_overlap",
                True,
            ),
            FeatureConfig(("task_count",)),
            result_store,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert not (tmp_path / "selections.jsonl").exists()
    assert not (tmp_path / "metrics.jsonl").exists()
    assert not result_store.path.exists()


def test_evaluate_selector_assigns_each_future_task_to_one_origin(
    tmp_path: Path, monkeypatch
) -> None:
    history_task = _task(
        "history-task", "history-check", available_at="2026-01-02T00:00:00Z"
    )
    first_future_task = _task(
        "first-future-task", "first-future-check", available_at="2026-01-06T00:00:00Z"
    )
    boundary_task = _task(
        "boundary-task", "boundary-check", available_at="2026-01-07T00:00:00Z"
    )
    second_future_task = _task(
        "second-future-task", "second-future-check", available_at="2026-01-08T00:00:00Z"
    )
    history_check = _check(
        "history-check", "history-task", available_at="2026-01-02T00:00:00Z"
    )
    first_future_check = _check(
        "first-future-check",
        "first-future-task",
        available_at="2026-01-06T00:00:00Z",
    )
    boundary_check = _check(
        "boundary-check",
        "boundary-task",
        available_at="2026-01-07T00:00:00Z",
    )
    second_future_check = _check(
        "second-future-check",
        "second-future-task",
        available_at="2026-01-08T00:00:00Z",
    )
    task_pool = _task_pool_with_refs(
        tmp_path,
        (history_task, first_future_task, boundary_task, second_future_task),
        (history_check, first_future_check, boundary_check, second_future_check),
    )

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        lambda task, check, agent, workspace_config, runtime_config, run_context: (
            _workspace_run(task, check, agent)
        ),
    )

    result_store = ResultStore(tmp_path / "results.jsonl")
    selection_snapshot_queries = []
    original_load_results = runner_module.result_store_module.load_results

    def track_selection_snapshot(store, query):
        if (
            query.agent_ids == ("agent",)
            and query.result_available_after is None
            and query.result_available_before is None
            and query.task_ids == task_pool.task_ids
            and query.check_ids == task_pool.check_ids
        ):
            selection_snapshot_queries.append(query)
        return original_load_results(store, query)

    monkeypatch.setattr(
        runner_module.result_store_module,
        "load_results",
        track_selection_snapshot,
    )
    selections, cell_sets, matrices, metrics = evaluate_selector(
        build_rule_selector(
            "recency",
            allowed_feature_classes=(
                "task_metadata",
                "pre_origin_result",
            ),
        ),
        task_pool,
        (_agent(),),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
        SelectorEvaluationConfig(
            origin_times=("2026-01-05T00:00:00Z", "2026-01-07T00:00:00Z"),
            budget=SelectionBudget(1),
        ),
        RollingOriginPolicy(
            "origin_time",
            "counterfactual_replay",
            "allow_cluster_overlap",
            True,
        ),
        FeatureConfig(("pre_origin_result_count",)),
        result_store,
        _workspace_config(),
        _runtime_config(),
        _scoring_config(),
        ResultCacheConfig(),
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )

    assert len(selection_snapshot_queries) == 1
    assert selection_snapshot_queries[0].result_available_before is None
    assert tuple(cell_set.future_task_check_refs for cell_set in cell_sets) == (
        (
            TaskCheckRef("first-future-task", "first-future-check"),
            TaskCheckRef("boundary-task", "boundary-check"),
        ),
        (TaskCheckRef("second-future-task", "second-future-check"),),
    )
    assert selections[1].selected_task_check_refs == (
        TaskCheckRef("boundary-task", "boundary-check"),
    )
    assert load_jsonl_records(
        tmp_path / "evaluation-cell-sets.jsonl",
        EvaluationCellSet,
    ) == list(cell_sets)
    assert load_jsonl_records(
        tmp_path / "result-matrices.jsonl",
        ResultMatrix,
    ) == list(matrices)
    origins = load_jsonl_records(tmp_path / "origins.jsonl", RollingOriginRecord)
    snapshots = load_jsonl_records(
        tmp_path / "feature-snapshots.jsonl",
        FeatureSnapshotRecord,
    )
    selector_inputs = load_jsonl_records(
        tmp_path / "selector-inputs.jsonl",
        SelectorInput,
    )
    selectors = load_jsonl_records(tmp_path / "selectors.jsonl", SelectorRecord)
    stored_results = tuple(load_results(result_store, ResultQuery()))
    write_report(
        task_pool,
        selections,
        stored_results,
        cell_sets,
        matrices,
        metrics,
        ReportConfig(
            tmp_path / "report",
            agents=(_agent(),),
            artifact_root=tmp_path,
        ),
        origins=origins,
        feature_snapshots=snapshots,
        selector_inputs=selector_inputs,
        selectors=selectors,
    )
    report = json.loads((tmp_path / "report" / "report.json").read_text())
    selector_section = next(
        section for section in report if section["section_id"] == "selector_performance"
    )
    claim_section = next(
        section for section in report if section["section_id"] == "claim_boundary"
    )
    assert selector_section["unsupported_claims"] == []
    assert selector_section["supported_claims"] == [
        "counterfactual_replay_selector_performance_summary"
    ]
    assert selector_section["summary"]["mae_summary"] is not None
    cohorts_by_origin = {
        row["origin_id"]: row for row in selector_section["summary"]["origin_cohorts"]
    }
    first_cohort = cohorts_by_origin[origins[0].origin_id]
    assert first_cohort["arrival_cohort_count"] == 2
    assert first_cohort["legacy_label_time_cohort_count"] == 2
    assert first_cohort["shared_cohort_count"] == 2
    assert "selector_metrics" in claim_section["supported_claims"]

    tampered_cases = {
        "future refs": (
            (
                record_with_digest(
                    replace(
                        origins[0],
                        future_holdout_task_check_refs=(),
                        origin_digest="",
                    )
                ),
                *origins[1:],
            ),
            tuple(selector_inputs),
        ),
        "policy": (
            (
                record_with_digest(
                    replace(
                        origins[0],
                        holdout_overlap_policy="disjoint_clusters",
                        origin_digest="",
                    )
                ),
                *origins[1:],
            ),
            tuple(selector_inputs),
        ),
        "Agent candidates": (
            tuple(origins),
            (
                record_with_digest(
                    replace(
                        selector_inputs[0],
                        agent_ids=("other-agent",),
                        selector_input_digest="",
                    )
                ),
                *selector_inputs[1:],
            ),
        ),
        "pre-origin denominator": (
            tuple(origins),
            (
                record_with_digest(
                    replace(
                        selector_inputs[0],
                        pre_origin_result_ids=("missing-result",),
                        pre_origin_result_digests=("missing-result-digest",),
                        selector_input_digest="",
                    )
                ),
                *selector_inputs[1:],
            ),
        ),
    }
    for label, (case_origins, case_inputs) in tampered_cases.items():
        section = runner_module.reporting_module.build_selector_report(
            selections,
            cell_sets,
            matrices,
            metrics,
            origins=case_origins,
            feature_snapshots=snapshots,
            selector_inputs=case_inputs,
            selectors=selectors,
            agents=(_agent(),),
            results=stored_results,
        )
        assert section.supported_claims == (), label
        assert section.unsupported_claims, label

    provenance_input = selector_inputs[-1]
    missing_result_input = replace(
        provenance_input,
        pre_origin_result_ids=("missing-result",),
        pre_origin_result_digests=("missing-result-digest",),
    )
    missing_result_section = runner_module.reporting_module.build_selector_report(
        selections,
        cell_sets,
        matrices,
        metrics,
        origins=origins,
        feature_snapshots=snapshots,
        selector_inputs=tuple(
            missing_result_input
            if selector_input.selector_input_id == provenance_input.selector_input_id
            else selector_input
            for selector_input in selector_inputs
        ),
        selectors=selectors,
        agents=(_agent(),),
        results=stored_results,
    )
    assert any(
        "references missing Result missing-result" in error
        for error in missing_result_section.unsupported_claims
    )

    provenance_snapshot = next(
        snapshot
        for snapshot in snapshots
        if snapshot.feature_snapshot_id == provenance_input.feature_snapshot_id
    )
    mismatched_view_snapshot = replace(
        provenance_snapshot,
        result_view_digest="mismatched-result-view",
    )
    mismatched_view_section = runner_module.reporting_module.build_selector_report(
        selections,
        cell_sets,
        matrices,
        metrics,
        origins=origins,
        feature_snapshots=tuple(
            mismatched_view_snapshot
            if snapshot.feature_snapshot_id == provenance_snapshot.feature_snapshot_id
            else snapshot
            for snapshot in snapshots
        ),
        selector_inputs=selector_inputs,
        selectors=selectors,
        agents=(_agent(),),
        results=stored_results,
    )
    assert any(
        "Result view does not match selector input" in error
        for error in mismatched_view_section.unsupported_claims
    )

    eligible_keys = {
        (ref.task_id, ref.check_id) for ref in provenance_input.eligible_task_check_refs
    }
    post_origin_result = next(
        result
        for result in stored_results
        if (result.task_id, result.check_id) in eligible_keys
    )
    post_origin_input = replace(
        provenance_input,
        pre_origin_result_ids=(post_origin_result.result_id,),
        pre_origin_result_digests=(post_origin_result.result_digest,),
    )
    post_origin_result_section = runner_module.reporting_module.build_selector_report(
        selections,
        cell_sets,
        matrices,
        metrics,
        origins=origins,
        feature_snapshots=snapshots,
        selector_inputs=tuple(
            post_origin_input
            if selector_input.selector_input_id == provenance_input.selector_input_id
            else selector_input
            for selector_input in selector_inputs
        ),
        selectors=selectors,
        agents=(_agent(),),
        results=stored_results,
    )
    assert not any(
        f"includes post-origin Result {post_origin_result.result_id}" in error
        for error in post_origin_result_section.unsupported_claims
    )
    strict_post_origin_input = replace(
        post_origin_input,
        eligibility_mode="strict_prospective",
    )
    strict_post_origin_section = runner_module.reporting_module.build_selector_report(
        selections,
        cell_sets,
        matrices,
        metrics,
        origins=origins,
        feature_snapshots=snapshots,
        selector_inputs=tuple(
            strict_post_origin_input
            if selector_input.selector_input_id == provenance_input.selector_input_id
            else selector_input
            for selector_input in selector_inputs
        ),
        selectors=selectors,
        agents=(_agent(),),
        results=stored_results,
    )
    assert any(
        f"includes post-origin Result {post_origin_result.result_id}" in error
        for error in strict_post_origin_section.unsupported_claims
    )

    disallowed_selector = replace(selectors[0], allowed_feature_classes=())
    disallowed_feature_section = runner_module.reporting_module.build_selector_report(
        selections,
        cell_sets,
        matrices,
        metrics,
        origins=origins,
        feature_snapshots=snapshots,
        selector_inputs=selector_inputs,
        selectors=(disallowed_selector, *selectors[1:]),
        agents=(_agent(),),
        results=stored_results,
    )
    assert any(
        "uses classes not allowed by Selector: pre_origin_result" in error
        for error in disallowed_feature_section.unsupported_claims
    )


def test_selector_report_publishes_replayed_stratified_forecast_diagnostics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tasks = (
        _task(
            "history-a",
            "check-a",
            available_at="2026-01-02T00:00:00Z",
            sampling_stratum="a",
        ),
        _task(
            "history-b",
            "check-b",
            available_at="2026-01-03T00:00:00Z",
            sampling_stratum="b",
        ),
        _task(
            "future-b",
            "future-check-b",
            available_at="2026-01-06T00:00:00Z",
            sampling_stratum="b",
        ),
    )
    checks = tuple(
        _check(
            task.check_ids[0],
            task.task_id,
            available_at=task.task_material_available_at,
        )
        for task in tasks
    )
    task_pool = _task_pool_with_refs(tmp_path, tasks, checks)
    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        lambda task, check, agent, workspace_config, runtime_config, run_context: (
            _workspace_run(task, check, agent)
        ),
    )
    selector = build_rule_selector(
        "stratified_forecast",
        {
            "dirichlet_alpha": 1.0,
            "trailing_ref_count": 2,
            "seed": 7,
            "weight_cap": 3.0,
        },
        allowed_feature_classes=("task_metadata",),
    )
    result_store = ResultStore(tmp_path / "results.jsonl")

    selections, cell_sets, matrices, metrics = evaluate_selector(
        selector,
        task_pool,
        (_agent(),),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
        SelectorEvaluationConfig(
            origin_times=("2026-01-05T00:00:00Z",),
            budget=SelectionBudget(1),
        ),
        RollingOriginPolicy(
            "origin_time",
            "counterfactual_replay",
            "allow_cluster_overlap",
            True,
        ),
        FeatureConfig(("task_stratum",)),
        result_store,
        _workspace_config(),
        _runtime_config(),
        _scoring_config(),
        ResultCacheConfig(),
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )
    section = runner_module.reporting_module.build_selector_report(
        selections,
        cell_sets,
        matrices,
        metrics,
        origins=load_jsonl_records(tmp_path / "origins.jsonl", RollingOriginRecord),
        feature_snapshots=load_jsonl_records(
            tmp_path / "feature-snapshots.jsonl", FeatureSnapshotRecord
        ),
        selector_inputs=load_jsonl_records(
            tmp_path / "selector-inputs.jsonl", SelectorInput
        ),
        selectors=(selector,),
        agents=(_agent(),),
        results=tuple(load_results(result_store, ResultQuery())),
        task_pool=task_pool,
        artifact_root=tmp_path,
    )

    row = section.summary["stratified_forecasts"][0]
    assert row["selection_id"] == selections[0].selection_id
    assert row["forecast_proportions"] == {"a": 0.5, "b": 0.5}
    assert row["future_proportions"] == {"b": 1.0}
    assert row["forecast_proportion_tv_error"] == pytest.approx(0.5)
    assert row["unweighted_selected_proportion_tv_error"] == pytest.approx(1.0)
    assert row["effective_sample_size"] == pytest.approx(1.0)


def test_evaluate_selector_does_not_execute_censored_future_label(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history_task = _task(
        "history-task",
        "history-check",
        available_at="2026-01-02T00:00:00Z",
    )
    future_task = _task(
        "future-task",
        "future-check",
        available_at="2026-01-07T00:00:00Z",
    )
    history_check = _check(
        "history-check",
        "history-task",
        available_at="2026-01-02T00:00:00Z",
    )
    future_check = _check(
        "future-check",
        "future-task",
        available_at="2026-01-15T00:00:00Z",
    )
    task_pool = _task_pool_with_refs(
        tmp_path,
        (history_task, future_task),
        (history_check, future_check),
    )
    agent = _agent()
    workspace_config = _workspace_config()
    runtime_config = _runtime_config()
    scoring_config = _scoring_config()
    result_store = ResultStore(tmp_path / "results.jsonl")
    store_result(
        _result(
            history_task,
            history_check,
            agent,
            workspace_config,
            runtime_config,
            scoring_config,
        ),
        result_store,
    )

    def fail_if_executed(*args, **kwargs):
        raise AssertionError("censored labels must not enter the execution plan")

    monkeypatch.setattr(
        runner_module.workspace_module,
        "run_agent_on_task",
        fail_if_executed,
    )

    _, cell_sets, _, _ = evaluate_selector(
        _selector(),
        task_pool,
        (agent,),
        TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
        SelectorEvaluationConfig(
            origin_times=("2026-01-05T00:00:00Z",),
            budget=SelectionBudget(1),
        ),
        RollingOriginPolicy(
            "origin_time",
            "counterfactual_replay",
            "allow_cluster_overlap",
            True,
            maturity_lag_seconds=0,
        ),
        FeatureConfig(("task_count",)),
        result_store,
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(),
        ResultJoinConfig(),
        WorkspaceRunContext(),
    )

    origins = load_jsonl_records(tmp_path / "origins.jsonl", RollingOriginRecord)
    assert origins[0].future_holdout_task_check_refs == ()
    assert origins[0].future_censored_task_check_refs == (
        TaskCheckRef("future-task", "future-check"),
    )
    assert cell_sets[0].future_task_check_refs == ()


def test_evaluate_selector_rejects_repeated_future_cluster_across_disjoint_origins(
    tmp_path: Path,
) -> None:
    tasks = (
        _task(
            "history-task",
            "history-check",
            available_at="2026-01-02T00:00:00Z",
            dependency_cluster_id="history-cluster",
        ),
        _task(
            "first-future-task",
            "first-future-check",
            available_at="2026-01-06T00:00:00Z",
            dependency_cluster_id="repeated-cluster",
        ),
        _task(
            "second-future-task",
            "second-future-check",
            available_at="2026-01-08T00:00:00Z",
            dependency_cluster_id="repeated-cluster",
        ),
    )
    checks = tuple(
        _check(
            task.check_ids[0],
            task.task_id,
            available_at=task.task_material_available_at,
        )
        for task in tasks
    )
    task_pool = _task_pool_with_refs(tmp_path, tasks, checks)

    with pytest.raises(ValueError, match="history and future clusters overlap"):
        evaluate_selector(
            _selector(),
            task_pool,
            (_agent(),),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
            SelectorEvaluationConfig(
                origin_times=("2026-01-05T00:00:00Z", "2026-01-07T00:00:00Z"),
                budget=SelectionBudget(1),
            ),
            RollingOriginPolicy(
                "origin_time",
                "counterfactual_replay",
                "disjoint_clusters",
                True,
            ),
            FeatureConfig(("task_count",)),
            ResultStore(tmp_path / "results.jsonl"),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )


def test_evaluate_selector_freezes_counterfactual_result_snapshot_before_selection(
    tmp_path: Path, monkeypatch
) -> None:
    selected_task = _task(
        "selected-task", "selected-check", available_at="2026-01-02T00:00:00Z"
    )
    future_task = _task(
        "future-task", "future-check", available_at="2026-01-07T00:00:00Z"
    )
    selected_check = _check(
        "selected-check", "selected-task", available_at="2026-01-02T00:00:00Z"
    )
    future_check = _check(
        "future-check", "future-task", available_at="2026-01-07T00:00:00Z"
    )
    task_pool = _task_pool_with_refs(
        tmp_path,
        (selected_task, future_task),
        (selected_check, future_check),
    )
    agent = _agent()
    pre_origin_result = _redigest_result(
        _result(
            selected_task,
            selected_check,
            agent,
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
        ),
        started_at="2026-01-03T00:00:00Z",
        finished_at="2026-01-03T00:00:05Z",
        source_result_available_at="2026-01-04T00:00:00Z",
        result_available_at="2026-01-04T00:00:00Z",
    )
    freeze_called = False
    pre_freeze_queries = []
    captured_selector_inputs = []

    class StopAfterSelectionAppend(Exception):
        pass

    def fake_load_results(store, query):
        if not freeze_called:
            pre_freeze_queries.append(query)
            return (pre_origin_result,)
        return ()

    def fake_select(selector_input, snapshot, selector):
        nonlocal freeze_called
        freeze_called = True
        captured_selector_inputs.append(selector_input)
        return _selection_for_origin(
            task_pool,
            selector_input.eligible_task_check_refs[0],
            selector_input.origin_id,
            selector_input.budget_digest,
            selector_input.feature_snapshot_id,
        )

    def fake_prepare(selection_origins, *args, **kwargs):
        selection = selection_origins[0][0]
        logged = load_jsonl_records(
            tmp_path / "selections.jsonl", BenchmarkSelectionRecord
        )
        assert logged == [selection]
        assert (
            len(load_jsonl_records(tmp_path / "selectors.jsonl", SelectorRecord)) == 1
        )
        assert (
            len(load_jsonl_records(tmp_path / "origins.jsonl", RollingOriginRecord))
            == 1
        )
        snapshots = load_jsonl_records(
            tmp_path / "feature-snapshots.jsonl",
            FeatureSnapshotRecord,
        )
        assert len(snapshots) == 1
        assert snapshots[0].leakage_lint_status == "passed"
        assert (
            len(load_jsonl_records(tmp_path / "selector-inputs.jsonl", SelectorInput))
            == 1
        )
        raise StopAfterSelectionAppend

    monkeypatch.setattr(
        runner_module.result_store_module, "load_results", fake_load_results
    )
    monkeypatch.setattr(
        runner_module.selection_module, "select_with_selector", fake_select
    )
    monkeypatch.setattr(runner_module, "_prepare_evaluation_cell_sets", fake_prepare)

    with pytest.raises(StopAfterSelectionAppend):
        evaluate_selector(
            _selector(),
            task_pool,
            (agent,),
            TimeRange("2026-01-01T00:00:00Z", "2026-01-10T00:00:00Z"),
            SelectorEvaluationConfig(
                origin_times=("2026-01-05T00:00:00.500000Z",),
                budget=SelectionBudget(7),
            ),
            RollingOriginPolicy(
                "origin_time",
                "counterfactual_replay",
                "allow_cluster_overlap",
                True,
            ),
            FeatureConfig(("pre_origin_result_count",)),
            ResultStore(tmp_path / "results.jsonl"),
            _workspace_config(),
            _runtime_config(),
            _scoring_config(),
            ResultCacheConfig(),
            ResultJoinConfig(),
            WorkspaceRunContext(),
        )

    assert freeze_called
    assert pre_freeze_queries
    assert all(
        query.result_available_before is None
        and query.result_available_after is None
        and query.task_ids == task_pool.task_ids
        and query.check_ids == task_pool.check_ids
        for query in pre_freeze_queries
    )
    assert len(pre_freeze_queries) == 1
    assert captured_selector_inputs[0].budget_digest == canonical_digest(
        {"max_task_checks": 7}
    )
    assert captured_selector_inputs[0].selection_budget_limit == 7
    assert (
        captured_selector_inputs[0].origin_as_of_cutoff == "2026-01-05T00:00:00.500000Z"
    )


def test_write_report_writes_human_and_machine_summaries(tmp_path: Path) -> None:
    task = _task()
    check = _check()
    agent = _agent()
    result = _result(
        task, check, agent, _workspace_config(), _runtime_config(), _scoring_config()
    )
    task_pool = _task_pool((task,), (check,))

    summary = write_report(
        task_pool,
        (),
        (result,),
        (),
        (),
        (),
        ReportConfig(tmp_path, agents=(agent,)),
    )

    report_paths = summary["report_paths"]
    assert isinstance(report_paths, dict)
    markdown_path = Path(report_paths["markdown"])
    json_path = Path(report_paths["json"])
    assert markdown_path.exists()
    assert json_path.exists()
    assert summary["section_ids"] == (
        "task_pool",
        "agent_results",
        "selector_performance",
        "claim_boundary",
    )
    assert "task_pool_digest" in markdown_path.read_text(encoding="utf-8")


def test_report_cli_reads_relative_jsonl_paths_and_writes_reports(
    tmp_path: Path, capsys
) -> None:
    task = _task()
    check = _check()
    task_pool = _task_pool((task,), (check,))
    future_task_pool = _task_pool(
        (task,),
        (check,),
        task_pool_id="future-task-pool",
    )
    records = tmp_path / "records"
    write_jsonl_records(records / "task_pool.jsonl", (task_pool,))
    write_jsonl_records(
        records / "future-task-pools.jsonl",
        (future_task_pool,),
    )
    config_path = tmp_path / "report.json"
    config_path.write_text(
        canonical_json(
            {
                "task_pool": "records/task_pool.jsonl",
                "future_task_pools": "records/future-task-pools.jsonl",
                "output_dir": "published",
            }
        ),
        encoding="utf-8",
    )

    assert cli_main(("report", str(config_path))) == 0

    assert (tmp_path / "published" / "report.md").exists()
    assert (tmp_path / "published" / "report.json").exists()
    report = json.loads(
        (tmp_path / "published" / "report.json").read_text(encoding="utf-8")
    )
    claim_section = next(
        section for section in report if section["section_id"] == "claim_boundary"
    )
    selector_section = next(
        section for section in report if section["section_id"] == "selector_performance"
    )
    assert selector_section["source_digests"]["future_task_pool_digests"] == [
        future_task_pool.task_pool_digest
    ]
    assert any(
        claim.startswith("task_pool_bundle_internal_consistency:")
        for claim in claim_section["unsupported_claims"]
    )
    assert '"section_ids"' in capsys.readouterr().out


def _write_runner_prepared_package(
    root: Path,
    candidate: task_pool_module.TaskCandidate,
    reference_patch: CapturedDiff,
    check_command: tuple[str, ...],
    check_manifest: dict[str, object],
    hidden_material: Path,
) -> Path:
    artifacts = root / "artifacts"
    artifacts.mkdir(parents=True)
    (artifacts / "reference.patch").write_text(
        reference_patch.diff_text,
        encoding="utf-8",
    )
    (artifacts / "check-manifest.json").write_text(
        canonical_json(check_manifest),
        encoding="utf-8",
    )
    (artifacts / "hidden-check.txt").write_bytes(hidden_material.read_bytes())
    material = record_with_digest(
        PreparedCandidateMaterialRecord(
            candidate_id=candidate.candidate_id,
            reference_patch_ref="artifacts/reference.patch",
            reference_patch_digest=reference_patch.diff_digest,
            check_command=check_command,
            check_manifest_ref="artifacts/check-manifest.json",
            check_manifest_digest=canonical_digest(check_manifest),
            hidden_material_ref="artifacts/hidden-check.txt",
            hidden_material_digest=hidden_material_digest(
                artifacts / "hidden-check.txt"
            ),
            material_digest="",
        )
    )
    frame_event = record_with_digest(
        ObservedFrameEventRecord(
            source_event_id=make_source_event_id(
                candidate.repository_id,
                candidate.source_family,
                candidate.source_ref,
            ),
            repository_id=candidate.repository_id,
            source_family=candidate.source_family,
            source_ref=candidate.source_ref,
            observed_at="2026-01-31T00:00:00.000000Z",
            frame_event_digest="",
        )
    )
    behavior = {
        "generator_family": "fixture",
        "adapter_version": "1",
        "implementation_digest": "fixture-implementation",
        "behavior_config": {"strategy": "stable"},
    }
    protocol = {
        "source_kind": "issue",
        "target_definition": "fixture issue frame",
        "query_semantics": {"state": "resolved"},
        "sampling_policy": {"mode": "all"},
        "deduplication_policy": {"key": "source_ref"},
    }
    protocol_digest = canonical_digest(protocol)
    frame = {
        "frame_id": "fixture-frame",
        "source_protocol_digest": protocol_digest,
        "source_revision": "fixture-revision",
        "window_start": "2026-01-01T00:00:00.000000Z",
        "window_end": "2026-01-31T00:00:00.000000Z",
        "event_inventory_ref": "observed-frame-events.jsonl",
        "event_inventory_digest": canonical_digest((frame_event,)),
        "observation_authority": "producer_attested",
        "observation_receipt_digest": "fixture-receipt",
        "known_blind_spots": [],
        "coverage_mode": "one_source_event_per_frame_unit_v1",
    }
    run = {
        "run_id": "fixture-run",
        "producer_id": "fixture-producer",
        "authority_kind": "external_attested",
        "authority_digest": "fixture-authority",
        "started_at": "2026-01-31T00:00:00.000000Z",
        "finished_at": "2026-01-31T00:00:01.000000Z",
        "input_snapshot_digest": "fixture-input",
    }
    adapter = {"schema_version": "fixture_v1", "count": 1}
    manifest = record_with_digest(
        PreparedCandidatePackageManifest(
            schema_version=(task_pool_module.PREPARED_CANDIDATE_PACKAGE_SCHEMA_VERSION),
            repository_id=candidate.repository_id,
            candidate_records_ref="candidates.jsonl",
            candidate_records_digest=canonical_digest((candidate,)),
            excluded_source_event_records_ref="excluded-source-events.jsonl",
            excluded_source_event_records_digest=canonical_digest(()),
            material_records_ref="materials.jsonl",
            material_records_digest=canonical_digest((material,)),
            generator_behavior=behavior,
            generator_behavior_digest=canonical_digest(behavior),
            source_protocol=protocol,
            source_protocol_digest=protocol_digest,
            observed_frame=frame,
            observed_frame_digest=canonical_digest(frame),
            run=run,
            run_digest=canonical_digest(run),
            adapter_evidence_ref="adapter-evidence.jsonl",
            adapter_evidence_digest=canonical_digest(adapter),
            manifest_digest="",
        )
    )
    write_jsonl_records(root / "candidates.jsonl", (candidate,))
    write_jsonl_records(root / "excluded-source-events.jsonl", ())
    write_jsonl_records(root / "materials.jsonl", (material,))
    write_jsonl_records(root / "observed-frame-events.jsonl", (frame_event,))
    write_jsonl_records(root / "adapter-evidence.jsonl", (adapter,))
    manifest_path = root / "prepared-candidate-package.jsonl"
    write_jsonl_records(manifest_path, (manifest,))
    return manifest_path


def _write_result_source_bundle(
    root: Path,
    results: tuple[ResultRecord, ...],
    *,
    availability_semantics: str,
) -> Path:
    root.mkdir(parents=True)
    result_path = root / "results.jsonl"
    write_jsonl_records(result_path, results)
    manifest = record_with_digest(
        ResultSourceManifest(
            schema_version=(
                runner_module.result_store_module.RESULT_SOURCE_MANIFEST_SCHEMA_VERSION
            ),
            producer_id="fixture-producer",
            authority_digest="trusted-authority",
            result_records_ref="results.jsonl",
            result_records_digest=canonical_digest(results),
            availability_semantics=availability_semantics,
            created_at="2026-01-10T00:00:00.000000Z",
            manifest_digest="",
        )
    )
    manifest_path = root / "result-source-manifest.jsonl"
    write_jsonl_records(manifest_path, (manifest,))
    return manifest_path


def _candidate_event(**overrides: object) -> dict[str, object]:
    event: dict[str, object] = {
        "candidate_id": "candidate",
        "repository_id": "repo",
        "base_commit": "commit",
        "source_ref": "issue-1",
        "source_resolved_at": "2026-01-05T00:00:00Z",
        "task_material_available_at": "2026-01-05T00:00:00Z",
        "check_material_available_at": "2026-01-05T00:00:00Z",
        "task_text": "Fix the bug and make the test pass.",
        "solver_material_refs": (),
        "dependency_cluster_id": "dependency-cluster",
        "sampling_stratum": "stratum",
        "check_manifest_digest": "check-manifest",
        "hidden_check_bundle_digest": "hidden-bundle",
        "resource_limits": {"timeout_seconds": 30},
        "oracle_source": "private",
        "check_type": "tests",
    }
    event.update(overrides)
    return event


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def _task(
    task_id: str = "task",
    check_id: str = "check",
    available_at: str = "2026-01-02T00:00:00Z",
    dependency_cluster_id: str = "dependency-cluster",
    sampling_stratum: str = "stratum",
) -> TaskRecord:
    task_text = f"Task {task_id}"
    solver_material_refs = (f"path:{task_id}.md",)
    return TaskRecord(
        task_id=task_id,
        repository_id="repo",
        base_commit="a" * 40,
        source_family="user_import",
        source_ref=f"source-{task_id}",
        source_resolved_at=available_at,
        task_material_available_at=available_at,
        task_text=task_text,
        solver_material_digest=make_solver_material_digest(
            task_text, solver_material_refs
        ),
        solver_material_refs=solver_material_refs,
        check_ids=(check_id,),
        dependency_cluster_id=dependency_cluster_id,
        sampling_stratum=sampling_stratum,
    )


def _check(
    check_id: str = "check",
    task_id: str = "task",
    available_at: str = "2026-01-02T00:00:00Z",
) -> CheckRecord:
    return CheckRecord(
        check_id=check_id,
        task_id=task_id,
        check_type="tests",
        check_manifest_digest=f"manifest-{check_id}",
        hidden_check_bundle_digest=f"hidden-{check_id}",
        resource_limits={"timeout_seconds": 30},
        oracle_source="private",
        check_material_available_at=available_at,
    )


def _agent(agent_id: str = "agent", manifest: str = "agent-manifest") -> AgentRecord:
    return AgentRecord(
        agent_id=agent_id,
        agent_manifest_digest=manifest,
        requested_model_id="model",
        model_snapshot_id="model",
        model_resolution_scope_id=None,
        model_resolution_scope_started_at=None,
        model_resolution_scope_ended_at=None,
        harness_digest=f"harness-{agent_id}",
        repository_instruction_digest="instructions",
        prompt_digest="prompt",
        tools_digest="tools",
        retrieval_digest="retrieval",
        skills_digest="skills",
        network_policy_digest="network",
        adapter_digest="adapter",
    )


def _selector() -> SelectorRecord:
    parameters = {}
    return record_with_digest(
        SelectorRecord(
            selector_id="selector",
            selector_family="recency",
            selector_version="1",
            training_source_digests=("training",),
            allowed_feature_classes=("task_metadata",),
            parameters=parameters,
            config_digest=canonical_digest(
                {"selector_family": "recency", "parameters": parameters}
            ),
            created_at="2026-01-04T00:00:00Z",
            selector_digest="",
        )
    )


def _workspace_config() -> WorkspaceConfig:
    return WorkspaceConfig("workspace", "checkout", "submodules", "image", "deps")


def _runtime_config() -> RuntimeConfig:
    return RuntimeConfig("runtime", "budget", "retry", "stochastic", 30, None)


def _scoring_config() -> ScoringConfig:
    return ScoringConfig("test", {"input_tokens": 0.01})


def _workspace_run(
    task: TaskRecord, check: CheckRecord, agent: AgentRecord, outcome: str = "pass"
) -> WorkspaceRunRecord:
    return WorkspaceRunRecord(
        workspace_run_id=f"workspace-run-{task.task_id}-{check.check_id}-{agent.agent_id}-{outcome}",
        task_id=task.task_id,
        check_id=check.check_id,
        agent_id=agent.agent_id,
        solver_workspace_digest="solver-workspace",
        verifier_workspace_digest="verifier-workspace",
        terminal_status="passed" if outcome == "pass" else "failed",
        diff_digest="diff",
        replay_status="applied",
        check_outcome=outcome,
        invalid_owner=None,
        failure_label=None,
        usage={"input_tokens": 10},
        latency={
            "workspace_seconds": 5.0,
            "agent_seconds": 2.0,
            "verification_seconds": 1.0,
            "solver_checkout_seconds": 0.5,
            "verifier_checkout_seconds": 0.5,
            "diff_replay_seconds": 0.25,
            "cleanup_seconds": 0.25,
        },
        started_at="2026-01-10T00:00:00Z",
        finished_at="2026-01-10T00:00:05Z",
    )


def _result(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: ScoringConfig,
    outcome: str = "pass",
):
    identity = compute_result_cache_identity(
        task, check, agent, workspace_config, runtime_config
    )
    return build_result_record(
        task,
        check,
        agent,
        _workspace_run(task, check, agent, outcome),
        identity,
        scoring_config,
    )


def _redigest_result(
    result: ResultRecord,
    **changes: object,
) -> ResultRecord:
    draft = replace(
        result,
        result_id="",
        result_digest="",
        **changes,
    )
    return record_with_digest(replace(draft, result_id=make_result_id(draft)))


def _task_pool(
    tasks: tuple[TaskRecord, ...],
    checks: tuple[CheckRecord, ...],
    *,
    task_pool_id: str = "task-pool",
    created_at: str | None = None,
    source_window: TimeRange | None = None,
) -> TaskPoolRecord:
    evidence = _certification_evidence(tasks, checks)
    source_events = _source_events(tasks, checks)
    if created_at is None:
        created_at = format_utc_timestamp(
            max(
                *(
                    parse_utc_timestamp(task.task_material_available_at)
                    for task in tasks
                ),
                *(
                    parse_utc_timestamp(check.check_material_available_at)
                    for check in checks
                ),
            )
        )
    record = TaskPoolRecord(
        task_pool_id=task_pool_id,
        task_pool_digest="",
        repository_id="repo",
        task_ids=tuple(task.task_id for task in tasks),
        check_ids=tuple(check.check_id for check in checks),
        task_records_ref="tasks.jsonl",
        task_records_digest=canonical_digest(tasks),
        check_records_ref="checks.jsonl",
        check_records_digest=canonical_digest(checks),
        certification_evidence_ref="certification-evidence.jsonl",
        source_event_records_ref="source-events.jsonl",
        source_event_records_digest=canonical_digest(source_events),
        rejected_candidate_ids=(),
        rejection_summary_digest=canonical_digest({"rejected_count": 0, "reasons": {}}),
        certification_evidence_digest=canonical_digest(evidence),
        generation_provenance_ref=None,
        generation_provenance_digest=None,
        generator_config_digest=None,
        source_protocol_digest=None,
        certification_config_digest=canonical_digest({"repeat_count": 1}),
        created_at=created_at,
        source_window_start=(
            format_utc_timestamp(parse_utc_timestamp(source_window.start))
            if source_window is not None
            else None
        ),
        source_window_end=(
            format_utc_timestamp(parse_utc_timestamp(source_window.end))
            if source_window is not None
            else None
        ),
    )
    return record_with_digest(record)


def _task_pool_bundle(
    tasks: tuple[TaskRecord, ...],
    checks: tuple[CheckRecord, ...],
    *,
    task_pool_id: str = "task-pool",
    created_at: str | None = None,
    source_window: TimeRange | None = None,
) -> task_pool_module.TaskPoolBundle:
    task_pool = _task_pool(
        tasks,
        checks,
        task_pool_id=task_pool_id,
        created_at=created_at,
        source_window=source_window,
    )
    return task_pool_module.validated_task_pool_bundle(
        task_pool,
        tasks,
        checks,
        _certification_evidence(tasks, checks),
        _source_events(tasks, checks),
    )


def _task_pool_with_refs(
    tmp_path: Path,
    tasks: tuple[TaskRecord, ...],
    checks: tuple[CheckRecord, ...],
    *,
    bundle_name: str | None = None,
    task_pool_id: str = "task-pool",
    created_at: str | None = None,
    source_window: TimeRange | None = None,
    generation_evidence: bool = False,
) -> TaskPoolRecord:
    bundle_root = tmp_path if bundle_name is None else tmp_path / bundle_name
    bundle_root.mkdir(parents=True, exist_ok=True)
    task_ref = bundle_root / "tasks.jsonl"
    check_ref = bundle_root / "checks.jsonl"
    evidence_ref = bundle_root / "certification-evidence.jsonl"
    source_event_ref = bundle_root / "source-events.jsonl"
    evidence = _certification_evidence(tasks, checks)
    source_events = _source_events(tasks, checks)
    write_jsonl_records(task_ref, tasks)
    write_jsonl_records(check_ref, checks)
    write_jsonl_records(evidence_ref, evidence)
    write_jsonl_records(source_event_ref, source_events)
    task_pool = record_with_digest(
        replace(
            _task_pool(
                tasks,
                checks,
                task_pool_id=task_pool_id,
                created_at=created_at,
                source_window=source_window,
            ),
            task_records_ref=str(task_ref),
            check_records_ref=str(check_ref),
            certification_evidence_ref=str(evidence_ref),
            source_event_records_ref=str(source_event_ref),
            task_pool_digest="",
        )
    )
    if not generation_evidence:
        return task_pool
    if source_window is None:
        raise ValueError("test generation evidence requires a source_window")
    behavior = {
        "generator_family": "test-fixture",
        "adapter_version": "1",
        "implementation_digest": "test-fixture-implementation",
        "behavior_config": {"mode": "stable"},
    }
    protocol = {
        "source_kind": "fixture",
        "target_definition": "fixture source frame",
        "query_semantics": {"mode": "all"},
        "sampling_policy": {"mode": "all"},
        "deduplication_policy": {"key": "source_ref"},
    }
    protocol_digest = canonical_digest(protocol)
    observed_at = format_utc_timestamp(
        parse_utc_timestamp(created_at or task_pool.created_at)
    )
    frame_events = tuple(
        record_with_digest(
            ObservedFrameEventRecord(
                source_event_id=event.source_event_id,
                repository_id=event.repository_id,
                source_family=event.source_family,
                source_ref=event.source_ref,
                observed_at=observed_at,
                frame_event_digest="",
            )
        )
        for event in source_events
    )
    frame_ref = bundle_root / "observed-frame-events.jsonl"
    frame = {
        "frame_id": f"{task_pool_id}-frame",
        "source_protocol_digest": protocol_digest,
        "source_revision": "fixture-revision",
        "window_start": format_utc_timestamp(parse_utc_timestamp(source_window.start)),
        "window_end": format_utc_timestamp(parse_utc_timestamp(source_window.end)),
        "event_inventory_ref": str(frame_ref),
        "event_inventory_digest": canonical_digest(frame_events),
        "observation_authority": "source_authoritative",
        "observation_receipt_digest": "fixture-receipt",
        "known_blind_spots": [],
        "coverage_mode": "one_source_event_per_frame_unit_v1",
    }
    run = {
        "run_id": f"{task_pool_id}-run",
        "producer_id": "fixture",
        "authority_kind": "barcarolle_managed",
        "authority_digest": "fixture-authority",
        "started_at": observed_at,
        "finished_at": observed_at,
        "input_snapshot_digest": "fixture-input",
    }
    outputs = {
        "prepared_candidate_records_digest": "fixture-candidates",
        "adapter_evidence_ref": None,
        "adapter_evidence_digest": None,
        "task_records_digest": task_pool.task_records_digest,
        "check_records_digest": task_pool.check_records_digest,
        "source_event_records_digest": task_pool.source_event_records_digest,
        "certification_evidence_digest": task_pool.certification_evidence_digest,
    }
    manifest = record_with_digest(
        GenerationProvenanceManifest(
            schema_version=task_pool_module.GENERATION_PROVENANCE_SCHEMA_VERSION,
            generator_behavior=behavior,
            generator_behavior_digest=canonical_digest(behavior),
            source_protocol=protocol,
            source_protocol_digest=protocol_digest,
            observed_frame=frame,
            observed_frame_digest=canonical_digest(frame),
            run=run,
            run_digest=canonical_digest(run),
            outputs=outputs,
            outputs_digest=canonical_digest(outputs),
            manifest_digest="",
        )
    )
    provenance_ref = bundle_root / "generation-provenance.jsonl"
    write_jsonl_records(frame_ref, frame_events)
    write_jsonl_records(provenance_ref, (manifest,))
    return record_with_digest(
        replace(
            task_pool,
            generation_provenance_ref=str(provenance_ref),
            generation_provenance_digest=manifest.manifest_digest,
            generator_config_digest=manifest.generator_behavior_digest,
            source_protocol_digest=manifest.source_protocol_digest,
            task_pool_digest="",
        )
    )


def _source_events(
    tasks: tuple[TaskRecord, ...],
    checks: tuple[CheckRecord, ...],
) -> tuple[SourceEventRecord, ...]:
    tasks_by_id = {task.task_id: task for task in tasks}
    return tuple(
        sorted(
            (
                record_with_digest(
                    SourceEventRecord(
                        source_event_id=make_source_event_id(
                            tasks_by_id[check.task_id].repository_id,
                            tasks_by_id[check.task_id].source_family,
                            tasks_by_id[check.task_id].source_ref,
                        ),
                        repository_id=tasks_by_id[check.task_id].repository_id,
                        source_family=tasks_by_id[check.task_id].source_family,
                        source_ref=tasks_by_id[check.task_id].source_ref,
                        source_resolved_at=tasks_by_id[
                            check.task_id
                        ].source_resolved_at,
                        task_material_available_at=tasks_by_id[
                            check.task_id
                        ].task_material_available_at,
                        check_material_available_at=check.check_material_available_at,
                        label_mature_at=format_utc_timestamp(
                            max(
                                parse_utc_timestamp(
                                    tasks_by_id[
                                        check.task_id
                                    ].task_material_available_at
                                ),
                                parse_utc_timestamp(check.check_material_available_at),
                            )
                        ),
                        candidate_id=f"candidate-{check.check_id}",
                        task_id=check.task_id,
                        check_id=check.check_id,
                        disposition="accepted",
                        rejection_stage=None,
                        rejection_reasons=(),
                        dependency_cluster_id=tasks_by_id[
                            check.task_id
                        ].dependency_cluster_id,
                        sampling_stratum=tasks_by_id[check.task_id].sampling_stratum,
                        source_event_digest="",
                    )
                )
                for check in checks
            ),
            key=lambda event: event.source_event_id,
        )
    )


def _certification_evidence(
    tasks: tuple[TaskRecord, ...],
    checks: tuple[CheckRecord, ...],
) -> tuple[dict[str, object], ...]:
    tasks_by_id = {task.task_id: task for task in tasks}
    return tuple(
        sorted(
            (
                {
                    "candidate_id": f"candidate-{check.check_id}",
                    "accepted": True,
                    "rejection_reasons": (),
                    "repeat_count": 1,
                    "base_check": (
                        {
                            "outcome": "fail",
                            "failure_label": "check_failed",
                            "timed_out": False,
                            "duration_seconds": 0.0,
                            "evidence_excerpt": "",
                        },
                    ),
                    "reference_patch_check": (
                        {
                            "outcome": "pass",
                            "failure_label": None,
                            "timed_out": False,
                            "duration_seconds": 0.0,
                            "evidence_excerpt": "",
                        },
                    ),
                    "reference_patch_digest": f"patch-{check.check_id}",
                    "task_digest": canonical_digest(tasks_by_id[check.task_id]),
                    "check_digest": canonical_digest(check),
                    "workspace_config_digest": canonical_digest(_workspace_config()),
                    "runtime_config_digest": canonical_digest(_runtime_config()),
                    "check_execution_binding_digest": canonical_digest(
                        {"fixture_check_id": check.check_id}
                    ),
                    "verification_adapter_digest": VERIFICATION_ADAPTER_DIGEST,
                }
                for check in checks
            ),
            key=lambda record: str(record["candidate_id"]),
        )
    )


def _selection(
    task_pool: TaskPoolRecord, ref: TaskCheckRef
) -> BenchmarkSelectionRecord:
    selection = BenchmarkSelectionRecord(
        selection_id="selection",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_id="origin",
        selector_id="selector",
        selector_digest="selector-digest",
        selected_task_check_refs=(ref,),
        selected_weights={task_check_ref_key(ref): 1.0},
        budget_digest="budget",
        selection_input_digest="selector-input",
        feature_snapshot_id="feature-snapshot",
        eligibility_mode="counterfactual_replay",
        created_at="2026-01-05T00:00:00Z",
        selection_digest="",
    )
    return record_with_digest(selection)


def _selection_for_origin(
    task_pool: TaskPoolRecord,
    ref: TaskCheckRef,
    origin_id: str,
    budget_digest: str,
    feature_snapshot_id: str,
) -> BenchmarkSelectionRecord:
    return record_with_digest(
        replace(
            _selection(task_pool, ref),
            origin_id=origin_id,
            budget_digest=budget_digest,
            feature_snapshot_id=feature_snapshot_id,
            selection_digest="",
        )
    )


def _persist_replayable_selection(
    task_pool_bundle: task_pool_module.TaskPoolBundle,
    selected_ref: TaskCheckRef,
    agents: tuple[AgentRecord, ...],
    store: ResultStore,
    *,
    origin: RollingOriginRecord | None = None,
) -> tuple[BenchmarkSelectionRecord, RollingOriginRecord]:
    task_pool = task_pool_bundle.task_pool
    if origin is None:
        effective_origin = replace(
            _origin(task_pool, selected_ref, selected_ref),
            origin_id="",
            future_holdout_task_check_refs=(),
            origin_digest="",
        )
        effective_origin = replace(
            effective_origin,
            origin_id=make_rolling_origin_id(effective_origin),
        )
        effective_origin = record_with_digest(effective_origin)
    else:
        effective_origin = origin
    feature_config = FeatureConfig(("task_count",))
    snapshot = runner_module.selection_module.build_feature_snapshot(
        effective_origin,
        task_pool,
        task_pool_bundle.tasks,
        task_pool_bundle.checks_by_id,
        (),
        feature_config,
    )
    selector_input = runner_module.selection_module.build_selector_input(
        effective_origin,
        task_pool,
        snapshot,
        (),
        agents,
        SelectionBudget(1),
        feature_config.leakage_policy(effective_origin.as_of_cutoff),
    )
    selector = _selector()
    selection = runner_module.selection_module.select_with_selector(
        selector_input,
        snapshot,
        selector,
    )
    runner_module._append_selector_record(selector, store)
    runner_module._append_origin_record(effective_origin, store)
    runner_module._append_feature_snapshot_record(snapshot, store)
    runner_module._append_selector_input_record(selector_input, store)
    persisted = runner_module._append_selection_record(selection, store)
    return persisted, effective_origin


def _origin(
    task_pool: TaskPoolRecord, selected_ref: TaskCheckRef, future_ref: TaskCheckRef
) -> RollingOriginRecord:
    policy_digest = make_rolling_origin_policy_digest(
        as_of_cutoff_rule="origin_time",
        eligibility_mode="counterfactual_replay",
        holdout_overlap_policy="allow_cluster_overlap",
        future_holdout_known=True,
        allowed_dependency_cluster_ids=(),
        maturity_lag_seconds=0,
    )
    origin = RollingOriginRecord(
        origin_id="",
        task_pool_id=task_pool.task_pool_id,
        task_pool_digest=task_pool.task_pool_digest,
        origin_time="2026-01-05T00:00:00Z",
        policy_digest=policy_digest,
        history_task_check_refs=(selected_ref,),
        history_censored_task_check_refs=(),
        future_holdout_task_check_refs=(future_ref,),
        future_censored_task_check_refs=(),
        as_of_cutoff="2026-01-05T00:00:00Z",
        eligibility_mode="counterfactual_replay",
        holdout_overlap_policy="allow_cluster_overlap",
        as_of_cutoff_rule="origin_time",
        history_window_start="2026-01-01T00:00:00Z",
        future_window_start="2026-01-05T00:00:00Z",
        future_window_end="2026-01-10T00:00:00Z",
        future_cohort_time_basis="task_material_available_at",
        maturity_lag_seconds=0,
        label_maturity_cutoff="2026-01-10T00:00:00.000000Z",
        future_holdout_known=True,
        allowed_dependency_cluster_ids=(),
        origin_digest="",
    )
    origin = replace(origin, origin_id=make_rolling_origin_id(origin))
    return record_with_digest(origin)
