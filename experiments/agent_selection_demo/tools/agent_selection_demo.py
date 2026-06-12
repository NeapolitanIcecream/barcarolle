from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PHASE0_TOOLS = ROOT / "experiments" / "phase0_headroom" / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import workspace_acut_run as workspace  # noqa: E402
from llm_endpoint_proxy import sanitized_child_env  # noqa: E402


DEMO_REL = Path("experiments/agent_selection_demo")
DEFAULT_CONFIG = DEMO_REL / "config" / "demo_config.json"
RESULTS_REL = DEMO_REL / "results"
REPORTS_REL = DEMO_REL / "reports"

SCOREABLE_STATUSES = {"verified_pass", "verified_fail"}
INFRA_STATUSES = {"invalid_output", "acut_harness_error", "policy_violation", "harness_error", "timeout"}
SECRET_ENV_NAMES = {"LLM_API_KEY", "LLM_BASE_URL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"}


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
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


def load_config(path: Path) -> dict[str, Any]:
    config = read_json(path)
    if config.get("schema_version") != "barcarolle.agent_selection_demo.config.v1":
        raise ValueError(f"unsupported config schema: {path}")
    return config


def result_path(name: str) -> Path:
    return ROOT / RESULTS_REL / name


def report_path(name: str) -> Path:
    return ROOT / REPORTS_REL / name


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
        lines = ["Repair the boltons behavior described by the approved public context."]
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


def load_task_pool(config: dict[str, Any]) -> tuple[list[workspace.TaskPackage], list[dict[str, Any]]]:
    exp = ROOT / "experiments" / "phase0_headroom"
    target = config["target_repo"]
    source_repo = repo_path(target["local_repo"])
    profile = read_json(repo_path(target["profile"]))
    by_task: dict[str, tuple[dict[str, Any], str]] = {}
    for source in config["task_sources"]:
        source_path = repo_path(source["path"])
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
                "statement_sha256": sha256_text(statement_for(row, code_files, visible_check)),
            }
        )
        if not (gates_pass and has_required_fields and base_present and target_present):
            continue
        metadata = {
            "evidence_level": "repo_history_local_certification",
            "task_time": row.get("task_time"),
            "changed_files": [str(path) for path in row.get("changed_files", [*code_files, *test_files])],
            "test_files": test_files,
            "allowed_context_refs": row.get("allowed_context_refs", []),
            "source_context_status": row.get("source_context_status") or row.get("public_context_available"),
            "statement_digest": f"sha256:{sha256_text(str(row.get('solver_facing_statement') or ''))}" if row.get("solver_facing_statement") else None,
            "statement_source": "certified_task_statement" if row.get("solver_facing_statement") else "sanitized_public_context",
            "verifier_command_metadata": {"visible_check": visible_check},
            "metadata_sources": {"task_source": source_name},
        }
        packages.append(
            workspace.TaskPackage(
                task_id=task_id,
                repo_id="boltons",
                split="unassigned",
                source_repo=source_repo,
                base_commit=base_commit,
                target_commit=target_commit,
                solver_facing_statement=statement_for(row, code_files, visible_check),
                verifier_command=verifier_command,
                allowed_code_paths=code_files,
                test_paths=test_files,
                timeout_seconds=180,
                scope_boundaries=str(row.get("scope_boundaries") or "Modify only listed implementation files; do not edit tests."),
                metadata=metadata,
            )
        )
    packages.sort(key=lambda package: (str(package.metadata.get("task_time") or ""), package.task_id))
    return packages, audit_rows


def split_counts(pool_size: int, policy: dict[str, Any]) -> tuple[int, int]:
    if pool_size >= int(policy["stronger_pool_size"]):
        return int(policy["stronger_selection_count"]), int(policy["stronger_holdout_count"])
    if pool_size >= int(policy["preferred_pool_size"]):
        return int(policy["preferred_selection_count"]), int(policy["preferred_holdout_count"])
    return int(policy["minimum_selection_count"]), int(policy["minimum_holdout_count"])


def freeze_split(packages: list[workspace.TaskPackage], config: dict[str, Any]) -> dict[str, Any]:
    policy = config["split_policy"]
    selection_count, holdout_count = split_counts(len(packages), policy)
    smoke_count = int(policy.get("smoke_task_count") or 1)
    needed = selection_count + holdout_count + smoke_count
    if len(packages) < needed:
        smoke_count = max(0, len(packages) - selection_count - holdout_count)
    selection = packages[:selection_count]
    holdout = packages[selection_count : selection_count + holdout_count]
    smoke = packages[selection_count + holdout_count : selection_count + holdout_count + smoke_count]
    return {
        "schema_version": "barcarolle.agent_selection_demo.split.v1",
        "generated_at": iso_now(),
        "target_repo": config["target_repo"]["repo_name"],
        "pool_size": len(packages),
        "selection_count": len(selection),
        "holdout_count": len(holdout),
        "smoke_count": len(smoke),
        "selection_tasks": [package.task_id for package in selection],
        "holdout_tasks": [package.task_id for package in holdout],
        "smoke_tasks": [package.task_id for package in smoke],
        "unused_tasks": [package.task_id for package in packages[selection_count + holdout_count + smoke_count :]],
        "split_rule": "ordered_by_task_time_then_task_id; selection first, holdout next, smoke from unused certified tasks",
    }


def endpoint_host_hash() -> str | None:
    base = os.environ.get("LLM_BASE_URL", "")
    if not base:
        return None
    parsed = urllib.parse.urlparse(base)
    host = parsed.netloc or base
    return hashlib.sha256(host.encode("utf-8")).hexdigest()[:12]


def model_gate(config: dict[str, Any]) -> dict[str, Any]:
    missing_env = [name for name in ["LLM_BASE_URL", "LLM_API_KEY"] if not os.environ.get(name)]
    planned_models = sorted({candidate["model"] for candidate in config["agent_candidates"]})
    if missing_env:
        return {
            "status": "blocked_missing_endpoint_env",
            "missing_env": missing_env,
            "planned_models": planned_models,
            "present_models": [],
            "endpoint_host_hash": None,
        }
    base = os.environ["LLM_BASE_URL"].rstrip("/")
    if not base.endswith("/v1"):
        base = f"{base}/v1"
    request = urllib.request.Request(f"{base}/models", headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    available = sorted(str(row.get("id")) for row in payload.get("data", []) if isinstance(row, dict) and row.get("id"))
    missing_models = [model for model in planned_models if model not in available]
    return {
        "status": "ready" if not missing_models else "blocked_missing_models",
        "endpoint_host_hash": endpoint_host_hash(),
        "planned_models": planned_models,
        "present_models": [model for model in planned_models if model in available],
        "missing_models": missing_models,
        "available_model_count": len(available),
    }


def secret_isolation_gate() -> dict[str, Any]:
    original = os.environ.copy()
    try:
        os.environ.update({"LLM_API_KEY": "real-secret", "LLM_BASE_URL": "https://endpoint.example", "OPENAI_API_KEY": "wrong-secret"})
        child_env = sanitized_child_env()
    finally:
        os.environ.clear()
        os.environ.update(original)
    visible_secret_names = sorted(name for name in SECRET_ENV_NAMES if name in child_env)
    return {
        "status": "ready" if not visible_secret_names else "blocked_secret_env_visible_to_agent_child",
        "real_endpoint_env_visible_to_agent_child": bool(visible_secret_names),
        "visible_secret_env_names": visible_secret_names,
        "dummy_key_env_present": "BARCAROLLE_LLM_PROXY_API_KEY" in child_env,
    }


def replay_reference_sample(packages: list[workspace.TaskPackage], sample_count: int = 3) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for package in packages[:sample_count]:
        with tempfile.TemporaryDirectory(prefix=f"barcarolle-demo-replay-{package.task_id}-") as tmp:
            replay_dir = Path(tmp) / "workspace"
            raw_dir = Path(tmp) / "raw"
            raw_dir.mkdir()
            workspace.archive_tree(package.source_repo, package.base_commit, replay_dir)
            workspace.initialize_workspace_git(replay_dir)
            code_patch = raw_dir / "reference_code.patch"
            diff = command_result(["git", "diff", "--binary", package.base_commit, package.target_commit, "--", *package.allowed_code_paths], package.source_repo)
            code_patch.write_text(diff.stdout, encoding="utf-8")
            applied, apply_error = workspace.apply_patch(replay_dir, code_patch)
            injected, inject_error = workspace.inject_hidden_oracle(ROOT, package, replay_dir, raw_dir) if applied else (False, "reference_patch_did_not_apply")
            verify = (
                workspace.run_command(package.verifier_command, replay_dir, timeout=package.timeout_seconds, env=workspace.verifier_env_for(package, replay_dir))
                if injected
                else None
            )
            rows.append(
                {
                    "task_id": package.task_id,
                    "reference_code_patch_applied": applied,
                    "hidden_oracle_injected": injected,
                    "inject_error": inject_error,
                    "apply_error_tail": apply_error[-500:] if apply_error else "",
                    "verifier_exit_code": verify.returncode if verify else None,
                    "verifier_passed": bool(verify and verify.returncode == 0),
                    "duration_seconds": round(verify.duration_seconds, 3) if verify else None,
                }
            )
    return rows


def gate(config: dict[str, Any], replay_sample_count: int = 3) -> dict[str, Any]:
    target_repo = repo_path(config["target_repo"]["local_repo"])
    git_ready = target_repo.exists() and command_result(["git", "rev-parse", "--is-inside-work-tree"], target_repo).returncode == 0
    dependency = command_result(
        ["uv", "run", "--project", "experiments/phase0_headroom", "--with", "pytest>=8,<9", "--with", "setuptools<81", "python", "-m", "pytest", "--version"],
        ROOT,
        timeout=120,
    )
    packages, audit_rows = load_task_pool(config) if git_ready else ([], [])
    policy = config["split_policy"]
    split = freeze_split(packages, config) if len(packages) >= int(policy["minimum_pool_size"]) else None
    models = model_gate(config)
    secret_gate = secret_isolation_gate()
    replay_rows = replay_reference_sample(packages, replay_sample_count) if packages and replay_sample_count > 0 else []
    blockers: list[str] = []
    if not git_ready:
        blockers.append("target_repo_checkout_missing_or_invalid")
    if dependency.returncode != 0:
        blockers.append("dependency_install_or_pytest_probe_failed")
    if len(packages) < int(policy["minimum_pool_size"]):
        blockers.append("certified_task_pool_below_30")
    if models["status"] != "ready":
        blockers.append(models["status"])
    if secret_gate["status"] != "ready":
        blockers.append(secret_gate["status"])
    if replay_rows and not all(row["verifier_passed"] for row in replay_rows):
        blockers.append("reference_replay_sample_failed")
    status = "ready" if not blockers else "blocked"
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.repository_gate.v1",
        "generated_at": iso_now(),
        "status": status,
        "target_repo": config["target_repo"]["repo_name"],
        "target_repo_checkout": display_path(target_repo),
        "target_repo_git_ready": git_ready,
        "dependency_probe_returncode": dependency.returncode,
        "dependency_probe_stdout_tail": dependency.stdout[-500:],
        "task_pool_size": len(packages),
        "task_audit_count": len(audit_rows),
        "minimum_pool_size": int(policy["minimum_pool_size"]),
        "model_gate": models,
        "secret_isolation_gate": secret_gate,
        "reference_replay_sample": replay_rows,
        "blockers": blockers,
        "split": split,
        "paid_agent_calls_made": False,
    }
    write_json(result_path("repository_gate.json"), payload)
    write_json(result_path("task_pool_audit.json"), {"generated_at": iso_now(), "rows": audit_rows})
    if split:
        write_json(result_path("frozen_split.json"), split)
    write_repository_gate_report(payload)
    return payload


def write_repository_gate_report(payload: dict[str, Any]) -> None:
    split = payload.get("split") or {}
    lines = [
        "# Agent Selection Demo Repository Gate",
        "",
        f"Status: `{payload['status']}`.",
        "",
        f"- Target repository: `{payload['target_repo']}`.",
        f"- Local checkout: `{payload['target_repo_checkout']}`.",
        f"- Certified task pool size: `{payload['task_pool_size']}`.",
        f"- Selection tasks: `{split.get('selection_count', 0)}`.",
        f"- Holdout tasks: `{split.get('holdout_count', 0)}`.",
        f"- Smoke tasks: `{split.get('smoke_count', 0)}`.",
        f"- Endpoint host hash: `{payload['model_gate'].get('endpoint_host_hash')}`.",
        f"- Planned models present: `{payload['model_gate'].get('present_models', [])}`.",
        f"- Agent child sees real endpoint env: `{payload['secret_isolation_gate']['real_endpoint_env_visible_to_agent_child']}`.",
        "- Paid Agent calls made: `false`.",
        "",
        "## Blockers",
        "",
    ]
    blockers = payload.get("blockers") or []
    lines.extend([f"- `{blocker}`" for blocker in blockers] or ["- None."])
    lines.extend(["", "## Reference Replay Sample", ""])
    replay_rows = payload.get("reference_replay_sample") or []
    lines.extend([f"- `{row['task_id']}` verifier passed: `{row['verifier_passed']}`." for row in replay_rows] or ["- Not run."])
    write_text(report_path("repository_gate.md"), "\n".join(lines) + "\n")


def load_split() -> dict[str, Any]:
    return read_json(result_path("frozen_split.json"))


def package_map(config: dict[str, Any]) -> dict[str, workspace.TaskPackage]:
    packages, _audit = load_task_pool(config)
    return {package.task_id: package for package in packages}


def candidate_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    candidates = [*config["agent_candidates"]]
    if config.get("fallback_candidate"):
        candidates.append(config["fallback_candidate"])
    return {candidate["agent_id"]: candidate for candidate in candidates}


def adapter_config_for(config: dict[str, Any], candidate: dict[str, Any]) -> workspace.AdapterConfig:
    script = repo_path(candidate["adapter_script"])
    timeout = int(candidate.get("timeout_seconds") or 900)
    command = (
        f"uv run --project {shlex.quote(str(ROOT / 'experiments' / 'phase0_headroom'))} "
        f"python {shlex.quote(str(script))} "
        "--workspace {workspace} --statement-file {statement_file} --raw-dir {raw_dir} --timeout {timeout_seconds} "
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
        command_template_source="agent_selection_demo_config",
        endpoint_proof_status="llm_endpoint_proxy_secret_isolated",
        timeout_seconds=timeout,
        requires_env=["LLM_BASE_URL", "LLM_API_KEY"],
        usage_mode="raw_stdout_usage_best_effort",
        usage_report_path=None,
    )


def stage_task_ids(split: dict[str, Any], stage: str) -> list[str]:
    if stage == "selection":
        return list(split["selection_tasks"])
    if stage == "holdout":
        return list(split["holdout_tasks"])
    if stage == "smoke":
        return list(split["smoke_tasks"] or split["selection_tasks"][:1])
    raise ValueError(f"unknown stage: {stage}")


def stage_paths(stage: str) -> dict[str, Path]:
    return {
        "submissions": result_path(f"{stage}_submissions.jsonl"),
        "verifiers": result_path(f"{stage}_verifier_results.jsonl"),
        "cost": result_path(f"{stage}_cost_ledger.jsonl"),
        "score": result_path(f"{stage}_score_table.csv"),
        "metrics": result_path(f"{stage}_metrics.json"),
        "report": report_path(f"{stage}_run_report.md"),
    }


def existing_run_ids(path: Path) -> set[str]:
    return {str(row.get("run_id")) for row in read_jsonl(path) if row.get("run_id")}


def raw_file_from_submission(submission: dict[str, Any], key: str) -> Path | None:
    rel = (submission.get("raw_artifacts") or {}).get(key)
    if not rel:
        return None
    return ROOT / "experiments" / "phase0_headroom" / rel


def find_usage_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if any(key in value for key in ["prompt_tokens", "completion_tokens", "input_tokens", "output_tokens"]):
            return value
        for nested in value.values():
            found = find_usage_object(nested)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_usage_object(item)
            if found:
                return found
    return None


def extract_usage_from_text(text: str) -> dict[str, Any] | None:
    for line in reversed(text.splitlines()):
        line = line.strip()
        if not line or not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        found = find_usage_object(parsed)
        if found:
            return found
    return None


def usage_from_submission(submission: dict[str, Any]) -> dict[str, Any] | None:
    for key in ["stdout", "stderr"]:
        path = raw_file_from_submission(submission, key)
        if path and path.exists():
            found = extract_usage_from_text(path.read_text(encoding="utf-8", errors="replace"))
            if found:
                return found
    return None


def estimate_cost(usage: dict[str, Any] | None, model: str, config: dict[str, Any]) -> tuple[bool, float, dict[str, int | None]]:
    if not usage:
        return False, float(config["run_policy"]["conservative_cell_estimate_usd"]), {
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
        }
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens"))
    details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    cached = usage.get("cached_input_tokens", details.get("cached_tokens"))
    if input_tokens is None and output_tokens is None:
        return False, float(config["run_policy"]["conservative_cell_estimate_usd"]), {
            "input_tokens": None,
            "cached_input_tokens": None,
            "output_tokens": None,
        }
    price = config["pricing_per_1m_tokens_usd"].get(model, {})
    input_total = max(int(input_tokens or 0), 0)
    cached_total = max(int(cached or 0), 0)
    uncached_total = max(input_total - cached_total, 0)
    output_total = max(int(output_tokens or 0), 0)
    cost = (
        uncached_total * float(price.get("input", 0.0))
        + cached_total * float(price.get("cached_input", price.get("input", 0.0)))
        + output_total * float(price.get("output", 0.0))
    ) / 1_000_000
    return True, round(cost, 8), {
        "input_tokens": input_total,
        "cached_input_tokens": cached_total,
        "output_tokens": output_total,
    }


def failure_category(verifier: dict[str, Any], submission: dict[str, Any]) -> str:
    status = str(verifier.get("status") or submission.get("status") or "")
    error = str(verifier.get("harness_error") or "")
    if status == "verified_pass":
        return "verified pass"
    if status == "verified_fail":
        return "hidden verifier failure"
    if status == "invalid_output":
        return "no meaningful change"
    if status == "timeout" or submission.get("acut_exit_code") == 124:
        return "exceeded budget or timeout"
    if status == "policy_violation" and "edited_tests" in error:
        return "edited tests when prohibited"
    if status == "policy_violation":
        return "edited prohibited paths"
    if "patch" in error and "apply" in error:
        return "patch did not apply"
    if status == "acut_harness_error":
        return "build/typecheck failure"
    if status == "harness_error":
        return "flaky or infrastructure failure"
    return "flaky or infrastructure failure"


def score_rows(stage: str, submissions: list[dict[str, Any]], verifiers: list[dict[str, Any]], cost_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    verifier_by_run = {row["run_id"]: row for row in verifiers}
    cost_by_run = {row["run_id"]: row for row in cost_rows}
    rows: list[dict[str, Any]] = []
    for submission in submissions:
        verifier = verifier_by_run.get(submission["run_id"], {})
        cost = cost_by_run.get(submission["run_id"], {})
        terminal = verifier.get("status") or submission.get("status")
        rows.append(
            {
                "stage": stage,
                "agent_id": submission.get("adapter_id", ""),
                "reviewer_name": cost.get("reviewer_name", ""),
                "harness": submission.get("harness_name", ""),
                "model": submission.get("model_or_agent_name", ""),
                "task_id": submission.get("task_id", ""),
                "terminal_status": terminal,
                "scoreable_cell": terminal in SCOREABLE_STATUSES,
                "verified_pass": terminal == "verified_pass",
                "failure_category": failure_category(verifier, submission),
                "latency_seconds": submission.get("latency_seconds", ""),
                "estimated_cost_usd": cost.get("estimated_cost_usd", ""),
                "usage_observed": cost.get("usage_observed", False),
                "patch_sha256": submission.get("patch_sha256", ""),
            }
        )
    return rows


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    index = math.ceil((p / 100.0) * len(values)) - 1
    return values[max(0, min(index, len(values) - 1))]


def summarize_stage(stage: str, rows: list[dict[str, Any]], expected_cells: int) -> dict[str, Any]:
    by_agent: dict[str, dict[str, Any]] = {}
    for agent_id in sorted({str(row["agent_id"]) for row in rows}):
        agent_rows = [row for row in rows if row["agent_id"] == agent_id]
        scoreable = [row for row in agent_rows if row["scoreable_cell"] is True]
        pass_count = sum(1 for row in agent_rows if row["verified_pass"] is True)
        costs = [float(row["estimated_cost_usd"] or 0.0) for row in agent_rows]
        latencies = [float(row["latency_seconds"] or 0.0) for row in agent_rows if row.get("latency_seconds") != ""]
        failure_counts = {
            category: sum(1 for row in agent_rows if row["failure_category"] == category)
            for category in sorted({str(row["failure_category"]) for row in agent_rows})
        }
        by_agent[agent_id] = {
            "reviewer_name": agent_rows[0].get("reviewer_name", "") if agent_rows else "",
            "harness": agent_rows[0].get("harness", "") if agent_rows else "",
            "model": agent_rows[0].get("model", "") if agent_rows else "",
            "scheduled_cells": len(agent_rows),
            "completed_cells": len(agent_rows),
            "scoreable_cells": len(scoreable),
            "scoreable_cell_rate": None if not agent_rows else round(len(scoreable) / len(agent_rows), 4),
            "verified_pass_count": pass_count,
            "verified_solve_rate": None if not agent_rows else round(pass_count / len(agent_rows), 4),
            "cost_per_task_usd": None if not agent_rows else round(sum(costs) / len(agent_rows), 8),
            "cost_per_solved_task_usd": None if pass_count == 0 else round(sum(costs) / pass_count, 8),
            "median_latency_seconds": None if not latencies else round(statistics.median(latencies), 3),
            "p90_latency_seconds": None if not latencies else round(percentile(latencies, 90) or 0.0, 3),
            "verifier_replay_success_rate": None if not agent_rows else round(len(scoreable) / len(agent_rows), 4),
            "failure_counts": failure_counts,
        }
    scoreable_count = sum(1 for row in rows if row["scoreable_cell"] is True)
    pass_count = sum(1 for row in rows if row["verified_pass"] is True)
    return {
        "schema_version": "barcarolle.agent_selection_demo.stage_metrics.v1",
        "generated_at": iso_now(),
        "stage": stage,
        "scheduled_cells": expected_cells,
        "completed_cells": len(rows),
        "scoreable_cells": scoreable_count,
        "scoreable_cell_rate": None if expected_cells == 0 else round(scoreable_count / expected_cells, 4),
        "verified_pass_count": pass_count,
        "verified_solve_rate": None if expected_cells == 0 else round(pass_count / expected_cells, 4),
        "agent_metrics": by_agent,
        "failure_category_counts": {
            category: sum(1 for row in rows if row["failure_category"] == category)
            for category in sorted({str(row["failure_category"]) for row in rows})
        },
        "usage_observed_count": sum(1 for row in rows if row.get("usage_observed") is True),
        "estimated_cost_usd": round(sum(float(row["estimated_cost_usd"] or 0.0) for row in rows), 8),
    }


def run_stage(config: dict[str, Any], stage: str, agent_ids: list[str] | None = None, rerun: bool = False) -> dict[str, Any]:
    missing_env = [name for name in ["LLM_BASE_URL", "LLM_API_KEY"] if not os.environ.get(name)]
    if missing_env:
        raise RuntimeError(f"missing endpoint env: {', '.join(missing_env)}")
    split = load_split()
    packages = package_map(config)
    task_ids = stage_task_ids(split, stage)
    candidates = candidate_by_id(config)
    selected_agents = agent_ids or [candidate["agent_id"] for candidate in config["agent_candidates"]]
    paths = stage_paths(stage)
    submissions = [] if rerun else read_jsonl(paths["submissions"])
    verifiers = [] if rerun else read_jsonl(paths["verifiers"])
    cost_rows = [] if rerun else read_jsonl(paths["cost"])
    seen = set() if rerun else existing_run_ids(paths["submissions"])
    new_submissions: list[dict[str, Any]] = []
    new_verifiers: list[dict[str, Any]] = []
    new_costs: list[dict[str, Any]] = []
    for agent_id in selected_agents:
        candidate = candidates[agent_id]
        adapter = adapter_config_for(config, candidate)
        for task_id in task_ids:
            package = packages[task_id]
            package = replace(package, split=stage)
            run_id = f"{stage}__{agent_id}__{task_id}"
            if run_id in seen:
                continue
            start = time.monotonic()
            result = workspace.run_workspace_cell(
                ROOT,
                package,
                adapter,
                run_id,
                result_prefix=f"{config['run_policy']['result_prefix']}_{stage}",
            )
            usage = usage_from_submission(result.submission)
            usage_observed, estimated_cost, token_counts = estimate_cost(usage, candidate["model"], config)
            new_submissions.append(result.submission)
            new_verifiers.append(result.verifier)
            new_costs.append(
                {
                    "schema_version": "barcarolle.agent_selection_demo.cost.v1",
                    "run_id": run_id,
                    "timestamp": iso_now(),
                    "stage": stage,
                    "agent_id": agent_id,
                    "reviewer_name": candidate["reviewer_name"],
                    "harness": candidate["harness"],
                    "model": candidate["model"],
                    "task_id": task_id,
                    "status": result.verifier["status"],
                    "usage_observed": usage_observed,
                    "estimated_cost_usd": estimated_cost,
                    "cost_method": "observed_token_estimate" if usage_observed else "conservative_per_cell_estimate",
                    "latency_seconds": result.submission.get("latency_seconds", round(time.monotonic() - start, 3)),
                    **token_counts,
                }
            )
    submissions = workspace.merge_rows_by_run_id(submissions, new_submissions)
    verifiers = workspace.merge_rows_by_run_id(verifiers, new_verifiers)
    cost_rows = workspace.merge_rows_by_run_id(cost_rows, new_costs)
    rows = score_rows(stage, submissions, verifiers, cost_rows)
    expected = len(task_ids) * len(selected_agents)
    metrics = summarize_stage(stage, rows, expected)
    write_jsonl(paths["submissions"], submissions)
    write_jsonl(paths["verifiers"], verifiers)
    write_jsonl(paths["cost"], cost_rows)
    write_csv(
        paths["score"],
        rows,
        [
            "stage",
            "agent_id",
            "reviewer_name",
            "harness",
            "model",
            "task_id",
            "terminal_status",
            "scoreable_cell",
            "verified_pass",
            "failure_category",
            "latency_seconds",
            "estimated_cost_usd",
            "usage_observed",
            "patch_sha256",
        ],
    )
    write_json(paths["metrics"], metrics)
    write_stage_report(stage, metrics)
    return metrics


def write_stage_report(stage: str, metrics: dict[str, Any]) -> None:
    lines = [
        f"# Agent Selection Demo {stage.title()} Run",
        "",
        f"- Scheduled cells: `{metrics['scheduled_cells']}`.",
        f"- Completed cells: `{metrics['completed_cells']}`.",
        f"- Scoreable-cell rate: `{metrics['scoreable_cell_rate']}`.",
        f"- Verified solve rate: `{metrics['verified_solve_rate']}`.",
        f"- Estimated cost: `${metrics['estimated_cost_usd']}`.",
        "",
        "| Agent | Solve rate | Scoreable rate | Cost/solved | Median latency |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for agent_id, row in metrics["agent_metrics"].items():
        lines.append(
            "| {name} | {solve} | {scoreable} | {cost} | {latency} |".format(
                name=row["reviewer_name"] or agent_id,
                solve=row["verified_solve_rate"],
                scoreable=row["scoreable_cell_rate"],
                cost=row["cost_per_solved_task_usd"],
                latency=row["median_latency_seconds"],
            )
        )
    write_text(stage_paths(stage)["report"], "\n".join(lines) + "\n")


def policy_failure_count(row: dict[str, Any]) -> int:
    return sum(count for category, count in row.get("failure_counts", {}).items() if category != "verified pass" and category not in {"hidden verifier failure"})


def recommend(config: dict[str, Any]) -> dict[str, Any]:
    metrics = read_json(stage_paths("selection")["metrics"])
    agent_metrics = metrics["agent_metrics"]
    if not agent_metrics:
        raise RuntimeError("selection metrics are empty")
    ranked = sorted(
        agent_metrics.items(),
        key=lambda item: (
            -(item[1].get("verified_solve_rate") or 0.0),
            policy_failure_count(item[1]),
            item[1].get("cost_per_solved_task_usd") if item[1].get("cost_per_solved_task_usd") is not None else float("inf"),
            item[1].get("median_latency_seconds") if item[1].get("median_latency_seconds") is not None else float("inf"),
            item[0],
        ),
    )
    top_rate = ranked[0][1].get("verified_solve_rate") or 0.0
    within = [
        (agent_id, row)
        for agent_id, row in ranked
        if top_rate - (row.get("verified_solve_rate") or 0.0) <= 0.05
    ]
    production = sorted(
        within,
        key=lambda item: (
            item[1].get("cost_per_solved_task_usd") if item[1].get("cost_per_solved_task_usd") is not None else float("inf"),
            item[1].get("median_latency_seconds") if item[1].get("median_latency_seconds") is not None else float("inf"),
            item[0],
        ),
    )[0]
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.recommendation_lock.v1",
        "generated_at": iso_now(),
        "status": "locked",
        "rule": {
            "primary_quality": "highest verified solve rate; ties by fewer policy/replay failures, lower cost per solved task, lower median latency",
            "production_value": "cheapest agent within five percentage points of the top verified solve rate; otherwise top quality agent",
        },
        "primary_quality_recommendation": {
            "agent_id": ranked[0][0],
            **ranked[0][1],
        },
        "production_value_recommendation": {
            "agent_id": production[0],
            **production[1],
        },
        "selection_rank": [{"agent_id": agent_id, **row} for agent_id, row in ranked],
        "recommended_agent_id_for_holdout": production[0],
        "nearest_competitor_agent_id": ranked[1][0] if len(ranked) > 1 else None,
    }
    write_json(result_path("recommendation_lock.json"), payload)
    write_recommendation_report(payload)
    return payload


def write_recommendation_report(payload: dict[str, Any]) -> None:
    lines = [
        "# Agent Selection Demo Recommendation Lock",
        "",
        f"- Primary quality recommendation: `{payload['primary_quality_recommendation']['reviewer_name']}`.",
        f"- Production value recommendation: `{payload['production_value_recommendation']['reviewer_name']}`.",
        f"- Recommended Agent for holdout: `{payload['recommended_agent_id_for_holdout']}`.",
        f"- Nearest competitor: `{payload['nearest_competitor_agent_id']}`.",
        "",
        "| Rank | Agent | Solve rate | Cost/solved | Median latency |",
        "| ---: | --- | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(payload["selection_rank"], start=1):
        lines.append(
            f"| {index} | {row['reviewer_name']} | {row['verified_solve_rate']} | {row['cost_per_solved_task_usd']} | {row['median_latency_seconds']} |"
        )
    write_text(report_path("recommendation_lock.md"), "\n".join(lines) + "\n")


def holdout_support() -> dict[str, Any]:
    lock = read_json(result_path("recommendation_lock.json"))
    selection = read_json(stage_paths("selection")["metrics"])
    holdout = read_json(stage_paths("holdout")["metrics"])
    recommended = lock["recommended_agent_id_for_holdout"]
    holdout_agents = holdout["agent_metrics"]
    ranked_holdout = sorted(
        holdout_agents.items(),
        key=lambda item: (
            -(item[1].get("verified_solve_rate") or 0.0),
            item[1].get("cost_per_solved_task_usd") if item[1].get("cost_per_solved_task_usd") is not None else float("inf"),
            item[0],
        ),
    )
    top_holdout = ranked_holdout[0][0] if ranked_holdout else None
    recommended_rate = (holdout_agents.get(recommended) or {}).get("verified_solve_rate")
    top_rate = ranked_holdout[0][1].get("verified_solve_rate") if ranked_holdout else None
    if top_holdout == recommended:
        verdict = "supports"
    elif recommended_rate is not None and top_rate is not None and top_rate - recommended_rate <= 0.05:
        verdict = "partially_supports"
    else:
        verdict = "contradicts"
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.holdout_check.v1",
        "generated_at": iso_now(),
        "recommended_agent_id": recommended,
        "selection_recommended_agent": lock["production_value_recommendation"],
        "selection_metrics": selection["agent_metrics"].get(recommended),
        "holdout_rank": [{"agent_id": agent_id, **row} for agent_id, row in ranked_holdout],
        "holdout_verdict": verdict,
    }
    write_json(result_path("holdout_check.json"), payload)
    return payload


def markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    lines = ["| " + " | ".join(label for label, _key in columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for _label, key in columns) + " |")
    return lines


def final_report(config: dict[str, Any]) -> dict[str, Any]:
    gate_payload = read_json(result_path("repository_gate.json"))
    split = read_json(result_path("frozen_split.json"))
    smoke = read_json(stage_paths("smoke")["metrics"])
    selection = read_json(stage_paths("selection")["metrics"])
    holdout = read_json(stage_paths("holdout")["metrics"])
    lock = read_json(result_path("recommendation_lock.json"))
    holdout_check = holdout_support()
    matrix_rows = [
        {
            "Agent": candidate["reviewer_name"],
            "Harness": candidate["harness"],
            "Model": candidate["model"],
        }
        for candidate in config["agent_candidates"]
    ]
    selection_rows = [
        {"Agent": row["reviewer_name"], "Solve": row["verified_solve_rate"], "Cost/Solved": row["cost_per_solved_task_usd"], "Latency": row["median_latency_seconds"]}
        for row in lock["selection_rank"]
    ]
    holdout_rows = [
        {"Agent": row["reviewer_name"], "Solve": row["verified_solve_rate"], "Cost/Solved": row["cost_per_solved_task_usd"], "Latency": row["median_latency_seconds"]}
        for row in holdout_check["holdout_rank"]
    ]
    cost_latency = {
        "smoke_estimated_cost_usd": smoke["estimated_cost_usd"],
        "selection_estimated_cost_usd": selection["estimated_cost_usd"],
        "holdout_estimated_cost_usd": holdout["estimated_cost_usd"],
        "total_estimated_cost_usd": round(smoke["estimated_cost_usd"] + selection["estimated_cost_usd"] + holdout["estimated_cost_usd"], 8),
        "usage_observed_count": smoke["usage_observed_count"] + selection["usage_observed_count"] + holdout["usage_observed_count"],
    }
    closeout = {
        "actual_agent_matrix": matrix_rows,
        "target_repo": config["target_repo"]["repo_name"],
        "task_source": "Barcarolle repo-history task generator outputs, SWE-Bench++ style changed-test oracle extraction and local certification",
        "selection_task_count": split["selection_count"],
        "holdout_task_count": split["holdout_count"],
        "recommendation": lock["production_value_recommendation"],
        "holdout_verdict": holdout_check["holdout_verdict"],
        "cost_latency": cost_latency,
        "scoreable_rates": {
            "smoke": smoke["scoreable_cell_rate"],
            "selection": selection["scoreable_cell_rate"],
            "holdout": holdout["scoreable_cell_rate"],
        },
    }
    write_json(result_path("closeout_summary.json"), closeout)
    lines = [
        "# 目标仓库 Coding Agent 选型 Demo 报告",
        "",
        "## 1. 我们比较了一个目标仓库上的真实 Coding Agent",
        "",
        f"本次目标仓库是 `{config['target_repo']['repo_name']}`。任务来自仓库历史中的真实改动：实现文件和测试文件一起变化，系统从测试变化中构造隐藏验证，并在干净工作区重放 Agent 的代码 diff。",
        "",
        *markdown_table(matrix_rows, [("Agent", "Agent"), ("运行方式", "Harness"), ("模型", "Model")]),
        "",
        "## 2. 每个 Agent 在同一批 selection tasks 上按同一规则求解",
        "",
        f"repository gate 得到 `{gate_payload['task_pool_size']}` 个本地认证任务。本次冻结 `{split['selection_count']}` 个 selection tasks、`{split['holdout_count']}` 个 holdout tasks，另留 `{split['smoke_count']}` 个 smoke task。",
        "",
        f"Smoke scoreable-cell rate: `{smoke['scoreable_cell_rate']}`。Selection scoreable-cell rate: `{selection['scoreable_cell_rate']}`。",
        "",
        *markdown_table(selection_rows, [("Agent", "Agent"), ("selection 通过率", "Solve"), ("每解出一题成本", "Cost/Solved"), ("中位延迟秒", "Latency")]),
        "",
        "## 3. 每个 diff 都在干净 verifier workspace 里重放",
        "",
        f"Selection 阶段共调度 `{selection['scheduled_cells']}` 个 cell，完成 `{selection['completed_cells']}` 个，scoreable `{selection['scoreable_cells']}` 个。Holdout 阶段共调度 `{holdout['scheduled_cells']}` 个 cell，完成 `{holdout['completed_cells']}` 个，scoreable `{holdout['scoreable_cells']}` 个。",
        "",
        "## 4. 推荐规则同时看质量、成本、延迟和失败类型",
        "",
        f"质量视图推荐：`{lock['primary_quality_recommendation']['reviewer_name']}`。生产价值视图推荐：`{lock['production_value_recommendation']['reviewer_name']}`。",
        "",
        f"本报告锁定的推荐 Agent 是：`{lock['production_value_recommendation']['reviewer_name']}`。",
        "",
        "## 5. 我们用 fresh holdout tasks 检查推荐是否仍合理",
        "",
        f"Holdout 结论：`{holdout_check['holdout_verdict']}`。",
        "",
        *markdown_table(holdout_rows, [("Agent", "Agent"), ("holdout 通过率", "Solve"), ("每解出一题成本", "Cost/Solved"), ("中位延迟秒", "Latency")]),
        "",
        "## 6. 成本、延迟和失败类型",
        "",
        f"估算总成本：`${cost_latency['total_estimated_cost_usd']}`。其中 smoke `${cost_latency['smoke_estimated_cost_usd']}`，selection `${cost_latency['selection_estimated_cost_usd']}`，holdout `${cost_latency['holdout_estimated_cost_usd']}`。",
        "",
        f"可解析 token usage 的 cell 数：`{cost_latency['usage_observed_count']}`。没有 usage 的 cell 使用预先声明的保守每 cell 估算，报告中不把它说成真实账单。",
        "",
        "Selection 失败类型：",
        "",
        *[f"- `{category}`: `{count}`" for category, count in selection["failure_category_counts"].items()],
        "",
        "Holdout 失败类型：",
        "",
        *[f"- `{category}`: `{count}`" for category, count in holdout["failure_category_counts"].items()],
        "",
        "## 7. 这个结果能说明什么，不能说明什么",
        "",
        "可以讲：在这个目标仓库、这批任务和这些候选 Agent 中，系统能端到端比较完整 Coding Agent，捕获 diff，在干净工作区验证，并把质量、成本、延迟和失败原因放在一张决策表里。",
        "",
        "不能讲：这不是跨仓库结论，不证明某个模型家族普遍更好，也不证明任务选择方法已经具备长期预测有效性。这个 demo 只支持一次目标仓库选型决策的可执行流程和本次候选集内的观察结果。",
        "",
        "## 8. 下一步建议",
        "",
        "- 扩大到第二个目标仓库，验证推荐规则是否仍稳定。",
        "- 对推荐 Agent 和最接近竞争者做重复运行，估计随机性和失败可复现性。",
        "- 接入真实 billed cost，替代保守 per-cell 估算。",
        "- 把失败类型反馈给候选 Agent 配置，用下一轮任务检查是否能降低失败率。",
        "",
    ]
    write_text(report_path("target_repo_coding_agent_selection_demo_report_zh.md"), "\n".join(lines))
    return closeout


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Agent selection demo.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    subcommands = parser.add_subparsers(dest="command", required=True)
    gate_parser = subcommands.add_parser("gate")
    gate_parser.add_argument("--replay-sample-count", type=int, default=3)
    for name in ["smoke", "selection", "holdout"]:
        run_parser = subcommands.add_parser(name)
        run_parser.add_argument("--agent", action="append", default=None)
        run_parser.add_argument("--rerun", action="store_true")
    subcommands.add_parser("recommend")
    subcommands.add_parser("report")
    args = parser.parse_args()
    config = load_config(repo_path(args.config))
    if args.command == "gate":
        payload = gate(config, replay_sample_count=args.replay_sample_count)
        return 0 if payload["status"] == "ready" else 2
    if args.command in {"smoke", "selection", "holdout"}:
        metrics = run_stage(config, args.command, agent_ids=args.agent, rerun=args.rerun)
        min_rate = (
            float(config["run_policy"]["smoke_scoreable_cell_rate_min"])
            if args.command == "smoke"
            else float(config["run_policy"]["main_scoreable_cell_rate_min"])
        )
        rate = metrics["scoreable_cell_rate"] or 0.0
        return 0 if rate >= min_rate else 2
    if args.command == "recommend":
        recommend(config)
        return 0
    if args.command == "report":
        final_report(config)
        return 0
    raise ValueError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
