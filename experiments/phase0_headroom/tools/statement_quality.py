from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


OLD_BODY_SUMMARY_CAP = 240
PUBLIC_BODY_SUMMARY_LIMIT = 640
TERMINAL_PUNCTUATION = {".", "!", "?", ")"}
KNOWN_UNDERSPECIFIED_REFS = {
    "issue:766": "resolve_types_attribs_api_behavior_under_specified",
}


def normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split())


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def short_excerpt(value: str, limit: int = 180) -> str:
    text = normalize_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def sanitize_public_body_summary(value: Any, *, limit: int = PUBLIC_BODY_SUMMARY_LIMIT) -> str:
    text = normalize_text(value)
    if len(text) <= limit:
        return text
    window = text[:limit].rstrip()
    sentence_end = max(window.rfind("."), window.rfind("!"), window.rfind("?"))
    if sentence_end >= max(80, limit // 3):
        window = window[: sentence_end + 1]
    return window.rstrip()


def source_kind(source_ref: str) -> str:
    if source_ref.startswith("issue:"):
        return "issue"
    if source_ref.startswith("pr:"):
        return "pull_request"
    if source_ref.startswith("commit:"):
        return "commit"
    return "unknown"


def linked_issue_refs(text: str) -> list[str]:
    refs: list[str] = []
    for match in re.finditer(r"(?:issues/|issue\s+|fixes\s+#|fix\s+#|close[sd]?\s+#|#)(\d+)", text, flags=re.IGNORECASE):
        ref = f"issue:{match.group(1)}"
        if ref not in refs:
            refs.append(ref)
    return refs


def is_test_path(path: str) -> bool:
    return path.startswith("tests/") or path.startswith("test/") or "/tests/" in path or Path(path).name.startswith("test_")


def is_implementation_path(path: str) -> bool:
    if is_test_path(path):
        return False
    if path in {"conftest.py", "setup.py", "noxfile.py", "tox.ini", "pyproject.toml", "setup.cfg"}:
        return False
    if path.startswith("changelog.d/") or path.startswith("docs/") or path.startswith(".github/"):
        return False
    return path.endswith((".py", ".pyi"))


def implementation_files(changed_files: list[str]) -> list[str]:
    return sorted(path for path in changed_files if is_implementation_path(path))


def test_files(changed_files: list[str], explicit_test_files: list[str] | None = None) -> list[str]:
    if explicit_test_files:
        return sorted(str(path) for path in explicit_test_files)
    return sorted(path for path in changed_files if is_test_path(path))


def ends_mid_sentence(body_summary: str, *, hit_cap: bool) -> bool:
    text = body_summary.rstrip()
    if not text:
        return True
    if not hit_cap:
        return False
    if text[-1] in TERMINAL_PUNCTUATION or text.endswith("```"):
        return False
    if text[-1] in {":", ",", ";", "-", "("}:
        return True
    tail_words = re.findall(r"[A-Za-z_]+", text[-40:].lower())
    if tail_words and tail_words[-1] in {"a", "an", "the", "to", "be", "fr", "if", "or", "and"}:
        return True
    return True


def statement_quality_flags(
    *,
    source_ref: str,
    title: str,
    body_summary: str,
    implementation_files: list[str],
    test_files: list[str],
) -> dict[str, Any]:
    del test_files
    body = body_summary or ""
    hit_cap = len(body) >= OLD_BODY_SUMMARY_CAP
    mid_code_fence = body.count("```") % 2 == 1
    mid_sentence = ends_mid_sentence(body, hit_cap=hit_cap)
    nearly_empty = len(normalize_text(body)) < 20
    missing_problem_summary = not normalize_text(title) or nearly_empty
    missing_scope = not implementation_files
    pr_source = source_ref.startswith("pr:")
    pr_without_linked_issue = pr_source and not linked_issue_refs(f"{title} {body}")
    known_under_spec = KNOWN_UNDERSPECIFIED_REFS.get(source_ref)
    probably_truncated = bool(hit_cap and (mid_code_fence or mid_sentence))

    risk_reasons: list[str] = []
    if hit_cap:
        risk_reasons.append("body_summary_hit_old_240_char_cap")
    if mid_code_fence:
        risk_reasons.append("statement_ends_mid_code_fence")
    if probably_truncated:
        risk_reasons.append("statement_probably_truncated")
    if pr_source:
        risk_reasons.append("pr_context_source")
    if pr_without_linked_issue:
        risk_reasons.append("pr_context_without_linked_issue")
    if known_under_spec:
        risk_reasons.append(known_under_spec)
    if nearly_empty:
        risk_reasons.append("empty_or_nearly_empty_body_summary")
    if missing_problem_summary:
        risk_reasons.append("statement_missing_public_problem_summary")
    if missing_scope:
        risk_reasons.append("statement_missing_editable_implementation_scope")

    material_risk = bool(
        probably_truncated
        or pr_source
        or pr_without_linked_issue
        or known_under_spec
        or nearly_empty
        or missing_problem_summary
        or missing_scope
    )
    return {
        "body_summary_hit_old_cap": hit_cap,
        "body_summary_length": len(body),
        "diagnostics": {
            "failure_signal": "statement_quality_risk_detected" if material_risk else "",
            "risk_flag_count": len(risk_reasons),
        },
        "empty_or_nearly_empty_body_summary": nearly_empty,
        "pr_context_risk": pr_source,
        "pr_context_without_linked_issue": pr_without_linked_issue,
        "risk_reasons": risk_reasons,
        "statement_ends_mid_code_fence": mid_code_fence,
        "statement_ends_mid_sentence": mid_sentence,
        "statement_missing_editable_implementation_scope": missing_scope,
        "statement_missing_public_problem_summary": missing_problem_summary,
        "statement_probably_truncated": probably_truncated,
        "statement_quality_gate": "material_risk" if material_risk else "pass",
        "statement_underspecified_risk": material_risk,
    }


def statement_quality_for_context(context: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    changed_files = [str(path) for path in row.get("changed_files", [])]
    impl_files = [str(path) for path in row.get("code_files", [])] or implementation_files(changed_files)
    tests = test_files(changed_files, [str(path) for path in row.get("test_files", [])])
    return statement_quality_flags(
        source_ref=str(context.get("ref") or ""),
        title=str(context.get("summary") or row.get("subject") or ""),
        body_summary=str(context.get("body_summary") or ""),
        implementation_files=impl_files,
        test_files=tests,
    )

