from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
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
TOP2_REPEAT_STAGE = "top2_repeat"
TOP2_REPEAT_AGENT_IDS = ["codex_gpt_5_4", "kilo_gpt_5_4"]

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
    if stage == TOP2_REPEAT_STAGE:
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


STAGE_SCORE_FIELDNAMES = [
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
    "cost_observation_kind",
    "usage_source",
    "billed_cost_usd",
    "patch_sha256",
]


def cost_observation_metadata(usage_observed: bool, billed_cost_usd: float | None = None) -> dict[str, Any]:
    if billed_cost_usd is not None:
        return {
            "cost_observation_kind": "billed_cost",
            "usage_source": "provider_billing_export",
            "billed_cost_usd": billed_cost_usd,
        }
    if usage_observed:
        return {
            "cost_observation_kind": "observed_tokens_estimated_cost",
            "usage_source": "adapter_output_usage_json",
            "billed_cost_usd": None,
        }
    return {
        "cost_observation_kind": "missing_usage_conservative_estimate",
        "usage_source": "missing_adapter_usage",
        "billed_cost_usd": None,
    }


def normalize_cost_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    usage_observed = normalized.get("usage_observed") is True or str(normalized.get("usage_observed")).lower() == "true"
    billed_raw = normalized.get("billed_cost_usd")
    billed_cost = None if billed_raw in {None, ""} else float(billed_raw)
    metadata = cost_observation_metadata(usage_observed, billed_cost_usd=billed_cost)
    if not normalized.get("cost_observation_kind"):
        normalized["cost_observation_kind"] = metadata["cost_observation_kind"]
    if not normalized.get("usage_source"):
        normalized["usage_source"] = metadata["usage_source"]
    if normalized.get("billed_cost_usd") in {None, ""}:
        normalized["billed_cost_usd"] = metadata["billed_cost_usd"]
    return normalized


def persist_stage_outputs(
    stage: str,
    submissions: list[dict[str, Any]],
    verifiers: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    expected_cells: int,
) -> dict[str, Any]:
    paths = stage_paths(stage)
    cost_rows = [normalize_cost_row(row) for row in cost_rows]
    rows = score_rows(stage, submissions, verifiers, cost_rows)
    metrics = summarize_stage(stage, rows, expected_cells)
    write_jsonl(paths["submissions"], submissions)
    write_jsonl(paths["verifiers"], verifiers)
    write_jsonl(paths["cost"], cost_rows)
    write_csv(paths["score"], rows, STAGE_SCORE_FIELDNAMES)
    write_json(paths["metrics"], metrics)
    write_stage_report(stage, metrics)
    return metrics


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
                "cost_observation_kind": cost.get("cost_observation_kind", cost.get("cost_method", "")),
                "usage_source": cost.get("usage_source", ""),
                "billed_cost_usd": cost.get("billed_cost_usd", ""),
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


def cost_observation_kind(observed_count: int, total_count: int) -> str:
    if total_count == 0:
        return "none"
    if observed_count == total_count:
        return "observed_tokens_estimated_cost"
    if observed_count == 0:
        return "missing_usage_conservative_estimate"
    return "mixed_observed_and_missing_usage_estimate"


def summarize_stage(stage: str, rows: list[dict[str, Any]], expected_cells: int) -> dict[str, Any]:
    by_agent: dict[str, dict[str, Any]] = {}
    for agent_id in sorted({str(row["agent_id"]) for row in rows}):
        agent_rows = [row for row in rows if row["agent_id"] == agent_id]
        scoreable = [row for row in agent_rows if row["scoreable_cell"] is True]
        pass_count = sum(1 for row in agent_rows if row["verified_pass"] is True)
        usage_observed_count = sum(1 for row in agent_rows if row.get("usage_observed") is True)
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
            "usage_observed_count": usage_observed_count,
            "usage_observed_rate": None if not agent_rows else round(usage_observed_count / len(agent_rows), 4),
            "cost_observation_kind": cost_observation_kind(usage_observed_count, len(agent_rows)),
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
        "usage_observed_rate": None if expected_cells == 0 else round(sum(1 for row in rows if row.get("usage_observed") is True) / expected_cells, 4),
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
    expected = len(task_ids) * len(selected_agents)
    metrics = persist_stage_outputs(stage, submissions, verifiers, cost_rows, expected)
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
            cost_row = (
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
                    **cost_observation_metadata(usage_observed),
                    "latency_seconds": result.submission.get("latency_seconds", round(time.monotonic() - start, 3)),
                    **token_counts,
                }
            )
            submissions = workspace.merge_rows_by_run_id(submissions, [result.submission])
            verifiers = workspace.merge_rows_by_run_id(verifiers, [result.verifier])
            cost_rows = workspace.merge_rows_by_run_id(cost_rows, [cost_row])
            seen.add(run_id)
            metrics = persist_stage_outputs(stage, submissions, verifiers, cost_rows, expected)
    return metrics


def phase0_exp() -> Path:
    return ROOT / "experiments" / "phase0_headroom"


def stage_namespace(config: dict[str, Any], stage: str, agent_id: str) -> Path:
    return workspace.artifact_namespace(f"{config['run_policy']['result_prefix']}_{stage}", agent_id)


def relative_to_phase0(path: Path) -> str:
    return str(path.relative_to(phase0_exp()))


def read_optional_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def infer_adapter_latency(raw_dir: Path, stderr_text: str, candidate: dict[str, Any]) -> float:
    match = re.search(r"duration_seconds=([0-9]+(?:\.[0-9]+)?)", stderr_text)
    if match:
        return round(float(match.group(1)), 3)
    files = [path for path in raw_dir.iterdir() if path.is_file()] if raw_dir.exists() else []
    if len(files) >= 2:
        mtimes = [path.stat().st_mtime for path in files]
        span = max(mtimes) - min(mtimes)
        if span > 0:
            return round(span, 3)
    return float(candidate.get("timeout_seconds") or 0)


def recover_replay_verifier(
    run_id: str,
    package: workspace.TaskPackage,
    patch_path: Path,
    raw_dir: Path,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"barcarolle-demo-recover-{run_id}-") as tmp:
        verifier_workspace = Path(tmp) / "verifier"
        workspace.archive_tree(package.source_repo, package.base_commit, verifier_workspace)
        workspace.initialize_workspace_git(verifier_workspace)
        applied, apply_error = workspace.apply_patch(verifier_workspace, patch_path)
        if not applied:
            return {
                "status": "harness_error",
                "verifier_exit_code": None,
                "fresh_workspace": True,
                "harness_error": "captured_patch_did_not_apply",
                "patch_apply_error_tail": apply_error,
            }
        injected, inject_error = workspace.inject_hidden_oracle(ROOT, package, verifier_workspace, raw_dir)
        if not injected:
            return {
                "status": "harness_error",
                "verifier_exit_code": None,
                "fresh_workspace": True,
                "harness_error": inject_error,
            }
        verify_stdout = raw_dir / "recovery_verifier_stdout.txt"
        verify_stderr = raw_dir / "recovery_verifier_stderr.txt"
        verify = workspace.run_command(
            package.verifier_command,
            verifier_workspace,
            timeout=package.timeout_seconds,
            env=workspace.verifier_env_for(package, verifier_workspace),
        )
        verify_stdout.write_text(verify.stdout, encoding="utf-8")
        verify_stderr.write_text(verify.stderr, encoding="utf-8")
        return {
            "status": "timeout" if verify.timed_out else "verified_pass" if verify.returncode == 0 else "verified_fail",
            "verifier_exit_code": verify.returncode,
            "fresh_workspace": True,
            "duration_seconds": round(verify.duration_seconds, 3),
            "raw_artifacts": {
                "stdout": relative_to_phase0(verify_stdout),
                "stderr": relative_to_phase0(verify_stderr),
            },
            "harness_error": None,
        }


def recover_cell_from_raw(
    config: dict[str, Any],
    stage: str,
    agent_id: str,
    task_id: str,
    package: workspace.TaskPackage,
    candidate: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
    run_id = f"{stage}__{agent_id}__{task_id}"
    namespace = stage_namespace(config, stage, agent_id)
    raw_dir = phase0_exp() / workspace.RAW_REL / namespace / run_id
    workspace_root = phase0_exp() / workspace.WORKSPACE_REL / namespace / run_id
    solver_workspace = workspace_root / "solver"
    if not raw_dir.exists():
        return None

    stdout_path = raw_dir / "acut_stdout.txt"
    stderr_path = raw_dir / "acut_stderr.txt"
    patch_path = raw_dir / "submission.patch"
    stderr_text = read_optional_text(stderr_path)
    patch_existed = patch_path.exists()
    if not patch_existed and solver_workspace.exists():
        patch_path.write_text(workspace.capture_diff(solver_workspace), encoding="utf-8")
    patch_text = read_optional_text(patch_path)
    changed = workspace.changed_paths(solver_workspace) if solver_workspace.exists() else []
    raw_artifacts: dict[str, str] = {}
    for key, path in [("stdout", stdout_path), ("stderr", stderr_path), ("patch", patch_path)]:
        if path.exists():
            raw_artifacts[key] = relative_to_phase0(path)

    latency = infer_adapter_latency(raw_dir, stderr_text, candidate)
    base_submission = {
        "schema_version": "barcarolle.workspace_acut_submission.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "adapter_id": agent_id,
        "acut_id": agent_id,
        "harness_name": candidate["harness"],
        "model_or_agent_name": candidate["model"],
        "command_template_source": "agent_selection_demo_config",
        "endpoint_proof_status": "llm_endpoint_proxy_secret_isolated",
        "task_id": package.task_id,
        "repo_id": package.repo_id,
        "split": stage,
        "patch_source": "recovered_from_ignored_workspace_diff" if not patch_existed else "git_diff_after_workspace_run",
        "patch_sha256": workspace.sha256_file(patch_path) if patch_path.exists() else sha256_text(""),
        "latency_seconds": latency,
        "raw_artifacts": raw_artifacts,
        "task_package_metadata": workspace.package_submission_metadata(package),
    }
    base_verifier = {
        "schema_version": "barcarolle.workspace_acut_verifier.v1",
        "run_id": run_id,
        "generated_at": iso_now(),
        "adapter_id": agent_id,
        "acut_id": agent_id,
        "harness_name": candidate["harness"],
        "model_or_agent_name": candidate["model"],
        "command_template_source": "agent_selection_demo_config",
        "endpoint_proof_status": "llm_endpoint_proxy_secret_isolated",
        "task_id": package.task_id,
        "repo_id": package.repo_id,
        "split": stage,
        "fresh_workspace": False,
        "status": "invalid_output",
        "verifier_exit_code": None,
        "harness_error": None,
    }

    acut_timed_out_before_capture = not patch_existed and not stderr_path.exists()
    if acut_timed_out_before_capture:
        submission = {
            **base_submission,
            "status": "acut_harness_error",
            "acut_exit_code": 124,
            "changed_paths": changed,
            "recovery_note": "adapter_timed_out_before_result_persistence",
        }
        verifier = {
            **base_verifier,
            "status": "acut_harness_error",
            "harness_error": "acut_command_failed",
            "acut_exit_code": 124,
        }
    elif not patch_text.strip():
        submission = {**base_submission, "status": "invalid_output", "acut_exit_code": 0}
        verifier = {**base_verifier, "status": "invalid_output", "harness_error": "empty_workspace_diff"}
    else:
        submission = {**base_submission, "status": "submitted", "acut_exit_code": 0, "changed_paths": changed}
        violation, violating_paths = workspace.policy_violation(changed, package)
        if violation:
            verifier = {
                **base_verifier,
                "status": "policy_violation",
                "harness_error": violation,
                "changed_paths": violating_paths,
            }
        else:
            verifier = {**base_verifier, **recover_replay_verifier(run_id, package, patch_path, raw_dir)}

    usage = usage_from_submission(submission)
    usage_observed, estimated_cost, token_counts = estimate_cost(usage, candidate["model"], config)
    cost = {
        "schema_version": "barcarolle.agent_selection_demo.cost.v1",
        "run_id": run_id,
        "timestamp": iso_now(),
        "stage": stage,
        "agent_id": agent_id,
        "reviewer_name": candidate["reviewer_name"],
        "harness": candidate["harness"],
        "model": candidate["model"],
        "task_id": task_id,
        "status": verifier["status"],
        "usage_observed": usage_observed,
        "estimated_cost_usd": estimated_cost,
        "cost_method": "observed_token_estimate" if usage_observed else "conservative_per_cell_estimate",
        **cost_observation_metadata(usage_observed),
        "latency_seconds": latency,
        **token_counts,
    }
    return submission, verifier, cost


def recover_stage(config: dict[str, Any], stage: str, agent_ids: list[str] | None = None) -> dict[str, Any]:
    split = load_split()
    packages = package_map(config)
    task_ids = stage_task_ids(split, stage)
    candidates = candidate_by_id(config)
    selected_agents = agent_ids or [candidate["agent_id"] for candidate in config["agent_candidates"]]
    paths = stage_paths(stage)
    submissions = read_jsonl(paths["submissions"])
    verifiers = read_jsonl(paths["verifiers"])
    cost_rows = read_jsonl(paths["cost"])
    recovered_run_ids: list[str] = []
    for agent_id in selected_agents:
        candidate = candidates[agent_id]
        for task_id in task_ids:
            package = replace(packages[task_id], split=stage)
            recovered = recover_cell_from_raw(config, stage, agent_id, task_id, package, candidate)
            if recovered is None:
                continue
            submission, verifier, cost = recovered
            submissions = workspace.merge_rows_by_run_id(submissions, [submission])
            verifiers = workspace.merge_rows_by_run_id(verifiers, [verifier])
            cost_rows = workspace.merge_rows_by_run_id(cost_rows, [cost])
            recovered_run_ids.append(submission["run_id"])
    expected = len(task_ids) * len(selected_agents)
    metrics = persist_stage_outputs(stage, submissions, verifiers, cost_rows, expected)
    write_json(
        result_path(f"{stage}_recovery_manifest.json"),
        {
            "schema_version": "barcarolle.agent_selection_demo.recovery_manifest.v1",
            "generated_at": iso_now(),
            "stage": stage,
            "agent_ids": selected_agents,
            "recovered_cells": len(recovered_run_ids),
            "paid_agent_calls_made": False,
            "run_ids_sha256": sha256_text("\n".join(sorted(recovered_run_ids))),
            "metrics": metrics,
        },
    )
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


def cost_usage_observed_threshold(config: dict[str, Any]) -> float:
    return float(config.get("run_policy", {}).get("cost_usage_observed_rate_min", 0.95))


def cost_comparison_summary(agent_metrics: dict[str, dict[str, Any]], threshold: float) -> dict[str, Any]:
    observed_rates = {
        agent_id: row.get("usage_observed_rate")
        for agent_id, row in sorted(agent_metrics.items())
    }
    comparable = bool(agent_metrics) and all((row.get("usage_observed_rate") or 0.0) >= threshold for row in agent_metrics.values())
    return {
        "status": "observed_cost_comparable" if comparable else "cost_inconclusive_usage_coverage",
        "usage_observed_rate_min": threshold,
        "agent_usage_observed_rates": observed_rates,
    }


def recommend(config: dict[str, Any]) -> dict[str, Any]:
    metrics = read_json(stage_paths("selection")["metrics"])
    agent_metrics = metrics["agent_metrics"]
    if not agent_metrics:
        raise RuntimeError("selection metrics are empty")
    cost_comparison = cost_comparison_summary(agent_metrics, cost_usage_observed_threshold(config))
    use_cost = cost_comparison["status"] == "observed_cost_comparable"

    def cost_sort_value(row: dict[str, Any]) -> float:
        if not use_cost:
            return 0.0
        value = row.get("cost_per_solved_task_usd")
        return value if value is not None else float("inf")

    ranked = sorted(
        agent_metrics.items(),
        key=lambda item: (
            -(item[1].get("verified_solve_rate") or 0.0),
            policy_failure_count(item[1]),
            cost_sort_value(item[1]),
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
    if use_cost:
        production = sorted(
            within,
            key=lambda item: (
                item[1].get("cost_per_solved_task_usd") if item[1].get("cost_per_solved_task_usd") is not None else float("inf"),
                item[1].get("median_latency_seconds") if item[1].get("median_latency_seconds") is not None else float("inf"),
                item[0],
            ),
        )[0]
        production_status = "cost_comparable"
    else:
        production = ranked[0]
        production_status = "cost_inconclusive_fallback_to_primary_quality"
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.recommendation_lock.v1",
        "generated_at": iso_now(),
        "status": "locked",
        "rule": {
            "primary_quality": (
                "highest verified solve rate; ties by fewer policy/replay failures, "
                + ("lower cost per solved task, " if use_cost else "cost skipped when usage coverage is inconclusive, ")
                + "lower median latency"
            ),
            "production_value": (
                "cheapest agent within five percentage points of the top verified solve rate when cost usage coverage is comparable; "
                "otherwise cost-inconclusive fallback to primary quality"
            ),
        },
        "cost_comparison": cost_comparison,
        "primary_quality_recommendation": {
            "agent_id": ranked[0][0],
            **ranked[0][1],
        },
        "production_value_recommendation": {
            "agent_id": production[0],
            **production[1],
        },
        "production_value_status": production_status,
        "selection_rank": [{"agent_id": agent_id, **row} for agent_id, row in ranked],
        "recommended_agent_id_for_holdout": production[0],
        "nearest_competitor_agent_id": ranked[1][0] if len(ranked) > 1 else None,
    }
    write_json(result_path("recommendation_lock.json"), payload)
    write_recommendation_report(payload)
    return payload


def write_recommendation_report(payload: dict[str, Any]) -> None:
    production_status = payload.get("production_value_status", "cost_comparable")
    lines = [
        "# Agent Selection Demo Recommendation Lock",
        "",
        f"- Primary quality recommendation: `{payload['primary_quality_recommendation']['reviewer_name']}`.",
        f"- Production value recommendation: `{payload['production_value_recommendation']['reviewer_name']}`.",
        f"- Production value status: `{production_status}`.",
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def pf(value: bool) -> str:
    return "P" if value else "F"


def outcome_mark(row: dict[str, str] | None) -> str:
    if row is None:
        return "M"
    status = row.get("terminal_status")
    if status == "verified_pass":
        return "P"
    if status == "verified_fail":
        return "F"
    return "I"


def top2_repeatability_report(config: dict[str, Any]) -> dict[str, Any]:
    split = read_json(result_path("frozen_split.json"))
    original_rows = [
        row
        for row in read_csv_rows(stage_paths("holdout")["score"])
        if row.get("agent_id") in TOP2_REPEAT_AGENT_IDS
    ]
    repeat_rows = [
        row
        for row in read_csv_rows(stage_paths(TOP2_REPEAT_STAGE)["score"])
        if row.get("agent_id") in TOP2_REPEAT_AGENT_IDS
    ]
    repeat_metrics = read_json(stage_paths(TOP2_REPEAT_STAGE)["metrics"])
    packages = package_map(config)

    def by_agent_task(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
        return {(row["agent_id"], row["task_id"]): row for row in rows}

    original_by_key = by_agent_task(original_rows)
    repeat_by_key = by_agent_task(repeat_rows)
    stability_rows: list[dict[str, Any]] = []
    for task_id in split["holdout_tasks"]:
        package = packages.get(task_id)
        source = ((package.metadata.get("metadata_sources") or {}).get("task_source") if package else "") or ""
        changed_files = package.metadata.get("changed_files", []) if package else []
        modules = sorted({Path(path).name for path in changed_files if not is_test_path(path)})
        row: dict[str, Any] = {
            "task_id": task_id,
            "source": source,
            "task_time": package.metadata.get("task_time") if package else "",
            "module": ", ".join(modules),
        }
        for agent_id in TOP2_REPEAT_AGENT_IDS:
            original = original_by_key.get((agent_id, task_id))
            repeat = repeat_by_key.get((agent_id, task_id))
            original_pass = csv_bool(original["verified_pass"]) if original else False
            repeat_pass = csv_bool(repeat["verified_pass"]) if repeat else False
            short = "codex" if agent_id == "codex_gpt_5_4" else "kilo"
            row[f"{short}_original"] = pf(original_pass)
            row[f"{short}_repeat"] = outcome_mark(repeat)
            row[f"{short}_changed"] = original_pass != repeat_pass if repeat and repeat.get("terminal_status") in SCOREABLE_STATUSES else ""
            row[f"{short}_repeat_status"] = repeat["terminal_status"] if repeat else "not_run"
        row["relationship_original"] = f"{row['codex_original']}/{row['kilo_original']}"
        row["relationship_repeat"] = f"{row['codex_repeat']}/{row['kilo_repeat']}"
        stability_rows.append(row)

    agent_summaries: dict[str, dict[str, Any]] = {}
    for agent_id in TOP2_REPEAT_AGENT_IDS:
        original_agent_rows = [row for row in original_rows if row["agent_id"] == agent_id]
        repeat_agent_rows = [row for row in repeat_rows if row["agent_id"] == agent_id]
        agent_summaries[agent_id] = {
            "reviewer_name": repeat_agent_rows[0]["reviewer_name"] if repeat_agent_rows else agent_id,
            "original_pass_count": sum(csv_bool(row["verified_pass"]) for row in original_agent_rows),
            "repeat_pass_count": sum(csv_bool(row["verified_pass"]) for row in repeat_agent_rows),
            "completed_cells": len(repeat_agent_rows),
            "timeout_or_infra_cells": sum(row["terminal_status"] not in SCOREABLE_STATUSES for row in repeat_agent_rows),
            "scoreable_cells": sum(csv_bool(row["scoreable_cell"]) for row in repeat_agent_rows),
            "changed_tasks": [row["task_id"] for row in stability_rows if row[f"{'codex' if agent_id == 'codex_gpt_5_4' else 'kilo'}_changed"]],
        }

    repeat_passes = {agent_id: row["repeat_pass_count"] for agent_id, row in agent_summaries.items()}
    original_passes = {agent_id: row["original_pass_count"] for agent_id, row in agent_summaries.items()}
    repeat_lead = repeat_passes["kilo_gpt_5_4"] - repeat_passes["codex_gpt_5_4"]
    original_lead = original_passes["kilo_gpt_5_4"] - original_passes["codex_gpt_5_4"]
    canonical_rows = [row for row in stability_rows if row["source"] == "canonical_history"]
    repeat_scoreable = repeat_metrics.get("scoreable_cells", 0)
    repeat_scheduled = repeat_metrics.get("scheduled_cells", len(repeat_rows))
    repeat_completed = repeat_metrics.get("completed_cells", len(repeat_rows))
    acceptance_reachable = repeat_completed == repeat_scheduled and repeat_scoreable / max(repeat_scheduled, 1) >= 0.95
    infrastructure_rows = [
        row
        for row in repeat_rows
        if row.get("terminal_status") not in SCOREABLE_STATUSES
    ]
    interpretation = (
        "blocked_infrastructure"
        if not acceptance_reachable
        else
        "stable_kilo_lead"
        if repeat_lead > 0 and repeat_scoreable / max(repeat_scheduled, 1) >= 0.95
        else "noisy_or_inconclusive"
    )
    cost_usage = {
        agent_id: {
            "usage_observed_count": row.get("usage_observed_count"),
            "usage_observed_rate": row.get("usage_observed_rate"),
            "cost_observation_kind": row.get("cost_observation_kind"),
            "cost_per_task_usd": row.get("cost_per_task_usd"),
            "cost_per_solved_task_usd": row.get("cost_per_solved_task_usd"),
        }
        for agent_id, row in repeat_metrics.get("agent_metrics", {}).items()
        if agent_id in TOP2_REPEAT_AGENT_IDS
    }
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.top2_repeatability.v1",
        "generated_at": iso_now(),
        "target_repo": config["target_repo"]["repo_name"],
        "stage": TOP2_REPEAT_STAGE,
        "agent_ids": TOP2_REPEAT_AGENT_IDS,
        "task_ids": split["holdout_tasks"],
        "repeat_cells": {
            "scheduled": repeat_metrics.get("scheduled_cells"),
            "completed": repeat_metrics.get("completed_cells"),
            "scoreable": repeat_metrics.get("scoreable_cells"),
            "scoreable_cell_rate": repeat_metrics.get("scoreable_cell_rate"),
            "acceptance_reachable": acceptance_reachable,
        },
        "original_passes": original_passes,
        "repeat_passes": repeat_passes,
        "original_kilo_lead_cells": original_lead,
        "repeat_kilo_lead_cells": repeat_lead,
        "agent_summaries": agent_summaries,
        "canonical_history_repeat": {
            "task_count": len(canonical_rows),
            "codex_pass_count": sum(row["codex_repeat"] == "P" for row in canonical_rows),
            "codex_scoreable_count": sum(row["codex_repeat"] in {"P", "F"} for row in canonical_rows),
            "kilo_pass_count": sum(row["kilo_repeat"] == "P" for row in canonical_rows),
            "kilo_scoreable_count": sum(row["kilo_repeat"] in {"P", "F"} for row in canonical_rows),
            "kilo_infra_count": sum(row["kilo_repeat"] == "I" for row in canonical_rows),
            "kilo_not_run_count": sum(row["kilo_repeat"] == "M" for row in canonical_rows),
        },
        "infrastructure_or_policy_rows": infrastructure_rows,
        "cost_usage": cost_usage,
        "interpretation": interpretation,
        "stability_rows": stability_rows,
    }
    write_json(result_path("top2_repeatability_check.json"), payload)
    write_csv(
        result_path("top2_repeatability_stability_table.csv"),
        stability_rows,
        [
            "task_id",
            "source",
            "task_time",
            "module",
            "codex_original",
            "codex_repeat",
            "codex_changed",
            "kilo_original",
            "kilo_repeat",
            "kilo_changed",
            "relationship_original",
            "relationship_repeat",
            "codex_repeat_status",
            "kilo_repeat_status",
        ],
    )

    candidates = candidate_by_id(config)
    matrix_rows = [
        {
            "Agent": candidates[agent_id]["reviewer_name"],
            "Harness": candidates[agent_id]["harness"],
            "Model": candidates[agent_id]["model"],
        }
        for agent_id in TOP2_REPEAT_AGENT_IDS
    ]
    summary_rows = [
        {
            "Agent": agent_summaries[agent_id]["reviewer_name"],
            "Original": agent_summaries[agent_id]["original_pass_count"],
            "Repeat": (
                f"{agent_summaries[agent_id]['repeat_pass_count']}/{agent_summaries[agent_id]['scoreable_cells']} scoreable; "
                f"{agent_summaries[agent_id]['completed_cells']} completed, {agent_summaries[agent_id]['timeout_or_infra_cells']} infra"
            ),
            "Changed": ", ".join(agent_summaries[agent_id]["changed_tasks"]) or "None",
            "Usage": cost_usage.get(agent_id, {}).get("cost_observation_kind", ""),
        }
        for agent_id in TOP2_REPEAT_AGENT_IDS
    ]
    task_rows = [
        {
            "Task": row["task_id"],
            "Source": row["source"],
            "Module": row["module"],
            "Codex": f"{row['codex_original']}->{row['codex_repeat']}",
            "Kilo": f"{row['kilo_original']}->{row['kilo_repeat']}",
        }
        for row in stability_rows
    ]
    highlighted = [row for row in stability_rows if row["task_id"] in {"boltons__hist__022", "boltons__hist__023", "boltons__hist__027", "boltons__hist__028"}]
    infra_sentence = (
        "repeat 中没有非可评分、超时、policy violation 或 verifier replay 基础设施失败。"
        if not infrastructure_rows
        else f"repeat 中有 `{len(infrastructure_rows)}` 个非可评分/基础设施相关 cell，需要单独排查。"
    )
    story_sentence = (
        "repeat 被 Kilo adapter timeout 阻断，不能作为 scoreable ranking 结果；Codex repeat 完成但 Kilo repeat 不完整。"
        if interpretation == "blocked_infrastructure"
        else
        "Kilo 的领先仍然存在；这让第一次 holdout 反转不太像纯单次随机波动。"
        if interpretation == "stable_kilo_lead"
        else "repeat 没有给出清晰稳定领先；单次运行随机性仍应作为主要解释。"
    )
    stochasticity_sentence = (
        "由于 Kilo repeat 没有达到可评分完整性，本次不能判断 Kilo holdout 领先是否稳定，也不能把变化归因于模型随机性；当前主要解释是 Kilo adapter/CLI timeout 基础设施问题。"
        if interpretation == "blocked_infrastructure"
        else "stochasticity 仍是合理解释的一部分，因为这里只做了一次 repeat，且两个 Agent 的若干 task-level outcome 发生变化；但 repeat 后 Kilo 仍领先，说明不能把第一次 Kilo 领先简单归因为一次偶然抽样。"
    )
    lines = [
        "# Top-2 Repeatability Check",
        "",
        "## 结论",
        "",
        f"本次只重复 `{config['target_repo']['repo_name']}` 的同一批 10 个 holdout tasks，Agent 矩阵为 Codex + GPT mainline 与 Kilo + GPT mainline，模型均为 `gpt-5.4`。",
        "",
        f"20 个 repeat cells 中完成 `{repeat_metrics.get('completed_cells')}` 个，可评分 `{repeat_metrics.get('scoreable_cells')}` 个，可评分率 `{repeat_metrics.get('scoreable_cell_rate')}`，acceptance reachable 为 `{acceptance_reachable}`。",
        "",
        f"原 holdout 是 Kilo `{original_passes['kilo_gpt_5_4']}/10` 对 Codex `{original_passes['codex_gpt_5_4']}/10`；当前 persisted repeat 是 Kilo `{repeat_passes['kilo_gpt_5_4']}/{agent_summaries['kilo_gpt_5_4']['scoreable_cells']}` scoreable（`{agent_summaries['kilo_gpt_5_4']['completed_cells']}` completed, `{agent_summaries['kilo_gpt_5_4']['timeout_or_infra_cells']}` infra）对 Codex `{repeat_passes['codex_gpt_5_4']}/10`。",
        "",
        story_sentence,
        "",
        stochasticity_sentence,
        "",
        "## 实际矩阵",
        "",
        *markdown_table(matrix_rows, [("Agent", "Agent"), ("Harness", "Harness"), ("Model", "Model")]),
        "",
        "## 任务集",
        "",
        f"任务集完全沿用 `frozen_split.json` 的 holdout tasks：`{', '.join(split['holdout_tasks'])}`。",
        "",
        "## Agent 汇总",
        "",
        *markdown_table(summary_rows, [("Agent", "Agent"), ("原 holdout pass", "Original"), ("repeat pass", "Repeat"), ("变化任务", "Changed"), ("成本 usage", "Usage")]),
        "",
        "## Task-level 稳定性",
        "",
        *markdown_table(task_rows, [("Task", "Task"), ("Source", "Source"), ("Module", "Module"), ("Codex 原->复", "Codex"), ("Kilo 原->复", "Kilo")]),
        "",
        "## 重点失败任务",
        "",
        *markdown_table(
            [
                {
                    "Task": row["task_id"],
                    "Codex": f"{row['codex_original']}->{row['codex_repeat']}",
                    "Kilo": f"{row['kilo_original']}->{row['kilo_repeat']}",
                    "Repeat relationship": row["relationship_repeat"],
                }
                for row in highlighted
            ],
            [("Task", "Task"), ("Codex 原->复", "Codex"), ("Kilo 原->复", "Kilo"), ("repeat 关系", "Repeat relationship")],
        ),
        "",
        "## Later canonical_history",
        "",
        f"holdout 中 `canonical_history` 任务 `{len(canonical_rows)}` 个。repeat 中 Codex 通过 `{payload['canonical_history_repeat']['codex_pass_count']}/{payload['canonical_history_repeat']['codex_scoreable_count']}` scoreable；Kilo 为 `{payload['canonical_history_repeat']['kilo_pass_count']}/{payload['canonical_history_repeat']['kilo_scoreable_count']}` scoreable，另有 `{payload['canonical_history_repeat']['kilo_infra_count']}` 个 infra、`{payload['canonical_history_repeat']['kilo_not_run_count']}` 个 not run，因此不能判断 Kilo 是否仍强于 later canonical_history。",
        "",
        "## 基础设施与成本 caveat",
        "",
        infra_sentence,
        "",
        "成本仍不能作为 production-value winner 的依据：Codex repeat usage 覆盖与 Kilo repeat usage 覆盖不对称时，Kilo 成本继续按 conservative per-cell estimate 标记，报告只把 pass/fail 稳定性作为主要结论。",
        "",
        "## 下一步建议",
        "",
        "建议下一步优先做更多 repeats 或修复 Kilo usage normalization 后再讨论成本；不要基于这次单仓库 top-2 repeat 进入第二仓库扩展、prompt/tool tuning、learned selector 或 rolling-origin paid validation。",
        "",
    ]
    write_text(report_path("top2_repeatability_check_zh.md"), "\n".join(lines))
    return payload


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
    verdict_labels = {
        "supports": "支持选择集推荐",
        "partially_supports": "部分支持选择集推荐",
        "contradicts": "不支持选择集推荐",
    }
    holdout_verdict_label = verdict_labels.get(holdout_check["holdout_verdict"], holdout_check["holdout_verdict"])
    cost_latency = {
        "smoke_estimated_cost_usd": smoke["estimated_cost_usd"],
        "selection_estimated_cost_usd": selection["estimated_cost_usd"],
        "holdout_estimated_cost_usd": holdout["estimated_cost_usd"],
        "total_estimated_cost_usd": round(smoke["estimated_cost_usd"] + selection["estimated_cost_usd"] + holdout["estimated_cost_usd"], 8),
        "usage_observed_count": smoke["usage_observed_count"] + selection["usage_observed_count"] + holdout["usage_observed_count"],
    }
    production_value_status = lock.get("production_value_status", "cost_comparable")
    production_value_sentence = (
        f"生产价值视图推荐：`{lock['production_value_recommendation']['reviewer_name']}`。"
        if production_value_status == "cost_comparable"
        else (
            "生产价值视图成本口径不足以给出单一成本赢家；"
            f"本次按质量视图 fallback 为：`{lock['production_value_recommendation']['reviewer_name']}`。"
        )
    )
    closeout = {
        "actual_agent_matrix": matrix_rows,
        "target_repo": config["target_repo"]["repo_name"],
        "task_source": "目标仓库历史改动；从测试变化构造隐藏验证，并通过本地干净重放认证",
        "selection_task_count": split["selection_count"],
        "holdout_task_count": split["holdout_count"],
        "recommendation": lock["production_value_recommendation"],
        "holdout_verdict": holdout_check["holdout_verdict"],
        "cost_latency": cost_latency,
        "production_value_status": production_value_status,
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
        f"本次目标仓库是 `{config['target_repo']['repo_name']}`。任务来自仓库历史中的真实改动：实现文件和测试文件一起变化，系统从测试变化中构造隐藏验证，并在干净工作区重放 Agent 的代码改动。",
        "",
        *markdown_table(matrix_rows, [("Agent", "Agent"), ("运行方式", "Harness"), ("模型", "Model")]),
        "",
        "## 2. 每个 Agent 在同一批选择集任务上按同一规则求解",
        "",
        f"前置检查得到 `{gate_payload['task_pool_size']}` 个本地认证任务。本次冻结 `{split['selection_count']}` 个选择集任务、`{split['holdout_count']}` 个留出检查任务，另留 `{split['smoke_count']}` 个冒烟任务。",
        "",
        f"冒烟可评分运行率：`{smoke['scoreable_cell_rate']}`。选择集可评分运行率：`{selection['scoreable_cell_rate']}`。",
        "",
        *markdown_table(selection_rows, [("Agent", "Agent"), ("选择集通过率", "Solve"), ("每解出一题成本", "Cost/Solved"), ("中位延迟秒", "Latency")]),
        "",
        "## 3. 每个代码改动都在干净验证目录里重放",
        "",
        f"选择集共调度 `{selection['scheduled_cells']}` 次运行，完成 `{selection['completed_cells']}` 次，可评分 `{selection['scoreable_cells']}` 次。留出检查共调度 `{holdout['scheduled_cells']}` 次运行，完成 `{holdout['completed_cells']}` 次，可评分 `{holdout['scoreable_cells']}` 次。",
        "",
        "## 4. 推荐规则同时看质量、成本、延迟和失败类型",
        "",
        f"质量视图推荐：`{lock['primary_quality_recommendation']['reviewer_name']}`。{production_value_sentence}",
        "",
        f"本报告锁定的推荐 Agent 是：`{lock['production_value_recommendation']['reviewer_name']}`。",
        "",
        "## 5. 我们用未参与选择的留出检查任务检查推荐是否仍合理",
        "",
        f"留出检查结论：{holdout_verdict_label}（`{holdout_check['holdout_verdict']}`）。",
        "",
        *markdown_table(holdout_rows, [("Agent", "Agent"), ("留出检查通过率", "Solve"), ("每解出一题成本", "Cost/Solved"), ("中位延迟秒", "Latency")]),
        "",
        "## 6. 成本、延迟和失败类型",
        "",
        f"估算总成本：`${cost_latency['total_estimated_cost_usd']}`。其中冒烟 `${cost_latency['smoke_estimated_cost_usd']}`，选择集 `${cost_latency['selection_estimated_cost_usd']}`，留出检查 `${cost_latency['holdout_estimated_cost_usd']}`。",
        "",
        f"可解析 token usage 的运行数：`{cost_latency['usage_observed_count']}`。没有 usage 的运行使用预先声明的保守单次估算，报告中不把它说成真实账单。",
        "",
        "选择集失败类型：",
        "",
        *[f"- `{category}`: `{count}`" for category, count in selection["failure_category_counts"].items()],
        "",
        "留出检查失败类型：",
        "",
        *[f"- `{category}`: `{count}`" for category, count in holdout["failure_category_counts"].items()],
        "",
        "## 7. 这个结果能说明什么，不能说明什么",
        "",
        "可以讲：在这个目标仓库、这批任务和这些候选 Agent 中，系统能端到端比较完整 Coding Agent，捕获代码改动，在干净目录验证，并把质量、成本、延迟和失败原因放在一张决策表里。",
        "",
        "不能讲：这不是跨仓库结论，不证明某个模型家族普遍更好，也不证明任务选择方法已经具备长期预测有效性。这个 demo 只支持一次目标仓库选型决策的可执行流程和本次候选集内的观察结果。",
        "",
        "## 8. 下一步建议",
        "",
        "- 扩大到第二个目标仓库，验证推荐规则是否仍稳定。",
        "- 对推荐 Agent 和最接近竞争者做重复运行，估计随机性和失败可复现性。",
        "- 接入真实账单成本，替代保守单次运行估算。",
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
    for name in ["smoke", "selection", "holdout", TOP2_REPEAT_STAGE]:
        run_parser = subcommands.add_parser(name)
        run_parser.add_argument("--agent", action="append", default=None)
        run_parser.add_argument("--rerun", action="store_true")
    recover_parser = subcommands.add_parser("recover-stage")
    recover_parser.add_argument("stage", choices=["smoke", "selection", "holdout", TOP2_REPEAT_STAGE])
    recover_parser.add_argument("--agent", action="append", default=None)
    subcommands.add_parser("recommend")
    subcommands.add_parser("report")
    subcommands.add_parser("top2-repeat-report")
    subcommands.add_parser("refresh-sanitized-stage-metadata")
    args = parser.parse_args()
    config = load_config(repo_path(args.config))
    if args.command == "gate":
        payload = gate(config, replay_sample_count=args.replay_sample_count)
        return 0 if payload["status"] == "ready" else 2
    if args.command in {"smoke", "selection", "holdout", TOP2_REPEAT_STAGE}:
        metrics = run_stage(config, args.command, agent_ids=args.agent, rerun=args.rerun)
        min_rate = (
            float(config["run_policy"]["smoke_scoreable_cell_rate_min"])
            if args.command == "smoke"
            else float(config["run_policy"]["main_scoreable_cell_rate_min"])
        )
        rate = metrics["scoreable_cell_rate"] or 0.0
        return 0 if rate >= min_rate else 2
    if args.command == "recover-stage":
        recover_stage(config, args.stage, agent_ids=args.agent)
        return 0
    if args.command == "recommend":
        recommend(config)
        return 0
    if args.command == "report":
        final_report(config)
        return 0
    if args.command == "top2-repeat-report":
        top2_repeatability_report(config)
        return 0
    if args.command == "refresh-sanitized-stage-metadata":
        for stage in ["smoke", "selection", "holdout", TOP2_REPEAT_STAGE]:
            paths = stage_paths(stage)
            if not paths["submissions"].exists():
                continue
            metrics_path = paths["metrics"]
            expected = read_json(metrics_path).get("scheduled_cells", 0) if metrics_path.exists() else len(read_jsonl(paths["submissions"]))
            persist_stage_outputs(stage, read_jsonl(paths["submissions"]), read_jsonl(paths["verifiers"]), read_jsonl(paths["cost"]), int(expected))
        return 0
    raise ValueError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
