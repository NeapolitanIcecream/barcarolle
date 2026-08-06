#!/usr/bin/env python3
"""Certify and publish one frozen SWE-bench prepared package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence


if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from barcarolle.records import (  # noqa: E402
    RuntimeConfig,
    WorkspaceConfig,
    canonical_digest,
    canonical_json,
)
from barcarolle.runner import (  # noqa: E402
    TaskPoolConfig,
    build_task_pool_from_package,
)
from barcarolle.task_pool import (  # noqa: E402
    CertificationConfig,
    PreparedCandidatePackage,
    load_prepared_candidate_package,
    open_task_pool_bundle,
    prepared_candidate_build_inputs,
)


def certify_pool(
    *,
    package_manifest: Path,
    repository_path: Path,
    artifact_root: Path,
    pull_images: bool = False,
    summary_path: Path | None = None,
) -> Mapping[str, Any]:
    package = load_prepared_candidate_package(package_manifest)
    _require_complete_repository(repository_path)
    _require_repository_commits(repository_path, package.batch.candidates)
    _require_no_repository_instructions(repository_path, package.batch.candidates)
    _, _, _, check_manifests = prepared_candidate_build_inputs(package)
    image_refs = tuple(
        sorted(
            {
                _required_string(manifest, "image_ref")
                for manifest in check_manifests.values()
            }
        )
    )
    if pull_images:
        _pull_images(image_refs)
    verify_images(image_refs)

    candidates = package.batch.candidates
    workspace_config, runtime_config = certification_configs(
        package,
        check_manifests,
    )
    run = package.manifest.run
    if not isinstance(run, Mapping):
        raise RuntimeError("prepared package generation run is missing")
    task_pool = build_task_pool_from_package(
        package,
        TaskPoolConfig(
            repository_id=package.manifest.repository_id,
            repository_path=repository_path.resolve(),
            artifact_root=artifact_root.resolve(),
            workspace_config=workspace_config,
            runtime_config=runtime_config,
            reference_patches={},
            check_commands={},
            hidden_material_paths={},
            certification_config=CertificationConfig(repeat_count=1),
            metadata={"created_at": _required_string(run, "finished_at")},
        ),
    )
    relative_dir = Path(task_pool.task_records_ref).parent
    published_manifest = artifact_root.resolve() / relative_dir / "task-pool.jsonl"
    bundle = open_task_pool_bundle(published_manifest)
    rejected = tuple(
        evidence
        for evidence in bundle.certification_evidence
        if evidence.get("accepted") is not True
    )
    if rejected or len(bundle.tasks) != len(candidates):
        reasons = "; ".join(
            f"{item.get('candidate_id')}: {item.get('rejection_reasons')}"
            for item in rejected
        )
        raise RuntimeError(
            "SWE-bench Task certification did not accept the full source frame"
            + (f": {reasons}" if reasons else "")
        )
    summary: Mapping[str, Any] = {
        "stage": "certified",
        "repository_id": task_pool.repository_id,
        "candidate_count": len(candidates),
        "task_count": len(bundle.tasks),
        "check_count": len(bundle.checks),
        "dependency_cluster_count": len(
            {task.dependency_cluster_id for task in bundle.tasks}
        ),
        "task_pool_id": task_pool.task_pool_id,
        "task_pool_digest": task_pool.task_pool_digest,
        "task_pool_manifest": str(published_manifest),
        "workspace_config": {
            "workspace_config_id": workspace_config.workspace_config_id,
            "digest": canonical_digest(workspace_config),
        },
        "runtime_config": {
            "runtime_config_id": runtime_config.runtime_config_id,
            "digest": canonical_digest(runtime_config),
        },
        "verified_image_count": len(image_refs),
    }
    if summary_path is not None:
        if summary_path.exists():
            raise FileExistsError(
                f"refusing to overwrite certification summary: {summary_path}"
            )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(canonical_json(summary) + "\n", encoding="utf-8")
    return summary


def certification_configs(
    package: PreparedCandidatePackage,
    check_manifests: Mapping[str, Mapping[str, object]],
) -> tuple[WorkspaceConfig, RuntimeConfig]:
    """Rebuild the exact certification configs used by the published pool."""
    candidates = package.batch.candidates
    base_commits = tuple(candidate.base_commit for candidate in candidates)
    image_refs = tuple(
        sorted(
            {
                _required_string(manifest, "image_ref")
                for manifest in check_manifests.values()
            }
        )
    )
    workspace_config = WorkspaceConfig(
        workspace_config_id=(
            f"swe-bench-static-{package.manifest.manifest_digest[:24]}"
        ),
        repository_checkout_config_digest=canonical_digest(
            {
                "checkout_mode": "exact_commit_fetch_v1",
                "repository_id": package.manifest.repository_id,
                "base_commits": base_commits,
            }
        ),
        submodule_state_digest="submodules-none",
        base_image_digest=canonical_digest(image_refs),
        dependency_lock_digest=canonical_digest(
            {
                "source_protocol_digest": (package.manifest.source_protocol_digest),
                "check_manifests": check_manifests,
            }
        ),
    )
    runtime_config = RuntimeConfig(
        runtime_config_id="swe-bench-static-certification-v1",
        budget_digest="hidden-check-certification-900s",
        retry_policy_digest="no-retry",
        stochastic_settings_digest="deterministic-reference-replay",
        timeout_seconds=max(
            _required_positive_int(candidate.resource_limits, "timeout_seconds")
            for candidate in candidates
        ),
        hardware_profile_digest=None,
    )
    return workspace_config, runtime_config


def _pull_images(image_refs: Sequence[str]) -> None:
    for index, image_ref in enumerate(image_refs, start=1):
        completed = subprocess.run(
            ("docker", "pull", "--platform", "linux/arm64", image_ref),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"could not pull verifier image: {image_ref}")
        if index % 10 == 0 or index == len(image_refs):
            print(
                json.dumps(
                    {
                        "stage": "images_pulled",
                        "complete": index,
                        "total": len(image_refs),
                    }
                ),
                flush=True,
            )


def verify_images(image_refs: Sequence[str]) -> None:
    for image_ref in image_refs:
        completed = subprocess.run(
            ("docker", "image", "inspect", image_ref),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"pinned verifier image is unavailable: {image_ref}")
        payload = json.loads(completed.stdout)
        if not isinstance(payload, list) or len(payload) != 1:
            raise RuntimeError(f"could not inspect pinned image: {image_ref}")
        image = payload[0]
        digests = image.get("RepoDigests") if isinstance(image, Mapping) else None
        architecture = image.get("Architecture") if isinstance(image, Mapping) else None
        if not isinstance(digests, list) or image_ref not in digests:
            raise RuntimeError(f"verifier image digest mismatch: {image_ref}")
        if architecture != "arm64":
            raise RuntimeError(f"verifier image is not arm64: {image_ref}")


def _require_complete_repository(path: Path) -> None:
    completed = subprocess.run(
        ("git", "rev-parse", "--is-inside-work-tree"),
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or completed.stdout.strip() != "true":
        raise RuntimeError("repository_path must be a Git worktree")
    shallow = subprocess.run(
        ("git", "rev-parse", "--is-shallow-repository"),
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if shallow.returncode != 0 or shallow.stdout.strip() == "true":
        raise RuntimeError("repository_path must provide complete base history")
    partial = subprocess.run(
        (
            "git",
            "config",
            "--get-regexp",
            r"^(extensions\.partialclone|remote\..*\.promisor|remote\..*\.partialclonefilter)$",
        ),
        cwd=path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if partial.returncode not in {0, 1} or partial.stdout.strip():
        raise RuntimeError("repository_path must not depend on partial-clone objects")


def _require_repository_commits(
    repository_path: Path,
    candidates: Sequence[Any],
) -> None:
    for candidate in candidates:
        completed = subprocess.run(
            ("git", "cat-file", "-e", f"{candidate.base_commit}^{{commit}}"),
            cwd=repository_path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"repository is missing base commit {candidate.base_commit}"
            )


def _require_no_repository_instructions(
    repository_path: Path,
    candidates: Sequence[Any],
) -> None:
    for candidate in candidates:
        completed = subprocess.run(
            ("git", "ls-tree", "-r", "--name-only", candidate.base_commit),
            cwd=repository_path,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"could not inspect repository at {candidate.base_commit}"
            )
        if any(
            Path(name).name == "AGENTS.md" for name in completed.stdout.splitlines()
        ):
            raise RuntimeError(
                f"repository at {candidate.base_commit} contains AGENTS.md"
            )


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a nonempty string")
    return item


def _required_positive_int(value: Mapping[str, Any], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int) or item <= 0:
        raise ValueError(f"{key} must be a positive integer")
    return item


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-manifest", type=Path, required=True)
    parser.add_argument("--repository-path", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--pull-images", action="store_true")
    parser.add_argument("--summary", type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    summary = certify_pool(
        package_manifest=args.package_manifest,
        repository_path=args.repository_path,
        artifact_root=args.artifact_root,
        pull_images=args.pull_images,
        summary_path=args.summary,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
