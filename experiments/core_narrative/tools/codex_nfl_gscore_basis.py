#!/usr/bin/env python3
"""Record the direct G_score feasibility basis for the core narrative run."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import emit_json, fail, iso_now, load_manifest


TOOL = "codex_nfl_gscore_basis"
REPO_ROOT = Path(__file__).resolve().parents[3]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(REPO_ROOT / "experiments/core_narrative/configs/general_benchmark.yaml"))
    parser.add_argument("--output", required=True)
    return parser.parse_args(list(argv))


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_capture(command: Sequence[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return {"available": False, "error_type": type(exc).__name__}
    return {
        "available": completed.returncode == 0,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip()[:500],
        "stderr": completed.stderr.strip()[:500],
    }


def cache_path_from_config(config: Mapping[str, Any]) -> Path | None:
    subset = config.get("task_subset") if isinstance(config.get("task_subset"), dict) else {}
    attempt = subset.get("materialization_attempt") if isinstance(subset.get("materialization_attempt"), dict) else {}
    raw = attempt.get("cache_path")
    return REPO_ROOT / raw if isinstance(raw, str) and raw else None


def expected_cache_sha(config: Mapping[str, Any]) -> str | None:
    subset = config.get("task_subset") if isinstance(config.get("task_subset"), dict) else {}
    attempt = subset.get("materialization_attempt") if isinstance(subset.get("materialization_attempt"), dict) else {}
    value = attempt.get("sha256_verified")
    if isinstance(value, str) and value:
        return value
    benchmark = config.get("benchmark") if isinstance(config.get("benchmark"), dict) else {}
    snapshot = benchmark.get("snapshot_basis") if isinstance(benchmark.get("snapshot_basis"), dict) else {}
    value = snapshot.get("data_file_sha256")
    return value if isinstance(value, str) and value else None


def likely_harness_paths(config: Mapping[str, Any]) -> list[Path]:
    harness = config.get("benchmark", {}).get("evaluation_harness", {}) if isinstance(config.get("benchmark"), dict) else {}
    repo = harness.get("repo") if isinstance(harness, dict) else None
    names = ["SWE-bench_Pro-os", "swebench_pro_os"]
    if isinstance(repo, str) and "/" in repo:
        names.append(repo.rsplit("/", 1)[-1])
    roots = [
        REPO_ROOT / "experiments/core_narrative/external_repos",
        REPO_ROOT / "experiments/core_narrative/cache",
        REPO_ROOT / "external_repos",
    ]
    return [root / name for root in roots for name in names]


def build_basis(config_path: Path) -> dict[str, Any]:
    config = load_manifest(config_path)
    cache_path = cache_path_from_config(config)
    expected_sha = expected_cache_sha(config)
    observed_sha = sha256_file(cache_path) if cache_path is not None else None
    harness_candidates = likely_harness_paths(config)
    existing_harnesses = [path for path in harness_candidates if path.exists()]
    docker = run_capture(["docker", "--version"])

    blockers: list[dict[str, Any]] = []
    if cache_path is None:
        blockers.append({"blocker": "dataset_cache_path_missing_from_config"})
    elif not cache_path.exists():
        blockers.append({"blocker": "dataset_cache_missing", "path": str(cache_path)})
    elif expected_sha and observed_sha != expected_sha:
        blockers.append(
            {
                "blocker": "dataset_cache_sha256_mismatch",
                "path": str(cache_path),
                "expected_sha256": expected_sha,
                "observed_sha256": observed_sha,
            }
        )
    if not existing_harnesses:
        blockers.append(
            {
                "blocker": "evaluation_harness_checkout_missing",
                "checked_paths": [str(path) for path in harness_candidates],
            }
        )
    if not docker["available"]:
        blockers.append({"blocker": "docker_unavailable", "diagnostic": docker})

    direct_feasible = not blockers
    return {
        "tool": TOOL,
        "status": "direct_gscore_feasible" if direct_feasible else "direct_gscore_blocked",
        "generated_at": iso_now(),
        "config_path": str(config_path),
        "direct_gscore_feasible_now": direct_feasible,
        "direct_gscore_used": False,
        "g_score_basis": "direct_run_unavailable" if blockers else "direct_smoke_required_before_scoring",
        "g_scores": {},
        "external_public_or_proxy_scores": {
            "used": False,
            "evidence_strength": "not_used",
            "comparability": "no public/proxy G_score values were substituted",
        },
        "checks": {
            "dataset_cache": {
                "path": str(cache_path) if cache_path is not None else None,
                "exists": cache_path.exists() if cache_path is not None else False,
                "expected_sha256": expected_sha,
                "observed_sha256": observed_sha,
            },
            "evaluation_harness": {
                "existing_paths": [str(path) for path in existing_harnesses],
                "checked_paths": [str(path) for path in harness_candidates],
            },
            "docker": docker,
        },
        "blockers": blockers,
        "next_defensible_action": (
            "materialize the pinned SWE-Bench Pro dataset cache and evaluator checkout, then run a gold-patch smoke on the locked six-task slice"
            if blockers
            else "run the smallest gold-patch smoke before any ACUT G_score model calls"
        ),
        "claim_limitations": [
            "No direct G_score values are available from this run.",
            "Prediction analysis must treat G_score as unavailable, not as zero.",
            "Public or external scores would be weak, scaffold-mismatched evidence and are not used here.",
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_basis(Path(args.config))
        emit_json(payload, args.output)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
