#!/usr/bin/env python3
"""Materialize and smoke-test SymPy B task candidates from selected anchors."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from collections import Counter
from statistics import median
from pathlib import Path
from typing import Any, Mapping, Sequence

import external_calibrated_repository_admission as admission
from _common import ToolError, emit_json, fail, iso_now, load_manifest, write_json


TOOL = "external_calibrated_b_task_admission"
SCHEMA_VERSION = "external-calibrated-repo-benchmark.b-task-admission.v1"
PROTOCOL_ID = admission.PROTOCOL_ID
REPO_ROOT = admission.REPO_ROOT
PREPARE = REPO_ROOT / "experiments/core_narrative/tools/prepare_workspace.py"
APPLY_VERIFY = REPO_ROOT / "experiments/core_narrative/tools/apply_and_verify.py"
DEFAULT_SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/sympy"
DEFAULT_CANDIDATES = REPO_ROOT / "experiments/core_narrative/results/task_admission/sympy_b_anchor_selection_20260515.json"
DEFAULT_PRIVATE_ANCHORS = REPO_ROOT / "experiments/core_narrative/large_artifacts/external_calibrated_b_anchor_selection_20260515/private_anchor_map.json"
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/external_calibrated_b_task_admission_20260516"
DEFAULT_WORKSPACE_ROOT = REPO_ROOT / "experiments/core_narrative/workspaces/external_calibrated_b_task_admission_20260516"
DEFAULT_SHEETS_DIR = REPO_ROOT / "experiments/core_narrative/results/task_admission/sympy_b_candidate_sheets"
DEFAULT_SUMMARY = REPO_ROOT / "experiments/core_narrative/results/task_admission/sympy_b_admission_summary.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/sympy_b_task_generation_report.md"
DEFAULT_PRIMARY = REPO_ROOT / "experiments/core_narrative/configs/tasks/sympy_barcarolle_b_v1.yaml"
DEFAULT_RESERVE = REPO_ROOT / "experiments/core_narrative/configs/tasks/sympy_barcarolle_b_v1_reserve.yaml"
DEFAULT_VENV = REPO_ROOT / "experiments/core_narrative/cache/sympy_admission_venv/bin/python"
TEST_DEF_RE = re.compile(r"^\+\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)\s*\(")
TEST_HUNK_RE = re.compile(r"^@@.*@@\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)\s*\(")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", default=str(DEFAULT_SOURCE_REPO))
    parser.add_argument("--candidates", default=str(DEFAULT_CANDIDATES))
    parser.add_argument("--private-anchors", default=str(DEFAULT_PRIVATE_ANCHORS))
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT))
    parser.add_argument("--workspace-root", default=str(DEFAULT_WORKSPACE_ROOT))
    parser.add_argument("--sheets-dir", default=str(DEFAULT_SHEETS_DIR))
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--primary-manifest", default=str(DEFAULT_PRIMARY))
    parser.add_argument("--reserve-manifest", default=str(DEFAULT_RESERVE))
    parser.add_argument("--venv-python", default=str(DEFAULT_VENV))
    parser.add_argument("--primary-target", type=int, default=20)
    parser.add_argument("--reserve-target", type=int, default=10)
    parser.add_argument(
        "--candidate-pool-target",
        type=int,
        help="Freeze the first N accepted candidates as the generated B candidate universe after oversampled screening.",
    )
    parser.add_argument("--max-candidates", type=int, help="Limit admission run for smoke/debugging.")
    parser.add_argument("--verifier-timeout", type=int, default=240)
    parser.add_argument("--force", action="store_true", default=True)
    parser.add_argument("--no-force", dest="force", action="store_false")
    return parser.parse_args(list(argv) if argv is not None else None)


def run_command(command: Sequence[str], *, cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def git(repo: Path, *args: str, timeout: int | None = 60) -> subprocess.CompletedProcess[str]:
    return run_command(["git", *args], cwd=repo, timeout=timeout)


def first_parent(repo: Path, commit: str) -> str:
    completed = git(repo, "rev-list", "--parents", "-n", "1", commit)
    if completed.returncode != 0:
        raise ToolError("failed to find first parent", commit=commit, stderr=completed.stderr[-500:])
    parts = completed.stdout.strip().split()
    if len(parts) < 2:
        raise ToolError("commit has no first parent", commit=commit)
    return parts[1]


def git_show_file(repo: Path, commit: str, file_path: str) -> str | None:
    completed = git(repo, "show", f"{commit}:{file_path}", timeout=60)
    return completed.stdout if completed.returncode == 0 else None


def git_diff(repo: Path, base: str, target: str, files: Sequence[str]) -> str:
    completed = git(repo, "diff", "--binary", "--no-ext-diff", "--unified=3", base, target, "--", *files, timeout=120)
    if completed.returncode != 0:
        raise ToolError("failed to build git diff", target=target, stderr=completed.stderr[-500:])
    return completed.stdout


def extract_test_nodes_from_diff(diff_text: str, test_file: str) -> list[str]:
    names: list[str] = []
    for line in diff_text.splitlines():
        match = TEST_DEF_RE.match(line) or TEST_HUNK_RE.match(line)
        if match and match.group(1) not in names:
            names.append(match.group(1))
    return [f"{test_file}::{name}" for name in names]


def extract_test_nodes(repo: Path, base: str, target: str, test_files: Sequence[str]) -> list[str]:
    nodes: list[str] = []
    for test_file in test_files:
        completed = git(repo, "diff", "--unified=0", base, target, "--", test_file, timeout=60)
        if completed.returncode != 0:
            continue
        nodes.extend(extract_test_nodes_from_diff(completed.stdout, test_file))
    return list(dict.fromkeys(nodes))[:8]


def visible_problem_statement(subject: str, family: str) -> str:
    cleaned = re.sub(r"\s*\(#\d+\)\s*$", "", subject).strip().rstrip(".")
    if not cleaned:
        cleaned = f"Implement the described SymPy {family} behavior regression"
    if not cleaned.lower().startswith(("fix", "add", "allow", "preserve", "support", "prevent", "handle", "improve", "make", "return", "treat")):
        cleaned = f"Implement the SymPy behavior change: {cleaned}"
    return cleaned + "."


def verifier_script(venv_python: Path, test_nodes: Sequence[str]) -> str:
    quoted_nodes = " ".join(test_nodes)
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "script_dir=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
        "hidden_dir=\"$script_dir/hidden\"\n"
        "if [ -d \"$hidden_dir\" ]; then\n"
        "  while IFS= read -r -d '' file; do\n"
        "    rel=\"${file#$hidden_dir/}\"\n"
        "    mkdir -p \"$(dirname \"$rel\")\"\n"
        "    cp \"$file\" \"$rel\"\n"
        "  done < <(find \"$hidden_dir\" -type f -print0)\n"
        "fi\n"
        "export PYTHONPATH=\"$PWD${PYTHONPATH:+:$PYTHONPATH}\"\n"
        f"exec \"{venv_python}\" -m pytest -q {quoted_nodes}\n"
    )


def load_private_anchor_map(path: Path) -> dict[str, Mapping[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    anchors = payload.get("anchors") if isinstance(payload, Mapping) else None
    if not isinstance(anchors, list):
        raise ToolError("private anchor map is missing anchors", path=admission.repo_relative(path))
    return {str(anchor.get("candidate_id")): anchor for anchor in anchors if isinstance(anchor, Mapping)}


def source_and_test_files(files: Sequence[str]) -> tuple[list[str], list[str]]:
    source_files = [path for path in files if path.endswith(".py") and "/tests/" not in path]
    test_files = [path for path in files if path.endswith(".py") and "/tests/" in path]
    return source_files, test_files


def digest_file(path: Path) -> str:
    return admission.sha256_text(path.read_text(encoding="utf-8"))


def yaml_dump(path: Path, payload: Mapping[str, Any]) -> None:
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ToolError("PyYAML is required to write YAML manifests") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(dict(payload), sort_keys=False, allow_unicode=False), encoding="utf-8")


def materialize_candidate(
    *,
    source_repo: Path,
    private_anchor: Mapping[str, Any],
    public_candidate: Mapping[str, Any],
    task_id: str,
    private_root: Path,
    venv_python: Path,
    verifier_timeout: int,
) -> dict[str, Any]:
    commit = str(private_anchor.get("commit", ""))
    if not commit:
        raise ToolError("private anchor missing commit", candidate_id=private_anchor.get("candidate_id"))
    base = first_parent(source_repo, commit)
    files = [str(path) for path in private_anchor.get("files", []) if isinstance(path, str)]
    source_files, test_files = source_and_test_files(files)
    if not source_files or not test_files:
        raise ToolError("candidate must have source and test files", candidate_id=private_anchor.get("candidate_id"))
    test_nodes = extract_test_nodes(source_repo, base, commit, test_files)
    if not test_nodes:
        raise ToolError("candidate has no extractable test nodes", candidate_id=private_anchor.get("candidate_id"))
    reference_patch = git_diff(source_repo, base, commit, source_files)
    if not reference_patch.strip():
        raise ToolError("candidate source reference patch is empty", candidate_id=private_anchor.get("candidate_id"))

    candidate_id = str(public_candidate.get("candidate_id"))
    task_private_dir = private_root / candidate_id
    if task_private_dir.exists():
        shutil.rmtree(task_private_dir)
    task_private_dir.mkdir(parents=True, exist_ok=True)
    patch_path = task_private_dir / "reference_source.patch"
    patch_path.write_text(reference_patch, encoding="utf-8")
    empty_patch = task_private_dir / "empty.patch"
    empty_patch.write_text("", encoding="utf-8")

    public_dir = task_private_dir / "task/public"
    verifier_dir = task_private_dir / "task/verifier"
    public_dir.mkdir(parents=True, exist_ok=True)
    verifier_dir.mkdir(parents=True, exist_ok=True)
    statement = visible_problem_statement(str(private_anchor.get("subject", "")), str(public_candidate.get("family", "")))
    (public_dir / "statement.md").write_text(f"# {task_id}\n\n{statement}\n", encoding="utf-8")
    run_path = verifier_dir / "run.sh"
    run_path.write_text(verifier_script(venv_python, test_nodes), encoding="utf-8")
    run_path.chmod(run_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    hidden_file_digests: list[dict[str, str]] = []
    for test_file in test_files:
        content = git_show_file(source_repo, commit, test_file)
        if content is None:
            continue
        hidden_path = verifier_dir / "hidden" / test_file
        hidden_path.parent.mkdir(parents=True, exist_ok=True)
        hidden_path.write_text(content, encoding="utf-8")
        hidden_file_digests.append({"path_digest": admission.sha256_text(test_file), "content_digest": admission.sha256_text(content)})
    if not hidden_file_digests:
        raise ToolError("candidate hidden verifier files were unavailable", candidate_id=candidate_id)

    task_manifest = {
        "schema_version": "core-narrative.task.v1",
        "task_id": task_id,
        "repo_slug": "sympy",
        "split": "external_calibrated_b",
        "source": {
            "kind": "git_commit_private_anchor",
            "base_commit": base,
            "target_commit": commit,
        },
        "task_family": public_candidate.get("family"),
        "task_statement_path": "public/statement.md",
        "allowed_context": {
            "include_git_history_before_base": False,
            "include_reference_patch": False,
            "include_target_commit": False,
        },
        "disallowed_context": [
            "reference patch or target diff",
            "hidden verifier files",
            "SWE-bench E problem statements, gold patches, test patches, or base commits",
            "ACUT outputs, failed patches, or near-miss scores",
            "future execution results for this task",
        ],
        "verifier": {"command": "verifier/run.sh", "timeout_seconds": verifier_timeout},
        "expected": {"no_op_fails": True, "reference_passes": True},
        "leakage": {
            "reviewed": True,
            "notes": "External-calibrated B admission uses selected SymPy anchors only; E raw materials and ACUT outputs are excluded.",
        },
        "metadata": {
            "candidate_id": candidate_id,
            "source_anchor_digest": public_candidate.get("source_anchor_digest"),
            "changed_file_set_digest": public_candidate.get("changed_file_set_digest"),
            "subject_digest": public_candidate.get("subject_digest"),
            "difficulty": public_candidate.get("difficulty"),
            "oracle_directness": public_candidate.get("oracle_directness"),
            "test_node_digests": [admission.sha256_text(node) for node in test_nodes],
        },
    }
    task_path = task_private_dir / "task/task.yaml"
    yaml_dump(task_path, task_manifest)
    return {
        "task_id": task_id,
        "candidate_id": candidate_id,
        "private_task_path": task_path,
        "reference_patch_path": patch_path,
        "empty_patch_path": empty_patch,
        "reference_patch_digest": digest_file(patch_path),
        "reference_patch_bytes": patch_path.stat().st_size,
        "hidden_verifier_digest": admission.sha256_text(json.dumps(hidden_file_digests, sort_keys=True)),
        "public_statement_digest": digest_file(public_dir / "statement.md"),
        "test_node_count": len(test_nodes),
        "hidden_file_count": len(hidden_file_digests),
        "base_commit_digest": admission.digest_parts("sympy/sympy", base),
        "target_commit_digest": admission.digest_parts("sympy/sympy", commit),
    }


def run_prepare(task_path: Path, source_repo: Path, workspace: Path, *, force: bool) -> dict[str, Any]:
    command = [
        sys.executable,
        str(PREPARE),
        "--task",
        str(task_path),
        "--source-repo",
        str(source_repo),
        "--workspace",
        str(workspace),
    ]
    if force:
        command.append("--force")
    started = time.monotonic()
    completed = run_command(command, timeout=240)
    return {
        "command": [Path(command[0]).name, *command[1:]],
        "exit_code": completed.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout_digest": admission.sha256_text(completed.stdout),
        "stderr_digest": admission.sha256_text(completed.stderr),
    }


def run_apply_verify(
    *,
    task_path: Path,
    workspace: Path,
    patch_path: Path,
    run_id: str,
    artifact_dir: Path,
    timeout: int,
    skip_apply: bool = False,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(APPLY_VERIFY),
        "--workspace",
        str(workspace),
        "--task",
        str(task_path),
        "--patch",
        str(patch_path),
        "--acut-id",
        "admission",
        "--attempt",
        "1",
        "--run-id",
        run_id,
        "--artifact-dir",
        str(artifact_dir),
        "--timeout-seconds",
        str(timeout),
        "--output",
        str(artifact_dir / "result.json"),
        "--redact-verifier-artifacts",
    ]
    if skip_apply:
        command.append("--skip-apply")
    started = time.monotonic()
    completed = run_command(command, timeout=timeout + 60)
    payload: dict[str, Any] = {}
    result_path = artifact_dir / "result.json"
    if result_path.exists():
        try:
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
    return {
        "exit_code": completed.returncode,
        "duration_seconds": round(time.monotonic() - started, 3),
        "status": payload.get("status"),
        "verification": payload.get("verification"),
        "stdout_digest": admission.sha256_text(completed.stdout),
        "stderr_digest": admission.sha256_text(completed.stderr),
        "result_path": admission.repo_relative(result_path) if result_path.exists() else None,
    }


def sheet_for(
    public_candidate: Mapping[str, Any],
    materialized: Mapping[str, Any],
    no_op: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> dict[str, Any]:
    noop_fails = no_op.get("status") == "failed"
    reference_passes = reference.get("status") == "passed"
    accepted = bool(noop_fails and reference_passes)
    blockers: list[str] = []
    if not noop_fails:
        blockers.append("noop_did_not_fail")
    if not reference_passes:
        blockers.append("reference_patch_did_not_pass")
    return {
        "schema_version": "external-calibrated-repo-benchmark.b-candidate-sheet.v1",
        "candidate_id": public_candidate.get("candidate_id"),
        "task_id": materialized.get("task_id"),
        "repo": "sympy/sympy",
        "source_anchor_digest": public_candidate.get("source_anchor_digest"),
        "source_time": public_candidate.get("source_time"),
        "base_commit_digest": materialized.get("base_commit_digest"),
        "family": public_candidate.get("family"),
        "difficulty": public_candidate.get("difficulty"),
        "reference_patch_digest": materialized.get("reference_patch_digest"),
        "hidden_verifier_digest": materialized.get("hidden_verifier_digest"),
        "public_statement_digest": materialized.get("public_statement_digest"),
        "changed_file_anchor_digest": public_candidate.get("changed_file_set_digest"),
        "oracle_directness": public_candidate.get("oracle_directness"),
        "no_op_fails": noop_fails,
        "reference_patch_passes": reference_passes,
        "noop_status": no_op.get("status"),
        "reference_status": reference.get("status"),
        "noop_duration_seconds": no_op.get("duration_seconds"),
        "reference_duration_seconds": reference.get("duration_seconds"),
        "test_node_count": materialized.get("test_node_count"),
        "hidden_file_count": materialized.get("hidden_file_count"),
        "admission_status": "accepted" if accepted else "rejected",
        "blockers": blockers,
        "leakage": {
            "public_statement_has_target_commit": False,
            "public_statement_has_reference_patch": False,
            "public_statement_has_hidden_verifier": False,
            "selected_using_acut_outputs": False,
            "selected_using_e_results": False,
        },
    }


def render_task_manifest(summary: Mapping[str, Any], *, reserve: bool = False) -> dict[str, Any]:
    tasks = summary.get("reserve_tasks" if reserve else "primary_tasks", [])
    return {
        "schema_version": "external-calibrated-repo-benchmark.b-task-split.v1",
        "prepared_at": summary.get("generated_at"),
        "status": "reserve_admitted_frozen" if reserve else "admitted_frozen",
        "repo": "sympy/sympy",
        "split": "B_reserve" if reserve else "B_primary",
        "task_count": len(tasks) if isinstance(tasks, list) else 0,
        "freeze": {
            "denominator_status": "frozen_not_run",
            "deterministic_run_seed": "external-calibrated-repo-benchmark-v1:sympy-b-v1",
            "attempts_per_acut_task": 1,
            "best_of_n": False,
            "acut_specific_retry_allowed": False,
            "replacement_tasks_after_denominator_freeze": False,
            "status_mapping": {
                "verified_pass": 1,
                "verified_fail": 0,
                "no_diff": 0,
                "timeout": 0,
                "unsafe_or_scope_violation": 0,
                "verifier_infra_error": None,
            },
        },
        "tasks": tasks,
    }


def public_task_entry(sheet: Mapping[str, Any], ordinal: int) -> dict[str, Any]:
    return {
        "ordinal": ordinal,
        "task_id": sheet.get("task_id"),
        "candidate_id": sheet.get("candidate_id"),
        "repo": "sympy/sympy",
        "family": sheet.get("family"),
        "difficulty": sheet.get("difficulty"),
        "source_anchor_digest": sheet.get("source_anchor_digest"),
        "source_time": sheet.get("source_time"),
        "reference_patch_digest": sheet.get("reference_patch_digest"),
        "hidden_verifier_digest": sheet.get("hidden_verifier_digest"),
        "public_statement_digest": sheet.get("public_statement_digest"),
        "changed_file_anchor_digest": sheet.get("changed_file_anchor_digest"),
        "oracle_directness": sheet.get("oracle_directness"),
        "no_op_fails": sheet.get("no_op_fails"),
        "reference_patch_passes": sheet.get("reference_patch_passes"),
    }


def pass_rate(items: Sequence[Mapping[str, Any]], key: str) -> float | None:
    if not items:
        return None
    return round(sum(1 for item in items if item.get(key) is True) / len(items), 4)


def runtime_summary(items: Sequence[Mapping[str, Any]], key: str) -> dict[str, float | None]:
    values = [float(item[key]) for item in items if isinstance(item.get(key), (int, float))]
    if not values:
        return {"median": None, "p90": None}
    values.sort()
    p90_index = min(len(values) - 1, int(round((len(values) - 1) * 0.9)))
    return {"median": round(median(values), 3), "p90": round(values[p90_index], 3)}


def summarize_sheets(
    sheets: Sequence[Mapping[str, Any]],
    *,
    primary_target: int,
    reserve_target: int,
    candidate_pool_target: int | None,
    sheets_dir: str,
    private_root: str,
    workspace_root: str,
) -> dict[str, Any]:
    accepted = [dict(sheet) for sheet in sheets if sheet.get("admission_status") == "accepted"]
    screened_count = len(sheets)
    if candidate_pool_target is None:
        candidate_pool = [dict(sheet) for sheet in sheets]
        selected_accepted = accepted
        candidate_pool_mode = "direct_evaluated_candidates"
        candidate_count = screened_count
        accepted_count = len(accepted)
    else:
        selected_accepted = accepted[:candidate_pool_target]
        candidate_pool = selected_accepted
        candidate_pool_mode = "screened_admitted_pool"
        candidate_count = len(candidate_pool)
        accepted_count = len(selected_accepted)

    primary = selected_accepted[:primary_target]
    reserve = selected_accepted[primary_target : primary_target + reserve_target]
    primary_entries = [public_task_entry(sheet, index) for index, sheet in enumerate(primary, start=1)]
    reserve_entries = [public_task_entry(sheet, index) for index, sheet in enumerate(reserve, start=1)]
    blockers: list[str] = []
    if candidate_pool_target is not None and len(selected_accepted) < candidate_pool_target:
        blockers.append("admitted_candidate_pool_below_target")
    if len(primary_entries) < primary_target:
        blockers.append("primary_task_count_below_target")
    if not candidate_pool:
        blockers.append("generated_candidate_pool_empty")

    noop_rate = pass_rate(candidate_pool, "no_op_fails")
    reference_rate = pass_rate(candidate_pool, "reference_patch_passes")
    if noop_rate is None or noop_rate < 0.9:
        blockers.append("noop_fail_rate_below_90_percent")
    if reference_rate is None or reference_rate < 0.9:
        blockers.append("reference_patch_pass_rate_below_90_percent")
    status = "b_primary_frozen" if not blockers else "b_admission_incomplete"
    noop_runtime = runtime_summary(candidate_pool, "noop_duration_seconds")
    reference_runtime = runtime_summary(candidate_pool, "reference_duration_seconds")
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "status": status,
        "candidate_pool_mode": candidate_pool_mode,
        "candidate_pool_target": candidate_pool_target,
        "candidate_count": candidate_count,
        "accepted_count": accepted_count,
        "primary_task_count": len(primary_entries),
        "reserve_task_count": len(reserve_entries),
        "noop_fail_rate": noop_rate,
        "reference_patch_pass_rate": reference_rate,
        "noop_runtime_median_seconds": noop_runtime["median"],
        "noop_runtime_p90_seconds": noop_runtime["p90"],
        "reference_runtime_median_seconds": reference_runtime["median"],
        "reference_runtime_p90_seconds": reference_runtime["p90"],
        "screened_anchor_count": screened_count,
        "screened_anchor_accepted_count": len(accepted),
        "screened_anchor_noop_fail_rate": pass_rate(sheets, "no_op_fails"),
        "screened_anchor_reference_patch_pass_rate": pass_rate(sheets, "reference_patch_passes"),
        "screened_anchor_blocker_counts": dict(
            sorted(Counter(str(blocker) for sheet in sheets for blocker in sheet.get("blockers", [])).items())
        ),
        "accepted_family_counts": dict(sorted(Counter(str(sheet.get("family")) for sheet in selected_accepted).items())),
        "accepted_difficulty_counts": dict(sorted(Counter(str(sheet.get("difficulty")) for sheet in selected_accepted).items())),
        "primary_tasks": primary_entries,
        "reserve_tasks": reserve_entries,
        "candidate_sheet_dir": sheets_dir,
        "private_artifact_root": private_root,
        "workspace_root": workspace_root,
        "materialization_errors": [],
        "blockers": blockers,
        "next_required_steps": [
            "Review accepted primary/reserve balance before ACUT execution.",
            "Do not run E or B ACUT primary until B manifests are frozen and audited.",
        ],
    }


def render_report(summary: Mapping[str, Any]) -> str:
    lines = [
        "# SymPy B Task Admission",
        "",
        f"Protocol: `{summary.get('protocol_id')}`",
        f"Status: `{summary.get('status')}`",
        f"Generated at: `{summary.get('generated_at')}`",
        "",
        "## Gate",
        "",
        f"- Candidate pool mode: `{summary.get('candidate_pool_mode')}`",
        f"- Generated candidates: `{summary.get('candidate_count')}`",
        f"- Screened anchors: `{summary.get('screened_anchor_count')}`",
        f"- Accepted: `{summary.get('accepted_count')}`",
        f"- Primary/reserve frozen: `{summary.get('primary_task_count')}` / `{summary.get('reserve_task_count')}`",
        f"- Reference pass rate: `{summary.get('reference_patch_pass_rate')}`",
        f"- No-op fail rate: `{summary.get('noop_fail_rate')}`",
        f"- Reference runtime median/p90 seconds: `{summary.get('reference_runtime_median_seconds')}` / `{summary.get('reference_runtime_p90_seconds')}`",
        f"- Screened anchor reference/no-op rates: `{summary.get('screened_anchor_reference_patch_pass_rate')}` / `{summary.get('screened_anchor_noop_fail_rate')}`",
        f"- Blockers: `{summary.get('blockers')}`",
        "",
        "## Families",
        "",
    ]
    families = summary.get("accepted_family_counts") if isinstance(summary.get("accepted_family_counts"), Mapping) else {}
    for family, count in families.items():
        lines.append(f"- `{family}`: `{count}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Public artifacts contain digests and admission statuses only. Raw reference patches, hidden tests, and verifier logs are kept under ignored private artifact roots.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    source_repo = Path(args.source_repo)
    candidates_payload = load_manifest(Path(args.candidates))
    private_anchors = load_private_anchor_map(Path(args.private_anchors))
    venv_python = Path(args.venv_python).absolute()
    if not venv_python.exists():
        raise ToolError("SymPy admission venv python is missing", path=str(venv_python))
    candidates = list(candidates_payload.get("candidates", []))
    if args.max_candidates is not None:
        candidates = candidates[: args.max_candidates]
    private_root = Path(args.private_root)
    workspace_root = Path(args.workspace_root)
    sheets_dir = Path(args.sheets_dir)
    if args.force:
        for path in (private_root, workspace_root, sheets_dir):
            if path.exists():
                shutil.rmtree(path)
    private_root.mkdir(parents=True, exist_ok=True)
    workspace_root.mkdir(parents=True, exist_ok=True)
    sheets_dir.mkdir(parents=True, exist_ok=True)

    sheets: list[dict[str, Any]] = []
    materialization_errors: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, Mapping):
            continue
        candidate_id = str(candidate.get("candidate_id"))
        private_anchor = private_anchors.get(candidate_id)
        if private_anchor is None:
            materialization_errors.append({"candidate_id": candidate_id, "error": "private_anchor_missing"})
            continue
        task_id = f"sympy__b__{index:03d}"
        try:
            materialized = materialize_candidate(
                source_repo=source_repo,
                private_anchor=private_anchor,
                public_candidate=candidate,
                task_id=task_id,
                private_root=private_root,
                venv_python=venv_python,
                verifier_timeout=args.verifier_timeout,
            )
            task_path = Path(materialized["private_task_path"])
            no_op_workspace = workspace_root / f"{task_id}__noop"
            ref_workspace = workspace_root / f"{task_id}__reference"
            prep_noop = run_prepare(task_path, source_repo, no_op_workspace, force=args.force)
            if prep_noop["exit_code"] != 0:
                raise ToolError("no-op workspace preparation failed", candidate_id=candidate_id)
            no_op = run_apply_verify(
                task_path=task_path,
                workspace=no_op_workspace,
                patch_path=Path(materialized["empty_patch_path"]),
                run_id=f"{task_id}__noop",
                artifact_dir=private_root / candidate_id / "noop_artifacts",
                timeout=args.verifier_timeout,
                skip_apply=True,
            )
            prep_ref = run_prepare(task_path, source_repo, ref_workspace, force=args.force)
            if prep_ref["exit_code"] != 0:
                raise ToolError("reference workspace preparation failed", candidate_id=candidate_id)
            reference = run_apply_verify(
                task_path=task_path,
                workspace=ref_workspace,
                patch_path=Path(materialized["reference_patch_path"]),
                run_id=f"{task_id}__reference",
                artifact_dir=private_root / candidate_id / "reference_artifacts",
                timeout=args.verifier_timeout,
            )
            sheet = sheet_for(candidate, materialized, no_op, reference)
        except Exception as exc:
            sheet = {
                "schema_version": "external-calibrated-repo-benchmark.b-candidate-sheet.v1",
                "candidate_id": candidate_id,
                "task_id": task_id,
                "repo": "sympy/sympy",
                "source_anchor_digest": candidate.get("source_anchor_digest"),
                "family": candidate.get("family"),
                "difficulty": candidate.get("difficulty"),
                "admission_status": "rejected",
                "blockers": ["materialization_or_smoke_error"],
                "error_type": type(exc).__name__,
                "error_digest": admission.sha256_text(str(exc)),
            }
        sheets.append(sheet)
        write_json(sheets_dir / f"{candidate_id}.json", sheet)

    summary = summarize_sheets(
        sheets,
        primary_target=args.primary_target,
        reserve_target=args.reserve_target,
        candidate_pool_target=args.candidate_pool_target,
        sheets_dir=admission.repo_relative(sheets_dir),
        private_root=admission.repo_relative(private_root),
        workspace_root=admission.repo_relative(workspace_root),
    )
    summary["materialization_errors"] = materialization_errors
    write_json(Path(args.summary), summary)
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(render_report(summary), encoding="utf-8")
    if summary.get("status") == "b_primary_frozen":
        yaml_dump(Path(args.primary_manifest), render_task_manifest(summary, reserve=False))
        yaml_dump(Path(args.reserve_manifest), render_task_manifest(summary, reserve=True))
    emit_json(
        {
            **summary,
            "summary_path": admission.repo_relative(Path(args.summary)),
            "report_path": admission.repo_relative(Path(args.report)),
            "primary_manifest_path": admission.repo_relative(Path(args.primary_manifest)) if Path(args.primary_manifest).exists() else None,
            "reserve_manifest_path": admission.repo_relative(Path(args.reserve_manifest)) if Path(args.reserve_manifest).exists() else None,
        }
    )
    return 0 if summary.get("status") == "b_primary_frozen" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
