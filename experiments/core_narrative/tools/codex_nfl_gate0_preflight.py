#!/usr/bin/env python3
"""Run no-model Gate 0 probes for the Codex NFL Click follow-up."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, write_json
from _llm_budget import unsafe_text_findings

import codex_nfl_experiment_runner as batch


TOOL = "codex_nfl_gate0_preflight"
DEFAULT_RUN_PREFIX = "codex_nfl_gate0_preflight_20260508"
PROBE_ACUT_ID = "cheap-generic-swe"
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
BENIGN_ORACLE_URL_PREFIXES = ("https://docs.pytest.org/",)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-prefix", default=DEFAULT_RUN_PREFIX)
    parser.add_argument(
        "--task-split",
        choices=sorted(batch.TASK_SPLIT_MANIFESTS),
        default="rbench",
        help="Click task split manifest and task-pack root to probe.",
    )
    parser.add_argument(
        "--task-split-manifest",
        help="Optional explicit task split manifest path; defaults from --task-split.",
    )
    parser.add_argument("--tasks", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--flakiness-runs", type=int, default=2)
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    return parser.parse_args(list(argv))


def run_capture(command: Sequence[str], *, cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def p95(values: Sequence[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = math.ceil(0.95 * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]


def unique_task_ids(task_ids: Sequence[str]) -> list[str]:
    seen = set()
    duplicates = set()
    unique = []
    for task_id in task_ids:
        if task_id in seen:
            duplicates.add(task_id)
            continue
        seen.add(task_id)
        unique.append(task_id)
    if duplicates:
        raise ToolError("Gate 0 tasks must be unique", duplicate_task_ids=sorted(duplicates))
    return unique


def git_diff(source_repo: Path, base_commit: str, target_commit: str, paths: Sequence[str]) -> str:
    command = ["git", "diff", "--binary", base_commit, target_commit, "--", *paths]
    completed = run_capture(command, cwd=source_repo, timeout=60)
    if completed.returncode != 0:
        raise ToolError("failed to generate reference diff", stderr=completed.stderr.strip())
    if not completed.stdout.strip():
        raise ToolError("reference diff was empty", base_commit=base_commit, target_commit=target_commit, paths=list(paths))
    return completed.stdout


def changed_files(task: Mapping[str, Any], workspace: Path | None = None) -> list[str]:
    compare = task.get("source_compare") if isinstance(task.get("source_compare"), dict) else {}
    paths = compare.get("changed_files") if isinstance(compare.get("changed_files"), list) else []
    valid = [str(path) for path in paths if isinstance(path, str)]
    if valid or workspace is None:
        return valid
    return batch.context_paths_for_task(task, workspace)


def reference_patch_for_task(task: Mapping[str, Any]) -> str:
    source = task.get("source") if isinstance(task.get("source"), dict) else {}
    base_commit = source.get("base_commit")
    target_commit = source.get("target_commit")
    if not isinstance(base_commit, str) or not isinstance(target_commit, str):
        raise ToolError("task source must include base_commit and target_commit", task_id=task.get("task_id"))
    paths = changed_files(task)
    if not paths:
        raise ToolError("task has no changed files for reference probe", task_id=task.get("task_id"))
    return git_diff(batch.SOURCE_REPO, base_commit, target_commit, paths)


def known_bad_patch_for_task(task: Mapping[str, Any], task_id: str, run_prefix: str, artifact_dir: Path) -> str:
    source_workspace, _summary = batch.prepare_workspace(
        task_id,
        f"{run_prefix}__{task_id}__known_bad_patch_source",
        artifact_dir,
        summary_name="prepare_known_bad_patch_source",
    )
    paths = [path for path in changed_files(task, source_workspace) if (source_workspace / path).is_file()]
    if not paths:
        raise ToolError("no source file available for known-bad patch", task_id=task_id)
    target = source_workspace / paths[0]
    text = target.read_text(encoding="utf-8")
    suffix = "" if text.endswith("\n") else "\n"
    target.write_text(text + suffix + "# Barcarolle known-bad probe: no behavior change.\n", encoding="utf-8")
    completed = run_capture(["git", "diff", "--binary", "--", paths[0]], cwd=source_workspace, timeout=30)
    if completed.returncode != 0:
        raise ToolError("failed to generate known-bad diff", stderr=completed.stderr.strip())
    if not completed.stdout.strip():
        raise ToolError("known-bad diff was empty", task_id=task_id)
    return completed.stdout


def verification_duration(result: Mapping[str, Any]) -> float | None:
    verification = result.get("verification") if isinstance(result.get("verification"), dict) else {}
    value = verification.get("duration_seconds")
    return float(value) if isinstance(value, (int, float)) else None


def admission_defect_classifications(
    *,
    gates: Mapping[str, bool],
    noop: Mapping[str, Any],
    reference_runs: Sequence[Mapping[str, Any]],
    known_bad: Mapping[str, Any],
    leakage: Mapping[str, Any],
) -> list[dict[str, Any]]:
    defects: list[dict[str, Any]] = []
    if not gates.get("no_op_probe", False):
        defects.append(
            {
                "gate": "no_op_probe",
                "owner": "verifier",
                "defect_class": "noop_verifier_passed",
                "severity": "blocking_for_task_admission",
                "summary": "Verifier passed before any submitted patch was applied.",
                "observed_status": noop.get("status"),
            }
        )
    if not gates.get("reference_probe", False):
        defects.append(
            {
                "gate": "reference_probe",
                "owner": "task_pack_reference_or_verifier",
                "defect_class": "reference_patch_failed_verifier",
                "severity": "blocking_for_strict_admission",
                "summary": "The source target-commit reference patch did not satisfy the packaged verifier.",
                "reference_statuses": [probe.get("status") for probe in reference_runs],
            }
        )
    if not gates.get("known_bad_probe", False):
        defects.append(
            {
                "gate": "known_bad_probe",
                "owner": "verifier",
                "defect_class": "known_bad_patch_passed",
                "severity": "blocking_for_task_admission",
                "summary": "A behavior-preserving known-bad patch passed the verifier.",
                "observed_status": known_bad.get("status"),
            }
        )
    if not gates.get("flakiness_probe", False):
        defects.append(
            {
                "gate": "flakiness_probe",
                "owner": "verifier_or_environment",
                "defect_class": "reference_replay_unstable_or_failed",
                "severity": "blocking_for_strict_admission",
                "summary": "Repeated reference replays did not all pass with the same status.",
                "reference_statuses": [probe.get("status") for probe in reference_runs],
            }
        )
    if not gates.get("verifier_runtime_p95_lt_timeout", False):
        defects.append(
            {
                "gate": "verifier_runtime_p95_lt_timeout",
                "owner": "verifier_or_environment",
                "defect_class": "runtime_budget_margin_failed",
                "severity": "admission_warning_or_blocker",
                "summary": "Verifier runtime p95 did not stay below the declared timeout.",
            }
        )
    if not gates.get("oracle_log_leakage", False):
        defects.append(
            {
                "gate": "oracle_log_leakage",
                "owner": "verifier",
                "defect_class": "oracle_log_leakage",
                "severity": "blocking_for_task_admission",
                "summary": "Verifier logs exposed unsafe oracle-like content.",
                "leakage": leakage,
            }
        )
    if not gates.get("clean_patch_replay", False):
        defects.append(
            {
                "gate": "clean_patch_replay",
                "owner": "task_pack_reference_or_verifier",
                "defect_class": "clean_reference_replay_failed",
                "severity": "blocking_for_strict_admission",
                "summary": "Reference patch replay on clean prepared workspaces did not pass.",
                "reference_statuses": [probe.get("status") for probe in reference_runs],
            }
        )
    return defects


def verifier_timeout_seconds(task_id: str) -> int:
    task = load_manifest(batch.task_manifest_path(task_id))
    verifier = task.get("verifier") if isinstance(task.get("verifier"), dict) else {}
    value = verifier.get("timeout_seconds")
    if not isinstance(value, int):
        raise ToolError("task verifier timeout_seconds is missing", task_id=task_id)
    return value


def leakage_findings(paths: Sequence[str | None]) -> dict[str, Any]:
    reason_counts: dict[str, int] = {}
    unsafe = False
    ignored_urls: list[str] = []
    for raw_path in paths:
        if not raw_path:
            continue
        path = Path(raw_path)
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        findings = unsafe_text_findings(text)
        benign_url_count = 0
        for url in URL_RE.findall(text):
            if any(url.startswith(prefix) for prefix in BENIGN_ORACLE_URL_PREFIXES):
                benign_url_count += 1
                ignored_urls.append(url)
        unsafe = unsafe or bool(findings["unsafe"])
        adjusted_counts = dict(findings["reason_counts"])
        if benign_url_count:
            adjusted_counts["full_url"] = max(0, int(adjusted_counts.get("full_url", 0)) - benign_url_count)
        for reason, count in adjusted_counts.items():
            if count == 0:
                continue
            reason_counts[reason] = reason_counts.get(reason, 0) + int(count)
    unsafe = bool(reason_counts)
    return {
        "unsafe": unsafe,
        "reason_counts": dict(sorted(reason_counts.items())),
        "ignored_benign_urls": sorted(set(ignored_urls)),
    }


def assert_probe_artifacts_available(
    *,
    run_id: str,
    artifact_dir: Path,
    normalized_path: Path | None = None,
) -> None:
    blockers: list[str] = []
    if artifact_dir.exists() and any(artifact_dir.iterdir()):
        blockers.append("raw_artifact_dir_exists")
    if normalized_path is not None and normalized_path.exists():
        blockers.append("normalized_result_exists")
    if blockers:
        raise ToolError("probe run id already has artifacts; refusing to reuse stale outputs", run_id=run_id, blockers=blockers)


def verify_patch_text(
    *,
    task_id: str,
    run_prefix: str,
    probe_name: str,
    patch_text: str,
    install_timeout_seconds: int,
) -> dict[str, Any]:
    run_id = f"{run_prefix}__{task_id}__{probe_name}"
    artifact_dir = batch.RAW_ROOT / run_id
    normalized_path = artifact_dir / "normalized_result.json"
    assert_probe_artifacts_available(run_id=run_id, artifact_dir=artifact_dir, normalized_path=normalized_path)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    workspace, prepare_summary = batch.prepare_workspace(task_id, run_id, artifact_dir)
    install_summary = batch.install_workspace(workspace, artifact_dir, install_timeout_seconds)
    patch_path = artifact_dir / "submission.patch"
    patch_path.write_text(patch_text, encoding="utf-8")
    verify_code, normalized = batch.verify_patch(
        workspace=workspace,
        task_id=task_id,
        acut_id=PROBE_ACUT_ID,
        attempt=1,
        run_id=run_id,
        artifact_dir=artifact_dir,
        normalized_path=normalized_path,
    )
    return {
        "run_id": run_id,
        "probe": probe_name,
        "status": normalized.get("status"),
        "verify_code": verify_code,
        "workspace": str(workspace),
        "artifact_dir": str(artifact_dir),
        "normalized_result": str(normalized_path),
        "verification": normalized.get("verification"),
        "prepare": prepare_summary,
        "install": install_summary,
    }


def run_noop_probe(
    *,
    task_id: str,
    run_prefix: str,
    install_timeout_seconds: int,
) -> dict[str, Any]:
    run_id = f"{run_prefix}__{task_id}__noop"
    artifact_dir = batch.RAW_ROOT / run_id
    assert_probe_artifacts_available(run_id=run_id, artifact_dir=artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    workspace, prepare_summary = batch.prepare_workspace(task_id, run_id, artifact_dir)
    install_summary = batch.install_workspace(workspace, artifact_dir, install_timeout_seconds)
    noop = batch.no_op_verify(
        workspace=workspace,
        task_id=task_id,
        acut_id=PROBE_ACUT_ID,
        attempt=1,
        run_id=run_id,
        artifact_dir=artifact_dir,
    )
    result = noop.get("result") if isinstance(noop.get("result"), dict) else {}
    return {
        "run_id": run_id,
        "probe": "noop",
        "status": result.get("status"),
        "workspace": str(workspace),
        "artifact_dir": str(artifact_dir),
        "verification": result.get("verification"),
        "prepare": prepare_summary,
        "install": install_summary,
        "command": noop.get("command"),
    }


def task_probe(task: Mapping[str, Any], *, run_prefix: str, flakiness_runs: int, install_timeout_seconds: int) -> dict[str, Any]:
    task_id = str(task["task_id"])
    task_artifact_dir = batch.RAW_ROOT / f"{run_prefix}__{task_id}"
    task_artifact_dir.mkdir(parents=True, exist_ok=True)
    reference_patch = reference_patch_for_task(task)
    write_json(task_artifact_dir / "reference_patch_metadata.json", {"task_id": task_id, "patch_bytes": len(reference_patch)})
    known_bad_patch = known_bad_patch_for_task(task, task_id, run_prefix, task_artifact_dir)
    write_json(task_artifact_dir / "known_bad_patch_metadata.json", {"task_id": task_id, "patch_bytes": len(known_bad_patch)})

    noop = run_noop_probe(task_id=task_id, run_prefix=run_prefix, install_timeout_seconds=install_timeout_seconds)
    reference_runs = [
        verify_patch_text(
            task_id=task_id,
            run_prefix=run_prefix,
            probe_name=f"reference_{index}",
            patch_text=reference_patch,
            install_timeout_seconds=install_timeout_seconds,
        )
        for index in range(1, flakiness_runs + 1)
    ]
    known_bad = verify_patch_text(
        task_id=task_id,
        run_prefix=run_prefix,
        probe_name="known_bad",
        patch_text=known_bad_patch,
        install_timeout_seconds=install_timeout_seconds,
    )

    runtime_values = [
        duration
        for probe in [noop, *reference_runs, known_bad]
        if (duration := verification_duration(probe)) is not None
    ]
    runtime_p95 = p95(runtime_values)
    timeout = verifier_timeout_seconds(task_id)
    leakage = leakage_findings(
        [
            artifact
            for probe in [noop, *reference_runs, known_bad]
            for artifact in (
                (probe.get("verification") or {}).get("stdout_artifact") if isinstance(probe.get("verification"), dict) else None,
                (probe.get("verification") or {}).get("stderr_artifact") if isinstance(probe.get("verification"), dict) else None,
            )
        ]
    )
    flakiness_statuses = [probe.get("status") for probe in reference_runs]
    gates = {
        "no_op_probe": noop.get("status") == "failed",
        "reference_probe": bool(reference_runs) and reference_runs[0].get("status") == "passed",
        "known_bad_probe": known_bad.get("status") == "failed",
        "flakiness_probe": bool(flakiness_statuses) and len(set(flakiness_statuses)) == 1 and flakiness_statuses[0] == "passed",
        "verifier_runtime_p95_lt_timeout": runtime_p95 is not None and runtime_p95 < timeout,
        "oracle_log_leakage": not leakage["unsafe"],
        "clean_patch_replay": all(
            probe.get("status") == "passed"
            and isinstance(probe.get("verification"), dict)
            and probe["verification"].get("exit_code") == 0
            for probe in reference_runs
        ),
    }
    defect_classifications = admission_defect_classifications(
        gates=gates,
        noop=noop,
        reference_runs=reference_runs,
        known_bad=known_bad,
        leakage=leakage,
    )
    return {
        "task_id": task_id,
        "status": "passed" if all(gates.values()) else "failed",
        "gates": gates,
        "defect_classifications": defect_classifications,
        "runtime_p95_seconds": runtime_p95,
        "verifier_timeout_seconds": timeout,
            "oracle_log_leakage_findings": leakage,
            "clean_patch_replay": {
                "supported": True,
                "reference_probe_count": len(reference_runs),
                "separate_workspaces": len(
                    {
                        str(probe.get("workspace"))
                        for probe in reference_runs
                        if isinstance(probe.get("workspace"), str)
                    }
                )
                == len(reference_runs),
            },
            "noop": noop,
        "reference_runs": reference_runs,
        "known_bad": known_bad,
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        started_at = iso_now()
        if args.flakiness_runs < 2:
            raise ToolError("--flakiness-runs must be at least 2")
        requested_task_ids = unique_task_ids(args.tasks)
        task_split = str(args.task_split).lower()
        split_manifest_path = Path(args.task_split_manifest) if args.task_split_manifest else batch.task_split_manifest_path(task_split)
        split_manifest = load_manifest(split_manifest_path)
        manifest_split = str(split_manifest.get("split", task_split)).lower()
        if manifest_split != task_split:
            raise ToolError(
                "task split manifest split does not match --task-split",
                task_split=task_split,
                manifest_split=manifest_split,
                manifest_path=str(split_manifest_path),
            )
        tasks = batch.task_by_id(split_manifest)
        selected = []
        for task_id in requested_task_ids:
            if task_id not in tasks:
                raise ToolError(
                    "requested task is not in selected Click manifest",
                    task_id=task_id,
                    task_split=task_split,
                    manifest_path=str(split_manifest_path),
                )
            task = tasks[task_id]
            encoded_split = batch.split_from_task_id(task_id)
            task_fields = (("task_id", encoded_split), ("split", task.get("split")), ("benchmark_split", task.get("benchmark_split")))
            for field, value in task_fields:
                if isinstance(value, str) and value.lower() != task_split:
                    raise ToolError(
                        "requested task split does not match --task-split",
                        task_id=task_id,
                        field=field,
                        task_split=task_split,
                        observed_split=value.lower(),
                        manifest_path=str(split_manifest_path),
                    )
            if not batch.task_manifest_path(task_id).exists():
                raise ToolError("materialized task manifest is missing", task_id=task_id)
            selected.append(task)
        per_task = [
            task_probe(
                task,
                run_prefix=args.run_prefix,
                flakiness_runs=args.flakiness_runs,
                install_timeout_seconds=args.install_timeout_seconds,
            )
            for task in selected
        ]
        defect_counts: dict[str, int] = {}
        for item in per_task:
            for defect in item.get("defect_classifications", []):
                if not isinstance(defect, dict):
                    continue
                defect_class = str(defect.get("defect_class"))
                defect_counts[defect_class] = defect_counts.get(defect_class, 0) + 1
        payload = {
            "tool": TOOL,
            "status": "passed" if len(selected) >= 3 and all(item["status"] == "passed" for item in per_task) else "failed",
            "run_prefix": args.run_prefix,
            "task_split": task_split,
            "task_split_manifest": str(split_manifest_path),
            "started_at": started_at,
            "finished_at": iso_now(),
            "selected_tasks_count": len(selected),
            "selected_tasks_count_gate": len(selected) >= 3,
            "tasks": [str(task["task_id"]) for task in selected],
            "flakiness_runs": args.flakiness_runs,
            "defect_classification_counts": dict(sorted(defect_counts.items())),
            "per_task": per_task,
        }
        emit_json(payload, args.output)
        return 0 if payload["status"] == "passed" else 2
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
