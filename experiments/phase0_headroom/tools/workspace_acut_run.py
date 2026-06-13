from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import signal
import shlex
import shutil
import subprocess
import tarfile
import time
import urllib.parse
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import statement_quality


EXP_REL = Path("experiments/phase0_headroom")
TOOLZ_REPO_REL = EXP_REL / "external_repos" / "toolz"
CLICK_REPO_REL = Path("archive/2026-05-agent-license-reset/experiments/core_narrative/external_repos/click")
RAW_REL = Path("results/raw/workspace_acut")
WORKSPACE_REL = Path("workspaces/workspace_acut")
CONFIG_REL = EXP_REL / "configs" / "acut_workspace_adapter.yaml"
ADAPTER_CONFIGS_REL = EXP_REL / "configs" / "acut_workspace_adapters.yaml"
MATRIX_CONFIG_REL = EXP_REL / "configs" / "workspace_acut_matrix.yaml"
RESULTS_REL = Path("results")
REPORTS_REL = Path("reports")
SCORE_FIELDS = [
    "adapter_id",
    "acut_id",
    "harness_name",
    "model_or_agent_name",
    "task_id",
    "split",
    "attempt",
    "submission_status",
    "terminal_status",
    "verifier_exit_code",
    "scoreable_cell",
    "agent_failure",
    "harness_error",
]
CONSERVATIVE_WORKSPACE_CELL_ESTIMATE_USD = 0.50


@dataclass
class CommandResult:
    command: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


@dataclass
class AdapterConfig:
    adapter_id: str
    acut_id: str
    model_or_agent_name: str
    command_template: str
    harness_name: str = ""
    command_template_source: str = "missing"
    endpoint_proof_status: str = "pending"
    timeout_seconds: int = 900
    requires_env: list[str] = field(default_factory=lambda: ["LLM_BASE_URL", "LLM_API_KEY"])
    usage_mode: str = "harness_report_optional"
    usage_report_path: str | None = None


@dataclass
class TaskPackage:
    task_id: str
    repo_id: str
    split: str
    source_repo: Path
    base_commit: str
    solver_facing_statement: str
    verifier_command: list[str]
    hidden_files: dict[str, str] = field(default_factory=dict)
    allowed_code_paths: list[str] = field(default_factory=list)
    test_paths: list[str] = field(default_factory=list)
    target_commit: str | None = None
    timeout_seconds: int = 180
    scope_boundaries: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CellResult:
    submission: dict[str, Any]
    verifier: dict[str, Any]
    solver_workspace: Path
    verifier_workspace: Path


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def phase0_root(root: Path) -> Path:
    candidate = root / EXP_REL
    return candidate if candidate.exists() else root


def run_command(command: list[str], cwd: Path, timeout: int = 120, env: dict[str, str] | None = None) -> CommandResult:
    def output_text(value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    def kill_process_tree(process: subprocess.Popen[str]) -> None:
        try:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return

    start = time.monotonic()
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=os.name != "nt",
        )
        stdout, stderr = process.communicate(timeout=timeout)
        return CommandResult(command, str(cwd), process.returncode or 0, stdout, stderr, time.monotonic() - start)
    except subprocess.TimeoutExpired:
        kill_process_tree(process)
        stdout, stderr = process.communicate()
        return CommandResult(
            command,
            str(cwd),
            124,
            output_text(stdout),
            output_text(stderr),
            time.monotonic() - start,
            timed_out=True,
        )


def require_success(result: CommandResult) -> str:
    if result.returncode != 0:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(result.command)}\n{result.stderr}")
    return result.stdout


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def simple_yaml_load(path: Path) -> dict[str, Any]:
    rows: list[tuple[int, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        rows.append((len(raw) - len(raw.lstrip(" ")), raw.strip()))

    def parse_block(index: int, indent: int) -> tuple[Any, int]:
        if index >= len(rows):
            return {}, index
        is_list = rows[index][0] == indent and rows[index][1].startswith("- ")
        if is_list:
            items = []
            while index < len(rows) and rows[index][0] == indent and rows[index][1].startswith("- "):
                item = rows[index][1][2:].strip()
                index += 1
                items.append(parse_scalar(item))
            return items, index

        mapping: dict[str, Any] = {}
        while index < len(rows):
            row_indent, text = rows[index]
            if row_indent < indent:
                break
            if row_indent > indent:
                raise ValueError(f"unsupported YAML indentation near: {text}")
            if ":" not in text:
                raise ValueError(f"unsupported YAML line: {text}")
            key, raw_value = text.split(":", 1)
            index += 1
            if raw_value.strip():
                mapping[key.strip()] = parse_scalar(raw_value)
                continue
            if index >= len(rows) or rows[index][0] <= row_indent:
                mapping[key.strip()] = {}
                continue
            mapping[key.strip()], index = parse_block(index, rows[index][0])
        return mapping, index

    if not rows:
        return {}
    parsed, final_index = parse_block(0, 0)
    if final_index != len(rows):
        raise ValueError(f"unparsed YAML content in {path}")
    if not isinstance(parsed, dict):
        raise ValueError(f"expected mapping YAML root in {path}")
    return parsed


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_path_component(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"_", "-", "."} else "_" for ch in value.strip())
    return safe or "default"


def result_file(exp: Path, result_prefix: str, stem: str, suffix: str) -> Path:
    return exp / RESULTS_REL / f"{safe_path_component(result_prefix)}_{stem}{suffix}"


def report_file(exp: Path, result_prefix: str, stem: str) -> Path:
    return exp / REPORTS_REL / f"{safe_path_component(result_prefix)}_{stem}.md"


def resolve_repo_path(root: Path, path: Path | str | None, default: Path) -> Path:
    chosen = default if path is None else Path(path)
    return chosen if chosen.is_absolute() else root / chosen


def display_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def artifact_namespace(result_prefix: str | None, adapter_id: str) -> Path:
    if not result_prefix or result_prefix == "workspace_acut":
        return Path()
    return Path(safe_path_component(result_prefix)) / safe_path_component(adapter_id)


def endpoint_host_hash() -> str | None:
    base = os.environ.get("LLM_BASE_URL", "")
    if not base:
        return None
    parsed = urllib.parse.urlparse(base)
    host = parsed.netloc or base
    return hashlib.sha256(host.encode("utf-8")).hexdigest()[:12]


def archive_tree(repo: Path, commit: str, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(["git", "archive", "--format=tar", commit], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace"))
    with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as tar:
        tar.extractall(destination)


def initialize_workspace_git(workspace: Path) -> None:
    require_success(run_command(["git", "init", "-q"], workspace))
    require_success(run_command(["git", "config", "user.name", "Barcarolle Phase0"], workspace))
    require_success(run_command(["git", "config", "user.email", "phase0@example.invalid"], workspace))
    require_success(run_command(["git", "add", "."], workspace))
    require_success(run_command(["git", "commit", "-q", "--allow-empty", "-m", "base task state"], workspace))


def changed_paths(workspace: Path) -> list[str]:
    result = run_command(["git", "diff", "--name-only"], workspace)
    require_success(result)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def capture_diff(workspace: Path) -> str:
    result = run_command(["git", "diff", "--binary"], workspace)
    require_success(result)
    return result.stdout


def apply_patch(workspace: Path, patch_path: Path) -> tuple[bool, str]:
    check = run_command(["git", "apply", "--check", str(patch_path)], workspace)
    if check.returncode != 0:
        return False, check.stderr[-1000:]
    applied = run_command(["git", "apply", str(patch_path)], workspace)
    if applied.returncode != 0:
        return False, applied.stderr[-1000:]
    return True, ""


def verifier_env_for(package: TaskPackage, workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    pythonpath = str(workspace / "src" if (workspace / "src").exists() else workspace)
    env["PYTHONPATH"] = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}" if env.get("PYTHONPATH") else pythonpath
    env[f"SETUPTOOLS_SCM_PRETEND_VERSION_FOR_{package.repo_id.upper().replace('-', '_')}"] = "0.0.0"
    return env


def render_command(template: str, *, workspace: Path, statement_file: Path, task_id: str, run_id: str, raw_dir: Path, timeout_seconds: int) -> list[str]:
    rendered = template.format(
        workspace=str(workspace),
        statement_file=str(statement_file),
        task_id=task_id,
        run_id=run_id,
        raw_dir=str(raw_dir),
        timeout_seconds=str(timeout_seconds),
    )
    return shlex.split(rendered)


def is_test_path(path: str) -> bool:
    return path.startswith("tests/") or "/tests/" in path


def split_scope_boundaries(scope_boundaries: str) -> tuple[list[str], list[str]]:
    editable_scope: list[str] = []
    verifier_only_scope: list[str] = []
    for raw_line in scope_boundaries.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if "tests/" in line or "/tests/" in line:
            verifier_only_scope.append(line)
        else:
            editable_scope.append(line)
    return editable_scope, verifier_only_scope


def render_statement(package: TaskPackage) -> str:
    editable_scope, verifier_only_scope = split_scope_boundaries(package.scope_boundaries)
    editable_paths = package.allowed_code_paths or ["<implementation files needed for the requested behavior>"]
    scope_lines = editable_scope or ["Keep the change focused on the requested behavior."]
    non_editable_lines = [
        "Do not edit tests, hidden verifier files, generated caches, lockfiles, or files outside the listed editable paths.",
        *[f"Do not edit: {path}" for path in package.test_paths],
        *[f"Verifier-only context, do not edit: {line}" for line in verifier_only_scope],
    ]
    return "\n".join(
        [
            f"# {package.task_id}",
            "",
            "## Task",
            "",
            package.solver_facing_statement,
            "",
            "## Editable Paths",
            "",
            *[f"- {path}" for path in editable_paths],
            "",
            "## Non-Editable Paths",
            "",
            *[f"- {line}" for line in non_editable_lines],
            "",
            "## Scope Boundary",
            "",
            *[f"- {line}" for line in scope_lines],
            "",
            "Hidden verifier material, source provenance, target commits, and reference patches are not solver-visible.",
            "",
        ]
    )


def write_statement_file(workspace: Path, package: TaskPackage) -> Path:
    statement = workspace / ".barcarolle" / "statement.md"
    write_text(statement, render_statement(package))
    return statement


def package_submission_metadata(package: TaskPackage) -> dict[str, Any]:
    if not package.metadata:
        return {}
    allowed_keys = {
        "evidence_level",
        "task_time",
        "changed_files",
        "test_files",
        "allowed_context_refs",
        "canonical_repo_split",
        "canonical_split",
        "original_hardening_status",
        "clean_overlay_promotion_decision",
        "promotion_rationale",
        "statement_quality",
        "statement_digest",
        "statement_source",
        "source_context_status",
        "metadata_sources",
        "verifier_command_metadata",
    }
    return {key: package.metadata[key] for key in sorted(allowed_keys) if key in package.metadata}


def policy_violation(changed: list[str], package: TaskPackage) -> tuple[str | None, list[str]]:
    edited_tests = [path for path in changed if is_test_path(path)]
    if edited_tests:
        return "submission_edited_tests", edited_tests
    if package.allowed_code_paths:
        out_of_scope = [path for path in changed if path not in package.allowed_code_paths]
        if out_of_scope:
            return "submission_edited_out_of_scope_paths", out_of_scope
    return None, []


def inject_hidden_oracle(root: Path, package: TaskPackage, verifier_workspace: Path, raw_dir: Path) -> tuple[bool, str | None]:
    for rel_path, content in package.hidden_files.items():
        write_text(verifier_workspace / rel_path, content)
    if package.target_commit and package.test_paths:
        patch_path = raw_dir / f"{package.task_id}_hidden_tests.patch"
        diff = run_command(["git", "diff", "--binary", package.base_commit, package.target_commit, "--", *package.test_paths], package.source_repo)
        if diff.returncode != 0:
            return False, "hidden_test_patch_generation_failed"
        patch_path.write_text(diff.stdout, encoding="utf-8")
        applied, _error = apply_patch(verifier_workspace, patch_path)
        if not applied:
            return False, "hidden_test_patch_did_not_apply"
    return True, None


def run_workspace_cell(root: Path, package: TaskPackage, config: AdapterConfig, run_id: str, result_prefix: str | None = None) -> CellResult:
    exp = phase0_root(root)
    namespace = artifact_namespace(result_prefix, config.adapter_id)
    raw_dir = exp / RAW_REL / namespace / run_id
    workspace_root = exp / WORKSPACE_REL / namespace / run_id
    solver_workspace = workspace_root / "solver"
    verifier_workspace = workspace_root / "verifier"
    archive_tree(package.source_repo, package.base_commit, solver_workspace)
    initialize_workspace_git(solver_workspace)
    statement_file = write_statement_file(solver_workspace, package)
    raw_dir.mkdir(parents=True, exist_ok=True)

    command = render_command(
        config.command_template,
        workspace=solver_workspace,
        statement_file=statement_file,
        task_id=package.task_id,
        run_id=run_id,
        raw_dir=raw_dir,
        timeout_seconds=config.timeout_seconds,
    )
    start = time.monotonic()
    acut = run_command(command, solver_workspace, timeout=config.timeout_seconds, env=os.environ.copy())
    latency = round(time.monotonic() - start, 3)
    stdout_path = raw_dir / "acut_stdout.txt"
    stderr_path = raw_dir / "acut_stderr.txt"
    stdout_path.write_text(acut.stdout, encoding="utf-8")
    stderr_path.write_text(acut.stderr, encoding="utf-8")
    patch_text = capture_diff(solver_workspace)
    patch_path = raw_dir / "submission.patch"
    patch_path.write_text(patch_text, encoding="utf-8")
    patch_sha = sha256_file(patch_path)
    base_submission = {
        "schema_version": "barcarolle.workspace_acut_submission.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "adapter_id": config.adapter_id,
        "acut_id": config.acut_id,
        "harness_name": config.harness_name,
        "model_or_agent_name": config.model_or_agent_name,
        "command_template_source": config.command_template_source,
        "endpoint_proof_status": config.endpoint_proof_status,
        "task_id": package.task_id,
        "repo_id": package.repo_id,
        "split": package.split,
        "patch_source": "git_diff_after_workspace_run",
        "patch_sha256": patch_sha,
        "latency_seconds": latency,
        "raw_artifacts": {
            "stdout": str(stdout_path.relative_to(exp)),
            "stderr": str(stderr_path.relative_to(exp)),
            "patch": str(patch_path.relative_to(exp)),
        },
        "task_package_metadata": package_submission_metadata(package),
    }
    verifier = {
        "schema_version": "barcarolle.workspace_acut_verifier.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "adapter_id": config.adapter_id,
        "acut_id": config.acut_id,
        "harness_name": config.harness_name,
        "model_or_agent_name": config.model_or_agent_name,
        "command_template_source": config.command_template_source,
        "endpoint_proof_status": config.endpoint_proof_status,
        "task_id": package.task_id,
        "repo_id": package.repo_id,
        "split": package.split,
        "fresh_workspace": False,
        "status": "invalid_output",
        "verifier_exit_code": None,
        "harness_error": None,
    }
    if acut.returncode != 0:
        submission = {**base_submission, "status": "acut_harness_error", "acut_exit_code": acut.returncode}
        verifier.update({"status": "acut_harness_error", "harness_error": "acut_command_failed", "acut_exit_code": acut.returncode})
        return CellResult(submission, verifier, solver_workspace, verifier_workspace)
    if not patch_text.strip():
        submission = {**base_submission, "status": "invalid_output", "acut_exit_code": acut.returncode}
        verifier.update({"status": "invalid_output", "harness_error": "empty_workspace_diff"})
        return CellResult(submission, verifier, solver_workspace, verifier_workspace)

    changed = changed_paths(solver_workspace)
    submission = {**base_submission, "status": "submitted", "acut_exit_code": acut.returncode, "changed_paths": changed}
    violation, violating_paths = policy_violation(changed, package)
    if violation:
        verifier.update({"status": "policy_violation", "harness_error": violation, "changed_paths": violating_paths})
        return CellResult(submission, verifier, solver_workspace, verifier_workspace)

    archive_tree(package.source_repo, package.base_commit, verifier_workspace)
    initialize_workspace_git(verifier_workspace)
    verifier["fresh_workspace"] = True
    applied, apply_error = apply_patch(verifier_workspace, patch_path)
    if not applied:
        verifier.update({"status": "harness_error", "harness_error": "captured_patch_did_not_apply", "patch_apply_error_tail": apply_error})
        return CellResult(submission, verifier, solver_workspace, verifier_workspace)
    injected, inject_error = inject_hidden_oracle(root, package, verifier_workspace, raw_dir)
    if not injected:
        verifier.update({"status": "harness_error", "harness_error": inject_error})
        return CellResult(submission, verifier, solver_workspace, verifier_workspace)

    verify_stdout = raw_dir / "verifier_stdout.txt"
    verify_stderr = raw_dir / "verifier_stderr.txt"
    verify = run_command(package.verifier_command, verifier_workspace, timeout=package.timeout_seconds, env=verifier_env_for(package, verifier_workspace))
    verify_stdout.write_text(verify.stdout, encoding="utf-8")
    verify_stderr.write_text(verify.stderr, encoding="utf-8")
    verifier.update(
        {
            "status": "timeout" if verify.timed_out else "verified_pass" if verify.returncode == 0 else "verified_fail",
            "verifier_exit_code": verify.returncode,
            "duration_seconds": round(verify.duration_seconds, 3),
            "raw_artifacts": {
                "stdout": str(verify_stdout.relative_to(exp)),
                "stderr": str(verify_stderr.relative_to(exp)),
            },
        }
    )
    return CellResult(submission, verifier, solver_workspace, verifier_workspace)


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value in {"null", "None"}:
        return None
    if value in {"true", "false"}:
        return value == "true"
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def command_template_with_source(data: dict[str, Any], env: dict[str, str]) -> tuple[str, str]:
    configured = str(data.get("command_template") or "")
    if configured.strip():
        return configured, "config"
    env_command = env.get("ACUT_WORKSPACE_COMMAND") or ""
    if env_command.strip():
        return env_command, "ACUT_WORKSPACE_COMMAND"
    return "", "missing"


def adapter_config_from_data(data: dict[str, Any], env: dict[str, str]) -> AdapterConfig:
    command_template, command_template_source = command_template_with_source(data, env)
    usage = data.get("usage_observation") if isinstance(data.get("usage_observation"), dict) else {}
    endpoint_proof = data.get("endpoint_proof") if isinstance(data.get("endpoint_proof"), dict) else {}
    return AdapterConfig(
        adapter_id=str(data.get("adapter_id") or "endpoint_workspace_acut"),
        acut_id=str(data.get("acut_id") or ""),
        harness_name=str(data.get("harness_name") or data.get("harness") or ""),
        model_or_agent_name=str(data.get("model_or_agent_name") or ""),
        command_template=command_template,
        command_template_source=command_template_source,
        endpoint_proof_status=str(data.get("endpoint_proof_status") or endpoint_proof.get("status") or "pending"),
        timeout_seconds=int(data.get("timeout_seconds") or 900),
        requires_env=[str(item) for item in data.get("requires_env", ["LLM_BASE_URL", "LLM_API_KEY"])],
        usage_mode=str(usage.get("mode") or "harness_report_optional"),
        usage_report_path=usage.get("report_path"),
    )


def load_adapter_config(path: Path, env: dict[str, str] | None = None) -> AdapterConfig:
    env = env or os.environ
    data: dict[str, Any] = {}
    list_key: str | None = None
    nested_key: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and list_key:
            data.setdefault(list_key, []).append(stripped[2:].strip())
            continue
        if line.startswith("  ") and nested_key and ":" in stripped:
            key, value = stripped.split(":", 1)
            data.setdefault(nested_key, {})[key.strip()] = parse_scalar(value)
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        raw_value = value.strip()
        list_key = None
        nested_key = None
        if raw_value == "":
            if key in {"requires_env"}:
                list_key = key
                data[key] = []
            else:
                nested_key = key
                data[key] = {}
        else:
            data[key] = parse_scalar(raw_value)
    return adapter_config_from_data(data, env)


def load_adapter_configs(path: Path, env: dict[str, str] | None = None) -> dict[str, AdapterConfig]:
    env = env or os.environ
    text = path.read_text(encoding="utf-8")
    if "\nadapters:" not in f"\n{text}":
        config = load_adapter_config(path, env)
        return {config.adapter_id: config}

    adapters: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    nested_key: str | None = None
    list_key: str | None = None
    in_adapters = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            in_adapters = stripped == "adapters:"
            nested_key = None
            list_key = None
            continue
        if not in_adapters:
            continue
        if stripped.startswith("- ") and indent <= 2:
            if current is not None:
                adapters.append(current)
            current = {}
            nested_key = None
            list_key = None
            item = stripped[2:].strip()
            if ":" in item:
                key, value = item.split(":", 1)
                current[key.strip()] = parse_scalar(value)
            continue
        if current is None:
            continue
        if stripped.startswith("- ") and list_key:
            current.setdefault(list_key, []).append(stripped[2:].strip())
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        raw_value = value.strip()
        if indent <= 4:
            nested_key = None
            list_key = None
            if raw_value == "":
                if key in {"requires_env"}:
                    current[key] = []
                    list_key = key
                else:
                    current[key] = {}
                    nested_key = key
            else:
                current[key] = parse_scalar(raw_value)
        elif nested_key:
            current.setdefault(nested_key, {})[key] = parse_scalar(raw_value)
    if current is not None:
        adapters.append(current)

    configs = [adapter_config_from_data(adapter, env) for adapter in adapters]
    return {config.adapter_id: config for config in configs}


def resolve_adapter_config(path: Path, adapter_id: str | None = None, env: dict[str, str] | None = None) -> AdapterConfig:
    configs = load_adapter_configs(path, env)
    if len(configs) == 1 and adapter_id is None:
        return next(iter(configs.values()))
    if not adapter_id:
        raise ValueError(f"adapter_id is required for multi-adapter config: {path}")
    if adapter_id not in configs:
        available = ", ".join(sorted(configs)) or "<none>"
        raise ValueError(f"adapter_id {adapter_id!r} not found in {path}; available: {available}")
    return configs[adapter_id]


def load_jsonl_map(path: Path) -> dict[str, dict[str, Any]]:
    return {row["task_id"]: row for row in read_jsonl(path)}


def config_path(root: Path, raw: Any) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def load_workspace_matrix_config(root: Path, matrix_config_path: Path | str | None) -> dict[str, Any]:
    path = resolve_repo_path(root, matrix_config_path, MATRIX_CONFIG_REL)
    if not path.exists():
        return {}
    config = simple_yaml_load(path)
    config["_path"] = str(path)
    return config


def matrix_task_ids(config: dict[str, Any]) -> list[str]:
    raw_task_ids = config.get("task_ids")
    if isinstance(raw_task_ids, list):
        return [str(item) for item in raw_task_ids]

    repo_splits = config.get("repo_splits") if isinstance(config.get("repo_splits"), dict) else {}
    if repo_splits:
        ordered: list[str] = []
        preferred = ["attrs/B_eval", "attrs/H_future", "boltons/B_eval", "boltons/H_future"]
        for split_name in [*preferred, *sorted(key for key in repo_splits if key not in preferred)]:
            raw = repo_splits.get(split_name)
            if isinstance(raw, list):
                ordered.extend(str(item) for item in raw)
        return ordered

    splits = config.get("splits") if isinstance(config.get("splits"), dict) else {}
    ordered: list[str] = []
    for split_name in ["b_eval", "h_future", "B_eval", "H_future"]:
        raw = splits.get(split_name)
        if isinstance(raw, list):
            ordered.extend(str(item) for item in raw)
    return ordered


def split_for_matrix_task(config: dict[str, Any]) -> dict[str, str]:
    repo_splits = config.get("repo_splits") if isinstance(config.get("repo_splits"), dict) else {}
    if repo_splits:
        mapping: dict[str, str] = {}
        for split_name, raw in repo_splits.items():
            if not isinstance(raw, list):
                continue
            label = str(split_name).split("/", 1)[1] if "/" in str(split_name) else str(split_name)
            for task_id in raw:
                mapping[str(task_id)] = label
        return mapping

    splits = config.get("splits") if isinstance(config.get("splits"), dict) else {}
    mapping: dict[str, str] = {}
    for split_name, raw in splits.items():
        if not isinstance(raw, list):
            continue
        label = "B_eval" if str(split_name).lower() == "b_eval" else "H_future" if str(split_name).lower() == "h_future" else str(split_name)
        for task_id in raw:
            mapping[str(task_id)] = label
    return mapping


def clean_overlay_statement(row: dict[str, Any], metadata: dict[str, Any], verifier_command_display: str) -> str:
    context = metadata.get("sanitized_context") if isinstance(metadata.get("sanitized_context"), dict) else {}
    refs = metadata.get("allowed_context_refs") or []
    code_files = [path for path in metadata.get("changed_files", []) if not is_test_path(str(path))]
    lines = [
        "Repair the public behavior described by the sanitized problem context.",
        "",
    ]
    if refs:
        lines.append(f"Allowed public context refs: {', '.join(str(ref) for ref in refs)}.")
    if context.get("summary"):
        lines.append(f"Problem summary: {context['summary']}")
    if context.get("body_summary"):
        lines.append(f"Problem details: {context['body_summary']}")
    if code_files:
        lines.append(f"Editable implementation scope: {', '.join(str(path) for path in code_files)}.")
    if verifier_command_display:
        lines.append(f"Verifier command metadata: {verifier_command_display}")
    lines.append("Preserve existing public behavior and do not edit tests or generated metadata.")
    return "\n".join(lines)


def command_display(template: str, test_files: list[str]) -> str:
    test_arg = " ".join(shlex.quote(path) for path in test_files)
    return template.format(test_files=test_arg)


def clean_overlay_package_for(
    *,
    root: Path,
    exp: Path,
    source_repo: Path,
    row: dict[str, Any],
    overlay_row: dict[str, Any],
    split: str,
    overlay_path: Path,
    clean_ext_path: Path,
    canonical_path: Path,
    release_path: Path,
    profile: dict[str, Any],
) -> TaskPackage:
    task_id = str(row["task_id"])
    test_files = [str(path) for path in row.get("test_files", [])]
    changed_files = [str(path) for path in row.get("changed_files") or [*row.get("code_files", []), *test_files]]
    code_files = [str(path) for path in row.get("code_files") or [path for path in changed_files if not is_test_path(path)]]
    command_template = str(row.get("harness_test_command") or profile.get("test_command") or "python -m pytest -q {test_files}")
    verifier_command = with_editable_current_worktree(absolute_uv_project(command_test_files(command_template, test_files), exp))
    context = row.get("sanitized_context") or overlay_row.get("sanitized_context") or {}
    promotion_decision = row.get("promotion_decision") or row.get("clean_overlay_promotion_decision") or overlay_row.get("promotion_decision") or overlay_row.get("clean_overlay_promotion_decision")
    metadata = {
        "evidence_level": "clean_supply_overlay_sidecar",
        "task_time": row.get("task_time") or overlay_row.get("task_time"),
        "base_commit": row.get("base_commit"),
        "target_commit": row.get("target_commit") or overlay_row.get("target_commit"),
        "changed_files": changed_files,
        "test_files": test_files,
        "allowed_context_refs": row.get("allowed_context_refs") or overlay_row.get("allowed_context_refs") or [],
        "sanitized_context": context,
        "source_context_status": row.get("source_context_status") or overlay_row.get("source_context_status"),
        "statement_quality": statement_quality.statement_quality_for_context(
            context,
            {**row, "changed_files": changed_files, "code_files": code_files, "test_files": test_files},
        )
        if context
        else {},
        "original_hardening_status": row.get("original_hardening_status") or overlay_row.get("original_hardening_status"),
        "original_hardening_reject_reasons": row.get("original_hardening_reject_reasons") or overlay_row.get("original_hardening_reject_reasons") or [],
        "clean_overlay_promotion_decision": promotion_decision,
        "promotion_rationale": row.get("promotion_rationale") or overlay_row.get("promotion_rationale"),
        "metadata_sources": {
            "clean_supply_overlay": display_path(root, overlay_path),
            "clean_ext_certified_tasks": display_path(root, clean_ext_path),
            "canonical_boltons_certified_tasks": display_path(root, canonical_path),
            "canonical_boltons_release": display_path(root, release_path),
        },
    }
    statement = (
        clean_overlay_statement(row, metadata, command_display(command_template, test_files))
        if context
        else str(row.get("solver_facing_statement") or "Repair the public behavior described by the certified task context.")
    )
    return TaskPackage(
        task_id=task_id,
        repo_id=str(row.get("repo_id") or "boltons"),
        split=split,
        source_repo=source_repo,
        base_commit=str(row["base_commit"]),
        target_commit=str(row.get("target_commit") or overlay_row.get("target_commit") or ""),
        solver_facing_statement=statement,
        verifier_command=verifier_command,
        allowed_code_paths=code_files,
        test_paths=test_files,
        timeout_seconds=180,
        scope_boundaries=str(row.get("scope_boundaries") or "Modify only implementation files needed for this behavior; do not edit tests."),
        metadata=metadata,
    )


def load_clean_overlay_packages(root: Path, matrix_config_path: Path | str | None = None) -> list[TaskPackage]:
    config = load_workspace_matrix_config(root, matrix_config_path)
    if not config or not config.get("clean_supply_overlay"):
        return []
    exp = phase0_root(root)
    overlay_path = config_path(root, config["clean_supply_overlay"])
    clean_ext_path = config_path(root, config["clean_ext_certified_tasks"])
    canonical_path = config_path(root, config["canonical_boltons_certified_tasks"])
    release_path = config_path(root, config["canonical_boltons_release"])
    profile_path = config_path(root, config.get("boltons_target_profile", EXP_REL / "target_profiles" / "boltons_target_profile.json"))
    overlay = read_json(overlay_path)
    clean_ext = load_jsonl_map(clean_ext_path)
    canonical = load_jsonl_map(canonical_path)
    profile = read_json(profile_path) if profile_path.exists() else {}
    source_repo = Path(str(profile.get("local_repo") or exp / "external_repos" / "boltons"))
    if not source_repo.is_absolute():
        source_repo = root / source_repo
    overlay_by_id = {str(row["task_id"]): row for row in overlay.get("promoted_tasks", []) if row.get("task_id")}
    split_by_id = split_for_matrix_task(config)
    ordered_ids = [*matrix_task_ids(config)]
    for task_id in overlay_by_id:
        if task_id not in ordered_ids:
            ordered_ids.append(task_id)

    packages: list[TaskPackage] = []
    for task_id in ordered_ids:
        row = {**canonical.get(task_id, {}), **clean_ext.get(task_id, {})}
        if not row:
            continue
        row.setdefault("task_id", task_id)
        overlay_row = overlay_by_id.get(task_id, {})
        split = split_by_id.get(task_id) or str(row.get("split") or overlay_row.get("split") or "")
        packages.append(
            clean_overlay_package_for(
                root=root,
                exp=exp,
                source_repo=source_repo,
                row=row,
                overlay_row=overlay_row,
                split=split,
                overlay_path=overlay_path,
                clean_ext_path=clean_ext_path,
                canonical_path=canonical_path,
                release_path=release_path,
                profile=profile,
            )
        )
    return packages


def second_repo_split_for_overlay(config: dict[str, Any], overlay: dict[str, Any]) -> dict[str, str]:
    split_by_id = split_for_matrix_task(config)
    for task_id in overlay.get("selected_b_eval_task_ids", []):
        split_by_id.setdefault(str(task_id), "B_eval")
    for task_id in overlay.get("selected_h_future_task_ids", []):
        split_by_id.setdefault(str(task_id), "H_future")
    for row in overlay.get("promoted_tasks", []):
        if row.get("task_id"):
            split_by_id.setdefault(str(row["task_id"]), str(row.get("selected_split") or row.get("split") or ""))
    return split_by_id


def load_second_repo_clean_overlay_packages(root: Path, matrix_config_path: Path | str | None = None) -> list[TaskPackage]:
    config = load_workspace_matrix_config(root, matrix_config_path)
    if not config or not config.get("second_repo_clean_supply_overlay"):
        return []
    exp = phase0_root(root)
    overlay_path = config_path(root, config["second_repo_clean_supply_overlay"])
    overlay = read_json(overlay_path)
    repo_id = str(overlay.get("selected_repo_id") or "")
    if not repo_id:
        return []

    second_config_path = config_path(root, overlay.get("config") or "experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml")
    second_config = simple_yaml_load(second_config_path) if second_config_path.exists() else {}
    repo_config = second_config.get("candidate_repos", {}).get(repo_id, {})
    prefix = str(repo_config.get("candidate_source_prefix") or f"{repo_id}_clean_outcome_unseen_supply")
    certified_path = exp / "certified_tasks" / f"{prefix}_certified_tasks.jsonl"
    certified = load_jsonl_map(certified_path)
    test_environment = repo_config.get("test_environment") if isinstance(repo_config.get("test_environment"), dict) else {}
    profile = {
        "local_repo": repo_config.get("local_repo") or exp / "external_repos" / repo_id,
        "test_command": test_environment.get("command_template") or "python -m pytest -q {test_files}",
    }
    source_repo = Path(str(profile["local_repo"]))
    if not source_repo.is_absolute():
        source_repo = root / source_repo

    overlay_by_id = {str(row["task_id"]): row for row in overlay.get("promoted_tasks", []) if row.get("task_id")}
    split_by_id = second_repo_split_for_overlay(config, overlay)
    ordered_ids = [*matrix_task_ids(config)]
    if not ordered_ids:
        ordered_ids = [*overlay.get("selected_b_eval_task_ids", []), *overlay.get("selected_h_future_task_ids", [])]
    for task_id in overlay_by_id:
        if task_id not in ordered_ids:
            ordered_ids.append(task_id)

    packages: list[TaskPackage] = []
    for task_id in ordered_ids:
        overlay_row = overlay_by_id.get(str(task_id), {})
        row = {**certified.get(str(task_id), {}), **overlay_row}
        if not row:
            continue
        row.setdefault("task_id", str(task_id))
        packages.append(
            clean_overlay_package_for(
                root=root,
                exp=exp,
                source_repo=source_repo,
                row=row,
                overlay_row=overlay_row,
                split=split_by_id.get(str(task_id), str(row.get("split") or "")),
                overlay_path=overlay_path,
                clean_ext_path=certified_path,
                canonical_path=certified_path,
                release_path=second_config_path,
                profile=profile,
            )
        )
    return packages


def ordered_statement_hardened_task_ids(manifest: dict[str, Any]) -> list[str]:
    groups = manifest.get("canonical_selected_task_ids_by_repo_split")
    if not isinstance(groups, dict):
        return []
    ordered: list[str] = []
    preferred = ["attrs/B_eval", "attrs/H_future", "boltons/B_eval", "boltons/H_future"]
    for repo_split in [*preferred, *sorted(key for key in groups if key not in preferred)]:
        raw = groups.get(repo_split)
        if isinstance(raw, list):
            ordered.extend(str(task_id) for task_id in raw)
    return ordered


def statement_hardened_repo_split_map(manifest: dict[str, Any]) -> dict[str, str]:
    groups = manifest.get("canonical_selected_task_ids_by_repo_split")
    if not isinstance(groups, dict):
        return {}
    mapping: dict[str, str] = {}
    for repo_split, task_ids in groups.items():
        if not isinstance(task_ids, list):
            continue
        for task_id in task_ids:
            mapping[str(task_id)] = str(repo_split)
    return mapping


def statement_hardened_attrs_profile(root: Path, exp: Path, config: dict[str, Any]) -> dict[str, Any]:
    config_path_raw = config.get("attrs_repo_config") or "experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml"
    attrs_config_path = config_path(root, config_path_raw)
    attrs_config = simple_yaml_load(attrs_config_path) if attrs_config_path.exists() else {}
    repo_config = attrs_config.get("candidate_repos", {}).get("attrs", {})
    test_environment = repo_config.get("test_environment") if isinstance(repo_config.get("test_environment"), dict) else {}
    return {
        "local_repo": repo_config.get("local_repo") or exp / "external_repos" / "attrs",
        "test_command": test_environment.get("command_template")
        or 'uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" --with "hypothesis<6" python -m pytest -q {test_files}',
    }


def statement_hardened_certified_rows(config: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    attrs_rows = load_jsonl_map(config_path(root, config["attrs_certified_tasks"]))
    boltons_clean_rows = load_jsonl_map(config_path(root, config["boltons_clean_ext_certified_tasks"]))
    boltons_canonical_rows = load_jsonl_map(config_path(root, config["boltons_canonical_certified_tasks"]))
    rows: dict[str, dict[str, Any]] = {}
    rows.update(attrs_rows)
    rows.update(boltons_canonical_rows)
    rows.update(boltons_clean_rows)
    return rows


def statement_hardened_source_repo(root: Path, exp: Path, repo_id: str, attrs_profile: dict[str, Any], boltons_profile: dict[str, Any]) -> Path:
    profile = attrs_profile if repo_id == "attrs" else boltons_profile
    source_repo = Path(str(profile.get("local_repo") or exp / "external_repos" / repo_id))
    return source_repo if source_repo.is_absolute() else root / source_repo


def statement_hardened_verifier_command(
    row: dict[str, Any],
    repo_id: str,
    exp: Path,
    attrs_profile: dict[str, Any],
    boltons_profile: dict[str, Any],
    test_files: list[str],
) -> list[str]:
    profile = attrs_profile if repo_id == "attrs" else boltons_profile
    command_template = str(row.get("harness_test_command") or profile.get("test_command") or "python -m pytest -q {test_files}")
    return with_editable_current_worktree(absolute_uv_project(command_test_files(command_template, test_files), exp))


def pilot_implementation_files(raw: dict[str, Any]) -> list[str]:
    if raw.get("code_files"):
        return sorted(str(path) for path in raw["code_files"])
    if raw.get("editable_paths"):
        return sorted(str(path) for path in raw["editable_paths"])
    changed = [str(path) for path in raw.get("changed_files", [])]
    return sorted(path for path in changed if path.endswith(".py") and not is_test_path(path))


def pilot_module_label(path: str) -> str:
    label = path
    if label.endswith(".pyi"):
        label = label[:-4]
    elif label.endswith(".py"):
        label = label[:-3]
    for prefix in ("src/", "boltons/", "toolz/"):
        if label.startswith(prefix):
            label = label[len(prefix) :]
    return label.replace("/", ".")


def pilot_module_list(raw: dict[str, Any], impl_files: list[str]) -> list[str]:
    modules = raw.get("module_or_package") or raw.get("module_or_package_list") or raw.get("api_surface_touched")
    if modules:
        if isinstance(modules, str):
            return [modules]
        return [str(item) for item in modules]
    return [pilot_module_label(path) for path in impl_files] or ["unknown_module"]


def phase1_paid_pilot_statement_text(raw: dict[str, Any], inventory_row: dict[str, Any]) -> str:
    if raw.get("solver_facing_statement"):
        return str(raw["solver_facing_statement"])
    context = raw.get("sanitized_context") or {}
    summary = context.get("summary") or raw.get("subject") or "certified repository task"
    modules = ", ".join(pilot_module_list({**raw, **inventory_row}, pilot_implementation_files({**raw, **inventory_row})))
    return f"Repair the {inventory_row.get('repo_id', raw.get('repo_id', 'repository'))} behavior described by the public context summary: {summary}. Focus on the {modules} module and preserve existing public behavior."


def load_phase1_weighted_design_paid_pilot_packages(root: Path, matrix_config_path: Path | str | None = None) -> list[TaskPackage]:
    config = load_workspace_matrix_config(root, matrix_config_path)
    if not config or not config.get("phase1_weighted_design_paid_pilot"):
        return []

    exp = phase0_root(root)
    inventory_path = config_path(root, config["candidate_inventory"])
    inventory = read_json(inventory_path)
    inventory_by_id = {str(row["task_id"]): row for row in inventory.get("rows", []) if row.get("task_id")}
    certified_by_id = statement_hardened_certified_rows(config, root)
    split_by_id = split_for_matrix_task(config)
    selected_ids = matrix_task_ids(config)
    attrs_profile = statement_hardened_attrs_profile(root, exp, config)
    boltons_profile_path = config_path(root, config.get("boltons_target_profile", EXP_REL / "target_profiles" / "boltons_target_profile.json"))
    boltons_profile = read_json(boltons_profile_path) if boltons_profile_path.exists() else {}

    packages: list[TaskPackage] = []
    for task_id in selected_ids:
        inventory_row = inventory_by_id.get(task_id)
        certified_row = certified_by_id.get(task_id)
        if not (inventory_row and certified_row):
            continue
        repo_id = str(inventory_row.get("repo_id") or certified_row.get("repo_id") or task_id.split("__", 1)[0])
        editable_paths = [str(path) for path in inventory_row.get("editable_paths") or pilot_implementation_files(certified_row)]
        test_paths = [str(path) for path in inventory_row.get("test_paths") or certified_row.get("test_files", [])]
        statement = phase1_paid_pilot_statement_text(certified_row, inventory_row)
        statement_digest = f"sha256:{sha256_text(statement)}"
        if inventory_row.get("statement_digest") and statement_digest != inventory_row.get("statement_digest"):
            raise ValueError(f"statement digest mismatch for {task_id}")
        verifier_command = statement_hardened_verifier_command(
            certified_row,
            repo_id,
            exp,
            attrs_profile,
            boltons_profile,
            test_paths,
        )
        source_repo = statement_hardened_source_repo(root, exp, repo_id, attrs_profile, boltons_profile)
        certified_source_key = (
            "attrs_certified_tasks"
            if repo_id == "attrs"
            else "boltons_clean_ext_certified_tasks"
            if task_id.startswith("boltons__clean_ext__")
            else "boltons_canonical_certified_tasks"
        )
        metadata = {
            "allowed_context_refs": certified_row.get("allowed_context_refs") or [],
            "base_commit": certified_row.get("base_commit") or inventory_row.get("base_commit"),
            "canonical_repo_split": split_by_id.get(task_id, ""),
            "canonical_split": split_by_id.get(task_id, "").split("/", 1)[1] if "/" in split_by_id.get(task_id, "") else split_by_id.get(task_id, ""),
            "changed_files": [str(path) for path in certified_row.get("changed_files", [*editable_paths, *test_paths])],
            "evidence_level": "phase1_weighted_design_paid_pilot",
            "metadata_sources": {
                "certified_tasks": display_path(root, config_path(root, config[certified_source_key])),
                "candidate_inventory": display_path(root, inventory_path),
                "workspace_matrix": display_path(root, config_path(root, config.get("_path", matrix_config_path or MATRIX_CONFIG_REL))),
            },
            "source_kind": inventory_row.get("source_kind"),
            "statement_digest": statement_digest,
            "statement_quality": {
                "status": inventory_row.get("statement_quality_status"),
                "risks": inventory_row.get("statement_quality_risks") or [],
            },
            "statement_source": inventory_row.get("statement_source"),
            "task_family_label": inventory_row.get("task_family_label"),
            "task_time": certified_row.get("task_time") or inventory_row.get("task_time"),
            "test_files": test_paths,
            "verifier_command_metadata": inventory_row.get("verifier_command_metadata"),
        }
        packages.append(
            TaskPackage(
                task_id=task_id,
                repo_id=repo_id,
                split=metadata["canonical_split"],
                source_repo=source_repo,
                base_commit=str(certified_row.get("base_commit") or inventory_row["base_commit"]),
                target_commit=str(certified_row.get("target_commit") or ""),
                solver_facing_statement=statement,
                verifier_command=verifier_command,
                allowed_code_paths=editable_paths,
                test_paths=test_paths,
                timeout_seconds=180,
                scope_boundaries="Modify only the listed editable implementation paths; do not edit tests or generated metadata.",
                metadata=metadata,
            )
        )
    return packages


def load_statement_hardened_after_canonical_repair_packages(root: Path, matrix_config_path: Path | str | None = None) -> list[TaskPackage]:
    config = load_workspace_matrix_config(root, matrix_config_path)
    if not config or not config.get("release_manifest"):
        return []
    exp = phase0_root(root)
    manifest_path = config_path(root, config["release_manifest"])
    preview_path = config_path(root, config["release_preview"])
    inventory_path = config_path(root, config["inventory"])
    manifest = read_json(manifest_path)
    preview = read_json(preview_path)
    inventory = read_json(inventory_path)
    if manifest.get("status") != "frozen":
        raise ValueError("statement-hardened release manifest must be frozen")

    preview_by_id = {str(row["task_id"]): row for row in preview.get("previews", []) if row.get("task_id")}
    inventory_by_id = {str(row["task_id"]): row for row in inventory.get("rows", []) if row.get("task_id")}
    certified_by_id = statement_hardened_certified_rows(config, root)
    repo_split_by_id = statement_hardened_repo_split_map(manifest)
    attrs_profile = statement_hardened_attrs_profile(root, exp, config)
    boltons_profile_path = config_path(root, config.get("boltons_target_profile", EXP_REL / "target_profiles" / "boltons_target_profile.json"))
    boltons_profile = read_json(boltons_profile_path) if boltons_profile_path.exists() else {}
    selected_ids = matrix_task_ids(config) or ordered_statement_hardened_task_ids(manifest)
    manifest_ids = set(ordered_statement_hardened_task_ids(manifest))
    unexpected = [task_id for task_id in selected_ids if task_id not in manifest_ids]
    if unexpected:
        raise ValueError(f"matrix selects task ids outside the frozen statement-hardened manifest: {unexpected}")

    packages: list[TaskPackage] = []
    for task_id in selected_ids:
        preview_row = preview_by_id.get(task_id)
        inventory_row = inventory_by_id.get(task_id)
        certified_row = certified_by_id.get(task_id)
        if not (preview_row and inventory_row and certified_row):
            continue
        statement = str(preview_row.get("visible_statement") or inventory_row.get("full_visible_statement") or "")
        statement_digest = str(preview_row.get("statement_digest") or inventory_row.get("statement_digest") or "")
        if statement_digest != f"sha256:{sha256_text(statement)}":
            raise ValueError(f"statement digest mismatch for {task_id}")
        if statement_digest != manifest.get("statement_digests", {}).get(task_id):
            raise ValueError(f"statement digest does not match frozen manifest for {task_id}")

        repo_id = str(preview_row.get("repo_id") or inventory_row.get("repo_id") or certified_row.get("repo_id") or task_id.split("__", 1)[0])
        repo_split = repo_split_by_id.get(task_id, str(preview_row.get("canonical_repo_split") or inventory_row.get("canonical_repo_split") or ""))
        split = repo_split.split("/", 1)[1] if "/" in repo_split else str(inventory_row.get("canonical_split") or "")
        editable_paths = [str(path) for path in manifest.get("editable_implementation_paths", {}).get(task_id, [])]
        test_paths = [str(path) for path in manifest.get("non_editable_test_paths", {}).get(task_id, [])]
        changed_files = [str(path) for path in certified_row.get("changed_files") or [*editable_paths, *test_paths]]
        verifier_command = statement_hardened_verifier_command(
            certified_row,
            repo_id,
            exp,
            attrs_profile,
            boltons_profile,
            test_paths,
        )
        source_repo = statement_hardened_source_repo(root, exp, repo_id, attrs_profile, boltons_profile)
        certified_source_key = (
            "attrs_certified_tasks"
            if repo_id == "attrs"
            else "boltons_clean_ext_certified_tasks"
            if task_id.startswith("boltons__clean_ext__")
            else "boltons_canonical_certified_tasks"
        )
        metadata = {
            "allowed_context_refs": preview_row.get("allowed_public_context_refs")
            or inventory_row.get("allowed_public_context_refs")
            or certified_row.get("allowed_context_refs")
            or [],
            "base_commit": certified_row.get("base_commit"),
            "canonical_repo_split": repo_split,
            "canonical_split": split,
            "changed_files": changed_files,
            "evidence_level": "statement_hardened_after_canonical_repair",
            "metadata_sources": {
                "certified_tasks": display_path(root, config_path(root, config[certified_source_key])),
                "inventory": display_path(root, inventory_path),
                "release_manifest": display_path(root, manifest_path),
                "release_preview": display_path(root, preview_path),
            },
            "statement_digest": statement_digest,
            "statement_source": preview_row.get("statement_source") or inventory_row.get("statement_source"),
            "task_time": certified_row.get("task_time") or inventory_row.get("task_time"),
            "test_files": test_paths,
            "verifier_command_metadata": inventory_row.get("verifier_command_metadata"),
        }
        packages.append(
            TaskPackage(
                task_id=task_id,
                repo_id=repo_id,
                split=split,
                source_repo=source_repo,
                base_commit=str(certified_row["base_commit"]),
                target_commit=str(certified_row.get("target_commit") or ""),
                solver_facing_statement=statement,
                verifier_command=verifier_command,
                allowed_code_paths=editable_paths,
                test_paths=test_paths,
                timeout_seconds=180,
                scope_boundaries="Modify only the listed editable implementation paths; do not edit tests or generated metadata.",
                metadata=metadata,
            )
        )
    return packages


def selected_three_repo_paid_validation_ids(config: dict[str, Any]) -> list[str]:
    return matrix_task_ids(config)


def three_repo_rows_by_id(path: Path) -> dict[str, dict[str, Any]]:
    payload = read_json(path)
    rows = payload.get("rows", []) if isinstance(payload, dict) else payload
    return {str(row["candidate_id"]): row for row in rows if isinstance(row, dict) and row.get("candidate_id")}


def three_repo_attrs_statement_packets_by_id(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    payload = read_json(path)
    packets = payload.get("statement_packets", []) if isinstance(payload, dict) else []
    return {str(row["candidate_id"]): row for row in packets if isinstance(row, dict) and row.get("candidate_id")}


def three_repo_split_by_id(path: Path) -> dict[str, str]:
    payload = read_json(path)
    return {
        str(row["candidate_id"]): str(row["split"])
        for row in payload.get("assignments", [])
        if isinstance(row, dict) and row.get("candidate_id")
    }


def three_repo_command_from_attempt(row: dict[str, Any]) -> list[str]:
    commands = [command for command in row.get("commands", []) if isinstance(command, dict)]
    winning_profile = str(row.get("winning_profile_id") or "")
    references = [
        command
        for command in commands
        if str(command.get("role", "")).startswith("reference") and int(command.get("returncode") or 0) == 0
    ]
    preferred = [command for command in references if str(command.get("profile_id") or "") == winning_profile]
    chosen = (preferred or references or commands)[:1]
    if not chosen:
        return []
    shape = chosen[0].get("command_shape") or []
    return [str(part).replace("<workspace>", ".") for part in shape]


def three_repo_public_context_refs(raw: dict[str, Any], packet: dict[str, Any], target_commit: str = "") -> list[str]:
    refs = [str(ref) for ref in raw.get("public_context_refs", []) if ref]
    primary_ref = packet.get("primary_ref")
    if primary_ref and str(primary_ref) not in refs:
        refs.append(str(primary_ref))
    for ref in packet.get("secondary_refs", []) or []:
        if ref and str(ref) not in refs:
            refs.append(str(ref))
    target_ref = f"commit:{target_commit}" if target_commit else ""
    return [ref for ref in refs if ref != target_ref]


def three_repo_statement(row: dict[str, Any], raw: dict[str, Any], packet: dict[str, Any]) -> str:
    repo_id = str(row.get("repo_id") or raw.get("repo_id") or "repository")
    implementation_files = [str(path) for path in row.get("implementation_files", [])]
    refs = three_repo_public_context_refs(raw, packet, str(row.get("target_commit") or ""))
    summary = packet.get("statement_summary") if isinstance(packet.get("statement_summary"), dict) else {}
    lines = [f"Repair the {repo_id} behavior described by the approved public context for this frozen validation task."]
    if refs:
        lines.append(f"Allowed public context refs: {', '.join(refs)}.")
    if summary.get("problem_summary"):
        lines.append(f"Problem summary: {summary['problem_summary']}")
    if summary.get("expected_behavior"):
        lines.append(f"Expected behavior: {summary['expected_behavior']}")
    if not summary:
        lines.append(
            "The committed package records the source context class and public reference but not raw public-context text; use the local repository history and the listed public reference as the only problem context."
        )
    if row.get("source_context_class") or row.get("source_context_quality"):
        lines.append(
            "Source context classification: "
            f"{row.get('source_context_class') or 'unknown'} / {row.get('source_context_quality') or 'unknown'}."
        )
    if implementation_files:
        lines.append(f"Focus on implementation path(s): {', '.join(implementation_files)}.")
    lines.append("Preserve existing public behavior. Do not edit tests, generated metadata, or benchmark artifacts.")
    return "\n".join(lines)


def load_phase1_three_repo_paid_validation_packages(root: Path, matrix_config_path: Path | str | None = None) -> list[TaskPackage]:
    config = load_workspace_matrix_config(root, matrix_config_path)
    if not config or not config.get("phase1_three_repo_paid_validation"):
        return []

    exp = phase0_root(root)
    task_table_path = config_path(root, config["task_table"])
    split_plan_path = config_path(root, config["split_plan"])
    fresh_attempts_path = config_path(root, config["fresh_certification_attempts"])
    third_attempts_path = config_path(root, config["third_repo_certification_attempts"])
    raw_inventory_path = config_path(root, config["task_supply_raw_anchor_inventory"])
    third_raw_inventory_path = config_path(root, config["third_repo_raw_anchor_inventory"])
    attrs_statement_packets_path = config_path(root, config.get("attrs_source_repair_statement_packets", ""))

    task_rows = three_repo_rows_by_id(task_table_path)
    split_by_id = three_repo_split_by_id(split_plan_path)
    attempt_rows = {
        **three_repo_rows_by_id(fresh_attempts_path),
        **three_repo_rows_by_id(third_attempts_path),
    }
    raw_rows = {
        **three_repo_rows_by_id(raw_inventory_path),
        **three_repo_rows_by_id(third_raw_inventory_path),
    }
    statement_packets = three_repo_attrs_statement_packets_by_id(attrs_statement_packets_path)
    selected_ids = selected_three_repo_paid_validation_ids(config)
    packages: list[TaskPackage] = []
    for task_id in selected_ids:
        row = task_rows.get(task_id)
        attempt = attempt_rows.get(task_id)
        if not (row and attempt):
            continue
        raw = raw_rows.get(task_id, {})
        packet = statement_packets.get(task_id, {})
        repo_id = str(row.get("repo_id") or attempt.get("repo_id") or task_id.split("__", 1)[0])
        split = split_by_id.get(task_id, str(row.get("split") or ""))
        implementation_files = [str(path) for path in row.get("implementation_files", [])]
        test_files = [str(path) for path in row.get("test_files", [])]
        statement = three_repo_statement(row, raw, packet)
        verifier_command = three_repo_command_from_attempt(attempt)
        source_repo = exp / "external_repos" / repo_id
        metadata = {
            "allowed_context_refs": three_repo_public_context_refs(raw, packet, str(row.get("target_commit") or "")),
            "base_commit": row.get("base_commit"),
            "canonical_repo_split": f"{repo_id}/{split}",
            "canonical_split": split,
            "changed_files": [*implementation_files, *test_files],
            "evidence_level": "phase1_three_repo_paid_validation",
            "metadata_sources": {
                "task_table": display_path(root, task_table_path),
                "split_plan": display_path(root, split_plan_path),
                "certification_attempts": display_path(
                    root,
                    third_attempts_path if repo_id == "click" else fresh_attempts_path,
                ),
                "raw_anchor_inventory": display_path(
                    root,
                    third_raw_inventory_path if repo_id == "click" else raw_inventory_path,
                ),
                "workspace_matrix": display_path(root, config_path(root, config.get("_path", matrix_config_path or MATRIX_CONFIG_REL))),
            },
            "source_context_status": row.get("source_context_quality"),
            "statement_digest": f"sha256:{sha256_text(statement)}",
            "statement_quality": {
                "status": row.get("source_context_quality"),
                "source_context_class": row.get("source_context_class"),
                "public_context_ref_count": row.get("public_context_ref_count"),
            },
            "statement_source": "phase1_three_repo_paid_validation_committed_metadata",
            "task_time": row.get("task_time"),
            "test_files": test_files,
            "verifier_command_metadata": {
                "winning_profile_id": attempt.get("winning_profile_id"),
                "command_source": "certification_attempt_command_shape",
            },
        }
        packages.append(
            TaskPackage(
                task_id=task_id,
                repo_id=repo_id,
                split=split,
                source_repo=source_repo,
                base_commit=str(row["base_commit"]),
                target_commit=str(row.get("target_commit") or attempt.get("target_commit_optional") or ""),
                solver_facing_statement=statement,
                verifier_command=verifier_command,
                allowed_code_paths=implementation_files,
                test_paths=test_files,
                timeout_seconds=240,
                scope_boundaries="Modify only the listed implementation paths; do not edit tests, generated metadata, or benchmark artifacts.",
                metadata=metadata,
            )
        )
    return packages


def load_toolz_packages(root: Path) -> list[TaskPackage]:
    exp = phase0_root(root)
    tasks = load_jsonl_map(exp / "certified_tasks" / "toolz_certified_tasks.jsonl")
    statements = load_jsonl_map(exp / "certified_tasks" / "toolz_task_statements.jsonl")
    release = read_json(exp / "releases" / "toolz_phase0_mini_release.json")
    repo = exp / "external_repos" / "toolz"
    packages: list[TaskPackage] = []
    for split in ["B_real", "W_real"]:
        for task_id in release["splits"].get(split, []):
            task = tasks[task_id]
            statement = statements[task_id]
            packages.append(
                TaskPackage(
                    task_id=task_id,
                    repo_id="toolz",
                    split=split,
                    source_repo=repo,
                    base_commit=task["base_commit"],
                    target_commit=task["target_commit"],
                    solver_facing_statement=statement["solver_facing_statement"],
                    verifier_command=["uv", "run", "--project", str(exp), "python", "-m", "pytest", "-q", *task["test_files"]],
                    allowed_code_paths=list(task.get("code_files", [])),
                    test_paths=list(task.get("test_files", [])),
                    timeout_seconds=180,
                    scope_boundaries=statement.get("scope_boundaries", ""),
                )
            )
    return packages


def load_generic_packages(root: Path) -> list[TaskPackage]:
    exp = phase0_root(root)
    protocol = read_json(exp / "results" / "generic_comparator_protocol.json")
    repo = root / CLICK_REPO_REL if (root / CLICK_REPO_REL).exists() else CLICK_REPO_REL
    packages: list[TaskPackage] = []
    for row in protocol.get("tasks", []):
        if not row.get("same_protocol_scoreable"):
            continue
        manifest = read_json(root / row["active_manifest"])
        manifest_dir = root / row["active_manifest"]
        manifest_dir = manifest_dir.parent
        packages.append(
            TaskPackage(
                task_id=manifest["task_id"],
                repo_id="click",
                split="G_mini",
                source_repo=repo,
                base_commit=manifest["base_commit"],
                solver_facing_statement=manifest["solver_facing_statement"],
                verifier_command=[str((manifest_dir / manifest["oracle_command"]).resolve())],
                allowed_code_paths=list(manifest.get("prompt_code_files", [])),
                timeout_seconds=int(manifest.get("cost_bound", {}).get("expected_timeout_seconds") or 60) + 120,
                scope_boundaries="\n".join(manifest.get("scope_review", {}).get("expected_touched_area", [])),
            )
        )
    return packages


def command_test_files(command_template: str, test_files: list[str]) -> list[str]:
    test_arg = " ".join(shlex.quote(path) for path in test_files)
    return shlex.split(command_template.format(test_files=test_arg))


def absolute_uv_project(command: list[str], exp: Path) -> list[str]:
    rewritten = list(command)
    for index, value in enumerate(rewritten[:-1]):
        if value == "--project" and rewritten[index + 1] == str(EXP_REL):
            rewritten[index + 1] = str(exp)
    return rewritten


def with_editable_current_worktree(command: list[str]) -> list[str]:
    if len(command) >= 2 and command[:2] == ["uv", "run"]:
        return [*command[:2], "--with-editable", ".", *command[2:]]
    return command


def load_repo_history_pilot_packages(root: Path, repo_id: str) -> list[TaskPackage]:
    exp = phase0_root(root)
    release_path = exp / "releases" / f"{repo_id}_phase0_pilot_release.json"
    certified_path = exp / "certified_tasks" / f"{repo_id}_certified_tasks.jsonl"
    profile_path = exp / "target_profiles" / f"{repo_id}_target_profile.json"
    if not (release_path.exists() and certified_path.exists() and profile_path.exists()):
        return []
    release = read_json(release_path)
    if not release.get("pilot_grade"):
        return []
    certified = load_jsonl_map(certified_path)
    profile = read_json(profile_path)
    source_repo = Path(profile.get("local_repo") or exp / "external_repos" / repo_id)
    if not source_repo.is_absolute():
        source_repo = root / source_repo
    split_by_task = {task_id: split for split, task_ids in release.get("splits", {}).items() for task_id in task_ids}
    packages: list[TaskPackage] = []
    for task in release.get("tasks", []):
        task_id = task["task_id"]
        row = certified[task_id]
        test_files = list(row.get("test_files", []))
        command = command_test_files(str(row.get("harness_test_command") or profile.get("test_command") or "python -m pytest -q {test_files}"), test_files)
        command = with_editable_current_worktree(absolute_uv_project(command, exp))
        packages.append(
            TaskPackage(
                task_id=task_id,
                repo_id=repo_id,
                split=split_by_task.get(task_id, str(task.get("split") or "")),
                source_repo=source_repo,
                base_commit=row["base_commit"],
                target_commit=row["target_commit"],
                solver_facing_statement=row["solver_facing_statement"],
                verifier_command=command,
                allowed_code_paths=list(row.get("code_files", [])),
                test_paths=test_files,
                timeout_seconds=180,
                scope_boundaries=row.get("scope_boundaries", ""),
            )
        )
    return packages


def load_second_repo_packages(root: Path) -> list[TaskPackage]:
    exp = phase0_root(root)
    packages: list[TaskPackage] = []
    releases = sorted((exp / "releases").glob("*_phase0_pilot_release.json"))
    for release_path in releases:
        repo_id = release_path.name.removesuffix("_phase0_pilot_release.json")
        if repo_id == "toolz":
            continue
        packages.extend(load_repo_history_pilot_packages(root, repo_id))
    return packages


def load_phase0_packages(root: Path, matrix_config_path: Path | str | None = None) -> list[TaskPackage]:
    three_repo_paid_validation_packages = load_phase1_three_repo_paid_validation_packages(root, matrix_config_path)
    if three_repo_paid_validation_packages:
        return three_repo_paid_validation_packages
    paid_pilot_packages = load_phase1_weighted_design_paid_pilot_packages(root, matrix_config_path)
    if paid_pilot_packages:
        return paid_pilot_packages
    statement_hardened_packages = load_statement_hardened_after_canonical_repair_packages(root, matrix_config_path)
    if statement_hardened_packages:
        return statement_hardened_packages
    overlay_packages = load_clean_overlay_packages(root, matrix_config_path)
    second_repo_overlay_packages = load_second_repo_clean_overlay_packages(root, matrix_config_path)
    matrix_config = load_workspace_matrix_config(root, matrix_config_path)
    if matrix_config.get("second_repo_clean_supply_overlay"):
        return second_repo_overlay_packages
    if matrix_config.get("clean_supply_overlay"):
        return overlay_packages
    overlay_task_ids = {package.task_id for package in [*overlay_packages, *second_repo_overlay_packages]}
    base_packages = [*load_toolz_packages(root), *load_generic_packages(root), *load_second_repo_packages(root)]
    if overlay_task_ids:
        base_packages = [package for package in base_packages if package.task_id not in overlay_task_ids]
    return [*base_packages, *overlay_packages, *second_repo_overlay_packages]


def select_packages(packages: list[TaskPackage], mode: str, task_ids: list[str] | None = None) -> list[TaskPackage]:
    if task_ids:
        by_task_id = {package.task_id: package for package in packages}
        return [by_task_id[task_id] for task_id in task_ids if task_id in by_task_id]
    if mode == "smoke":
        wanted = {"toolz__hist__002", "click__rbench__001"}
        return [package for package in packages if package.task_id in wanted]
    return packages


def score_rows(submissions: list[dict[str, Any]], verifiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verifier_by_run = {row["run_id"]: row for row in verifiers}
    rows = []
    for submission in submissions:
        verifier = verifier_by_run.get(submission["run_id"], {})
        terminal = verifier.get("status") or submission["status"]
        rows.append(
            {
                "adapter_id": submission.get("adapter_id", ""),
                "acut_id": submission.get("acut_id", ""),
                "harness_name": submission.get("harness_name", ""),
                "model_or_agent_name": submission.get("model_or_agent_name", ""),
                "task_id": submission["task_id"],
                "split": submission["split"],
                "attempt": 1,
                "submission_status": submission["status"],
                "terminal_status": terminal,
                "verifier_exit_code": verifier.get("verifier_exit_code", ""),
                "scoreable_cell": terminal in {"verified_pass", "verified_fail"},
                "agent_failure": terminal == "verified_fail",
                "harness_error": terminal in {"invalid_output", "acut_harness_error", "policy_violation", "harness_error", "timeout"},
            }
        )
    return rows


def metrics_payload(rows: list[dict[str, Any]], cost_summary: dict[str, Any]) -> dict[str, Any]:
    split_metrics: dict[str, dict[str, Any]] = {}
    for split in sorted({row["split"] for row in rows}):
        split_rows = [row for row in rows if row["split"] == split]
        scoreable = [row for row in split_rows if row["scoreable_cell"] is True]
        split_metrics[split] = {
            "cell_count": len(split_rows),
            "scoreable_cell_count": len(scoreable),
            "verified_pass_count": sum(1 for row in scoreable if row["terminal_status"] == "verified_pass"),
            "verified_fail_count": sum(1 for row in scoreable if row["terminal_status"] == "verified_fail"),
            "pass_rate": None if not scoreable else round(sum(1 for row in scoreable if row["terminal_status"] == "verified_pass") / len(scoreable), 4),
        }
    harness_metrics: dict[str, dict[str, Any]] = {}
    for adapter_id in sorted({row.get("adapter_id", "") for row in rows}):
        harness_rows = [row for row in rows if row.get("adapter_id", "") == adapter_id]
        scoreable = [row for row in harness_rows if row["scoreable_cell"] is True]
        harness_metrics[adapter_id] = {
            "cell_count": len(harness_rows),
            "scoreable_cell_count": len(scoreable),
            "scoreable_rate": None if not harness_rows else round(len(scoreable) / len(harness_rows), 4),
            "terminal_status_counts": {status: sum(1 for row in harness_rows if row["terminal_status"] == status) for status in sorted({row["terminal_status"] for row in harness_rows})},
        }
    total = len(rows)
    scoreable_total = sum(1 for row in rows if row["scoreable_cell"] is True)
    return {
        "schema_version": "barcarolle.workspace_acut_metrics.v1",
        "generated_at": iso_now(),
        "status": "not_run" if total == 0 else "workspace_acut_matrix_complete",
        "total_cells": total,
        "scoreable_cell_count": scoreable_total,
        "terminal_status_counts": {status: sum(1 for row in rows if row["terminal_status"] == status) for status in sorted({row["terminal_status"] for row in rows})},
        "split_metrics": split_metrics,
        "harness_metrics": harness_metrics,
        "cost_per_submitted_cell_usd": None if total == 0 else round(float(cost_summary.get("estimated_cost_usd") or 0.0) / total, 8),
        "cost_per_scoreable_cell_usd": None if scoreable_total == 0 else round(float(cost_summary.get("estimated_cost_usd") or 0.0) / scoreable_total, 8),
        "median_latency_seconds": cost_summary.get("median_latency_seconds"),
        "g_mini_to_w_real_available": split_metrics.get("G_mini", {}).get("scoreable_cell_count", 0) >= 3 and split_metrics.get("W_real", {}).get("scoreable_cell_count", 0) > 0,
        "g_mini_plus_b_real_to_w_real_available": split_metrics.get("G_mini", {}).get("scoreable_cell_count", 0) >= 3 and split_metrics.get("B_real", {}).get("scoreable_cell_count", 0) > 0 and split_metrics.get("W_real", {}).get("scoreable_cell_count", 0) > 0,
        "mae": "not_applicable_underpowered",
        "rmse": "not_applicable_underpowered",
        "brier_score": "not_applicable_underpowered",
    }


def cost_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    latencies = sorted(float(row.get("latency_seconds") or 0.0) for row in rows if row.get("latency_seconds") is not None)
    return {
        "schema_version": "barcarolle.workspace_acut_cost_summary.v1",
        "generated_at": iso_now(),
        "call_count": len(rows),
        "usage_observed_count": sum(1 for row in rows if row.get("usage_observed") is True),
        "usage_observed_rate": None if not rows else round(sum(1 for row in rows if row.get("usage_observed") is True) / len(rows), 4),
        "estimated_cost_usd": round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows), 8),
        "actual_cost_usd": None,
        "median_latency_seconds": None if not latencies else latencies[len(latencies) // 2],
    }


def merge_rows_by_run_id(existing: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order: list[str] = []
    by_run_id: dict[str, dict[str, Any]] = {}
    for row in [*existing, *new_rows]:
        run_id = str(row.get("run_id") or "")
        if not run_id:
            continue
        if run_id not in by_run_id:
            order.append(run_id)
        by_run_id[run_id] = row
    return [by_run_id[run_id] for run_id in order]


def existing_task_ids_for_adapter(rows: list[dict[str, Any]], adapter_id: str) -> set[str]:
    return {str(row.get("task_id")) for row in rows if row.get("adapter_id") == adapter_id and row.get("task_id")}


def write_empty_result_files(root: Path, status: str, reason: str, result_prefix: str = "workspace_acut") -> None:
    exp = phase0_root(root)
    write_jsonl(result_file(exp, result_prefix, "submissions", ".jsonl"), [])
    write_jsonl(result_file(exp, result_prefix, "verifier_results", ".jsonl"), [])
    write_csv(result_file(exp, result_prefix, "score_table", ".csv"), [], SCORE_FIELDS)
    write_jsonl(result_file(exp, result_prefix, "cost_ledger", ".jsonl"), [])
    summary = cost_summary([])
    write_json(result_file(exp, result_prefix, "cost_summary", ".json"), summary)
    metrics = metrics_payload([], summary)
    metrics["status"] = status
    metrics["blocker"] = reason
    write_json(result_file(exp, result_prefix, "metrics", ".json"), metrics)
    write_json(
        result_file(exp, result_prefix, "matrix", ".json"),
        {
            "schema_version": "barcarolle.workspace_acut_matrix.v1",
            "generated_at": iso_now(),
            "status": status,
            "blocker": reason,
            "scheduled_cell_count": 0,
            "terminal_status_counts": {},
            "scoreable_cell_count": 0,
        },
    )


def inspect_packages(
    root: Path,
    matrix_config_path: Path | str | None = None,
    result_prefix: str = "workspace_acut",
    task_ids: list[str] | None = None,
) -> dict[str, Any]:
    exp = phase0_root(root)
    resolved_matrix_config = resolve_repo_path(root, matrix_config_path, MATRIX_CONFIG_REL)
    config = load_workspace_matrix_config(root, matrix_config_path)
    configured_task_ids = matrix_task_ids(config)
    requested_task_ids = task_ids or configured_task_ids
    packages = load_phase0_packages(root, matrix_config_path=resolved_matrix_config)
    selected = select_packages(packages, mode="matrix", task_ids=requested_task_ids) if requested_task_ids else packages
    selected_ids = [package.task_id for package in selected]
    missing = [task_id for task_id in requested_task_ids if task_id not in selected_ids]
    payload = {
        "schema_version": "barcarolle.workspace_acut_package_inspection.v1",
        "generated_at": iso_now(),
        "status": "ready" if not missing else "blocked_missing_task_packages",
        "matrix_config": display_path(root, resolved_matrix_config),
        "configured_task_ids": configured_task_ids,
        "requested_task_ids": requested_task_ids,
        "selected_task_ids": selected_ids,
        "missing_task_ids": missing,
        "package_count": len(selected),
        "paid_acut_calls_made": False,
        "packages": [
            {
                "task_id": package.task_id,
                "repo_id": package.repo_id,
                "split": package.split,
                "base_commit": package.base_commit,
                "target_commit": package.target_commit,
                "source_repo": display_path(root, package.source_repo),
                "allowed_code_paths": package.allowed_code_paths,
                "test_paths": package.test_paths,
                "statement_sha256": sha256_text(render_statement(package)),
                "solver_facing_statement_digest": f"sha256:{sha256_text(package.solver_facing_statement)}",
                "frozen_statement_digest": package.metadata.get("statement_digest"),
                "statement_digest_matches_frozen": package.metadata.get("statement_digest") == f"sha256:{sha256_text(package.solver_facing_statement)}"
                if package.metadata.get("statement_digest")
                else None,
                "metadata": package_submission_metadata(package),
            }
            for package in selected
        ],
    }
    write_json(result_file(exp, result_prefix, "package_inspection", ".json"), payload)
    write_text(
        report_file(exp, result_prefix, "package_inspection"),
        "\n".join(
            [
                "# Workspace ACUT Package Inspection",
                "",
                f"Status: `{payload['status']}`.",
                "",
                f"- Matrix config: `{payload['matrix_config']}`.",
                f"- Selected task ids: `{', '.join(selected_ids) if selected_ids else 'none'}`.",
                f"- Missing task ids: `{', '.join(missing) if missing else 'none'}`.",
                "- Paid ACUT calls made: `false`.",
                "",
            ]
        ),
    )
    return payload


def write_default_adapter_config(root: Path) -> None:
    path = root / CONFIG_REL
    if path.exists():
        return
    write_text(
        path,
        "\n".join(
            [
                "schema_version: barcarolle.acut_workspace_adapter_config.v1",
                "adapter_id: endpoint_workspace_acut",
                'acut_id: ""',
                'model_or_agent_name: ""',
                'command_template: ""',
                "timeout_seconds: 900",
                "requires_env:",
                "  - LLM_BASE_URL",
                "  - LLM_API_KEY",
                "workspace_arg_style: template",
                "statement_delivery: file",
                "usage_observation:",
                "  mode: harness_report_optional",
                "  report_path: null",
                "allowed_network: acut_harness_defined",
                "raw_log_policy: ignored_path_only",
                "",
            ]
        ),
    )


def write_workspace_matrix_config(root: Path) -> None:
    write_text(
        root / MATRIX_CONFIG_REL,
        "\n".join(
            [
                "schema_version: barcarolle.workspace_acut_matrix_config.v1",
                "status: configured_waiting_for_endpoint_workspace_acut",
                "adapter_config: experiments/phase0_headroom/configs/acut_workspace_adapter.yaml",
                "historical_baseline: experiments/phase0_headroom/results/headroom_matrix.json",
                "old_diff_only_matrix_a: historical_non_scoreable_for_workspace_adapter",
                "budget:",
                "  hard_cap_usd: 25",
                "  stop_before_batch_projected_incremental_usd: 15",
                "projections:",
                "  smoke_subset_cells: 2",
                "  full_matrix_cells: 10",
                "  optional_rerun_or_second_acut: disabled_by_default",
                "splits:",
                "  B_real:",
                "    - toolz__hist__001",
                "    - toolz__hist__002",
                "    - toolz__hist__003",
                "  W_real:",
                "    - toolz__hist__004",
                "    - toolz__hist__010",
                "    - toolz__hist__016",
                "  G_mini:",
                "    protocol_status: scoreable_same_protocol",
                "    task_ids:",
                "      - click__rbench__001",
                "      - click__rbench__002",
                "      - click__rbench__003",
                "      - click__rbench__004",
                "",
            ]
        ),
    )


def preflight(
    root: Path,
    adapter_config_path: Path | str | None = None,
    adapter_id: str | None = None,
    matrix_config_path: Path | str | None = None,
    result_prefix: str = "workspace_acut",
) -> dict[str, Any]:
    resolved_adapter_config = resolve_repo_path(root, adapter_config_path, CONFIG_REL)
    if resolved_adapter_config == root / CONFIG_REL:
        write_default_adapter_config(root)
    write_workspace_matrix_config(root)
    exp = phase0_root(root)
    config = resolve_adapter_config(resolved_adapter_config, adapter_id)
    package_inspection = inspect_packages(root, matrix_config_path=matrix_config_path, result_prefix=result_prefix)
    missing_env = [name for name in config.requires_env if not os.environ.get(name)]
    configured = bool(config.command_template.strip())
    first_token = shlex.split(config.command_template)[0] if configured and shlex.split(config.command_template) else None
    command_exists = bool(first_token and (Path(first_token).exists() or shutil.which(first_token)))
    protocol = read_json(exp / "results" / "generic_comparator_protocol.json")
    status = "ready" if configured and command_exists and not missing_env else "blocked_no_acut_command" if not configured else "blocked_preflight_failed"
    blockers = []
    if missing_env:
        blockers.append("missing_required_endpoint_env")
    if not configured:
        blockers.append("no_acut_workspace_command_configured")
    elif not command_exists:
        blockers.append("acut_command_not_found")
    if int(protocol.get("scoreable_same_protocol_count") or 0) < 3:
        blockers.append("generic_comparator_below_three_scoreable_tasks")
        status = "blocked_preflight_failed"
    if package_inspection["status"] != "ready":
        blockers.append("matrix_task_package_selection_failed")
        status = "blocked_preflight_failed"
    payload = {
        "schema_version": "barcarolle.workspace_acut_preflight.v1",
        "generated_at": iso_now(),
        "status": status,
        "adapter_id": config.adapter_id,
        "acut_id_configured": bool(config.acut_id),
        "harness_name": config.harness_name,
        "model_or_agent_name_configured": bool(config.model_or_agent_name),
        "command_template_configured": configured,
        "command_template_source": config.command_template_source,
        "endpoint_proof_status": config.endpoint_proof_status,
        "command_first_token": first_token,
        "command_exists": command_exists,
        "required_env_present": not missing_env,
        "missing_env": missing_env,
        "endpoint_host_hash": endpoint_host_hash(),
        "local_subscription_fallback": "disabled",
        "openai_or_provider_fallback": "disabled",
        "generic_comparator_scoreable_same_protocol_count": protocol.get("scoreable_same_protocol_count"),
        "usage_observation_mode": config.usage_mode,
        "cost_policy": "stop_without_configured_endpoint_backed_harness",
        "blockers": blockers,
        "matrix_config": package_inspection["matrix_config"],
        "configured_task_ids": package_inspection["configured_task_ids"],
        "selected_task_ids": package_inspection["selected_task_ids"],
        "missing_task_ids": package_inspection["missing_task_ids"],
    }
    write_json(result_file(exp, result_prefix, "preflight", ".json"), payload)
    if status != "ready":
        write_empty_result_files(root, status, ",".join(blockers), result_prefix=result_prefix)
    write_text(
        report_file(exp, result_prefix, "preflight"),
        "\n".join(
            [
                "# Workspace ACUT Preflight",
                "",
                f"Status: `{status}`.",
                "",
                f"- Adapter config: `{display_path(root, resolved_adapter_config)}`.",
                f"- Adapter id: `{config.adapter_id}`.",
                f"- Harness: `{config.harness_name}`.",
                f"- Command configured: `{configured}`.",
                f"- Command template source: `{config.command_template_source}`.",
                f"- Command exists: `{command_exists}`.",
                f"- Endpoint proof status: `{config.endpoint_proof_status}`.",
                f"- Required endpoint env present: `{not missing_env}`.",
                f"- Endpoint host hash: `{payload['endpoint_host_hash']}`.",
                "- Local Codex/ChatGPT subscription fallback: `disabled`.",
                f"- Generic comparator same-protocol tasks: `{protocol.get('scoreable_same_protocol_count')}`.",
                f"- Usage observation mode: `{config.usage_mode}`.",
                f"- Matrix config: `{payload['matrix_config']}`.",
                f"- Selected task ids: `{', '.join(payload['selected_task_ids']) if payload['selected_task_ids'] else 'none'}`.",
                f"- Missing task ids: `{', '.join(payload['missing_task_ids']) if payload['missing_task_ids'] else 'none'}`.",
                "",
                "## Blockers",
                "",
                *(f"- `{blocker}`" for blocker in blockers),
                "" if blockers else "- None.",
                "",
            ]
        ),
    )
    return payload


def run_matrix(
    root: Path,
    mode: str,
    adapter_config_path: Path | str | None = None,
    adapter_id: str | None = None,
    matrix_config_path: Path | str | None = None,
    result_prefix: str = "workspace_acut",
    task_ids: list[str] | None = None,
    timeout_seconds: int | None = None,
) -> None:
    exp = phase0_root(root)
    resolved_adapter_config = resolve_repo_path(root, adapter_config_path, CONFIG_REL)
    resolved_matrix_config = resolve_repo_path(root, matrix_config_path, MATRIX_CONFIG_REL)
    config = resolve_adapter_config(resolved_adapter_config, adapter_id)
    if timeout_seconds is not None:
        config = replace(config, timeout_seconds=timeout_seconds)
    if not config.command_template.strip():
        raise RuntimeError("ACUT workspace command is not configured")
    submission_path = result_file(exp, result_prefix, "submissions", ".jsonl")
    verifier_path = result_file(exp, result_prefix, "verifier_results", ".jsonl")
    cost_path = result_file(exp, result_prefix, "cost_ledger", ".jsonl")
    existing_submissions = read_jsonl(submission_path)
    reusable_task_ids = existing_task_ids_for_adapter(existing_submissions, config.adapter_id) if mode == "matrix" else set()
    packages = select_packages(load_phase0_packages(root, matrix_config_path=resolved_matrix_config), mode=mode, task_ids=task_ids)
    submissions: list[dict[str, Any]] = []
    verifiers: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []
    for package in packages:
        if package.task_id in reusable_task_ids:
            continue
        run_acut_id = config.acut_id or "acut"
        if result_prefix == "workspace_acut":
            run_id = f"workspace_{run_acut_id}__{package.task_id}__{mode}1"
        else:
            run_id = f"{safe_path_component(result_prefix)}_{safe_path_component(config.adapter_id)}__{run_acut_id}__{package.task_id}__{mode}1"
        result = run_workspace_cell(root, package, config, run_id, result_prefix=result_prefix)
        submissions.append(result.submission)
        verifiers.append(result.verifier)
        cost_rows.append(
            {
                "schema_version": "barcarolle.workspace_acut_cost.v1",
                "run_id": run_id,
                "timestamp": iso_now(),
                "event": "workspace_acut_cell",
                "adapter_id": config.adapter_id,
                "acut_id": config.acut_id,
                "harness_name": config.harness_name,
                "model_or_agent_name": config.model_or_agent_name,
                "endpoint_proof_status": config.endpoint_proof_status,
                "task_id": package.task_id,
                "status": result.verifier["status"],
                "usage_observed": False,
                "estimated_cost_usd": CONSERVATIVE_WORKSPACE_CELL_ESTIMATE_USD,
                "latency_seconds": result.submission.get("latency_seconds"),
                "notes": "adapter captured workspace diff; harness usage report not imported; conservative per-cell estimate applied",
            }
        )
    submissions = merge_rows_by_run_id(existing_submissions, submissions)
    verifiers = merge_rows_by_run_id(read_jsonl(verifier_path), verifiers)
    cost_rows = merge_rows_by_run_id(read_jsonl(cost_path), cost_rows)
    write_jsonl(submission_path, submissions)
    write_jsonl(verifier_path, verifiers)
    write_jsonl(cost_path, cost_rows)
    rows = score_rows(submissions, verifiers)
    write_csv(result_file(exp, result_prefix, "score_table", ".csv"), rows, SCORE_FIELDS)
    summary = cost_summary(cost_rows)
    write_json(result_file(exp, result_prefix, "cost_summary", ".json"), summary)
    metrics = metrics_payload(rows, summary)
    metrics["status"] = "workspace_acut_smoke_complete" if mode == "smoke" else "workspace_acut_matrix_complete"
    write_json(result_file(exp, result_prefix, "metrics", ".json"), metrics)
    write_json(
        result_file(exp, result_prefix, "matrix", ".json"),
        {
            "schema_version": "barcarolle.workspace_acut_matrix.v1",
            "generated_at": iso_now(),
            "status": "workspace_acut_smoke_complete" if mode == "smoke" else "workspace_acut_matrix_complete",
            "adapter_config": display_path(root, resolved_adapter_config),
            "matrix_config": display_path(root, resolved_matrix_config),
            "adapter_ids": sorted({row.get("adapter_id", config.adapter_id) for row in submissions}),
            "scheduled_cell_count": len(rows),
            "terminal_status_counts": metrics["terminal_status_counts"],
            "scoreable_cell_count": metrics["scoreable_cell_count"],
        },
    )


def summarize(root: Path, result_prefix: str = "workspace_acut") -> None:
    exp = phase0_root(root)
    submissions = read_jsonl(result_file(exp, result_prefix, "submissions", ".jsonl"))
    verifiers = read_jsonl(result_file(exp, result_prefix, "verifier_results", ".jsonl"))
    cost_rows = read_jsonl(result_file(exp, result_prefix, "cost_ledger", ".jsonl"))
    rows = score_rows(submissions, verifiers)
    summary = cost_summary(cost_rows)
    write_csv(result_file(exp, result_prefix, "score_table", ".csv"), rows, SCORE_FIELDS)
    write_json(result_file(exp, result_prefix, "cost_summary", ".json"), summary)
    write_json(result_file(exp, result_prefix, "metrics", ".json"), metrics_payload(rows, summary))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 0 workspace ACUT adapter.")
    parser.add_argument("--root", default=".")
    subcommands = parser.add_subparsers(dest="command", required=True)

    def add_common_options(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("--adapter-config", default=None, help="Path to a single-adapter or multi-adapter workspace ACUT config.")
        command_parser.add_argument("--adapter-id", default=None, help="Adapter id to select when --adapter-config contains adapters.")
        command_parser.add_argument("--matrix-config", default=None, help="Path to the matrix config to associate with this run.")
        command_parser.add_argument("--result-prefix", default="workspace_acut", help="Prefix for result and report artifact filenames.")
        command_parser.add_argument("--task-id", action="append", default=None, help="Task id to run; repeat to run a bounded subset.")
        command_parser.add_argument("--timeout-seconds", type=int, default=None, help="Override the selected adapter timeout for this run.")

    for name in ["preflight", "smoke", "run-matrix", "summarize", "inspect-packages"]:
        add_common_options(subcommands.add_parser(name))
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.command == "preflight":
        preflight(
            root,
            adapter_config_path=args.adapter_config,
            adapter_id=args.adapter_id,
            matrix_config_path=args.matrix_config,
            result_prefix=args.result_prefix,
        )
    elif args.command == "smoke":
        run_matrix(
            root,
            "smoke",
            adapter_config_path=args.adapter_config,
            adapter_id=args.adapter_id,
            matrix_config_path=args.matrix_config,
            result_prefix=args.result_prefix,
            task_ids=args.task_id,
            timeout_seconds=args.timeout_seconds,
        )
    elif args.command == "run-matrix":
        run_matrix(
            root,
            "matrix",
            adapter_config_path=args.adapter_config,
            adapter_id=args.adapter_id,
            matrix_config_path=args.matrix_config,
            result_prefix=args.result_prefix,
            task_ids=args.task_id,
            timeout_seconds=args.timeout_seconds,
        )
    elif args.command == "summarize":
        summarize(root, result_prefix=args.result_prefix)
    elif args.command == "inspect-packages":
        inspect_packages(root, matrix_config_path=args.matrix_config, result_prefix=args.result_prefix, task_ids=args.task_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
