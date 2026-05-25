from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from phase1_future_holdout import simple_yaml_load


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
PHASE0_TOOLS = REPO_ROOT / "experiments" / "phase0_headroom" / "tools"
if str(PHASE0_TOOLS) not in sys.path:
    sys.path.insert(0, str(PHASE0_TOOLS))

import statement_quality  # noqa: E402


DEFAULT_CONFIG = ROOT / "configs" / "phase1_diff_assisted_statement_regeneration.yaml"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def config_path(raw: str | Path) -> Path:
    path = Path(str(raw))
    return path if path.is_absolute() else REPO_ROOT / path


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    config = simple_yaml_load(path)
    if config.get("schema_version") != "barcarolle.phase1_diff_assisted_statement_regeneration.v1":
        raise ValueError("unexpected diff-assisted statement regeneration config schema_version")
    config["_path"] = str(path)
    return config


def artifact_path(config: dict[str, Any], key: str) -> Path:
    return config_path(str(config["source_artifacts"][key]))


def output_path(config: dict[str, Any], key: str) -> Path:
    return config_path(str(config["output_paths"][key]))


def stable_generated_at(config: dict[str, Any]) -> str:
    preflight = output_path(config, "preflight")
    if preflight.exists():
        return str(read_json(preflight).get("generated_at") or config.get("created_at") or "2026-05-25T00:00:00Z")
    return str(config.get("created_at") or "2026-05-25T00:00:00Z")


def source_kind(source_ref: str) -> str:
    return statement_quality.source_kind(source_ref)


def normalize_text(value: Any) -> str:
    return statement_quality.normalize_text(value)


def short_excerpt(value: Any, *, limit: int = 700) -> str:
    return statement_quality.sanitize_public_body_summary(value, limit=limit)


def unique_sorted(values: list[str]) -> list[str]:
    return sorted(dict.fromkeys(str(value) for value in values if str(value)))


def row_by_task(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["task_id"]): row for row in rows if row.get("task_id")}


def git_bytes(repo: Path, args: list[str]) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.DEVNULL)


def safe_git_bytes(repo: Path, args: list[str]) -> bytes:
    try:
        return git_bytes(repo, args)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return b""


def parse_numstat(raw: bytes) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in raw.decode("utf-8", errors="replace").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, removed, path = parts[0], parts[1], parts[2]
        rows.append(
            {
                "path": path,
                "added_lines": None if added == "-" else int(added),
                "removed_lines": None if removed == "-" else int(removed),
            }
        )
    return rows


def diff_summary(
    *,
    repo_path: Path,
    base_commit: str,
    target_commit: str,
    changed_files: list[str],
    implementation_files: list[str],
    test_files: list[str],
) -> dict[str, Any]:
    if not repo_path.exists() or not base_commit or not target_commit:
        return {
            "available": False,
            "changed_file_count": len(changed_files),
            "changed_files": changed_files,
            "implementation_files_changed": implementation_files,
            "line_counts_by_file": [],
            "summary": "External repository or commit metadata unavailable; using certified changed-file metadata only.",
            "test_files_touched": test_files,
        }

    diff_args = ["diff", "--no-ext-diff", base_commit, target_commit, "--", *changed_files]
    raw_diff = safe_git_bytes(repo_path, diff_args)
    test_diff = safe_git_bytes(repo_path, ["diff", "--no-ext-diff", base_commit, target_commit, "--", *test_files]) if test_files else b""
    numstat = parse_numstat(safe_git_bytes(repo_path, ["diff", "--numstat", base_commit, target_commit, "--", *changed_files]))
    name_status = safe_git_bytes(repo_path, ["diff", "--name-status", base_commit, target_commit, "--", *changed_files]).decode(
        "utf-8", errors="replace"
    )
    status_counts = Counter(line.split("\t", 1)[0] for line in name_status.splitlines() if line.strip())
    changed_impl = [row["path"] for row in numstat if row["path"] in set(implementation_files)]
    touched_tests = [row["path"] for row in numstat if row["path"] in set(test_files)]
    summary = (
        f"{len(changed_impl)} implementation file(s) and {len(touched_tests)} test file(s) changed; "
        f"{sum((row.get('added_lines') or 0) for row in numstat)} added line(s), "
        f"{sum((row.get('removed_lines') or 0) for row in numstat)} removed line(s)."
    )
    return {
        "available": bool(raw_diff or numstat),
        "changed_file_count": len(changed_files),
        "changed_files": changed_files,
        "implementation_files_changed": unique_sorted(changed_impl or implementation_files),
        "line_counts_by_file": numstat,
        "name_status_counts": dict(sorted(status_counts.items())),
        "summary": summary,
        "target_diff_digest": f"sha256:{digest_bytes(raw_diff)}" if raw_diff else "",
        "test_diff_digest": f"sha256:{digest_bytes(test_diff)}" if test_diff else "",
        "test_files_touched": unique_sorted(touched_tests or test_files),
    }


def public_context_for(candidate: dict[str, Any], certified: dict[str, Any] | None, source_context: dict[str, Any] | None) -> dict[str, Any]:
    context = source_context or (certified or {}).get("sanitized_context") or {}
    title = normalize_text(context.get("summary") or candidate.get("problem_summary"))
    body = normalize_text(context.get("body_summary") or candidate.get("short_sanitized_public_excerpt"))
    source_ref = str(context.get("ref") or candidate.get("source_ref") or "")
    return {
        "body_digest": f"sha256:{digest_text(body)}" if body else "",
        "body_excerpt": short_excerpt(body),
        "body_length": len(body),
        "classification": str(context.get("classification") or ""),
        "source_kind": source_kind(source_ref),
        "source_ref": source_ref,
        "state": str(context.get("state") or ""),
        "title": title,
    }


def certification_summary(candidate: dict[str, Any], certified: dict[str, Any] | None) -> dict[str, Any]:
    summary = candidate.get("certification_gate_summary") or {}
    if summary:
        return summary
    gates = (certified or {}).get("clean_overlay_certification_gates") or (certified or {}).get("local_certification_gates") or {}
    failed = sorted(str(key) for key, value in gates.items() if value != "pass")
    return {
        "all_pass": bool(gates) and not failed,
        "failed_gates": failed,
        "gate_count": len(gates),
        "gate_counts": dict(sorted(Counter(str(value) for value in gates.values()).items())),
    }


def build_candidate_packet(
    *,
    config: dict[str, Any],
    candidate: dict[str, Any],
    certified: dict[str, Any] | None,
    source_context: dict[str, Any] | None,
) -> dict[str, Any]:
    repo_id = str(candidate["repo_id"])
    source_ref = str(candidate.get("source_ref") or "")
    changed_files = unique_sorted([str(path) for path in (certified or {}).get("changed_files", [])])
    if not changed_files:
        changed_files = unique_sorted([str(path) for path in candidate.get("changed_files", [])])
    implementation_files = unique_sorted([str(path) for path in candidate.get("implementation_files", [])])
    test_files = unique_sorted([str(path) for path in candidate.get("test_files", [])])
    repo_path = config_path(str(config["external_repos"].get(repo_id, "")))
    diff = diff_summary(
        repo_path=repo_path,
        base_commit=str((certified or {}).get("base_commit") or ""),
        target_commit=str((certified or {}).get("target_commit") or ""),
        changed_files=changed_files,
        implementation_files=implementation_files,
        test_files=test_files,
    )
    public_context = public_context_for(candidate, certified, source_context)
    return {
        "schema_version": "barcarolle.phase1.diff_assisted_candidate_packet.v1",
        "task_id": str(candidate["task_id"]),
        "repo_id": repo_id,
        "task_time": str(candidate.get("task_time") or ""),
        "source_ref": source_ref,
        "source_kind": source_kind(source_ref),
        "public_context": public_context,
        "changed_files": changed_files,
        "implementation_files": implementation_files,
        "test_files": test_files,
        "module_or_package": [str(value) for value in candidate.get("module_or_package", [])],
        "certification_gate_summary": certification_summary(candidate, certified),
        "old_statement_quality": {
            "gate": str(candidate.get("statement_quality_gate") or ""),
            "risk_reasons": [str(value) for value in candidate.get("statement_quality_risk_reasons", [])],
            "body_summary_hit_old_cap": bool((candidate.get("statement_quality_diagnostics") or {}).get("body_summary_hit_old_cap")),
            "statement_probably_truncated": bool((candidate.get("statement_quality_diagnostics") or {}).get("statement_probably_truncated")),
            "old_truncation_treated_as_recoverable_renderer_defect": True,
        },
        "diff_summary": {
            key: value
            for key, value in diff.items()
            if key not in {"target_diff_digest", "test_diff_digest"}
        },
        "target_diff_digest": diff.get("target_diff_digest", ""),
        "test_diff_digest": diff.get("test_diff_digest", ""),
        "scope_metadata": {
            "editable_paths": implementation_files,
            "non_editable_test_paths": test_files,
            "implementation_scope_only": True,
            "verifier_command_metadata": str(candidate.get("verifier_command_metadata") or ""),
        },
    }


def load_source_contexts(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("boltons_source_context", "attrs_source_context"):
        rows.extend(read_jsonl(artifact_path(config, key)))
    return row_by_task(rows)


def load_certified_tasks(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("boltons_certified_tasks", "attrs_certified_tasks"):
        rows.extend(read_jsonl(artifact_path(config, key)))
    return row_by_task(rows)


def build_candidate_packets(config: dict[str, Any]) -> dict[str, Any]:
    inventory = read_json(artifact_path(config, "statement_hardened_inventory"))
    certified_by_task = load_certified_tasks(config)
    context_by_task = load_source_contexts(config)
    packets = [
        build_candidate_packet(
            config=config,
            candidate=candidate,
            certified=certified_by_task.get(str(candidate.get("task_id"))),
            source_context=context_by_task.get(str(candidate.get("task_id"))),
        )
        for candidate in inventory.get("candidates", [])
    ]
    return {
        "schema_version": "barcarolle.phase1.diff_assisted_candidate_packets.v1",
        "generated_at": stable_generated_at(config),
        "candidate_count": len(packets),
        "source_inventory_digest": f"sha256:{digest_text(json.dumps(inventory, sort_keys=True))}",
        "raw_target_diffs_committed": False,
        "hidden_verifier_material_included": False,
        "historical_paid_outcomes_included": False,
        "packets": packets,
    }


def render_candidate_packets_markdown(payload: dict[str, Any]) -> str:
    packets = payload["packets"]
    repo_counts = Counter(packet["repo_id"] for packet in packets)
    recoverable_old_cap = sum(1 for packet in packets if packet["old_statement_quality"]["body_summary_hit_old_cap"])
    lines = [
        "# Phase 1 Diff-Assisted Candidate Packets",
        "",
        f"Generated: `{payload['generated_at']}`.",
        "",
        "## Summary",
        "",
        f"- Candidate packets: `{payload['candidate_count']}`.",
        f"- Repos: `{dict(sorted(repo_counts.items()))}`.",
        f"- Old 240-character cap flags treated as recoverable renderer defects: `{recoverable_old_cap}`.",
        "- Raw target diffs committed: `false`.",
        "- Hidden verifier material included: `false`.",
        "- Historical paid outcomes included: `false`.",
        "",
        "## Packets",
        "",
    ]
    for packet in packets:
        lines.extend(
            [
                f"### {packet['task_id']}",
                "",
                f"- Repo: `{packet['repo_id']}`.",
                f"- Source: `{packet['source_ref']}` (`{packet['source_kind']}`).",
                f"- Public title: {packet['public_context']['title'] or '`missing`'}",
                f"- Editable paths: `{', '.join(packet['implementation_files'])}`.",
                f"- Non-editable tests: `{', '.join(packet['test_files'])}`.",
                f"- Diff summary: {packet['diff_summary']['summary']}",
                f"- Old quality gate: `{packet['old_statement_quality']['gate']}`; risks: `{packet['old_statement_quality']['risk_reasons']}`.",
                "",
            ]
        )
    return "\n".join(lines)


def write_candidate_packets(config: dict[str, Any]) -> dict[str, Any]:
    payload = build_candidate_packets(config)
    write_json(output_path(config, "candidate_packets"), payload)
    write_text(output_path(config, "candidate_packets_report"), render_candidate_packets_markdown(payload))
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Phase 1 diff-assisted statement regeneration artifacts.")
    parser.add_argument("mode", choices=["packets"])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if args.mode == "packets":
        write_candidate_packets(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
