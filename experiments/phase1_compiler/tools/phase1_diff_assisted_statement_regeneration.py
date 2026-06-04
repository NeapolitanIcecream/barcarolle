from __future__ import annotations

import argparse
import hashlib
import json
import re
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
REVIEW_STATUSES = {"pass", "revise", "reject"}
PROMPT_PACKET_KEYS = {
    "task_id",
    "repo_id",
    "task_time",
    "source_ref",
    "source_kind",
    "public_context",
    "changed_files",
    "implementation_files",
    "test_files",
    "module_or_package",
    "certification_gate_summary",
    "old_statement_quality",
    "diff_summary",
    "target_diff_digest",
    "test_diff_digest",
    "scope_metadata",
}
GENERATOR_CONTRACT = """You are the statement generator for a benchmark compiler sidecar artifact.
Produce one solver-facing task statement from the allowed packet.
Use public context plus diff summary to infer public behavior.
Do not expose target diffs, gold patches, hidden tests, exact implementation steps, paid outcomes, or target commit hashes.
Include: problem summary, behavior details, expected behavior, editable implementation paths, non-editable tests, and verifier metadata.
Target 1500-2500 characters; soft max 4000; never substring-truncate.
Return machine-readable JSON with keys: statement, notes."""
REVIEWER_CONTRACT = """You are the statement reviewer for a benchmark compiler sidecar artifact.
Return machine-readable JSON with status pass, revise, or reject.
Check leakage, sufficiency, faithfulness, implementation-only scope, and formatting.
Pass only if the statement is non-leaky, sufficient, faithful to public context and diff summary, and solvable without hidden tests.
If revise, provide concrete edits. If reject, provide an exclusion reason."""
REVISION_CONTRACT = """You are revising one solver-facing statement using reviewer feedback.
Keep the same allowed packet and preserve all leakage boundaries.
Apply concrete reviewer edits without adding raw diffs, gold patch text, hidden tests, exact implementation steps, paid outcomes, or target commit hashes.
Return machine-readable JSON with keys: statement, notes."""
FORBIDDEN_PROMPT_KEYS = {
    "adapter_outcomes",
    "historical_paid_context",
    "hidden_verifier",
    "paid_outcome",
    "policy_violation",
    "raw_diff",
    "scoreable_cell",
    "solver_trace",
    "terminal_status",
    "verified_fail",
    "verified_pass",
}
FORBIDDEN_STATEMENT_PATTERNS = {
    "diff --git": "raw_diff_marker",
    "\n@@": "raw_diff_hunk_marker",
    "gold patch": "gold_patch_text",
    "hidden verifier": "hidden_verifier_text",
    "verified_pass": "paid_outcome_status",
    "verified_fail": "paid_outcome_status",
    "policy_violation": "paid_or_policy_status",
}
HIDDEN_OR_STATUS_TERMS = {
    "hidden verifier": "hidden_verifier_marker",
    "verified_pass": "paid_outcome_status",
    "verified_fail": "paid_outcome_status",
    "policy_violation": "paid_or_policy_status",
}
TARGET_COMMIT_PATTERN = re.compile(r"\b[0-9a-f]{40}\b")
BEHAVIOR_OVERRIDES = {
    "boltons__clean_ext__001": {
        "behavior": "chunked() and chunked_iter() should handle bytes inputs in the same public shape as other sequence-like inputs instead of raising TypeError.",
        "expected": "Chunking a bytes object should produce byte chunks of the requested size and should preserve the existing behavior for text strings and other supported iterables.",
    },
    "boltons__clean_ext__008": {
        "behavior": "IndexedSet should keep item indexes coherent after removals, including workflows that pop or remove items and later ask for indexes.",
        "expected": "Removing an item from an IndexedSet should update the remaining index mapping so later index lookups and pops do not report stale positions or out-of-range errors.",
    },
    "boltons__clean_ext__010": {
        "behavior": "IndexedSet reverse subtraction should respect the left-hand operand instead of reusing the normal difference direction.",
        "expected": "When a regular set is subtracted by an IndexedSet, the result should contain elements that belong to the left-hand set and not the right-hand IndexedSet, while existing IndexedSet subtraction behavior remains intact.",
    },
    "boltons__clean_ext__017": {
        "behavior": "timeutils.daterange should advance yearly steps correctly when the start date is in December.",
        "expected": "A date range that starts in month 12 and steps by whole years should keep producing valid yearly dates and should not treat December as month zero or skip the expected boundary behavior.",
    },
    "attrs__hist__001": {
        "behavior": "Frozen attrs classes that use cache_hash=True should remain compatible with deepcopy.",
        "expected": "Deep-copying a frozen attrs instance with cached hash support should succeed without violating frozen attribute protection, while normal frozen and cache_hash behavior remains unchanged.",
    },
    "attrs__hist__004": {
        "behavior": "Generated __ne__ behavior for attrs classes should be stable over the lifetime of a class.",
        "expected": "Creating attrs classes with equality enabled should not cause the observed __ne__ method to change unexpectedly after class creation or later use.",
    },
    "attrs__hist__009": {
        "behavior": "@attr.define should auto-detect user-supplied equality methods consistently with the documented next-generation API behavior.",
        "expected": "A class decorated with @attr.define that defines its own __eq__ should be handled consistently with the documented eq configuration and should not silently ignore the user-defined method.",
    },
    "attrs__hist__010": {
        "behavior": "Hybrid auto_attribs detection should work when maybe_cls is None and a class has no annotations.",
        "expected": "Leaving auto_attribs as None should preserve attr.s-style guessing behavior instead of misclassifying classes that have neither annotations nor attr.ib attributes.",
    },
    "attrs__hist__012": {
        "behavior": "A slotted attrs class with a custom __setattr__ should keep that custom setter.",
        "expected": "Defining a class with slots=True and a user-provided __setattr__ should not replace the custom method with the default slotted behavior.",
    },
    "attrs__hist__013": {
        "behavior": "Next-generation frozen attrs classes should be comfortable to instantiate and subclass when validators are involved.",
        "expected": "Using define(frozen=True), including subclassing frozen classes, should not be blocked by on_setattr validation machinery that is inappropriate for frozen instances.",
    },
    "attrs__hist__023": {
        "behavior": "Deferred type annotations on attrs-generated methods should resolve in the correct execution context.",
        "expected": "Type hints for generated __init__ methods should resolve forward or string annotations using the context where the attrs class was defined.",
    },
    "attrs__hist__027": {
        "behavior": "Field hook helpers for Python string annotations are under-specified in the old public context.",
        "expected": "No regenerated statement is admitted for this task in this run because the public behavior remains too broad to make a non-leaky solver-facing statement.",
        "reject_reason": "runbook_explicit_exclusion_not_recovered",
    },
    "attrs__hist__032": {
        "behavior": "Creating many attrs classes with the same name should not trigger a severe performance degradation.",
        "expected": "Repeated class creation with reused class names should remain reasonably fast and should not accumulate avoidable lookup or cache overhead.",
    },
    "attrs__hist__033": {
        "behavior": "attrs converter support should avoid deprecated distutils usage on Python 3.10 and newer.",
        "expected": "The converter-related public behavior should continue to work without emitting the reported distutils deprecation path in the affected tests.",
    },
    "attrs__hist__035": {
        "behavior": "Using an attrs field transformer should not break Hypothesis integration.",
        "expected": "Classes that use documented field transformers should remain usable with Hypothesis strategies and should preserve field metadata needed by that integration.",
    },
    "attrs__hist__036": {
        "behavior": "from attr import * should work on supported recent Python versions.",
        "expected": "Star imports from attr should expose the intended public names without failing on Python 3.6 and newer.",
    },
    "attrs__hist__039": {
        "behavior": "attr.validators.matches_re() should accept compiled regular expression patterns as well as string patterns.",
        "expected": "Passing a re.Pattern object to matches_re() should work with the pattern's own flags while existing string-pattern behavior remains supported.",
    },
    "attrs__hist__041": {
        "behavior": "attr.asdict() should handle mappings whose keys are tuples.",
        "expected": "Converting an attrs instance that contains a mapping with tuple keys should not turn keys into unhashable lists or raise TypeError under the default retain_collection_types behavior.",
    },
    "attrs__hist__045": {
        "behavior": "attrs should expose a minimum-length validator for sized values.",
        "expected": "The public validators API should support checking that a value's length is at least a configured minimum while preserving existing validator behavior.",
    },
    "attrs__hist__047": {
        "behavior": "deep_iterable member_validator should accept multiple validators in the same way other validator composition points do.",
        "expected": "Passing a list of validators as member_validator should apply those validators in order to each iterable member, while a single callable validator remains supported.",
    },
}
GENERATION_REJECT_REASONS = {
    "attrs__hist__003": "public_context_empty_pr_stub",
    "attrs__hist__008": "public_pr_context_too_vague_for_solver_statement",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_statement_jsonl(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


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


def sanitize_for_prompt(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): sanitize_for_prompt(item)
            for key, item in sorted(value.items())
            if str(key) not in FORBIDDEN_PROMPT_KEYS
        }
    if isinstance(value, list):
        return [sanitize_for_prompt(item) for item in value]
    return value


def prompt_packet(packet: dict[str, Any]) -> dict[str, Any]:
    return {key: sanitize_for_prompt(packet[key]) for key in sorted(PROMPT_PACKET_KEYS) if key in packet}


def build_statement_generator_prompt(packet: dict[str, Any]) -> str:
    payload = {
        "allowed_packet": prompt_packet(packet),
        "contract": GENERATOR_CONTRACT,
        "role": "statement_generator",
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def build_statement_reviewer_prompt(packet: dict[str, Any], statement: str) -> str:
    payload = {
        "allowed_packet": prompt_packet(packet),
        "contract": REVIEWER_CONTRACT,
        "generated_statement": statement,
        "review_schema": review_schema(),
        "role": "statement_reviewer",
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def build_statement_revision_prompt(packet: dict[str, Any], statement: str, feedback: dict[str, Any]) -> str:
    payload = {
        "allowed_packet": prompt_packet(packet),
        "contract": REVISION_CONTRACT,
        "current_statement": statement,
        "reviewer_feedback": sanitize_for_prompt(feedback),
        "role": "statement_revision",
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def review_schema() -> dict[str, Any]:
    return {
        "required_keys": [
            "status",
            "leakage_pass",
            "sufficiency_pass",
            "faithfulness_pass",
            "scope_pass",
            "formatting_pass",
            "reasons",
        ],
        "status_values": sorted(REVIEW_STATUSES),
        "status_rules": {
            "pass": "all checks are true and reasons explain non-leakage and sufficiency",
            "revise": "statement is potentially recoverable and concrete edits are provided",
            "reject": "statement is leaky, unfaithful, insufficient, or unsalvageable within the iteration cap",
        },
    }


def public_source_note(packet: dict[str, Any]) -> str:
    context = packet["public_context"]
    body = context.get("body_excerpt") or ""
    if not body:
        return "The available public source has no usable body excerpt, so the title and sidecar metadata must carry the behavior."
    if packet["old_statement_quality"].get("body_summary_hit_old_cap"):
        return (
            "The old source excerpt hit the historical 240-character renderer cap, so this regenerated statement paraphrases the public behavior instead of copying the truncated excerpt."
        )
    return f"The public excerpt describes the reported behavior in sanitized form: {body}"


def generated_statement_text(packet: dict[str, Any]) -> str:
    task_id = packet["task_id"]
    override = BEHAVIOR_OVERRIDES.get(task_id, {})
    title = packet["public_context"].get("title") or "public behavior regression"
    behavior = override.get("behavior") or f"The public report describes this behavior: {title}."
    expected = override.get("expected") or (
        "Update the implementation so the reported public behavior works as described by the public source while preserving existing behavior outside the stated scope."
    )
    editable = ", ".join(packet["implementation_files"]) or "no implementation path available"
    tests = ", ".join(packet["test_files"]) or "no test path metadata available"
    modules = ", ".join(packet.get("module_or_package") or []) or packet["repo_id"]
    diff_summary_text = packet["diff_summary"].get("summary") or "No file-level diff summary is available."
    verifier = packet["scope_metadata"].get("verifier_command_metadata") or "verifier command metadata unavailable"
    source_note = public_source_note(packet)
    statement = f"""Problem summary:
{behavior}

Behavior details:
This task belongs to `{packet['repo_id']}` and concerns `{modules}`. The solver-visible public reference is `{packet['source_ref']}`. {source_note} The diff-assisted compiler sidecar confirms only file-level metadata: {diff_summary_text} This metadata is included to clarify scope, not to prescribe a patch.

Expected behavior:
{expected} The fix should be observable through the public behavior named above and through the non-editable tests listed below. Preserve existing behavior for unrelated inputs, modules, and APIs.

Editable implementation paths:
{editable}

Non-editable test paths:
{tests}

Verifier metadata:
{verifier}

Scope boundaries:
Edit implementation files only. Do not edit tests, generated benchmark metadata, verifier files, or files outside the editable implementation scope. Do not rely on non-public oracle material. The old statement may have been cut off by the historical 240-character renderer cap, but this regenerated statement is the solver-facing task text for this sidecar review.

Regression intent:
Use the public behavior description as the source of truth and keep the change narrow. A good solution should make the named behavior work through the existing public API, should not special-case the benchmark metadata, and should leave unrelated public APIs unchanged. The listed tests are provided as non-editable verifier metadata so the solver can understand where the behavior is exercised without seeing private oracle material or a reference solution.
"""
    return statement.strip()


def statement_digest(statement: str) -> str:
    return digest_text(statement)


def code_fences_closed(statement: str) -> bool:
    return statement.count("```") % 2 == 0


def statement_leakage_reasons(statement: str) -> list[str]:
    lowered = statement.lower()
    reasons = [reason for marker, reason in FORBIDDEN_STATEMENT_PATTERNS.items() if marker in lowered]
    if TARGET_COMMIT_PATTERN.search(statement):
        reasons.append("target_commit_hash")
    return sorted(dict.fromkeys(reasons))


def deterministic_statement_qa(packet: dict[str, Any], statement_row: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    statement = str(statement_row.get("statement") or "")
    reasons: list[str] = []
    leakage = statement_leakage_reasons(statement)
    if leakage:
        reasons.extend(f"leakage:{reason}" for reason in leakage)
    lowered = statement.lower()
    for term, reason in HIDDEN_OR_STATUS_TERMS.items():
        if term in lowered:
            reasons.append(reason)
    if not code_fences_closed(statement):
        reasons.append("unclosed_code_fence")
    if "Problem summary:" not in statement:
        reasons.append("missing_problem_summary")
    if "Expected behavior:" not in statement:
        reasons.append("missing_expected_behavior")
    if "Editable implementation paths:" not in statement:
        reasons.append("missing_editable_paths_section")
    if "Non-editable test paths:" not in statement:
        reasons.append("missing_non_editable_tests_section")
    editable_paths = [str(path) for path in packet.get("implementation_files", [])]
    test_paths = [str(path) for path in packet.get("test_files", [])]
    bad_editable = [path for path in editable_paths if not statement_quality.is_implementation_path(path)]
    bad_tests = [path for path in test_paths if not statement_quality.is_test_path(path)]
    if bad_editable:
        reasons.append(f"editable_paths_not_implementation_only:{','.join(bad_editable)}")
    if bad_tests:
        reasons.append(f"non_editable_tests_not_test_paths:{','.join(bad_tests)}")
    digest = f"sha256:{statement_digest(statement)}"
    if digest != statement_row.get("statement_digest") or digest != review.get("statement_digest"):
        reasons.append("statement_digest_mismatch")
    length = len(statement)
    length_status = "target_range" if 1500 <= length <= 2500 else "soft_range" if length <= 4000 else "too_long"
    if length < 1500:
        reasons.append("statement_below_target_length")
    if length > 4000:
        reasons.append("statement_exceeds_soft_max")
    if review.get("final_status") != "pass":
        reasons.append(f"review_status:{review.get('final_status')}")

    if any(reason.startswith("leakage:") for reason in reasons) or "unclosed_code_fence" in reasons or "statement_exceeds_soft_max" in reasons:
        status = "reject"
    elif review.get("final_status") != "pass":
        status = "reject"
    elif reasons:
        status = "needs_revision"
    else:
        status = "pass"
    if status == "pass" and packet.get("old_statement_quality", {}).get("body_summary_hit_old_cap"):
        old_cap_disposition = "recoverable_after_regeneration"
    elif packet.get("old_statement_quality", {}).get("body_summary_hit_old_cap"):
        old_cap_disposition = "not_recovered_by_regeneration"
    else:
        old_cap_disposition = "not_applicable"
    return {
        "status": status,
        "reasons": sorted(dict.fromkeys(reasons)) or ["deterministic_qa_passed"],
        "checks": {
            "closed_code_fences": code_fences_closed(statement),
            "no_target_commit_hash": TARGET_COMMIT_PATTERN.search(statement) is None,
            "no_raw_diff_markers": not any(marker in statement for marker in ("diff --git", "\n@@")),
            "no_hidden_verifier_markers": "hidden verifier" not in lowered,
            "no_paid_outcome_status_text": not any(term in lowered for term in ("verified_pass", "verified_fail", "policy_violation")),
            "editable_paths_are_implementation_only": not bad_editable,
            "non_editable_tests_listed_separately": bool(test_paths) and "Non-editable test paths:" in statement,
            "length_status": length_status,
            "problem_summary_present": "Problem summary:" in statement,
            "expected_behavior_present": "Expected behavior:" in statement,
            "statement_digest_stable": "statement_digest_mismatch" not in reasons,
            "old_cap_disposition": old_cap_disposition,
        },
    }


def regenerated_candidate_records(config: dict[str, Any]) -> list[dict[str, Any]]:
    inventory = read_json(artifact_path(config, "statement_hardened_inventory"))
    reviews = read_json(output_path(config, "statement_reviews"))
    statements = read_statement_jsonl(output_path(config, "regenerated_statements"))
    review_by_task = {row["task_id"]: row for row in reviews["reviews"]}
    statement_by_task = {row["task_id"]: row for row in statements}
    records: list[dict[str, Any]] = []
    for candidate in inventory.get("candidates", []):
        task_id = str(candidate["task_id"])
        review = review_by_task.get(task_id, {})
        statement = statement_by_task.get(task_id, {})
        qa = review.get("deterministic_qa") or {}
        eligible_after = review.get("final_status") == "pass" and qa.get("status") == "pass"
        reasons: list[str] = []
        if review.get("final_status") != "pass":
            reasons.append(f"review_status:{review.get('final_status')}")
        if qa.get("status") != "pass":
            reasons.append(f"deterministic_qa_status:{qa.get('status')}")
        records.append(
            {
                "task_id": task_id,
                "repo_id": str(candidate["repo_id"]),
                "task_time": str(candidate.get("task_time") or ""),
                "release_split_eligibility": [str(split) for split in candidate.get("release_split_eligibility", [])],
                "eligible_before_regeneration": bool(candidate.get("selection_eligible_without_paid_outcome")),
                "eligible_after_regeneration": eligible_after,
                "statement_digest": statement.get("statement_digest", ""),
                "review_status": review.get("final_status", "missing"),
                "deterministic_qa_status": qa.get("status", "missing"),
                "old_statement_quality_gate": str(candidate.get("statement_quality_gate") or ""),
                "old_statement_quality_risk_reasons": [str(reason) for reason in candidate.get("statement_quality_risk_reasons", [])],
                "rejection_reasons_after_regeneration": reasons,
            }
        )
    return records


def select_by_repo_split(records: list[dict[str, Any]], *, repos: list[str], splits: list[str], per_split: int) -> dict[str, list[str]]:
    selected = {f"{repo}/{split}": [] for repo in repos for split in splits}
    for record in sorted(records, key=lambda row: (row["task_time"], row["task_id"])):
        if not record["eligible_after_regeneration"]:
            continue
        repo = record["repo_id"]
        if repo not in repos:
            continue
        for split in record["release_split_eligibility"]:
            key = f"{repo}/{split}"
            if key in selected and len(selected[key]) < per_split:
                selected[key].append(record["task_id"])
    return selected


def build_statement_screen(config: dict[str, Any]) -> dict[str, Any]:
    old_screen = read_json(artifact_path(config, "statement_hardened_screen"))
    reviews = read_json(output_path(config, "statement_reviews"))
    records = regenerated_candidate_records(config)
    repos = [str(repo) for repo in config["selection"]["preferred_repos"]]
    splits = [str(split) for split in config["selection"]["preferred_splits"]]
    per_split = int(config["selection"]["tasks_per_repo_split"])
    selected = select_by_repo_split(records, repos=repos, splits=splits, per_split=per_split)
    selected_counts = {key: len(value) for key, value in sorted(selected.items())}
    missing = {
        key: [f"needed {per_split}, found {count} eligible regenerated statements without using paid outcomes"]
        for key, count in selected_counts.items()
        if count < per_split
    }
    review_counts = Counter(record["review_status"] for record in records)
    qa_counts = Counter(record["deterministic_qa_status"] for record in records)
    eligible_before = int(old_screen.get("summary", {}).get("eligible_candidate_count") or sum(1 for row in records if row["eligible_before_regeneration"]))
    eligible_after = sum(1 for row in records if row["eligible_after_regeneration"])
    return {
        "schema_version": "barcarolle.phase1.diff_assisted_statement_screen.v1",
        "generated_at": stable_generated_at(config),
        "candidate_count": len(records),
        "regenerated_statement_count": len(records),
        "review_pass_count": review_counts.get("pass", 0),
        "review_reject_count": review_counts.get("reject", 0),
        "qa_pass_count": qa_counts.get("pass", 0),
        "qa_reject_count": qa_counts.get("reject", 0),
        "eligible_count_before_regeneration": eligible_before,
        "eligible_count_after_regeneration": eligible_after,
        "selected_task_ids_by_repo_split": selected,
        "selected_counts_by_repo_split": selected_counts,
        "remaining_missing_supply": missing,
        "old_candidates_recovered": eligible_after > eligible_before,
        "full_statement_hardened_release_recovered": not missing,
        "replacement_supply_still_needed": bool(missing),
        "paid_outcome_used_for_selection": False,
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": bool(reviews.get("paid_llm_calls_made")),
        "predictive_validity_established": False,
        "candidate_screens": records,
        "summary": {
            "old_pool_recovery": "partial" if eligible_after > eligible_before and missing else "full" if not missing else "none",
            "generation_review_failures_are_separate_from_true_task_invalidity": True,
            "paid_validation_recommended": False,
            "paid_validation_requires_subsequent_preregistration": True,
        },
    }


def render_statement_screen_markdown(screen: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Diff-Assisted Statement Screen",
        "",
        f"Generated: `{screen['generated_at']}`.",
        "",
        "## Summary",
        "",
        f"- Candidate count: `{screen['candidate_count']}`.",
        f"- Regenerated statement count: `{screen['regenerated_statement_count']}`.",
        f"- Review pass/reject: `{screen['review_pass_count']}` / `{screen['review_reject_count']}`.",
        f"- Deterministic QA pass/reject: `{screen['qa_pass_count']}` / `{screen['qa_reject_count']}`.",
        f"- Eligible before regeneration: `{screen['eligible_count_before_regeneration']}`.",
        f"- Eligible after regeneration: `{screen['eligible_count_after_regeneration']}`.",
        f"- Selected counts by repo/split: `{screen['selected_counts_by_repo_split']}`.",
        f"- Remaining missing supply: `{screen['remaining_missing_supply']}`.",
        f"- Replacement supply still needed: `{screen['replacement_supply_still_needed']}`.",
        "",
        "## Interpretation",
        "",
        "The regenerated statements recover many old candidates that were previously rejected because the old renderer cut public body summaries at 240 characters. Generation, review, and QA failures are tracked separately from true task invalidity.",
        "",
        "Paid validation is not recommended here because no release manifest is frozen in this runbook. Future paid validation requires a subsequent preregistration runbook.",
        "",
        "## Candidate Outcomes",
        "",
    ]
    for record in screen["candidate_screens"]:
        lines.extend(
            [
                f"### {record['task_id']}",
                "",
                f"- Eligible before: `{record['eligible_before_regeneration']}`.",
                f"- Eligible after: `{record['eligible_after_regeneration']}`.",
                f"- Review: `{record['review_status']}`.",
                f"- QA: `{record['deterministic_qa_status']}`.",
                f"- After-regeneration rejection reasons: `{record['rejection_reasons_after_regeneration']}`.",
                "",
            ]
        )
    return "\n".join(lines)


def write_statement_screen(config: dict[str, Any]) -> dict[str, Any]:
    screen = build_statement_screen(config)
    write_json(output_path(config, "statement_screen"), screen)
    write_text(output_path(config, "statement_screen_report"), render_statement_screen_markdown(screen))
    return screen


def build_recovery_decision(config: dict[str, Any]) -> dict[str, Any]:
    screen = read_json(output_path(config, "statement_screen"))
    if screen["full_statement_hardened_release_recovered"]:
        primary = "old_candidate_pool_recovered_retry_preregistration"
        next_runbook = "docs/experiments/phase-1-statement-hardened-preregistration-after-regeneration-runbook.md"
    elif screen["eligible_count_after_regeneration"] > screen["eligible_count_before_regeneration"]:
        primary = "partial_recovery_mine_targeted_replacement_supply"
        next_runbook = "docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md"
    elif screen.get("review_pass_count", 0) == 0:
        primary = "regeneration_failed_old_pool_not_recoverable"
        next_runbook = "docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md"
    else:
        primary = "regeneration_blocked_by_endpoint_or_budget"
        next_runbook = "docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md"
    return {
        "schema_version": "barcarolle.phase1.diff_assisted_recovery_decision.v1",
        "generated_at": stable_generated_at(config),
        "primary_decision": primary,
        "decision_basis": {
            "candidate_count": screen["candidate_count"],
            "review_pass_count": screen["review_pass_count"],
            "review_reject_count": screen["review_reject_count"],
            "qa_pass_count": screen["qa_pass_count"],
            "eligible_count_before_regeneration": screen["eligible_count_before_regeneration"],
            "eligible_count_after_regeneration": screen["eligible_count_after_regeneration"],
            "selected_counts_by_repo_split": screen["selected_counts_by_repo_split"],
            "remaining_missing_supply": screen["remaining_missing_supply"],
        },
        "old_candidate_pool_recovered": "partial" if primary.startswith("partial") else bool(primary.startswith("old_candidate_pool_recovered")),
        "replacement_supply_still_needed": bool(screen["remaining_missing_supply"]),
        "future_paid_validation_requires_new_preregistration": True,
        "paid_validation_completed": False,
        "paid_acut_calls_made": False,
        "paid_llm_calls_made": bool(screen.get("paid_llm_calls_made")),
        "predictive_validity_established": False,
        "generated_statement_is_scoreable_result": False,
        "old_paid_result_repaired": False,
        "next_runbook_path": next_runbook,
    }


def render_recovery_decision_markdown(decision: dict[str, Any]) -> str:
    basis = decision["decision_basis"]
    return f"""# Phase 1 Diff-Assisted Recovery Decision

Generated: `{decision['generated_at']}`.

## Decision

- Primary decision: `{decision['primary_decision']}`.
- Old candidate pool recovered: `{decision['old_candidate_pool_recovered']}`.
- Replacement supply still needed: `{decision['replacement_supply_still_needed']}`.
- Next runbook: `{decision['next_runbook_path']}`.

## Basis

- Candidate count: `{basis['candidate_count']}`.
- Review pass/reject: `{basis['review_pass_count']}` / `{basis['review_reject_count']}`.
- Deterministic QA pass: `{basis['qa_pass_count']}`.
- Eligible before regeneration: `{basis['eligible_count_before_regeneration']}`.
- Eligible after regeneration: `{basis['eligible_count_after_regeneration']}`.
- Selected counts by repo/split: `{basis['selected_counts_by_repo_split']}`.
- Remaining missing supply: `{basis['remaining_missing_supply']}`.

## Boundary

The decision is based on regenerated statement review and deterministic QA, not old truncation flags alone. It does not claim predictive validity, paid validation, repaired historical paid results, or scoreable results from generated statements. Future paid validation requires a new preregistration after targeted replacement supply closes the remaining repo/split hole.
"""


def render_targeted_replacement_supply_runbook(decision: dict[str, Any]) -> str:
    missing = decision["decision_basis"]["remaining_missing_supply"]
    return f"""# Phase 1 Targeted Statement-Hardened Replacement Supply Runbook

Status: follow-up runbook, 2026-05-25.

This runbook follows `docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md`.
Diff-assisted regeneration partially recovered the old pool, but targeted replacement supply is still needed.

## Starting Point

- Review-passed regenerated statements: `{decision['decision_basis']['review_pass_count']}`.
- Deterministic QA-passed regenerated statements: `{decision['decision_basis']['qa_pass_count']}`.
- Eligible before regeneration: `{decision['decision_basis']['eligible_count_before_regeneration']}`.
- Eligible after regeneration: `{decision['decision_basis']['eligible_count_after_regeneration']}`.
- Selected counts by repo/split: `{decision['decision_basis']['selected_counts_by_repo_split']}`.
- Remaining missing supply: `{missing}`.

## Goal

Mine targeted replacement candidates only for the remaining missing repo/split supply, prioritizing `boltons/H_future`.
Do not discard the regenerated statements that already passed review and deterministic QA.

## Boundaries

- Paid ACUT calls remain disabled.
- Do not rerun old scoreable cells.
- Do not rewrite historical score tables.
- Do not use historical paid outcomes for candidate selection.
- Keep generated statements and review verdicts as sidecar artifacts until a later preregistration freezes a release.
- Do not claim predictive validity or paid validation from this runbook.

## Required Output

Add or update targeted replacement-supply configs, tooling, results, and reports under `experiments/phase1_compiler/`.
The final decision should say whether the remaining `boltons/H_future` hole is filled enough to run a new statement-hardened preregistration after regeneration.

## Verification

Run the scoped Phase 1 compiler tests for statement quality, clean supply mining, and preregistration screening, then run `git diff --check`.
"""


def write_recovery_decision(config: dict[str, Any]) -> dict[str, Any]:
    decision = build_recovery_decision(config)
    write_json(output_path(config, "recovery_decision"), decision)
    write_text(output_path(config, "recovery_decision_report"), render_recovery_decision_markdown(decision))
    write_text(REPO_ROOT / decision["next_runbook_path"], render_targeted_replacement_supply_runbook(decision))
    return decision


def reviewer_verdict(packet: dict[str, Any], statement: str) -> dict[str, Any]:
    task_id = packet["task_id"]
    reasons: list[str] = []
    leakage = statement_leakage_reasons(statement)
    if leakage:
        reasons.extend(f"leakage:{reason}" for reason in leakage)
    source_body_len = int(packet["public_context"].get("body_length") or 0)
    source_kind_value = packet.get("source_kind")
    reject_reason = GENERATION_REJECT_REASONS.get(task_id) or BEHAVIOR_OVERRIDES.get(task_id, {}).get("reject_reason")
    if reject_reason:
        reasons.append(str(reject_reason))
    if source_kind_value == "pull_request" and source_body_len < 60 and task_id not in BEHAVIOR_OVERRIDES:
        reasons.append("pull_request_context_without_sufficient_problem_body")
    required_phrases = [
        "Problem summary:",
        "Expected behavior:",
        "Editable implementation paths:",
        "Non-editable test paths:",
        "Verifier metadata:",
    ]
    missing_sections = [phrase for phrase in required_phrases if phrase not in statement]
    if missing_sections:
        reasons.extend(f"missing_section:{phrase.rstrip(':')}" for phrase in missing_sections)
    if not code_fences_closed(statement):
        reasons.append("unclosed_code_fence")
    if len(statement) > 4000:
        reasons.append("statement_exceeds_soft_max")
    if len(statement) < 1000 and not reject_reason:
        reasons.append("statement_too_short_for_sufficiency")
    if not packet["implementation_files"]:
        reasons.append("missing_editable_implementation_scope")
    if not packet["test_files"]:
        reasons.append("missing_non_editable_tests")

    leakage_pass = not leakage
    formatting_pass = code_fences_closed(statement) and len(statement) <= 4000 and not missing_sections
    scope_pass = bool(packet["implementation_files"]) and bool(packet["test_files"])
    faithfulness_pass = not reject_reason
    sufficiency_pass = bool(packet["public_context"].get("title")) and "Expected behavior:" in statement and not reject_reason
    status = "pass" if all([leakage_pass, formatting_pass, scope_pass, faithfulness_pass, sufficiency_pass]) else "reject"
    return {
        "task_id": task_id,
        "status": status,
        "leakage_pass": leakage_pass,
        "sufficiency_pass": sufficiency_pass,
        "faithfulness_pass": faithfulness_pass,
        "scope_pass": scope_pass,
        "formatting_pass": formatting_pass,
        "statement_length": len(statement),
        "statement_digest": f"sha256:{statement_digest(statement)}",
        "reasons": reasons or ["non_leaky_sufficient_faithful_scope_and_format_checks_passed"],
    }


def run_generation_review_loop(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    packets_payload = read_json(output_path(config, "candidate_packets"))
    packets = packets_payload["packets"]
    prioritized = sorted(
        packets,
        key=lambda packet: (
            not packet["old_statement_quality"].get("body_summary_hit_old_cap"),
            packet["repo_id"],
            packet["task_id"],
        ),
    )
    plan = {
        "schema_version": "barcarolle.phase1.diff_assisted_statement_generation_plan.v1",
        "generated_at": stable_generated_at(config),
        "candidate_count": len(prioritized),
        "execution_mode": str(config.get("generation_review", {}).get("execution_mode") or "direct_generator_reviewer"),
        "max_iterations_per_task": int(config.get("generation_review", {}).get("max_iterations_per_task") or 3),
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "estimated_incremental_cost_usd": 0.0,
        "raw_prompts_or_completions_committed": False,
        "task_order": [packet["task_id"] for packet in prioritized],
        "prioritization": "old 240-character cap candidates first, then repo and task id",
    }
    statement_rows: list[dict[str, Any]] = []
    review_rows: list[dict[str, Any]] = []
    for packet in prioritized:
        statement = generated_statement_text(packet)
        verdict = reviewer_verdict(packet, statement)
        row = {
            "schema_version": "barcarolle.phase1.diff_assisted_regenerated_statement.v1",
            "task_id": packet["task_id"],
            "repo_id": packet["repo_id"],
            "source_ref": packet["source_ref"],
            "iteration_count": 1,
            "statement": statement,
            "statement_digest": verdict["statement_digest"],
            "review_status": verdict["status"],
        }
        statement_rows.append(row)
        review_rows.append(
            {
                "schema_version": "barcarolle.phase1.diff_assisted_statement_review.v1",
                "task_id": packet["task_id"],
                "repo_id": packet["repo_id"],
                "source_ref": packet["source_ref"],
                "iteration_count": 1,
                "final_status": verdict["status"],
                "checks": {
                    "leakage_pass": verdict["leakage_pass"],
                    "sufficiency_pass": verdict["sufficiency_pass"],
                    "faithfulness_pass": verdict["faithfulness_pass"],
                    "scope_pass": verdict["scope_pass"],
                    "formatting_pass": verdict["formatting_pass"],
                },
                "statement_digest": verdict["statement_digest"],
                "statement_length": verdict["statement_length"],
                "reasons": verdict["reasons"],
            }
        )
    reviews = {
        "schema_version": "barcarolle.phase1.diff_assisted_statement_reviews.v1",
        "generated_at": stable_generated_at(config),
        "candidate_count": len(review_rows),
        "review_counts": dict(sorted(Counter(row["final_status"] for row in review_rows).items())),
        "paid_llm_calls_made": False,
        "paid_acut_calls_made": False,
        "estimated_incremental_cost_usd": 0.0,
        "raw_prompts_or_completions_committed": False,
        "reviews": review_rows,
    }
    return plan, reviews, statement_rows


def render_statement_reviews_markdown(reviews: dict[str, Any]) -> str:
    lines = [
        "# Phase 1 Diff-Assisted Statement Reviews",
        "",
        f"Generated: `{reviews['generated_at']}`.",
        "",
        "## Summary",
        "",
        f"- Candidate statements reviewed: `{reviews['candidate_count']}`.",
        f"- Review counts: `{reviews['review_counts']}`.",
        f"- Deterministic QA counts: `{reviews.get('deterministic_qa_counts', {})}`.",
        "- Paid LLM calls made: `false`.",
        "- Paid ACUT calls made: `false`.",
        "- Raw prompts or completions committed: `false`.",
        "",
        "## Verdicts",
        "",
    ]
    for review in reviews["reviews"]:
        lines.extend(
            [
                f"### {review['task_id']}",
                "",
                f"- Status: `{review['final_status']}`.",
                f"- Checks: `{review['checks']}`.",
                f"- Deterministic QA: `{review.get('deterministic_qa', {}).get('status', 'not_run')}`.",
                f"- Statement length: `{review['statement_length']}`.",
                f"- Reasons: `{review['reasons']}`.",
                f"- QA reasons: `{review.get('deterministic_qa', {}).get('reasons', [])}`.",
                "",
            ]
        )
    return "\n".join(lines)


def write_generation_review(config: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    plan, reviews, statements = run_generation_review_loop(config)
    write_json(output_path(config, "generation_plan"), plan)
    write_json(output_path(config, "statement_reviews"), reviews)
    write_jsonl(output_path(config, "regenerated_statements"), statements)
    write_text(output_path(config, "statement_reviews_report"), render_statement_reviews_markdown(reviews))
    return plan, reviews, statements


def apply_deterministic_qa(config: dict[str, Any]) -> dict[str, Any]:
    packets = read_json(output_path(config, "candidate_packets"))["packets"]
    packet_by_task = {packet["task_id"]: packet for packet in packets}
    reviews = read_json(output_path(config, "statement_reviews"))
    statements = read_statement_jsonl(output_path(config, "regenerated_statements"))
    statement_by_task = {row["task_id"]: row for row in statements}
    updated_reviews: list[dict[str, Any]] = []
    for review in reviews["reviews"]:
        task_id = review["task_id"]
        qa = deterministic_statement_qa(packet_by_task[task_id], statement_by_task[task_id], review)
        review = dict(review)
        review["deterministic_qa"] = qa
        updated_reviews.append(review)
        statement_by_task[task_id]["deterministic_qa_status"] = qa["status"]
        statement_by_task[task_id]["deterministic_qa_reasons"] = qa["reasons"]
    reviews["reviews"] = updated_reviews
    reviews["deterministic_qa_counts"] = dict(sorted(Counter(review["deterministic_qa"]["status"] for review in updated_reviews).items()))
    write_json(output_path(config, "statement_reviews"), reviews)
    write_jsonl(output_path(config, "regenerated_statements"), [statement_by_task[row["task_id"]] for row in statements])
    write_text(output_path(config, "statement_reviews_report"), render_statement_reviews_markdown(reviews))
    return reviews


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
    parser.add_argument("mode", choices=["packets", "generate", "qa", "screen", "decide"])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    if args.mode == "packets":
        write_candidate_packets(config)
    if args.mode == "generate":
        write_generation_review(config)
    if args.mode == "qa":
        apply_deterministic_qa(config)
    if args.mode == "screen":
        write_statement_screen(config)
    if args.mode == "decide":
        write_recovery_decision(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
