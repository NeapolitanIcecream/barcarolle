from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PHASE0_TOOLS = ROOT / "experiments" / "phase0_headroom" / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import workspace_acut_run as workspace  # noqa: E402


DEFAULT_AGENT_TIMEOUT_SECONDS = 1800
DEFAULT_ADAPTER_CLEANUP_GRACE_SECONDS = 60
DEFAULT_VERIFIER_TIMEOUT_SECONDS = 360


def repo_path(raw: str | Path, root: Path = ROOT) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else root / path


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_config(path: Path, expected_schema: str | None = None) -> dict[str, Any]:
    config = read_json(path)
    if expected_schema and config.get("schema_version") != expected_schema:
        raise ValueError(f"unsupported config schema: {path}")
    return config


def run_policy_int(config: dict[str, Any], key: str, default: int) -> int:
    return int(config.get("run_policy", {}).get(key, default))


def command_result(command: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def git_commit_exists(repo: Path, commit: str) -> bool:
    result = command_result(["git", "cat-file", "-e", f"{commit}^{{commit}}"], repo)
    return result.returncode == 0


def all_required_gates_pass(row: dict[str, Any]) -> bool:
    gates = (
        row.get("clean_overlay_certification_gates")
        or row.get("reviewed_required_gates")
        or row.get("gates")
        or row.get("local_certification_gates")
        or {}
    )
    if not isinstance(gates, dict) or not gates:
        return row.get("status") == "certified" or row.get("promotion_decision") in {
            "locally_certified_statement_ready",
            "promote_to_clean_benchmark_candidate",
        }
    required = [
        "checkout",
        "oracle_extractable",
        "known_bad_fail",
        "reference_pass",
        "flakiness_check",
        "solution_leakage_review",
        "scope_clarity_review",
        "ambiguity_review",
        "taxonomy_labelability",
        "cost_boundedness",
    ]
    return all(gates.get(gate) == "pass" for gate in required)


def is_test_path(path: str) -> bool:
    return workspace.is_test_path(path)


def code_files_for(row: dict[str, Any]) -> list[str]:
    raw = row.get("code_files") or row.get("implementation_files") or []
    if raw:
        return [str(path) for path in raw]
    return [str(path) for path in row.get("changed_files", []) if not is_test_path(str(path))]


def test_files_for(row: dict[str, Any]) -> list[str]:
    raw = row.get("test_files") or row.get("candidate_oracle_source") or row.get("oracle_refs") or []
    return [str(path) for path in raw if is_test_path(str(path))]


def visible_command(row: dict[str, Any], profile: dict[str, Any], test_files: list[str], exp: Path) -> tuple[str, list[str]]:
    template = str(row.get("harness_test_command") or profile.get("test_command") or "python -m pytest -q {test_files}")
    display = template.format(test_files=" ".join(shlex.quote(path) for path in test_files))
    command = workspace.with_editable_current_worktree(workspace.absolute_uv_project(workspace.command_test_files(template, test_files), exp))
    return display, command


def statement_for(row: dict[str, Any], code_files: list[str], visible_check: str) -> str:
    if row.get("solver_facing_statement"):
        statement = str(row["solver_facing_statement"]).strip()
    else:
        context = row.get("sanitized_context") if isinstance(row.get("sanitized_context"), dict) else {}
        refs = [str(ref) for ref in row.get("allowed_context_refs", []) if ref]
        lines = ["Repair the target repository behavior described by the approved public context."]
        if refs:
            lines.append(f"Allowed public context refs: {', '.join(refs)}.")
        if context.get("summary"):
            lines.append(f"Problem summary: {context['summary']}")
        if context.get("body_summary"):
            lines.append(f"Problem details: {context['body_summary']}")
        if code_files:
            lines.append(f"Focus on implementation path(s): {', '.join(code_files)}.")
        lines.append("Preserve existing public behavior.")
        statement = "\n".join(lines)
    return "\n".join(
        [
            statement,
            "",
            f"Visible local check command: `{visible_check}`.",
            "Do not edit tests, generated metadata, benchmark artifacts, or files outside the listed editable implementation paths.",
        ]
    )


def load_task_pool(config: dict[str, Any], root: Path = ROOT) -> tuple[list[workspace.TaskPackage], list[dict[str, Any]]]:
    exp = root / "experiments" / "phase0_headroom"
    target = config["target_repo"]
    source_repo = repo_path(target["local_repo"], root=root)
    profile = read_json(repo_path(target["profile"], root=root))
    verifier_timeout = run_policy_int(config, "verifier_timeout_seconds", DEFAULT_VERIFIER_TIMEOUT_SECONDS)
    by_task: dict[str, tuple[dict[str, Any], str]] = {}
    for source in config["task_sources"]:
        source_path = repo_path(source["path"], root=root)
        for row in read_jsonl(source_path):
            task_id = str(row.get("task_id") or row.get("candidate_id") or "")
            if not task_id or task_id in by_task:
                continue
            by_task[task_id] = ({**row, "task_id": task_id}, str(source["name"]))

    packages: list[workspace.TaskPackage] = []
    audit_rows: list[dict[str, Any]] = []
    for task_id in sorted(by_task):
        row, source_name = by_task[task_id]
        code_files = code_files_for(row)
        test_files = test_files_for(row)
        base_commit = str(row.get("base_commit") or "")
        target_commit = str(row.get("target_commit") or "")
        gates_pass = all_required_gates_pass(row)
        has_required_fields = bool(base_commit and target_commit and code_files and test_files)
        base_present = git_commit_exists(source_repo, base_commit) if base_commit and source_repo.exists() else False
        target_present = git_commit_exists(source_repo, target_commit) if target_commit and source_repo.exists() else False
        visible_check, verifier_command = visible_command(row, profile, test_files, exp)
        audit_rows.append(
            {
                "task_id": task_id,
                "source": source_name,
                "task_time": row.get("task_time", ""),
                "gates_pass": gates_pass,
                "has_required_fields": has_required_fields,
                "base_commit_present": base_present,
                "target_commit_present": target_present,
                "code_files": code_files,
                "test_files": test_files,
            }
        )
        if not (gates_pass and has_required_fields and base_present and target_present):
            continue
        packages.append(
            workspace.TaskPackage(
                task_id=task_id,
                repo_id=str(target["repo_id"]),
                split="unassigned",
                source_repo=source_repo,
                base_commit=base_commit,
                target_commit=target_commit,
                solver_facing_statement=statement_for(row, code_files, visible_check),
                verifier_command=verifier_command,
                hidden_files={str(path): str(path) for path in test_files},
                allowed_code_paths=code_files,
                test_paths=test_files,
                timeout_seconds=verifier_timeout,
                scope_boundaries="implementation files only; test edits are prohibited",
                metadata={
                    "task_time": row.get("task_time"),
                    "statement_digest": row.get("statement_digest"),
                    "source_context_status": row.get("source_context_status"),
                    "metadata_sources": {"task_source": source_name},
                    "allowed_context_refs": row.get("allowed_context_refs") or [],
                    "verifier_command_metadata": {"visible_check": visible_check},
                },
            )
        )
    return packages, audit_rows


def package_map(config: dict[str, Any], root: Path = ROOT) -> dict[str, workspace.TaskPackage]:
    packages, _audit = load_task_pool(config, root=root)
    return {package.task_id: package for package in packages}


def candidate_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    candidates = [*config["agent_candidates"]]
    if config.get("fallback_candidate"):
        candidates.append(config["fallback_candidate"])
    return {candidate["agent_id"]: candidate for candidate in candidates}


def adapter_config_for(
    config: dict[str, Any],
    candidate: dict[str, Any],
    root: Path = ROOT,
    command_template_source: str = "workspace_config",
) -> workspace.AdapterConfig:
    script = repo_path(candidate["adapter_script"], root=root)
    timeout = int(candidate.get("timeout_seconds") or DEFAULT_AGENT_TIMEOUT_SECONDS)
    cleanup_grace = run_policy_int(config, "adapter_cleanup_grace_seconds", DEFAULT_ADAPTER_CLEANUP_GRACE_SECONDS)
    outer_timeout = timeout + max(cleanup_grace, 0)
    command = (
        f"uv run --project {shlex.quote(str(root / 'experiments' / 'phase0_headroom'))} "
        f"python {shlex.quote(str(script))} "
        f"--workspace {{workspace}} --statement-file {{statement_file}} --raw-dir {{raw_dir}} --timeout {timeout} "
        f"--model {shlex.quote(str(candidate['model']))}"
    )
    if candidate["harness"] == "kilo":
        command += f" --completion-mode {shlex.quote(str(candidate.get('completion_mode') or 'strict-final'))}"
    return workspace.AdapterConfig(
        adapter_id=str(candidate["agent_id"]),
        acut_id=str(candidate["agent_id"]),
        harness_name=str(candidate["harness"]),
        model_or_agent_name=str(candidate["model"]),
        command_template=command,
        command_template_source=command_template_source,
        endpoint_proof_status="llm_endpoint_proxy_secret_isolated",
        timeout_seconds=outer_timeout,
        requires_env=["LLM_BASE_URL", "LLM_API_KEY"],
        usage_mode="raw_stdout_usage_best_effort",
        usage_report_path=None,
    )

