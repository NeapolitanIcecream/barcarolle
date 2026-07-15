#!/usr/bin/env python3
"""Certify and dry-run the five-task boltons real-target regression."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    AgentRecord,
    RuntimeConfig,
    WorkspaceConfig,
    canonical_digest,
    canonical_json,
    write_jsonl_records,
)
from barcarolle.result_store import (  # noqa: E402
    ResultStore,
    ScoringConfig,
    build_result_record,
    compute_result_cache_identity,
    load_results,
    ResultQuery,
    store_result,
)
from barcarolle.task_pool import (  # noqa: E402
    CertificationConfig,
    TaskCandidate,
    build_check_candidate,
    certification_evidence_records,
    certify_task_candidate,
    freeze_task_pool,
)
from barcarolle.workspace import (  # noqa: E402
    CapturedDiff,
    bind_agent_harness,
    bind_check_material,
    bind_repository_source,
    run_agent_on_task,
)


HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = Path(
    "outputs/user-journeys/2026-07-15-boltons-current-schema-regression"
)
PINNED_COMMIT = "979fa9b613fa8c0a455ae16ea6f2ec91c11ecafe"
CHECK_COMMAND = (
    sys.executable,
    "-m",
    "pytest",
    "-q",
    ".barcarolle/check_bundle/test_task.py",
)


@dataclass(frozen=True)
class _TaskInput:
    source_ref: str
    available_at: str
    cluster_id: str
    title: str
    body: str
    solver_material_refs: tuple[str, ...]


TASK_INPUTS = (
    _TaskInput(
        "boltons-iterutils-chunked-iter-count",
        "2026-06-03T10:00:00Z",
        "iterutils",
        "Add count support to chunked_iter",
        (
            "The public chunked() helper already accepts count, but chunked_iter() rejects it. "
            "Add a count keyword to chunked_iter() so callers can lazily stop after the requested "
            "number of chunks while preserving existing fill behavior and string/bytes chunk types."
        ),
        ("boltons/iterutils.py",),
    ),
    _TaskInput(
        "boltons-iterutils-windowed-positive-size",
        "2026-06-06T09:30:00Z",
        "iterutils",
        "Reject non-positive window sizes",
        (
            "windowed() and windowed_iter() should reject zero or negative window sizes with a "
            "ValueError, matching the existing positive-size validation used by related iterutils helpers."
        ),
        ("boltons/iterutils.py",),
    ),
    _TaskInput(
        "boltons-urlutils-parse-qsl-blank-values",
        "2026-06-10T12:00:00Z",
        "urlutils",
        "Preserve explicitly blank query values",
        (
            "parse_qsl() currently treats a bare key and an explicitly blank key the same. "
            "Preserve 'a=' as an empty string while still representing a bare 'a' as None when "
            "blank values are kept."
        ),
        ("boltons/urlutils.py",),
    ),
    _TaskInput(
        "boltons-dictutils-omd-keyword-update",
        "2026-07-03T15:45:00Z",
        "dictutils",
        "Allow keyword-only OrderedMultiDict.update",
        (
            "OrderedMultiDict.update() should accept keyword-only calls like dict.update(). "
            "Calling update(a=1) should update the mapping instead of raising TypeError for a missing positional argument."
        ),
        ("boltons/dictutils.py",),
    ),
    _TaskInput(
        "boltons-cacheutils-lri-keyword-update",
        "2026-07-06T11:15:00Z",
        "cacheutils",
        "Allow keyword-only LRI and LRU updates",
        (
            "LRI.update(), and therefore LRU.update(), should accept keyword-only updates like dict.update(). "
            "Calling update(a=1) should populate the cache without requiring an explicit positional mapping."
        ),
        ("boltons/cacheutils.py",),
    ),
)


def run(target_repo: Path, output_dir: Path) -> dict[str, object]:
    target_repo = target_repo.resolve()
    output_dir = output_dir.resolve()
    records_dir = output_dir / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    _clear_previous_records(records_dir)
    _require_pinned_commit(target_repo)

    workspace_config = WorkspaceConfig(
        workspace_config_id="boltons-pinned-current-schema",
        repository_checkout_config_digest=canonical_digest(
            {"repository": "boltons", "base_commit": PINNED_COMMIT}
        ),
        submodule_state_digest="submodules-none",
        base_image_digest=canonical_digest({"python": sys.version.split()[0]}),
        dependency_lock_digest=canonical_digest({"pytest": "barcarolle-dev-lock"}),
    )
    runtime_config = RuntimeConfig(
        runtime_config_id="boltons-scripted-120s",
        budget_digest="scripted-no-paid-call",
        retry_policy_digest="retry-none",
        stochastic_settings_digest="deterministic",
        timeout_seconds=120,
        hardware_profile_digest=None,
    )
    bind_repository_source(workspace_config, target_repo)

    candidates = tuple(_candidate(task_input) for task_input in TASK_INPUTS)
    for task_input, candidate in zip(TASK_INPUTS, candidates, strict=True):
        bind_check_material(
            build_check_candidate(candidate),
            CHECK_COMMAND,
            _hidden_check_dir(task_input.source_ref),
        )

    certification_config = CertificationConfig(repeat_count=1)
    certified = tuple(
        certify_task_candidate(
            candidate,
            certification_config,
            workspace_config,
            runtime_config,
            _reference_patch(task_input.source_ref),
        )
        for task_input, candidate in zip(TASK_INPUTS, candidates, strict=True)
    )
    write_jsonl_records(
        records_dir / "certification-evidence.jsonl",
        certification_evidence_records(certified),
    )
    rejected = tuple(result for result in certified if not result.accepted)
    if rejected:
        failures = "; ".join(
            f"{result.candidate_id}: {', '.join(result.rejection_reasons)}"
            for result in rejected
        )
        raise RuntimeError(f"boltons Task certification failed: {failures}")

    tasks = tuple(result.task for result in certified if result.task is not None)
    checks = tuple(result.check for result in certified if result.check is not None)
    task_pool = freeze_task_pool(
        tasks,
        checks,
        (),
        {
            "repository_id": "boltons",
            "accepted_certification_results": certified,
            "task_records_ref": "records/tasks.jsonl",
            "check_records_ref": "records/checks.jsonl",
            "certification_evidence_ref": "records/certification-evidence.jsonl",
            "source_event_inventory_digest": canonical_digest(
                tuple(task_input.source_ref for task_input in TASK_INPUTS)
            ),
            "generator_config_digest": canonical_digest(
                {
                    "fixture": "boltons-current-schema-regression-v1",
                    "base_commit": PINNED_COMMIT,
                }
            ),
            "certification_config_digest": canonical_digest(certification_config),
            "created_at": "2026-07-15T00:00:00Z",
        },
    )
    write_jsonl_records(records_dir / "tasks.jsonl", tasks)
    write_jsonl_records(records_dir / "checks.jsonl", checks)
    write_jsonl_records(records_dir / "task_pool.jsonl", (task_pool,))

    command = (
        sys.executable,
        str((HERE / "scripted_agent.py").resolve()),
        "--patch-dir",
        str((HERE / "reference-patches").resolve()),
    )
    agent = _scripted_agent(command)
    bind_agent_harness(agent, command)
    checks_by_id = {check.check_id: check for check in checks}
    scoring_config = ScoringConfig(
        pricing_version="not-applicable-scripted", cost_rates={}
    )
    result_store = ResultStore(records_dir / "results.jsonl")
    for task in tasks:
        check = checks_by_id[task.check_ids[0]]
        workspace_run = run_agent_on_task(
            task, check, agent, workspace_config, runtime_config
        )
        identity = compute_result_cache_identity(
            task, check, agent, workspace_config, runtime_config
        )
        result = build_result_record(
            task, check, agent, workspace_run, identity, scoring_config
        )
        store_result(result, result_store)

    results = tuple(load_results(result_store, ResultQuery()))
    summary: dict[str, object] = {
        "task_pool_id": task_pool.task_pool_id,
        "task_count": len(tasks),
        "certified_base_fail_count": sum(
            result.evidence["base_check"][0]["outcome"] == "fail"
            for result in certified
        ),
        "certified_reference_pass_count": sum(
            result.evidence["reference_patch_check"][0]["outcome"] == "pass"
            for result in certified
        ),
        "scripted_result_count": len(results),
        "scripted_pass_count": sum(result.outcome == "pass" for result in results),
        "paid_call_count": 0,
        "predictive_evidence": False,
        "records_dir": str(records_dir),
    }
    (output_dir / "summary.json").write_text(
        canonical_json(summary) + "\n", encoding="utf-8"
    )
    if summary["scripted_pass_count"] != len(tasks):
        failed = ", ".join(
            result.task_id for result in results if result.outcome != "pass"
        )
        raise RuntimeError(f"scripted boltons regression failed for Task ids: {failed}")
    return summary


def _candidate(task_input: _TaskInput) -> TaskCandidate:
    hidden_check = _hidden_check_dir(task_input.source_ref)
    return TaskCandidate(
        candidate_id=f"candidate-{task_input.source_ref}",
        repository_id="boltons",
        base_commit=PINNED_COMMIT,
        source_family="regression_fixture",
        source_ref=task_input.source_ref,
        source_resolved_at=task_input.available_at,
        task_material_available_at=task_input.available_at,
        check_material_available_at=task_input.available_at,
        task_text=f"{task_input.title}\n\n{task_input.body}",
        solver_material_refs=task_input.solver_material_refs,
        cluster_id=task_input.cluster_id,
        check_manifest_digest=canonical_digest({"check_command": CHECK_COMMAND}),
        hidden_check_bundle_digest=_path_digest(hidden_check),
        resource_limits={"timeout_seconds": 60},
        oracle_source="private_pytest_fixture",
        check_type="pytest",
    )


def _scripted_agent(command: tuple[str, ...]) -> AgentRecord:
    harness_digest = canonical_digest({"agent_command": command})
    return AgentRecord(
        agent_id="scripted-known-good-boltons",
        agent_manifest_digest=canonical_digest(
            {"agent": "scripted-known-good-boltons", "harness_digest": harness_digest}
        ),
        model_snapshot_id="none-scripted",
        harness_digest=harness_digest,
        repository_instruction_digest="none",
        prompt_digest="task-md-v1",
        tools_digest="git-apply-only",
        retrieval_digest="none",
        skills_digest="none",
        network_policy_digest="offline",
        adapter_digest="barcarolle-worktree-diff-v1",
    )


def _reference_patch(source_ref: str) -> CapturedDiff:
    patch_text = (HERE / "reference-patches" / f"{source_ref}.diff").read_text(
        encoding="utf-8"
    )
    return CapturedDiff(
        diff_text=patch_text,
        diff_digest=hashlib.sha256(patch_text.encode("utf-8")).hexdigest(),
    )


def _hidden_check_dir(source_ref: str) -> Path:
    return HERE / "hidden-checks" / source_ref


def _path_digest(path: Path) -> str:
    entries = tuple(
        (str(child.relative_to(path)), hashlib.sha256(child.read_bytes()).hexdigest())
        for child in sorted(item for item in path.rglob("*") if item.is_file())
    )
    return canonical_digest(entries)


def _require_pinned_commit(target_repo: Path) -> None:
    if not (target_repo / ".git").exists():
        raise ValueError("--target-repo must be a Git checkout")
    completed = subprocess.run(
        ("git", "cat-file", "-e", f"{PINNED_COMMIT}^{{commit}}"),
        cwd=target_repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(
            f"--target-repo does not contain pinned boltons commit {PINNED_COMMIT}"
        )


def _clear_previous_records(records_dir: Path) -> None:
    for name in (
        "certification-evidence.jsonl",
        "tasks.jsonl",
        "checks.jsonl",
        "task_pool.jsonl",
        "results.jsonl",
    ):
        (records_dir / name).unlink(missing_ok=True)
    (records_dir.parent / "summary.json").unlink(missing_ok=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Certify and run the no-paid five-task boltons current-schema regression."
    )
    parser.add_argument("--target-repo", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    summary = run(args.target_repo, args.output_dir)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
