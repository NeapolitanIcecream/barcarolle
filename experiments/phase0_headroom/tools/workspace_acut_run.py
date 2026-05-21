from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import shlex
import shutil
import subprocess
import tarfile
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(command, str(cwd), completed.returncode, completed.stdout, completed.stderr, time.monotonic() - start)
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command,
            str(cwd),
            124,
            exc.stdout or "",
            exc.stderr or "",
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


def write_statement_file(workspace: Path, package: TaskPackage) -> Path:
    statement = workspace / ".barcarolle" / "statement.md"
    write_text(
        statement,
        "\n".join(
            [
                f"# {package.task_id}",
                "",
                "## Task",
                "",
                package.solver_facing_statement,
                "",
                "## Scope Boundary",
                "",
                package.scope_boundaries or "Keep the change focused on the requested behavior.",
                "",
                "Hidden verifier material, source provenance, target commits, and reference patches are not solver-visible.",
                "",
            ]
        ),
    )
    return statement


def is_test_path(path: str) -> bool:
    return path.startswith("tests/") or "/tests/" in path


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
    verify = run_command(package.verifier_command, verifier_workspace, timeout=package.timeout_seconds)
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


def load_phase0_packages(root: Path) -> list[TaskPackage]:
    return [*load_toolz_packages(root), *load_generic_packages(root)]


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
    result_prefix: str = "workspace_acut",
) -> dict[str, Any]:
    resolved_adapter_config = resolve_repo_path(root, adapter_config_path, CONFIG_REL)
    if resolved_adapter_config == root / CONFIG_REL:
        write_default_adapter_config(root)
    write_workspace_matrix_config(root)
    exp = phase0_root(root)
    config = resolve_adapter_config(resolved_adapter_config, adapter_id)
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
) -> None:
    exp = phase0_root(root)
    resolved_adapter_config = resolve_repo_path(root, adapter_config_path, CONFIG_REL)
    resolved_matrix_config = resolve_repo_path(root, matrix_config_path, MATRIX_CONFIG_REL)
    config = resolve_adapter_config(resolved_adapter_config, adapter_id)
    if not config.command_template.strip():
        raise RuntimeError("ACUT workspace command is not configured")
    submission_path = result_file(exp, result_prefix, "submissions", ".jsonl")
    verifier_path = result_file(exp, result_prefix, "verifier_results", ".jsonl")
    cost_path = result_file(exp, result_prefix, "cost_ledger", ".jsonl")
    existing_submissions = read_jsonl(submission_path)
    reusable_task_ids = existing_task_ids_for_adapter(existing_submissions, config.adapter_id) if mode == "matrix" else set()
    packages = load_phase0_packages(root)
    if mode == "smoke":
        wanted = {"toolz__hist__002", "click__rbench__001"}
        packages = [package for package in packages if package.task_id in wanted]
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

    for name in ["preflight", "smoke", "run-matrix", "summarize"]:
        add_common_options(subcommands.add_parser(name))
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if args.command == "preflight":
        preflight(root, adapter_config_path=args.adapter_config, adapter_id=args.adapter_id, result_prefix=args.result_prefix)
    elif args.command == "smoke":
        run_matrix(root, "smoke", adapter_config_path=args.adapter_config, adapter_id=args.adapter_id, matrix_config_path=args.matrix_config, result_prefix=args.result_prefix)
    elif args.command == "run-matrix":
        run_matrix(root, "matrix", adapter_config_path=args.adapter_config, adapter_id=args.adapter_id, matrix_config_path=args.matrix_config, result_prefix=args.result_prefix)
    elif args.command == "summarize":
        summarize(root, result_prefix=args.result_prefix)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
