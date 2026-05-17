#!/usr/bin/env python3
"""Select a SymPy B-task anchor pool after the external E slice is frozen."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import external_calibrated_repository_admission as admission
from _common import ToolError, emit_json, fail, iso_now, write_json


TOOL = "external_calibrated_b_anchor_selection"
SCHEMA_VERSION = "external-calibrated-repo-benchmark.b-anchor-selection.v1"
PROTOCOL_ID = admission.PROTOCOL_ID
REPO_ROOT = admission.REPO_ROOT
DEFAULT_E_FREEZE = REPO_ROOT / "experiments/core_narrative/results/external/e_task_smoke.json"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/task_admission/sympy_b_anchor_selection_20260515.json"
DEFAULT_MANIFEST = REPO_ROOT / "experiments/core_narrative/configs/tasks/sympy_barcarolle_b_candidates_v0.yaml"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/sympy_b_anchor_selection_report.md"
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/external_calibrated_b_anchor_selection_20260515"
DEFAULT_SOURCE_REPO = REPO_ROOT / "experiments/core_narrative/external_repos/sympy"
SELECTION_SALT = "external-calibrated-repo-benchmark-v1:sympy-b-anchor-selection:v0"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", default=str(DEFAULT_SOURCE_REPO), help="SymPy checkout.")
    parser.add_argument("--e-freeze", default=str(DEFAULT_E_FREEZE), help="Frozen E task smoke/freeze JSON.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Public JSON output.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Public candidate manifest YAML.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown report output.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Ignored private provenance root.")
    parser.add_argument("--candidate-target", type=int, default=40, help="Public candidate anchor target.")
    parser.add_argument("--primary-target", type=int, default=20, help="Future primary B target size.")
    parser.add_argument("--reserve-target", type=int, default=10, help="Future reserve target size.")
    return parser.parse_args(list(argv) if argv is not None else None)


def load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ToolError("failed to load JSON artifact", path=admission.repo_relative(path), cause=str(exc)) from exc
    if not isinstance(payload, dict):
        raise ToolError("JSON artifact root must be an object", path=admission.repo_relative(path))
    return payload


def changed_file_set_digest(files: Sequence[str]) -> str:
    return admission.sha256_text("\n".join(sorted(files)))


def difficulty_label(changed_file_count: int, changed_python_file_count: int) -> str:
    if changed_file_count <= 2 and changed_python_file_count <= 2:
        return "easy-medium"
    if changed_file_count <= 6 and changed_python_file_count <= 4:
        return "medium"
    return "medium-hard"


def selection_key(candidate: Mapping[str, Any], *, salt: str = SELECTION_SALT) -> str:
    return admission.digest_parts(
        salt,
        str(candidate.get("family", "")),
        str(candidate.get("source_anchor_digest", "")),
        str(candidate.get("changed_file_set_digest", "")),
    )


def e_anchor_digest_set(e_freeze: Mapping[str, Any]) -> set[str]:
    values: set[str] = set()
    for task in e_freeze.get("task_table", []):
        if not isinstance(task, Mapping):
            continue
        for key in ("base_commit_digest", "instance_id_digest", "problem_statement_digest"):
            value = task.get(key)
            if isinstance(value, str):
                values.add(value)
    return values


def candidate_from_commit(repo_slug: str, row: Mapping[str, Any]) -> dict[str, Any] | None:
    files = [str(path) for path in row.get("files", []) if isinstance(path, str)]
    subject = str(row.get("subject", ""))
    if admission.subject_is_low_signal(subject):
        return None
    surface = admission.candidate_surface(repo_slug, files)
    if surface != "source_and_tests":
        return None
    family = admission.classify_candidate_family(repo_slug, subject, files)
    changed_python_file_count = sum(1 for path in files if path.endswith(".py"))
    if len(files) > 40 or changed_python_file_count > 40:
        return None
    return {
        "repo": "sympy/sympy",
        "source_anchor_digest": admission.digest_parts("sympy/sympy", str(row.get("commit", ""))),
        "source_time": row.get("committed_at"),
        "subject_digest": admission.sha256_text(subject),
        "changed_file_set_digest": changed_file_set_digest(files),
        "changed_file_count": len(files),
        "changed_python_file_count": changed_python_file_count,
        "surface": surface,
        "family": family,
        "difficulty": difficulty_label(len(files), changed_python_file_count),
        "oracle_directness": "direct_source_and_tests_commit",
        "admission_status": "anchor_selected_not_task_admitted",
    }


def round_robin_select(candidates: Sequence[Mapping[str, Any]], *, target: int) -> list[dict[str, Any]]:
    by_family: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_family[str(candidate.get("family", "core/mixed"))].append(candidate)
    for family_candidates in by_family.values():
        family_candidates.sort(key=lambda item: (selection_key(item), str(item.get("source_time", ""))))
    selected: list[dict[str, Any]] = []
    families = sorted(by_family, key=lambda family: (-len(by_family[family]), family))
    while len(selected) < target and any(by_family.values()):
        for family in families:
            if not by_family[family]:
                continue
            selected.append(dict(by_family[family].pop(0)))
            if len(selected) >= target:
                break
    return selected


def select_anchor_pool(rows: Sequence[Mapping[str, Any]], e_freeze: Mapping[str, Any], *, target: int) -> list[dict[str, Any]]:
    e_digests = e_anchor_digest_set(e_freeze)
    candidates: list[dict[str, Any]] = []
    seen_file_sets: set[str] = set()
    for row in rows:
        candidate = candidate_from_commit("sympy", row)
        if candidate is None:
            continue
        if candidate["source_anchor_digest"] in e_digests:
            continue
        if candidate["changed_file_set_digest"] in seen_file_sets:
            continue
        seen_file_sets.add(candidate["changed_file_set_digest"])
        candidates.append(candidate)
    selected = round_robin_select(candidates, target=target)
    for index, candidate in enumerate(selected, start=1):
        candidate["candidate_id"] = f"sympy_b_anchor_{index:03d}"
        candidate["ordinal"] = index
    return selected


def private_anchor_map(rows: Sequence[Mapping[str, Any]], selected: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_digest = {
        admission.digest_parts("sympy/sympy", str(row.get("commit", ""))): row
        for row in rows
        if row.get("commit")
    }
    anchors = []
    for candidate in selected:
        row = by_digest.get(str(candidate.get("source_anchor_digest")), {})
        anchors.append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "commit": row.get("commit"),
                "committed_at": row.get("committed_at"),
                "subject": row.get("subject"),
                "files": row.get("files"),
            }
        )
    return {
        "schema_version": f"{SCHEMA_VERSION}.private.v1",
        "generated_at": iso_now(),
        "policy": "Ignored private provenance for later oracle construction; do not expose to ACUT prompts.",
        "anchors": anchors,
    }


def build_payload(
    selected: Sequence[Mapping[str, Any]],
    *,
    e_freeze: Mapping[str, Any],
    primary_target: int,
    reserve_target: int,
) -> dict[str, Any]:
    families = Counter(str(candidate.get("family")) for candidate in selected)
    difficulties = Counter(str(candidate.get("difficulty")) for candidate in selected)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "protocol_id": PROTOCOL_ID,
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "status": "anchor_pool_selected_task_admission_pending",
        "repo": "sympy/sympy",
        "source_repo": admission.repo_relative(DEFAULT_SOURCE_REPO),
        "selection_rule": {
            "salt": SELECTION_SALT,
            "source_window_start": admission.RECENT_WINDOW_START.isoformat(),
            "source_window_end": admission.T0.isoformat(),
            "surface_required": "source_and_tests",
            "selected_using_acut_outputs": False,
            "selected_using_e_results": False,
            "raw_e_material_used": False,
        },
        "e_freeze_status": e_freeze.get("status"),
        "e_task_count": e_freeze.get("task_count"),
        "candidate_target": len(selected),
        "future_primary_target": primary_target,
        "future_reserve_target": reserve_target,
        "family_counts": dict(sorted(families.items())),
        "difficulty_counts": dict(sorted(difficulties.items())),
        "candidates": list(selected),
        "next_required_steps": [
            "Draft public task statements from selected anchors without exposing reference patches.",
            "Construct hidden verifiers and reference patches from private provenance.",
            "Run no-op fail and reference-patch pass smokes before freezing primary/reserve B manifests.",
        ],
    }


def yaml_quote(value: Any) -> str:
    if value is None:
        return "null"
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def render_manifest(payload: Mapping[str, Any]) -> str:
    lines = [
        "schema_version: external-calibrated-repo-benchmark.b-anchor-candidates.v0",
        f"protocol_id: {yaml_quote(payload.get('protocol_id'))}",
        f"status: {yaml_quote(payload.get('status'))}",
        f"generated_at: {yaml_quote(payload.get('generated_at'))}",
        "repo: sympy/sympy",
        "selection_policy:",
        "  source: SymPy local git history",
        "  surface_required: source_and_tests",
        "  selected_using_acut_outputs: false",
        "  selected_using_e_results: false",
        "  raw_e_material_used: false",
        "task_admission_status: not_started",
        "candidates:",
    ]
    for candidate in payload.get("candidates", []):
        if not isinstance(candidate, Mapping):
            continue
        lines.extend(
            [
                f"  - candidate_id: {yaml_quote(candidate.get('candidate_id'))}",
                f"    ordinal: {candidate.get('ordinal')}",
                f"    source_anchor_digest: {yaml_quote(candidate.get('source_anchor_digest'))}",
                f"    source_time: {yaml_quote(candidate.get('source_time'))}",
                f"    subject_digest: {yaml_quote(candidate.get('subject_digest'))}",
                f"    changed_file_set_digest: {yaml_quote(candidate.get('changed_file_set_digest'))}",
                f"    family: {yaml_quote(candidate.get('family'))}",
                f"    difficulty: {yaml_quote(candidate.get('difficulty'))}",
                f"    changed_file_count: {candidate.get('changed_file_count')}",
                f"    changed_python_file_count: {candidate.get('changed_python_file_count')}",
                f"    oracle_directness: {yaml_quote(candidate.get('oracle_directness'))}",
                f"    admission_status: {yaml_quote(candidate.get('admission_status'))}",
            ]
        )
    return "\n".join(lines) + "\n"


def render_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# SymPy B Anchor Selection",
        "",
        f"Protocol: `{payload.get('protocol_id')}`",
        f"Status: `{payload.get('status')}`",
        f"Generated at: `{payload.get('generated_at')}`",
        "",
        "## Summary",
        "",
        f"- Candidate anchors: `{payload.get('candidate_target')}`",
        f"- Future primary/reserve targets: `{payload.get('future_primary_target')}` / `{payload.get('future_reserve_target')}`",
        f"- E freeze status/count: `{payload.get('e_freeze_status')}` / `{payload.get('e_task_count')}`",
        "",
        "## Families",
        "",
    ]
    families = payload.get("family_counts") if isinstance(payload.get("family_counts"), Mapping) else {}
    for family, count in families.items():
        lines.append(f"- `{family}`: `{count}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This is an anchor-selection artifact only. It does not freeze B primary tasks, and it does not claim no-op/reference verifier admission.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    source_repo = Path(args.source_repo)
    if not (source_repo / ".git").exists():
        raise ToolError("source repository checkout is missing", path=admission.repo_relative(source_repo))
    e_freeze = load_json_object(Path(args.e_freeze))
    if e_freeze.get("freeze_allowed") is not True:
        raise ToolError("E slice must be frozen before selecting B anchors", e_status=e_freeze.get("status"))
    rows = admission.commit_rows_with_files(source_repo, since=admission.RECENT_WINDOW_START, until=admission.T0)
    selected = select_anchor_pool(rows, e_freeze, target=args.candidate_target)
    if len(selected) < args.candidate_target:
        raise ToolError("insufficient selected B anchors", selected=len(selected), requested=args.candidate_target)
    payload = build_payload(selected, e_freeze=e_freeze, primary_target=args.primary_target, reserve_target=args.reserve_target)

    output = Path(args.output)
    write_json(output, payload)
    manifest = Path(args.manifest)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(render_manifest(payload), encoding="utf-8")
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")

    private_root = Path(args.private_root)
    private_root.mkdir(parents=True, exist_ok=True)
    private_path = private_root / "private_anchor_map.json"
    write_json(private_path, private_anchor_map(rows, selected))

    emit_json(
        {
            **payload,
            "output_path": admission.repo_relative(output),
            "manifest_path": admission.repo_relative(manifest),
            "report_path": admission.repo_relative(report),
            "private_anchor_map_path": admission.repo_relative(private_path),
        }
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
