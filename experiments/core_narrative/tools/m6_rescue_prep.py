#!/usr/bin/env python3
"""Prepare no-new-call M6 rescue diagnostics from the completed M5-W2 run."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, write_json


TOOL = "m6_rescue_prep"
SCHEMA_VERSION = "core-narrative.m6-rescue-prep.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SUMMARY = REPO_ROOT / "experiments/core_narrative/results/m5_w2_primary/summary.json"
DEFAULT_RESULTS_ROOT = REPO_ROOT / "experiments/core_narrative/results/m5_w2_primary"
DEFAULT_TASK_ROOT = REPO_ROOT / "experiments/core_narrative/tasks/click/rwork"
DEFAULT_SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/click"
DEFAULT_DEEP_ACUT = "cheap-click-deep-specialist-v2"
DEFAULT_CHEAP_ACUT = "cheap-generic-swe"
DEFAULT_FRONTIER_ACUT = "frontier-generic-swe"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--results-root", default=str(DEFAULT_RESULTS_ROOT))
    parser.add_argument("--task-root", default=str(DEFAULT_TASK_ROOT))
    parser.add_argument("--source-repo", default=str(DEFAULT_SOURCE_REPO))
    parser.add_argument("--deep-acut", default=DEFAULT_DEEP_ACUT)
    parser.add_argument("--cheap-acut", default=DEFAULT_CHEAP_ACUT)
    parser.add_argument("--frontier-acut", default=DEFAULT_FRONTIER_ACUT)
    parser.add_argument("--output-dir", default=str(DEFAULT_RESULTS_ROOT))
    parser.add_argument(
        "--report",
        default=str(REPO_ROOT / "experiments/core_narrative/reports/2026-05-13_m5_w2_failure_forensics.md"),
    )
    parser.add_argument("--output", help="Optional command summary JSON.")
    return parser.parse_args(list(argv) if argv is not None else None)


def resolve_repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate.resolve() if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def path_variants(path: str) -> set[str]:
    cleaned = path.strip().removeprefix("a/").removeprefix("b/")
    variants = {cleaned}
    if cleaned.startswith("src/"):
        variants.add(cleaned[4:])
    if cleaned.startswith("click/"):
        variants.add(f"src/{cleaned}")
    return variants


def paths_overlap(left: str, right: str) -> bool:
    return bool(path_variants(left) & path_variants(right))


def tokenize_patch_lines(lines: Sequence[str]) -> set[str]:
    tokens: set[str] = set()
    for line in lines:
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", line):
            tokens.add(token.lower())
    return tokens


def jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return round(len(left & right) / len(left | right), 4)


def normalize_hunk_header(header: str) -> str:
    return re.sub(r"@@[^@]*@@", "@@", header).strip()


def parse_unified_diff(text: str) -> dict[str, Any]:
    files: dict[str, dict[str, Any]] = {}
    current_file: str | None = None
    current_header: str | None = None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                candidate = parts[3]
                current_file = candidate[2:] if candidate.startswith("b/") else candidate
                files.setdefault(current_file, {"hunks": [], "added": [], "removed": [], "line_count": 0})
            else:
                current_file = None
            current_header = None
            continue
        if current_file is None:
            continue
        files[current_file]["line_count"] += 1
        if line.startswith("@@"):
            current_header = normalize_hunk_header(line)
            files[current_file]["hunks"].append(
                {
                    "header_sha256": sha256_text(current_header),
                    "line_count": 0,
                }
            )
            continue
        if current_header is not None and files[current_file]["hunks"]:
            files[current_file]["hunks"][-1]["line_count"] += 1
        if line.startswith("+") and not line.startswith("+++"):
            files[current_file]["added"].append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            files[current_file]["removed"].append(line[1:])
    return {
        "changed_files": sorted(files),
        "file_count": len(files),
        "hunk_count": sum(len(item["hunks"]) for item in files.values()),
        "hunk_header_hashes": sorted({hunk["header_sha256"] for item in files.values() for hunk in item["hunks"]}),
        "added_token_count": len(tokenize_patch_lines([line for item in files.values() for line in item["added"]])),
        "removed_token_count": len(tokenize_patch_lines([line for item in files.values() for line in item["removed"]])),
        "patch_token_count": len(
            tokenize_patch_lines(
                [line for item in files.values() for line in item["added"]]
                + [line for item in files.values() for line in item["removed"]]
            )
        ),
        "_tokens": tokenize_patch_lines(
            [line for item in files.values() for line in item["added"]]
            + [line for item in files.values() for line in item["removed"]]
        ),
    }


def public_patch_stats(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {
            "present": False,
            "sha256": None,
            "size_bytes": None,
            "changed_files": [],
            "file_count": 0,
            "hunk_count": 0,
            "hunk_header_hashes": [],
            "added_token_count": 0,
            "removed_token_count": 0,
            "patch_token_count": 0,
            "_tokens": set(),
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    parsed = parse_unified_diff(text)
    return {
        **parsed,
        "present": True,
        "sha256": sha256_text(text),
        "size_bytes": path.stat().st_size,
    }


def git_diff(source_repo: Path, base_commit: str, target_commit: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(source_repo), "diff", "--binary", "--no-ext-diff", "--unified=3", base_commit, target_commit],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ToolError(
            "failed to compute reference diff",
            base_commit=base_commit,
            target_commit=target_commit,
            stderr=completed.stderr[-500:],
        )
    return completed.stdout


def reference_patch_stats(source_repo: Path, task_manifest: Mapping[str, Any]) -> dict[str, Any]:
    source = task_manifest.get("source") if isinstance(task_manifest.get("source"), Mapping) else {}
    base = source.get("base_commit")
    target = source.get("target_commit")
    if not isinstance(base, str) or not isinstance(target, str):
        return {"present": False, "error": "missing base_commit or target_commit", "_tokens": set()}
    text = git_diff(source_repo, base, target)
    parsed = parse_unified_diff(text)
    return {
        **parsed,
        "present": True,
        "sha256": sha256_text(text),
        "size_bytes": len(text.encode("utf-8")),
        "source_base_commit": base,
        "source_target_commit": target,
    }


def task_manifest_path(task_root: Path, task_id: str) -> Path:
    return task_root / task_id / "task.yaml"


def load_task_manifests(task_root: Path, task_ids: Sequence[str]) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for task_id in task_ids:
        manifests[task_id] = load_manifest(task_manifest_path(task_root, task_id))
    return manifests


def cells_by_task(summary: Mapping[str, Any]) -> dict[str, dict[str, Mapping[str, Any]]]:
    by_task: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    cells = summary.get("cells")
    if not isinstance(cells, list):
        raise ToolError("summary does not contain cells list")
    for cell in cells:
        if not isinstance(cell, Mapping):
            continue
        task_id = cell.get("task_id")
        acut_id = cell.get("acut_id")
        if isinstance(task_id, str) and isinstance(acut_id, str):
            by_task[task_id][acut_id] = cell
    return dict(by_task)


def classify_task(scores: Mapping[str, int | None]) -> str:
    scored = [value for value in scores.values() if isinstance(value, int)]
    if not scored:
        return "unscored"
    if all(value == 1 for value in scored):
        return "ceiling"
    if all(value == 0 for value in scored):
        return "floor"
    return "separator"


def build_task_separation_matrix(
    *,
    summary: Mapping[str, Any],
    task_manifests: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    by_task = cells_by_task(summary)
    rows: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    for task_id in sorted(by_task):
        cells = by_task[task_id]
        scores = {acut_id: cell.get("score_value") for acut_id, cell in sorted(cells.items())}
        statuses = {acut_id: cell.get("status") for acut_id, cell in sorted(cells.items())}
        task_class = classify_task(scores)
        class_counts[task_class] += 1
        manifest = task_manifests[task_id]
        rows.append(
            {
                "task_id": task_id,
                "task_family": manifest.get("task_family"),
                "classification": task_class,
                "scores": scores,
                "statuses": statuses,
                "pass_count": sum(1 for value in scores.values() if value == 1),
                "fail_count": sum(1 for value in scores.values() if value == 0),
                "expected_touched_area": manifest.get("metadata", {}).get("expected_touched_area")
                if isinstance(manifest.get("metadata"), Mapping)
                else manifest.get("expected_touched_area"),
                "source_changed_files": (
                    manifest.get("metadata", {}).get("source_compare", {}).get("changed_files")
                    if isinstance(manifest.get("metadata"), Mapping)
                    else None
                )
                or (manifest.get("source_compare", {}).get("changed_files") if isinstance(manifest.get("source_compare"), Mapping) else []),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "generated_at": iso_now(),
        "status": "completed",
        "source_summary_status": summary.get("status"),
        "task_count": len(rows),
        "classification_counts": dict(sorted(class_counts.items())),
        "rows": rows,
    }


def verifier_failure_label(status: str, raw_dir: Path) -> str:
    if status == "verified_pass":
        return "verified_pass"
    if status == "no_diff":
        return "no_diff"
    if status == "unsafe_or_scope_violation":
        return "unsafe_or_scope_violation"
    stdout = (raw_dir / "verifier.stdout.txt").read_text(encoding="utf-8", errors="replace") if (raw_dir / "verifier.stdout.txt").exists() else ""
    stderr = (raw_dir / "verifier.stderr.txt").read_text(encoding="utf-8", errors="replace") if (raw_dir / "verifier.stderr.txt").exists() else ""
    text = f"{stdout}\n{stderr}"
    if "FAILED" in text or "failed" in text:
        return "verifier_test_failed"
    if "ERROR" in text or "Error" in text:
        return "verifier_error"
    if status == "verified_fail":
        return "verifier_nonzero"
    return status


def normalized_artifact_dir(cell: Mapping[str, Any]) -> Path | None:
    path = cell.get("normalized_result")
    if not isinstance(path, str):
        return None
    payload = read_json(Path(path))
    if not payload:
        return None
    artifacts = payload.get("artifact_paths") if isinstance(payload.get("artifact_paths"), Mapping) else {}
    artifact_dir = artifacts.get("artifact_dir")
    return Path(artifact_dir) if isinstance(artifact_dir, str) else None


def candidate_patch_path(cell: Mapping[str, Any]) -> Path | None:
    path = cell.get("normalized_result")
    if not isinstance(path, str):
        return None
    payload = read_json(Path(path))
    if not payload:
        return None
    candidate = payload.get("candidate_patch") if isinstance(payload.get("candidate_patch"), Mapping) else {}
    patch_path = candidate.get("path")
    return Path(patch_path) if isinstance(patch_path, str) else None


def expected_files(task_manifest: Mapping[str, Any], reference_files: Sequence[str]) -> list[str]:
    source_compare = task_manifest.get("source_compare") if isinstance(task_manifest.get("source_compare"), Mapping) else {}
    files = source_compare.get("changed_files")
    if isinstance(files, list) and files:
        return [str(path) for path in files]
    metadata = task_manifest.get("metadata") if isinstance(task_manifest.get("metadata"), Mapping) else {}
    nested = metadata.get("source_compare") if isinstance(metadata.get("source_compare"), Mapping) else {}
    files = nested.get("changed_files")
    if isinstance(files, list) and files:
        return [str(path) for path in files]
    return list(reference_files)


def overlap_row(
    *,
    task_id: str,
    acut_id: str,
    cell: Mapping[str, Any],
    task_manifest: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> dict[str, Any]:
    raw_dir = normalized_artifact_dir(cell)
    candidate = public_patch_stats(candidate_patch_path(cell))
    reference_files = [str(path) for path in reference.get("changed_files", [])]
    expected = expected_files(task_manifest, reference_files)
    candidate_files = [str(path) for path in candidate.get("changed_files", [])]
    candidate_hunks = set(candidate.get("hunk_header_hashes", []))
    reference_hunks = set(reference.get("hunk_header_hashes", []))
    touched_expected_file = any(paths_overlap(left, right) for left in candidate_files for right in expected)
    touched_reference_file = any(paths_overlap(left, right) for left in candidate_files for right in reference_files)
    touched_expected_function_or_class = bool(candidate_hunks & reference_hunks)
    token_overlap = jaccard(candidate.get("_tokens", set()), reference.get("_tokens", set()))
    if not candidate.get("present"):
        conceptual = "candidate_no_public_patch"
    elif touched_expected_function_or_class and token_overlap >= 0.15:
        conceptual = "strong_automated_proxy"
    elif touched_reference_file and token_overlap >= 0.2:
        conceptual = "moderate_automated_proxy"
    elif touched_reference_file:
        conceptual = "weak_file_only_proxy"
    else:
        conceptual = "no_automated_overlap"
    status = str(cell.get("status"))
    return {
        "task_id": task_id,
        "acut_id": acut_id,
        "primary_status": status,
        "score_value": cell.get("score_value"),
        "candidate_patch_sha256": candidate.get("sha256"),
        "candidate_patch_size_bytes": candidate.get("size_bytes"),
        "candidate_changed_files": candidate_files,
        "candidate_hunk_count": candidate.get("hunk_count"),
        "reference_patch_sha256": reference.get("sha256"),
        "reference_changed_files": reference_files,
        "reference_hunk_count": reference.get("hunk_count"),
        "expected_files": expected,
        "touched_expected_file": touched_expected_file,
        "touched_reference_file": touched_reference_file,
        "touched_expected_function_or_class_proxy": touched_expected_function_or_class,
        "same_conceptual_fix_proxy": conceptual,
        "patch_token_jaccard": token_overlap,
        "verifier_fail_reason": verifier_failure_label(status, raw_dir or Path()),
        "raw_patch_content_recorded": False,
        "reference_patch_content_recorded": False,
        "reviewer_instruction": "Use private raw artifacts only for blinded near-miss scoring; do not alter primary score.",
    }


def build_overlap_and_near_miss(
    *,
    summary: Mapping[str, Any],
    task_manifests: Mapping[str, Mapping[str, Any]],
    source_repo: Path,
    deep_acut: str,
    cheap_acut: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    by_task = cells_by_task(summary)
    rows: list[dict[str, Any]] = []
    near_miss_rows: list[dict[str, Any]] = []
    for task_id in sorted(by_task):
        reference = reference_patch_stats(source_repo, task_manifests[task_id])
        for acut_id in (deep_acut, cheap_acut):
            cell = by_task[task_id].get(acut_id)
            if not cell:
                continue
            row = overlap_row(task_id=task_id, acut_id=acut_id, cell=cell, task_manifest=task_manifests[task_id], reference=reference)
            rows.append(row)
            if row["score_value"] == 0:
                near_miss_rows.append(
                    {
                        "task_id": task_id,
                        "acut_id": acut_id,
                        "primary_status": row["primary_status"],
                        "candidate_patch_sha256": row["candidate_patch_sha256"],
                        "reference_patch_sha256": row["reference_patch_sha256"],
                        "candidate_changed_files": row["candidate_changed_files"],
                        "reference_changed_files": row["reference_changed_files"],
                        "automated_overlap_proxy": row["same_conceptual_fix_proxy"],
                        "patch_token_jaccard": row["patch_token_jaccard"],
                        "verifier_fail_reason": row["verifier_fail_reason"],
                        "blind_review_score": None,
                        "blind_review_scale": {
                            "0": "unrelated or no useful patch",
                            "1": "right file but wrong logic",
                            "2": "right function or condition but incomplete",
                            "3": "near reference, likely boundary or small omission",
                        },
                        "primary_score_locked": True,
                        "raw_patch_content_recorded": False,
                    }
                )
    audit = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "generated_at": iso_now(),
        "status": "completed",
        "source_summary_status": summary.get("status"),
        "scope": {
            "subject_acuts": [deep_acut, cheap_acut],
            "model_calls_made": 0,
            "primary_scores_modified": False,
        },
        "row_count": len(rows),
        "rows": rows,
    }
    near_miss = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "generated_at": iso_now(),
        "status": "packet_prepared_unscored",
        "source_summary_status": summary.get("status"),
        "model_calls_made": 0,
        "primary_scores_modified": False,
        "review_packet_count": len(near_miss_rows),
        "review_rows": near_miss_rows,
    }
    return audit, near_miss


def acut_summary_path(cell: Mapping[str, Any]) -> Path | None:
    path = cell.get("normalized_result")
    if not isinstance(path, str):
        return None
    payload = read_json(Path(path))
    if not payload:
        return None
    artifacts = payload.get("artifact_paths") if isinstance(payload.get("artifact_paths"), Mapping) else {}
    acut_summary = artifacts.get("acut_summary")
    return Path(acut_summary) if isinstance(acut_summary, str) else None


def delivery_row(cell: Mapping[str, Any], *, expected_enabled: bool) -> dict[str, Any]:
    summary_path = acut_summary_path(cell)
    summary = read_json(summary_path) if summary_path else None
    pack = summary.get("specialist_context_pack") if isinstance(summary, Mapping) and isinstance(summary.get("specialist_context_pack"), Mapping) else {}
    prompt_checks = pack.get("prompt_checks") if isinstance(pack.get("prompt_checks"), Mapping) else {}
    prompt = summary.get("prompt") if isinstance(summary, Mapping) and isinstance(summary.get("prompt"), Mapping) else {}
    leakage = pack.get("leakage_guards") if isinstance(pack.get("leakage_guards"), Mapping) else {}
    prompt_contains_context_inferred = (
        pack.get("enabled") is True
        and prompt_checks.get("marker_present") is True
        and prompt_checks.get("pack_hash_present") is True
        and prompt_checks.get("pack_id_present") is True
        and prompt_checks.get("all_expected_sections_present") is True
    )
    leakage_values = [value for value in leakage.values() if isinstance(value, bool)]
    passed = (
        bool(summary)
        and pack.get("enabled") is expected_enabled
        and pack.get("expected_for_acut") is expected_enabled
        and (prompt_contains_context_inferred if expected_enabled else pack.get("context_prompt_char_count") == 0)
        and prompt.get("manifest_truncated") is False
        and prompt.get("statement_truncated") is False
        and not any(leakage_values)
    )
    return {
        "task_id": cell.get("task_id"),
        "acut_id": cell.get("acut_id"),
        "run_id": Path(str(summary_path)).parent.parent.name if summary_path else None,
        "summary_present": bool(summary),
        "expected_context_enabled": expected_enabled,
        "context_enabled": pack.get("enabled"),
        "expected_for_acut": pack.get("expected_for_acut"),
        "pack_id": pack.get("pack_id"),
        "pack_hash": pack.get("pack_hash"),
        "manifest_sha256": pack.get("manifest_sha256"),
        "context_prompt_sha256": pack.get("context_prompt_sha256"),
        "context_prompt_char_count": pack.get("context_prompt_char_count"),
        "prompt_char_count": prompt.get("char_count") or prompt_checks.get("prompt_char_count"),
        "prompt_sha256": prompt.get("sha256") or prompt_checks.get("prompt_sha256"),
        "prompt_content_recorded": prompt.get("content_recorded") or prompt_checks.get("prompt_content_recorded"),
        "prompt_manifest_truncated": prompt.get("manifest_truncated"),
        "prompt_statement_truncated": prompt.get("statement_truncated"),
        "prompt_contains_context_inferred_from_redacted_checks": prompt_contains_context_inferred,
        "prompt_checks": {
            "marker_present": prompt_checks.get("marker_present"),
            "pack_hash_present": prompt_checks.get("pack_hash_present"),
            "pack_id_present": prompt_checks.get("pack_id_present"),
            "all_expected_sections_present": prompt_checks.get("all_expected_sections_present"),
            "section_ids_present": prompt_checks.get("section_ids_present"),
        },
        "leakage_guard_flag_count": sum(1 for value in leakage_values if value),
        "raw_prompt_content_recorded": False,
        "passed": passed,
    }


def build_treatment_delivery_audit(
    *,
    summary: Mapping[str, Any],
    deep_acut: str,
    cheap_acut: str,
) -> dict[str, Any]:
    cells = summary.get("cells") if isinstance(summary.get("cells"), list) else []
    deep_rows = [delivery_row(cell, expected_enabled=True) for cell in cells if isinstance(cell, Mapping) and cell.get("acut_id") == deep_acut]
    cheap_rows = [delivery_row(cell, expected_enabled=False) for cell in cells if isinstance(cell, Mapping) and cell.get("acut_id") == cheap_acut]
    all_rows = deep_rows + cheap_rows
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "generated_at": iso_now(),
        "status": "completed" if all(row["passed"] for row in all_rows) else "issues_found",
        "source_summary_status": summary.get("status"),
        "model_calls_made": 0,
        "raw_prompt_content_recorded": False,
        "audit_basis": "redacted codex_cli_patch_command specialist_context_pack metadata",
        "deep_specialist": {
            "acut_id": deep_acut,
            "run_count": len(deep_rows),
            "passed_count": sum(1 for row in deep_rows if row["passed"]),
            "all_prompt_contains_context_inferred": all(row["prompt_contains_context_inferred_from_redacted_checks"] for row in deep_rows),
            "rows": deep_rows,
        },
        "cheap_generic_negative_control": {
            "acut_id": cheap_acut,
            "run_count": len(cheap_rows),
            "passed_count": sum(1 for row in cheap_rows if row["passed"]),
            "all_context_disabled": all(row["context_enabled"] is False for row in cheap_rows),
            "rows": cheap_rows,
        },
    }


def render_report(
    *,
    summary: Mapping[str, Any],
    task_matrix: Mapping[str, Any],
    delivery: Mapping[str, Any],
    overlap: Mapping[str, Any],
    near_miss: Mapping[str, Any],
    output_paths: Mapping[str, Path],
    deep_acut: str,
    cheap_acut: str,
    frontier_acut: str,
) -> str:
    rows = task_matrix.get("rows") if isinstance(task_matrix.get("rows"), list) else []
    by_acut: dict[str, int] = defaultdict(int)
    for cell in summary.get("cells", []):
        if isinstance(cell, Mapping) and cell.get("score_value") == 1:
            by_acut[str(cell.get("acut_id"))] += 1
    lines = [
        "# M5-W2 Failure Forensics",
        "",
        f"Status: `completed_no_new_model_calls`  ",
        f"Generated at: `{task_matrix.get('generated_at')}`  ",
        f"Source summary: `experiments/core_narrative/results/m5_w2_primary/summary.json`",
        "",
        "## Bottom Line",
        "",
        "The M5-W2 negative result is preserved. This report does not change primary scores, rerun ACUTs, or reinterpret the preregistered gate.",
        "",
        f"- `{deep_acut}`: {by_acut.get(deep_acut, 0)} / 10",
        f"- `{cheap_acut}`: {by_acut.get(cheap_acut, 0)} / 10",
        f"- `{frontier_acut}`: {by_acut.get(frontier_acut, 0)} / 10",
        f"- Context delivery audit: `{delivery.get('status')}`",
        f"- Near-miss packet status: `{near_miss.get('status')}`",
        "",
        "## Task Separation",
        "",
        f"Classification counts: `{json.dumps(task_matrix.get('classification_counts'), sort_keys=True)}`.",
        "",
        "| Task | Family | Class | Passes |",
        "|---|---|---:|---:|",
    ]
    for row in rows:
        lines.append(f"| `{row['task_id']}` | {row.get('task_family')} | `{row.get('classification')}` | {row.get('pass_count')} / 4 |")
    lines.extend(
        [
            "",
            "## Treatment Delivery",
            "",
            f"Deep specialist runs checked: {delivery.get('deep_specialist', {}).get('run_count')}; passed: {delivery.get('deep_specialist', {}).get('passed_count')}.",
            f"Cheap generic negative-control runs checked: {delivery.get('cheap_generic_negative_control', {}).get('run_count')}; passed: {delivery.get('cheap_generic_negative_control', {}).get('passed_count')}.",
            "The audit uses redacted prompt metadata: context pack id/hash markers and section-presence checks, not raw prompt content.",
            "",
            "## Patch / Reference Overlap",
            "",
            f"Rows generated: {overlap.get('row_count')}. Candidate and reference patch contents are not copied into public artifacts.",
            "The `same_conceptual_fix_proxy` field is automated and conservative; blind review can fill the near-miss scores later without changing primary scoring.",
            "",
            "## Artifacts",
            "",
        ]
    )
    for label, path in output_paths.items():
        lines.append(f"- {label}: `{repo_relative(path)}`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "These diagnostics support M6 design only. They do not rescue M5-W2 as positive evidence, do not alter the W2 fixed denominator, and do not authorize W3 primary execution.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    summary_path = resolve_repo_path(args.summary)
    results_root = resolve_repo_path(args.results_root)
    task_root = resolve_repo_path(args.task_root)
    source_repo = resolve_repo_path(args.source_repo)
    output_dir = resolve_repo_path(args.output_dir)
    report_path = resolve_repo_path(args.report)
    output_path = resolve_repo_path(args.output) if args.output else None

    summary = load_manifest(summary_path)
    by_task = cells_by_task(summary)
    task_ids = sorted(by_task)
    task_manifests = load_task_manifests(task_root, task_ids)

    task_matrix = build_task_separation_matrix(summary=summary, task_manifests=task_manifests)
    overlap, near_miss = build_overlap_and_near_miss(
        summary=summary,
        task_manifests=task_manifests,
        source_repo=source_repo,
        deep_acut=args.deep_acut,
        cheap_acut=args.cheap_acut,
    )
    delivery = build_treatment_delivery_audit(summary=summary, deep_acut=args.deep_acut, cheap_acut=args.cheap_acut)

    output_paths = {
        "task_separation_matrix": output_dir / "task_separation_matrix.json",
        "patch_reference_overlap_audit": output_dir / "patch_reference_overlap_audit.json",
        "near_miss_blind_review": output_dir / "near_miss_blind_review.json",
        "treatment_delivery_audit": output_dir / "treatment_delivery_audit.json",
    }
    write_json(output_paths["task_separation_matrix"], task_matrix)
    write_json(output_paths["patch_reference_overlap_audit"], overlap)
    write_json(output_paths["near_miss_blind_review"], near_miss)
    write_json(output_paths["treatment_delivery_audit"], delivery)
    report = render_report(
        summary=summary,
        task_matrix=task_matrix,
        delivery=delivery,
        overlap=overlap,
        near_miss=near_miss,
        output_paths={**output_paths, "failure_forensics_report": report_path},
        deep_acut=args.deep_acut,
        cheap_acut=args.cheap_acut,
        frontier_acut=args.frontier_acut,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "summary": repo_relative(summary_path),
        "outputs": {key: repo_relative(path) for key, path in output_paths.items()},
        "report": repo_relative(report_path),
        "task_count": len(task_ids),
        "task_classification_counts": task_matrix["classification_counts"],
        "treatment_delivery_status": delivery["status"],
        "near_miss_packet_status": near_miss["status"],
        "model_calls_made": 0,
        "primary_scores_modified": False,
    }
    emit_json(payload, output_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
