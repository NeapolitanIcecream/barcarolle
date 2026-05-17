#!/usr/bin/env python3
"""Run a redacted official SWE-bench gold smoke for Phase 0 admission."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import external_calibrated_repository_admission as admission
from _common import ToolError, emit_json, fail, iso_now, write_json


TOOL = "external_calibrated_swebench_smoke"
SCHEMA_VERSION = "external-calibrated-repo-benchmark.swebench-smoke-summary.v1"
PROTOCOL_ID = admission.PROTOCOL_ID
REPO_ROOT = admission.REPO_ROOT
RESULTS_ROOT = admission.RESULTS_ROOT
DEFAULT_OUTPUT = RESULTS_ROOT / "repository_admission/swebench_gold_smoke_summary_20260515.json"
DEFAULT_RAW_ROOT = RESULTS_ROOT / "repository_admission/raw_swebench_smoke"
DEFAULT_DATASET = "SWE-bench/SWE-bench_Verified"
DEFAULT_SPLIT = "test"
DEFAULT_REPO = "sympy/sympy"
DEFAULT_RUN_ID = "external_calibrated_sympy_gold_smoke_20260515_w5"
DEFAULT_SELECTION_SALT = "external-calibrated-repo-benchmark-v1:swebench-gold-smoke:v1"
SENSITIVE_RAW_NAMES = {
    "patch.diff",
    "eval.sh",
    "test_output.txt",
    "run_instance.log",
    "report.json",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Redacted JSON summary output.")
    parser.add_argument("--dataset-name", default=DEFAULT_DATASET, help="SWE-bench dataset name.")
    parser.add_argument("--split", default=DEFAULT_SPLIT, help="SWE-bench split.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Repository id, or a known slug such as sympy.")
    parser.add_argument("--sample-size", type=int, default=5, help="Deterministic sample size when instance ids are omitted.")
    parser.add_argument("--instance-id", action="append", help="Explicit instance id. May be repeated.")
    parser.add_argument("--selection-salt", default=DEFAULT_SELECTION_SALT, help="Deterministic sample salt.")
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID, help="Official harness run id.")
    parser.add_argument("--raw-dir", help="Raw harness directory. Defaults under results/repository_admission/raw_swebench_smoke.")
    parser.add_argument("--python", default=sys.executable, help="Python executable that can import swebench.")
    parser.add_argument("--max-workers", type=int, default=1, help="Official harness worker count.")
    parser.add_argument("--timeout", type=int, default=900, help="Per-instance harness timeout in seconds.")
    parser.add_argument("--command-timeout", type=int, default=7200, help="Overall subprocess timeout in seconds.")
    parser.add_argument("--cache-level", default="base", choices=["none", "base", "env", "instance"], help="SWE-bench cache level.")
    parser.add_argument("--retain-raw", action="store_true", help="Keep raw harness artifacts for local debugging.")
    return parser.parse_args(list(argv) if argv is not None else None)


def repo_id_from_arg(value: str) -> str:
    if "/" in value:
        return value
    repo_spec = admission.REPOSITORIES.get(value)
    if not repo_spec:
        raise ToolError("unknown repository slug", repo=value)
    return str(repo_spec["repo_id"])


def selection_key(*, salt: str, instance_id: str) -> str:
    return admission.digest_parts(salt, instance_id)


def select_instance_ids(
    rows: Sequence[Mapping[str, Any]],
    *,
    repo_id: str,
    sample_size: int,
    explicit_instance_ids: Sequence[str] | None,
    salt: str,
) -> list[str]:
    available = [str(row.get("instance_id")) for row in rows if row.get("repo") == repo_id and row.get("instance_id")]
    available_set = set(available)
    if explicit_instance_ids:
        missing = [instance_id for instance_id in explicit_instance_ids if instance_id not in available_set]
        if missing:
            raise ToolError("explicit instance ids were not found for repo", repo=repo_id, missing_instance_ids=missing)
        return list(dict.fromkeys(explicit_instance_ids))
    if sample_size <= 0:
        raise ToolError("sample size must be positive", sample_size=sample_size)
    ordered = sorted(available, key=lambda instance_id: (selection_key(salt=salt, instance_id=instance_id), instance_id))
    if len(ordered) < sample_size:
        raise ToolError("not enough repo instances for requested smoke sample", repo=repo_id, available=len(ordered), requested=sample_size)
    return ordered[:sample_size]


def load_dataset_rows(dataset_name: str, *, split: str) -> list[dict[str, Any]]:
    try:
        from datasets import load_dataset  # type: ignore[import-not-found]
    except ImportError:
        return admission.fetch_dataset_rows(dataset_name, split=split)
    try:
        dataset = load_dataset(dataset_name, split=split)
    except Exception:
        return admission.fetch_dataset_rows(dataset_name, split=split)
    return [dict(row) for row in dataset]


def harness_command(args: argparse.Namespace, instance_ids: Sequence[str]) -> list[str]:
    return [
        python_executable(args.python),
        "-m",
        "swebench.harness.run_evaluation",
        "--dataset_name",
        args.dataset_name,
        "--split",
        args.split,
        "--predictions_path",
        "gold",
        "--instance_ids",
        *instance_ids,
        "--max_workers",
        str(args.max_workers),
        "--timeout",
        str(args.timeout),
        "--cache_level",
        args.cache_level,
        "--run_id",
        args.run_id,
        "--report_dir",
        "reports",
    ]


def python_executable(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or "/" not in value:
        return value
    return str((REPO_ROOT / path).absolute())


def command_digest(value: str) -> dict[str, Any]:
    return {
        "sha256": admission.sha256_text(value),
        "line_count": len(value.splitlines()),
        "byte_count": len(value.encode("utf-8", errors="replace")),
    }


def run_harness(args: argparse.Namespace, raw_dir: Path, instance_ids: Sequence[str]) -> tuple[subprocess.CompletedProcess[str] | None, float, str | None]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    command = harness_command(args, instance_ids)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=raw_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=args.command_timeout,
            check=False,
        )
        return completed, time.monotonic() - started, None
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        return None, duration, f"harness command timed out after {args.command_timeout} seconds"


def load_run_report(raw_dir: Path, run_id: str) -> dict[str, Any]:
    report_path = raw_dir / f"gold.{run_id}.json"
    if not report_path.exists():
        return {}
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError("failed to parse SWE-bench run report", path=admission.repo_relative(report_path), cause=str(exc)) from exc
    if not isinstance(payload, dict):
        raise ToolError("SWE-bench run report was not an object", path=admission.repo_relative(report_path))
    return payload


def report_id_list(report: Mapping[str, Any], key: str) -> list[str]:
    value = report.get(key)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def safe_dataset_metadata(dataset_name: str) -> dict[str, Any]:
    try:
        return admission.dataset_api_metadata(dataset_name)
    except Exception as exc:
        return {
            "dataset": dataset_name,
            "metadata_fetch_error_type": type(exc).__name__,
            "metadata_fetch_error_digest": admission.sha256_text(str(exc)),
        }


def raw_artifact_inventory(raw_dir: Path) -> dict[str, Any]:
    file_count = 0
    total_bytes = 0
    sensitive_count = 0
    sensitive_path_digests: list[str] = []
    if not raw_dir.exists():
        return {
            "file_count": 0,
            "total_bytes": 0,
            "sensitive_file_count": 0,
            "sensitive_path_digests": [],
        }
    for path in raw_dir.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        file_count += 1
        try:
            total_bytes += path.stat().st_size
        except OSError:
            pass
        if path.name in SENSITIVE_RAW_NAMES:
            sensitive_count += 1
            sensitive_path_digests.append(admission.sha256_text(path.relative_to(raw_dir).as_posix()))
    return {
        "file_count": file_count,
        "total_bytes": total_bytes,
        "sensitive_file_count": sensitive_count,
        "sensitive_path_digests": sorted(sensitive_path_digests),
    }


def ensure_deletable_raw_dir(raw_dir: Path) -> None:
    resolved = raw_dir.resolve()
    allowed_roots = [
        (RESULTS_ROOT / "repository_admission").resolve(),
    ]
    if not any(resolved == root or root in resolved.parents for root in allowed_roots):
        raise ToolError("refusing to delete raw directory outside repository admission results", raw_dir=str(raw_dir))


def cleanup_raw_dir(raw_dir: Path) -> bool:
    if not raw_dir.exists():
        return True
    ensure_deletable_raw_dir(raw_dir)
    shutil.rmtree(raw_dir)
    return not raw_dir.exists()


def build_summary(
    args: argparse.Namespace,
    *,
    repo_id: str,
    rows: Sequence[Mapping[str, Any]],
    instance_ids: Sequence[str],
    report: Mapping[str, Any],
    completed: subprocess.CompletedProcess[str] | None,
    duration_seconds: float,
    timeout_error: str | None,
    inventory: Mapping[str, Any],
    raw_deleted: bool,
    raw_dir: Path,
) -> dict[str, Any]:
    metadata = safe_dataset_metadata(args.dataset_name)
    exit_code = completed.returncode if completed is not None else None
    completed_instances = int(report.get("completed_instances", 0) or 0)
    resolved_instances = int(report.get("resolved_instances", 0) or 0)
    error_instances = int(report.get("error_instances", len(instance_ids)) or 0)
    empty_patch_instances = int(report.get("empty_patch_instances", 0) or 0)
    unresolved_instances = int(report.get("unresolved_instances", 0) or 0)
    passed = (
        completed is not None
        and exit_code == 0
        and completed_instances == len(instance_ids)
        and resolved_instances == len(instance_ids)
        and error_instances == 0
        and empty_patch_instances == 0
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "smoke_id": args.run_id,
        "benchmark_source": args.dataset_name,
        "split": args.split,
        "repo": repo_id,
        "prediction_source": "gold",
        "dataset_metadata": metadata,
        "selection_rule": {
            "source": "Hugging Face dataset rows filtered by repository id",
            "salt": args.selection_salt,
            "sample_size": args.sample_size if not args.instance_id else None,
            "explicit_instance_ids_used": bool(args.instance_id),
        },
        "instance_ids": list(instance_ids),
        "instance_id_digests": [admission.digest_parts(repo_id, instance_id) for instance_id in instance_ids],
        "dataset_repo_instance_count": sum(1 for row in rows if row.get("repo") == repo_id),
        "total_instances_requested": len(instance_ids),
        "completed_instances": completed_instances,
        "resolved_instances": resolved_instances,
        "unresolved_instances": unresolved_instances,
        "empty_patch_instances": empty_patch_instances,
        "error_instances": error_instances,
        "completed_ids": report_id_list(report, "completed_ids"),
        "resolved_ids": report_id_list(report, "resolved_ids"),
        "unresolved_ids": report_id_list(report, "unresolved_ids"),
        "empty_patch_ids": report_id_list(report, "empty_patch_ids"),
        "error_ids": report_id_list(report, "error_ids"),
        "harness": {
            "exit_code": exit_code,
            "duration_seconds": round(duration_seconds, 3),
            "timeout_error": timeout_error,
            "stdout": command_digest(completed.stdout if completed is not None else ""),
            "stderr": command_digest(completed.stderr if completed is not None else ""),
            "python_executable": args.python,
            "max_workers": args.max_workers,
            "timeout_seconds_per_instance": args.timeout,
            "cache_level": args.cache_level,
        },
        "raw_artifact_count_before_redaction": inventory.get("file_count", 0),
        "raw_artifact_total_bytes_before_redaction": inventory.get("total_bytes", 0),
        "raw_sensitive_artifact_count_before_redaction": inventory.get("sensitive_file_count", 0),
        "raw_artifact_path_digests_before_redaction": inventory.get("sensitive_path_digests", []),
        "raw_artifacts_retained": bool(args.retain_raw),
        "raw_dir_path": admission.repo_relative(raw_dir) if args.retain_raw else None,
        "raw_dir_deleted": raw_deleted,
        "redaction_policy": {
            "raw_gold_patch_retained": bool(args.retain_raw),
            "raw_eval_script_retained": bool(args.retain_raw),
            "raw_test_output_retained": bool(args.retain_raw),
            "raw_instance_report_retained": bool(args.retain_raw),
            "reason": "Do not leave E gold patches or hidden verifier/test material in artifacts that can be read during B generation.",
        },
        "pass": passed,
    }


def raw_dir_for(args: argparse.Namespace) -> Path:
    if args.raw_dir:
        path = Path(args.raw_dir)
        return path if path.is_absolute() else REPO_ROOT / path
    return DEFAULT_RAW_ROOT / args.run_id


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_id = repo_id_from_arg(args.repo)
    rows = load_dataset_rows(args.dataset_name, split=args.split)
    instance_ids = select_instance_ids(
        rows,
        repo_id=repo_id,
        sample_size=args.sample_size,
        explicit_instance_ids=args.instance_id,
        salt=args.selection_salt,
    )
    raw_dir = raw_dir_for(args)
    if raw_dir.exists():
        ensure_deletable_raw_dir(raw_dir)
        shutil.rmtree(raw_dir)
    completed, duration, timeout_error = run_harness(args, raw_dir, instance_ids)
    report = load_run_report(raw_dir, args.run_id)
    inventory = raw_artifact_inventory(raw_dir)
    raw_deleted = False if args.retain_raw else cleanup_raw_dir(raw_dir)
    summary = build_summary(
        args,
        repo_id=repo_id,
        rows=rows,
        instance_ids=instance_ids,
        report=report,
        completed=completed,
        duration_seconds=duration,
        timeout_error=timeout_error,
        inventory=inventory,
        raw_deleted=raw_deleted,
        raw_dir=raw_dir,
    )
    output = Path(args.output)
    write_json(output, summary)
    emit_json({**summary, "output_path": admission.repo_relative(output)})
    return 0 if summary["pass"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
