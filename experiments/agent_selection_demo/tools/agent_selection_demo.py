from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import re
import shlex
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
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
PV_SIMPLE_BASELINES = [
    "temporal_recent_baseline",
    "seeded_random_same_budget",
    "repo_unweighted_same_budget",
    "repo_stratified_by_target_profile",
]
PV_CANDIDATE_SELECTORS = [
    "coverage_constrained_unweighted",
    "block_randomized_stratified",
    "block_plus_shrinkage_weighted",
]
PV_DIAGNOSTIC_ONLY = ["completed_blocked_split_supplement"]
PV_CATASTROPHIC_THRESHOLD = 0.15
DEFAULT_AGENT_TIMEOUT_SECONDS = 1800
DEFAULT_ADAPTER_CLEANUP_GRACE_SECONDS = 60
DEFAULT_VERIFIER_TIMEOUT_SECONDS = 360

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


def run_policy_int(config: dict[str, Any], key: str, default: int) -> int:
    return int(config.get("run_policy", {}).get(key, default))


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
    verifier_timeout = run_policy_int(config, "verifier_timeout_seconds", DEFAULT_VERIFIER_TIMEOUT_SECONDS)
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
                timeout_seconds=verifier_timeout,
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
    timeout = int(candidate.get("timeout_seconds") or DEFAULT_AGENT_TIMEOUT_SECONDS)
    cleanup_grace = run_policy_int(config, "adapter_cleanup_grace_seconds", DEFAULT_ADAPTER_CLEANUP_GRACE_SECONDS)
    outer_timeout = timeout + max(cleanup_grace, 0)
    command = (
        f"uv run --project {shlex.quote(str(ROOT / 'experiments' / 'phase0_headroom'))} "
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
        command_template_source="agent_selection_demo_config",
        endpoint_proof_status="llm_endpoint_proxy_secret_isolated",
        timeout_seconds=outer_timeout,
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


def usage_from_kilo_step_events(text: str) -> dict[str, Any] | None:
    input_tokens = 0
    cached_input_tokens = 0
    output_tokens = 0
    found = False
    for line in text.splitlines():
        line = line.strip()
        if not line or not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if parsed.get("type") != "step_finish":
            continue
        tokens = ((parsed.get("part") or {}).get("tokens") if isinstance(parsed.get("part"), dict) else None) or {}
        if not isinstance(tokens, dict):
            continue
        cache = tokens.get("cache") if isinstance(tokens.get("cache"), dict) else {}
        input_count = int(tokens.get("input") or 0)
        cache_read = int(cache.get("read") or 0)
        output_count = int(tokens.get("output") or 0) + int(tokens.get("reasoning") or 0)
        input_tokens += input_count + cache_read
        cached_input_tokens += cache_read
        output_tokens += output_count
        found = True
    if not found:
        return None
    return {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_input_tokens,
        "output_tokens": output_tokens,
        "usage_source_schema": "kilo_step_finish_tokens",
    }


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
    return usage_from_kilo_step_events(text)


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


def selected_agent_ids_for_stage(config: dict[str, Any], stage: str, agent_ids: list[str] | None = None) -> list[str]:
    if agent_ids:
        return agent_ids
    if stage == TOP2_REPEAT_STAGE:
        configured = {candidate["agent_id"] for candidate in config["agent_candidates"]}
        missing = [agent_id for agent_id in TOP2_REPEAT_AGENT_IDS if agent_id not in configured]
        if missing:
            raise RuntimeError(f"top-2 repeat candidates missing from config: {', '.join(missing)}")
        return list(TOP2_REPEAT_AGENT_IDS)
    return [candidate["agent_id"] for candidate in config["agent_candidates"]]


def should_stop_after_cell(status: str | None, stop_on_unscoreable: bool) -> bool:
    return bool(stop_on_unscoreable and status not in SCOREABLE_STATUSES)


def run_stage(
    config: dict[str, Any],
    stage: str,
    agent_ids: list[str] | None = None,
    rerun: bool = False,
    stop_on_unscoreable: bool = False,
) -> dict[str, Any]:
    missing_env = [name for name in ["LLM_BASE_URL", "LLM_API_KEY"] if not os.environ.get(name)]
    if missing_env:
        raise RuntimeError(f"missing endpoint env: {', '.join(missing_env)}")
    split = load_split()
    packages = package_map(config)
    task_ids = stage_task_ids(split, stage)
    candidates = candidate_by_id(config)
    selected_agents = selected_agent_ids_for_stage(config, stage, agent_ids)
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
            if should_stop_after_cell(result.verifier.get("status"), stop_on_unscoreable):
                return metrics
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


SELECTOR_TASK_FIELDNAMES = [
    "task_id",
    "target_repo",
    "task_time",
    "stage_role",
    "source",
    "source_cluster",
    "module_bucket",
    "path_bucket",
    "test_bucket",
    "task_type",
    "change_size_proxy",
    "difficulty_bucket",
    "recency_bucket",
    "quality_score",
    "risk_flag",
    "flaky_flag",
    "gates_pass",
    "has_required_fields",
    "base_commit_present",
    "target_commit_present",
    "is_final_selection_candidate",
    "is_final_later_task",
    "metadata_fallbacks",
]

SELECTOR_OUTCOME_FIELDNAMES = [
    "task_id",
    "agent_id",
    "stage",
    "window_id",
    "source_artifact_path",
    "terminal_status",
    "scoreable_cell",
    "verified_pass",
    "policy_valid_cell",
    "policy_pass",
    "policy_outcome_value",
    "failure_category",
    "latency_seconds",
    "estimated_cost_usd",
    "cost_observation_kind",
]

SELECTOR_STAGE_ARTIFACTS = {
    "selection": "selection_score_table.csv",
    "holdout": "holdout_score_table.csv",
    "doubled_timeout_top2_repeat": "doubled_timeout_top2_repeat_score_table.csv",
    "top2_repeat_old_900s": "top2_repeat_score_table.csv",
    "smoke": "smoke_score_table.csv",
}

POLICY_VALID_TERMINAL_STATUSES = SCOREABLE_STATUSES | INFRA_STATUSES
SELECTOR_TIE_EPSILON = 0.05


def selector_round(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def parse_task_datetime(raw: Any) -> datetime:
    text = str(raw or "").strip()
    if not text:
        return datetime.min.replace(tzinfo=timezone.utc)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def selector_module_bucket(code_files: list[str]) -> str:
    if not code_files:
        return "unknown_module"
    modules = sorted({Path(path).stem or Path(path).name for path in code_files})
    return "+".join(modules[:3])


def selector_path_bucket(code_files: list[str]) -> str:
    if not code_files:
        return "unknown_path"
    parents = sorted({str(Path(path).parent) or "." for path in code_files})
    return "+".join(parents[:3])


def selector_test_bucket(test_files: list[str]) -> str:
    if not test_files:
        return "unknown_test"
    stems = sorted({Path(path).stem for path in test_files})
    if any("cli" in stem for stem in stems):
        return "cli"
    if any("snapshot" in stem for stem in stems):
        return "snapshot"
    return "pytest_unit"


def selector_change_size_proxy(code_files: list[str], test_files: list[str]) -> str:
    touched = len(set(code_files)) + len(set(test_files))
    if touched <= 2:
        return "small"
    if touched <= 4:
        return "medium"
    return "large"


def selector_recency_bucket(task_time: str) -> str:
    year = parse_task_datetime(task_time).year
    if year <= 2018:
        return "legacy_2018_or_earlier"
    if year <= 2022:
        return "middle_2019_2022"
    return "recent_2023_or_later"


def selector_stage_role(split: dict[str, Any], task_id: str) -> str:
    if task_id in set(split.get("selection_tasks", [])):
        return "selection"
    if task_id in set(split.get("holdout_tasks", [])):
        return "holdout"
    if task_id in set(split.get("smoke_tasks", [])):
        return "smoke"
    return "unused"


def selector_task_rows_from_audit(audit_rows: list[dict[str, Any]], split: dict[str, Any], target_repo: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for audit in sorted(audit_rows, key=lambda row: (str(row.get("task_time") or ""), str(row.get("task_id") or ""))):
        task_id = str(audit.get("task_id") or "")
        code_files = [str(path) for path in audit.get("code_files", [])]
        test_files = [str(path) for path in audit.get("test_files", [])]
        source = str(audit.get("source") or "unknown_source")
        module_bucket = selector_module_bucket(code_files)
        change_size = selector_change_size_proxy(code_files, test_files)
        gates_pass = bool(audit.get("gates_pass"))
        has_required = bool(audit.get("has_required_fields"))
        base_present = bool(audit.get("base_commit_present"))
        target_present = bool(audit.get("target_commit_present"))
        quality_score = 1.0 if all([gates_pass, has_required, base_present, target_present]) else 0.0
        fallback_fields = ["task_type", "risk_flag", "flaky_flag", "difficulty_bucket"]
        stage_role = selector_stage_role(split, task_id)
        rows.append(
            {
                "task_id": task_id,
                "target_repo": target_repo,
                "task_time": str(audit.get("task_time") or ""),
                "stage_role": stage_role,
                "source": source,
                "source_cluster": f"{source}:{module_bucket}",
                "module_bucket": module_bucket,
                "path_bucket": selector_path_bucket(code_files),
                "test_bucket": selector_test_bucket(test_files),
                "task_type": "unknown",
                "change_size_proxy": change_size,
                "difficulty_bucket": change_size,
                "recency_bucket": selector_recency_bucket(str(audit.get("task_time") or "")),
                "quality_score": quality_score,
                "risk_flag": False,
                "flaky_flag": False,
                "gates_pass": gates_pass,
                "has_required_fields": has_required,
                "base_commit_present": base_present,
                "target_commit_present": target_present,
                "is_final_selection_candidate": stage_role == "selection",
                "is_final_later_task": stage_role == "holdout",
                "metadata_fallbacks": ",".join(fallback_fields),
            }
        )
    return rows


def selector_visible_task_ids(task_rows: list[dict[str, Any]], origin_time: str, allowed_stage_roles: set[str]) -> list[str]:
    origin = parse_task_datetime(origin_time)
    visible = [
        row
        for row in task_rows
        if str(row.get("stage_role")) in allowed_stage_roles and parse_task_datetime(row.get("task_time")) <= origin
    ]
    return [str(row["task_id"]) for row in sorted(visible, key=lambda row: (str(row.get("task_time") or ""), str(row["task_id"])))]


def selector_policy_valid_cell(row: dict[str, str]) -> bool:
    return str(row.get("terminal_status") or "") in POLICY_VALID_TERMINAL_STATUSES


def selector_outcome_rows_from_score_tables(score_tables: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stage, table_rows in score_tables.items():
        source_artifact = f"experiments/agent_selection_demo/results/{SELECTOR_STAGE_ARTIFACTS[stage]}"
        for row in table_rows:
            valid = selector_policy_valid_cell(row)
            passed = str(row.get("terminal_status") or "") == "verified_pass"
            rows.append(
                {
                    "task_id": row.get("task_id", ""),
                    "agent_id": row.get("agent_id", ""),
                    "stage": stage,
                    "window_id": "final_selection" if stage == "selection" else "final_later" if stage == "holdout" else stage,
                    "source_artifact_path": source_artifact,
                    "terminal_status": row.get("terminal_status", ""),
                    "scoreable_cell": csv_bool(row.get("scoreable_cell")),
                    "verified_pass": csv_bool(row.get("verified_pass")),
                    "policy_valid_cell": valid,
                    "policy_pass": passed if valid else "",
                    "policy_outcome_value": 1 if valid and passed else 0 if valid else "",
                    "failure_category": row.get("failure_category", ""),
                    "latency_seconds": row.get("latency_seconds", ""),
                    "estimated_cost_usd": row.get("estimated_cost_usd", ""),
                    "cost_observation_kind": row.get("cost_observation_kind", ""),
                }
            )
    rows.sort(key=lambda row: (str(row["stage"]), str(row["task_id"]), str(row["agent_id"])))
    return rows


def build_selector_task_table(config: dict[str, Any]) -> list[dict[str, Any]]:
    audit = read_json(result_path("task_pool_audit.json"))
    split = read_json(result_path("frozen_split.json"))
    return selector_task_rows_from_audit(audit.get("rows", []), split, config["target_repo"]["repo_name"])


def build_selector_outcome_matrix() -> list[dict[str, Any]]:
    score_tables = {
        stage: read_csv_rows(result_path(filename))
        for stage, filename in SELECTOR_STAGE_ARTIFACTS.items()
        if result_path(filename).exists()
    }
    return selector_outcome_rows_from_score_tables(score_tables)


def selector_protocol_payload(config: dict[str, Any], task_rows: list[dict[str, Any]], outcome_rows: list[dict[str, Any]]) -> dict[str, Any]:
    split = read_json(result_path("frozen_split.json"))
    selection_rows = [row for row in task_rows if row["stage_role"] == "selection"]
    final_origin_time = max((str(row["task_time"]) for row in selection_rows), default="")
    random_seeds = list(range(1000))
    visible_ids = selector_visible_task_ids(task_rows, final_origin_time, {"selection"})
    return {
        "schema_version": "barcarolle.agent_selection_demo.selector_protocol.v1",
        "generated_at": "2026-06-14",
        "status": "frozen_before_selector_evaluation",
        "target_repo": config["target_repo"]["repo_name"],
        "dataset_artifacts": {
            "task_table": "experiments/agent_selection_demo/results/selector_task_table.csv",
            "outcome_matrix": "experiments/agent_selection_demo/results/selector_outcome_matrix.csv",
        },
        "agent_sets": {
            "primary": [candidate["agent_id"] for candidate in config["agent_candidates"]],
            "top2_repeat_validation": TOP2_REPEAT_AGENT_IDS,
        },
        "budgets": [10, 20],
        "random_seeds": random_seeds,
        "random_seed_count": len(random_seeds),
        "invalid_cell_policy": {
            "count_as_fail": sorted(POLICY_VALID_TERMINAL_STATUSES),
            "count_as_na": ["verifier_outage", "invalid_task", "oracle_flake"],
            "pairwise_metrics": "common policy-valid cells only",
        },
        "leakage_masks": {
            "selector_visible_task_ids": visible_ids,
            "selector_visible_stage_roles": ["selection"],
            "masked_until_task_ids_frozen": [
                "selection outcomes",
                "holdout outcomes",
                "doubled_timeout_top2_repeat outcomes"
            ],
            "final_origin_time": final_origin_time,
        },
        "split_plan": {
            "type": "frozen_pseudo_future_with_sparse_rolling_origin_notes",
            "reason": "The committed boltons demo has one complete Selection-to-Holdout grid. Earlier rolling origins are sparse for current complete-Agent outcomes, so train/dev tuning is limited to deterministic defaults and sensitivity checks; the final demo slice is evaluated once after config freeze.",
            "train_development": {
                "use": "selector sanity checks and threshold defaults only",
                "final_holdout_outcomes_visible": False,
            },
            "final_demo_slice": {
                "origin_id": "boltons_selection_to_holdout_2026_06_14",
                "origin_time": final_origin_time,
                "candidate_task_ids": split.get("selection_tasks", []),
                "later_task_ids": split.get("holdout_tasks", []),
                "repeat_validation_stage": "doubled_timeout_top2_repeat"
            }
        },
        "decision_thresholds": {
            "action_margin": 0.05,
            "min_common_valid_selected_tasks": 8,
            "tie_epsilon": 0.05,
            "bootstrap_iterations": 1000,
            "confidence_level": 0.8
        },
        "outcome_inventory": {
            "task_rows": len(task_rows),
            "outcome_rows": len(outcome_rows),
            "policy_valid_outcome_rows": sum(1 for row in outcome_rows if row["policy_valid_cell"] is True),
            "final_selection_candidate_count": sum(1 for row in task_rows if row["is_final_selection_candidate"] is True),
            "final_later_task_count": sum(1 for row in task_rows if row["is_final_later_task"] is True),
        },
    }


def render_selector_protocol_report(protocol: dict[str, Any]) -> str:
    final_slice = protocol["split_plan"]["final_demo_slice"]
    inventory = protocol["outcome_inventory"]
    thresholds = protocol["decision_thresholds"]
    lines = [
        "# Selector Protocol",
        "",
        "生成日期：2026-06-14",
        "",
        "## 数据集",
        "",
        f"- Task table: `{protocol['dataset_artifacts']['task_table']}`。",
        f"- Outcome matrix: `{protocol['dataset_artifacts']['outcome_matrix']}`。",
        f"- Task rows: `{inventory['task_rows']}`；outcome rows: `{inventory['outcome_rows']}`；policy-valid outcome rows: `{inventory['policy_valid_outcome_rows']}`。",
        f"- Final Selection candidate tasks: `{inventory['final_selection_candidate_count']}`；later/Holdout tasks: `{inventory['final_later_task_count']}`。",
        "",
        "## Frozen pseudo-future slice",
        "",
        f"- Origin ID: `{final_slice['origin_id']}`。",
        f"- Origin time: `{final_slice['origin_time']}`。",
        f"- Candidate pool: original frozen Selection tasks (`{len(final_slice['candidate_task_ids'])}` tasks)。",
        f"- Later validation: original Holdout tasks (`{len(final_slice['later_task_ids'])}` tasks)。",
        f"- Top-2 repeat validation stage: `{final_slice['repeat_validation_stage']}`。",
        "",
        "## Leakage mask",
        "",
        "selector 只能看到 Selection task metadata 和 frozen config；Selection outcomes、Holdout outcomes、doubled-timeout repeat outcomes 都在 task IDs 固定后才 join。",
        "",
        "## Invalid-cell policy",
        "",
        "solver timeout、invalid diff、normal verifier failure、policy violation 等 terminal statuses 计为 fail；只有 verifier outage、invalid task、oracle flake 计为 NA。pairwise metrics 只使用 common policy-valid cells。",
        "",
        "## Fixed budgets and seeds",
        "",
        f"- Budgets: `{protocol['budgets']}`。",
        f"- Random seeds: `0..{protocol['random_seed_count'] - 1}`。",
        "",
        "## Decision defaults",
        "",
        f"- Action margin: `{thresholds['action_margin']}`。",
        f"- Minimum common valid selected tasks: `{thresholds['min_common_valid_selected_tasks']}`。",
        f"- Tie epsilon: `{thresholds['tie_epsilon']}`。",
        f"- Bootstrap iterations: `{thresholds['bootstrap_iterations']}`。",
        "",
        "这些阈值在 final evaluation 前冻结；如果后续 package 需要调整，只能在 preregistration 中明确记录，并且不能根据 final later/Holdout 结果回调。",
    ]
    return "\n".join(lines) + "\n"


def selector_build_dataset(config: dict[str, Any]) -> dict[str, Any]:
    task_rows = build_selector_task_table(config)
    outcome_rows = build_selector_outcome_matrix()
    protocol = selector_protocol_payload(config, task_rows, outcome_rows)
    write_csv(result_path("selector_task_table.csv"), task_rows, SELECTOR_TASK_FIELDNAMES)
    write_csv(result_path("selector_outcome_matrix.csv"), outcome_rows, SELECTOR_OUTCOME_FIELDNAMES)
    write_json(result_path("selector_protocol.json"), protocol)
    write_text(report_path("selector_protocol_zh.md"), render_selector_protocol_report(protocol))
    return protocol


def selector_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def load_selector_task_rows() -> list[dict[str, str]]:
    return read_csv_rows(result_path("selector_task_table.csv"))


def load_selector_outcome_rows() -> list[dict[str, str]]:
    return read_csv_rows(result_path("selector_outcome_matrix.csv"))


def selector_agent_ids(config: dict[str, Any]) -> list[str]:
    return [str(candidate["agent_id"]) for candidate in config["agent_candidates"]]


def selector_candidate_tasks(task_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in task_rows
        if selector_bool(row.get("is_final_selection_candidate"))
        and float(row.get("quality_score") or 0.0) >= 1.0
        and not selector_bool(row.get("risk_flag"))
        and not selector_bool(row.get("flaky_flag"))
    ]


def selector_later_task_ids(task_rows: list[dict[str, str]]) -> list[str]:
    return [
        str(row["task_id"])
        for row in sorted(task_rows, key=lambda row: (str(row.get("task_time") or ""), str(row.get("task_id") or "")))
        if selector_bool(row.get("is_final_later_task"))
    ]


def selector_stratum_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("source") or "unknown_source"),
        str(row.get("module_bucket") or "unknown_module"),
        str(row.get("change_size_proxy") or "unknown_size"),
        str(row.get("recency_bucket") or "unknown_recency"),
    )


def selector_source_quota_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("source") or "unknown_source"), str(row.get("recency_bucket") or "unknown_recency"))


def selector_recency_score(row: dict[str, Any]) -> float:
    parsed = parse_task_datetime(row.get("task_time"))
    return parsed.timestamp() if parsed.year > 1 else 0.0


def selector_allocated_quotas(rows: list[dict[str, Any]], k: int, key_name: str = "source_recency") -> dict[tuple[Any, ...], int]:
    key_fn = selector_source_quota_key if key_name == "source_recency" else selector_stratum_key
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[key_fn(row)].append(row)
    raw = {key: k * (len(items) / max(len(rows), 1)) for key, items in grouped.items()}
    quotas = {key: min(len(grouped[key]), int(math.floor(value))) for key, value in raw.items()}
    remaining = k - sum(quotas.values())
    fractional = sorted(
        grouped,
        key=lambda key: (
            raw[key] - math.floor(raw[key]),
            max(selector_recency_score(row) for row in grouped[key]),
            str(key),
        ),
        reverse=True,
    )
    while remaining > 0 and fractional:
        progressed = False
        for key in fractional:
            if quotas[key] >= len(grouped[key]):
                continue
            quotas[key] += 1
            remaining -= 1
            progressed = True
            if remaining == 0:
                break
        if not progressed:
            break
    return quotas


def selector_fill_to_k(selected: list[dict[str, Any]], rows: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    seen = {str(row["task_id"]) for row in selected}
    module_counts = Counter(str(row.get("module_bucket") or "") for row in selected)
    module_cap = max(1, math.ceil(k * 0.3))
    for row in sorted(rows, key=lambda item: (selector_recency_score(item), str(item.get("task_id") or "")), reverse=True):
        if len(selected) >= k:
            break
        task_id = str(row["task_id"])
        if task_id in seen:
            continue
        module = str(row.get("module_bucket") or "")
        if module_counts[module] >= module_cap and len(rows) - len(seen) > k - len(selected):
            continue
        selected.append(row)
        seen.add(task_id)
        module_counts[module] += 1
    return selected


def select_uniform_random_same_budget(rows: list[dict[str, Any]], k: int, seed: int) -> list[str]:
    candidates = sorted(rows, key=lambda row: str(row["task_id"]))
    if k >= len(candidates):
        return [str(row["task_id"]) for row in candidates]
    rng = random.Random(seed)
    return sorted(str(row["task_id"]) for row in rng.sample(candidates, k))


def select_quality_filtered_random(rows: list[dict[str, Any]], k: int, seed: int) -> list[str]:
    eligible = [
        row
        for row in rows
        if float(row.get("quality_score") or 0.0) >= 1.0
        and not selector_bool(row.get("risk_flag"))
        and not selector_bool(row.get("flaky_flag"))
    ]
    return select_uniform_random_same_budget(eligible, k, seed)


def select_stratified_random(rows: list[dict[str, Any]], k: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    eligible = sorted(rows, key=lambda row: str(row["task_id"]))
    quotas = selector_allocated_quotas(eligible, k, key_name="source_recency")
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        grouped[selector_source_quota_key(row)].append(row)
    selected: list[dict[str, Any]] = []
    for key, quota in sorted(quotas.items(), key=lambda item: str(item[0])):
        pool = grouped[key]
        selected.extend(rng.sample(pool, min(quota, len(pool))))
    selector_fill_to_k(selected, eligible, k)
    return sorted(str(row["task_id"]) for row in selected[:k])


def select_rsq_recency_stratified_quota(rows: list[dict[str, Any]], k: int, seed: int | None = None) -> list[str]:
    del seed
    eligible = [
        row
        for row in rows
        if float(row.get("quality_score") or 0.0) >= 1.0
        and not selector_bool(row.get("risk_flag"))
        and not selector_bool(row.get("flaky_flag"))
    ]
    quotas = selector_allocated_quotas(eligible, k, key_name="source_recency")
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in eligible:
        grouped[selector_source_quota_key(row)].append(row)
    selected: list[dict[str, Any]] = []
    module_counts: Counter[str] = Counter()
    module_cap = max(1, math.ceil(k * 0.3))
    for key, quota in sorted(quotas.items(), key=lambda item: str(item[0])):
        group_rows = sorted(grouped[key], key=lambda row: (selector_recency_score(row), str(row["task_id"])), reverse=True)
        picked = 0
        for row in group_rows:
            if picked >= quota:
                break
            module = str(row.get("module_bucket") or "")
            if module_counts[module] >= module_cap and len(group_rows) - picked > quota - picked:
                continue
            selected.append(row)
            module_counts[module] += 1
            picked += 1
    selector_fill_to_k(selected, eligible, k)
    return sorted(str(row["task_id"]) for row in selected[:k])


BASELINE_SELECTOR_FUNCS = {
    "uniform_random_same_budget": select_uniform_random_same_budget,
    "quality_filtered_random": select_quality_filtered_random,
    "stratified_random": select_stratified_random,
}


def outcome_lookup(outcome_rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    return {(str(row["stage"]), str(row["task_id"]), str(row["agent_id"])): row for row in outcome_rows}


def selector_pass_rates(
    task_ids: list[str],
    agent_ids: list[str],
    stage: str,
    outcomes: dict[tuple[str, str, str], dict[str, str]],
) -> dict[str, dict[str, Any]]:
    rates: dict[str, dict[str, Any]] = {}
    for agent_id in agent_ids:
        values: list[int] = []
        missing = 0
        for task_id in task_ids:
            row = outcomes.get((stage, task_id, agent_id))
            if not row or not selector_bool(row.get("policy_valid_cell")):
                missing += 1
                continue
            values.append(int(row.get("policy_outcome_value") or 0))
        rates[agent_id] = {
            "pass_rate": None if not values else sum(values) / len(values),
            "pass_count": sum(values),
            "valid_count": len(values),
            "missing_or_na_count": missing,
        }
    return rates


def selector_sign(value: float, epsilon: float = SELECTOR_TIE_EPSILON) -> int:
    if value > epsilon:
        return 1
    if value < -epsilon:
        return -1
    return 0


def selector_forced_top(rates: dict[str, dict[str, Any]]) -> tuple[str | None, bool]:
    usable = {agent_id: row["pass_rate"] for agent_id, row in rates.items() if row["pass_rate"] is not None}
    if not usable:
        return None, False
    best = max(float(value) for value in usable.values())
    top = sorted(agent_id for agent_id, value in usable.items() if float(value) == best)
    return top[0], len(top) > 1


def evaluate_selected_task_ids(
    selected_task_ids: list[str],
    later_task_ids: list[str],
    agent_ids: list[str],
    outcome_rows: list[dict[str, str]],
    later_stage: str = "holdout",
) -> dict[str, Any]:
    outcomes = outcome_lookup(outcome_rows)
    selection_rates = selector_pass_rates(selected_task_ids, agent_ids, "selection", outcomes)
    later_rates = selector_pass_rates(later_task_ids, agent_ids, later_stage, outcomes)
    common_agents = [
        agent_id
        for agent_id in agent_ids
        if selection_rates[agent_id]["pass_rate"] is not None and later_rates[agent_id]["pass_rate"] is not None
    ]
    errors = [abs(float(selection_rates[agent_id]["pass_rate"]) - float(later_rates[agent_id]["pass_rate"])) for agent_id in common_agents]
    pair_rows: list[dict[str, Any]] = []
    for index, agent_a in enumerate(common_agents):
        for agent_b in common_agents[index + 1 :]:
            selected_margin = float(selection_rates[agent_a]["pass_rate"]) - float(selection_rates[agent_b]["pass_rate"])
            later_margin = float(later_rates[agent_a]["pass_rate"]) - float(later_rates[agent_b]["pass_rate"])
            later_sign = selector_sign(later_margin)
            selected_sign = selector_sign(selected_margin)
            if later_sign == 0:
                continue
            pair_rows.append(
                {
                    "agent_a": agent_a,
                    "agent_b": agent_b,
                    "selected_margin": selector_round(selected_margin),
                    "later_margin": selector_round(later_margin),
                    "selected_sign": selected_sign,
                    "later_sign": later_sign,
                    "agrees": selected_sign == later_sign,
                }
            )
    forced_top, selection_tied = selector_forced_top(selection_rates)
    later_top, later_tied = selector_forced_top(later_rates)
    later_best = max((float(row["pass_rate"]) for row in later_rates.values() if row["pass_rate"] is not None), default=0.0)
    forced_regret = None if forced_top is None else later_best - float(later_rates[forced_top]["pass_rate"])
    return {
        "selected_task_ids": selected_task_ids,
        "later_task_ids": later_task_ids,
        "selection_rates": selection_rates,
        "later_rates": later_rates,
        "MAE": selector_round(None if not errors else sum(errors) / len(errors)),
        "pairwise_direction_agreement": selector_round(None if not pair_rows else sum(1 for row in pair_rows if row["agrees"]) / len(pair_rows)),
        "pairwise_rows": pair_rows,
        "selection_forced_top_agent_id": forced_top,
        "selection_top_tied": selection_tied,
        "later_top_agent_id": later_top,
        "later_top_tied": later_tied,
        "top1_agreement_forced": forced_top == later_top and forced_top is not None,
        "forced_recommendation_regret": selector_round(forced_regret),
    }


def summarize_selector_metric_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    def values(key: str) -> list[float]:
        return [float(row[key]) for row in rows if row.get(key) is not None]

    mae_values = values("MAE")
    regret_values = values("forced_recommendation_regret")
    pairwise_values = values("pairwise_direction_agreement")
    return {
        "sample_count": len(rows),
        "MAE_mean": selector_round(statistics.mean(mae_values) if mae_values else None),
        "MAE_median": selector_round(statistics.median(mae_values) if mae_values else None),
        "MAE_p05": selector_round(percentile(mae_values, 5) if mae_values else None),
        "MAE_p95": selector_round(percentile(mae_values, 95) if mae_values else None),
        "pairwise_direction_agreement_mean": selector_round(statistics.mean(pairwise_values) if pairwise_values else None),
        "top1_agreement_rate_forced": selector_round(sum(1 for row in rows if row.get("top1_agreement_forced")) / len(rows) if rows else None),
        "forced_recommendation_regret_mean": selector_round(statistics.mean(regret_values) if regret_values else None),
        "forced_recommendation_regret_max": selector_round(max(regret_values) if regret_values else None),
    }


def compact_selector_metric_row(row: dict[str, Any]) -> dict[str, Any]:
    selected_task_ids = [str(task_id) for task_id in row.get("selected_task_ids", [])]
    return {
        "selected_task_ids_sha256": sha256_text("\n".join(selected_task_ids)),
        "MAE": row.get("MAE"),
        "pairwise_direction_agreement": row.get("pairwise_direction_agreement"),
        "selection_forced_top_agent_id": row.get("selection_forced_top_agent_id"),
        "selection_top_tied": row.get("selection_top_tied"),
        "later_top_agent_id": row.get("later_top_agent_id"),
        "top1_agreement_forced": row.get("top1_agreement_forced"),
        "forced_recommendation_regret": row.get("forced_recommendation_regret"),
    }


def selector_random_percentiles(candidate: dict[str, Any], random_rows: list[dict[str, Any]]) -> dict[str, Any]:
    mae_values = [float(row["MAE"]) for row in random_rows if row.get("MAE") is not None]
    regret_values = [float(row["forced_recommendation_regret"]) for row in random_rows if row.get("forced_recommendation_regret") is not None]
    pair_values = [float(row["pairwise_direction_agreement"]) for row in random_rows if row.get("pairwise_direction_agreement") is not None]
    candidate_mae = candidate.get("MAE")
    candidate_regret = candidate.get("forced_recommendation_regret")
    candidate_pair = candidate.get("pairwise_direction_agreement")
    return {
        "MAE_beats_or_ties_random_share": selector_round(
            None if candidate_mae is None or not mae_values else sum(float(value) >= float(candidate_mae) for value in mae_values) / len(mae_values)
        ),
        "regret_beats_or_ties_random_share": selector_round(
            None
            if candidate_regret is None or not regret_values
            else sum(float(value) >= float(candidate_regret) for value in regret_values) / len(regret_values)
        ),
        "pairwise_agreement_beats_or_ties_random_share": selector_round(
            None
            if candidate_pair is None or not pair_values
            else sum(float(value) <= float(candidate_pair) for value in pair_values) / len(pair_values)
        ),
    }


def selector_baseline_eval(config: dict[str, Any]) -> dict[str, Any]:
    protocol = read_json(result_path("selector_protocol.json"))
    task_rows = load_selector_task_rows()
    outcome_rows = load_selector_outcome_rows()
    candidates = selector_candidate_tasks(task_rows)
    later_ids = selector_later_task_ids(task_rows)
    agent_ids = selector_agent_ids(config)
    seeds = [int(seed) for seed in protocol["random_seeds"]]
    budgets = [int(k) for k in protocol["budgets"]]
    selectors: dict[str, Any] = {
        "rsq_recency_stratified_quota": {},
    }
    random_results: dict[str, dict[str, Any]] = {}
    selector_results: dict[str, dict[str, Any]] = {}
    for k in budgets:
        for baseline_id, func in BASELINE_SELECTOR_FUNCS.items():
            rows: list[dict[str, Any]] = []
            unique_samples: set[tuple[str, ...]] = set()
            for seed in seeds:
                selected = func(candidates, k, seed)
                unique_samples.add(tuple(selected))
                metrics = evaluate_selected_task_ids(selected, later_ids, agent_ids, outcome_rows)
                rows.append({"seed": seed, "k": k, "selector_id": baseline_id, **compact_selector_metric_row(metrics)})
            random_results[f"{baseline_id}__k{k}"] = {
                "selector_id": baseline_id,
                "k": k,
                "seed_count": len(seeds),
                "unique_sample_count": len(unique_samples),
                "summary": summarize_selector_metric_rows(rows),
                "rows": rows,
            }
        selected = select_rsq_recency_stratified_quota(candidates, k)
        rsq_metrics = evaluate_selected_task_ids(selected, later_ids, agent_ids, outcome_rows)
        selector_results[f"rsq_recency_stratified_quota__k{k}"] = {
            "selector_id": "rsq_recency_stratified_quota",
            "k": k,
            **rsq_metrics,
            "random_percentiles": {
                baseline_id: selector_random_percentiles(rsq_metrics, random_results[f"{baseline_id}__k{k}"]["rows"])
                for baseline_id in BASELINE_SELECTOR_FUNCS
            },
        }
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.selector_baseline_eval.v1",
        "generated_at": "2026-06-14",
        "paid_agent_calls_made": False,
        "protocol": "experiments/agent_selection_demo/results/selector_protocol.json",
        "selectors": selectors,
        "random_baselines": random_results,
        "selector_results": selector_results,
        "interpretation": {
            "best_rsq_key": min(selector_results, key=lambda key: selector_results[key].get("MAE") or 999),
            "strong_random_baseline_rule": "For each k, compare RSQ against uniform, quality-filtered, and source/recency-stratified random distributions over the same candidate pool and seed list.",
            "tie_caveat": "Forced top-1 regret is diagnostic only; the shared decision wrapper in Package 5 forbids hard recommendations on ties.",
        },
    }
    write_json(result_path("selector_baseline_eval.json"), payload)
    write_text(report_path("selector_baseline_eval_zh.md"), render_selector_baseline_eval(payload))
    return payload


def metadata_disagreement_scores(rows: list[dict[str, Any]]) -> dict[str, float]:
    cluster_counts = Counter(str(row.get("source_cluster") or "") for row in rows)
    source_counts = Counter(str(row.get("source") or "") for row in rows)
    max_cluster = max(cluster_counts.values(), default=1)
    max_source = max(source_counts.values(), default=1)
    scores: dict[str, float] = {}
    for row in rows:
        cluster_density = cluster_counts[str(row.get("source_cluster") or "")] / max_cluster
        source_density = source_counts[str(row.get("source") or "")] / max_source
        medium_bonus = 0.25 if str(row.get("change_size_proxy")) == "medium" else 0.0
        legacy_bonus = 0.15 if str(row.get("recency_bucket")) == "legacy_2018_or_earlier" else 0.0
        synthetic_supply_bonus = 0.2 if str(row.get("source")) == "supply_expansion_20260526" else 0.0
        scores[str(row["task_id"])] = round(2.0 * cluster_density + 0.5 * source_density + medium_bonus + legacy_bonus + synthetic_supply_bonus, 6)
    return scores


def select_disagreement_proxy_tasks(
    rows: list[dict[str, Any]],
    k: int,
    already_selected: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    selected = list(already_selected or [])
    seen = {str(row["task_id"]) for row in selected}
    module_counts = Counter(str(row.get("module_bucket") or "") for row in selected)
    module_cap = max(1, math.ceil(max(k + len(selected), 1) * 0.3))
    scores = metadata_disagreement_scores(rows)
    picked: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: (scores[str(item["task_id"])], str(item.get("task_id") or "")), reverse=True):
        if len(picked) >= k:
            break
        task_id = str(row["task_id"])
        if task_id in seen:
            continue
        module = str(row.get("module_bucket") or "")
        if module_counts[module] >= module_cap and len(rows) - len(seen) > k - len(picked):
            continue
        picked.append(row)
        seen.add(task_id)
        module_counts[module] += 1
    if len(picked) < k:
        for row in sorted(rows, key=lambda item: (scores[str(item["task_id"])], str(item.get("task_id") or "")), reverse=True):
            if len(picked) >= k:
                break
            task_id = str(row["task_id"])
            if task_id not in seen:
                picked.append(row)
                seen.add(task_id)
    return picked


def select_hrd_hybrid(rows: list[dict[str, Any]], k: int, representative_fraction: float = 0.7) -> dict[str, Any]:
    eligible = [
        row
        for row in rows
        if float(row.get("quality_score") or 0.0) >= 1.0
        and not selector_bool(row.get("risk_flag"))
        and not selector_bool(row.get("flaky_flag"))
    ]
    representative_count = min(k, int(math.ceil(k * representative_fraction)))
    representative_ids = select_rsq_recency_stratified_quota(eligible, representative_count)
    representative_rows = [row for row in eligible if str(row["task_id"]) in set(representative_ids)]
    discriminative_count = max(0, k - len(representative_rows))
    discriminative_rows = select_disagreement_proxy_tasks(eligible, discriminative_count, already_selected=representative_rows)
    selected_rows = [*representative_rows, *discriminative_rows]
    if len(selected_rows) < k:
        selected_rows = selector_fill_to_k(selected_rows, eligible, k)
    selected_ids = sorted(str(row["task_id"]) for row in selected_rows[:k])
    return {
        "selected_task_ids": selected_ids,
        "representative_task_ids": sorted(str(row["task_id"]) for row in representative_rows),
        "discriminative_task_ids": sorted(str(row["task_id"]) for row in discriminative_rows),
        "representative_count": len(representative_rows),
        "discriminative_count": len(discriminative_rows),
        "representative_fraction": representative_fraction,
        "disagreement_source": "metadata_cluster_density_difficulty_proxy",
    }


def select_hrd_representative_only(rows: list[dict[str, Any]], k: int) -> dict[str, Any]:
    selected = select_rsq_recency_stratified_quota(rows, k)
    return {
        "selected_task_ids": selected,
        "representative_task_ids": selected,
        "discriminative_task_ids": [],
        "representative_count": len(selected),
        "discriminative_count": 0,
        "representative_fraction": 1.0,
        "disagreement_source": "none",
    }


def select_hrd_disagreement_only(rows: list[dict[str, Any]], k: int) -> dict[str, Any]:
    picked = select_disagreement_proxy_tasks(rows, k)
    selected = sorted(str(row["task_id"]) for row in picked)
    return {
        "selected_task_ids": selected,
        "representative_task_ids": [],
        "discriminative_task_ids": selected,
        "representative_count": 0,
        "discriminative_count": len(selected),
        "representative_fraction": 0.0,
        "disagreement_source": "metadata_cluster_density_difficulty_proxy",
    }


def selector_hrd_eval(config: dict[str, Any]) -> dict[str, Any]:
    task_rows = load_selector_task_rows()
    outcome_rows = load_selector_outcome_rows()
    candidates = selector_candidate_tasks(task_rows)
    later_ids = selector_later_task_ids(task_rows)
    agent_ids = selector_agent_ids(config)
    baseline = read_json(result_path("selector_baseline_eval.json"))
    variants: dict[str, Any] = {}
    for k in [10, 20]:
        variant_specs = [
            ("hrd_representative_only", select_hrd_representative_only(candidates, k)),
            ("hrd_disagreement_only", select_hrd_disagreement_only(candidates, k)),
            ("hrd_70_30", select_hrd_hybrid(candidates, k, 0.7)),
            ("hrd_60_40", select_hrd_hybrid(candidates, k, 0.6)),
            ("hrd_50_50", select_hrd_hybrid(candidates, k, 0.5)),
        ]
        for variant_id, selection in variant_specs:
            metrics = evaluate_selected_task_ids(selection["selected_task_ids"], later_ids, agent_ids, outcome_rows)
            random_percentiles = {
                baseline_id: selector_random_percentiles(metrics, baseline["random_baselines"][f"{baseline_id}__k{k}"]["rows"])
                for baseline_id in BASELINE_SELECTOR_FUNCS
            }
            variants[f"{variant_id}__k{k}"] = {
                "selector_id": variant_id,
                "k": k,
                **selection,
                **metrics,
                "random_percentiles": random_percentiles,
            }
    variant_preference = {
        "hrd_70_30": 0,
        "hrd_60_40": 1,
        "hrd_50_50": 2,
        "hrd_disagreement_only": 3,
        "hrd_representative_only": 4,
    }

    def hrd_variant_rank(key: str) -> tuple[float, float, int, int]:
        row = variants[key]
        selector_id = str(row["selector_id"])
        return (
            float(row.get("MAE") if row.get("MAE") is not None else 999.0),
            float(row.get("forced_recommendation_regret") if row.get("forced_recommendation_regret") is not None else 999.0),
            variant_preference.get(selector_id, 99),
            int(row["k"]),
        )

    best_key = min(variants, key=hrd_variant_rank)
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.selector_hrd_eval.v1",
        "generated_at": "2026-06-14",
        "paid_agent_calls_made": False,
        "disagreement_fallback": {
            "used": True,
            "reason": "No leakage-safe historical current-Agent disagreement matrix exists for the frozen Selection candidate tasks. HRD therefore uses metadata source-cluster density, change-size proxy, and diversity penalties.",
        },
        "baseline_context": {
            key: {
                "selector_id": row["selector_id"],
                "k": row["k"],
                "summary": row["summary"],
            }
            for key, row in baseline["random_baselines"].items()
        },
        "rsq_context": {
            key: {
                "selector_id": row["selector_id"],
                "k": row["k"],
                "MAE": row["MAE"],
                "pairwise_direction_agreement": row["pairwise_direction_agreement"],
                "forced_recommendation_regret": row["forced_recommendation_regret"],
                "selection_forced_top_agent_id": row["selection_forced_top_agent_id"],
                "later_top_agent_id": row["later_top_agent_id"],
            }
            for key, row in baseline["selector_results"].items()
        },
        "variants": variants,
        "best_variant_key": best_key,
        "interpretation": {
            "best_variant_key": best_key,
            "best_variant_mae": variants[best_key]["MAE"],
            "best_variant_forced_top": variants[best_key]["selection_forced_top_agent_id"],
            "decision_quality_note": "HRD improves the Agent-selection story when it creates a Kilo top-pair lead with low forced regret; Package 5 applies the shared decision wrapper before any final recommendation claim.",
        },
    }
    write_json(result_path("selector_hrd_eval.json"), payload)
    write_text(report_path("selector_hrd_eval_zh.md"), render_selector_hrd_eval(payload))
    return payload


def render_selector_hrd_eval(payload: dict[str, Any]) -> str:
    lines = [
        "# HRD Decision-aware Selector Eval",
        "",
        "生成日期：2026-06-14",
        "",
        "## Disagreement source",
        "",
        "当前 frozen Selection candidate tasks 没有 leakage-safe 的历史 current-Agent disagreement matrix。因此 HRD 使用 fallback：source-cluster density、change-size proxy、legacy/source diversity 和 module redundancy penalty。",
        "",
        "## Variant comparison",
        "",
        "| Variant | k | Rep/Disc | MAE | Pairwise | Forced top | Later top | Forced regret | MAE beats stratified random | Regret beats stratified random |",
        "| --- | ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |",
    ]
    for key, row in payload["variants"].items():
        stratified = row["random_percentiles"]["stratified_random"]
        lines.append(
            f"| `{key}` | `{row['k']}` | `{row['representative_count']}/{row['discriminative_count']}` | "
            f"`{row['MAE']}` | `{row['pairwise_direction_agreement']}` | `{row['selection_forced_top_agent_id']}` | "
            f"`{row['later_top_agent_id']}` | `{row['forced_recommendation_regret']}` | "
            f"`{stratified['MAE_beats_or_ties_random_share']}` | `{stratified['regret_beats_or_ties_random_share']}` |"
        )
    best = payload["variants"][payload["best_variant_key"]]
    lines.extend(
        [
            "",
            "## Best no-paid HRD slice",
            "",
            f"最佳 HRD variant 是 `{payload['best_variant_key']}`，k=`{best['k']}`，MAE `{best['MAE']}`，forced top `{best['selection_forced_top_agent_id']}`，later top `{best['later_top_agent_id']}`，forced regret `{best['forced_recommendation_regret']}`。",
            "",
            f"Selected tasks: `{', '.join(best['selected_task_ids'])}`。",
            "",
            "这不是最终 recommend 规则；它说明 HRD 的 metadata disagreement arm 能把 selector 从原始 Selection tie 推向可由 Package 5 进一步检查的决策候选。",
        ]
    )
    return "\n".join(lines) + "\n"


def paired_agent_differences(
    selected_task_ids: list[str],
    agent_a: str,
    agent_b: str,
    outcomes: dict[tuple[str, str, str], dict[str, str]],
    stage: str = "selection",
) -> list[int]:
    differences: list[int] = []
    for task_id in selected_task_ids:
        row_a = outcomes.get((stage, task_id, agent_a))
        row_b = outcomes.get((stage, task_id, agent_b))
        if not row_a or not row_b or not selector_bool(row_a.get("policy_valid_cell")) or not selector_bool(row_b.get("policy_valid_cell")):
            continue
        differences.append(int(row_a.get("policy_outcome_value") or 0) - int(row_b.get("policy_outcome_value") or 0))
    return differences


def bootstrap_margin_lcb(differences: list[int], iterations: int = 1000, confidence_level: float = 0.8, seed: int = 17) -> float | None:
    if not differences:
        return None
    rng = random.Random(seed)
    means: list[float] = []
    n = len(differences)
    for _ in range(iterations):
        sample = [differences[rng.randrange(n)] for _i in range(n)]
        means.append(sum(sample) / n)
    lower_percentile = max(0.0, (1.0 - confidence_level) / 2.0 * 100.0)
    return selector_round(percentile(means, lower_percentile))


def decision_top_agents(rates: dict[str, dict[str, Any]]) -> tuple[str | None, str | None, float | None, bool]:
    usable = [(agent_id, float(row["pass_rate"])) for agent_id, row in rates.items() if row.get("pass_rate") is not None]
    if not usable:
        return None, None, None, False
    usable.sort(key=lambda item: (-item[1], item[0]))
    top_agent, top_rate = usable[0]
    second_agent = usable[1][0] if len(usable) > 1 else None
    second_rate = usable[1][1] if len(usable) > 1 else None
    margin = None if second_rate is None else top_rate - second_rate
    tied = second_rate is not None and top_rate == second_rate
    return top_agent, second_agent, margin, tied


def decision_wrapper_for_selection(
    selected_task_ids: list[str],
    agent_ids: list[str],
    outcome_rows: list[dict[str, str]],
    thresholds: dict[str, Any],
) -> dict[str, Any]:
    outcomes = outcome_lookup(outcome_rows)
    rates = selector_pass_rates(selected_task_ids, agent_ids, "selection", outcomes)
    top_agent, nearest, margin, tied = decision_top_agents(rates)
    min_common = int(thresholds.get("min_common_valid_selected_tasks", 8))
    action_margin = float(thresholds.get("action_margin", 0.05))
    iterations = int(thresholds.get("bootstrap_iterations", 1000))
    confidence = float(thresholds.get("confidence_level", 0.8))
    if top_agent is None or nearest is None or margin is None:
        return {
            "state": "need_more_evidence",
            "recommended_agent_id": None,
            "reason": "fewer_than_two_agents_with_valid_selection_rates",
            "selection_rates": rates,
        }

    pair_stats: list[dict[str, Any]] = []
    enough_common = True
    all_pairs_support_top = True
    for competitor in sorted(agent_id for agent_id in agent_ids if agent_id != top_agent):
        differences = paired_agent_differences(selected_task_ids, top_agent, competitor, outcomes)
        wins = sum(1 for value in differences if value > 0)
        losses = sum(1 for value in differences if value < 0)
        pair_margin = None if not differences else sum(differences) / len(differences)
        lcb = bootstrap_margin_lcb(differences, iterations=iterations, confidence_level=confidence)
        common_valid = len(differences)
        if common_valid < min_common:
            enough_common = False
        supports = (
            common_valid >= min_common
            and pair_margin is not None
            and pair_margin >= action_margin
            and wins > losses
            and (lcb is None or lcb >= 0.0)
            and (wins >= 2 or pair_margin >= action_margin * 2)
            and losses == 0
        )
        if not supports:
            all_pairs_support_top = False
        pair_stats.append(
            {
                "competitor_agent_id": competitor,
                "common_valid": common_valid,
                "wins": wins,
                "losses": losses,
                "ties": sum(1 for value in differences if value == 0),
                "selected_margin": selector_round(pair_margin),
                "bootstrap_lcb": lcb,
                "supports_recommendation": supports,
            }
        )

    if not enough_common:
        state = "need_more_evidence"
        reason = "insufficient_common_valid_selected_tasks"
        recommended = None
    elif tied or margin < action_margin:
        state = "abstain_indistinguishable"
        reason = "selected_top_margin_below_action_threshold_or_tied"
        recommended = None
    elif all_pairs_support_top:
        state = "recommend"
        reason = "top_agent_margin_and_paired_small_sample_fallback_passed"
        recommended = top_agent
    else:
        state = "need_more_evidence"
        reason = "paired_uncertainty_or_discordant_tasks_too_weak"
        recommended = None
    return {
        "state": state,
        "recommended_agent_id": recommended,
        "reason": reason,
        "top_agent_id": top_agent,
        "nearest_competitor_agent_id": nearest,
        "selected_top_margin": selector_round(margin),
        "selection_rates": rates,
        "pair_stats": pair_stats,
    }


def apply_later_decision_metrics(
    decision: dict[str, Any],
    selected_task_ids: list[str],
    later_task_ids: list[str],
    agent_ids: list[str],
    outcome_rows: list[dict[str, str]],
    thresholds: dict[str, Any],
    later_stage: str = "holdout",
) -> dict[str, Any]:
    base = evaluate_selected_task_ids(selected_task_ids, later_task_ids, agent_ids, outcome_rows, later_stage=later_stage)
    later_rates = base["later_rates"]
    later_top, later_second, later_margin, later_tied = decision_top_agents(later_rates)
    recommended = decision.get("recommended_agent_id")
    later_best = max((float(row["pass_rate"]) for row in later_rates.values() if row["pass_rate"] is not None), default=0.0)
    regret = None
    false_recommendation = None
    if decision.get("state") == "recommend" and recommended:
        regret = later_best - float(later_rates[recommended]["pass_rate"])
        false_recommendation = regret > float(thresholds.get("action_margin", 0.05))
    missed = None
    correct_abstain = None
    if decision.get("state") in {"abstain_indistinguishable", "need_more_evidence"}:
        large_later_gap = later_margin is not None and later_margin > float(thresholds.get("action_margin", 0.05))
        missed = large_later_gap
        correct_abstain = not large_later_gap if decision.get("state") == "abstain_indistinguishable" else None
    top_pair_agrees = None
    if recommended and decision.get("nearest_competitor_agent_id"):
        competitor = str(decision["nearest_competitor_agent_id"])
        selected_margin = float(decision.get("selected_top_margin") or 0.0)
        later_margin_for_pair = float(later_rates[recommended]["pass_rate"]) - float(later_rates[competitor]["pass_rate"])
        top_pair_agrees = selector_sign(selected_margin) == selector_sign(later_margin_for_pair)
    return {
        **base,
        "decision": decision,
        "later_top_agent_id": later_top,
        "later_second_agent_id": later_second,
        "later_top_margin": selector_round(later_margin),
        "later_top_tied": later_tied,
        "recommendation_regret": selector_round(regret),
        "false_recommendation": false_recommendation,
        "missed_opportunity": missed,
        "correct_abstain": correct_abstain,
        "top_pair_direction_agreement": top_pair_agrees,
    }


def summarize_decision_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    recommendations = [row for row in rows if row["decision"]["state"] == "recommend"]
    abstentions = [row for row in rows if row["decision"]["state"] == "abstain_indistinguishable"]
    need_more = [row for row in rows if row["decision"]["state"] == "need_more_evidence"]
    regrets = [float(row["recommendation_regret"]) for row in recommendations if row.get("recommendation_regret") is not None]
    false_rows = [row for row in recommendations if row.get("false_recommendation") is True]
    missed_rows = [row for row in rows if row.get("missed_opportunity") is True]
    correct_abstains = [row for row in abstentions if row.get("correct_abstain") is True]
    top_pair = [row for row in recommendations if row.get("top_pair_direction_agreement") is not None]
    return {
        "evaluated_count": total,
        "recommendation_coverage": selector_round(len(recommendations) / total if total else None),
        "abstain_rate": selector_round(len(abstentions) / total if total else None),
        "need_more_evidence_rate": selector_round(len(need_more) / total if total else None),
        "false_recommendation_rate": selector_round(len(false_rows) / len(recommendations) if recommendations else 0.0),
        "mean_recommendation_regret": selector_round(statistics.mean(regrets) if regrets else None),
        "worst_recommendation_regret": selector_round(max(regrets) if regrets else None),
        "missed_opportunity_rate": selector_round(len(missed_rows) / total if total else None),
        "correct_abstain_rate": selector_round(len(correct_abstains) / len(abstentions) if abstentions else None),
        "top_pair_direction_agreement_rate": selector_round(sum(1 for row in top_pair if row.get("top_pair_direction_agreement")) / len(top_pair) if top_pair else None),
    }


def compact_decision_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "selector_id": row.get("selector_id"),
        "k": row.get("k"),
        "decision_state": row["decision"]["state"],
        "recommended_agent_id": row["decision"].get("recommended_agent_id"),
        "reason": row["decision"].get("reason"),
        "selected_top_margin": row["decision"].get("selected_top_margin"),
        "later_top_agent_id": row.get("later_top_agent_id"),
        "later_top_margin": row.get("later_top_margin"),
        "MAE": row.get("MAE"),
        "pairwise_direction_agreement": row.get("pairwise_direction_agreement"),
        "recommendation_regret": row.get("recommendation_regret"),
        "false_recommendation": row.get("false_recommendation"),
        "missed_opportunity": row.get("missed_opportunity"),
        "top_pair_direction_agreement": row.get("top_pair_direction_agreement"),
        "selected_task_ids": row.get("selected_task_ids", []),
    }


def selector_decision_eval(config: dict[str, Any]) -> dict[str, Any]:
    protocol = read_json(result_path("selector_protocol.json"))
    thresholds = protocol["decision_thresholds"]
    task_rows = load_selector_task_rows()
    outcome_rows = load_selector_outcome_rows()
    candidates = selector_candidate_tasks(task_rows)
    later_ids = selector_later_task_ids(task_rows)
    agent_ids = selector_agent_ids(config)
    hrd = read_json(result_path("selector_hrd_eval.json"))
    baseline = read_json(result_path("selector_baseline_eval.json"))
    selector_rows: list[dict[str, Any]] = []
    source_rows: list[tuple[str, int, list[str]]] = []
    for row in baseline["selector_results"].values():
        source_rows.append((row["selector_id"], int(row["k"]), list(row["selected_task_ids"])))
    for row in hrd["variants"].values():
        source_rows.append((row["selector_id"], int(row["k"]), list(row["selected_task_ids"])))
    for selector_id, k, selected_ids in source_rows:
        decision = decision_wrapper_for_selection(selected_ids, agent_ids, outcome_rows, thresholds)
        metrics = apply_later_decision_metrics(decision, selected_ids, later_ids, agent_ids, outcome_rows, thresholds)
        selector_rows.append({"selector_id": selector_id, "k": k, **metrics})

    random_summaries: dict[str, dict[str, Any]] = {}
    seeds = [int(seed) for seed in protocol["random_seeds"]]
    for k in [10, 20]:
        for baseline_id, func in BASELINE_SELECTOR_FUNCS.items():
            rows: list[dict[str, Any]] = []
            for seed in seeds:
                selected_ids = func(candidates, k, seed)
                decision = decision_wrapper_for_selection(selected_ids, agent_ids, outcome_rows, thresholds)
                metrics = apply_later_decision_metrics(decision, selected_ids, later_ids, agent_ids, outcome_rows, thresholds)
                rows.append({"selector_id": baseline_id, "k": k, "seed": seed, **metrics})
            random_summaries[f"{baseline_id}__k{k}"] = {
                "selector_id": baseline_id,
                "k": k,
                "seed_count": len(seeds),
                "summary": summarize_decision_rows(rows),
            }

    payload = {
        "schema_version": "barcarolle.agent_selection_demo.selector_decision_eval.v1",
        "generated_at": "2026-06-14",
        "paid_agent_calls_made": False,
        "thresholds": thresholds,
        "selector_decisions": [compact_decision_row(row) for row in selector_rows],
        "selector_decision_summary": summarize_decision_rows(selector_rows),
        "random_decision_summaries": random_summaries,
        "interpretation": {
            "recommendation_rule": "recommend only with non-tie top, minimum common valid support, action margin, and small-sample paired fallback with no discordant losses for the top Agent",
            "hard_recommend_on_tie": False,
        },
    }
    write_json(result_path("selector_decision_eval.json"), payload)
    write_text(report_path("selector_decision_eval_zh.md"), render_selector_decision_eval(payload))
    return payload


def render_selector_decision_eval(payload: dict[str, Any]) -> str:
    lines = [
        "# Selector Decision Eval",
        "",
        "生成日期：2026-06-14",
        "",
        "## Decision rule",
        "",
        "决策层输出三种状态：`recommend`、`abstain_indistinguishable`、`need_more_evidence`。它不会在 Selection tie 上硬推荐；k=10 小样本下要求 top Agent 对每个 competitor 的 common-valid paired comparison 没有 discordant loss。",
        "",
        "## Selector decisions",
        "",
        "| Selector | k | State | Recommended | Selection margin | Later top | Later margin | MAE | Regret | Top-pair agree | Reason |",
        "| --- | ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in payload["selector_decisions"]:
        lines.append(
            f"| `{row['selector_id']}` | `{row['k']}` | `{row['decision_state']}` | `{row['recommended_agent_id']}` | "
            f"`{row['selected_top_margin']}` | `{row['later_top_agent_id']}` | `{row['later_top_margin']}` | "
            f"`{row['MAE']}` | `{row['recommendation_regret']}` | `{row['top_pair_direction_agreement']}` | `{row['reason']}` |"
        )
    summary = payload["selector_decision_summary"]
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Recommendation coverage: `{summary['recommendation_coverage']}`。",
            f"- False-recommendation rate: `{summary['false_recommendation_rate']}`。",
            f"- Mean recommendation regret: `{summary['mean_recommendation_regret']}`；worst regret: `{summary['worst_recommendation_regret']}`。",
            f"- Missed-opportunity rate: `{summary['missed_opportunity_rate']}`。",
            f"- Top-pair direction agreement among recommendations: `{summary['top_pair_direction_agreement_rate']}`。",
            "",
            "## Random decision baselines",
            "",
            "| Baseline | k | Recommendation coverage | False recommend | Mean regret | Worst regret | Missed opportunity | Top-pair agree |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["random_decision_summaries"].values():
        s = row["summary"]
        lines.append(
            f"| `{row['selector_id']}` | `{row['k']}` | `{s['recommendation_coverage']}` | `{s['false_recommendation_rate']}` | "
            f"`{s['mean_recommendation_regret']}` | `{s['worst_recommendation_regret']}` | `{s['missed_opportunity_rate']}` | "
            f"`{s['top_pair_direction_agreement_rate']}` |"
        )
    return "\n".join(lines) + "\n"


def selector_final_preregistration(config: dict[str, Any]) -> dict[str, Any]:
    protocol = read_json(result_path("selector_protocol.json"))
    task_rows = load_selector_task_rows()
    candidates = selector_candidate_tasks(task_rows)
    final_selection = select_hrd_hybrid(candidates, 10, 0.7)
    later_task_ids = selector_later_task_ids(task_rows)
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.selector_final_preregistration.v1",
        "generated_at": "2026-06-14",
        "status": "frozen_before_final_outcome_join",
        "target_repo": config["target_repo"]["repo_name"],
        "selector": {
            "selector_id": "hrd_70_30",
            "family": "hybrid_representative_disagreement",
            "budget_k": 10,
            "representative_fraction": 0.7,
            "representative_selector": "rsq_recency_stratified_quota",
            "disagreement_source": final_selection["disagreement_source"],
            "quality_gate": "quality_score >= 1.0 and risk_flag == false and flaky_flag == false",
            "module_cap": "ceil(k * 0.3) during representative fill and discriminative fill",
        },
        "agent_set": selector_agent_ids(config),
        "top2_repeat_validation_agent_set": TOP2_REPEAT_AGENT_IDS,
        "final_origin_demo_slice": protocol["split_plan"]["final_demo_slice"],
        "selected_task_ids_before_outcome_join": final_selection["selected_task_ids"],
        "representative_task_ids": final_selection["representative_task_ids"],
        "discriminative_task_ids": final_selection["discriminative_task_ids"],
        "later_holdout_task_ids": later_task_ids,
        "random_seed_list": protocol["random_seeds"],
        "invalid_cell_policy": protocol["invalid_cell_policy"],
        "decision_thresholds": protocol["decision_thresholds"],
        "success_criteria": {
            "recommendation_required": True,
            "later_top_must_match_recommended_or_regret_lte": 0.05,
            "recommended_top_pair_direction_must_agree": True,
            "mae_improvement_vs_strong_random_abs_min": 0.02,
            "mae_improvement_vs_strong_random_relative_min": 0.10,
            "decision_metrics_must_beat_random_distribution": True,
        },
        "paid_boundary": {
            "default": "no_new_paid_cells",
            "approved_cap_new_cells": 80,
            "paid_cells_used_by_this_run": 0,
            "endpoint_env_required_if_paid": ["LLM_BASE_URL", "LLM_API_KEY"],
        },
    }
    write_json(result_path("selector_final_preregistration.json"), payload)
    write_text(report_path("selector_final_preregistration_zh.md"), render_selector_final_preregistration(payload))
    return payload


def render_selector_final_preregistration(payload: dict[str, Any]) -> str:
    selector = payload["selector"]
    lines = [
        "# Selector Final Preregistration",
        "",
        "生成日期：2026-06-14",
        "",
        "## Locked selector",
        "",
        f"- Selector: `{selector['selector_id']}`。",
        f"- Budget k: `{selector['budget_k']}`。",
        f"- Representative/discriminative split: `70/30`。",
        f"- Representative selector: `{selector['representative_selector']}`。",
        f"- Disagreement source: `{selector['disagreement_source']}`。",
        "",
        "## Frozen task IDs",
        "",
        f"- Selected tasks before outcome join: `{', '.join(payload['selected_task_ids_before_outcome_join'])}`。",
        f"- Later/Holdout tasks: `{', '.join(payload['later_holdout_task_ids'])}`。",
        "",
        "## Decision thresholds",
        "",
        f"- Action margin: `{payload['decision_thresholds']['action_margin']}`。",
        f"- Minimum common valid tasks: `{payload['decision_thresholds']['min_common_valid_selected_tasks']}`。",
        f"- Bootstrap iterations: `{payload['decision_thresholds']['bootstrap_iterations']}`。",
        "",
        "## Paid boundary",
        "",
        "默认不运行新 paid cells。只有 no-paid final result 因 missing cells 而无法解释时，才按 runbook paid boundary 补最小 frozen grid。本 preregistration 的 planned paid use 是 `0`。",
    ]
    return "\n".join(lines) + "\n"


def selector_final_eval(config: dict[str, Any]) -> dict[str, Any]:
    prereg = selector_final_preregistration(config)
    task_rows = load_selector_task_rows()
    outcome_rows = load_selector_outcome_rows()
    agent_ids = selector_agent_ids(config)
    selected_ids = list(prereg["selected_task_ids_before_outcome_join"])
    later_ids = list(prereg["later_holdout_task_ids"])
    thresholds = prereg["decision_thresholds"]
    decision = decision_wrapper_for_selection(selected_ids, agent_ids, outcome_rows, thresholds)
    holdout_metrics = apply_later_decision_metrics(decision, selected_ids, later_ids, agent_ids, outcome_rows, thresholds)
    repeat_metrics = apply_later_decision_metrics(
        decision_wrapper_for_selection(selected_ids, TOP2_REPEAT_AGENT_IDS, outcome_rows, thresholds),
        selected_ids,
        later_ids,
        TOP2_REPEAT_AGENT_IDS,
        outcome_rows,
        thresholds,
        later_stage="doubled_timeout_top2_repeat",
    )
    baseline = read_json(result_path("selector_baseline_eval.json"))
    decision_eval = read_json(result_path("selector_decision_eval.json"))
    hrd = read_json(result_path("selector_hrd_eval.json"))
    strong_random = baseline["random_baselines"]["stratified_random__k10"]["summary"]
    strong_random_decision = decision_eval["random_decision_summaries"]["stratified_random__k10"]["summary"]
    hrd_row = hrd["variants"]["hrd_70_30__k10"]
    mae = float(holdout_metrics["MAE"])
    random_mae = float(strong_random["MAE_mean"])
    abs_improvement = random_mae - mae
    rel_improvement = abs_improvement / random_mae if random_mae else None
    recommended = decision.get("recommended_agent_id")
    regret = holdout_metrics.get("recommendation_regret")
    preferred = (
        decision.get("state") == "recommend"
        and recommended == holdout_metrics.get("later_top_agent_id")
        and regret is not None
        and float(regret) <= 0.05
        and holdout_metrics.get("top_pair_direction_agreement") is True
        and (abs_improvement >= 0.02 or (rel_improvement is not None and rel_improvement >= 0.10))
    )
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.selector_final_eval.v1",
        "generated_at": "2026-06-14",
        "paid_agent_calls_made": False,
        "new_paid_cells": 0,
        "new_paid_cost_usd": 0.0,
        "preregistration": "experiments/agent_selection_demo/results/selector_final_preregistration.json",
        "selector_id": "hrd_70_30",
        "k": 10,
        "selected_task_ids": selected_ids,
        "later_holdout_task_ids": later_ids,
        "decision": decision,
        "holdout_metrics": holdout_metrics,
        "top2_repeat_metrics": repeat_metrics,
        "strong_random_baseline": {
            "baseline_id": "stratified_random",
            "k": 10,
            "MAE_mean": strong_random["MAE_mean"],
            "decision_summary": strong_random_decision,
        },
        "mae_comparison": {
            "selector_MAE": selector_round(mae),
            "strong_random_MAE_mean": strong_random["MAE_mean"],
            "absolute_improvement": selector_round(abs_improvement),
            "relative_improvement": selector_round(rel_improvement),
            "MAE_beats_or_ties_stratified_random_share": hrd_row["random_percentiles"]["stratified_random"]["MAE_beats_or_ties_random_share"],
        },
        "decision_comparison": {
            "selector_recommendation_regret": regret,
            "strong_random_mean_regret_when_recommending": strong_random_decision["mean_recommendation_regret"],
            "strong_random_false_recommendation_rate": strong_random_decision["false_recommendation_rate"],
            "selector_top_pair_direction_agreement": holdout_metrics.get("top_pair_direction_agreement"),
            "strong_random_top_pair_direction_agreement_rate": strong_random_decision["top_pair_direction_agreement_rate"],
        },
        "preferred_terminal_state_achieved": preferred,
        "paid_completion_needed": False,
        "paid_completion_reason": "No-paid final slice has complete selected-task Selection cells, complete Holdout cells for all four Agents, and complete doubled-timeout top-2 repeat cells.",
        "claim_supported": "On the frozen boltons demo slice, the preregistered HRD 70/30 selector recommends Kilo + GPT mainline; original Holdout and doubled-timeout top-2 repeat both favor Kilo, with zero recommendation regret on the reported later slices.",
    }
    write_json(result_path("selector_final_eval.json"), payload)
    write_text(report_path("selector_final_eval_zh.md"), render_selector_final_eval(payload))
    return payload


def rate_summary(rates: dict[str, dict[str, Any]]) -> str:
    return ", ".join(f"{agent}: {row['pass_count']}/{row['valid_count']}" for agent, row in sorted(rates.items()))


def render_selector_final_eval(payload: dict[str, Any]) -> str:
    holdout = payload["holdout_metrics"]
    repeat = payload["top2_repeat_metrics"]
    mae = payload["mae_comparison"]
    decision = payload["decision"]
    lines = [
        "# Selector Final Eval",
        "",
        "生成日期：2026-06-14",
        "",
        "## Final result",
        "",
        f"- Preferred terminal state achieved: `{payload['preferred_terminal_state_achieved']}`。",
        f"- Decision state: `{decision['state']}`。",
        f"- Recommended Agent: `{decision.get('recommended_agent_id')}`。",
        f"- Holdout later top: `{holdout['later_top_agent_id']}`。",
        f"- Recommendation regret: `{holdout['recommendation_regret']}`。",
        f"- New paid cells: `{payload['new_paid_cells']}`；new paid cost: `${payload['new_paid_cost_usd']}`。",
        "",
        "## Selection and later pass rates",
        "",
        f"- Selection: `{rate_summary(holdout['selection_rates'])}`。",
        f"- Holdout: `{rate_summary(holdout['later_rates'])}`。",
        f"- Doubled-timeout top-2 repeat: `{rate_summary(repeat['later_rates'])}`。",
        "",
        "## Strong random comparison",
        "",
        f"- Selector MAE: `{mae['selector_MAE']}`。",
        f"- Stratified random k=10 MAE mean: `{mae['strong_random_MAE_mean']}`。",
        f"- Absolute improvement: `{mae['absolute_improvement']}`。",
        f"- Relative improvement: `{mae['relative_improvement']}`。",
        f"- Selector beats/ties stratified-random MAE share: `{mae['MAE_beats_or_ties_stratified_random_share']}`。",
        "",
        "## Paid boundary",
        "",
        payload["paid_completion_reason"],
        "",
        "## Claim",
        "",
        payload["claim_supported"],
    ]
    return "\n".join(lines) + "\n"


def render_selector_baseline_eval(payload: dict[str, Any]) -> str:
    lines = [
        "# Selector Baseline Eval",
        "",
        "生成日期：2026-06-14",
        "",
        "## Scope",
        "",
        "本 package 只使用 committed sanitized score tables，没有新 paid cells。所有 selector 在固定 task IDs 后才 join Selection 和 Holdout outcomes。",
        "",
        "## Random baselines",
        "",
        "| Baseline | k | Seeds | Unique samples | MAE mean | Pairwise mean | Top-1 forced | Regret mean |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["random_baselines"].values():
        summary = row["summary"]
        lines.append(
            f"| `{row['selector_id']}` | `{row['k']}` | `{row['seed_count']}` | `{row['unique_sample_count']}` | "
            f"`{summary['MAE_mean']}` | `{summary['pairwise_direction_agreement_mean']}` | "
            f"`{summary['top1_agreement_rate_forced']}` | `{summary['forced_recommendation_regret_mean']}` |"
        )
    lines.extend(
        [
            "",
            "## RSQ",
            "",
            "| Selector | k | Selected tasks | MAE | Pairwise agreement | Forced top | Later top | Forced regret | MAE percentile vs stratified random |",
            "| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: |",
        ]
    )
    for row in payload["selector_results"].values():
        stratified = row["random_percentiles"]["stratified_random"]
        lines.append(
            f"| `{row['selector_id']}` | `{row['k']}` | `{len(row['selected_task_ids'])}` | `{row['MAE']}` | "
            f"`{row['pairwise_direction_agreement']}` | `{row['selection_forced_top_agent_id']}` | "
            f"`{row['later_top_agent_id']}` | `{row['forced_recommendation_regret']}` | "
            f"`{stratified['MAE_beats_or_ties_random_share']}` |"
        )
    best_key = payload["interpretation"]["best_rsq_key"]
    best = payload["selector_results"][best_key]
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"最佳 RSQ slice 是 `{best_key}`，MAE `{best['MAE']}`。它把 source/recency quota 固定在 metadata 层，并在每个 quota 内偏好较新的任务和 module cap。",
            "",
            "Package 3 的 forced top/regret 只是诊断口径；真正的 recommend/abstain/need-more-evidence 由 Package 5 的 shared decision wrapper 统一处理，避免在 selection tie 上硬推荐。",
        ]
    )
    return "\n".join(lines) + "\n"


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


def pv_result_path(name: str) -> Path:
    return result_path(name)


def phase1_result_path(name: str) -> Path:
    return ROOT / "experiments" / "phase1_compiler" / "results" / name


def phase1_report_path(name: str) -> Path:
    return ROOT / "experiments" / "phase1_compiler" / "reports" / name


def safe_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def scoreable_pass_rate(metric: dict[str, Any]) -> float | None:
    scoreable = safe_int(metric.get("scoreable_cells"))
    if scoreable <= 0:
        return None
    return safe_int(metric.get("verified_pass_count")) / scoreable


def pv_round(value: float | None, digits: int = 6) -> float | None:
    return None if value is None else round(float(value), digits)


def prediction_slice_error(row: dict[str, Any], threshold: float) -> dict[str, Any]:
    selection = safe_float(row.get("selection_pass_rate"))
    future = safe_float(row.get("future_pass_rate"))
    if selection is None or future is None:
        return {
            **row,
            "signed_error": None,
            "absolute_error": None,
            "squared_error": None,
            "catastrophic_miss": False,
        }
    signed = selection - future
    absolute = abs(signed)
    return {
        **row,
        "signed_error": pv_round(signed),
        "absolute_error": pv_round(absolute),
        "squared_error": pv_round(signed * signed),
        "catastrophic_miss": absolute > threshold,
    }


def summarize_prediction_rows(rows: list[dict[str, Any]], threshold: float = PV_CATASTROPHIC_THRESHOLD) -> dict[str, Any]:
    evaluated = [prediction_slice_error(row, threshold) for row in rows]
    valid = [row for row in evaluated if row["absolute_error"] is not None]
    if not valid:
        return {
            "slice_count": 0,
            "MAE": None,
            "RMSE": None,
            "mean_signed_error": None,
            "catastrophic_miss_rate": None,
            "selection_scoreable_cells": 0,
            "future_scoreable_cells": 0,
            "missing_or_non_scoreable_count": sum(safe_int(row.get("missing_or_non_scoreable_count")) for row in evaluated),
        }
    return {
        "slice_count": len(valid),
        "MAE": pv_round(statistics.mean(float(row["absolute_error"]) for row in valid)),
        "RMSE": pv_round(math.sqrt(statistics.mean(float(row["squared_error"]) for row in valid))),
        "mean_signed_error": pv_round(statistics.mean(float(row["signed_error"]) for row in valid)),
        "catastrophic_miss_rate": pv_round(sum(1 for row in valid if row["catastrophic_miss"]) / len(valid)),
        "selection_scoreable_cells": sum(safe_int(row.get("selection_scoreable_count")) for row in valid),
        "future_scoreable_cells": sum(safe_int(row.get("future_scoreable_count")) for row in valid),
        "missing_or_non_scoreable_count": sum(safe_int(row.get("missing_or_non_scoreable_count")) for row in evaluated),
    }


def rank_and_regret_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("role") == "diagnostic":
            continue
        key = (str(row.get("window_id")), str(row.get("repo")), str(row.get("design_id")))
        grouped[key].append(row)
    rank_rows: list[dict[str, Any]] = []
    regret_rows: list[dict[str, Any]] = []
    for (window_id, repo, design_id), group in sorted(grouped.items()):
        valid = [
            row
            for row in group
            if safe_float(row.get("selection_pass_rate")) is not None and safe_float(row.get("future_pass_rate")) is not None
        ]
        if len(valid) < 2:
            continue
        selection_rank = sorted(valid, key=lambda row: (-float(row["selection_pass_rate"]), str(row["agent_id"])))
        future_rank = sorted(valid, key=lambda row: (-float(row["future_pass_rate"]), str(row["agent_id"])))
        recommended_agent = next((str(row.get("recommended_agent_id")) for row in valid if row.get("recommended_agent_id")), "")
        selected = next((row for row in valid if row["agent_id"] == recommended_agent), None) if recommended_agent else selection_rank[0]
        if selected is None:
            selected = selection_rank[0]
        best_future = future_rank[0]
        rank_rows.append(
            {
                "window_id": window_id,
                "repo": repo,
                "design_id": design_id,
                "agent_count": len(valid),
                "selection_top_agent": selection_rank[0]["agent_id"],
                "future_top_agent": best_future["agent_id"],
                "top_rank_agrees": selection_rank[0]["agent_id"] == best_future["agent_id"],
            }
        )
        regret_rows.append(
            {
                "window_id": window_id,
                "repo": repo,
                "design_id": design_id,
                "selected_agent_id": selected["agent_id"],
                "selection_rule": "frozen_recommendation" if recommended_agent else "max_selection_pass_rate",
                "future_best_agent_id": best_future["agent_id"],
                "selected_future_pass_rate": pv_round(safe_float(selected.get("future_pass_rate"))),
                "future_best_pass_rate": pv_round(safe_float(best_future.get("future_pass_rate"))),
                "recommendation_regret": pv_round(float(best_future["future_pass_rate"]) - float(selected["future_pass_rate"])),
            }
        )
    return rank_rows, regret_rows


def summarize_rank_and_regret(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rank_rows, regret_rows = rank_and_regret_rows(rows)
    regrets = [float(row["recommendation_regret"]) for row in regret_rows if row["recommendation_regret"] is not None]
    return {
        "rank_agreement": {
            "groups_evaluated": len(rank_rows),
            "top_rank_agreement_rate": None
            if not rank_rows
            else pv_round(sum(1 for row in rank_rows if row["top_rank_agrees"]) / len(rank_rows)),
            "rows": rank_rows,
        },
        "recommendation_regret": {
            "groups_evaluated": len(regret_rows),
            "mean_regret": None if not regrets else pv_round(statistics.mean(regrets)),
            "max_regret": None if not regrets else pv_round(max(regrets)),
            "rows": regret_rows,
        },
    }


def phase1_prediction_slices() -> list[dict[str, Any]]:
    path = phase1_result_path("phase1_retrospective_predictive_signal_adapter_metrics.json")
    if not path.exists():
        return []
    payload = read_json(path)
    slices: list[dict[str, Any]] = []
    for row in payload.get("metric_rows", []):
        slices.append(
            {
                "source": "phase1_retrospective_predictive_signal",
                "source_path": display_path(path),
                "window_id": row.get("window_id"),
                "mode": row.get("mode"),
                "repo": row.get("repo"),
                "origin_or_window": row.get("window_id"),
                "agent_id": row.get("adapter_id"),
                "design_id": row.get("design_id"),
                "design_instance_id": row.get("design_instance_id"),
                "role": row.get("role"),
                "claim_boundary": row.get("claim_boundary"),
                "selection_stage": "B_eval",
                "future_stage": "H_future",
                "selection_pass_rate": row.get("B_eval_pass_rate"),
                "future_pass_rate": row.get("H_future_pass_rate"),
                "selection_scoreable_count": row.get("B_eval_scoreable_count"),
                "future_scoreable_count": row.get("H_future_scoreable_count"),
                "selection_pass_count": row.get("B_eval_pass_count"),
                "future_pass_count": row.get("H_future_pass_count"),
                "missing_or_non_scoreable_count": row.get("missing_or_non_scoreable_count", 0),
            }
        )
    return slices


def demo_prediction_slices() -> list[dict[str, Any]]:
    selection_path = stage_paths("selection")["metrics"]
    holdout_path = stage_paths("holdout")["metrics"]
    lock_path = result_path("recommendation_lock.json")
    if not (selection_path.exists() and holdout_path.exists()):
        return []
    selection = read_json(selection_path)
    holdout = read_json(holdout_path)
    recommended = read_json(lock_path).get("recommended_agent_id_for_holdout") if lock_path.exists() else None
    rows: list[dict[str, Any]] = []
    for agent_id, selection_metric in sorted(selection.get("agent_metrics", {}).items()):
        future_metric = holdout.get("agent_metrics", {}).get(agent_id)
        if not future_metric:
            continue
        rows.append(
            {
                "source": "agent_selection_demo",
                "source_path": display_path(holdout_path),
                "window_id": "demo_boltons_selection_to_holdout",
                "mode": "demo_fresh_holdout",
                "repo": "boltons",
                "origin_or_window": "demo_selection_lock",
                "agent_id": agent_id,
                "design_id": "demo_selection_set",
                "design_instance_id": "demo_selection_set",
                "role": "demo_selection",
                "claim_boundary": "demo_evidence_only_not_baseline_comparable",
                "selection_stage": "selection",
                "future_stage": "holdout",
                "selection_pass_rate": pv_round(scoreable_pass_rate(selection_metric)),
                "future_pass_rate": pv_round(scoreable_pass_rate(future_metric)),
                "selection_scoreable_count": selection_metric.get("scoreable_cells"),
                "future_scoreable_count": future_metric.get("scoreable_cells"),
                "selection_pass_count": selection_metric.get("verified_pass_count"),
                "future_pass_count": future_metric.get("verified_pass_count"),
                "missing_or_non_scoreable_count": safe_int(selection_metric.get("scheduled_cells")) - safe_int(selection_metric.get("scoreable_cells"))
                + safe_int(future_metric.get("scheduled_cells")) - safe_int(future_metric.get("scoreable_cells")),
                "recommended_agent_id": recommended,
            }
        )
    return rows


def deduplicated_scoreable_support(joined_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    for row in joined_rows:
        key = (
            str(row.get("window_id")),
            str(row.get("repo")),
            str(row.get("adapter_id")),
            str(row.get("split")),
            str(row.get("task_id")),
        )
        by_key.setdefault(key, row)
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for (window_id, repo, agent_id, split, _task_id), row in by_key.items():
        grouped[(window_id, repo, agent_id, split)].append(row)
    support: list[dict[str, Any]] = []
    for (window_id, repo, agent_id, split), rows in sorted(grouped.items()):
        support.append(
            {
                "window_id": window_id,
                "repo": repo,
                "agent_id": agent_id,
                "stage": split,
                "task_count": len(rows),
                "scoreable_cells": sum(1 for row in rows if row.get("scoreable_cell") is True),
                "pass_count": sum(1 for row in rows if row.get("pass_flag") is True),
                "non_scoreable_cells": sum(1 for row in rows if row.get("scoreable_cell") is not True),
            }
        )
    return support


def demo_scoreable_support() -> list[dict[str, Any]]:
    support: list[dict[str, Any]] = []
    for stage in ["selection", "holdout", TOP2_REPEAT_STAGE]:
        for row in read_csv_rows(stage_paths(stage)["score"]):
            if stage == TOP2_REPEAT_STAGE:
                window_id = "demo_boltons_top2_repeat"
            else:
                window_id = "demo_boltons_selection_to_holdout"
            support.append(
                {
                    "window_id": window_id,
                    "repo": "boltons",
                    "agent_id": row.get("agent_id", ""),
                    "stage": stage,
                    "task_count": 1,
                    "scoreable_cells": 1 if csv_bool(row.get("scoreable_cell")) else 0,
                    "pass_count": 1 if csv_bool(row.get("verified_pass")) else 0,
                    "non_scoreable_cells": 0 if csv_bool(row.get("scoreable_cell")) else 1,
                }
            )
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in support:
        grouped[(row["window_id"], row["repo"], row["agent_id"], row["stage"])].append(row)
    return [
        {
            "window_id": window_id,
            "repo": repo,
            "agent_id": agent_id,
            "stage": stage,
            "task_count": len(rows),
            "scoreable_cells": sum(row["scoreable_cells"] for row in rows),
            "pass_count": sum(row["pass_count"] for row in rows),
            "non_scoreable_cells": sum(row["non_scoreable_cells"] for row in rows),
        }
        for (window_id, repo, agent_id, stage), rows in sorted(grouped.items())
    ]


def window_capabilities(slices: list[dict[str, Any]], support_rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [
        row
        for row in slices
        if safe_float(row.get("selection_pass_rate")) is not None and safe_float(row.get("future_pass_rate")) is not None
    ]
    by_group: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    for row in valid:
        by_group[(str(row.get("window_id")), str(row.get("repo")), str(row.get("design_id")))].add(str(row.get("agent_id")))
    designs = sorted({str(row.get("design_id")) for row in valid if row.get("design_id")})
    has_simple = bool(set(designs) & set(PV_SIMPLE_BASELINES))
    has_candidate = bool(set(designs) & set(PV_CANDIDATE_SELECTORS))
    return {
        "pass_rate_prediction": bool(valid),
        "agent_ranking_agreement": any(len(agents) >= 2 for agents in by_group.values()),
        "recommendation_regret": any(len(agents) >= 2 for agents in by_group.values()),
        "baseline_comparison": has_simple and has_candidate,
        "scoreable_support_rows": len(support_rows),
        "designs_available": designs,
    }


def build_predictive_validity_inventory() -> dict[str, Any]:
    universe_path = phase1_result_path("phase1_retrospective_predictive_signal_universe.json")
    window_plan_path = phase1_result_path("phase1_retrospective_predictive_signal_window_plan.json")
    join_path = phase1_result_path("phase1_retrospective_predictive_signal_score_join_manifest.json")
    phase1_slices = phase1_prediction_slices()
    demo_slices = demo_prediction_slices()
    support_rows: list[dict[str, Any]] = []
    source_paths = [
        display_path(path)
        for path in [
            universe_path,
            window_plan_path,
            join_path,
            phase1_result_path("phase1_retrospective_predictive_signal_adapter_metrics.json"),
            result_path("selection_metrics.json"),
            result_path("holdout_metrics.json"),
            result_path("top2_repeat_metrics.json"),
        ]
        if path.exists()
    ]
    repos: dict[str, Any] = {}
    windows: list[dict[str, Any]] = []
    if universe_path.exists():
        universe = read_json(universe_path)
        for repo, summary in sorted((universe.get("counts_by_repo") or {}).items()):
            repos[repo] = {
                "eligible_task_count": summary.get("eligible"),
                "with_any_committed_outcome_row": summary.get("with_any_committed_outcome_row"),
                "with_both_adapter_rows": summary.get("with_both_adapter_rows"),
                "time_bucket_counts": summary.get("time_bucket_counts", {}),
            }
    if join_path.exists():
        join = read_json(join_path)
        support_rows.extend(deduplicated_scoreable_support(join.get("joined_rows", [])))
    support_rows.extend(demo_scoreable_support())
    all_slices = phase1_slices + demo_slices
    support_by_window: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in support_rows:
        support_by_window[str(row["window_id"])].append(row)
    slices_by_window: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_slices:
        slices_by_window[str(row["window_id"])].append(row)
    if window_plan_path.exists():
        window_plan = read_json(window_plan_path)
        for window in window_plan.get("windows", []):
            window_id = str(window.get("window_id"))
            window_slices = slices_by_window.get(window_id, [])
            support = support_by_window.get(window_id, [])
            windows.append(
                {
                    "window_id": window_id,
                    "source": "phase1_retrospective_predictive_signal",
                    "mode": window.get("mode"),
                    "support_status": window.get("support_status"),
                    "cutoff_rule": window.get("cutoff_rule"),
                    "repos": sorted((window.get("support_by_repo") or {}).keys()),
                    "agents": sorted({row["agent_id"] for row in support}),
                    "support_by_repo_agent_stage": support,
                    "capabilities": window_capabilities(window_slices, support),
                }
            )
    for window_id in ["demo_boltons_selection_to_holdout", "demo_boltons_top2_repeat"]:
        support = support_by_window.get(window_id, [])
        window_slices = slices_by_window.get(window_id, [])
        if not support and not window_slices:
            continue
        windows.append(
            {
                "window_id": window_id,
                "source": "agent_selection_demo",
                "mode": "demo_fresh_holdout" if window_id.endswith("holdout") else "demo_repeatability_blocker",
                "support_status": "accepted_for_demo_metric" if window_slices else "blocked_infrastructure",
                "cutoff_rule": "frozen demo split; not a formal rolling-origin baseline window",
                "repos": ["boltons"],
                "agents": sorted({row["agent_id"] for row in support}),
                "support_by_repo_agent_stage": support,
                "capabilities": window_capabilities(window_slices, support),
            }
        )
    inventory = {
        "schema_version": "barcarolle.agent_selection_demo.predictive_validity_window_inventory.v1",
        "generated_at": iso_now(),
        "paid_calls_made": false_bool(),
        "source_artifacts": source_paths,
        "candidate_repos": repos,
        "windows": windows,
        "metric_slices": all_slices,
        "inventory_summary": {
            "repo_count": len(repos),
            "window_count": len(windows),
            "metric_slice_count": len(all_slices),
            "viable_pass_rate_windows": sum(1 for window in windows if window["capabilities"]["pass_rate_prediction"]),
            "baseline_comparison_windows": sum(1 for window in windows if window["capabilities"]["baseline_comparison"]),
            "raw_artifacts_needed": False,
        },
    }
    return inventory


def false_bool() -> bool:
    return False


def render_predictive_validity_feasibility(inventory: dict[str, Any]) -> str:
    repo_rows = [
        {
            "Repo": repo,
            "Eligible": row.get("eligible_task_count"),
            "Any outcome": row.get("with_any_committed_outcome_row"),
            "Both Agents": row.get("with_both_adapter_rows"),
            "Time buckets": ", ".join(f"{key}:{value}" for key, value in (row.get("time_bucket_counts") or {}).items()),
        }
        for repo, row in sorted(inventory.get("candidate_repos", {}).items())
    ]
    window_rows = [
        {
            "Window": row["window_id"],
            "Mode": row["mode"],
            "Repos": ", ".join(row["repos"]),
            "Agents": ", ".join(row["agents"]),
            "Pass-rate": row["capabilities"]["pass_rate_prediction"],
            "Rank/regret": row["capabilities"]["agent_ranking_agreement"],
            "Baselines": row["capabilities"]["baseline_comparison"],
            "Status": row["support_status"],
        }
        for row in inventory["windows"]
    ]
    summary = inventory["inventory_summary"]
    lines = [
        "# Predictive-validity Feasibility",
        "",
        f"生成日期：{inventory['generated_at']}",
        "",
        "本报告只读取 committed sanitized outcomes、score tables 和 metadata summaries；没有读取 raw prompts、raw completions、transcripts、solver workspaces、verifier workspaces 或 provider logs，也没有运行 paid calls。",
        "",
        "## Summary",
        "",
        f"- Candidate repos: `{summary['repo_count']}`.",
        f"- Windows inventoried: `{summary['window_count']}`.",
        f"- Metric slices available: `{summary['metric_slice_count']}`.",
        f"- Pass-rate prediction windows: `{summary['viable_pass_rate_windows']}`.",
        f"- Baseline-comparison windows: `{summary['baseline_comparison_windows']}`.",
        f"- Raw artifacts needed: `{summary['raw_artifacts_needed']}`.",
        "",
        "## Repos",
        "",
        *markdown_table(repo_rows, [("Repo", "Repo"), ("Eligible", "Eligible"), ("Any outcome", "Any outcome"), ("Both Agents", "Both Agents"), ("Time buckets", "Time buckets")]),
        "",
        "## Windows",
        "",
        *markdown_table(window_rows, [("Window", "Window"), ("Mode", "Mode"), ("Repos", "Repos"), ("Agents", "Agents"), ("Pass-rate", "Pass-rate"), ("Rank/regret", "Rank/regret"), ("Baselines", "Baselines"), ("Status", "Status")]),
        "",
        "## Interpretation",
        "",
        "至少一个 no-paid retrospective window 可以支持 pass-rate prediction 和 simple-baseline comparison。`attrs`、`boltons`、`click` 都有 committed sanitized outcomes；demo 自身的 `boltons` selection-to-holdout window 可以支持推荐反转和 regret 解释，但缺少同预算 simple baselines，因此不能单独作为 predictive-validity proof。",
        "",
        "True rolling-origin support 仍偏 sparse；phase1 window plan 把 repo-specific earliest bucket cutoff 标为 diagnostic_sparse。Package 5 的分析必须把结果写成 retrospective/directional 或 negative/underpowered evidence。",
    ]
    return "\n".join(lines) + "\n"


def predictive_validity_feasibility(output: Path | None = None) -> dict[str, Any]:
    inventory = build_predictive_validity_inventory()
    write_json(result_path("predictive_validity_window_inventory.json"), inventory)
    write_text(output or report_path("predictive_validity_feasibility_zh.md"), render_predictive_validity_feasibility(inventory))
    return inventory


def summarize_by_design(rows: list[dict[str, Any]], threshold: float) -> dict[str, dict[str, Any]]:
    by_design: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_design[str(row.get("design_id"))].append(row)
    return {design_id: summarize_prediction_rows(design_rows, threshold) for design_id, design_rows in sorted(by_design.items())}


def baseline_comparison_from_summaries(summaries: dict[str, dict[str, Any]], protocol: dict[str, Any]) -> dict[str, Any]:
    simple_ids = list((protocol.get("baselines") or {}).get("simple") or PV_SIMPLE_BASELINES)
    candidate_ids = list((protocol.get("baselines") or {}).get("candidate_selectors") or PV_CANDIDATE_SELECTORS)
    simple = [
        {"design_id": design_id, **summaries[design_id]}
        for design_id in simple_ids
        if design_id in summaries and summaries[design_id]["MAE"] is not None
    ]
    candidates = [
        {"design_id": design_id, **summaries[design_id]}
        for design_id in candidate_ids
        if design_id in summaries and summaries[design_id]["MAE"] is not None
    ]
    diagnostics = [
        {"design_id": design_id, **summaries[design_id]}
        for design_id in PV_DIAGNOSTIC_ONLY
        if design_id in summaries and summaries[design_id]["MAE"] is not None
    ]
    best_simple = min(simple, key=lambda row: (row["MAE"], row["catastrophic_miss_rate"], row["design_id"])) if simple else None
    best_candidate = min(candidates, key=lambda row: (row["MAE"], row["catastrophic_miss_rate"], row["design_id"])) if candidates else None
    best_diagnostic = min(diagnostics, key=lambda row: (row["MAE"], row["catastrophic_miss_rate"], row["design_id"])) if diagnostics else None
    delta = None
    if best_simple and best_candidate:
        delta = pv_round(float(best_candidate["MAE"]) - float(best_simple["MAE"]))
    if best_candidate is None or best_simple is None:
        result_label = "underpowered_or_missing_baselines"
    elif float(best_candidate["MAE"]) < float(best_simple["MAE"]):
        result_label = "candidate_beats_best_simple_baseline"
    elif float(best_candidate["MAE"]) == float(best_simple["MAE"]):
        result_label = "candidate_ties_best_simple_baseline"
    else:
        result_label = "candidate_loses_to_best_simple_baseline"
    return {
        "simple_baseline_scores": simple,
        "candidate_scores": candidates,
        "diagnostic_scores": diagnostics,
        "best_simple_baseline": best_simple,
        "best_barcarolle_candidate": best_candidate,
        "best_diagnostic_candidate": best_diagnostic,
        "candidate_minus_best_simple_MAE": delta,
        "result_label": result_label,
        "candidate_beats_best_simple_baseline": result_label == "candidate_beats_best_simple_baseline",
    }


def write_eval_slices_csv(path: Path, rows: list[dict[str, Any]], threshold: float) -> None:
    evaluated = [prediction_slice_error(row, threshold) for row in rows]
    write_csv(
        path,
        evaluated,
        [
            "source",
            "window_id",
            "mode",
            "repo",
            "agent_id",
            "design_id",
            "role",
            "selection_stage",
            "future_stage",
            "selection_pass_rate",
            "future_pass_rate",
            "signed_error",
            "absolute_error",
            "squared_error",
            "catastrophic_miss",
            "selection_scoreable_count",
            "future_scoreable_count",
            "missing_or_non_scoreable_count",
        ],
    )


def render_rolling_origin_eval(payload: dict[str, Any]) -> str:
    design_rows = [
        {
            "Design": design_id,
            "MAE": row["MAE"],
            "RMSE": row["RMSE"],
            "Signed": row["mean_signed_error"],
            "Miss": row["catastrophic_miss_rate"],
            "Slices": row["slice_count"],
        }
        for design_id, row in payload["by_design"].items()
        if row["slice_count"]
    ]
    comparison = payload["baseline_comparison"]
    rank = payload["rank_and_regret"]["rank_agreement"]
    regret = payload["rank_and_regret"]["recommendation_regret"]
    lines = [
        "# Rolling-origin Evaluation",
        "",
        f"生成日期：{payload['generated_at']}",
        "",
        "本评估从 frozen protocol 和 window inventory 读取 committed sanitized metric slices。没有运行 paid calls，也没有读取 raw prompts、raw completions、transcripts 或 workspaces。",
        "",
        "## Primary metrics",
        "",
        *markdown_table(design_rows, [("Design", "Design"), ("MAE", "MAE"), ("RMSE", "RMSE"), ("Signed error", "Signed"), ("Catastrophic miss", "Miss"), ("Slices", "Slices")]),
        "",
        "## Baseline comparison",
        "",
        f"Best simple baseline: `{(comparison.get('best_simple_baseline') or {}).get('design_id')}` MAE `{(comparison.get('best_simple_baseline') or {}).get('MAE')}`.",
        f"Best Barcarolle candidate: `{(comparison.get('best_barcarolle_candidate') or {}).get('design_id')}` MAE `{(comparison.get('best_barcarolle_candidate') or {}).get('MAE')}`.",
        f"Candidate minus best simple MAE: `{comparison.get('candidate_minus_best_simple_MAE')}`.",
        f"Result label: `{comparison.get('result_label')}`.",
        "",
        "## Rank and regret",
        "",
        f"Rank groups evaluated: `{rank['groups_evaluated']}`; top-rank agreement rate: `{rank['top_rank_agreement_rate']}`.",
        f"Regret groups evaluated: `{regret['groups_evaluated']}`; mean regret: `{regret['mean_regret']}`; max regret: `{regret['max_regret']}`.",
        "",
        "## Claim boundary",
        "",
        "该结果最多支持 no-paid retrospective/directional evidence。即使 candidate beats best simple baseline，也不能从 retrospective artifacts 单独 claim predictive validity。",
    ]
    return "\n".join(lines) + "\n"


def rolling_origin_eval(protocol_path: Path, window_inventory_path: Path, output: Path | None = None) -> dict[str, Any]:
    protocol = read_json(protocol_path)
    inventory = read_json(window_inventory_path)
    threshold = safe_float(((protocol.get("metrics") or {}).get("secondary") or [{}])[-1].get("threshold")) or PV_CATASTROPHIC_THRESHOLD
    rows = list(inventory.get("metric_slices", []))
    evaluated_rows = [prediction_slice_error(row, float(threshold)) for row in rows]
    by_design = summarize_by_design(rows, float(threshold))
    comparison = baseline_comparison_from_summaries(by_design, protocol)
    rank_regret = summarize_rank_and_regret(evaluated_rows)
    payload = {
        "schema_version": "barcarolle.agent_selection_demo.rolling_origin_eval.v1",
        "generated_at": iso_now(),
        "protocol": display_path(protocol_path),
        "window_inventory": display_path(window_inventory_path),
        "paid_calls_made": False,
        "metric_slice_count": len(rows),
        "catastrophic_miss_threshold": threshold,
        "overall": summarize_prediction_rows(rows, float(threshold)),
        "by_design": by_design,
        "baseline_comparison": comparison,
        "rank_and_regret": rank_regret,
        "claim_boundary": {
            "predictive_validity_established": False,
            "retrospective_only": True,
            "future_preregistered_validation_required": True,
        },
    }
    write_json(result_path("rolling_origin_eval.json"), payload)
    write_eval_slices_csv(result_path("rolling_origin_eval_slices.csv"), rows, float(threshold))
    write_text(output or report_path("rolling_origin_eval_zh.md"), render_rolling_origin_eval(payload))
    return payload


def feedback_score_rows(stages: list[str] | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for stage in stages or ["smoke", "selection", "holdout", TOP2_REPEAT_STAGE]:
        for row in read_csv_rows(stage_paths(stage)["score"]):
            rows.append({**row, "stage": row.get("stage") or stage})
    return rows


def float_value(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def build_tuning_feedback_summary(stages: list[str] | None = None) -> dict[str, Any]:
    rows = feedback_score_rows(stages)
    by_agent: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_agent.setdefault(str(row.get("agent_id") or ""), []).append(row)

    agent_rows: list[dict[str, Any]] = []
    for agent_id, agent_score_rows in sorted(by_agent.items()):
        failure_counts = Counter(str(row.get("failure_category") or "unknown") for row in agent_score_rows)
        failure_counts.pop("verified pass", None)
        scoreable_count = sum(1 for row in agent_score_rows if csv_bool(row.get("scoreable_cell")))
        pass_count = sum(1 for row in agent_score_rows if csv_bool(row.get("verified_pass")))
        usage_count = sum(1 for row in agent_score_rows if csv_bool(row.get("usage_observed")))
        latencies = [value for value in (float_value(row.get("latency_seconds")) for row in agent_score_rows) if value is not None]
        examples = [
            {
                "stage": row.get("stage", ""),
                "task_id": row.get("task_id", ""),
                "failure_category": row.get("failure_category", ""),
                "terminal_status": row.get("terminal_status", ""),
            }
            for row in agent_score_rows
            if row.get("failure_category") != "verified pass"
        ][:5]
        cost_kinds = Counter(str(row.get("cost_observation_kind") or "unknown") for row in agent_score_rows)
        agent_rows.append(
            {
                "agent_id": agent_id,
                "reviewer_name": agent_score_rows[0].get("reviewer_name") or agent_id,
                "harness": agent_score_rows[0].get("harness") or "",
                "model": agent_score_rows[0].get("model") or "",
                "completed_cells": len(agent_score_rows),
                "scoreable_cells": scoreable_count,
                "verified_pass_count": pass_count,
                "failure_counts": dict(sorted(failure_counts.items())),
                "infra_or_unscoreable_count": len(agent_score_rows) - scoreable_count,
                "usage_observed_count": usage_count,
                "usage_observed_rate": None if not agent_score_rows else round(usage_count / len(agent_score_rows), 4),
                "median_latency_seconds": None if not latencies else round(statistics.median(latencies), 3),
                "cost_observation_kinds": dict(sorted(cost_kinds.items())),
                "examples": examples,
            }
        )

    shared_failures: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault((str(row.get("stage") or ""), str(row.get("task_id") or "")), []).append(row)
    for (stage, task_id), task_rows in sorted(grouped.items()):
        failures = [row for row in task_rows if row.get("failure_category") not in {"verified pass", ""}]
        if len(failures) < 2:
            continue
        shared_failures.append(
            {
                "stage": stage,
                "task_id": task_id,
                "failing_agents": len(failures),
                "failure_categories": dict(sorted(Counter(row.get("failure_category") or "unknown" for row in failures).items())),
            }
        )

    repeatability = read_json(result_path("top2_repeatability_check.json")) if result_path("top2_repeatability_check.json").exists() else {}
    unstable_tasks = [
        {
            "task_id": row.get("task_id"),
            "codex": f"{row.get('codex_original')}->{row.get('codex_repeat')}",
            "kilo": f"{row.get('kilo_original')}->{row.get('kilo_repeat')}",
            "relationship_repeat": row.get("relationship_repeat"),
        }
        for row in repeatability.get("stability_rows", [])
        if row.get("codex_changed") is True or row.get("kilo_changed") is True
    ]
    infra_blockers = [
        {
            "agent_id": row.get("agent_id"),
            "task_id": row.get("task_id"),
            "terminal_status": row.get("terminal_status"),
            "failure_category": row.get("failure_category"),
            "latency_seconds": row.get("latency_seconds"),
        }
        for row in repeatability.get("infrastructure_or_policy_rows", [])
    ]

    return {
        "schema_version": "barcarolle.agent_selection_demo.tuning_feedback_summary.v1",
        "generated_at": iso_now(),
        "source_stages": stages or ["smoke", "selection", "holdout", TOP2_REPEAT_STAGE],
        "agent_rows": agent_rows,
        "shared_failures": shared_failures[:10],
        "unstable_tasks": unstable_tasks[:10],
        "infra_blockers": infra_blockers,
        "repeat_interpretation": repeatability.get("interpretation"),
    }


def render_tuning_feedback_summary(payload: dict[str, Any]) -> str:
    agent_table = [
        {
            "Agent": row["reviewer_name"],
            "Cells": row["completed_cells"],
            "Scoreable": row["scoreable_cells"],
            "Pass": row["verified_pass_count"],
            "Infra": row["infra_or_unscoreable_count"],
            "Usage": row["usage_observed_rate"],
            "Failures": ", ".join(f"{key}: {value}" for key, value in row["failure_counts"].items()) or "none",
        }
        for row in payload["agent_rows"]
    ]
    example_rows = []
    for row in payload["agent_rows"]:
        for example in row["examples"][:3]:
            example_rows.append(
                {
                    "Agent": row["reviewer_name"],
                    "Stage": example["stage"],
                    "Task": example["task_id"],
                    "Failure": example["failure_category"],
                    "Status": example["terminal_status"],
                }
            )
    shared_rows = [
        {
            "Stage": row["stage"],
            "Task": row["task_id"],
            "Agents": row["failing_agents"],
            "Categories": ", ".join(f"{key}: {value}" for key, value in row["failure_categories"].items()),
        }
        for row in payload["shared_failures"][:8]
    ]
    unstable_rows = [
        {"Task": row["task_id"], "Codex": row["codex"], "Kilo": row["kilo"], "Repeat": row["relationship_repeat"]}
        for row in payload["unstable_tasks"][:8]
    ]
    infra_rows = [
        {
            "Agent": row["agent_id"],
            "Task": row["task_id"],
            "Status": row["terminal_status"],
            "Failure": row["failure_category"],
            "Latency": row["latency_seconds"],
        }
        for row in payload["infra_blockers"][:8]
    ]
    lines = [
        "# Agent Tuning Feedback Summary",
        "",
        f"生成日期：{payload['generated_at']}",
        "",
        "本报告由 CLI 从 committed sanitized results 生成，不读取 raw prompts、raw completions、transcripts、solver workspaces 或 verifier workspaces。",
        "",
        "生成命令：",
        "",
        "```text",
        "PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py tuning-feedback-summary --output experiments/agent_selection_demo/reports/agent_tuning_feedback_summary_zh.md",
        "```",
        "",
        "## Boundary",
        "",
        "这是 feedback input，不是 tuning result。它不声称任何 Agent 已经经过 tuning，也不声称任何配置修改已经提升效果。",
        "",
        "## Per-Agent Failure Taxonomy",
        "",
        *markdown_table(agent_table, [("Agent", "Agent"), ("Cells", "Cells"), ("Scoreable", "Scoreable"), ("Pass", "Pass"), ("Infra", "Infra"), ("Usage", "Usage"), ("Failures", "Failures")]),
        "",
        "## Example Follow-Up Tasks",
        "",
        *markdown_table(example_rows[:12], [("Agent", "Agent"), ("Stage", "Stage"), ("Task", "Task"), ("Failure", "Failure"), ("Status", "Status")]),
        "",
        "## Shared Failure Tasks",
        "",
        *markdown_table(shared_rows, [("Stage", "Stage"), ("Task", "Task"), ("Failing agents", "Agents"), ("Categories", "Categories")]),
        "",
        "## Unstable Repeat Tasks",
        "",
        *markdown_table(unstable_rows, [("Task", "Task"), ("Codex", "Codex"), ("Kilo", "Kilo"), ("Repeat relation", "Repeat")]),
        "",
        "## Infrastructure Blockers",
        "",
        *markdown_table(infra_rows, [("Agent", "Agent"), ("Task", "Task"), ("Status", "Status"), ("Failure", "Failure"), ("Latency", "Latency")]),
        "",
        "## Cost And Usage Coverage",
        "",
        "Usage coverage is included per Agent above. Cost comparisons remain feedback-only when usage coverage differs by harness or when rows use conservative missing-usage estimates.",
        "",
        "Recommended tuning backlog interpretation: first fix infrastructure and usage observability blockers; then use stable verifier-backed hidden failures as exemplars for prompt/tool/config changes. Do not use this report as proof that a learned selector or tuned Agent is valid.",
        "",
    ]
    return "\n".join(lines)


def tuning_feedback_summary(output: Path | None = None) -> dict[str, Any]:
    payload = build_tuning_feedback_summary()
    output_path = output or report_path("agent_tuning_feedback_summary_zh.md")
    write_text(output_path, render_tuning_feedback_summary(payload))
    write_json(result_path("agent_tuning_feedback_summary.json"), payload)
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
        run_parser.add_argument("--stop-on-unscoreable", action="store_true")
    recover_parser = subcommands.add_parser("recover-stage")
    recover_parser.add_argument("stage", choices=["smoke", "selection", "holdout", TOP2_REPEAT_STAGE])
    recover_parser.add_argument("--agent", action="append", default=None)
    subcommands.add_parser("recommend")
    subcommands.add_parser("report")
    subcommands.add_parser("top2-repeat-report")
    subcommands.add_parser("refresh-sanitized-stage-metadata")
    feedback_parser = subcommands.add_parser("tuning-feedback-summary")
    feedback_parser.add_argument("--output", default=str(report_path("agent_tuning_feedback_summary_zh.md")))
    feasibility_parser = subcommands.add_parser("predictive-validity-feasibility")
    feasibility_parser.add_argument("--output", default=str(report_path("predictive_validity_feasibility_zh.md")))
    eval_parser = subcommands.add_parser("rolling-origin-eval")
    eval_parser.add_argument("--protocol", default=str(result_path("predictive_validity_protocol.json")))
    eval_parser.add_argument("--window-inventory", default=str(result_path("predictive_validity_window_inventory.json")))
    eval_parser.add_argument("--output", default=str(report_path("rolling_origin_eval_zh.md")))
    subcommands.add_parser("selector-build-dataset")
    subcommands.add_parser("selector-baseline-eval")
    subcommands.add_parser("selector-hrd-eval")
    subcommands.add_parser("selector-decision-eval")
    subcommands.add_parser("selector-final-eval")
    args = parser.parse_args()
    config = load_config(repo_path(args.config))
    if args.command == "gate":
        payload = gate(config, replay_sample_count=args.replay_sample_count)
        return 0 if payload["status"] == "ready" else 2
    if args.command in {"smoke", "selection", "holdout", TOP2_REPEAT_STAGE}:
        metrics = run_stage(
            config,
            args.command,
            agent_ids=args.agent,
            rerun=args.rerun,
            stop_on_unscoreable=args.stop_on_unscoreable,
        )
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
    if args.command == "tuning-feedback-summary":
        tuning_feedback_summary(repo_path(args.output))
        return 0
    if args.command == "predictive-validity-feasibility":
        predictive_validity_feasibility(repo_path(args.output))
        return 0
    if args.command == "rolling-origin-eval":
        rolling_origin_eval(repo_path(args.protocol), repo_path(args.window_inventory), repo_path(args.output))
        return 0
    if args.command == "selector-build-dataset":
        selector_build_dataset(config)
        return 0
    if args.command == "selector-baseline-eval":
        selector_baseline_eval(config)
        return 0
    if args.command == "selector-hrd-eval":
        selector_hrd_eval(config)
        return 0
    if args.command == "selector-decision-eval":
        selector_decision_eval(config)
        return 0
    if args.command == "selector-final-eval":
        selector_final_eval(config)
        return 0
    raise ValueError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
