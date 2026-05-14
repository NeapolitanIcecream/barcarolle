#!/usr/bin/env python3
"""Generate source-only localization hints for repository-local ACUTs."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Sequence

from _common import emit_json, fail, iso_now, write_json


TOOL = "repository_localization_hints"
SCHEMA_VERSION = "core-narrative.repository-localization-hints.v1"
STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "be",
    "by",
    "fix",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "with",
}
DIFF_MARKERS = ("diff --git", "\n@@", "\n--- a/", "\n+++ b/", "\nindex ")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Repository source tree.")
    parser.add_argument("--statement", required=True, help="Public task statement path.")
    parser.add_argument("--output", help="Optional JSON output path.")
    parser.add_argument("--max-files", type=int, default=5)
    parser.add_argument("--max-symbols", type=int, default=10)
    return parser.parse_args(list(argv) if argv is not None else None)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def forbidden_statement_findings(text: str) -> list[str]:
    lowered = text.lower()
    findings: list[str] = []
    if any(marker in text for marker in DIFF_MARKERS):
        findings.append("implementation_diff")
    if re.search(r"\b[0-9a-f]{40}\b", text):
        findings.append("target_commit_or_sha")
    if "target_commit" in lowered or "target commit" in lowered:
        findings.append("target_commit")
    if "reference patch" in lowered or "reference_patch" in lowered or "patch_sha256" in lowered:
        findings.append("reference_patch")
    if "hidden verifier" in lowered or "verifier/hidden" in lowered or "hidden/tests" in lowered:
        findings.append("hidden_verifier")
    return sorted(set(findings))


def keywords(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", text.lower())
    ordered: list[str] = []
    for word in words:
        if word in STOPWORDS or word in ordered:
            continue
        ordered.append(word)
    return ordered


def python_files(repo: Path) -> list[Path]:
    ignored = {".git", ".venv", "venv", "__pycache__", ".tox", ".nox", "build", "dist"}
    files: list[Path] = []
    for path in repo.rglob("*.py"):
        if any(part in ignored for part in path.relative_to(repo).parts):
            continue
        files.append(path)
    return sorted(files)


def symbol_names(path: Path, repo: Path, content: str) -> list[dict[str, Any]]:
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    symbols: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                {
                    "symbol": node.name,
                    "path": path.relative_to(repo).as_posix(),
                    "line": getattr(node, "lineno", None),
                    "kind": type(node).__name__.replace("Def", "").lower(),
                }
            )
    class_by_line = {item["line"]: item["symbol"] for item in symbols if item["kind"] == "class"}
    for item in symbols:
        if item["kind"] == "function":
            parent = max((line for line in class_by_line if line and item["line"] and line < item["line"]), default=None)
            if parent is not None:
                item["symbol"] = f"{class_by_line[parent]}.{item['symbol']}"
    return symbols


def score_file(relative_path: str, content: str, terms: Sequence[str]) -> int:
    haystack = f"{relative_path.lower()}\n{content.lower()}"
    score = 0
    for term in terms:
        if term in relative_path.lower():
            score += 8
        score += min(haystack.count(term), 8)
    return score


def localize(repo: Path, statement_path: Path, *, max_files: int = 5, max_symbols: int = 10) -> dict[str, Any]:
    statement = statement_path.read_text(encoding="utf-8")
    findings = forbidden_statement_findings(statement)
    base_payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "generated_at": iso_now(),
        "statement_digest": sha256_text(statement),
        "policy": {
            "source_material": "public_statement_and_repo_source_only",
            "uses_reference_patch": False,
            "uses_target_diff": False,
            "uses_hidden_verifier": False,
            "uses_target_commit": False,
        },
    }
    if findings:
        return {**base_payload, "status": "blocked_forbidden_public_statement", "forbidden_findings": findings, "files": [], "symbols": []}

    terms = keywords(statement)
    scored_files: list[dict[str, Any]] = []
    scored_symbols: list[dict[str, Any]] = []
    for path in python_files(repo):
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(repo).as_posix()
        score = score_file(relative, content, terms)
        if score <= 0:
            continue
        scored_files.append({"path": relative, "score": score})
        for symbol in symbol_names(path, repo, content):
            symbol_score = score_file(f"{relative}\n{symbol['symbol']}", content[:2000], terms)
            if symbol_score > 0:
                scored_symbols.append({**symbol, "score": symbol_score})

    scored_files.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    scored_symbols.sort(key=lambda item: (-int(item["score"]), str(item["path"]), str(item["symbol"])))
    return {
        **base_payload,
        "status": "completed",
        "keywords_digest": sha256_text("\n".join(terms)),
        "file_count_scanned": len(python_files(repo)),
        "files": scored_files[:max_files],
        "symbols": scored_symbols[:max_symbols],
    }


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    payload = localize(Path(args.repo), Path(args.statement), max_files=args.max_files, max_symbols=args.max_symbols)
    emit_json(payload, args.output)
    return 0 if payload["status"] == "completed" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(run(sys.argv[1:]))
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
