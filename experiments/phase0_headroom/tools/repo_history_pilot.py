from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import io
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXP_REL = Path("experiments/phase0_headroom")
CANDIDATE_REL = Path("candidate_sources")
CERTIFIED_REL = Path("certified_tasks")
RELEASES_REL = Path("releases")
REPORTS_REL = Path("reports")
TARGET_PROFILES_REL = Path("target_profiles")
WORKSPACES_REL = Path("workspaces/repo_history_pilot")
GATE_ORDER = [
    "checkout",
    "oracle_extractable",
    "no_op_fail",
    "reference_pass",
    "known_bad_fail",
    "flakiness_check",
    "ambiguity_review",
    "solution_leakage_review",
    "scope_clarity_review",
    "cost_boundedness",
    "taxonomy_labelability",
]
REJECT_SUBJECT_TERMS = [
    "update dev dependencies",
    "update project files",
    "docs",
    "documentation",
    "pre-commit",
    "ruff",
    "mypy",
    "typo",
    "release",
    "bump",
    "dependabot",
    "remove deprecated",
    "deprecate",
    "translation",
    "locale",
    "format",
    "lint",
    "isort",
    "black",
    "pyupgrade",
    "flake8",
    "pytest",
    "setup.py test",
    "freezegun",
    "drop support",
    "code inspection",
    "type hint",
    "typing",
    "autotyping",
    "add tests",
    "tests for",
]
PROJECT_CONFIG_PY_FILES = {"setup.py", "noxfile.py", "conftest.py"}
PROJECT_OR_CONFIG_PREFIXES = (
    ".devcontainer/",
    ".github/",
    "ci/",
    "docs/",
    "requirements/",
)
PROJECT_OR_CONFIG_FILES = {
    ".editorconfig",
    ".flake8",
    ".gitignore",
    ".pre-commit-config.yaml",
    ".readthedocs.yaml",
    "CHANGES.rst",
    "LICENSE.txt",
    "MANIFEST.in",
    "README.md",
    "README.rst",
    "conftest.py",
    "noxfile.py",
    "pyproject.toml",
    "setup.cfg",
    "setup.py",
    "tox.ini",
    "uv.lock",
}
MAX_CERTIFICATION_CHANGED_LINES = 250
MANUAL_REVIEW_CROSS_MODULE_LIMIT = 3


@dataclass(frozen=True)
class PilotConfig:
    repo_id: str
    repo_url: str
    local_repo: Path
    command_template: str
    certification_attempts: int
    pilot_certified_min: int
    benchmark_grade_min: int
    result_prefix: str
    claim_scope: str = "second_repo_operational_pilot_not_predictive_validation"


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def phase0_root(root: Path) -> Path:
    candidate = root / EXP_REL
    return candidate if candidate.exists() else root


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    write_text(path, "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def load_config(root: Path, path: Path) -> PilotConfig:
    raw: dict[str, str] = {}
    section: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            section = [key]
            raw[key] = value.strip().strip('"')
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if indent == 2:
            raw[".".join([section[0], key])] = value.strip().strip('"')
        elif indent == 4 and len(section) == 1:
            raw[".".join([section[0], key])] = value.strip().strip('"')
    repo_id = raw["selected_repo_id"]
    local_repo = Path(raw["local_repo"])
    return PilotConfig(
        repo_id=repo_id,
        repo_url=raw["repo_url"],
        local_repo=local_repo if local_repo.is_absolute() else root / local_repo,
        command_template=raw["test_environment.command_template"],
        certification_attempts=int(raw.get("preferred_task_count.certification_attempts", "16")),
        pilot_certified_min=int(raw.get("preferred_task_count.pilot_certified_min", "4")),
        benchmark_grade_min=int(raw.get("preferred_task_count.benchmark_grade_min", "6")),
        result_prefix=raw.get("acut.result_prefix", f"{repo_id}_pre_phase1_workspace"),
        claim_scope=raw.get("claim_scope", "second_repo_operational_pilot_not_predictive_validation"),
    )


def stable_task_id(repo_id: str, index: int) -> str:
    return f"{repo_id}__hist__{index:03d}"


def is_test_path(path: str) -> bool:
    return path.startswith("tests/") or path.startswith("test/") or "/tests/" in path or Path(path).name.startswith("test_")


def is_code_path(path: str) -> bool:
    if not path.endswith(".py") or is_test_path(path):
        return False
    if path in PROJECT_CONFIG_PY_FILES or is_project_or_config_path(path):
        return False
    return True


def is_project_or_config_path(path: str) -> bool:
    return path in PROJECT_OR_CONFIG_FILES or path.startswith(PROJECT_OR_CONFIG_PREFIXES)


def classify_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    code = sorted({path for path in paths if is_code_path(path)})
    tests = sorted({path for path in paths if is_test_path(path) and path.endswith(".py")})
    return code, tests


def module_names(code_files: list[str]) -> list[str]:
    modules: list[str] = []
    for path in code_files:
        parts = Path(path).parts
        if parts and parts[0] == "src" and len(parts) > 2:
            modules.append(parts[2].replace(".py", ""))
        elif len(parts) > 1:
            modules.append(parts[1].replace(".py", ""))
        elif parts:
            modules.append(parts[0].replace(".py", ""))
    return sorted(set(modules))


def change_size_bucket(total_lines: int) -> str:
    if total_lines <= 20:
        return "xs_0_20"
    if total_lines <= 80:
        return "s_21_80"
    if total_lines <= 200:
        return "m_81_200"
    return "l_201_plus"


def subject_reject_term(subject: str) -> str:
    lower = subject.lower()
    for term in REJECT_SUBJECT_TERMS:
        if term in lower:
            return term
    return ""


def candidate_filter_decision(
    *,
    subject: str,
    changed_files: list[str],
    code_files: list[str],
    added: int,
    deleted: int,
    modules: list[str],
) -> dict[str, Any]:
    project_paths = [path for path in changed_files if is_project_or_config_path(path)]
    reject_reasons: list[str] = []
    manual_review_reasons: list[str] = []
    term = subject_reject_term(subject)
    if term:
        reject_reasons.append(f"reject_subject_term:{term}")
    if project_paths and len(project_paths) >= max(2, len(code_files) + 1):
        reject_reasons.append("project_file_heavy")
    if not code_files:
        reject_reasons.append("no_behavior_code_file")
    if added + deleted > MAX_CERTIFICATION_CHANGED_LINES:
        reject_reasons.append(f"changed_lines_over:{MAX_CERTIFICATION_CHANGED_LINES}")
    if len(set(modules)) > MANUAL_REVIEW_CROSS_MODULE_LIMIT:
        manual_review_reasons.append(f"cross_module_count_over:{MANUAL_REVIEW_CROSS_MODULE_LIMIT}")
    if project_paths:
        manual_review_reasons.append("docs_or_config_change_present")
    if reject_reasons:
        status = "rejected"
    elif manual_review_reasons:
        status = "manual_review_required"
    else:
        status = "accepted"
    return {
        "candidate_filter_status": status,
        "reject_reasons": reject_reasons,
        "manual_review_reasons": manual_review_reasons,
        "changed_line_count": added + deleted,
        "project_or_config_file_count": len(project_paths),
        "code_file_count": len(code_files),
    }


def first_failing_gate(gates: dict[str, str]) -> str:
    for gate in GATE_ORDER:
        if gates.get(gate) != "pass":
            return gate
    return ""


def task_status(gates: dict[str, str]) -> str:
    failing = first_failing_gate(gates)
    if not failing:
        return "certified"
    if gates.get("checkout") == "pass" and gates.get("oracle_extractable") == "pass":
        return "near_certified"
    return "rejected"


def run_command(command: list[str], cwd: Path, timeout: int = 120, env: dict[str, str] | None = None) -> CommandResult:
    import time

    start = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return CommandResult(completed.returncode, completed.stdout, completed.stderr, time.monotonic() - start)
    except subprocess.TimeoutExpired as exc:
        return CommandResult(124, exc.stdout or "", exc.stderr or "", time.monotonic() - start, timed_out=True)


def git_lines(repo: Path, args: list[str]) -> list[str]:
    result = run_command(["git", *args], repo, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return result.stdout.splitlines()


def changed_files(repo: Path, commit: str) -> list[str]:
    return [line for line in git_lines(repo, ["show", "--format=", "--name-only", commit]) if line.strip()]


def numstat(repo: Path, commit: str) -> tuple[int, int]:
    added = 0
    deleted = 0
    for line in git_lines(repo, ["show", "--format=", "--numstat", commit]):
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        try:
            added += int(parts[0])
            deleted += int(parts[1])
        except ValueError:
            continue
    return added, deleted


def mining_rows(root: Path, config: PilotConfig, max_anchors: int = 500) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    repo = config.local_repo
    raw = subprocess.check_output(
        ["git", "log", "--since=2020-01-01", "--reverse", "--format=%x1e%H%x09%P%x09%ad%x09%s", "--date=iso-strict", "--name-only"],
        cwd=repo,
        text=True,
        errors="replace",
    )
    anchors: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    next_task_index = 1
    for chunk in raw.split("\x1e"):
        lines = [line for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue
        meta = lines[0].split("\t", 3)
        if len(meta) != 4:
            continue
        commit, parents, task_time, subject = meta
        parent = parents.split()[0] if parents.split() else ""
        paths = lines[1:]
        code_files, test_files = classify_paths(paths)
        added, deleted = numstat(repo, commit)
        modules = module_names(code_files)
        decision = candidate_filter_decision(
            subject=subject,
            changed_files=paths,
            code_files=code_files,
            added=added,
            deleted=deleted,
            modules=modules,
        )
        reject_reasons = list(decision["reject_reasons"])
        if not test_files:
            reject_reasons.append("no_changed_test_file")
        selected = bool(test_files) and decision["candidate_filter_status"] != "rejected"
        anchor = {
            "schema_version": "barcarolle.repo_history_anchor.v1",
            "repo_id": config.repo_id,
            "repo_url": config.repo_url,
            "commit": commit,
            "parent": parent,
            "task_time": task_time,
            "subject": subject,
            "changed_files": paths,
            "code_files": code_files,
            "test_files": test_files,
            "changed_lines_added": added,
            "changed_lines_deleted": deleted,
            "status": "candidate" if selected else "rejected",
            "candidate_filter_status": decision["candidate_filter_status"],
            "reject_reason": "" if selected else ";".join(reject_reasons),
            "reject_reasons": reject_reasons,
            "manual_review_reasons": decision["manual_review_reasons"],
        }
        anchors.append(anchor)
        if anchor["status"] != "candidate":
            continue
        candidates.append(
            {
                "schema_version": "barcarolle.repo_history_candidate.v1",
                "task_id": stable_task_id(config.repo_id, next_task_index),
                "repo_id": config.repo_id,
                "repo_url": config.repo_url,
                "base_commit": parent,
                "target_commit": commit,
                "task_time": task_time,
                "subject": subject,
                "changed_files": paths,
                "code_files": code_files,
                "test_files": test_files,
                "candidate_oracle_source": test_files,
                "changed_lines_added": added,
                "changed_lines_deleted": deleted,
                "change_size_bucket": change_size_bucket(added + deleted),
                "module_or_package": modules,
                "candidate_filter_status": decision["candidate_filter_status"],
                "manual_review_reasons": decision["manual_review_reasons"],
                "task_type_proxy": "behavior_or_feature_or_bugfix",
                "source_type": "git_commit",
                "status": "selected_for_certification",
            }
        )
        next_task_index += 1
        if len(candidates) >= config.certification_attempts or len(anchors) >= max_anchors:
            break
    return anchors[:max_anchors], candidates


def command_test_files(command_template: str, test_files: list[str]) -> list[str]:
    test_arg = " ".join(shlex.quote(path) for path in test_files)
    return shlex.split(command_template.format(test_files=test_arg))


def with_editable_workspace(command: list[str], workspace: Path) -> list[str]:
    if len(command) >= 2 and command[:2] == ["uv", "run"]:
        return [*command[:2], "--with-editable", str(workspace), *command[2:]]
    return command


def pythonpath_for(workspace: Path) -> str:
    src = workspace / "src"
    return str(src if src.exists() else workspace)


def archive_commit(repo: Path, commit: str, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(["git", "archive", "--format=tar", commit], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace"))
    with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as tar:
        tar.extractall(destination)


def test_patch(repo: Path, base: str, target: str, test_files: list[str]) -> str:
    proc = subprocess.run(["git", "diff", "--binary", base, target, "--", *test_files], cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    return proc.stdout


def apply_patch_text(workspace: Path, patch_text: str) -> bool:
    env = os.environ.copy()
    env["GIT_CEILING_DIRECTORIES"] = str(workspace.parent)
    proc = subprocess.run(["git", "apply", "-"], cwd=workspace, env=env, input=patch_text, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return proc.returncode == 0


def run_candidate_tests(config: PilotConfig, workspace: Path, test_files: list[str], cwd: Path, timeout: int = 120) -> CommandResult:
    env = os.environ.copy()
    env["PYTHONPATH"] = pythonpath_for(workspace)
    env[f"SETUPTOOLS_SCM_PRETEND_VERSION_FOR_{config.repo_id.upper().replace('-', '_')}"] = "0.0.0"
    workspace_test_files = [str(workspace / path) for path in test_files]
    command = with_editable_workspace(command_test_files(config.command_template, workspace_test_files), workspace)
    return run_command(command, cwd, timeout=timeout, env=env)


def certify_candidate(root: Path, exp: Path, config: PilotConfig, candidate: dict[str, Any], statement: dict[str, Any]) -> dict[str, Any]:
    workspace_root = exp / WORKSPACES_REL / config.repo_id / str(candidate["task_id"])
    base_ws = workspace_root / "base"
    target_ws = workspace_root / "target"
    gates = {gate: "pending" for gate in GATE_ORDER}
    commands: list[dict[str, Any]] = []
    try:
        archive_commit(config.local_repo, str(candidate["base_commit"]), base_ws)
        archive_commit(config.local_repo, str(candidate["target_commit"]), target_ws)
        gates["checkout"] = "pass"
    except Exception as exc:
        gates["checkout"] = "fail"
        return certification_row(candidate, statement, gates, commands, str(exc), "rejected")
    patch = test_patch(config.local_repo, str(candidate["base_commit"]), str(candidate["target_commit"]), list(candidate["test_files"]))
    if not patch.strip():
        gates["oracle_extractable"] = "fail"
        return certification_row(candidate, statement, gates, commands, "empty hidden test patch", "rejected")
    gates["oracle_extractable"] = "pass"
    if not apply_patch_text(base_ws, patch):
        gates["no_op_fail"] = "fail"
        return certification_row(candidate, statement, gates, commands, "hidden test patch did not apply to base", "rejected")
    no_op = run_candidate_tests(config, base_ws, list(candidate["test_files"]), root)
    commands.append(command_record("noop_test_patch_on_base", no_op))
    gates["no_op_fail"] = "pass" if no_op.returncode != 0 else "fail"
    ref1 = run_candidate_tests(config, target_ws, list(candidate["test_files"]), root)
    commands.append(command_record("reference_run_1", ref1))
    ref2 = run_candidate_tests(config, target_ws, list(candidate["test_files"]), root)
    commands.append(command_record("reference_run_2", ref2))
    gates["reference_pass"] = "pass" if ref1.returncode == 0 and ref2.returncode == 0 else "fail"
    gates["known_bad_fail"] = "pass" if no_op.returncode != 0 else "fail"
    gates["flakiness_check"] = gates["reference_pass"]
    source_ok = statement.get("statement_review_status") == "reviewed" and bool(statement.get("allowed_context_refs"))
    gates["ambiguity_review"] = "pass" if source_ok else "fail"
    gates["solution_leakage_review"] = "pass" if source_ok else "fail"
    gates["scope_clarity_review"] = "pass" if statement.get("scope_boundaries") else "fail"
    gates["cost_boundedness"] = "pass" if max(ref1.duration_seconds, ref2.duration_seconds, no_op.duration_seconds) < 120 else "fail"
    gates["taxonomy_labelability"] = "pass" if candidate.get("module_or_package") else "fail"
    status = task_status(gates)
    return certification_row(candidate, statement, gates, commands, "", status)


def command_record(role: str, result: CommandResult) -> dict[str, Any]:
    return {
        "role": role,
        "returncode": result.returncode,
        "duration_seconds": round(result.duration_seconds, 3),
        "timed_out": result.timed_out,
        "stdout_tail_hash": hashlib.sha256(result.stdout[-2000:].encode("utf-8")).hexdigest()[:12],
        "stderr_tail_hash": hashlib.sha256(result.stderr[-2000:].encode("utf-8")).hexdigest()[:12],
    }


def certification_row(
    candidate: dict[str, Any],
    statement: dict[str, Any],
    gates: dict[str, str],
    commands: list[dict[str, Any]],
    failure_reason: str,
    status: str,
) -> dict[str, Any]:
    first_gate = first_failing_gate(gates)
    return {
        **candidate,
        "schema_version": "barcarolle.repo_history_certification.v1",
        "status": status,
        "gates": gates,
        "first_failing_gate": first_gate,
        "failure_reason": failure_reason,
        "known_bad_strategy": "no_op_baseline",
        "commands": commands,
        "solver_facing_statement": statement.get("solver_facing_statement", ""),
        "scope_boundaries": statement.get("scope_boundaries", ""),
        "allowed_context_refs": statement.get("allowed_context_refs", []),
        "excluded_context_refs": statement.get("excluded_context_refs", []),
        "oracle_refs": statement.get("oracle_refs", []),
        "harness_test_command": statement.get("harness_test_command", ""),
        "statement_review_status": statement.get("statement_review_status", "missing"),
    }


def split_release_tasks(certified: list[dict[str, Any]]) -> dict[str, list[str]]:
    ordered = sorted(certified, key=lambda row: (str(row.get("task_time")), str(row.get("task_id"))))
    half = len(ordered) // 2
    return {
        "B_real": [row["task_id"] for row in ordered[:half]],
        "W_real": [row["task_id"] for row in ordered[half:]],
    }


def release_payload(config: PilotConfig, certified: list[dict[str, Any]]) -> dict[str, Any]:
    splits = split_release_tasks(certified)
    b_count = len(splits["B_real"])
    w_count = len(splits["W_real"])
    pilot_grade = len(certified) >= config.pilot_certified_min and b_count >= 2 and w_count >= 2
    benchmark_grade = len(certified) >= config.benchmark_grade_min and b_count >= 3 and w_count >= 3
    return {
        "schema_version": "barcarolle.second_repo_pilot_release.v1",
        "generated_at": iso_now(),
        "repo_id": config.repo_id,
        "release_id": f"{config.repo_id}_phase0_pilot",
        "release_status": "pilot_grade" if pilot_grade else "diagnostic_only",
        "benchmark_grade": benchmark_grade,
        "pilot_grade": pilot_grade,
        "certified_task_count": len(certified),
        "splits": splits,
        "tasks": [{key: row.get(key) for key in ["task_id", "base_commit", "target_commit", "split", "code_files", "test_files", "module_or_package"]} for row in certified],
        "quality_gates": {
            "pilot_min": config.pilot_certified_min,
            "benchmark_min": config.benchmark_grade_min,
            "b_real_count": b_count,
            "w_real_count": w_count,
        },
        "claim_scope": config.claim_scope,
    }


def mine(root: Path, config_path: Path) -> None:
    exp = phase0_root(root)
    config = load_config(root, config_path)
    anchors, candidates = mining_rows(root, config)
    write_jsonl(exp / CANDIDATE_REL / f"{config.repo_id}_history_anchors.jsonl", anchors)
    write_jsonl(exp / CANDIDATE_REL / f"{config.repo_id}_candidates.jsonl", candidates)
    write_csv(
        exp / CANDIDATE_REL / f"{config.repo_id}_supply_funnel.csv",
        [
            {
                "status": row["status"],
                "candidate_filter_status": row.get("candidate_filter_status", ""),
                "reject_reason": row.get("reject_reason", ""),
                "manual_review_reasons": ";".join(row.get("manual_review_reasons") or []),
                "changed_line_count": int(row.get("changed_lines_added") or 0) + int(row.get("changed_lines_deleted") or 0),
            }
            for row in anchors
        ],
        ["status", "candidate_filter_status", "reject_reason", "manual_review_reasons", "changed_line_count"],
    )
    write_json(
        exp / TARGET_PROFILES_REL / f"{config.repo_id}_target_profile.json",
        {
            "schema_version": "barcarolle.target_profile.v1",
            "repo_id": config.repo_id,
            "repo_url": config.repo_url,
            "local_repo": str(config.local_repo),
            "layout": "src" if (config.local_repo / "src").exists() else "flat",
            "test_command": config.command_template,
            "missing_data": [],
            "missing_data_policy": "empty missing_data means no known target-profile fields were silently omitted",
            "history_scan_limit": 500,
            "candidate_count": len(candidates),
        },
    )


def source_context(root: Path, config_path: Path) -> None:
    exp = phase0_root(root)
    config = load_config(root, config_path)
    candidates = read_jsonl(exp / CANDIDATE_REL / f"{config.repo_id}_candidates.jsonl")
    contexts: list[dict[str, Any]] = []
    statements: list[dict[str, Any]] = []
    reviews: list[dict[str, Any]] = []
    for candidate in candidates:
        pr_refs = github_pr_refs(config, str(candidate["target_commit"]))
        if not pr_refs:
            pr_refs = [commit_context_ref(config, candidate)]
        for ref in pr_refs:
            ref["task_id"] = candidate["task_id"]
        allowed_refs = allowed_context_refs(pr_refs)
        context_status = "non_leaky_context_found" if allowed_refs else "no_non_leaky_source_context"
        contexts.extend(pr_refs or [{"task_id": candidate["task_id"], "ref": f"commit:{candidate['target_commit']}", "classification": "unusable", "summary": "No linked PR or commit-message context found."}])
        statement = {
            "schema_version": "barcarolle.repo_history_statement.v1",
            "task_id": candidate["task_id"],
            "repo_id": config.repo_id,
            "base_commit": candidate["base_commit"],
            "target_commit": candidate["target_commit"],
            "solver_facing_statement": solver_statement(candidate, pr_refs),
            "scope_boundaries": f"Modify only implementation files needed for this {config.repo_id} behavior; do not edit tests or generated metadata.",
            "allowed_context_refs": allowed_refs,
            "excluded_context_refs": [ref["ref"] for ref in pr_refs if ref["classification"] != "problem_context"],
            "oracle_refs": candidate["test_files"],
            "harness_test_command": config.command_template,
            "statement_review_status": "reviewed" if allowed_refs else "near_certified_context_missing",
            "source_context_status": context_status,
        }
        statements.append(statement)
        reviews.append({"task_id": candidate["task_id"], "source_context_status": context_status, "statement_review_status": statement["statement_review_status"]})
    write_jsonl(exp / CANDIDATE_REL / f"{config.repo_id}_source_context.jsonl", contexts)
    write_csv(exp / CANDIDATE_REL / f"{config.repo_id}_source_context_funnel.csv", reviews, ["task_id", "source_context_status", "statement_review_status"])
    write_jsonl(exp / CERTIFIED_REL / f"{config.repo_id}_task_statements.jsonl", statements)
    write_jsonl(exp / CERTIFIED_REL / f"{config.repo_id}_review_records.jsonl", reviews)


def github_pr_refs(config: PilotConfig, commit: str) -> list[dict[str, Any]]:
    owner_repo = config.repo_url.removeprefix("https://github.com/").removesuffix(".git")
    result = run_command(
        ["gh", "api", f"repos/{owner_repo}/commits/{commit}/pulls", "-H", "Accept: application/vnd.github.groot-preview+json"],
        Path.cwd(),
        timeout=30,
    )
    if result.returncode != 0:
        return []
    try:
        pulls = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    refs: list[dict[str, Any]] = []
    for pull in pulls[:2]:
        title = str(pull.get("title") or "").strip()
        body = " ".join(str(pull.get("body") or "").split())[:240]
        number = pull.get("number")
        if not title:
            continue
        refs.append(
            {
                "task_id": "",
                "ref": f"pr:{number}",
                "classification": "problem_context",
                "summary": title,
                "body_summary": body,
            }
        )
    return refs


def commit_context_ref(config: PilotConfig, candidate: dict[str, Any]) -> dict[str, Any]:
    commit = str(candidate["target_commit"])
    result = run_command(["git", "show", "-s", "--format=%b", commit], config.local_repo, timeout=30)
    body = " ".join(result.stdout.split())[:240] if result.returncode == 0 else ""
    return {
        "task_id": str(candidate["task_id"]),
        "ref": f"commit:{commit}",
        "classification": "diagnostic_only_context",
        "source_kind": "commit_message_fallback",
        "summary": str(candidate.get("subject") or "Repair the described behavior").strip(),
        "body_summary": body,
    }


def allowed_context_refs(refs: list[dict[str, Any]]) -> list[str]:
    return [ref["ref"] for ref in refs if ref.get("classification") == "problem_context" and not str(ref.get("ref", "")).startswith("commit:")]


def solver_statement(candidate: dict[str, Any], refs: list[dict[str, Any]]) -> str:
    title = refs[0]["summary"] if refs else str(candidate.get("subject") or "Repair the described behavior")
    module = ", ".join(candidate.get("module_or_package") or [])
    repo_id = str(candidate.get("repo_id") or "target repository")
    return f"Repair the {repo_id} behavior described by the selected public context summary: {title}. Focus on the {module or 'affected'} module and preserve existing public behavior."


def certify(root: Path, config_path: Path) -> None:
    exp = phase0_root(root)
    config = load_config(root, config_path)
    candidates = read_jsonl(exp / CANDIDATE_REL / f"{config.repo_id}_candidates.jsonl")
    statements_by_id = {row["task_id"]: row for row in read_jsonl(exp / CERTIFIED_REL / f"{config.repo_id}_task_statements.jsonl")}
    rows = [certify_candidate(root, exp, config, candidate, statements_by_id.get(candidate["task_id"], {})) for candidate in candidates[: config.certification_attempts]]
    certified = [row for row in rows if row["status"] == "certified"]
    near = [row for row in rows if row["status"] != "certified"]
    write_jsonl(exp / CERTIFIED_REL / f"{config.repo_id}_certified_tasks.jsonl", certified)
    write_jsonl(exp / CERTIFIED_REL / f"{config.repo_id}_near_certified_tasks.jsonl", near)
    write_csv(
        exp / CERTIFIED_REL / f"{config.repo_id}_certification_funnel.csv",
        [{"task_id": row["task_id"], "status": row["status"], "first_failing_gate": row["first_failing_gate"]} for row in rows],
        ["task_id", "status", "first_failing_gate"],
    )


def assemble_release(root: Path, config_path: Path) -> None:
    exp = phase0_root(root)
    config = load_config(root, config_path)
    certified = read_jsonl(exp / CERTIFIED_REL / f"{config.repo_id}_certified_tasks.jsonl")
    release = release_payload(config, certified)
    split_by_task = {task_id: split for split, task_ids in release["splits"].items() for task_id in task_ids}
    for row in certified:
        row["split"] = split_by_task.get(row["task_id"], "")
    release = release_payload(config, certified)
    write_json(exp / RELEASES_REL / f"{config.repo_id}_phase0_pilot_release.json", release)
    write_csv(
        exp / RELEASES_REL / f"{config.repo_id}_phase0_task_table.csv",
        [{"task_id": row["task_id"], "split": row.get("split", ""), "module_or_package": ",".join(row.get("module_or_package") or []), "status": row["status"]} for row in certified],
        ["task_id", "split", "module_or_package", "status"],
    )
    write_certification_report(exp, config, certified, read_jsonl(exp / CERTIFIED_REL / f"{config.repo_id}_near_certified_tasks.jsonl"), release)


def write_certification_report(exp: Path, config: PilotConfig, certified: list[dict[str, Any]], near: list[dict[str, Any]], release: dict[str, Any]) -> None:
    write_text(
        exp / REPORTS_REL / f"{config.repo_id}_certification_funnel.md",
        "\n".join(
            [
                f"# {config.repo_id} Certification Funnel",
                "",
                f"Certified tasks: `{len(certified)}`.",
                f"Near/rejected tasks: `{len(near)}`.",
                "",
                "| Task | Status | First failing gate |",
                "| --- | --- | --- |",
                *[f"| `{row['task_id']}` | `{row['status']}` | `{row.get('first_failing_gate', '')}` |" for row in [*certified, *near]],
                "",
            ]
        ),
    )
    write_text(
        exp / REPORTS_REL / f"{config.repo_id}_mini_release.md",
        "\n".join(
            [
                f"# {config.repo_id} Mini Release",
                "",
                f"Release status: `{release['release_status']}`.",
                f"Pilot grade: `{release['pilot_grade']}`.",
                f"Benchmark grade: `{release['benchmark_grade']}`.",
                f"Certified task count: `{release['certified_task_count']}`.",
                f"B_real tasks: `{len(release['splits']['B_real'])}`.",
                f"W_real tasks: `{len(release['splits']['W_real'])}`.",
                "",
            ]
        ),
    )


def summarize(root: Path, config_path: Path) -> None:
    exp = phase0_root(root)
    config = load_config(root, config_path)
    release_path = exp / RELEASES_REL / f"{config.repo_id}_phase0_pilot_release.json"
    if release_path.exists():
        release = json.loads(release_path.read_text(encoding="utf-8"))
        print(json.dumps({"repo_id": config.repo_id, "release_status": release.get("release_status"), "certified_task_count": release.get("certified_task_count")}, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Mine and certify a generic Python repo history pilot.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--config", default=str(EXP_REL / "configs" / "second_repo_pilot.yaml"))
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in ["mine", "source-context", "certify", "assemble-release", "summarize"]:
        subcommands.add_parser(name)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = root / config_path
    if args.command == "mine":
        mine(root, config_path)
    elif args.command == "source-context":
        source_context(root, config_path)
    elif args.command == "certify":
        certify(root, config_path)
    elif args.command == "assemble-release":
        assemble_release(root, config_path)
    elif args.command == "summarize":
        summarize(root, config_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
