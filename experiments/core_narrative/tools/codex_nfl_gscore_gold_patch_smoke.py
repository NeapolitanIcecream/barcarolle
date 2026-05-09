#!/usr/bin/env python3
"""No-model gold-patch smoke for the pinned SWE-Bench Pro G_score basis."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, write_json


TOOL = "codex_nfl_gscore_gold_patch_smoke"
SCHEMA_VERSION = "core-narrative.gscore-gold-patch-smoke.v1"
SCORE_PARSER_SCHEMA_VERSION = "core-narrative.gscore-score-parser.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG = REPO_ROOT / "experiments/core_narrative/configs/general_benchmark.yaml"
DEFAULT_RESULTS_RAW = REPO_ROOT / "experiments/core_narrative/results/raw"

EXPECTED_CONFIG = {
    "id": "gscore_swebench_pro_public_6_v1",
    "status": "locked",
    "benchmark.name": "SWE-Bench Pro Public",
    "benchmark.dataset_id": "ScaleAI/SWE-bench_Pro",
    "benchmark.dataset_config": "default",
    "benchmark.split": "test",
    "benchmark.snapshot_basis.huggingface_revision": "7ab5114912baf22bb098818e604c02fe7ad2c11f",
    "benchmark.snapshot_basis.data_file_commit": "2dd05cab1572ce1d59fdc699b386692ff8e0bd29",
    "benchmark.snapshot_basis.data_file_path": "data/test-00000-of-00001.parquet",
    "benchmark.snapshot_basis.data_file_sha256": "c8cd7115496ad4e9a8b21d088cef576a65bf821bb542b24336f13f714cef13f8",
    "benchmark.snapshot_basis.rows": 731,
    "benchmark.evaluation_harness.repo": "scaleapi/SWE-bench_Pro-os",
    "benchmark.evaluation_harness.revision": "0c64e26f00b9c190432de7fc520c8ceed5c25518",
    "benchmark.evaluation_harness.entrypoint": "swe_bench_pro_eval.py",
    "task_subset.name": "barcarolle_gscore_swebp_public_6_v1",
    "task_subset.target_size": 6,
    "task_subset.selection_status": "locked",
    "task_subset.selection_rule.salt": "barcarolle-core-narrative-gscore-v1",
    "score_basis.direct_run": True,
    "score_basis.external_public_scores_used_for_g_score": False,
}

REQUIRED_ROW_FIELDS = [
    "instance_id",
    "repo",
    "patch",
    "before_repo_set_cmd",
    "selected_test_files_to_run",
    "base_commit",
    "fail_to_pass",
    "pass_to_pass",
    "dockerhub_tag",
]
OPTIONAL_EXPECTED_ROW_FIELDS = ["test_patch"]
EVALUATOR_OUTPUT_FILE = "eval_results.json"
GOLD_PATCH_PREFIX = "gold_patch_smoke"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Pinned general benchmark config.")
    parser.add_argument("--output", required=True, help="Machine-readable smoke JSON output path.")
    parser.add_argument("--report", help="Optional Markdown report output path.")
    parser.add_argument("--artifact-dir", help="Raw artifact directory. Defaults under results/raw/<output-stem>.")
    parser.add_argument("--dataset-cache", help="Override the dataset cache path from the config.")
    parser.add_argument("--harness-path", help="Override the evaluator checkout path.")
    parser.add_argument(
        "--execute-gold-patch",
        action="store_true",
        help="Run the pinned evaluator on gold patches if all preflight checks pass.",
    )
    parser.add_argument(
        "--backend",
        choices=["local-docker", "modal"],
        default="local-docker",
        help="Evaluator runtime backend to use when --execute-gold-patch is set.",
    )
    parser.add_argument("--num-workers", type=int, default=1, help="Evaluator workers for an executed smoke.")
    parser.add_argument("--timeout-seconds", type=int, default=14_400, help="Evaluator subprocess timeout.")
    parser.add_argument("--dockerhub-username", default="jefzda", help="Docker Hub user for sweap-images.")
    parser.add_argument("--docker-platform", help="Optional Docker platform override for local Docker.")
    parser.add_argument("--python", default=sys.executable, help="Python executable for the evaluator subprocess.")
    return parser.parse_args(list(argv))


def get_path(mapping: Mapping[str, Any], dotted: str) -> Any:
    value: Any = mapping
    for part in dotted.split("."):
        if not isinstance(value, Mapping):
            return None
        value = value.get(part)
    return value


def as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def resolve_repo_path(path: str | Path | None) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def cache_path_from_config(config: Mapping[str, Any], override: str | None = None) -> Path | None:
    if override:
        return resolve_repo_path(override)
    raw = get_path(config, "task_subset.materialization_attempt.cache_path")
    return resolve_repo_path(raw) if isinstance(raw, str) and raw else None


def expected_cache_sha(config: Mapping[str, Any]) -> str | None:
    value = get_path(config, "task_subset.materialization_attempt.sha256_verified")
    if isinstance(value, str) and value:
        return value
    value = get_path(config, "benchmark.snapshot_basis.data_file_sha256")
    return value if isinstance(value, str) and value else None


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_capture(command: Sequence[str], *, cwd: Path | None = None, timeout: int = 20) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:
        return {"available": False, "error_type": type(exc).__name__, "error": str(exc)[:500]}
    return {
        "available": completed.returncode == 0,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip()[:1000],
        "stderr": completed.stderr.strip()[:1000],
    }


def blocker(name: str, **details: Any) -> dict[str, Any]:
    return {"blocker": name, **details}


def likely_harness_paths(config: Mapping[str, Any], override: str | None = None) -> list[Path]:
    if override:
        resolved = resolve_repo_path(override)
        return [] if resolved is None else [resolved]
    repo = get_path(config, "benchmark.evaluation_harness.repo")
    names = ["SWE-bench_Pro-os", "swebench_pro_os"]
    if isinstance(repo, str) and "/" in repo:
        names.append(repo.rsplit("/", 1)[-1])
    roots = [
        REPO_ROOT / "experiments/core_narrative/external_repos",
        REPO_ROOT / "experiments/core_narrative/cache",
        REPO_ROOT / "external_repos",
    ]
    paths: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        for name in names:
            path = root / name
            key = str(path)
            if key not in seen:
                paths.append(path)
                seen.add(key)
    return paths


def locked_tasks(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    tasks = as_list(get_path(config, "task_subset.locked_task_ids"))
    return [dict(task) for task in tasks if isinstance(task, Mapping)]


def validate_pinned_config(config: Mapping[str, Any]) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    metadata_checks: dict[str, Any] = {}
    for dotted, expected in EXPECTED_CONFIG.items():
        observed = get_path(config, dotted)
        passed = observed == expected
        metadata_checks[dotted] = {"expected": expected, "observed": observed, "passed": passed}
        if not passed:
            blockers.append(blocker("pinned_metadata_mismatch", field=dotted, expected=expected, observed=observed))

    tasks = locked_tasks(config)
    target_size = get_path(config, "task_subset.target_size")
    denominator_formula = get_path(config, "scoring_method.formula")
    denominator_policy = get_path(config, "scoring_method.denominator_policy")
    ordinals = [task.get("ordinal") for task in tasks]
    instance_ids = [task.get("instance_id") for task in tasks if isinstance(task.get("instance_id"), str)]
    repos = [task.get("repo") for task in tasks if isinstance(task.get("repo"), str)]
    denominator_passed = (
        target_size == 6
        and len(tasks) == 6
        and len(set(instance_ids)) == 6
        and ordinals == [1, 2, 3, 4, 5, 6]
        and isinstance(denominator_formula, str)
        and "/ 6" in denominator_formula
        and isinstance(denominator_policy, str)
        and "fixed" in denominator_policy.lower()
    )
    if not denominator_passed:
        blockers.append(
            blocker(
                "pinned_task_denominator_mismatch",
                target_size=target_size,
                locked_task_count=len(tasks),
                unique_instance_id_count=len(set(instance_ids)),
                ordinals=ordinals,
                formula=denominator_formula,
                denominator_policy=denominator_policy,
            )
        )

    salt = get_path(config, "task_subset.selection_rule.salt")
    selection_key_checks: list[dict[str, Any]] = []
    for task in tasks:
        instance_id = task.get("instance_id")
        observed_key = task.get("selection_key")
        expected_key = None
        passed = False
        if isinstance(salt, str) and isinstance(instance_id, str):
            expected_key = hashlib.sha256(f"{salt}\n{instance_id}".encode("utf-8")).hexdigest()
            passed = observed_key == expected_key
        selection_key_checks.append(
            {
                "ordinal": task.get("ordinal"),
                "repo": task.get("repo"),
                "instance_id": instance_id,
                "expected_selection_key": expected_key,
                "observed_selection_key": observed_key,
                "passed": passed,
            }
        )
        if not passed:
            blockers.append(
                blocker(
                    "selection_key_mismatch",
                    ordinal=task.get("ordinal"),
                    instance_id=instance_id,
                    expected_selection_key=expected_key,
                    observed_selection_key=observed_key,
                )
            )

    repo_counts: dict[str, int] = {}
    for repo in repos:
        repo_counts[repo] = repo_counts.get(repo, 0) + 1
    expected_repo_counts = {"NodeBB/NodeBB": 2, "ansible/ansible": 2, "element-hq/element-web": 2}
    repo_stratification_passed = repo_counts == expected_repo_counts
    if not repo_stratification_passed:
        blockers.append(blocker("selection_repo_stratification_mismatch", expected=expected_repo_counts, observed=repo_counts))

    return {
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "metadata_checks": metadata_checks,
        "denominator": {
            "passed": denominator_passed,
            "target_size": target_size,
            "locked_task_count": len(tasks),
            "unique_instance_id_count": len(set(instance_ids)),
            "ordinals": ordinals,
            "formula": denominator_formula,
            "denominator_policy": denominator_policy,
        },
        "selection_rule": {
            "salt": salt,
            "selection_key_checks": selection_key_checks,
            "repo_counts": repo_counts,
            "repo_stratification_passed": repo_stratification_passed,
            "algorithm": get_path(config, "task_subset.selection_rule.algorithm"),
            "replacement_rule": get_path(config, "task_subset.replacement_rule"),
        },
    }


def read_json_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        rows = data
    elif isinstance(data, Mapping):
        for key in ("rows", "data", "results"):
            if isinstance(data.get(key), list):
                rows = data[key]
                break
        else:
            raise ToolError("JSON dataset cache must be a list or contain rows/data/results", path=str(path))
    else:
        raise ToolError("JSON dataset cache root must be a list or object", path=str(path))
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def read_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, Mapping):
            raise ToolError("JSONL dataset row must be an object", path=str(path), line_number=line_number)
        rows.append(dict(row))
    return rows


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_parquet_rows(path: Path) -> list[dict[str, Any]]:
    try:
        import pyarrow.parquet as pq  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ToolError("parquet reader unavailable", dependency="pyarrow") from exc
    table = pq.read_table(path)
    return [dict(row) for row in table.to_pylist()]


def read_dataset_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return read_json_rows(path)
    if suffix == ".jsonl":
        return read_jsonl_rows(path)
    if suffix == ".csv":
        return read_csv_rows(path)
    if suffix == ".parquet":
        return read_parquet_rows(path)
    raise ToolError("unsupported dataset cache format", path=str(path), suffix=suffix)


def parse_listish(value: Any) -> dict[str, Any]:
    if isinstance(value, list):
        return {"parseable": True, "count": len(value)}
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return {"parseable": False, "reason": "empty_string"}
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            try:
                import ast

                parsed = ast.literal_eval(stripped)
            except Exception as exc:
                return {"parseable": False, "reason": type(exc).__name__}
        return {"parseable": isinstance(parsed, list), "count": len(parsed) if isinstance(parsed, list) else None}
    return {"parseable": False, "reason": type(value).__name__}


def validate_dataset_rows(config: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    locked = locked_tasks(config)
    expected_ids = [str(task["instance_id"]) for task in locked if isinstance(task.get("instance_id"), str)]
    rows_by_id = {str(row.get("instance_id")): dict(row) for row in rows if isinstance(row.get("instance_id"), str)}
    missing_ids = [instance_id for instance_id in expected_ids if instance_id not in rows_by_id]
    if missing_ids:
        blockers.append(blocker("locked_task_rows_missing_from_dataset_cache", missing_instance_ids=missing_ids))

    expected_rows = get_path(config, "benchmark.snapshot_basis.rows")
    row_count_passed = expected_rows is None or len(rows) == expected_rows
    if not row_count_passed:
        blockers.append(blocker("dataset_row_count_mismatch", expected_rows=expected_rows, observed_rows=len(rows)))

    selection_from_dataset = validate_selection_against_dataset(config, rows, expected_ids)
    blockers.extend(selection_from_dataset["blockers"])

    task_checks: list[dict[str, Any]] = []
    for task in locked:
        instance_id = str(task.get("instance_id"))
        row = rows_by_id.get(instance_id)
        if row is None:
            continue
        missing_fields = [field for field in REQUIRED_ROW_FIELDS if field not in row]
        empty_required_fields = [
            field
            for field in REQUIRED_ROW_FIELDS
            if field in row and (row[field] is None or (isinstance(row[field], str) and not row[field].strip()))
        ]
        missing_optional_fields = [field for field in OPTIONAL_EXPECTED_ROW_FIELDS if field not in row]
        fail_to_pass_parse = parse_listish(row.get("fail_to_pass"))
        pass_to_pass_parse = parse_listish(row.get("pass_to_pass"))
        repo_matches = row.get("repo") == task.get("repo")
        check = {
            "ordinal": task.get("ordinal"),
            "instance_id": instance_id,
            "repo": task.get("repo"),
            "row_present": True,
            "repo_matches_config": repo_matches,
            "missing_required_fields": missing_fields,
            "empty_required_fields": empty_required_fields,
            "missing_optional_expected_fields": missing_optional_fields,
            "fail_to_pass": fail_to_pass_parse,
            "pass_to_pass": pass_to_pass_parse,
            "gold_patch_bytes": len(str(row.get("patch", "")).encode("utf-8")) if "patch" in row else 0,
            "dockerhub_tag": row.get("dockerhub_tag"),
        }
        task_checks.append(check)
        if missing_fields or empty_required_fields or missing_optional_fields:
            blockers.append(
                blocker(
                    "gold_patch_or_evaluator_row_fields_missing",
                    instance_id=instance_id,
                    missing_required_fields=missing_fields,
                    empty_required_fields=empty_required_fields,
                    missing_optional_expected_fields=missing_optional_fields,
                )
            )
        if not repo_matches:
            blockers.append(
                blocker("locked_task_repo_mismatch", instance_id=instance_id, expected=task.get("repo"), observed=row.get("repo"))
            )
        if not fail_to_pass_parse.get("parseable") or not pass_to_pass_parse.get("parseable"):
            blockers.append(
                blocker(
                    "evaluator_test_list_unparseable",
                    instance_id=instance_id,
                    fail_to_pass=fail_to_pass_parse,
                    pass_to_pass=pass_to_pass_parse,
                )
            )

    return {
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "row_count": len(rows),
        "expected_row_count": expected_rows,
        "row_count_passed": row_count_passed,
        "selection_from_dataset": selection_from_dataset,
        "locked_rows_present_count": len(expected_ids) - len(missing_ids),
        "locked_task_checks": task_checks,
    }


def selection_key(salt: str, instance_id: str) -> str:
    return hashlib.sha256(f"{salt}\n{instance_id}".encode("utf-8")).hexdigest()


def compute_selection_from_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    salt: str,
    target_size: int,
    rows_per_repo: int,
) -> list[dict[str, str]]:
    groups: dict[str, list[str]] = {}
    for row in rows:
        repo = row.get("repo")
        instance_id = row.get("instance_id")
        if isinstance(repo, str) and isinstance(instance_id, str):
            groups.setdefault(repo, []).append(instance_id)

    selected: list[dict[str, str]] = []
    for repo in sorted(groups):
        for instance_id in sorted(groups[repo], key=lambda value: (selection_key(salt, value), value))[:rows_per_repo]:
            selected.append(
                {
                    "repo": repo,
                    "instance_id": instance_id,
                    "selection_key": selection_key(salt, instance_id),
                }
            )
            if len(selected) >= target_size:
                return selected
    return selected


def validate_selection_against_dataset(
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    expected_instance_ids: Sequence[str],
) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    salt = get_path(config, "task_subset.selection_rule.salt")
    target_size = get_path(config, "task_subset.target_size")
    rows_per_repo = get_path(config, "task_subset.stratification.rows_per_repo")
    if not isinstance(salt, str) or not isinstance(target_size, int) or not isinstance(rows_per_repo, int):
        return {
            "status": "blocked",
            "blockers": [
                blocker(
                    "selection_rule_parameters_missing",
                    salt=salt,
                    target_size=target_size,
                    rows_per_repo=rows_per_repo,
                )
            ],
            "computed_selection": [],
            "expected_instance_ids": list(expected_instance_ids),
        }

    computed = compute_selection_from_rows(rows, salt=salt, target_size=target_size, rows_per_repo=rows_per_repo)
    computed_ids = [item["instance_id"] for item in computed]
    if computed_ids != list(expected_instance_ids):
        blockers.append(
            blocker(
                "dataset_selection_rule_mismatch",
                expected_instance_ids=list(expected_instance_ids),
                computed_instance_ids=computed_ids,
            )
        )
    return {
        "status": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "computed_selection": computed,
        "expected_instance_ids": list(expected_instance_ids),
    }


def materialize_gold_patch_inputs(
    *,
    config: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    artifact_dir: Path,
) -> dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    rows_by_id = {str(row.get("instance_id")): dict(row) for row in rows if isinstance(row.get("instance_id"), str)}
    selected_rows: list[dict[str, Any]] = []
    patches: list[dict[str, Any]] = []
    for task in locked_tasks(config):
        instance_id = str(task["instance_id"])
        row = dict(rows_by_id[instance_id])
        selected_rows.append(row)
        patches.append({"instance_id": instance_id, "patch": str(row["patch"]), "prefix": GOLD_PATCH_PREFIX})

    raw_sample_path = artifact_dir / "gold_patch_raw_samples.jsonl"
    with raw_sample_path.open("w", encoding="utf-8") as handle:
        for row in selected_rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    patch_path = artifact_dir / "gold_patches.json"
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(json.dumps(patches, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest_path = artifact_dir / "gold_patch_artifact_manifest.json"
    manifest = {
        "schema_version": "core-narrative.gscore-gold-patch-artifacts.v1",
        "raw_sample_path": str(raw_sample_path),
        "patch_path": str(patch_path),
        "patch_format": [{"instance_id": "string", "patch": "git patch content", "prefix": GOLD_PATCH_PREFIX}],
        "selected_instance_ids": [patch["instance_id"] for patch in patches],
        "selected_task_count": len(patches),
    }
    write_json(manifest_path, manifest)
    return {
        "status": "materialized",
        "artifact_dir": str(artifact_dir),
        "raw_sample_path": str(raw_sample_path),
        "patch_path": str(patch_path),
        "manifest_path": str(manifest_path),
        "selected_task_count": len(patches),
        "patch_bytes_total": sum(len(patch["patch"].encode("utf-8")) for patch in patches),
    }


def validate_dataset_cache(
    *,
    config: Mapping[str, Any],
    dataset_override: str | None,
    artifact_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]] | None, dict[str, Any] | None]:
    blockers: list[dict[str, Any]] = []
    cache_path = cache_path_from_config(config, dataset_override)
    expected_sha = expected_cache_sha(config)
    observed_sha = sha256_file(cache_path) if cache_path is not None else None
    rows: list[dict[str, Any]] | None = None
    row_validation: dict[str, Any] | None = None
    materialized: dict[str, Any] | None = None

    cache_check: dict[str, Any] = {
        "path": str(cache_path) if cache_path is not None else None,
        "exists": cache_path.exists() if cache_path is not None else False,
        "expected_sha256": expected_sha,
        "observed_sha256": observed_sha,
        "row_validation": None,
        "gold_patch_artifacts": None,
    }
    if cache_path is None:
        blockers.append(blocker("dataset_cache_path_missing_from_config"))
    elif not cache_path.exists():
        blockers.append(blocker("dataset_cache_missing", path=str(cache_path)))
    elif expected_sha and observed_sha != expected_sha:
        blockers.append(
            blocker(
                "dataset_cache_sha256_mismatch",
                path=str(cache_path),
                expected_sha256=expected_sha,
                observed_sha256=observed_sha,
            )
        )
    else:
        try:
            rows = read_dataset_rows(cache_path)
        except ToolError as exc:
            if exc.details.get("dependency") == "pyarrow":
                blockers.append(blocker("parquet_reader_unavailable", dependency="pyarrow", path=str(cache_path)))
            else:
                blockers.append(blocker("dataset_cache_read_failed", path=str(cache_path), error=str(exc), details=exc.details))
        else:
            row_validation = validate_dataset_rows(config, rows)
            cache_check["row_validation"] = row_validation
            blockers.extend(row_validation["blockers"])
            if not row_validation["blockers"]:
                materialized = materialize_gold_patch_inputs(config=config, rows=rows, artifact_dir=artifact_dir)
                cache_check["gold_patch_artifacts"] = materialized

    cache_check["status"] = "passed" if not blockers else "blocked"
    cache_check["blockers"] = blockers
    return cache_check, rows, materialized


def validate_harness(
    *,
    config: Mapping[str, Any],
    harness_override: str | None,
    backend: str,
    execute: bool,
    python_executable: str,
) -> dict[str, Any]:
    blockers: list[dict[str, Any]] = []
    candidates = likely_harness_paths(config, harness_override)
    existing = [path for path in candidates if path.exists()]
    selected = existing[0] if existing else None
    revision = get_path(config, "benchmark.evaluation_harness.revision")
    entrypoint = get_path(config, "benchmark.evaluation_harness.entrypoint")
    check: dict[str, Any] = {
        "status": "blocked",
        "selected_path": str(selected) if selected is not None else None,
        "existing_paths": [str(path) for path in existing],
        "checked_paths": [str(path) for path in candidates],
        "expected_revision": revision,
        "entrypoint": entrypoint,
        "entrypoint_exists": False,
        "run_scripts_dir_exists": False,
        "dockerfiles_dir_exists": False,
        "git_head": None,
        "python_dependency_check": None,
        "blockers": blockers,
    }
    if selected is None:
        blockers.append(blocker("evaluation_harness_checkout_missing", checked_paths=[str(path) for path in candidates]))
        return check
    if not selected.is_dir():
        blockers.append(blocker("evaluation_harness_path_not_directory", path=str(selected)))
        return check

    git_head = run_capture(["git", "rev-parse", "HEAD"], cwd=selected)
    check["git_head"] = git_head
    observed_head = git_head.get("stdout") if git_head.get("available") else None
    if not observed_head:
        blockers.append(blocker("evaluation_harness_git_head_unavailable", path=str(selected), diagnostic=git_head))
    elif isinstance(revision, str) and observed_head != revision:
        blockers.append(blocker("evaluation_harness_revision_mismatch", path=str(selected), expected=revision, observed=observed_head))

    entrypoint_path = selected / str(entrypoint)
    check["entrypoint_exists"] = entrypoint_path.exists()
    if not entrypoint_path.exists():
        blockers.append(blocker("evaluation_harness_entrypoint_missing", path=str(entrypoint_path)))

    run_scripts_dir = selected / "run_scripts"
    dockerfiles_dir = selected / "dockerfiles"
    check["run_scripts_dir_exists"] = run_scripts_dir.exists()
    check["dockerfiles_dir_exists"] = dockerfiles_dir.exists()
    if not run_scripts_dir.exists():
        blockers.append(blocker("evaluation_harness_run_scripts_missing", path=str(run_scripts_dir)))
    if not dockerfiles_dir.exists():
        blockers.append(blocker("evaluation_harness_dockerfiles_missing", path=str(dockerfiles_dir)))

    if execute:
        imports = ["pandas", "tqdm"]
        imports.append("docker" if backend == "local-docker" else "modal")
        import_code = "; ".join(f"import {name}" for name in imports)
        dependency_check = run_capture([python_executable, "-c", import_code], cwd=selected)
        check["python_dependency_check"] = {**dependency_check, "imports": imports}
        if not dependency_check.get("available"):
            blockers.append(blocker("evaluation_harness_python_dependency_missing", imports=imports, diagnostic=dependency_check))

    check["status"] = "passed" if not blockers else "blocked"
    check["blockers"] = blockers
    return check


def docker_check(backend: str, execute: bool) -> dict[str, Any]:
    version = run_capture(["docker", "--version"])
    info = run_capture(["docker", "info", "--format", "{{json .ServerVersion}} {{json .OperatingSystem}}"])
    required = backend == "local-docker"
    blockers: list[dict[str, Any]] = []
    if required and not version.get("available"):
        blockers.append(blocker("docker_unavailable", diagnostic=version))
    if required and not info.get("available"):
        blockers.append(blocker("docker_daemon_unavailable", diagnostic=info))
    return {
        "status": "passed" if not blockers else "blocked",
        "backend": backend,
        "required_for_selected_backend": required,
        "execute_gold_patch_requested": execute,
        "version": version,
        "info": info,
        "host_platform": platform.platform(),
        "machine": platform.machine(),
        "blockers": blockers,
    }


def evaluator_command(
    *,
    config: Mapping[str, Any],
    harness_path: Path,
    materialized_artifacts: Mapping[str, Any],
    output_dir: Path,
    backend: str,
    num_workers: int,
    dockerhub_username: str,
    docker_platform: str | None,
    python_executable: str,
) -> list[str]:
    entrypoint = harness_path / str(get_path(config, "benchmark.evaluation_harness.entrypoint"))
    scripts_dir = harness_path / "run_scripts"
    command = [
        python_executable,
        str(entrypoint),
        f"--raw_sample_path={materialized_artifacts['raw_sample_path']}",
        f"--patch_path={materialized_artifacts['patch_path']}",
        f"--output_dir={output_dir}",
        f"--scripts_dir={scripts_dir}",
        f"--dockerhub_username={dockerhub_username}",
        f"--num_workers={num_workers}",
        "--redo",
    ]
    if backend == "local-docker":
        command.append("--use_local_docker")
        if docker_platform:
            command.append(f"--docker_platform={docker_platform}")
    return command


def run_evaluator(
    *,
    command: Sequence[str],
    cwd: Path,
    artifact_dir: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    stdout_path = artifact_dir / "evaluator.stdout.txt"
    stderr_path = artifact_dir / "evaluator.stderr.txt"
    command_path = artifact_dir / "evaluator_command.json"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    started_at = iso_now()
    try:
        with stdout_path.open("w", encoding="utf-8") as stdout_file:
            with stderr_path.open("w", encoding="utf-8") as stderr_file:
                completed = subprocess.run(
                    list(command),
                    cwd=str(cwd),
                    stdout=stdout_file,
                    stderr=stderr_file,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
        exit_code = completed.returncode
        timed_out = False
        error = None
    except subprocess.TimeoutExpired:
        exit_code = None
        timed_out = True
        error = "timeout"
    finished_at = iso_now()
    summary = {
        "command": list(command),
        "cwd": str(cwd),
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": round(time.monotonic() - started, 3),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "error": error,
        "stdout_artifact": str(stdout_path),
        "stderr_artifact": str(stderr_path),
    }
    write_json(command_path, summary)
    return {**summary, "command_artifact": str(command_path)}


def coerce_json_boolean(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def coerce_permissive_resolved(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "passed", "pass", "resolved", "success", "1"}:
            return True
        if normalized in {"false", "failed", "fail", "unresolved", "error", "0"}:
            return False
    return None


def extract_result_mapping(payload: Any) -> tuple[dict[str, Any] | None, str]:
    if isinstance(payload, Mapping):
        for key in ("eval_results", "results_by_instance", "instance_results"):
            value = payload.get(key)
            if isinstance(value, Mapping):
                return dict(value), key
        for key in ("results", "instances"):
            value = payload.get(key)
            if isinstance(value, list):
                mapping: dict[str, Any] = {}
                for item in value:
                    if not isinstance(item, Mapping):
                        continue
                    instance_id = item.get("instance_id")
                    if not isinstance(instance_id, str):
                        continue
                    if "resolved" in item:
                        mapping[instance_id] = item["resolved"]
                    elif "passed" in item:
                        mapping[instance_id] = item["passed"]
                    elif "status" in item:
                        mapping[instance_id] = item["status"]
                return mapping, key
        if all(isinstance(key, str) for key in payload.keys()):
            return dict(payload), "direct_instance_mapping"
    return None, "unknown"


def _parse_score_payload(
    payload: Any,
    expected_instance_ids: Sequence[str],
    *,
    value_semantics: str,
    coerce_value: Any,
    parsed_status: str,
    proof_capable: bool,
) -> dict[str, Any]:
    expected = list(expected_instance_ids)
    mapping, source_shape = extract_result_mapping(payload)
    if mapping is None:
        return {
            "schema_version": SCORE_PARSER_SCHEMA_VERSION,
            "status": "invalid",
            "source_shape": source_shape,
            "value_semantics": value_semantics,
            "proof_eligible": False,
            "expected_denominator": len(expected),
            "denominator": len(expected),
            "resolved_count": 0,
            "resolved_rate_percent": None,
            "missing_instance_ids": expected,
            "unexpected_instance_ids": [],
            "invalid_entries": [{"reason": "no_instance_result_mapping"}],
            "unresolved_instance_ids": expected,
        }

    normalized: dict[str, bool] = {}
    invalid_entries: list[dict[str, Any]] = []
    for instance_id, value in mapping.items():
        resolved = coerce_value(value)
        if resolved is None:
            reason = (
                "not_json_boolean_resolved_status"
                if value_semantics == "json_boolean_proof"
                else "unrecognized_resolved_status"
            )
            invalid_entries.append({"instance_id": instance_id, "value": value, "reason": reason})
        else:
            normalized[str(instance_id)] = resolved

    expected_set = set(expected)
    observed_set = set(normalized)
    raw_observed_set = {str(instance_id) for instance_id in mapping}
    missing = [instance_id for instance_id in expected if instance_id not in observed_set]
    unexpected = sorted(raw_observed_set - expected_set)
    unresolved = [instance_id for instance_id in expected if normalized.get(instance_id) is False or instance_id not in normalized]
    resolved_count = sum(1 for instance_id in expected if normalized.get(instance_id) is True)
    status = parsed_status if not missing and not unexpected and not invalid_entries else "invalid"
    proof_eligible = (
        proof_capable
        and status == "parsed"
        and source_shape == "direct_instance_mapping"
        and resolved_count == len(expected)
    )
    return {
        "schema_version": SCORE_PARSER_SCHEMA_VERSION,
        "status": status,
        "source_shape": source_shape,
        "value_semantics": value_semantics,
        "proof_eligible": proof_eligible,
        "expected_denominator": len(expected),
        "denominator": len(expected),
        "resolved_count": resolved_count,
        "resolved_rate_percent": round(100 * resolved_count / len(expected), 6) if expected else None,
        "missing_instance_ids": missing,
        "unexpected_instance_ids": unexpected,
        "invalid_entries": invalid_entries,
        "unresolved_instance_ids": unresolved,
        "normalized_results": {instance_id: normalized.get(instance_id) for instance_id in expected},
    }


def parse_score_payload(payload: Any, expected_instance_ids: Sequence[str]) -> dict[str, Any]:
    return _parse_score_payload(
        payload,
        expected_instance_ids,
        value_semantics="json_boolean_proof",
        coerce_value=coerce_json_boolean,
        parsed_status="parsed",
        proof_capable=True,
    )


def parse_score_payload_permissive(payload: Any, expected_instance_ids: Sequence[str]) -> dict[str, Any]:
    return _parse_score_payload(
        payload,
        expected_instance_ids,
        value_semantics="permissive_non_proof",
        coerce_value=coerce_permissive_resolved,
        parsed_status="parsed_non_proof",
        proof_capable=False,
    )


def parse_score_artifact(path: Path, expected_instance_ids: Sequence[str]) -> dict[str, Any]:
    if not path.exists():
        parsed = parse_score_payload(None, expected_instance_ids)
        return {**parsed, "artifact_path": str(path), "status": "invalid", "missing_artifact": True}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        parsed = parse_score_payload(None, expected_instance_ids)
        return {
            **parsed,
            "artifact_path": str(path),
            "status": "invalid",
            "missing_artifact": False,
            "invalid_entries": [{"reason": "json_parse_failed", "error": str(exc)}],
        }
    parsed = parse_score_payload(payload, expected_instance_ids)
    return {**parsed, "artifact_path": str(path), "missing_artifact": False}


def score_parser_expectations(expected_denominator: int) -> dict[str, Any]:
    return {
        "official_artifact": EVALUATOR_OUTPUT_FILE,
        "proof_schema": "Official eval_results.json object mapping instance_id to JSON boolean resolved status",
        "proof_value_semantics": "json_boolean_only",
        "proof_eligible_source_shape": "direct_instance_mapping",
        "accepted_fallback_schemas": [
            "JSON object with eval_results/results_by_instance/instance_results mapping, parsed for diagnostics only unless it matches the proof schema",
            "JSON object with results or instances list carrying instance_id plus resolved/passed/status, parsed for diagnostics only unless it matches the proof schema",
        ],
        "non_proof_permissive_parser": "parse_score_payload_permissive accepts string/int convenience values only with status parsed_non_proof and proof_eligible false",
        "fixed_denominator": expected_denominator,
        "missing_expected_instance": "invalid_score_artifact",
        "unexpected_instance": "invalid_score_artifact",
        "non_json_boolean_status": "invalid_score_artifact",
    }


def artifact_layout_check(
    *,
    artifact_dir: Path,
    materialized_artifacts: Mapping[str, Any] | None,
    evaluator_run: Mapping[str, Any] | None,
) -> dict[str, Any]:
    expected_inputs = {
        "raw_sample_path": artifact_dir / "gold_patch_raw_samples.jsonl",
        "patch_path": artifact_dir / "gold_patches.json",
        "manifest_path": artifact_dir / "gold_patch_artifact_manifest.json",
    }
    expected_execution = {
        "command_artifact": artifact_dir / "evaluator_command.json",
        "stdout_artifact": artifact_dir / "evaluator.stdout.txt",
        "stderr_artifact": artifact_dir / "evaluator.stderr.txt",
        "score_artifact": artifact_dir / "evaluator_output" / EVALUATOR_OUTPUT_FILE,
    }
    present_inputs = {name: path.exists() for name, path in expected_inputs.items()}
    present_execution = {name: path.exists() for name, path in expected_execution.items()}
    input_layout_expected_now = materialized_artifacts is not None
    execution_layout_expected_now = evaluator_run is not None and evaluator_run.get("status") != "not_requested"
    missing_inputs = [
        str(path)
        for name, path in expected_inputs.items()
        if input_layout_expected_now and not present_inputs[name]
    ]
    missing_execution = [
        str(path)
        for name, path in expected_execution.items()
        if execution_layout_expected_now and not present_execution[name]
    ]
    return {
        "status": "passed" if not missing_inputs and not missing_execution else "blocked",
        "artifact_dir": str(artifact_dir),
        "input_layout_expected_now": input_layout_expected_now,
        "execution_layout_expected_now": execution_layout_expected_now,
        "expected_inputs": {name: str(path) for name, path in expected_inputs.items()},
        "expected_execution_artifacts": {name: str(path) for name, path in expected_execution.items()},
        "present_inputs": present_inputs,
        "present_execution_artifacts": present_execution,
        "missing_expected_now": missing_inputs + missing_execution,
        "notes": [
            "Input artifacts are required once the pinned dataset cache is readable.",
            "Execution artifacts are required only when the evaluator gold-patch path is actually run.",
        ],
    }


def build_smoke(args: argparse.Namespace) -> dict[str, Any]:
    config_path = resolve_repo_path(args.config)
    if config_path is None:
        raise ToolError("--config resolved to no path")
    config = load_manifest(config_path)
    output_path = resolve_repo_path(args.output)
    artifact_dir = resolve_repo_path(args.artifact_dir) if args.artifact_dir else None
    if artifact_dir is None:
        stem = output_path.stem if output_path is not None else "gscore_gold_patch_smoke"
        artifact_dir = DEFAULT_RESULTS_RAW / stem

    static_check = validate_pinned_config(config)
    dataset_check, _rows, materialized_artifacts = validate_dataset_cache(
        config=config,
        dataset_override=args.dataset_cache,
        artifact_dir=artifact_dir,
    )
    harness_check = validate_harness(
        config=config,
        harness_override=args.harness_path,
        backend=args.backend,
        execute=args.execute_gold_patch,
        python_executable=args.python,
    )
    docker = docker_check(args.backend, args.execute_gold_patch)

    all_blockers: list[dict[str, Any]] = []
    all_blockers.extend(static_check["blockers"])
    all_blockers.extend(dataset_check["blockers"])
    all_blockers.extend(harness_check["blockers"])
    all_blockers.extend(docker["blockers"])

    selected_ids = [str(task["instance_id"]) for task in locked_tasks(config)]
    evaluator_run: dict[str, Any] | None = None
    score_parser: dict[str, Any] | None = None
    gold_patch_path_ran = False
    gold_patch_basis_proven = False

    if args.execute_gold_patch and not all_blockers and materialized_artifacts is not None:
        harness_path = Path(str(harness_check["selected_path"]))
        evaluator_output_dir = artifact_dir / "evaluator_output"
        command = evaluator_command(
            config=config,
            harness_path=harness_path,
            materialized_artifacts=materialized_artifacts,
            output_dir=evaluator_output_dir,
            backend=args.backend,
            num_workers=args.num_workers,
            dockerhub_username=args.dockerhub_username,
            docker_platform=args.docker_platform,
            python_executable=args.python,
        )
        evaluator_run = run_evaluator(
            command=command,
            cwd=harness_path,
            artifact_dir=artifact_dir,
            timeout_seconds=args.timeout_seconds,
        )
        gold_patch_path_ran = evaluator_run.get("exit_code") == 0 and evaluator_run.get("timed_out") is False
        score_parser = parse_score_artifact(evaluator_output_dir / EVALUATOR_OUTPUT_FILE, selected_ids)
        gold_patch_basis_proven = (
            gold_patch_path_ran
            and score_parser.get("status") == "parsed"
            and score_parser.get("proof_eligible") is True
            and score_parser.get("resolved_count") == len(selected_ids)
        )
    elif not args.execute_gold_patch and not all_blockers:
        evaluator_run = {
            "status": "not_requested",
            "reason": "--execute-gold-patch was not supplied",
            "safe_next_command": "rerun this tool with --execute-gold-patch after reviewing local runtime cost",
        }

    artifact_layout = artifact_layout_check(
        artifact_dir=artifact_dir,
        materialized_artifacts=materialized_artifacts,
        evaluator_run=evaluator_run,
    )

    if all_blockers:
        status = "gold_patch_smoke_blocked"
    elif gold_patch_basis_proven:
        status = "gold_patch_smoke_passed"
    elif args.execute_gold_patch:
        status = "gold_patch_smoke_failed"
    else:
        status = "gold_patch_smoke_ready_not_executed"

    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": status,
        "generated_at": iso_now(),
        "config_path": str(config_path),
        "artifact_dir": str(artifact_dir),
        "no_model_calls_made": True,
        "public_leaderboard_proxy_used": False,
        "gold_patch_path": {
            "execute_requested": bool(args.execute_gold_patch),
            "ran": gold_patch_path_ran,
            "basis_proven": gold_patch_basis_proven,
            "evaluator_run": evaluator_run,
            "score_parser": score_parser,
        },
        "direct_acut_scoring": {
            "attempted": False,
            "g_score_available": False,
            "g_scores": {},
            "reason": "This smoke only checks the gold-patch/evaluator basis before any ACUT patch-generation or scoring.",
        },
        "checks": {
            "pinned_config": static_check,
            "dataset_cache": dataset_check,
            "evaluation_harness": harness_check,
            "docker": docker,
            "artifact_layout": artifact_layout,
            "score_parser_expectations": score_parser_expectations(len(selected_ids)),
        },
        "blockers": all_blockers,
        "claim_limitations": [
            "This artifact is gold-patch infrastructure evidence only.",
            "No ACUT patch-generation was run.",
            "No ACUT G_score is available from this smoke.",
            "Public leaderboard or proxy scores were not used.",
            "If blocked, G_score must remain unavailable rather than zero-filled.",
        ],
        "next_defensible_action": next_action(status),
    }
    return payload


def next_action(status: str) -> str:
    if status == "gold_patch_smoke_blocked":
        return "Resolve the recorded environment/data/evaluator blockers, then rerun the no-model gold-patch smoke."
    if status == "gold_patch_smoke_ready_not_executed":
        return "Run the same tool with --execute-gold-patch to prove the evaluator path before ACUT scoring."
    if status == "gold_patch_smoke_failed":
        return "Inspect evaluator stdout/stderr and score parser output; replace locked tasks only through the pre-ACUT global-infra replacement rule if gold patches cannot pass."
    return "The pinned gold-patch evaluator basis is proven; ACUT dry-run/artifact validation can be considered next, still before scored ACUT G_score runs."


def report_markdown(payload: Mapping[str, Any]) -> str:
    blockers = as_list(payload.get("blockers"))
    checks = as_mapping(payload.get("checks"))
    dataset = as_mapping(checks.get("dataset_cache"))
    harness = as_mapping(checks.get("evaluation_harness"))
    docker = as_mapping(checks.get("docker"))
    artifact_layout = as_mapping(checks.get("artifact_layout"))
    gold_path = as_mapping(payload.get("gold_patch_path"))
    direct = as_mapping(payload.get("direct_acut_scoring"))

    blocker_lines = "\n".join(
        f"- `{item.get('blocker')}`: `{json.dumps({k: v for k, v in item.items() if k != 'blocker'}, sort_keys=True)}`"
        for item in blockers
    )
    if not blocker_lines:
        blocker_lines = "- None."

    score_parser = as_mapping(gold_path.get("score_parser"))
    if score_parser:
        parser_lines = (
            f"- Score parser status: `{score_parser.get('status')}`\n"
            f"- Proof eligible: `{score_parser.get('proof_eligible')}`\n"
            f"- Resolved count: `{score_parser.get('resolved_count')}` / `{score_parser.get('denominator')}`\n"
            f"- Missing expected instances: `{score_parser.get('missing_instance_ids')}`\n"
            f"- Unexpected instances: `{score_parser.get('unexpected_instance_ids')}`"
        )
    else:
        parser_lines = "- Score parser did not run because the evaluator gold-patch path did not run."

    return f"""# G-score Gold-Patch Smoke

Status: `{payload.get('status')}`  
Generated at: `{payload.get('generated_at')}`  
Config: `{payload.get('config_path')}`

## Scope

This is a no-model smoke for the pinned six-task SWE-Bench Pro general benchmark basis. It checks the locked denominator, pinned dataset/evaluator metadata, selection keys, gold-patch input path, evaluator artifact layout, Docker/backend readiness, and score parser expectations.

It is not ACUT scoring. ACUT patch-generation attempted: `{direct.get('attempted')}`. ACUT G_score available: `{direct.get('g_score_available')}`. Public leaderboard proxy used: `{payload.get('public_leaderboard_proxy_used')}`.

## Outcome

- Gold-patch execution requested: `{gold_path.get('execute_requested')}`
- Gold-patch path ran: `{gold_path.get('ran')}`
- Gold-patch basis proven: `{gold_path.get('basis_proven')}`
- Dataset cache status: `{dataset.get('status')}` at `{dataset.get('path')}`
- Evaluator checkout status: `{harness.get('status')}` at `{harness.get('selected_path')}`
- Docker status: `{docker.get('status')}`
- Artifact layout status: `{artifact_layout.get('status')}` under `{artifact_layout.get('artifact_dir')}`

## Blockers

{blocker_lines}

## Score Parser

{parser_lines}

The parser keeps the denominator fixed at six pinned tasks. Missing expected task ids, unexpected task ids, or non-boolean resolved statuses invalidate the score artifact instead of shrinking the denominator.

## Claim Boundary

No G_score is claimed by this report. A passing gold-patch smoke would prove only that the pinned evaluator basis can score known-good patches; it would still not be an ACUT result. If this report is blocked, G_score remains unavailable, not zero and not replaced by a public leaderboard score.

## Reproduction

```bash
python3 experiments/core_narrative/tools/codex_nfl_gscore_gold_patch_smoke.py \\
  --output experiments/core_narrative/results/gscore_gold_patch_smoke_20260509.json \\
  --report experiments/core_narrative/reports/gscore_gold_patch_smoke_20260509.md
```

After the pinned dataset cache and evaluator checkout are present, run the evaluator path deliberately:

```bash
python3 experiments/core_narrative/tools/codex_nfl_gscore_gold_patch_smoke.py \\
  --execute-gold-patch \\
  --output experiments/core_narrative/results/gscore_gold_patch_smoke_20260509.json \\
  --report experiments/core_narrative/reports/gscore_gold_patch_smoke_20260509.md
```
"""


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_smoke(args)
        emit_json(payload, args.output)
        if args.report:
            report_path = resolve_repo_path(args.report)
            if report_path is None:
                raise ToolError("--report resolved to no path")
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_markdown(payload), encoding="utf-8")
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
