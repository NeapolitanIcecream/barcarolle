#!/usr/bin/env python3
"""Run one hidden SWE-bench check in a pinned instance image."""

from __future__ import annotations

# The optional Docker/SWE-bench environment is installed only in the verifier.
# Keep first-party checks enabled without treating absent local packages as debt.
# pyright: reportMissingImports=false, reportMissingModuleSource=false

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping


FAIL_TO_PASS = "FAIL_TO_PASS"
PASS_TO_PASS = "PASS_TO_PASS"
CAPTURE_PATHSPEC = (
    ".",
    ":(top,exclude).barcarolle",
    ":(top,exclude).barcarolle/**",
    ":(top,glob,exclude)**/.pytest_cache/**",
    ":(top,glob,exclude)**/__pycache__/**",
)


def capture_workspace_diff(workspace: Path) -> str:
    subprocess.run(
        (
            "git",
            "add",
            "--intent-to-add",
            "--force",
            "--",
            *CAPTURE_PATHSPEC,
        ),
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    completed = subprocess.run(
        (
            "git",
            "diff",
            "--binary",
            "--no-color",
            "--no-ext-diff",
            "--no-textconv",
            "--no-renames",
            "--src-prefix=a/",
            "--dst-prefix=b/",
            "HEAD",
            "--",
            *CAPTURE_PATHSPEC,
        ),
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout


def summarize_report(
    report: Mapping[str, Any], instance_id: str, patch_digest: str
) -> dict[str, Any]:
    cell = report.get(instance_id)
    if not isinstance(cell, Mapping):
        raise RuntimeError("SWE-bench report is missing the instance result")
    statuses = cell.get("tests_status")
    if not isinstance(statuses, Mapping):
        raise RuntimeError("SWE-bench report is missing test status")
    groups: dict[str, dict[str, int]] = {}
    status_digest_input: dict[str, dict[str, tuple[str, ...]]] = {}
    for group_name in (FAIL_TO_PASS, PASS_TO_PASS):
        group = statuses.get(group_name)
        if not isinstance(group, Mapping):
            raise RuntimeError(f"SWE-bench report is missing {group_name}")
        successes = tuple(
            sorted(_string_tuple(group.get("success"), f"{group_name}.success"))
        )
        failures = tuple(
            sorted(_string_tuple(group.get("failure"), f"{group_name}.failure"))
        )
        groups[group_name] = {
            "success_count": len(successes),
            "failure_count": len(failures),
        }
        status_digest_input[group_name] = {
            "success": successes,
            "failure": failures,
        }
    return {
        "instance_id": instance_id,
        "patch_digest": patch_digest,
        "resolved": cell.get("resolved") is True,
        "state": "scored",
        "status_digest": _json_digest(status_digest_input),
        "tests": groups,
    }


def run_check(
    *,
    bundle: Path,
    image_ref: str,
    raw_output_dir: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    from docker import from_env
    from swebench.harness.docker_utils import (
        cleanup_container,
        copy_to_container,
        exec_run_with_timeout,
    )
    from swebench.harness.grading import get_eval_report
    from swebench.harness.test_spec import TestSpec

    spec_payload = _load_json(bundle / "spec.json")
    instance_id = _required_string(spec_payload, "instance_id")
    base_commit = _required_string(spec_payload, "base_commit")
    spec = TestSpec(
        instance_id=instance_id,
        repo=_required_string(spec_payload, "repo"),
        repo_directory="/testbed",
        version=_required_string(spec_payload, "version"),
        repo_script_list=[],
        eval_script_list=_string_list(
            spec_payload.get("eval_script_list"), "eval_script_list"
        ),
        env_script_list=[],
        arch="arm64",
        FAIL_TO_PASS=_string_list(spec_payload.get(FAIL_TO_PASS), FAIL_TO_PASS),
        PASS_TO_PASS=_string_list(spec_payload.get(PASS_TO_PASS), PASS_TO_PASS),
    )
    patch = capture_workspace_diff(Path.cwd())
    patch_digest = hashlib.sha256(patch.encode("utf-8")).hexdigest()
    run_dir = raw_output_dir / instance_id / patch_digest
    run_dir.mkdir(parents=True, exist_ok=True)
    summary_path = run_dir / "summary.json"
    summary_path.unlink(missing_ok=True)
    prediction = {
        "instance_id": instance_id,
        "model_name_or_path": "barcarolle-check",
        "model_patch": patch,
    }
    client = from_env()
    image = client.images.get(image_ref)
    if image_ref not in image.attrs.get("RepoDigests", ()):
        raise RuntimeError("local image does not match the pinned RepoDigest")
    container_name = f"barcarolle-{instance_id.rsplit('-', 1)[-1]}-{patch_digest[:12]}"
    container = None
    try:
        stale = client.containers.list(
            all=True, filters={"name": f"^{container_name}$"}
        )
        for item in stale:
            item.remove(force=True)
        container = client.containers.create(
            image=image_ref,
            name=container_name,
            user="root",
            detach=True,
            command=["tail", "-f", "/dev/null"],
            platform=spec.platform,
        )
        container.start()
        observed_head = container.exec_run(
            "git rev-parse HEAD", workdir="/testbed", user="root"
        )
        if not isinstance(observed_head.output, bytes):
            raise RuntimeError("instance HEAD command returned streamed output")
        if (
            observed_head.exit_code != 0
            or observed_head.output.decode().strip() != base_commit
        ):
            raise RuntimeError("instance image is not at the expected base commit")
        if patch:
            patch_path = run_dir / "candidate.diff"
            patch_path.write_text(patch, encoding="utf-8")
            copy_to_container(container, patch_path, Path("/tmp/candidate.diff"))
            applied = container.exec_run(
                "git apply --verbose /tmp/candidate.diff",
                workdir="/testbed",
                user="root",
            )
            if applied.exit_code != 0:
                raise RuntimeError("candidate diff did not apply in the instance image")
        eval_path = run_dir / "eval.sh"
        eval_path.write_text(spec.eval_script, encoding="utf-8")
        copy_to_container(container, eval_path, Path("/eval.sh"))
        output, timed_out, runtime_seconds = exec_run_with_timeout(
            container, "/bin/bash /eval.sh", timeout_seconds
        )
        log_dir = run_dir / instance_id
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "test_output.txt"
        log_path.write_text(output, encoding="utf-8")
        if timed_out:
            raise RuntimeError("SWE-bench check timed out")
        report = get_eval_report(
            spec,
            prediction,
            str(log_path),
            include_tests_status=True,
        )
        summary = summarize_report(report, instance_id, patch_digest)
        summary["runtime_seconds"] = runtime_seconds
        _write_json(summary_path, summary)
        return summary
    finally:
        if container is not None:
            cleanup_container(client, container, "quiet")


def _load_json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise RuntimeError(f"{key} must be a non-empty string")
    return item


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise RuntimeError(f"{label} must be a list of strings")
    return value


def _string_tuple(value: object, label: str) -> tuple[str, ...]:
    return tuple(_string_list(value, label))


def _json_digest(value: object) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=Path(".barcarolle/check_bundle"))
    parser.add_argument("--image-ref", required=True)
    parser.add_argument("--raw-output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        summary = run_check(
            bundle=args.bundle,
            image_ref=args.image_ref,
            raw_output_dir=args.raw_output_dir,
            timeout_seconds=args.timeout_seconds,
        )
    except BaseException as exc:
        print(
            json.dumps(
                {"state": "infrastructure_error", "error": type(exc).__name__},
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["resolved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
