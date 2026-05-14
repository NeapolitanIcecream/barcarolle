#!/usr/bin/env python3
"""Run a one-candidate Rich direct-oracle admission smoke pilot."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, slug, write_json
from rich_task_admission_readiness import (
    DEFAULT_REPO,
    changed_file_set_digest,
    discover_candidates,
    run_git,
    sha256_text,
    source_anchor_digest,
)


TOOL = "rich_direct_smoke_pilot"
SCHEMA_VERSION = "core-narrative.rich-direct-smoke-pilot.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
PREPARE = REPO_ROOT / "experiments/core_narrative/tools/prepare_workspace.py"
VERIFY = REPO_ROOT / "experiments/core_narrative/tools/apply_and_verify.py"
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/rich_direct_smoke_pilot_20260514"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/rich_direct_smoke_pilot_20260514.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-14_rich_direct_smoke_pilot.md"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO), help="Local Rich checkout.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Ignored private artifact root.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Public redacted JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Public markdown report.")
    parser.add_argument("--candidate-index", type=int, default=0, help="Zero-based W* direct candidate index.")
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    parser.add_argument("--verifier-timeout-seconds", type=int, default=120)
    parser.add_argument("--venv-python", default=sys.executable)
    parser.add_argument("--force", action="store_true", default=True)
    parser.add_argument("--no-force", dest="force", action="store_false")
    return parser.parse_args(list(argv) if argv is not None else None)


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


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


def run_artifact_command(
    command: Sequence[str],
    *,
    artifact_dir: Path,
    name: str,
    cwd: Path | None,
    timeout: int | None,
) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
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
    stdout_path = artifact_dir / f"{name}.stdout.txt"
    stderr_path = artifact_dir / f"{name}.stderr.txt"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    summary = {
        "name": name,
        "command": list(command),
        "exit_code": completed.returncode,
        "timed_out": completed.returncode == 124,
        "duration_seconds": round(time.monotonic() - started, 3),
        "stdout_artifact": repo_relative(stdout_path),
        "stderr_artifact": repo_relative(stderr_path),
    }
    write_json(artifact_dir / f"{name}.json", summary)
    return summary


def patch_for_candidate(repo_path: Path, candidate: Mapping[str, Any]) -> str:
    files = list(candidate.get("source_files", [])) + list(candidate.get("test_files", []))
    completed = run_git(
        repo_path,
        "diff",
        "--binary",
        "--no-ext-diff",
        "--unified=3",
        str(candidate["base_commit"]),
        str(candidate["commit"]),
        "--",
        *[str(path) for path in files],
        timeout=120,
    )
    if completed.returncode != 0:
        raise ToolError("failed to build Rich reference patch", stderr=completed.stderr[-500:])
    return completed.stdout


def git_show_file(repo_path: Path, commit: str, file_path: str) -> str:
    completed = run_git(repo_path, "show", f"{commit}:{file_path}", timeout=60)
    if completed.returncode != 0:
        raise ToolError("failed to read target hidden verifier file", path=file_path, stderr=completed.stderr[-500:])
    return completed.stdout


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


def problem_statement(subject: str) -> str:
    cleaned = subject.strip().rstrip(".")
    if not cleaned.lower().startswith(("fix", "add", "allow", "preserve", "support", "prevent", "handle", "avoid")):
        cleaned = f"Implement the Rich behavior change: {cleaned}"
    return cleaned + "."


def materialize_task_pack(candidate: Mapping[str, Any], task_dir: Path, repo_path: Path) -> dict[str, Any]:
    shutil.rmtree(task_dir, ignore_errors=True)
    public_dir = task_dir / "public"
    verifier_dir = task_dir / "verifier"
    public_dir.mkdir(parents=True)
    verifier_dir.mkdir(parents=True)
    task_id = "rich__wstar_direct_pilot__001"
    (public_dir / "statement.md").write_text(
        f"# {task_id}\n\n## Problem Statement\n\n{problem_statement(str(candidate['subject']))}\n",
        encoding="utf-8",
    )
    command = str(candidate["verifier_command"])
    run_path = verifier_dir / "run.sh"
    run_path.write_text(verifier_script(command), encoding="utf-8")
    run_path.chmod(run_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    hidden_files: list[str] = []
    for test_file in candidate.get("test_files", []):
        content = git_show_file(repo_path, str(candidate["commit"]), str(test_file))
        hidden_path = verifier_dir / "hidden" / str(test_file)
        hidden_path.parent.mkdir(parents=True, exist_ok=True)
        hidden_path.write_text(content, encoding="utf-8")
        hidden_files.append(str(test_file))
    task = {
        "schema_version": "core-narrative.task.v1",
        "task_id": task_id,
        "repo_slug": "rich",
        "split": "W_star",
        "source": {
            "kind": "commit_or_pull_request",
            "base_commit": candidate["base_commit"],
            "target_commit": candidate["commit"],
        },
        "task_family": candidate["family"],
        "task_statement_path": "public/statement.md",
        "allowed_context": {
            "include_git_history_before_base": True,
            "include_issue_text": False,
            "include_pr_text": False,
            "include_reference_patch": False,
        },
        "disallowed_context": [
            "reference patch",
            "target diff",
            "hidden verifier files",
            "target commit",
            "ACUT outputs",
            "W* results",
        ],
        "verifier": {"command": "verifier/run.sh", "timeout_seconds": 120},
        "expected": {"no_op_fails": True, "reference_passes": True},
        "leakage": {"reviewed": True, "notes": "Direct-smoke pilot keeps raw source anchors in ignored private artifacts only."},
        "admission": {"status": "pilot_pending", "reviewer": "codex-rich-direct-smoke-pilot"},
    }
    task_path = task_dir / "task.json"
    write_json(task_path, task)
    return {"task_id": task_id, "task_path": task_path, "hidden_files": hidden_files}


def hidden_verifier_digest(repo_path: Path, candidate: Mapping[str, Any]) -> str:
    files = []
    for test_file in candidate.get("test_files", []):
        content = git_show_file(repo_path, str(candidate["commit"]), str(test_file))
        files.append({"path_digest": sha256_text(str(test_file)), "content_sha256": sha256_text(content)})
    return sha256_text(json.dumps({"command": candidate["verifier_command"], "hidden_files": files}, sort_keys=True))


def prepare_workspace(task_path: Path, repo_path: Path, workspace: Path, artifact_dir: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(PREPARE),
        "--task",
        str(task_path),
        "--source-repo",
        str(repo_path),
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
    steps = [
        ("venv_create", [venv_python, "-m", "venv", ".venv"]),
        ("venv_pip_upgrade", [".venv/bin/python", "-m", "pip", "install", "-q", "--upgrade", "pip"]),
        ("venv_install", [".venv/bin/python", "-m", "pip", "install", "-q", "-e", ".", "pytest", "attrs"]),
    ]
    summaries: dict[str, Any] = {}
    for name, command in steps:
        summary = run_artifact_command(command, artifact_dir=artifact_dir, name=name, cwd=workspace, timeout=timeout_seconds)
        summaries[name] = summary
        if summary["exit_code"] != 0:
            return {"status": "blocked", **summaries}
    return {"status": "installed", **summaries}


def noop_status(exit_code: Any, *, timed_out: bool) -> str:
    if timed_out:
        return "blocked_timeout"
    if exit_code == 0:
        return "passed_unexpected"
    if exit_code in {4, 5}:
        return "blocked_pytest_collection"
    if exit_code is None:
        return "blocked"
    return "failed"


def run_noop_smoke(task_path: Path, repo_path: Path, private_root: Path, install_timeout: int, verifier_timeout: int, venv_python: str) -> dict[str, Any]:
    artifact_dir = private_root / "artifacts/noop"
    workspace = private_root / "workspaces/noop"
    shutil.rmtree(artifact_dir, ignore_errors=True)
    shutil.rmtree(workspace, ignore_errors=True)
    prepare = prepare_workspace(task_path, repo_path, workspace, artifact_dir)
    if prepare["exit_code"] != 0:
        return {"status": "blocked", "prepare": prepare}
    install = install_workspace(workspace, artifact_dir, install_timeout, venv_python)
    if install["status"] != "installed":
        return {"status": "blocked", "install": install}
    verify = run_artifact_command(["bash", str(task_path.parent / "verifier/run.sh")], artifact_dir=artifact_dir, name="noop_verify", cwd=workspace, timeout=verifier_timeout)
    return {
        "status": noop_status(verify.get("exit_code"), timed_out=bool(verify.get("timed_out"))),
        "verifier_exit_code": verify.get("exit_code"),
        "duration_seconds": verify.get("duration_seconds"),
        "public_artifact_redacted": True,
    }


def run_reference_smoke(
    task_path: Path,
    repo_path: Path,
    candidate: Mapping[str, Any],
    private_root: Path,
    install_timeout: int,
    verifier_timeout: int,
    venv_python: str,
) -> dict[str, Any]:
    artifact_dir = private_root / "artifacts/reference"
    workspace = private_root / "workspaces/reference"
    shutil.rmtree(artifact_dir, ignore_errors=True)
    shutil.rmtree(workspace, ignore_errors=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    patch = patch_for_candidate(repo_path, candidate)
    patch_path = artifact_dir / "reference.patch"
    patch_path.write_text(patch, encoding="utf-8")
    prepare = prepare_workspace(task_path, repo_path, workspace, artifact_dir)
    if prepare["exit_code"] != 0:
        return {"status": "blocked", "prepare": prepare, "reference_patch_digest": sha256_text(patch)}
    install = install_workspace(workspace, artifact_dir, install_timeout, venv_python)
    if install["status"] != "installed":
        return {"status": "blocked", "install": install, "reference_patch_digest": sha256_text(patch)}
    output = artifact_dir / "normalized_result.json"
    command = [
        sys.executable,
        str(VERIFY),
        "--workspace",
        str(workspace),
        "--task",
        str(task_path),
        "--patch",
        str(patch_path),
        "--acut-id",
        "reference-gold-smoke",
        "--attempt",
        "1",
        "--run-id",
        "rich_direct_smoke_pilot_reference",
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
        "status": normalized.get("status", "blocked"),
        "verifier_exit_code": verification.get("exit_code"),
        "verify_command_exit_code": summary.get("exit_code"),
        "reference_patch_digest": sha256_text(patch),
        "reference_patch_bytes": len(patch.encode("utf-8")),
        "public_artifact_redacted": True,
    }


def admission_decision(noop: str, reference: str) -> str:
    return "accepted" if noop == "failed" and reference == "passed" else "rejected"


def public_result(
    *,
    candidate: Mapping[str, Any],
    hidden_verifier_digest: str,
    reference_patch_digest: str,
    reference_patch_bytes: int,
    noop: Mapping[str, Any],
    reference: Mapping[str, Any],
    private_root: str,
) -> dict[str, Any]:
    decision = admission_decision(str(noop.get("status")), str(reference.get("status")))
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "repo_slug": "rich",
        "split": "W_star",
        "pilot_scope": "one_direct_oracle_candidate",
        "source_anchor_digest": source_anchor_digest(str(candidate["commit"])),
        "base_anchor_digest": source_anchor_digest(str(candidate["base_commit"])),
        "subject_digest": sha256_text(str(candidate["subject"])),
        "family": candidate["family"],
        "surface": candidate["surface"],
        "source_file_count": candidate["source_file_count"],
        "test_file_count": candidate["test_file_count"],
        "test_node_count": candidate["test_node_count"],
        "changed_file_set_digest": candidate.get("changed_file_set_digest")
        or changed_file_set_digest(list(candidate.get("source_files", [])) + list(candidate.get("test_files", []))),
        "statement_digest": sha256_text(problem_statement(str(candidate["subject"]))),
        "hidden_verifier_digest": hidden_verifier_digest,
        "reference_patch_digest": reference_patch_digest,
        "reference_patch_bytes": reference_patch_bytes,
        "no_op_result": {
            "status": noop.get("status"),
            "verifier_exit_code": noop.get("verifier_exit_code"),
            "public_artifact_redacted": True,
        },
        "reference_result": {
            "status": reference.get("status"),
            "verifier_exit_code": reference.get("verifier_exit_code"),
            "public_artifact_redacted": True,
        },
        "admission_decision": decision,
        "primary_runs_authorized": False,
        "private_artifact_root": private_root,
        "claim_boundary": [
            "This is a one-candidate direct-smoke pilot, not a frozen Rich denominator.",
            "Raw source commits and hidden verifier files are retained only in ignored private artifacts.",
            "No ACUT primary attempt or model call was made.",
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Rich Direct-Smoke Pilot",
            "",
            f"Status: `{payload.get('status')}`",
            f"Generated at: `{payload.get('generated_at')}`",
            "",
            "## Result",
            "",
            f"- Admission decision: `{payload.get('admission_decision')}`",
            f"- No-op status: `{payload.get('no_op_result', {}).get('status') if isinstance(payload.get('no_op_result'), Mapping) else None}`",
            f"- Reference status: `{payload.get('reference_result', {}).get('status') if isinstance(payload.get('reference_result'), Mapping) else None}`",
            f"- Family: `{payload.get('family')}`",
            f"- Test node count: `{payload.get('test_node_count')}`",
            "",
            "Primary R/W* model attempts remain unauthorized. This pilot checks one direct-oracle Rich W* candidate only.",
            "",
        ]
    )


def select_candidate(repo_path: Path, index: int) -> Mapping[str, Any]:
    candidates = [
        candidate
        for candidate in discover_candidates(repo_path)
        if candidate.get("window") == "W_star" and candidate.get("direct_smoke_ready")
    ]
    if not candidates:
        raise ToolError("no Rich W* direct-smoke candidates found")
    if index < 0 or index >= len(candidates):
        raise ToolError("candidate index out of range", index=index, candidate_count=len(candidates))
    return candidates[index]


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_path = Path(args.repo).resolve()
    private_root = Path(args.private_root).resolve()
    if args.force:
        shutil.rmtree(private_root, ignore_errors=True)
    private_root.mkdir(parents=True, exist_ok=True)
    candidate = select_candidate(repo_path, args.candidate_index)
    task_pack = materialize_task_pack(candidate, private_root / "candidate_task_pack", repo_path)
    task_path = Path(task_pack["task_path"])
    hidden_digest = hidden_verifier_digest(repo_path, candidate)
    reference_patch = patch_for_candidate(repo_path, candidate)
    reference_digest = sha256_text(reference_patch)
    noop = run_noop_smoke(
        task_path,
        repo_path,
        private_root,
        args.install_timeout_seconds,
        args.verifier_timeout_seconds,
        args.venv_python,
    )
    reference = run_reference_smoke(
        task_path,
        repo_path,
        candidate,
        private_root,
        args.install_timeout_seconds,
        args.verifier_timeout_seconds,
        args.venv_python,
    )
    payload = public_result(
        candidate=candidate,
        hidden_verifier_digest=hidden_digest,
        reference_patch_digest=reference_digest,
        reference_patch_bytes=len(reference_patch.encode("utf-8")),
        noop=noop,
        reference=reference,
        private_root=repo_relative(private_root),
    )
    output = Path(args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output), "report_path": repo_relative(report)})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
