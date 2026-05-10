#!/usr/bin/env python3
"""Create the R0 Click mini-release hygiene artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, load_manifest, write_json


TOOL = "click_r0_release_hygiene"
SCHEMA_VERSION = "core-narrative.click-r0-release-hygiene.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_ROOT = REPO_ROOT / "experiments/core_narrative/tasks/click"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/releases/click_r0_20260510/release_metadata.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-10_click_r0_release_hygiene.md"
SHA7_PLUS_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE)
URL_RE = re.compile(r"https?://", re.IGNORECASE)
COMPARE_RE = re.compile(r"\bcompare\b|/compare/", re.IGNORECASE)
FORBIDDEN_STATEMENT_TERMS = ("reference.patch", "target diff", "target_commit", "target commit url")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-root", default=str(TASK_ROOT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(list(argv))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def digest_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def task_dirs(task_root: Path) -> list[Path]:
    return sorted(path for path in task_root.glob("*/*") if (path / "task.yaml").exists())


def remove_public_source_section(statement: str) -> str:
    lines = statement.splitlines()
    out: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip() == "## Public Source":
            index += 1
            while index < len(lines) and not lines[index].startswith("## "):
                index += 1
            continue
        out.append(line)
        index += 1
    text = sanitize_acut_visible_text("\n".join(out).strip()) + "\n"
    addition = """
## ACUT-Visible Context Boundary

Use only this task statement, the prepared repository workspace, allowed pre-base repository context, and the ACUT policy. Source provenance identifiers, answer artifacts, hidden verifier material, ACUT outputs, public model results, and future execution results are not ACUT-visible.
""".strip()
    return text + "\n" + addition + "\n"


def sanitize_acut_visible_text(text: str) -> str:
    replacements = (
        (re.compile(r"\btarget diff\b", re.IGNORECASE), "answer artifact"),
        (re.compile(r"\breference patch(?:es)?\b", re.IGNORECASE), "answer artifact"),
        (re.compile(r"\btarget commit(?:s)?\b", re.IGNORECASE), "source provenance"),
        (re.compile(r"\bcompare link(?:s)?\b", re.IGNORECASE), "provenance link"),
    )
    result = text
    for pattern, replacement in replacements:
        result = pattern.sub(replacement, result)
    return result


def acut_statement_leakage(text: str) -> dict[str, Any]:
    lower = text.lower()
    return {
        "contains_url": bool(URL_RE.search(text)),
        "contains_hex_sha_7_plus": bool(SHA7_PLUS_RE.search(text)),
        "contains_compare_link": bool(COMPARE_RE.search(text)),
        "forbidden_term_hits": [term for term in FORBIDDEN_STATEMENT_TERMS if term in lower],
    }


def is_acut_statement_safe(text: str) -> bool:
    leakage = acut_statement_leakage(text)
    return (
        leakage["contains_url"] is False
        and leakage["contains_hex_sha_7_plus"] is False
        and leakage["contains_compare_link"] is False
        and not leakage["forbidden_term_hits"]
    )


def as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def source_summary(task: Mapping[str, Any]) -> dict[str, Any]:
    source = task.get("source") if isinstance(task.get("source"), Mapping) else {}
    metadata = task.get("metadata") if isinstance(task.get("metadata"), Mapping) else {}
    compare = metadata.get("source_compare") if isinstance(metadata.get("source_compare"), Mapping) else {}
    if not compare and isinstance(task.get("source_compare"), Mapping):
        compare = task["source_compare"]  # type: ignore[assignment]
    return {
        "kind": source.get("kind"),
        "public_url": source.get("public_url"),
        "anchor_id": source.get("anchor_id"),
        "base_commit": source.get("base_commit"),
        "target_commit": source.get("target_commit"),
        "changed_files": as_list(compare.get("changed_files")) if isinstance(compare, Mapping) else [],
        "commits_ahead": compare.get("commits_ahead") if isinstance(compare, Mapping) else None,
    }


def oracle_grade(task: Mapping[str, Any]) -> str:
    expected = task.get("expected") if isinstance(task.get("expected"), Mapping) else {}
    verifier = task.get("verifier") if isinstance(task.get("verifier"), Mapping) else {}
    if expected.get("no_op_fails") is True and expected.get("reference_passes") is True and verifier.get("command"):
        return "B"
    return "C"


def risk_permission_tags(task: Mapping[str, Any]) -> list[str]:
    tags = ["local_filesystem_edit", "local_test_execution", "network_not_required_for_verifier"]
    allowed = task.get("allowed_context") if isinstance(task.get("allowed_context"), Mapping) else {}
    if allowed.get("include_git_history_before_base") is True:
        tags.append("pre_base_git_history_allowed")
    if allowed.get("include_issue_text") is True:
        tags.append("issue_text_allowed")
    if allowed.get("include_pr_text") is True:
        tags.append("pr_text_allowed")
    if allowed.get("include_reference_patch") is False:
        tags.append("reference_patch_forbidden")
    return tags


def leakage_notes(task: Mapping[str, Any]) -> dict[str, Any]:
    leakage = task.get("leakage") if isinstance(task.get("leakage"), Mapping) else {}
    return {
        "reviewed": leakage.get("reviewed") is True,
        "notes": leakage.get("notes"),
        "acut_statement_excludes_provenance_urls_and_shas": True,
        "provenance_preserved_in_audit_artifact": True,
    }


def update_task_statement_path(task_yaml: Path) -> bool:
    text = task_yaml.read_text(encoding="utf-8")
    updated = text.replace("task_statement_path: public/statement.md", "task_statement_path: public/acut_statement.md")
    if updated == text:
        return False
    task_yaml.write_text(updated, encoding="utf-8")
    return True


def provenance_markdown(task_id: str, task: Mapping[str, Any]) -> str:
    source = source_summary(task)
    changed_files = source.get("changed_files") if isinstance(source.get("changed_files"), list) else []
    changed = "\n".join(f"- `{path}`" for path in changed_files) or "- none recorded"
    return f"""# {task_id} Provenance

This audit-only artifact preserves source and replay provenance that is intentionally excluded from the ACUT-visible statement.

## Source

- Kind: `{source.get("kind")}`
- Anchor: `{source.get("anchor_id")}`
- Public URL: `{source.get("public_url")}`
- Base commit: `{source.get("base_commit")}`
- Target commit: `{source.get("target_commit")}`
- Commits ahead: `{source.get("commits_ahead")}`

## Changed Files From Source Compare

{changed}

## Leakage Boundary

The ACUT-visible statement is `public/acut_statement.md`. It excludes target commit URLs, target SHAs, compare links, and reference patch material. This file is verifier/coordinator audit material, not ACUT input.
"""


def build_task_record(task_dir: Path, *, dry_run: bool) -> dict[str, Any]:
    task_yaml = task_dir / "task.yaml"
    task = load_manifest(task_yaml)
    task_id = str(task.get("task_id") or task_dir.name)
    statement_path = task_dir / "public" / "statement.md"
    if not statement_path.exists():
        raise ToolError("public statement missing", task_id=task_id, path=str(statement_path))
    acut_text = remove_public_source_section(statement_path.read_text(encoding="utf-8"))
    leakage = acut_statement_leakage(acut_text)
    if not is_acut_statement_safe(acut_text):
        raise ToolError("generated ACUT-visible statement failed leakage guard", task_id=task_id, leakage=leakage)
    acut_path = task_dir / "public" / "acut_statement.md"
    audit_dir = task_dir / "audit"
    provenance_path = audit_dir / "provenance.md"
    if not dry_run:
        acut_path.write_text(acut_text, encoding="utf-8")
        audit_dir.mkdir(parents=True, exist_ok=True)
        provenance_path.write_text(provenance_markdown(task_id, task), encoding="utf-8")
        update_task_statement_path(task_yaml)
        task = load_manifest(task_yaml)
    return {
        "task_id": task_id,
        "split": task.get("split"),
        "task_family": task.get("task_family"),
        "task_family_tags": [str(task.get("task_family"))],
        "risk_permission_tags": risk_permission_tags(task),
        "oracle_grade": oracle_grade(task),
        "leakage_notes": leakage_notes(task),
        "allowed_context": task.get("allowed_context", {}),
        "acut_statement_path": str(acut_path.relative_to(REPO_ROOT)),
        "acut_statement_sha256": sha256_file(acut_path) if acut_path.exists() else digest_payload(acut_text),
        "acut_statement_leakage_guard": leakage,
        "compat_statement_path": str(statement_path.relative_to(REPO_ROOT)),
        "audit_provenance_path": str(provenance_path.relative_to(REPO_ROOT)),
        "audit_provenance_sha256": sha256_file(provenance_path) if provenance_path.exists() else digest_payload(provenance_markdown(task_id, task)),
        "task_manifest_path": str(task_yaml.relative_to(REPO_ROOT)),
        "task_manifest_sha256": sha256_file(task_yaml),
        "source": source_summary(task),
    }


def build_release(task_root: Path, *, dry_run: bool) -> dict[str, Any]:
    records = [build_task_record(path, dry_run=dry_run) for path in task_dirs(task_root)]
    digest_material = {
        "schema_version": SCHEMA_VERSION,
        "release_id": "click-r0-20260510",
        "tasks": [
            {
                key: record.get(key)
                for key in (
                    "task_id",
                    "split",
                    "task_family",
                    "risk_permission_tags",
                    "oracle_grade",
                    "allowed_context",
                    "acut_statement_sha256",
                    "audit_provenance_sha256",
                    "task_manifest_sha256",
                )
            }
            for record in records
        ],
    }
    return {
        "tool": TOOL,
        "schema_version": SCHEMA_VERSION,
        "status": "dry_run_completed" if dry_run else "completed",
        "generated_at": iso_now(),
        "release_id": "click-r0-20260510",
        "release_scope": "Click RBench/RWork mini release hygiene; provisional, not final benchmark authority",
        "task_count": len(records),
        "tasks": records,
        "release_digest": digest_payload(digest_material),
        "leakage_policy": {
            "acut_visible_statement": "public/acut_statement.md",
            "compat_statement_preserved": "public/statement.md",
            "audit_provenance": "audit/provenance.md",
            "target_commit_urls_shas_compare_links_reference_patch_excluded_from_acut_statement": True,
        },
        "claim_boundary": {
            "final_benchmark_authority": False,
            "license_or_admission_output": False,
            "predictivity_claim": False,
        },
    }


def report_markdown(payload: Mapping[str, Any]) -> str:
    rows = []
    for record in payload.get("tasks", []):
        if not isinstance(record, Mapping):
            continue
        rows.append(
            "| "
            + " | ".join(
                [
                    f"`{record.get('task_id')}`",
                    f"`{record.get('split')}`",
                    f"`{record.get('oracle_grade')}`",
                    f"`{record.get('acut_statement_path')}`",
                    f"`{record.get('audit_provenance_path')}`",
                ]
            )
            + " |"
        )
    return f"""# Click R0 Release Hygiene

Date: 2026-05-10

## Scope

R0 turns the current Click smoke slice into an auditable mini release without claiming final benchmark authority. Existing `public/statement.md` files are preserved for compatibility. ACUT-visible inputs now use `public/acut_statement.md`; source URLs, target SHAs, compare links, and reference patch material are preserved separately under `audit/provenance.md`.

Release digest: `{payload.get("release_digest")}`
Task count: `{payload.get("task_count")}`

| Task | Split | Oracle Grade | ACUT Statement | Audit Provenance |
| --- | --- | --- | --- | --- |
{chr(10).join(rows)}

## Leakage Reduction

The ACUT-visible task path now omits target commit URLs, target SHAs, compare links, and reference patch material. Those fields remain in `audit/provenance.md` and release metadata so reviewers can reproduce the package and audit lineage without exposing answer-adjacent anchors to ACUT runs.

## Remaining Provisional

This release still uses smoke-slice task membership and focused verifier grades. It does not assert final benchmark authority, predictive validity, license, admission, or authorization.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/click_r0_release_hygiene.py \\
  --output experiments/core_narrative/releases/click_r0_20260510/release_metadata.json \\
  --report experiments/core_narrative/reports/2026-05-10_click_r0_release_hygiene.md
```
"""


def write_report(path: str | Path, payload: Mapping[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_markdown(payload), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = build_release(Path(args.task_root), dry_run=args.dry_run)
        if not args.dry_run:
            write_json(args.output, payload)
            if args.report:
                write_report(args.report, payload)
        emit_json(payload, None)
        return 0
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    raise SystemExit(main())
