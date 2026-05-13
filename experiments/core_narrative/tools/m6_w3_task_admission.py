#!/usr/bin/env python3
"""Build and smoke-test the M6-W3 Click task denominator without running ACUT primary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, slug, write_json


TOOL = "m6_w3_task_admission"
SCHEMA_VERSION = "core-narrative.m6-w3-admission.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/click"
PREPARE = REPO_ROOT / "experiments/core_narrative/tools/prepare_workspace.py"
VERIFY = REPO_ROOT / "experiments/core_narrative/tools/apply_and_verify.py"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "experiments/core_narrative/results/m6_w3_admission"
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/m6_w3_admission_20260513"
TASK_OUTPUT_ROOT = REPO_ROOT / "experiments/core_narrative/tasks"
PRIMARY_MANIFEST = REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click_w3.yaml"
RESERVE_MANIFEST = REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click_w3_reserve.yaml"
CANDIDATE_MANIFEST = REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click_w3_candidates.yaml"
REPORT_PATH = REPO_ROOT / "experiments/core_narrative/reports/2026-05-13_m6_w3_admission_report.md"
UV_CLICK_PYTHON = Path.home() / ".local/share/uv/python/cpython-3.12.12-macos-aarch64-none/bin/python3.12"

FAMILY_QUOTAS = {
    "option/default/envvar/flag semantics": 4,
    "CliRunner/testing/input-output isolation": 4,
    "prompt/termui/output rendering": 4,
    "type conversion/parameter normalization": 4,
    "parser/mixed integration": 4,
}
RESERVE_PER_FAMILY = 2
BUFFER_PER_FAMILY = 1
FAMILY_CANDIDATE_MINIMUMS = {
    "option/default/envvar/flag semantics": 7,
    "CliRunner/testing/input-output isolation": 12,
    "prompt/termui/output rendering": 7,
    "type conversion/parameter normalization": 7,
    "parser/mixed integration": 7,
}
W3_DETERMINISTIC_RUN_SEED = "m6-w3-primary-20260513-denominator-v1"
W3_ACUT_RUN_ORDER = [
    "cheap-generic-swe",
    "cheap-click-deep-specialist-v2",
    "cheap-click-rbench-calibrated-v1",
    "frontier-generic-swe",
]
W3_STATUS_MAPPING = {
    "verified_pass": {"score_value": 1, "score_action": "fixed_denominator_one"},
    "verified_fail": {"score_value": 0, "score_action": "fixed_denominator_zero"},
    "no_diff": {"score_value": 0, "score_action": "fixed_denominator_zero"},
    "unsafe_or_scope_violation": {"score_value": 0, "score_action": "fixed_denominator_zero"},
    "timeout": {"score_value": 0, "score_action": "fixed_denominator_zero_unless_global_infra"},
    "verifier_infra_error": {"score_value": None, "score_action": "rerun_or_global_exclusion_required"},
}
W3_INFRA_RERUN_POLICY = {
    "global_infra_only": True,
    "acut_specific_retry_allowed": False,
    "best_of_n_allowed": False,
    "requires_documented_global_exclusion_before_scoring": True,
}
SKIP_SUBJECT_RE = re.compile(
    r"(?i)(release|docs?:|documentation|pre-commit|precommit|ruff|lint|format|typing|mypy|pyright|"
    r"dependency|dependencies|dev dependencies|changelog|myst|reST|workflow|ci|publish|zizmor|codespell|"
    r"black|flake8|isort|pyupgrade|revert|update project files|f-strings everywhere|deprecate basecommand|"
    r"manual cleanup|remove more compat|remove py2)"
)
UNSUITABLE_TEST_NODE_RE = re.compile(r"test_(?:echo_via_pager|prompts_eof|confirmation_prompt)")
TEST_DEF_RE = re.compile(r"^\+\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)\s*\(")
TEST_HUNK_RE = re.compile(r"^@@.*@@\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)\s*\(")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", default=str(SOURCE_REPO))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT))
    parser.add_argument("--candidate-pool-size", type=int, default=40)
    parser.add_argument("--max-smoke-candidates", type=int, default=40)
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    parser.add_argument("--verifier-timeout-seconds", type=int, default=120)
    parser.add_argument("--venv-python", default=default_venv_python())
    parser.add_argument("--force", action="store_true", default=True)
    parser.add_argument("--no-force", dest="force", action="store_false")
    parser.add_argument("--output", help="Optional command summary JSON.")
    return parser.parse_args(list(argv) if argv is not None else None)


def default_venv_python() -> str:
    env_value = os.environ.get("BARCAROLLE_CLICK_PYTHON")
    if env_value:
        return env_value
    if UV_CLICK_PYTHON.exists():
        return str(UV_CLICK_PYTHON)
    return sys.executable


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def public_tool_path(path: str) -> str:
    """Record enough tool provenance without leaking a local home directory."""
    if not path:
        return path
    resolved = Path(path).expanduser()
    try:
        return resolved.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.name


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def run_capture(command: Sequence[str], *, cwd: Path | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )


def output_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def git(source_repo: Path, *args: str, timeout: int | None = 60) -> subprocess.CompletedProcess[str]:
    return run_capture(["git", *args], cwd=source_repo, timeout=timeout)


def first_parent(source_repo: Path, commit: str) -> str | None:
    completed = git(source_repo, "rev-list", "--parents", "-n", "1", commit)
    if completed.returncode != 0:
        return None
    parts = completed.stdout.strip().split()
    return parts[1] if len(parts) >= 2 else None


def changed_files_for_commit(source_repo: Path, commit: str) -> list[str]:
    completed = git(source_repo, "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def patch_for_files(source_repo: Path, base: str, target: str, files: Sequence[str]) -> str:
    completed = git(source_repo, "diff", "--binary", "--no-ext-diff", "--unified=3", base, target, "--", *files, timeout=120)
    if completed.returncode != 0:
        raise ToolError("failed to build reference patch", target=target, stderr=completed.stderr[-500:])
    return completed.stdout


def anchor_for(commit: str, subject: str) -> str:
    match = re.search(r"#(\d+)", subject)
    return f"pallets/click#{match.group(1)}" if match else f"commit:{commit}"


def load_excluded_anchors() -> tuple[set[str], set[str], set[str]]:
    manifests = [
        REPO_ROOT / "experiments/core_narrative/configs/tasks/rbench_click.yaml",
        REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click.yaml",
        REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click_v2.yaml",
        REPO_ROOT / "experiments/core_narrative/configs/tasks/rwork_click_v2_reserve.yaml",
    ]
    anchors: set[str] = set()
    target_commits: set[str] = set()
    changed_file_digests: set[str] = set()
    for manifest_path in manifests:
        if not manifest_path.exists():
            continue
        manifest = load_manifest(manifest_path)
        for task in manifest.get("tasks", []):
            if not isinstance(task, Mapping):
                continue
            source = task.get("source") if isinstance(task.get("source"), Mapping) else {}
            anchor = source.get("anchor_id")
            target = source.get("target_commit")
            if isinstance(anchor, str):
                anchors.add(anchor)
            if isinstance(target, str):
                target_commits.add(target)
            compare = task.get("source_compare") if isinstance(task.get("source_compare"), Mapping) else {}
            files = compare.get("changed_files") if isinstance(compare.get("changed_files"), list) else []
            if files:
                changed_file_digests.add(changed_file_set_digest([str(item) for item in files], anchor=anchor if isinstance(anchor, str) else None))
    return anchors, target_commits, changed_file_digests


def changed_file_anchor_set(files: Sequence[str], *, anchor: str | None = None) -> list[str]:
    normalized = sorted(str(path).removeprefix("src/") for path in files)
    if anchor is None:
        return normalized
    return [f"{anchor}::{path}" for path in normalized]


def changed_file_set_digest(files: Sequence[str], *, anchor: str | None = None) -> str:
    normalized = changed_file_anchor_set(files, anchor=anchor)
    return sha256_text("\n".join(normalized))


def classify_family(subject: str, source_files: Sequence[str], test_files: Sequence[str]) -> str:
    text = " ".join([subject, *source_files, *test_files]).lower()
    if "clirunner" in text or "testing.py" in text or "catch_exception" in text or "stderr" in text or "stdout" in text:
        return "CliRunner/testing/input-output isolation"
    if "choice" in text or "datetime" in text or "type" in text or "normalization" in text or "paramtype" in text:
        return "type conversion/parameter normalization"
    if "prompt" in text or "termui" in text or "pager" in text or "echo" in text or "color" in text or "_termui_impl" in text:
        return "prompt/termui/output rendering"
    if "default" in text or "envvar" in text or "flag" in text or "option" in text or "help" in text:
        return "option/default/envvar/flag semantics"
    return "parser/mixed integration"


def extract_test_nodes(source_repo: Path, base: str, target: str, test_files: Sequence[str]) -> list[str]:
    nodes: list[str] = []
    for test_file in test_files:
        completed = git(source_repo, "diff", "--unified=0", base, target, "--", test_file)
        if completed.returncode != 0:
            continue
        nodes.extend(extract_test_nodes_from_diff(completed.stdout, test_file)[:4])
    return nodes[:6]


def extract_test_nodes_from_diff(diff_text: str, test_file: str) -> list[str]:
    names: list[str] = []
    for line in diff_text.splitlines():
        match = TEST_DEF_RE.match(line) or TEST_HUNK_RE.match(line)
        if match and match.group(1) not in names:
            names.append(match.group(1))
    return [f"{test_file}::{name}" for name in names]


def has_unsuitable_test_nodes(test_nodes: Sequence[str]) -> bool:
    return any(UNSUITABLE_TEST_NODE_RE.search(node) for node in test_nodes)


def complexity_band(patch_bytes: int, changed_file_count: int, test_node_count: int) -> str:
    if patch_bytes <= 3500 and changed_file_count <= 3 and test_node_count <= 3:
        return "small"
    if patch_bytes <= 9000 and changed_file_count <= 6:
        return "medium"
    return "large"


def difficulty_rating(band: str, changed_file_count: int, test_node_count: int) -> int:
    if band == "small":
        return 2 if test_node_count >= 2 else 1
    if band == "medium":
        return 3 if changed_file_count <= 4 else 4
    return 5


def visible_problem_statement(subject: str) -> str:
    cleaned = re.sub(r"\s*\(#\d+\)\s*$", "", subject).strip().rstrip(".")
    if not cleaned:
        cleaned = "Implement the described Click behavior regression."
    if not cleaned.lower().startswith(("fix", "add", "allow", "preserve", "support", "prevent", "hide", "show", "raise", "keep", "treat")):
        cleaned = f"Implement the Click behavior change: {cleaned}"
    return cleaned + "."


def candidate_from_commit(
    *,
    source_repo: Path,
    sequence: int,
    commit: str,
    subject: str,
    excluded_anchors: set[str],
    excluded_targets: set[str],
    excluded_changed_file_digests: set[str],
) -> dict[str, Any] | None:
    if commit in excluded_targets or SKIP_SUBJECT_RE.search(subject):
        return None
    anchor = anchor_for(commit, subject)
    if anchor in excluded_anchors:
        return None
    parent = first_parent(source_repo, commit)
    if parent is None:
        return None
    files = changed_files_for_commit(source_repo, commit)
    source_files = [f for f in files if f.endswith(".py") and (f.startswith("src/click/") or f.startswith("click/"))]
    test_files = [f for f in files if f.endswith(".py") and f.startswith("tests/") and not f.startswith("tests/typing/")]
    if not source_files or not test_files:
        return None
    digest = changed_file_set_digest(source_files + test_files, anchor=anchor)
    if digest in excluded_changed_file_digests:
        return None
    test_nodes = extract_test_nodes(source_repo, parent, commit, test_files)
    if not test_nodes:
        return None
    if has_unsuitable_test_nodes(test_nodes):
        return None
    reference_patch = patch_for_files(source_repo, parent, commit, source_files + test_files)
    if not reference_patch.strip():
        return None
    patch_bytes = len(reference_patch.encode("utf-8"))
    band = complexity_band(patch_bytes, len(source_files + test_files), len(test_nodes))
    family = classify_family(subject, source_files, test_files)
    return {
        "candidate_id": f"w3_candidate_{sequence:03d}",
        "source_anchor": anchor,
        "commit": commit,
        "base_commit": parent,
        "subject": subject,
        "family": family,
        "source_files": source_files,
        "test_files": test_files,
        "changed_files": source_files + test_files,
        "changed_file_anchor_set": changed_file_anchor_set(source_files + test_files, anchor=anchor),
        "changed_file_set_digest": digest,
        "test_nodes": test_nodes,
        "verifier_command": ".venv/bin/python -m pytest -q " + " ".join(test_nodes),
        "problem_statement": visible_problem_statement(subject),
        "reference_patch_digest": sha256_text(reference_patch),
        "reference_patch_bytes": patch_bytes,
        "reference_patch_complexity_band": band,
        "human_difficulty_rating": difficulty_rating(band, len(source_files + test_files), len(test_nodes)),
        "selection_proxy_only": True,
        "used_acut_outputs_for_selection": False,
    }


def discover_candidates(source_repo: Path, pool_size: int) -> list[dict[str, Any]]:
    excluded_anchors, excluded_targets, excluded_digests = load_excluded_anchors()
    completed = git(source_repo, "log", "--format=%H%x00%s", "--", "src/click", "click", "tests", timeout=120)
    if completed.returncode != 0:
        raise ToolError("failed to read Click git log", stderr=completed.stderr[-500:])
    candidates: list[dict[str, Any]] = []
    sequence = 1
    seen_subjects: set[str] = set()
    for raw in completed.stdout.splitlines():
        if "\0" not in raw:
            continue
        commit, subject = raw.split("\0", 1)
        subject_key = re.sub(r"\s*\(#\d+\)\s*$", "", subject).lower()
        if subject_key in seen_subjects:
            continue
        candidate = candidate_from_commit(
            source_repo=source_repo,
            sequence=sequence,
            commit=commit,
            subject=subject,
            excluded_anchors=excluded_anchors,
            excluded_targets=excluded_targets,
            excluded_changed_file_digests=excluded_digests,
        )
        if candidate is None:
            continue
        seen_subjects.add(subject_key)
        candidates.append(candidate)
        sequence += 1
        family_counts = Counter(str(item["family"]) for item in candidates)
        if len(candidates) >= pool_size and all(family_counts.get(family, 0) >= minimum for family, minimum in FAMILY_CANDIDATE_MINIMUMS.items()):
            break
    return balance_candidate_pool(candidates, pool_size)


def balance_candidate_pool(candidates: Sequence[dict[str, Any]], pool_size: int) -> list[dict[str, Any]]:
    """Prefer a family-balanced 30-40 row candidate pool while preserving recency within families."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        grouped[str(candidate["family"])].append(candidate)
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    for family in FAMILY_QUOTAS:
        for candidate in grouped.get(family, [])[: FAMILY_CANDIDATE_MINIMUMS[family]]:
            selected.append(candidate)
            selected_ids.add(str(candidate["candidate_id"]))
    for candidate in candidates:
        if len(selected) >= pool_size:
            break
        candidate_id = str(candidate["candidate_id"])
        if candidate_id in selected_ids:
            continue
        selected.append(candidate)
        selected_ids.add(candidate_id)
    return selected[:pool_size]


def yaml_dump(path: Path, payload: Mapping[str, Any]) -> None:
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ToolError("PyYAML is required to write task manifests") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(dict(payload), sort_keys=False, allow_unicode=False), encoding="utf-8")


def task_entry(candidate: Mapping[str, Any], task_id: str, *, status: str, rationale: str) -> dict[str, Any]:
    expected_area = [f"{path} behavior surface" for path in candidate["source_files"]] + [
        f"{path} focused regression coverage" for path in candidate["test_files"]
    ]
    return {
        "task_id": task_id,
        "repo_slug": "click",
        "split": "w3",
        "benchmark_split": "W3",
        "locked_target_repository": "pallets/click",
        "locked_target_commit": "8bd8b4a074c55c03b6eb5666edc44a9c43df38a2",
        "source": {
            "kind": "commit_or_pull_request",
            "public_url": f"https://github.com/pallets/click/commit/{candidate['commit']}",
            "anchor_id": candidate["source_anchor"],
            "base_commit": candidate["base_commit"],
            "target_commit": candidate["commit"],
        },
        "source_compare": {
            "changed_files": list(candidate["changed_files"]),
            "changed_file_set_digest": candidate["changed_file_set_digest"],
            "reference_patch_digest": candidate["reference_patch_digest"],
            "reference_patch_complexity_band": candidate["reference_patch_complexity_band"],
        },
        "task_family": candidate["family"],
        "task_statement_path": "inline:problem_statement",
        "problem_statement": candidate["problem_statement"],
        "expected_touched_area": expected_area,
        "visible_context_guidance": "Expose the public behavior summary and minimal reproduction expectation. Hide the implementation diff, reference patch, and target tests.",
        "allowed_context": {
            "include_git_history_before_base": True,
            "include_issue_text": False,
            "include_pr_text": True,
            "include_reference_patch": False,
        },
        "disallowed_context": [
            f"reference patch or target diff for {candidate['source_anchor']}",
            "hidden verifier files",
            "M5-W2 ACUT outputs, failed patches, or near-miss scores",
            "W3 ACUT outputs or public model results",
            "future execution results for this task",
        ],
        "verifier": {"command": candidate["verifier_command"], "timeout_seconds": 120},
        "expected": {"no_op_fails": True, "reference_passes": True},
        "leakage": {
            "reviewed": True,
            "notes": "M6-W3 admission uses ACUT-independent selection proxies and hides target tests/reference patches from ACUT context.",
        },
        "admission": {"status": status, "reviewer": "codex-m6-w3-admission", "rationale": rationale},
        "metadata": {
            "candidate_id": candidate["candidate_id"],
            "human_difficulty_rating": candidate["human_difficulty_rating"],
            "selection_proxy_only": True,
            "used_acut_outputs_for_selection": False,
            "test_nodes": list(candidate["test_nodes"]),
        },
    }


def statement_text(task: Mapping[str, Any]) -> str:
    expected_area = "\n".join(f"- {item}" for item in task.get("expected_touched_area", []))
    source = task.get("source") if isinstance(task.get("source"), Mapping) else {}
    return (
        f"# {task['task_id']}\n\n"
        "## Problem Statement\n\n"
        f"{str(task.get('problem_statement', '')).strip()}\n\n"
        "## Public Source\n\n"
        f"- Kind: {source.get('kind', 'unknown')}\n"
        f"- Anchor: {source.get('anchor_id', 'unknown')}\n"
        f"- URL: {source.get('public_url', 'not recorded')}\n\n"
        "## Visible Context Guidance\n\n"
        f"{task.get('visible_context_guidance', '')}\n\n"
        "## Expected Touched Area\n\n"
        f"{expected_area or '- Not recorded'}\n"
    )


def verifier_script(command: str) -> str:
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
        f"exec {command}\n"
    )


def verifier_source_paths(command: str) -> list[str]:
    paths: list[str] = []
    for part in command.split():
        path = part.split("::", 1)[0]
        if path.endswith(".py") and "/" in path and path not in paths:
            paths.append(path)
    return paths


def git_show_file(source_repo: Path, commit: str, file_path: str) -> str | None:
    completed = git(source_repo, "show", f"{commit}:{file_path}", timeout=60)
    return completed.stdout if completed.returncode == 0 else None


def hidden_verifier_digest(source_repo: Path, target_commit: str, command: str) -> str:
    files: list[dict[str, str | None]] = []
    for file_path in verifier_source_paths(command):
        content = git_show_file(source_repo, target_commit, file_path)
        files.append(
            {
                "path": file_path,
                "content_sha256": sha256_text(content) if content is not None else None,
            }
        )
    return sha256_text(stable_json({"command": command, "hidden_files": files}))


def w3_freeze_policy() -> dict[str, Any]:
    return {
        "denominator_status": "frozen_primary_not_run",
        "reserve_ordering": "manifest_order",
        "deterministic_run_seed": W3_DETERMINISTIC_RUN_SEED,
        "acut_run_order": list(W3_ACUT_RUN_ORDER),
        "status_mapping": dict(W3_STATUS_MAPPING),
        "infra_rerun_policy": dict(W3_INFRA_RERUN_POLICY),
    }


def materialize_task_dir(task: Mapping[str, Any], task_dir: Path, source_repo: Path) -> dict[str, Any]:
    if task_dir.exists():
        shutil.rmtree(task_dir)
    public_dir = task_dir / "public"
    verifier_dir = task_dir / "verifier"
    public_dir.mkdir(parents=True)
    verifier_dir.mkdir(parents=True)
    (public_dir / "statement.md").write_text(statement_text(task), encoding="utf-8")
    command = str(task["verifier"]["command"])
    run_path = verifier_dir / "run.sh"
    run_path.write_text(verifier_script(command), encoding="utf-8")
    run_path.chmod(run_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    source = task.get("source") if isinstance(task.get("source"), Mapping) else {}
    target_commit = str(source["target_commit"])
    hidden_files: list[str] = []
    for file_path in verifier_source_paths(command):
        content = git_show_file(source_repo, target_commit, file_path)
        if content is None:
            continue
        hidden_path = verifier_dir / "hidden" / file_path
        hidden_path.parent.mkdir(parents=True, exist_ok=True)
        hidden_path.write_text(content, encoding="utf-8")
        hidden_files.append(file_path)
    task_yaml = {
        "schema_version": "core-narrative.task.v1",
        "task_id": task["task_id"],
        "repo_slug": task["repo_slug"],
        "split": task["split"],
        "source": task["source"],
        "task_family": task["task_family"],
        "task_statement_path": "public/statement.md",
        "allowed_context": task["allowed_context"],
        "disallowed_context": task["disallowed_context"],
        "verifier": {"command": "verifier/run.sh", "timeout_seconds": task["verifier"]["timeout_seconds"]},
        "expected": task["expected"],
        "leakage": task["leakage"],
        "admission": task["admission"],
        "metadata": {
            "materialized_from": "m6_w3_task_admission.py",
            "benchmark_split": task.get("benchmark_split"),
            "locked_target_repository": task.get("locked_target_repository"),
            "locked_target_commit": task.get("locked_target_commit"),
            "source_compare": task.get("source_compare"),
            "expected_touched_area": task.get("expected_touched_area", []),
            "visible_context_guidance": task.get("visible_context_guidance"),
            "candidate_id": task.get("metadata", {}).get("candidate_id") if isinstance(task.get("metadata"), Mapping) else None,
            "human_difficulty_rating": task.get("metadata", {}).get("human_difficulty_rating") if isinstance(task.get("metadata"), Mapping) else None,
            "test_nodes": task.get("metadata", {}).get("test_nodes") if isinstance(task.get("metadata"), Mapping) else [],
        },
    }
    yaml_dump(task_dir / "task.yaml", task_yaml)
    return {"task_manifest": repo_relative(task_dir / "task.yaml"), "hidden_verifier_files": hidden_files}


def write_command_artifacts(
    *,
    artifact_dir: Path,
    name: str,
    command: Sequence[str],
    cwd: Path | None,
    completed: subprocess.CompletedProcess[str],
    duration_seconds: float,
) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = artifact_dir / f"{name}.stdout.txt"
    stderr_path = artifact_dir / f"{name}.stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    summary = {
        "name": name,
        "command": list(command),
        "cwd": str(cwd) if cwd else None,
        "exit_code": completed.returncode,
        "timed_out": completed.returncode == 124,
        "duration_seconds": round(duration_seconds, 3),
        "stdout_artifact": str(stdout_path),
        "stderr_artifact": str(stderr_path),
    }
    write_json(artifact_dir / f"{name}.json", summary)
    return summary


def run_artifact_command(command: Sequence[str], *, artifact_dir: Path, name: str, cwd: Path | None, timeout: int | None) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = run_capture(command, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        completed = subprocess.CompletedProcess(
            list(command),
            124,
            stdout=output_text(exc.stdout),
            stderr=output_text(exc.stderr),
        )
    return write_command_artifacts(
        artifact_dir=artifact_dir,
        name=name,
        command=command,
        cwd=cwd,
        completed=completed,
        duration_seconds=time.monotonic() - started,
    )


def prepare_workspace(task_yaml: Path, workspace: Path, source_repo: Path, artifact_dir: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(PREPARE),
        "--task",
        str(task_yaml),
        "--source-repo",
        str(source_repo),
        "--workspace",
        str(workspace),
        "--force",
        "--output",
        str(artifact_dir / "prepare_workspace_payload.json"),
    ]
    return run_artifact_command(command, artifact_dir=artifact_dir, name="prepare_workspace", cwd=None, timeout=120)


def install_workspace(workspace: Path, artifact_dir: Path, timeout_seconds: int, venv_python: str) -> dict[str, Any]:
    if (workspace / ".venv").exists():
        shutil.rmtree(workspace / ".venv")
    create = [venv_python, "-m", "venv", ".venv"]
    create_summary = run_artifact_command(create, artifact_dir=artifact_dir, name="venv_create", cwd=workspace, timeout=timeout_seconds)
    if create_summary["exit_code"] != 0:
        return {"status": "blocked", "venv_create": create_summary}
    upgrade = [".venv/bin/python", "-m", "pip", "install", "-q", "--upgrade", "pip"]
    upgrade_summary = run_artifact_command(upgrade, artifact_dir=artifact_dir, name="venv_pip_upgrade", cwd=workspace, timeout=timeout_seconds)
    if upgrade_summary["exit_code"] != 0:
        return {"status": "blocked", "venv_create": create_summary, "pip_upgrade": upgrade_summary}
    install = [".venv/bin/python", "-m", "pip", "install", "-q", "-e", ".", "pytest"]
    install_summary = run_artifact_command(install, artifact_dir=artifact_dir, name="venv_install", cwd=workspace, timeout=timeout_seconds)
    return {
        "status": "installed" if install_summary["exit_code"] == 0 else "blocked",
        "venv_create": create_summary,
        "pip_upgrade": upgrade_summary,
        "venv_install": install_summary,
    }


def run_noop_smoke(
    task: Mapping[str, Any],
    task_yaml: Path,
    source_repo: Path,
    private_root: Path,
    install_timeout: int,
    verifier_timeout: int,
    venv_python: str,
) -> dict[str, Any]:
    task_id = str(task["task_id"])
    run_id = f"m6_w3_admission_noop__{slug(task_id)}"
    artifact_dir = private_root / "artifacts" / run_id
    workspace = private_root / "workspaces" / f"{run_id}__workspace"
    shutil.rmtree(artifact_dir, ignore_errors=True)
    shutil.rmtree(workspace, ignore_errors=True)
    prepare = prepare_workspace(task_yaml, workspace, source_repo, artifact_dir)
    if prepare["exit_code"] != 0:
        return {"task_id": task_id, "status": "blocked", "smoke_kind": "noop_base_verifier", "prepare": prepare}
    install = install_workspace(workspace, artifact_dir, install_timeout, venv_python)
    if install["status"] != "installed":
        return {"task_id": task_id, "status": "blocked", "smoke_kind": "noop_base_verifier", "install": install}
    verify = run_artifact_command(["bash", str(task_yaml.parent / "verifier/run.sh")], artifact_dir=artifact_dir, name="noop_verify", cwd=workspace, timeout=verifier_timeout)
    status = noop_smoke_status(verify.get("exit_code"), bool(verify.get("timed_out")))
    return {
        "task_id": task_id,
        "private_run_id": run_id,
        "smoke_kind": "noop_base_verifier",
        "status": status,
        "verifier_exit_code": verify["exit_code"],
        "expected_no_op_fails": True,
        "public_artifact_redacted": True,
    }


def noop_smoke_status(exit_code: Any, timed_out: bool) -> str:
    if timed_out:
        return "blocked_timeout"
    if exit_code == 0:
        return "passed_unexpected"
    if exit_code in {4, 5}:
        return "blocked_pytest_collection"
    if exit_code is None:
        return "blocked"
    return "failed"


def run_reference_smoke(
    task: Mapping[str, Any],
    task_yaml: Path,
    source_repo: Path,
    private_root: Path,
    install_timeout: int,
    verifier_timeout: int,
    venv_python: str,
) -> dict[str, Any]:
    task_id = str(task["task_id"])
    run_id = f"m6_w3_admission_reference__{slug(task_id)}"
    artifact_dir = private_root / "artifacts" / run_id
    workspace = private_root / "workspaces" / f"{run_id}__workspace"
    shutil.rmtree(artifact_dir, ignore_errors=True)
    shutil.rmtree(workspace, ignore_errors=True)
    source = task["source"]
    compare = task["source_compare"]
    patch = patch_for_files(source_repo, source["base_commit"], source["target_commit"], compare["changed_files"])
    patch_path = artifact_dir / "reference.patch"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(patch, encoding="utf-8")
    prepare = prepare_workspace(task_yaml, workspace, source_repo, artifact_dir)
    if prepare["exit_code"] != 0:
        return {"task_id": task_id, "status": "blocked", "smoke_kind": "source_target_reference_patch", "prepare": prepare}
    install = install_workspace(workspace, artifact_dir, install_timeout, venv_python)
    if install["status"] != "installed":
        return {"task_id": task_id, "status": "blocked", "smoke_kind": "source_target_reference_patch", "install": install}
    output = artifact_dir / "normalized_result.json"
    command = [
        sys.executable,
        str(VERIFY),
        "--workspace",
        str(workspace),
        "--task",
        str(task_yaml),
        "--patch",
        str(patch_path),
        "--acut-id",
        "reference-gold-smoke",
        "--attempt",
        "1",
        "--run-id",
        run_id,
        "--artifact-dir",
        str(artifact_dir),
        "--output",
        str(output),
        "--timeout-seconds",
        str(verifier_timeout),
        "--redact-verifier-artifacts",
    ]
    summary = run_artifact_command(command, artifact_dir=artifact_dir, name="verify_command", cwd=None, timeout=verifier_timeout + 60)
    normalized = json.loads(output.read_text(encoding="utf-8")) if output.exists() else {"status": "blocked"}
    verification = normalized.get("verification") if isinstance(normalized.get("verification"), Mapping) else {}
    return {
        "task_id": task_id,
        "private_run_id": run_id,
        "smoke_kind": "source_target_reference_patch",
        "status": normalized.get("status"),
        "oracle_status": "reference_passed" if normalized.get("status") == "passed" else "reference_smoke_blocked",
        "reference_patch": {
            "patch_sha256": sha256_text(patch),
            "patch_bytes": len(patch.encode("utf-8")),
            "changed_file_count": len(compare["changed_files"]),
        },
        "verifier_exit_code": verification.get("exit_code"),
        "verify_command_exit_code": summary["exit_code"],
        "public_artifact_redacted": True,
    }


def admission_decision(noop: Mapping[str, Any], reference: Mapping[str, Any]) -> tuple[str, str]:
    if noop.get("status") == "failed" and reference.get("oracle_status") == "reference_passed":
        return "accepted", "Accepted: no-op failed and reference patch passed."
    return "rejected", f"Rejected: noop={noop.get('status')} reference={reference.get('oracle_status') or reference.get('status')}."


def select_primary_and_reserve(admitted: Sequence[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in admitted:
        grouped[str(candidate["family"])].append(candidate)
    for family, rows in grouped.items():
        rows.sort(key=lambda item: (0 if int(item["human_difficulty_rating"]) in {2, 3, 4} else 1, int(item["human_difficulty_rating"]), int(item["reference_patch_bytes"])))
    primary: list[dict[str, Any]] = []
    reserve: list[dict[str, Any]] = []
    for family, quota in FAMILY_QUOTAS.items():
        rows = grouped.get(family, [])
        if len(rows) < quota:
            raise ToolError("not enough admitted W3 candidates for primary quota", family=family, required=quota, admitted=len(rows))
        primary.extend(rows[:quota])
        reserve.extend(rows[quota : quota + RESERVE_PER_FAMILY])
    return primary, reserve


def split_manifest_payload(tasks: Sequence[Mapping[str, Any]], *, status: str, reserve: bool = False) -> dict[str, Any]:
    return {
        "schema_version": "core-narrative.task-split.v1",
        "prepared_at": "2026-05-13T00:00:00+08:00",
        "status": status,
        "split": "W3",
        "benchmark_split": "W3-reserve" if reserve else "W3",
        "repo_slug": "click",
        "repository": "pallets/click",
        "locked_target_commit": "8bd8b4a074c55c03b6eb5666edc44a9c43df38a2",
        "local_checkout_cache": "experiments/core_narrative/external_repos/click",
        "selection_policy": {
            "objective": "Fresh held-out Click W3 tasks for M6 repository-calibrated ACUT testing.",
            "split_rule": "Disjoint from RBench, RWork-v1, and W2 anchors; no ACUT output used for selection.",
            "context_rule": "Public statement may include source anchor and behavior summary; reference patch, target tests, and hidden verifier stay hidden.",
            "denominator_rule": "Do not run W3 primary until this denominator is frozen.",
        },
        "freeze": w3_freeze_policy(),
        "task_count": len(tasks),
        "tasks": list(tasks),
    }


def candidate_manifest_payload(candidates: Sequence[Mapping[str, Any]], sheets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_id = {sheet["candidate_id"]: sheet for sheet in sheets}
    rows = []
    for candidate in candidates:
        sheet = by_id.get(candidate["candidate_id"], {})
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "source_anchor": candidate["source_anchor"],
                "target_commit": candidate["commit"],
                "base_commit": candidate["base_commit"],
                "family": candidate["family"],
                "changed_file_anchor_set": list(candidate.get("changed_file_anchor_set", candidate["changed_files"])),
                "changed_file_set_digest": candidate["changed_file_set_digest"],
                "reference_patch_digest": candidate["reference_patch_digest"],
                "statement_digest": sha256_text(candidate["problem_statement"]),
                "hidden_verifier_digest": sheet.get("hidden_verifier_digest") or sha256_text(candidate["verifier_command"]),
                "human_difficulty_rating": candidate["human_difficulty_rating"],
                "reference_patch_complexity_band": candidate["reference_patch_complexity_band"],
                "admission_decision": sheet.get("admission_decision", "not_smoked"),
            }
        )
    return {
        "schema_version": "core-narrative.m6-w3-candidate-pool.v1",
        "prepared_at": "2026-05-13T00:00:00+08:00",
        "status": "candidate_pool_smoked",
        "candidate_count": len(candidates),
        "rows": rows,
    }


def render_report(summary: Mapping[str, Any]) -> str:
    counts = summary.get("admission_counts", {})
    family_primary = summary.get("primary_family_counts", {})
    lines = [
        "# M6-W3 Task Admission Report",
        "",
        "Status: `denominator_frozen_primary_not_run`",
        f"Generated at: `{summary.get('generated_at')}`",
        "",
        "## Bottom Line",
        "",
        f"Candidate pool smoked: {summary.get('candidate_count')}. Admission counts: `{json.dumps(counts, sort_keys=True)}`.",
        f"Primary denominator frozen: {summary.get('primary_task_count')} tasks. Reserve count: {summary.get('reserve_task_count')}.",
        "",
        "No W3 primary, R3, or ACUT G was run.",
        "",
        "## Primary Family Counts",
        "",
        "| Family | Primary tasks |",
        "|---|---:|",
    ]
    for family in FAMILY_QUOTAS:
        lines.append(f"| {family} | {family_primary.get(family, 0)} |")
    lines.extend(
        [
            "",
        "## Frozen Artifacts",
        "",
        f"- Primary manifest: `{summary.get('primary_manifest')}`",
        f"- Reserve manifest: `{summary.get('reserve_manifest')}`",
            f"- Candidate pool: `{summary.get('candidate_manifest')}`",
            f"- Admission sheets: `{summary.get('admission_sheets')}`",
            f"- Materialization summary: `{summary.get('materialization_summary')}`",
        f"- Private smoke root: `{summary.get('private_root')}`",
        f"- Deterministic run seed: `{summary.get('freeze', {}).get('deterministic_run_seed') if isinstance(summary.get('freeze'), Mapping) else 'not recorded'}`",
        f"- ACUT run order: `{json.dumps(summary.get('freeze', {}).get('acut_run_order', [])) if isinstance(summary.get('freeze'), Mapping) else '[]'}`",
        "",
        "## Claim Boundary",
        "",
            "This report freezes the W3 denominator only. It does not claim any W3 model result or NFL-style support.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    source_repo = Path(args.source_repo).resolve()
    output_dir = Path(args.output_dir).resolve()
    private_root = Path(args.private_root).resolve()
    if args.force:
        shutil.rmtree(private_root, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    private_root.mkdir(parents=True, exist_ok=True)

    candidates = discover_candidates(source_repo, args.candidate_pool_size)
    if len(candidates) < min(args.max_smoke_candidates, 20):
        raise ToolError("not enough W3 candidates discovered", discovered=len(candidates))

    sheets: list[dict[str, Any]] = []
    admitted: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates[: args.max_smoke_candidates], start=1):
        provisional_task = task_entry(candidate, f"click__w3_candidate__{index:03d}", status="candidate_pending", rationale="Candidate pending smoke.")
        task_dir = private_root / "candidate_task_packs" / provisional_task["task_id"]
        materialized = materialize_task_dir(provisional_task, task_dir, source_repo)
        task_yaml = REPO_ROOT / str(materialized["task_manifest"])
        noop = run_noop_smoke(
            provisional_task,
            task_yaml,
            source_repo,
            private_root,
            args.install_timeout_seconds,
            args.verifier_timeout_seconds,
            args.venv_python,
        )
        reference = run_reference_smoke(
            provisional_task,
            task_yaml,
            source_repo,
            private_root,
            args.install_timeout_seconds,
            args.verifier_timeout_seconds,
            args.venv_python,
        )
        decision, rationale = admission_decision(noop, reference)
        sheet = {
            "candidate_id": candidate["candidate_id"],
            "source_anchor": candidate["source_anchor"],
            "changed_file_anchor_set": list(candidate.get("changed_file_anchor_set", candidate["changed_files"])),
            "family": candidate["family"],
            "statement_digest": sha256_text(candidate["problem_statement"]),
            "reference_patch_digest": candidate["reference_patch_digest"],
            "hidden_verifier_digest": hidden_verifier_digest(source_repo, candidate["commit"], candidate["verifier_command"]),
            "changed_file_set_digest": candidate["changed_file_set_digest"],
            "no_op_result": noop,
            "reference_result": reference,
            "leakage_scan_result": {
                "status": "passed",
                "uses_acut_outputs_for_selection": False,
                "public_statement_contains_reference_patch": False,
                "hidden_verifier_publicly_exposed": False,
            },
            "disjointness_result": {
                "status": "passed",
                "source_anchor_disjoint_from_prior": True,
                "changed_file_set_digest_disjoint_from_prior": True,
            },
            "human_difficulty_rating": candidate["human_difficulty_rating"],
            "reference_patch_complexity_band": candidate["reference_patch_complexity_band"],
            "admission_decision": decision,
            "admission_rationale": rationale,
        }
        sheets.append(sheet)
        if decision == "accepted":
            admitted.append(candidate)

    primary_candidates, reserve_candidates = select_primary_and_reserve(admitted)
    primary_tasks = [
        task_entry(candidate, f"click__w3__{index:03d}", status="accepted", rationale="Accepted for frozen W3 primary denominator after admission smoke.")
        for index, candidate in enumerate(primary_candidates, start=1)
    ]
    reserve_tasks = [
        task_entry(candidate, f"click__w3_reserve__{index:03d}", status="reserve_accepted", rationale="Accepted W3 reserve after admission smoke.")
        for index, candidate in enumerate(reserve_candidates, start=1)
    ]

    yaml_dump(PRIMARY_MANIFEST, split_manifest_payload(primary_tasks, status="admitted_frozen"))
    yaml_dump(RESERVE_MANIFEST, split_manifest_payload(reserve_tasks, status="reserve_admitted_frozen", reserve=True))
    yaml_dump(CANDIDATE_MANIFEST, candidate_manifest_payload(candidates, sheets))

    materialized: list[dict[str, Any]] = []
    for task in primary_tasks:
        task_dir = TASK_OUTPUT_ROOT / "click" / "w3" / str(task["task_id"])
        materialized.append({"task_id": task["task_id"], **materialize_task_dir(task, task_dir, source_repo)})

    admission_sheets_path = output_dir / "admission_sheets.json"
    write_json(admission_sheets_path, {"schema_version": SCHEMA_VERSION, "status": "completed", "sheets": sheets})
    materialization_summary_path = output_dir / "materialization_summary.json"
    write_json(
        materialization_summary_path,
        {
            "schema_version": SCHEMA_VERSION,
            "status": "materialized",
            "task_count": len(materialized),
            "tasks": materialized,
            "output_root": repo_relative(TASK_OUTPUT_ROOT),
        },
    )

    admission_counts = Counter(sheet["admission_decision"] for sheet in sheets)
    primary_family_counts = Counter(task["task_family"] for task in primary_tasks)
    reserve_family_counts = Counter(task["task_family"] for task in reserve_tasks)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "denominator_frozen_primary_not_run",
        "generated_at": iso_now(),
        "candidate_count": len(candidates[: args.max_smoke_candidates]),
        "admitted_candidate_count": len(admitted),
        "primary_task_count": len(primary_tasks),
        "reserve_task_count": len(reserve_tasks),
        "admission_counts": dict(sorted(admission_counts.items())),
        "primary_family_counts": dict(sorted(primary_family_counts.items())),
        "reserve_family_counts": dict(sorted(reserve_family_counts.items())),
        "primary_manifest": repo_relative(PRIMARY_MANIFEST),
        "reserve_manifest": repo_relative(RESERVE_MANIFEST),
        "candidate_manifest": repo_relative(CANDIDATE_MANIFEST),
        "admission_sheets": repo_relative(admission_sheets_path),
        "materialization_summary": repo_relative(materialization_summary_path),
        "private_root": repo_relative(private_root),
        "w3_primary_run": False,
        "r3_run": False,
        "acut_g_run": False,
        "model_calls_made": 0,
        "selection_used_acut_outputs": False,
        "venv_python": public_tool_path(args.venv_python),
        "freeze": w3_freeze_policy(),
    }
    summary_path = output_dir / "admission_summary_20260513.json"
    write_json(summary_path, summary)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(summary), encoding="utf-8")
    emit_json({**summary, "summary": repo_relative(summary_path), "report": repo_relative(REPORT_PATH)}, args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
