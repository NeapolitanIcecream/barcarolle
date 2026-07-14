"""Offline minimal Barcarolle demo with deterministic fixture results."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import subprocess
import sys


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle import reporting
from barcarolle.records import (
    AgentRecord,
    CheckRecord,
    ResultRecord,
    RuntimeConfig,
    SelectorRecord,
    TaskCheckRef,
    TaskPoolRecord,
    TaskRecord,
    WorkspaceConfig,
    WorkspaceRunRecord,
    canonical_digest,
    record_with_digest,
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
from barcarolle.runner import prepare_evaluation_cells, score_selection
from barcarolle.selection import (
    FeatureConfig,
    LeakagePolicy,
    MetricConfig,
    RollingOriginPolicy,
    SelectionBudget,
    SelectionConfig,
    build_feature_snapshot,
    build_rolling_origin,
    build_selector_input,
    select_with_selector,
)
from barcarolle.task_pool import (
    CertificationConfig,
    TaskCandidate,
    TimeRange,
    build_check_candidate,
    certification_evidence_records,
    certify_task_candidate,
    freeze_task_pool,
)
from barcarolle.workspace import CapturedDiff, bind_check_material, bind_repository_source


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "out"
ORIGIN_TIME = datetime(2026, 1, 6, tzinfo=UTC)
ORIGIN_TIME_ISO = "2026-01-06T00:00:00.000000Z"
FUTURE_END_ISO = "2026-01-12T00:00:00Z"


def main(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, object]:
    output_dir = output_dir.resolve()
    records_dir = output_dir / "records"
    _clear_output_dir(output_dir)
    records_dir.mkdir(parents=True, exist_ok=True)

    tasks, checks, task_pool = _build_task_pool(records_dir)
    checks_by_id = {check.check_id: check for check in checks}
    agents = _agents()
    workspace_config = WorkspaceConfig("workspace-fixture", "checkout-fixture", "submodules-none", "python-fixture", "deps-fixture")
    runtime_config = RuntimeConfig("runtime-fixture", "budget-fixture", "retry-none", "deterministic", 30, None)
    scoring_config = ScoringConfig("fixture-v1", {"input_tokens": 0.0})
    result_store = ResultStore(records_dir / "results.jsonl")
    _store_fixture_results(tasks, checks_by_id, agents, workspace_config, runtime_config, scoring_config, result_store)

    policy = RollingOriginPolicy(
        policy_digest="rolling-origin-fixture",
        as_of_cutoff_rule="origin_time",
        cluster_constraints_digest="clusters-all",
        eligibility_mode="strict_history",
        holdout_overlap_policy="disjoint",
        future_holdout_known=True,
    )
    origin = build_rolling_origin(
        task_pool,
        tasks,
        checks_by_id,
        ORIGIN_TIME,
        TimeRange(start=ORIGIN_TIME_ISO, end=FUTURE_END_ISO),
        policy,
    )
    pre_origin_results = _pre_origin_results(result_store, origin.history_task_check_refs, agents, ORIGIN_TIME_ISO)
    feature_config = FeatureConfig(
        feature_config_digest="feature-fixture",
        leakage_policy_digest="leakage-fixture",
        feature_names=("task_count", "pre_origin_result_count", "task_cluster"),
        allowed_leakage_classes=("task_metadata", "pre_origin_result"),
    )
    snapshot = build_feature_snapshot(origin, task_pool, tasks, checks_by_id, pre_origin_results, feature_config)
    budget = SelectionBudget("budget-one-task-check", 1)
    selector_input = build_selector_input(
        origin,
        task_pool,
        snapshot,
        pre_origin_results,
        agents,
        budget,
        LeakagePolicy(feature_config.leakage_policy_digest, feature_config.allowed_leakage_classes, origin.as_of_cutoff),
    )
    selector_parameters = {}
    selector = SelectorRecord(
        selector_id="selector-demo-recency",
        selector_family="recency",
        selector_version="1",
        training_source_digests=(task_pool.task_pool_digest, snapshot.feature_records_digest),
        allowed_feature_classes=feature_config.allowed_leakage_classes,
        parameters=selector_parameters,
        config_digest=canonical_digest(
            {"selector_family": "recency", "parameters": selector_parameters}
        ),
        created_at="2026-01-05T00:00:00Z",
    )
    selection = select_with_selector(
        selector_input,
        selector,
        SelectionConfig(
            selection_config_digest="selection-fixture",
            selector_id=selector.selector_id,
            feature_snapshot_id=snapshot.feature_snapshot_id,
            eligibility_mode="recency",
        ),
    )
    cell_set = prepare_evaluation_cells(
        selection,
        origin,
        task_pool,
        tasks,
        checks_by_id,
        agents,
        workspace_config,
        runtime_config,
        scoring_config,
        ResultCacheConfig(),
        result_store,
        ResultJoinConfig("join-fixture", "denominator-fixture"),
    )
    scored_cell_set, selected_matrix, future_matrix, metrics = score_selection(
        selection,
        origin,
        task_pool,
        tasks,
        checks_by_id,
        agents,
        cell_set,
        result_store,
        ResultJoinConfig("join-fixture", "denominator-fixture"),
        MetricConfig("metric-fixture", budget.budget_digest),
    )
    results = tuple(load_results(result_store, ResultQuery()))
    sections = (
        reporting.build_task_pool_report(task_pool),
        reporting.build_result_report(results, agents),
        reporting.build_selector_report((selection,), (scored_cell_set,), (selected_matrix, future_matrix), metrics),
    )
    markdown_path = output_dir / "report.md"
    json_path = output_dir / "report.json"
    reporting.write_report(sections, markdown_path)
    reporting.write_report(sections, json_path)
    return {
        "markdown": str(markdown_path),
        "json": str(json_path),
        "task_count": len(tasks),
        "result_count": len(results),
        "selected_task_check_count": len(selection.selected_task_check_refs),
        "future_task_check_count": len(origin.future_holdout_task_check_refs),
    }


def _build_task_pool(records_dir: Path) -> tuple[tuple[TaskRecord, ...], tuple[CheckRecord, ...], TaskPoolRecord]:
    certification_config = CertificationConfig()
    with TemporaryDirectory(prefix="barcarolle-demo-task-") as temp_dir:
        (
            candidates,
            workspace_config,
            runtime_config,
            reference_patch,
        ) = _executable_task_candidates(Path(temp_dir))
        certified = tuple(
            certify_task_candidate(
                candidate,
                certification_config,
                workspace_config,
                runtime_config,
                reference_patch,
            )
            for candidate in candidates
        )
    accepted_tasks = tuple(result.task for result in certified if result.accepted and result.task is not None)
    accepted_checks = tuple(result.check for result in certified if result.accepted and result.check is not None)
    rejected = tuple(result for result in certified if not result.accepted)
    task_pool = freeze_task_pool(
        accepted_tasks,
        accepted_checks,
        rejected,
        {
            "repository_id": "demo-repo",
            "accepted_certification_results": tuple(result for result in certified if result.accepted),
            "task_records_ref": "records/tasks.jsonl",
            "check_records_ref": "records/checks.jsonl",
            "certification_evidence_ref": "records/certification-evidence.jsonl",
            "source_event_inventory_digest": canonical_digest(tuple(candidate.source_ref for candidate in candidates)),
            "generator_config_digest": "generator-fixture",
            "certification_config_digest": canonical_digest(certification_config),
            "created_at": "2026-01-01T00:00:00Z",
        },
    )
    write_jsonl_records(records_dir / "tasks.jsonl", accepted_tasks)
    write_jsonl_records(records_dir / "checks.jsonl", accepted_checks)
    write_jsonl_records(
        records_dir / "certification-evidence.jsonl",
        certification_evidence_records(certified),
    )
    return accepted_tasks, accepted_checks, task_pool


def _task_candidates(
    base_commit: str,
    check_manifest_digest: str,
    hidden_check_bundle_digest: str,
) -> tuple[TaskCandidate, ...]:
    return (
        _candidate(
            "candidate-config-parse",
            "history-1",
            "2026-01-02T00:00:00Z",
            "configuration",
            "Parse optional timeout values",
            "Accept missing timeout values while preserving existing defaults.",
            base_commit,
            check_manifest_digest,
            hidden_check_bundle_digest,
        ),
        _candidate(
            "candidate-cache-key",
            "history-2",
            "2026-01-04T00:00:00Z",
            "result-store",
            "Include scoring identity in cache keys",
            "Keep cached results separate when scoring settings differ.",
            base_commit,
            check_manifest_digest,
            hidden_check_bundle_digest,
        ),
        _candidate(
            "candidate-selection-summary",
            "future-1",
            "2026-01-08T00:00:00Z",
            "reporting",
            "Summarize selected and future matrix evidence",
            "Report selected benchmark cells separately from future holdout cells.",
            base_commit,
            check_manifest_digest,
            hidden_check_bundle_digest,
        ),
        _candidate(
            "candidate-denominator-policy",
            "future-2",
            "2026-01-10T00:00:00Z",
            "selection",
            "Track denominator policy in metrics",
            "Bind rolling-origin metrics to the denominator policy used for scoring.",
            base_commit,
            check_manifest_digest,
            hidden_check_bundle_digest,
        ),
    )


def _candidate(
    candidate_id: str,
    source_ref: str,
    available_at: str,
    cluster_id: str,
    title: str,
    body: str,
    base_commit: str,
    check_manifest_digest: str,
    hidden_check_bundle_digest: str,
) -> TaskCandidate:
    return TaskCandidate(
        candidate_id=candidate_id,
        repository_id="demo-repo",
        base_commit=base_commit,
        source_family="fixture",
        source_ref=source_ref,
        source_resolved_at=available_at,
        task_material_available_at=available_at,
        check_material_available_at=available_at,
        task_text=f"{title}\n\n{body}",
        solver_material_refs=(),
        cluster_id=cluster_id,
        check_manifest_digest=check_manifest_digest,
        hidden_check_bundle_digest=hidden_check_bundle_digest,
        resource_limits={"timeout_seconds": 30},
        oracle_source="fixture",
        check_type="tests",
    )


def _executable_task_candidates(
    root: Path,
) -> tuple[tuple[TaskCandidate, ...], WorkspaceConfig, RuntimeConfig, CapturedDiff]:
    repository = root / "repository"
    repository.mkdir()
    _git(repository, "init", "--quiet")
    _git(repository, "config", "user.email", "demo@example.invalid")
    _git(repository, "config", "user.name", "Barcarolle Demo")
    (repository / "value.txt").write_text("broken\n", encoding="utf-8")
    _git(repository, "add", "value.txt")
    _git(repository, "commit", "--quiet", "-m", "base")
    base_commit = _git(repository, "rev-parse", "HEAD").stdout.strip()

    hidden_material = root / "private-check.txt"
    hidden_material.write_text("demo private check\n", encoding="utf-8")
    check_command = (
        sys.executable,
        "-c",
        "from pathlib import Path; "
        "fixed = Path('value.txt').read_text(encoding='utf-8') == 'fixed\\n'; "
        "private = Path('.barcarolle/check_bundle').read_text(encoding='utf-8') == "
        "'demo private check\\n'; "
        "raise SystemExit(0 if fixed and private else 1)",
    )
    check_manifest_digest = canonical_digest({"check_command": check_command})
    hidden_check_bundle_digest = hashlib.sha256(hidden_material.read_bytes()).hexdigest()
    candidates = _task_candidates(base_commit, check_manifest_digest, hidden_check_bundle_digest)
    workspace_config = WorkspaceConfig(
        "workspace-task-validation-fixture",
        canonical_digest({"repository_path": str(repository)}),
        "submodules-none",
        "python-fixture",
        "deps-fixture",
    )
    runtime_config = RuntimeConfig(
        "runtime-task-validation-fixture",
        "budget-fixture",
        "retry-none",
        "deterministic",
        30,
        None,
    )
    bind_repository_source(workspace_config, repository)
    for candidate in candidates:
        check = build_check_candidate(candidate)
        bind_check_material(check, check_command, hidden_material)

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
    return candidates, workspace_config, runtime_config, reference_patch


def _git(repository: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=repository,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def _agents() -> tuple[AgentRecord, ...]:
    return (
        AgentRecord(
            agent_id="fixture-fast",
            agent_manifest_digest="agent-fast-manifest",
            model_snapshot_id="fixture-model-fast",
            harness_digest="fixture-harness-fast",
            repository_instruction_digest="fixture-instructions",
            prompt_digest="fixture-prompt-fast",
            tools_digest="fixture-tools",
            retrieval_digest="fixture-retrieval",
            skills_digest="fixture-skills",
            network_policy_digest="offline",
            adapter_digest="fixture-adapter-fast",
        ),
        AgentRecord(
            agent_id="fixture-careful",
            agent_manifest_digest="agent-careful-manifest",
            model_snapshot_id="fixture-model-careful",
            harness_digest="fixture-harness-careful",
            repository_instruction_digest="fixture-instructions",
            prompt_digest="fixture-prompt-careful",
            tools_digest="fixture-tools",
            retrieval_digest="fixture-retrieval",
            skills_digest="fixture-skills",
            network_policy_digest="offline",
            adapter_digest="fixture-adapter-careful",
        ),
    )


def _store_fixture_results(
    tasks: tuple[TaskRecord, ...],
    checks: dict[str, CheckRecord],
    agents: tuple[AgentRecord, ...],
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: ScoringConfig,
    result_store: ResultStore,
) -> None:
    outcomes = {
        ("history-1", "fixture-fast"): ("pass", "2026-01-03T00:00:00Z"),
        ("history-1", "fixture-careful"): ("pass", "2026-01-03T00:05:00Z"),
        ("history-2", "fixture-fast"): ("pass", "2026-01-05T00:00:00Z"),
        ("history-2", "fixture-careful"): ("pass", "2026-01-05T00:05:00Z"),
        ("future-1", "fixture-fast"): ("fail", "2026-01-09T00:00:00Z"),
        ("future-1", "fixture-careful"): ("pass", "2026-01-09T00:05:00Z"),
        ("future-2", "fixture-fast"): ("pass", "2026-01-11T00:00:00Z"),
        ("future-2", "fixture-careful"): ("pass", "2026-01-11T00:05:00Z"),
    }
    for task in tasks:
        check = checks[task.check_ids[0]]
        for agent in agents:
            source_key = task.source_ref
            outcome, available_at = outcomes[(source_key, agent.agent_id)]
            result = _fixture_result(
                task,
                check,
                agent,
                workspace_config,
                runtime_config,
                scoring_config,
                outcome,
                available_at,
            )
            store_result(result, result_store)


def _fixture_result(
    task: TaskRecord,
    check: CheckRecord,
    agent: AgentRecord,
    workspace_config: WorkspaceConfig,
    runtime_config: RuntimeConfig,
    scoring_config: ScoringConfig,
    outcome: str,
    result_available_at: str,
) -> ResultRecord:
    identity = compute_result_cache_identity(task, check, agent, workspace_config, runtime_config)
    workspace_run = WorkspaceRunRecord(
        workspace_run_id=f"fixture-run-{task.source_ref}-{agent.agent_id}-{outcome}",
        task_id=task.task_id,
        check_id=check.check_id,
        agent_id=agent.agent_id,
        solver_workspace_digest=f"solver-workspace-{task.source_ref}-{agent.agent_id}",
        verifier_workspace_digest=f"verifier-workspace-{task.source_ref}-{agent.agent_id}",
        terminal_status="passed" if outcome == "pass" else "failed",
        diff_digest=f"diff-{task.source_ref}-{agent.agent_id}-{outcome}",
        replay_status="applied",
        check_outcome=outcome,
        invalid_owner=None,
        failure_label=None if outcome == "pass" else "check_failed",
        usage={"input_tokens": 100, "output_tokens": 20},
        started_at=result_available_at,
        finished_at=result_available_at,
    )
    result = build_result_record(task, check, agent, workspace_run, identity, scoring_config)
    return record_with_digest(replace(result, result_available_at=result_available_at, result_digest=""))


def _pre_origin_results(
    result_store: ResultStore,
    refs: tuple[TaskCheckRef, ...],
    agents: tuple[AgentRecord, ...],
    cutoff: str,
) -> tuple[ResultRecord, ...]:
    task_ids = tuple(dict.fromkeys(ref.task_id for ref in refs))
    check_ids = tuple(dict.fromkeys(ref.check_id for ref in refs))
    results = load_results(
        result_store,
        ResultQuery(
            task_ids=task_ids,
            check_ids=check_ids,
            agent_ids=tuple(agent.agent_id for agent in agents),
            result_available_before=cutoff,
        ),
    )
    allowed = {(ref.task_id, ref.check_id) for ref in refs}
    return tuple(result for result in results if (result.task_id, result.check_id) in allowed)


def _clear_output_dir(output_dir: Path) -> None:
    for path in (
        output_dir / "report.md",
        output_dir / "report.json",
        output_dir / "records" / "tasks.jsonl",
        output_dir / "records" / "checks.jsonl",
        output_dir / "records" / "results.jsonl",
        output_dir / "records" / "metrics.jsonl",
    ):
        if path.exists():
            path.unlink()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the offline Barcarolle minimal demo.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    summary = main(_parse_args().output_dir)
    print(f"Wrote {_display_path(Path(str(summary['markdown'])))}")
    print(f"Wrote {_display_path(Path(str(summary['json'])))}")
