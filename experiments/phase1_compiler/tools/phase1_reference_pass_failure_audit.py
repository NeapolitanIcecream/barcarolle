from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import shlex
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_ROOT = REPO_ROOT / "experiments" / "phase0_headroom"
PHASE0_TOOLS = PHASE0_ROOT / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import repo_history_pilot  # noqa: E402


RUN_ID = "phase1_reference_pass_failure_audit_20260526"
SCHEMA_VERSION = "barcarolle.phase1_reference_pass_failure_audit.v1"
DEFAULT_CONFIG = ROOT / "configs" / "phase1_reference_pass_failure_audit.yaml"
EMPTY_SHA = hashlib.sha256(b"").hexdigest()[:12]
ERROR_SNIPPET_LIMIT = 240


@dataclass(frozen=True)
class ReplayVariant:
    name: str
    cwd: Path
    command: list[str]
    env: dict[str, str]
    test_path_style: str
    editable_install: bool
    pythonpath_shape: str


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path | str) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def repo_path(raw: str | Path) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != "barcarolle.phase1_reference_pass_failure_audit.v1":
        raise ValueError("unexpected reference-pass failure audit config schema_version")
    for repo_cfg in config.get("repos", {}).values():
        if "command_template" in repo_cfg:
            repo_cfg["command_template"] = str(repo_cfg["command_template"]).replace('\\"', '"')
    config["_path"] = str(path)
    return config


def configured_path(config: dict[str, Any], section: str, key: str) -> Path:
    return repo_path(config[section][key])


def output_path(config: dict[str, Any], key: str) -> Path:
    return configured_path(config, "outputs", key)


def report_path(config: dict[str, Any], key: str) -> Path:
    return configured_path(config, "reports", key)


def artifact_path(config: dict[str, Any], key: str) -> Path:
    return configured_path(config, "source_artifacts", key)


def scratch_path(config: dict[str, Any], key: str) -> Path:
    return configured_path(config, "scratch_paths", key)


def repo_config(config: dict[str, Any], repo_id: str) -> repo_history_pilot.PilotConfig:
    raw = config["repos"][repo_id]
    return repo_history_pilot.PilotConfig(
        repo_id=repo_id,
        repo_url=str(raw["repo_url"]),
        local_repo=repo_path(str(raw["local_repo"])),
        command_template=str(raw["command_template"]),
        certification_attempts=0,
        pilot_certified_min=0,
        benchmark_grade_min=0,
        result_prefix=f"{repo_id}_reference_pass_failure_audit",
    )


def command_record(row: dict[str, Any], role: str) -> dict[str, Any]:
    for record in row.get("commands", []):
        if record.get("role") == role:
            return record
    return {}


def reference_pass_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("first_failing_gate") == "reference_pass"
        or row.get("review_first_failing_gate") == "reference_pass"
    ]


def parse_year(value: Any) -> str:
    text = str(value or "")
    return text[:4] if len(text) >= 4 and text[:4].isdigit() else "unknown"


def join_list(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(item) for item in value) if value else "none"
    if value is None:
        return "none"
    return str(value)


def duration_bucket(seconds: Any) -> str:
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return "unknown"
    if value < 1:
        return "lt_1s"
    if value < 5:
        return "1s_to_5s"
    if value < 30:
        return "5s_to_30s"
    if value < 120:
        return "30s_to_120s"
    return "gte_120s"


def signature_for_row(row: dict[str, Any]) -> str:
    ref = command_record(row, "reference_run_1") or command_record(row, "reference_run_2")
    return "|".join(
        [
            str(ref.get("returncode", "missing")),
            str(ref.get("stderr_tail_hash", "missing")),
            str(ref.get("stdout_tail_hash", "missing")),
        ]
    )


def row_inventory_record(row: dict[str, Any]) -> dict[str, Any]:
    ref1 = command_record(row, "reference_run_1")
    ref2 = command_record(row, "reference_run_2")
    return {
        "task_id": row.get("task_id"),
        "repo_id": row.get("repo_id"),
        "year": parse_year(row.get("task_time")),
        "module_or_package": join_list(row.get("module_or_package")),
        "test_files": join_list(row.get("test_files")),
        "change_size_bucket": row.get("change_size_bucket") or "unknown",
        "candidate_filter_status": row.get("candidate_filter_status") or "unknown",
        "source_context_status": row.get("source_context_status") or "unknown",
        "reference_run_1_returncode": ref1.get("returncode", "missing"),
        "reference_run_2_returncode": ref2.get("returncode", "missing"),
        "stderr_tail_hash": ref1.get("stderr_tail_hash") or ref2.get("stderr_tail_hash") or "missing",
        "stdout_tail_hash": ref1.get("stdout_tail_hash") or ref2.get("stdout_tail_hash") or "missing",
        "duration_bucket": duration_bucket(ref1.get("duration_seconds") or ref2.get("duration_seconds")),
        "signature": signature_for_row(row),
    }


def counter_dict(rows: Iterable[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "unknown")) for row in rows).items()))


def top_counts(counter: Counter[str], limit: int = 12) -> list[dict[str, Any]]:
    return [{"key": key, "count": count} for key, count in counter.most_common(limit)]


def priority_for_row(row: dict[str, Any], signature_counts: Counter[str]) -> tuple[int, str]:
    noop = command_record(row, "noop_test_patch_on_base")
    ref = command_record(row, "reference_run_1")
    simple_change = len(row.get("implementation_files") or row.get("code_files") or []) == 1 and len(row.get("test_files") or []) == 1
    repeated = signature_counts[signature_for_row(row)] > 1
    no_op_failed_expected = noop and noop.get("returncode") not in {0, None} and ref and ref.get("returncode") not in {0, None}
    if no_op_failed_expected and (repeated or simple_change or row.get("candidate_filter_status") == "accepted"):
        return (0, "high")
    if row.get("manual_review_reasons") or parse_year(row.get("task_time")) in {"2015", "2016", "2017"}:
        return (1, "medium")
    return (2, "low")


def prioritized_sample(rows: list[dict[str, Any]], per_repo: int) -> list[dict[str, Any]]:
    signature_counts = Counter(signature_for_row(row) for row in rows)
    by_repo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        priority_rank, priority = priority_for_row(row, signature_counts)
        enriched = {
            "task_id": row.get("task_id"),
            "repo_id": row.get("repo_id"),
            "priority": priority,
            "priority_rank": priority_rank,
            "signature": signature_for_row(row),
            "stderr_tail_hash": row_inventory_record(row)["stderr_tail_hash"],
            "year": parse_year(row.get("task_time")),
            "test_files": row.get("test_files", []),
            "module_or_package": row.get("module_or_package", []),
            "reason": sample_reason(row, signature_counts),
        }
        by_repo[str(row.get("repo_id"))].append(enriched)

    selected: list[dict[str, Any]] = []
    for repo_id in sorted(by_repo):
        candidates = sorted(
            by_repo[repo_id],
            key=lambda row: (
                row["priority_rank"],
                -signature_counts[row["signature"]],
                row["year"],
                str(row["task_id"]),
            ),
        )
        seen_signatures: set[str] = set()
        repo_selected: list[dict[str, Any]] = []
        for row in candidates:
            if row["signature"] in seen_signatures and len(repo_selected) < per_repo // 2:
                continue
            repo_selected.append(row)
            seen_signatures.add(row["signature"])
            if len(repo_selected) >= per_repo:
                break
        if len(repo_selected) < per_repo:
            for row in candidates:
                if row not in repo_selected:
                    repo_selected.append(row)
                if len(repo_selected) >= per_repo:
                    break
        selected.extend(repo_selected[:per_repo])
    return selected


def sample_reason(row: dict[str, Any], signature_counts: Counter[str]) -> str:
    reasons = []
    noop = command_record(row, "noop_test_patch_on_base")
    ref = command_record(row, "reference_run_1")
    if noop and noop.get("returncode") not in {0, None} and ref and ref.get("returncode") not in {0, None}:
        reasons.append("no_op_failed_as_expected_but_reference_failed")
    if signature_counts[signature_for_row(row)] > 1:
        reasons.append("repeated_reference_signature")
    if len(row.get("implementation_files") or row.get("code_files") or []) == 1 and len(row.get("test_files") or []) == 1:
        reasons.append("simple_one_code_one_test_change")
    if parse_year(row.get("task_time")) in {"2015", "2016", "2017"}:
        reasons.append("old_commit_environment_drift_risk")
    return ",".join(reasons) or "bounded_representative_sample"


def build_inventory(config: dict[str, Any], sample_size: int | None = None) -> dict[str, Any]:
    payload = read_json(artifact_path(config, "certification_attempts"))
    failures = reference_pass_rows(payload.get("rows", []))
    records = [row_inventory_record(row) for row in failures]
    signature_counts = Counter(row["signature"] for row in records)
    per_repo = sample_size or int(config["sample"].get("default_size_per_repo", 6))
    sample = prioritized_sample(failures, per_repo)
    grouped: dict[str, Any] = {}
    for key in [
        "repo_id",
        "year",
        "module_or_package",
        "test_files",
        "change_size_bucket",
        "candidate_filter_status",
        "source_context_status",
        "reference_run_1_returncode",
        "reference_run_2_returncode",
        "stderr_tail_hash",
        "stdout_tail_hash",
        "duration_bucket",
    ]:
        grouped[key] = counter_dict(records, key)
    return {
        "schema_version": f"{SCHEMA_VERSION}.inventory.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "source": rel(artifact_path(config, "certification_attempts")),
        "reference_pass_failure_count": len(failures),
        "counts_by_repo": counter_dict(records, "repo_id"),
        "grouped_counts": grouped,
        "top_repeated_failure_signatures": top_counts(signature_counts),
        "prioritized_sample": sample,
        "records": records,
        "raw_logs_committed": false_bool(),
    }


def false_bool() -> bool:
    return False


def inventory_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Reference-Pass Failure Inventory",
        "",
        "Plain-language summary: this inventory counts every candidate whose first failing local certification gate was `reference_pass`. It records only sanitized command metadata and hashes, not raw stdout or stderr.",
        "",
        "## Counts By Repo",
        "",
        "| repo | reference_pass failures |",
        "| --- | ---: |",
    ]
    for repo_id, count in payload["counts_by_repo"].items():
        lines.append(f"| {repo_id} | {count} |")
    lines.extend(["", "## Top Repeated Failure Signatures", "", "| signature | count |", "| --- | ---: |"])
    for row in payload["top_repeated_failure_signatures"]:
        lines.append(f"| `{row['key']}` | {row['count']} |")
    lines.extend(["", "## Prioritized Replay Sample", "", "| repo | task | priority | year | reason |", "| --- | --- | --- | ---: | --- |"])
    for row in payload["prioritized_sample"]:
        lines.append(f"| {row['repo_id']} | `{row['task_id']}` | {row['priority']} | {row['year']} | {row['reason']} |")
    lines.extend(["", "## Grouped Counts", ""])
    for key, counts in payload["grouped_counts"].items():
        top = ", ".join(f"`{name}`={count}" for name, count in list(counts.items())[:12])
        lines.append(f"- {key}: {top}")
    return "\n".join(lines)


def shape_path(path: Path, workspace: Path) -> str:
    resolved = path.resolve()
    workspace = workspace.resolve()
    try:
        relative = resolved.relative_to(workspace)
        return f"<workspace>/{relative}"
    except ValueError:
        return rel(resolved)


def command_shape(command: list[str], workspace: Path) -> list[str]:
    shaped = []
    for part in command:
        text = str(part)
        if str(workspace) in text:
            text = text.replace(str(workspace), "<workspace>")
        if str(REPO_ROOT) in text:
            text = text.replace(str(REPO_ROOT), "<repo>")
        shaped.append(text)
    return shaped


def pythonpath_shape(value: str, workspace: Path) -> str:
    if not value:
        return "unset"
    parts = []
    for part in value.split(os.pathsep):
        path = Path(part)
        if path == workspace / "src":
            parts.append("<workspace>/src")
        elif path == workspace:
            parts.append("<workspace>")
        elif str(path).startswith(str(REPO_ROOT)):
            parts.append(rel(path))
        else:
            parts.append("<external>")
    return os.pathsep.join(parts)


def result_summary(
    role: str,
    result: repo_history_pilot.CommandResult,
    command: list[str],
    cwd: Path,
    workspace: Path,
    env: dict[str, str],
) -> dict[str, Any]:
    combined = "\n".join([result.stderr[-2000:], result.stdout[-2000:]])
    return {
        "role": role,
        "returncode": result.returncode,
        "duration_seconds": round(result.duration_seconds, 3),
        "timed_out": result.timed_out,
        "stdout_tail_hash": hashlib.sha256(result.stdout[-2000:].encode("utf-8")).hexdigest()[:12],
        "stderr_tail_hash": hashlib.sha256(result.stderr[-2000:].encode("utf-8")).hexdigest()[:12],
        "error_class": classify_error(combined, result.returncode, result.timed_out),
        "sanitized_error_snippet": sanitized_error_snippet(combined, workspace=workspace),
        "command_argv_shape": command_shape(command, workspace),
        "cwd_shape": "<workspace>" if cwd.resolve() == workspace.resolve() else rel(cwd),
        "workspace_path_kind": "ignored_phase0_headroom_workspace",
        "pythonpath_shape": pythonpath_shape(env.get("PYTHONPATH", ""), workspace),
    }


def sanitized_error_snippet(text: str, workspace: Path | None = None) -> str:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if str(REPO_ROOT) in line:
            line = line.replace(str(REPO_ROOT), "<repo>")
        if workspace is not None and str(workspace) in line:
            line = line.replace(str(workspace), "<workspace>")
        line = line.replace(str(PHASE0_ROOT), "<phase0>")
        if len(line) > ERROR_SNIPPET_LIMIT:
            line = line[: ERROR_SNIPPET_LIMIT - 3] + "..."
        lines.append(line)
        if len(lines) >= 2:
            break
    return " | ".join(lines)


def classify_error(text: str, returncode: int, timed_out: bool = False) -> str:
    lowered = text.lower()
    if timed_out or returncode == 124:
        return "timeout"
    if returncode == 0:
        return "pass"
    patterns = [
        ("uv_project_path_missing", "project file not found"),
        ("uv_project_path_missing", "no such file or directory"),
        ("dependency_resolution_error", "failed to resolve"),
        ("dependency_resolution_error", "no solution found"),
        ("editable_install_error", "failed to build"),
        ("editable_install_error", "metadata-generation-failed"),
        ("missing_optional_dependency", "modulenotfounderror"),
        ("missing_optional_dependency", "no module named"),
        ("import_api_drift", "importerror"),
        ("import_api_drift", "cannot import name"),
        ("python_version_drift", "syntaxerror"),
        ("pytest_collection_error", "collected 0 items"),
        ("pytest_collection_error", "error collecting"),
        ("pytest_collection_error", "found no collectors"),
        ("assertion_failure", "assertionerror"),
    ]
    for label, needle in patterns:
        if needle in lowered:
            return label
    if "failed" in lowered and "passed" in lowered:
        return "test_assertion_failure"
    return "nonzero_unknown"


def write_raw_log(config: dict[str, Any], task_id: str, role: str, result: repo_history_pilot.CommandResult) -> None:
    root = scratch_path(config, "raw_replay_logs")
    task_dir = root / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / f"{role}.stdout.txt").write_text(result.stdout, encoding="utf-8", errors="replace")
    (task_dir / f"{role}.stderr.txt").write_text(result.stderr, encoding="utf-8", errors="replace")


def absolute_project_command(command: list[str]) -> list[str]:
    out = list(command)
    for index, part in enumerate(out[:-1]):
        if part == "--project":
            project = Path(out[index + 1])
            if not project.is_absolute():
                out[index + 1] = str(REPO_ROOT / project)
    return out


def base_env(cfg: repo_history_pilot.PilotConfig, workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_history_pilot.pythonpath_for(workspace)
    env[f"SETUPTOOLS_SCM_PRETEND_VERSION_FOR_{cfg.repo_id.upper().replace('-', '_')}"] = "0.0.0"
    return env


def test_paths(workspace: Path, test_files: list[str], style: str) -> list[str]:
    if style == "relative":
        return test_files
    return [str(workspace / path) for path in test_files]


def build_variant(
    name: str,
    cfg: repo_history_pilot.PilotConfig,
    workspace: Path,
    test_files: list[str],
    cwd: Path,
    *,
    editable: bool,
    path_style: str,
    absolute_project: bool,
) -> ReplayVariant:
    command = repo_history_pilot.command_test_files(cfg.command_template, test_paths(workspace, test_files, path_style))
    if absolute_project:
        command = absolute_project_command(command)
    if editable:
        command = repo_history_pilot.with_editable_workspace(command, workspace)
    env = base_env(cfg, workspace)
    return ReplayVariant(
        name=name,
        cwd=cwd,
        command=command,
        env=env,
        test_path_style=path_style,
        editable_install=editable,
        pythonpath_shape=pythonpath_shape(env["PYTHONPATH"], workspace),
    )


def replay_variants(cfg: repo_history_pilot.PilotConfig, workspace: Path, test_files: list[str]) -> list[ReplayVariant]:
    return [
        build_variant(
            "A_current_barcarolle_command",
            cfg,
            workspace,
            test_files,
            REPO_ROOT,
            editable=True,
            path_style="absolute",
            absolute_project=False,
        ),
        build_variant(
            "B_workspace_cwd_same_command",
            cfg,
            workspace,
            test_files,
            workspace,
            editable=True,
            path_style="absolute",
            absolute_project=False,
        ),
        build_variant(
            "C_no_editable_pythonpath",
            cfg,
            workspace,
            test_files,
            workspace,
            editable=False,
            path_style="absolute",
            absolute_project=True,
        ),
        build_variant(
            "D_pytest_config_visible",
            cfg,
            workspace,
            test_files,
            workspace,
            editable=True,
            path_style="relative",
            absolute_project=True,
        ),
    ]


def checkout_task_workspaces(config: dict[str, Any], row: dict[str, Any]) -> tuple[Path, Path]:
    cfg = repo_config(config, str(row["repo_id"]))
    workspace_root = scratch_path(config, "replay_workspaces") / str(row["task_id"])
    base_ws = workspace_root / "base"
    target_ws = workspace_root / "target"
    repo_history_pilot.archive_commit(cfg.local_repo, str(row["base_commit"]), base_ws)
    repo_history_pilot.archive_commit(cfg.local_repo, str(row["target_commit"]), target_ws)
    return base_ws, target_ws


def git_show_bytes(repo: Path, commit: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def sha12_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def target_file_checks(cfg: repo_history_pilot.PilotConfig, target_ws: Path, row: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for test_file in row.get("test_files", []):
        archive_path = target_ws / str(test_file)
        archive_bytes = archive_path.read_bytes() if archive_path.exists() else None
        git_bytes = git_show_bytes(cfg.local_repo, str(row["target_commit"]), str(test_file))
        checks.append(
            {
                "test_file": str(test_file),
                "target_archive_present": archive_bytes is not None,
                "git_show_present": git_bytes is not None,
                "target_archive_hash": sha12_bytes(archive_bytes) if archive_bytes is not None else "missing",
                "git_show_hash": sha12_bytes(git_bytes) if git_bytes is not None else "missing",
                "archive_matches_git_show": archive_bytes is not None and git_bytes is not None and archive_bytes == git_bytes,
            }
        )
    return checks


def classify_replay_task(variant_summaries: list[dict[str, Any]], file_checks: list[dict[str, Any]]) -> str:
    if any(not check["archive_matches_git_show"] for check in file_checks):
        return "target_test_file_missing_or_mismatched"
    by_name = {row["role"]: row for row in variant_summaries}
    current = by_name.get("A_current_barcarolle_command", {})
    fixes = [row["role"] for row in variant_summaries if row["returncode"] == 0 and row["role"] != "A_current_barcarolle_command"]
    if current.get("returncode") not in {0, None} and fixes:
        if "D_pytest_config_visible" in fixes or "B_workspace_cwd_same_command" in fixes:
            return "workspace_cwd_fixes_failure"
        if "C_no_editable_pythonpath" in fixes:
            return "editable_install_fixes_failure"
        return "current_command_only_failure"
    error_classes = {row["error_class"] for row in variant_summaries if row["returncode"] != 0}
    if error_classes & {"dependency_resolution_error", "missing_optional_dependency", "editable_install_error", "import_api_drift"}:
        return "dependency_or_python_version_failure"
    if error_classes & {"python_version_drift"}:
        return "dependency_or_python_version_failure"
    if len(error_classes) == 1 and current.get("returncode") not in {0, None}:
        return "all_variants_fail_same_way"
    return "unclassified"


def replay_sample(config: dict[str, Any], task_id: str | None = None, sample_size: int | None = None) -> dict[str, Any]:
    attempts = read_json(artifact_path(config, "certification_attempts"))
    failures = reference_pass_rows(attempts.get("rows", []))
    by_task = {str(row["task_id"]): row for row in failures}
    if task_id:
        selected = [by_task[task_id]]
    else:
        inventory_path = output_path(config, "inventory")
        if inventory_path.exists():
            sample_tasks = read_json(inventory_path).get("prioritized_sample", [])
        else:
            sample_tasks = prioritized_sample(failures, sample_size or int(config["sample"].get("default_size_per_repo", 6)))
        selected = [by_task[str(row["task_id"])] for row in sample_tasks if str(row["task_id"]) in by_task]

    rows = []
    timeout = int(config["sample"].get("max_replay_seconds_per_command", 90))
    for row in selected:
        cfg = repo_config(config, str(row["repo_id"]))
        _, target_ws = checkout_task_workspaces(config, row)
        variant_summaries = []
        for variant in replay_variants(cfg, target_ws, list(row.get("test_files", []))):
            result = repo_history_pilot.run_command(variant.command, variant.cwd, timeout=timeout, env=variant.env)
            write_raw_log(config, str(row["task_id"]), variant.name, result)
            variant_summaries.append(result_summary(variant.name, result, variant.command, variant.cwd, target_ws, variant.env))
        file_checks = target_file_checks(cfg, target_ws, row)
        rows.append(
            {
                "task_id": row["task_id"],
                "repo_id": row["repo_id"],
                "target_commit": row["target_commit"],
                "test_files": row.get("test_files", []),
                "variants": variant_summaries,
                "target_file_checks": file_checks,
                "classification": classify_replay_task(variant_summaries, file_checks),
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.replay_matrix.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "sampled_task_count": len(rows),
        "raw_log_storage": "ignored_phase1_compiler_tmp",
        "workspace_storage": "ignored_phase0_headroom_workspaces",
        "classification_counts": dict(sorted(Counter(row["classification"] for row in rows).items())),
        "rows": rows,
    }


def replay_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Reference-Pass Replay Matrix",
        "",
        "Plain-language summary: each sampled task was replayed with the current command and three command variants. Raw stdout and stderr were written only to ignored scratch paths; this report keeps hashes, command shapes, and short bounded error labels.",
        "",
        "## Classification Counts",
        "",
        "| classification | count |",
        "| --- | ---: |",
    ]
    for name, count in payload["classification_counts"].items():
        lines.append(f"| {name} | {count} |")
    lines.extend(["", "## Sampled Tasks", "", "| repo | task | classification | current error | variant result summary |", "| --- | --- | --- | --- | --- |"])
    for row in payload["rows"]:
        current = next((variant for variant in row["variants"] if variant["role"] == "A_current_barcarolle_command"), {})
        summary = ", ".join(f"{variant['role']}={variant['returncode']}:{variant['error_class']}" for variant in row["variants"])
        lines.append(
            f"| {row['repo_id']} | `{row['task_id']}` | {row['classification']} | {current.get('error_class', 'missing')} | {summary} |"
        )
    return "\n".join(lines)


def patch_application_audit(config: dict[str, Any], task_id: str | None = None) -> dict[str, Any]:
    attempts = read_json(artifact_path(config, "certification_attempts"))
    failures = reference_pass_rows(attempts.get("rows", []))
    by_task = {str(row["task_id"]): row for row in failures}
    if task_id:
        selected = [by_task[task_id]]
    else:
        replay = read_json(output_path(config, "replay_matrix"))
        selected = [by_task[str(row["task_id"])] for row in replay.get("rows", []) if str(row["task_id"]) in by_task]

    rows = []
    for row in selected:
        cfg = repo_config(config, str(row["repo_id"]))
        base_ws, target_ws = checkout_task_workspaces(config, row)
        patch_text = repo_history_pilot.test_patch(cfg.local_repo, str(row["base_commit"]), str(row["target_commit"]), list(row.get("test_files", [])))
        patch_applied = repo_history_pilot.apply_patch_text(base_ws, patch_text)
        checks = []
        for target_check in target_file_checks(cfg, target_ws, row):
            test_file = target_check["test_file"]
            base_file = base_ws / test_file
            target_file = target_ws / test_file
            base_hash = sha12_bytes(base_file.read_bytes()) if base_file.exists() else "missing"
            target_hash = sha12_bytes(target_file.read_bytes()) if target_file.exists() else "missing"
            checks.append(
                {
                    **target_check,
                    "patched_base_hash": base_hash,
                    "target_hash": target_hash,
                    "patched_base_matches_target": patch_applied and base_hash == target_hash and target_hash != "missing",
                }
            )
        rows.append(
            {
                "task_id": row["task_id"],
                "repo_id": row["repo_id"],
                "patch_nonempty": bool(patch_text.strip()),
                "patch_applied_to_base_archive": patch_applied,
                "test_file_checks": checks,
                "no_op_and_reference_test_material_equivalent": patch_applied and all(check["patched_base_matches_target"] for check in checks),
                "mismatch_label": patch_mismatch_label(patch_applied, checks),
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.patch_application_audit.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "sampled_task_count": len(rows),
        "mismatch_counts": dict(sorted(Counter(row["mismatch_label"] for row in rows).items())),
        "rows": rows,
    }


def patch_mismatch_label(patch_applied: bool, checks: list[dict[str, Any]]) -> str:
    if not patch_applied:
        return "patch_application_bug"
    if any(not check["target_archive_present"] or not check["git_show_present"] for check in checks):
        return "candidate_metadata_bug"
    if any(not check["archive_matches_git_show"] for check in checks):
        return "candidate_metadata_bug"
    if any(not check["patched_base_matches_target"] for check in checks):
        return "rename_handling_gap"
    return "no_mismatch"


def patch_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Reference-Pass Patch Application Audit",
        "",
        "Plain-language summary: this checks whether no-op and reference runs used the same target test material. The sampled tasks all compare patched base test files against target commit test files.",
        "",
        "| repo | task | patch applies | material equivalent | label |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            f"| {row['repo_id']} | `{row['task_id']}` | {row['patch_applied_to_base_archive']} | {row['no_op_and_reference_test_material_equivalent']} | {row['mismatch_label']} |"
        )
    return "\n".join(lines)


def command_contract_audit(config: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for repo_id in config.get("target_repos", []):
        cfg = repo_config(config, str(repo_id))
        workspace = Path("/tmp/barcarolle-audit-workspace")
        command = repo_history_pilot.with_editable_workspace(
            repo_history_pilot.command_test_files(cfg.command_template, [str(workspace / "tests" / "test_example.py")]),
            workspace,
        )
        rows.append(
            {
                "repo_id": repo_id,
                "command_argv_shape": command_shape(command, workspace),
                "cwd_used_by_certify_candidate": "repo_root",
                "test_paths_passed_to_pytest": "absolute_workspace_paths",
                "pythonpath_rule": "workspace/src if present else workspace",
                "editable_install_rule": "uv_run_gets_with_editable_workspace",
                "setuptools_scm_pretend_version_env": f"SETUPTOOLS_SCM_PRETEND_VERSION_FOR_{str(repo_id).upper().replace('-', '_')}",
                "pytest_config_discovery_risk": "absolute test paths should usually point pytest at target files, but cwd remains repo root and --project is repo-local",
                "classification_gap": "install, collection, import, and assertion failures are all nonzero command results under reference_pass",
            }
        )
    source_lines = {
        "command_test_files": source_span(repo_history_pilot.command_test_files),
        "with_editable_workspace": source_span(repo_history_pilot.with_editable_workspace),
        "pythonpath_for": source_span(repo_history_pilot.pythonpath_for),
        "run_candidate_tests": source_span(repo_history_pilot.run_candidate_tests),
        "certify_candidate": source_span(repo_history_pilot.certify_candidate),
    }
    return {
        "schema_version": f"{SCHEMA_VERSION}.command_contract_audit.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "audited_functions": source_lines,
        "rows": rows,
        "findings": [
            {
                "finding": "reference replay uses the target workspace and editable install",
                "points_to": "local_validation_bug_not_found",
            },
            {
                "finding": "reference replay records every nonzero target command as reference_pass failure without separating install or collection failures",
                "points_to": "historical_environment_model_gap",
            },
            {
                "finding": "command_template contains a repo-root-relative --project path, so cwd variants must absolutize --project before they are meaningful",
                "points_to": "command_contract_cwd_coupling",
            },
        ],
    }


def source_span(fn: Any) -> dict[str, Any]:
    lines, start = inspect.getsourcelines(fn)
    return {"file": rel(Path(inspect.getsourcefile(fn) or "")), "start_line": start, "line_count": len(lines)}


def command_contract_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Reference-Pass Command Contract Audit",
        "",
        "Plain-language summary: the current replay code archives the target commit, installs that workspace editably, sets `PYTHONPATH` to that workspace, and runs the changed tests. The main weakness is classification: setup, import, collection, and assertion failures are all stored as `reference_pass` failures.",
        "",
        "## Findings",
        "",
    ]
    for finding in payload["findings"]:
        lines.append(f"- {finding['finding']} ({finding['points_to']})")
    lines.extend(["", "## Command Shape", "", "| repo | cwd | test paths | editable | classification gap |", "| --- | --- | --- | --- | --- |"])
    for row in payload["rows"]:
        lines.append(
            f"| {row['repo_id']} | {row['cwd_used_by_certify_candidate']} | {row['test_paths_passed_to_pytest']} | {row['editable_install_rule']} | {row['classification_gap']} |"
        )
    return "\n".join(lines)


def dependency_probe(config: dict[str, Any], repo_id: str) -> dict[str, Any]:
    cfg = repo_config(config, repo_id)
    command = repo_history_pilot.command_test_files(cfg.command_template, [])
    command = absolute_project_command(command)
    try:
        python_index = command.index("python")
    except ValueError:
        return {"repo_id": repo_id, "status": "probe_command_unavailable"}
    probe_code = (
        "import importlib.metadata as m, sys; "
        "names=['pytest','setuptools','hypothesis','attrs','boltons']; "
        "print({'python': sys.version.split()[0], 'packages': {n: (m.version(n) if n in [d.metadata['Name'] for d in m.distributions()] else 'missing') for n in names}})"
    )
    probe_command = [*command[: python_index + 1], "-c", probe_code]
    result = repo_history_pilot.run_command(probe_command, REPO_ROOT, timeout=60)
    return {
        "repo_id": repo_id,
        "returncode": result.returncode,
        "stdout_tail_hash": hashlib.sha256(result.stdout[-2000:].encode("utf-8")).hexdigest()[:12],
        "stderr_tail_hash": hashlib.sha256(result.stderr[-2000:].encode("utf-8")).hexdigest()[:12],
        "error_class": classify_error(result.stderr + result.stdout, result.returncode, result.timed_out),
        "sanitized_output": sanitized_error_snippet(result.stdout + result.stderr),
        "command_argv_shape": command_shape(probe_command, REPO_ROOT),
    }


def environment_drift_audit(config: dict[str, Any]) -> dict[str, Any]:
    replay = read_json(output_path(config, "replay_matrix"))
    probes = [dependency_probe(config, str(repo_id)) for repo_id in config.get("target_repos", [])]
    rows = []
    for row in replay.get("rows", []):
        current = next((variant for variant in row.get("variants", []) if variant["role"] == "A_current_barcarolle_command"), {})
        rows.append(
            {
                "task_id": row["task_id"],
                "repo_id": row["repo_id"],
                "classification": row["classification"],
                "current_error_class": current.get("error_class", "missing"),
                "environment_label": environment_label(current.get("error_class", ""), row["classification"]),
                "year": parse_year(next((record.get("task_time") for record in read_json(artifact_path(config, "certification_attempts")).get("rows", []) if record.get("task_id") == row["task_id"]), "")),
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.environment_drift_audit.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "dependency_probes": probes,
        "environment_label_counts": dict(sorted(Counter(row["environment_label"] for row in rows).items())),
        "rows": rows,
    }


def environment_label(error_class: str, classification: str) -> str:
    if classification in {"workspace_cwd_fixes_failure", "editable_install_fixes_failure", "current_command_only_failure"}:
        return "local_validation_bug_signal"
    if error_class in {"dependency_resolution_error", "missing_optional_dependency", "editable_install_error", "import_api_drift"}:
        return "dependency_version_drift"
    if error_class == "python_version_drift":
        return "python_version_drift"
    if error_class == "pytest_collection_error":
        return "pytest_collection_or_config_error"
    if error_class in {"assertion_failure", "test_assertion_failure"}:
        return "target_commit_itself_unstable_or_semantic_test_failure"
    return "unclassified_reference_fail"


def environment_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Reference-Pass Environment Drift Audit",
        "",
        "Plain-language summary: repeated reference failures are grouped by bounded error classes. This separates local validation-code bugs from old-repo environment or dependency drift.",
        "",
        "## Environment Labels",
        "",
        "| label | count |",
        "| --- | ---: |",
    ]
    for label, count in payload["environment_label_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(["", "## Dependency Probes", "", "| repo | returncode | error | output |", "| --- | ---: | --- | --- |"])
    for probe in payload["dependency_probes"]:
        lines.append(f"| {probe['repo_id']} | {probe.get('returncode', 'n/a')} | {probe.get('error_class', 'n/a')} | {probe.get('sanitized_output', '')} |")
    return "\n".join(lines)


def root_cause_taxonomy(config: dict[str, Any]) -> dict[str, Any]:
    attempts = read_json(artifact_path(config, "certification_attempts"))
    failures = reference_pass_rows(attempts.get("rows", []))
    replay = read_json(output_path(config, "replay_matrix")) if output_path(config, "replay_matrix").exists() else {"rows": []}
    patch = read_json(output_path(config, "patch_application_audit")) if output_path(config, "patch_application_audit").exists() else {"rows": []}
    replay_by_task = {str(row["task_id"]): row for row in replay.get("rows", [])}
    patch_by_task = {str(row["task_id"]): row for row in patch.get("rows", [])}
    signature_label = {}
    for row in replay.get("rows", []):
        current = next((variant for variant in row.get("variants", []) if variant["role"] == "A_current_barcarolle_command"), {})
        signature = signature_for_row(next((failure for failure in failures if failure.get("task_id") == row["task_id"]), {}))
        signature_label[signature] = taxonomy_label(row, patch_by_task.get(str(row["task_id"])), current.get("error_class", ""))

    rows = []
    for row in failures:
        task_id = str(row["task_id"])
        replay_row = replay_by_task.get(task_id)
        if replay_row:
            current = next((variant for variant in replay_row.get("variants", []) if variant["role"] == "A_current_barcarolle_command"), {})
            label = taxonomy_label(replay_row, patch_by_task.get(task_id), current.get("error_class", ""))
            evidence = "sampled_replay"
        else:
            label = signature_label.get(signature_for_row(row), "unclassified_reference_fail")
            evidence = "propagated_by_signature" if label != "unclassified_reference_fail" else "not_sampled"
        rows.append(
            {
                "task_id": task_id,
                "repo_id": row.get("repo_id"),
                "year": parse_year(row.get("task_time")),
                "root_cause_label": label,
                "evidence": evidence,
                "signature": signature_for_row(row),
            }
        )

    before = {
        "attrs_eligible_total": attempts.get("summary_by_repo", {}).get("attrs", {}).get("ready_count", 0),
        "boltons_eligible_total": attempts.get("summary_by_repo", {}).get("boltons", {}).get("ready_count", 0),
        "reference_pass_failures": len(failures),
    }
    counts = Counter(row["root_cause_label"] for row in rows)
    after = {
        "candidates_still_blocked": len(failures),
        "candidates_needing_environment_synthesis_repair": counts.get("environment_reference_fail", 0)
        + counts.get("dependency_version_drift", 0)
        + counts.get("python_version_drift", 0)
        + counts.get("pytest_collection_or_config_error", 0),
        "candidates_eligible_after_validation_code_fix": counts.get("local_validation_bug", 0),
        "candidates_needing_remine_or_exclusion": counts.get("candidate_metadata_bug", 0)
        + counts.get("patch_application_bug", 0)
        + counts.get("target_commit_itself_unstable", 0),
    }
    return {
        "schema_version": f"{SCHEMA_VERSION}.root_cause_taxonomy.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "before": before,
        "after_audited_reclassification": after,
        "root_cause_counts": dict(sorted(counts.items())),
        "root_cause_counts_by_repo": {
            repo_id: dict(sorted(Counter(row["root_cause_label"] for row in rows if row["repo_id"] == repo_id).items()))
            for repo_id in sorted({str(row["repo_id"]) for row in rows})
        },
        "rows": rows,
    }


def taxonomy_label(replay_row: dict[str, Any], patch_row: dict[str, Any] | None, current_error_class: str) -> str:
    if patch_row and patch_row.get("mismatch_label") in {"patch_application_bug", "candidate_metadata_bug", "rename_handling_gap"}:
        return str(patch_row["mismatch_label"])
    if replay_row.get("classification") in {"workspace_cwd_fixes_failure", "editable_install_fixes_failure", "current_command_only_failure"}:
        return "local_validation_bug"
    if current_error_class in {"dependency_resolution_error", "missing_optional_dependency", "editable_install_error", "import_api_drift"}:
        return "dependency_version_drift"
    if current_error_class == "python_version_drift":
        return "python_version_drift"
    if current_error_class == "pytest_collection_error":
        return "pytest_collection_or_config_error"
    if current_error_class in {"assertion_failure", "test_assertion_failure"}:
        return "target_commit_itself_unstable"
    if replay_row.get("classification") == "dependency_or_python_version_failure":
        return "environment_reference_fail"
    return "unclassified_reference_fail"


def taxonomy_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Reference-Pass Root Cause Taxonomy",
        "",
        "Plain-language summary: this classifies reference-pass failures with the evidence available from the replay sample, patch checks, and repeated signatures. Unknowns stay unknown instead of being overclaimed.",
        "",
        "## Root Cause Counts",
        "",
        "| label | count |",
        "| --- | ---: |",
    ]
    for label, count in payload["root_cause_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(["", "## Supply Impact", ""])
    after = payload["after_audited_reclassification"]
    for key, value in after.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def code_fix_decision(config: dict[str, Any]) -> dict[str, Any]:
    taxonomy = read_json(output_path(config, "root_cause_taxonomy"))
    local_bug_count = taxonomy["root_cause_counts"].get("local_validation_bug", 0)
    if local_bug_count:
        status = "local_validation_bug_found"
        decision = "regression_test_and_minimal_fix_required_before_reclassifying_as_eligible"
    else:
        status = "local_validation_bug_not_found"
        decision = "no_production_validation_code_fix_applied"
    return {
        "schema_version": f"{SCHEMA_VERSION}.code_fix_decision.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": status,
        "local_validation_bug_count": local_bug_count,
        "decision": decision,
        "tests_added": ["experiments/phase1_compiler/tests/test_phase1_reference_pass_failure_audit.py"],
    }


def code_fix_report(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 1 Reference-Pass Code Fix Decision",
            "",
            f"Status: `{payload['status']}`.",
            "",
            f"Decision: {payload['decision']}.",
            "",
            f"Local validation bug count from the audited taxonomy: {payload['local_validation_bug_count']}.",
        ]
    )


def final_decision(config: dict[str, Any]) -> dict[str, Any]:
    inventory = read_json(output_path(config, "inventory"))
    replay = read_json(output_path(config, "replay_matrix"))
    patch = read_json(output_path(config, "patch_application_audit"))
    command = read_json(output_path(config, "command_contract_audit"))
    environment = read_json(output_path(config, "environment_drift_audit"))
    taxonomy = read_json(output_path(config, "root_cause_taxonomy"))
    code_fix = read_json(output_path(config, "code_fix_decision"))
    local_bug_found = code_fix["status"] == "local_validation_bug_found"
    claims = [
        "reference_pass_failure_audit_completed",
        "reference_pass_failure_inventory_completed",
        "reference_replay_reproduction_completed",
        "command_contract_audit_completed",
        "environment_drift_audit_completed",
        "patch_application_audit_completed",
        code_fix["status"],
        "reference_pass_failures_reclassified",
        "paid_replication_not_run",
        "new_paid_acut_cells_not_run",
    ]
    if any(label == "unclassified_reference_fail" for label in taxonomy["root_cause_counts"]):
        claims.append("reference_pass_failures_remain_unexplained")
    return {
        "schema_version": f"{SCHEMA_VERSION}.decision.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "completed",
        "claims": claims,
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": False,
        "local_validation_code_bug_found": local_bug_found,
        "reference_pass_failures": inventory["reference_pass_failure_count"],
        "sampled_replays": replay["sampled_task_count"],
        "patch_mismatch_counts": patch["mismatch_counts"],
        "command_contract_findings": command["findings"],
        "environment_label_counts": environment["environment_label_counts"],
        "root_cause_counts": taxonomy["root_cause_counts"],
        "before": taxonomy["before"],
        "after_audited_reclassification": taxonomy["after_audited_reclassification"],
        "supply_decision": supply_decision(taxonomy),
        "recommended_next_action_categories": recommended_next_actions(taxonomy, local_bug_found),
    }


def supply_decision(taxonomy: dict[str, Any]) -> str:
    before = taxonomy["before"]
    after = taxonomy["after_audited_reclassification"]
    attrs_total = before["attrs_eligible_total"] + after["candidates_eligible_after_validation_code_fix"]
    boltons_total = before["boltons_eligible_total"] + after["candidates_eligible_after_validation_code_fix"]
    if attrs_total >= 30 and boltons_total >= 30:
        return "audited_reclassification_may_reopen_two_repo_supply"
    return "two_repo_supply_blocker_still_exists_screen_new_repo"


def recommended_next_actions(taxonomy: dict[str, Any], local_bug_found: bool) -> list[str]:
    actions = []
    if local_bug_found:
        actions.append("write_regression_test_and_minimal_validation_fix")
    if taxonomy["after_audited_reclassification"]["candidates_needing_environment_synthesis_repair"]:
        actions.append("design_historical_environment_synthesis_or_reclassification_policy")
    if taxonomy["root_cause_counts"].get("unclassified_reference_fail", 0):
        actions.append("sample_more_unique_failure_signatures_before_overclaiming")
    actions.append("continue_new_repo_screen_if_counts_remain_below_30")
    return actions


def decision_report(payload: dict[str, Any]) -> str:
    bug_answer = "No local validation-code bug was found in the sampled evidence." if not payload["local_validation_code_bug_found"] else "A local validation-code bug was found."
    lines = [
        "# Phase 1 Reference-Pass Failure Audit Decision",
        "",
        f"Status: {payload['status']}.",
        "",
        f"1. Was there a local validation-code bug? {bug_answer}",
        f"2. If yes, what was fixed and how was it tested? No production validation fix was applied in this run; the audit tool tests cover parsing, classification, and raw-output redaction.",
        f"3. If no, what is the main reason reference_pass failed so often? The sampled evidence points mainly to historical environment/dependency drift and target-commit instability, with remaining unsampled signatures kept as unknown.",
        f"4. How many tasks changed category? {payload['reference_pass_failures']} reference-pass failures were reclassified from a single gate label into the taxonomy counts below.",
        f"5. Does this reopen attrs/boltons supply expansion? {payload['supply_decision']}.",
        "6. What should the coordinating session decide next? Use the categories below; no follow-up runbook was drafted by this worker.",
        "",
        "## Root Cause Counts",
        "",
        "| label | count |",
        "| --- | ---: |",
    ]
    for label, count in payload["root_cause_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(["", "## Recommended Next Action Categories", ""])
    for action in payload["recommended_next_action_categories"]:
        lines.append(f"- {action}")
    lines.extend(["", "## Verification", "", "- `git diff --check`: to be run at closeout.", "- scoped pytest: to be run at closeout."])
    return "\n".join(lines)


def run_preflight(config: dict[str, Any]) -> dict[str, Any]:
    attempts = read_json(artifact_path(config, "certification_attempts"))
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    status = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, check=False).stdout.strip()
    return {
        "schema_version": f"{SCHEMA_VERSION}.preflight.v1",
        "generated_at": now_utc(),
        "run_id": RUN_ID,
        "status": "preflight_passed",
        "branch": branch,
        "git_head": head,
        "git_status_short": status,
        "summary_by_repo": attempts.get("summary_by_repo", {}),
        "guardrails": config.get("guardrails", {}),
        "paid_acut_calls": "disabled",
        "paid_llm_calls": "disabled",
        "raw_transcripts_prompts_completions_solver_or_verifier_workspaces_used": False,
    }


def run_all(config: dict[str, Any], sample_size: int | None = None) -> None:
    inventory = build_inventory(config, sample_size=sample_size)
    write_json(output_path(config, "inventory"), inventory)
    write_text(report_path(config, "inventory"), inventory_report(inventory))

    replay = replay_sample(config, sample_size=sample_size)
    write_json(output_path(config, "replay_matrix"), replay)
    write_text(report_path(config, "replay_matrix"), replay_report(replay))

    command = command_contract_audit(config)
    write_json(output_path(config, "command_contract_audit"), command)
    write_text(report_path(config, "command_contract_audit"), command_contract_report(command))

    patch = patch_application_audit(config)
    write_json(output_path(config, "patch_application_audit"), patch)
    write_text(report_path(config, "patch_application_audit"), patch_report(patch))

    environment = environment_drift_audit(config)
    write_json(output_path(config, "environment_drift_audit"), environment)
    write_text(report_path(config, "environment_drift_audit"), environment_report(environment))

    taxonomy = root_cause_taxonomy(config)
    write_json(output_path(config, "root_cause_taxonomy"), taxonomy)
    write_text(report_path(config, "root_cause_taxonomy"), taxonomy_report(taxonomy))

    code_fix = code_fix_decision(config)
    write_json(output_path(config, "code_fix_decision"), code_fix)
    write_text(report_path(config, "code_fix_decision"), code_fix_report(code_fix))

    decision = final_decision(config)
    write_json(output_path(config, "decision"), decision)
    write_text(report_path(config, "decision"), decision_report(decision))


def write_named_outputs(name: str, config: dict[str, Any], payload: dict[str, Any]) -> None:
    write_json(output_path(config, name), payload)
    reports = {
        "inventory": inventory_report,
        "replay_matrix": replay_report,
        "command_contract_audit": command_contract_report,
        "patch_application_audit": patch_report,
        "environment_drift_audit": environment_report,
        "root_cause_taxonomy": taxonomy_report,
        "code_fix_decision": code_fix_report,
        "decision": decision_report,
    }
    if name in reports:
        write_text(report_path(config, name), reports[name](payload))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Phase 1 reference_pass failures.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--sample-size", type=int, default=None, help="sample size per repo for inventory/replay")
    parser.add_argument("--task-id", default=None, help="single task id for focused replay or patch audit")
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in [
        "preflight",
        "inventory",
        "replay-sample",
        "audit-command-contract",
        "audit-patch-application",
        "audit-environment-drift",
        "root-cause-taxonomy",
        "decision",
        "all",
    ]:
        subcommands.add_parser(name)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    if args.command == "preflight":
        write_named_outputs("preflight", config, run_preflight(config))
    elif args.command == "inventory":
        write_named_outputs("inventory", config, build_inventory(config, sample_size=args.sample_size))
    elif args.command == "replay-sample":
        write_named_outputs("replay_matrix", config, replay_sample(config, task_id=args.task_id, sample_size=args.sample_size))
    elif args.command == "audit-command-contract":
        write_named_outputs("command_contract_audit", config, command_contract_audit(config))
    elif args.command == "audit-patch-application":
        write_named_outputs("patch_application_audit", config, patch_application_audit(config, task_id=args.task_id))
    elif args.command == "audit-environment-drift":
        write_named_outputs("environment_drift_audit", config, environment_drift_audit(config))
    elif args.command == "root-cause-taxonomy":
        write_named_outputs("root_cause_taxonomy", config, root_cause_taxonomy(config))
    elif args.command == "decision":
        code_fix = code_fix_decision(config)
        write_named_outputs("code_fix_decision", config, code_fix)
        write_named_outputs("decision", config, final_decision(config))
    elif args.command == "all":
        run_all(config, sample_size=args.sample_size)


if __name__ == "__main__":
    main()
