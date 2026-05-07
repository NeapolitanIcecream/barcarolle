#!/usr/bin/env python3
"""Build the task-agnostic Click specialist context pack.

The pack is generated only from the locked local Click checkout and records
deterministic maps, indexes, and retrieval policy for the 2x2 Click-specialist
ACUT treatment. It does not inspect benchmark tasks, hidden verifier files,
ACUT outputs, or Git history beyond the locked checkout commit id.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from _common import ToolError, fail


TOOL = "build_click_specialist_context_pack"
PACK_ID = "click_specialist_context_pack_v1"
PACK_MARKER = "CLICK_SPECIALIST_CONTEXT_PACK_V1"
DEFAULT_CLICK_ROOT = Path("experiments/core_narrative/external_repos/click")
DEFAULT_OUTPUT_DIR = Path("experiments/core_narrative/context_packs/click_specialist")
DEFAULT_GENERATED_AT = "2026-04-30T09:25:00+08:00"
SECTION_IDS = [
    "repo_map",
    "docs_map",
    "symbol_index",
    "convention_playbook",
    "deterministic_retrieval_policy",
]
ARTIFACT_FILENAMES = {
    "repo_map": "repo_map.json",
    "docs_map": "docs_map.json",
    "symbol_index": "symbol_index.json",
    "convention_playbook": "convention_playbook.json",
    "deterministic_retrieval_policy": "retrieval_policy.json",
    "context_prompt": "context_prompt.md",
}
SOURCE_ALLOWLIST = [
    "README.md",
    "CHANGES.rst",
    "LICENSE.txt",
    "pyproject.toml",
    "src/click/*.py",
    "src/click/**/*.py",
    "src/click/py.typed",
    "docs/*.md",
    "docs/*.rst",
    "docs/**/*.md",
    "docs/**/*.rst",
    "docs/conf.py",
    "examples/*/*.py",
    "examples/**/*.py",
    "examples/**/README",
    "examples/**/pyproject.toml",
    "tests/*.py",
    "tests/**/*.py",
]
SOURCE_EXCLUDES = [
    ".git/**",
    ".github/**",
    ".devcontainer/**",
    "docs/_build/**",
    "docs/_static/**",
    "examples/**/*.jpg",
    "uv.lock",
]
FORBIDDEN_OUTPUT_PATTERNS = [
    ("full_url", re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://\S+")),
    ("ip_address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/=-]+")),
    ("resolved_secret_assignment", re.compile(r"(?i)\b(api[_-]?key|token|secret)\s*[:=]\s*['\"][^'\"]+['\"]")),
    ("benchmark_task_artifact_path", re.compile(r"experiments/core_narrative/tasks/")),
    ("hidden_verifier_path", re.compile(r"verifier/hidden|hidden/tests")),
    ("acut_output_path", re.compile(r"experiments/core_narrative/results/(raw|normalized)/pilot_")),
]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--click-root", default=str(DEFAULT_CLICK_ROOT), help="Locked local Click checkout.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Context pack output directory.")
    parser.add_argument(
        "--generated-at",
        default=DEFAULT_GENERATED_AT,
        help="Explicit task-agnostic generation timestamp recorded in the manifest.",
    )
    parser.add_argument(
        "--command-label",
        help=(
            "Reproducible command string recorded in the manifest. Defaults to "
            "the normalized command using relative experiment paths."
        ),
    )
    return parser.parse_args(list(argv))


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def stable_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def git_output(args: Sequence[str], cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ToolError("git command failed", command=["git", *args], stderr=completed.stderr.strip())
    return completed.stdout.strip()


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def iter_allowed_files(click_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in click_root.rglob("*"):
        if not path.is_file():
            continue
        relative = relpath(path, click_root)
        if matches_any(relative, SOURCE_EXCLUDES):
            continue
        if matches_any(relative, SOURCE_ALLOWLIST):
            files.append(path)
    return sorted(files, key=lambda item: relpath(item, click_root))


def line_count(path: Path) -> int:
    text = read_text(path)
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def module_name_for(path: Path, click_root: Path) -> str | None:
    relative = relpath(path, click_root)
    if not relative.endswith(".py"):
        return None
    if relative.startswith("src/"):
        module = relative.removeprefix("src/").removesuffix(".py").replace("/", ".")
        return module.removesuffix(".__init__")
    if relative.startswith("tests/"):
        return relative.removesuffix(".py").replace("/", ".")
    if relative.startswith("examples/"):
        return relative.removesuffix(".py").replace("/", ".")
    return None


def ast_tree(path: Path) -> ast.AST | None:
    try:
        return ast.parse(read_text(path), filename=str(path))
    except SyntaxError:
        return None


def simple_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = simple_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return simple_name(node.func)
    if isinstance(node, ast.Subscript):
        return simple_name(node.value)
    return ""


def local_imports(tree: ast.AST | None) -> list[str]:
    if tree is None:
        return []
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if node.level or module.startswith("click"):
                prefix = "." * int(node.level) + module
                imports.add(prefix or ".")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("click"):
                    imports.add(alias.name)
    return sorted(imports)


def public_api_exports(tree: ast.AST | None) -> list[str]:
    if tree is None:
        return []
    exports: set[str] = set()
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            for alias in node.names:
                name = alias.asname or alias.name
                if not name.startswith("_"):
                    exports.add(name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    exports.add(target.id)
    return sorted(exports)


def function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args: list[str] = []
    for arg in list(node.args.posonlyargs) + list(node.args.args):
        args.append(arg.arg)
    if node.args.vararg is not None:
        args.append(f"*{node.args.vararg.arg}")
    elif node.args.kwonlyargs:
        args.append("*")
    for arg in node.args.kwonlyargs:
        args.append(arg.arg)
    if node.args.kwarg is not None:
        args.append(f"**{node.args.kwarg.arg}")
    return f"{node.name}({', '.join(args)})"


def decorators(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> list[str]:
    values = [simple_name(item) for item in node.decorator_list]
    return sorted(value for value in values if value)


def symbols_for_file(path: Path, click_root: Path) -> list[dict[str, Any]]:
    tree = ast_tree(path)
    if tree is None:
        return []
    module = module_name_for(path, click_root)
    if module is None:
        return []

    symbols: list[dict[str, Any]] = []
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.ClassDef):
            class_name = f"{module}.{node.name}"
            symbols.append(
                {
                    "kind": "class",
                    "name": node.name,
                    "qualified_name": class_name,
                    "module": module,
                    "path": relpath(path, click_root),
                    "line": node.lineno,
                    "decorators": decorators(node),
                }
            )
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(
                        {
                            "kind": "method",
                            "name": child.name,
                            "qualified_name": f"{class_name}.{child.name}",
                            "module": module,
                            "path": relpath(path, click_root),
                            "line": child.lineno,
                            "signature": function_signature(child),
                            "decorators": decorators(child),
                        }
                    )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                {
                    "kind": "function",
                    "name": node.name,
                    "qualified_name": f"{module}.{node.name}",
                    "module": module,
                    "path": relpath(path, click_root),
                    "line": node.lineno,
                    "signature": function_signature(node),
                    "decorators": decorators(node),
                }
            )
    return symbols


def extract_md_headings(text: str) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            headings.append(match.group(2).strip())
    return headings


def extract_rst_headings(text: str) -> list[str]:
    lines = text.splitlines()
    headings: list[str] = []
    underline_chars = set("=-~^\"'")
    for index in range(len(lines) - 1):
        title = lines[index].strip()
        underline = lines[index + 1].strip()
        if not title or not underline:
            continue
        if len(underline) >= len(title) and len(set(underline)) == 1 and underline[0] in underline_chars:
            headings.append(title)
    return headings


def extract_headings(path: Path) -> list[str]:
    text = read_text(path)
    if path.suffix.lower() == ".md":
        headings = extract_md_headings(text)
    else:
        headings = extract_rst_headings(text)
    return headings[:24]


def source_input_digest(files: Sequence[Path], click_root: Path) -> str:
    chunks: list[str] = []
    for path in files:
        chunks.append(f"{relpath(path, click_root)}\0{sha256_file(path)}")
    return sha256_text("\n".join(chunks) + "\n")


def build_repo_map(files: Sequence[Path], click_root: Path, commit: str) -> dict[str, Any]:
    python_files = [path for path in files if path.suffix == ".py"]
    source_files = [path for path in python_files if relpath(path, click_root).startswith("src/click/")]
    test_files = [path for path in python_files if relpath(path, click_root).startswith("tests/")]
    example_files = [path for path in python_files if relpath(path, click_root).startswith("examples/")]
    docs_files = [
        path
        for path in files
        if relpath(path, click_root).startswith("docs/") and path.suffix.lower() in {".md", ".rst"}
    ]
    init_tree = ast_tree(click_root / "src" / "click" / "__init__.py")

    modules = []
    for path in source_files:
        tree = ast_tree(path)
        symbols = symbols_for_file(path, click_root)
        modules.append(
            {
                "path": relpath(path, click_root),
                "module": module_name_for(path, click_root),
                "line_count": line_count(path),
                "class_count": sum(1 for item in symbols if item["kind"] == "class"),
                "function_count": sum(1 for item in symbols if item["kind"] == "function"),
                "method_count": sum(1 for item in symbols if item["kind"] == "method"),
                "local_imports": local_imports(tree),
            }
        )

    return {
        "pack_id": PACK_ID,
        "marker": PACK_MARKER,
        "section_id": "repo_map",
        "locked_click_commit": commit,
        "source_root_label": DEFAULT_CLICK_ROOT.as_posix(),
        "history_mining": "not_used",
        "file_counts": {
            "allowlisted_total": len(files),
            "source_python": len(source_files),
            "public_test_python": len(test_files),
            "example_python": len(example_files),
            "docs_pages": len(docs_files),
        },
        "package_layout": {
            "source_root": "src/click",
            "tests_root": "tests",
            "docs_root": "docs",
            "examples_root": "examples",
        },
        "core_modules": modules,
        "public_api_exports_from_click_init": public_api_exports(init_tree),
        "public_test_files": [relpath(path, click_root) for path in test_files],
        "example_entrypoints": [relpath(path, click_root) for path in example_files],
    }


def build_docs_map(files: Sequence[Path], click_root: Path) -> dict[str, Any]:
    docs_paths = [
        path
        for path in files
        if (
            relpath(path, click_root).startswith("docs/")
            or relpath(path, click_root) == "README.md"
            or relpath(path, click_root).startswith("examples/")
        )
        and (path.suffix.lower() in {".md", ".rst"} or path.name == "README")
    ]
    docs = []
    for path in docs_paths:
        headings = extract_headings(path)
        docs.append(
            {
                "path": relpath(path, click_root),
                "title": headings[0] if headings else path.stem,
                "heading_count": len(headings),
                "headings": headings,
            }
        )
    return {
        "pack_id": PACK_ID,
        "marker": PACK_MARKER,
        "section_id": "docs_map",
        "heading_extraction": "markdown_hash_headings_and_rst_underlined_titles_only",
        "docs": docs,
    }


def build_symbol_index(files: Sequence[Path], click_root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for path in files:
        if path.suffix != ".py":
            continue
        relative = relpath(path, click_root)
        if not (
            relative.startswith("src/click/")
            or relative.startswith("tests/")
            or relative.startswith("examples/")
        ):
            continue
        entries.extend(symbols_for_file(path, click_root))
    entries.sort(key=lambda item: (item["path"], item["line"], item["qualified_name"]))
    return {
        "pack_id": PACK_ID,
        "marker": PACK_MARKER,
        "section_id": "symbol_index",
        "symbol_count": len(entries),
        "entries": entries,
    }


def regex_count(files: Sequence[Path], pattern: str) -> int:
    compiled = re.compile(pattern)
    count = 0
    for path in files:
        if path.suffix != ".py":
            continue
        count += len(compiled.findall(read_text(path)))
    return count


def pyproject_value(pyproject: str, key: str) -> str | None:
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=\s*\"([^\"]+)\"", pyproject)
    return match.group(1) if match else None


def build_convention_playbook(files: Sequence[Path], click_root: Path) -> dict[str, Any]:
    pyproject = read_text(click_root / "pyproject.toml")
    source_files = [path for path in files if relpath(path, click_root).startswith("src/click/") and path.suffix == ".py"]
    test_files = [path for path in files if relpath(path, click_root).startswith("tests/") and path.suffix == ".py"]
    private_modules = [relpath(path, click_root) for path in source_files if Path(path).name.startswith("_")]
    public_modules = [relpath(path, click_root) for path in source_files if not Path(path).name.startswith("_")]
    return {
        "pack_id": PACK_ID,
        "marker": PACK_MARKER,
        "section_id": "convention_playbook",
        "observed_project_config": {
            "requires_python": pyproject_value(pyproject, "requires-python"),
            "testpaths_declared": "testpaths = [\"tests\"]" in pyproject,
            "warnings_as_errors_declared": "error" in pyproject and "filterwarnings" in pyproject,
        },
        "observed_code_shape": {
            "public_source_modules": public_modules,
            "private_support_modules": private_modules,
            "public_api_export_file": "src/click/__init__.py",
        },
        "observed_test_conventions": {
            "pytest_import_count": regex_count(test_files, r"\bimport pytest\b"),
            "cli_runner_reference_count": regex_count(test_files, r"\bCliRunner\b"),
            "isolated_filesystem_reference_count": regex_count(test_files, r"\bisolated_filesystem\b"),
            "result_exit_code_assertions": regex_count(test_files, r"\bexit_code\b"),
        },
        "playbook": [
            {
                "id": "patch_public_api_carefully",
                "guidance": "When changing public behavior, check exports in src/click/__init__.py and behavior tests in tests/test_*.py.",
                "evidence_paths": ["src/click/__init__.py", "tests"],
            },
            {
                "id": "use_cli_runner_for_cli_behavior",
                "guidance": "CLI behavior is commonly exercised through click.testing.CliRunner and result exit/output assertions.",
                "evidence_paths": ["src/click/testing.py", "tests/test_testing.py", "tests/test_options.py"],
            },
            {
                "id": "keep_parser_option_type_boundaries",
                "guidance": "Parser, option, argument, type, formatting, terminal UI, and shell-completion behavior live in separate modules with matching public tests.",
                "evidence_paths": [
                    "src/click/parser.py",
                    "src/click/core.py",
                    "src/click/types.py",
                    "src/click/formatting.py",
                    "src/click/termui.py",
                    "src/click/shell_completion.py",
                ],
            },
            {
                "id": "prefer_focused_pytest",
                "guidance": "Use focused pytest module or test-name selection first; broaden only when the changed surface crosses modules.",
                "evidence_paths": ["pyproject.toml", "tests"],
            },
            {
                "id": "docs_follow_behavior",
                "guidance": "When user-facing command semantics change, inspect the matching docs page heading map before editing docs.",
                "evidence_paths": ["docs", "README.md"],
            },
        ],
    }


def build_retrieval_policy() -> dict[str, Any]:
    return {
        "pack_id": PACK_ID,
        "marker": PACK_MARKER,
        "section_id": "deterministic_retrieval_policy",
        "policy_id": "deterministic_click_retrieval_v1",
        "task_agnostic": True,
        "history_mining": "not_used",
        "selection_order": [
            "Read the public task statement and named files.",
            "Map mentioned symbols or failing imports to symbol_index exact names.",
            "Inspect repo_map for the owning Click module and adjacent public tests.",
            "Use docs_map headings only when behavior is public or documented.",
            "Apply convention_playbook guidance for verification scope and public API boundaries.",
        ],
        "allowed_sources": [
            "public_task_statement",
            "files explicitly named in the task statement",
            "files surfaced by failing tests or import errors",
            "adjacent public tests",
            "direct symbol and filename search results",
            "this precomputed task-agnostic Click context pack",
        ],
        "forbidden_material_policy": {
            "benchmark_solution_patches_content_present": False,
            "hidden_verifier_files_present": False,
            "hidden_human_hints_present": False,
            "acut_outputs_or_failed_generated_patches_present": False,
            "task_specific_private_artifacts_present": False,
            "network_fetched_docs_present": False,
        },
        "prompt_use": {
            "inject_for_acut_specializations": ["frontier-click-specialist", "cheap-click-specialist"],
            "do_not_inject_for_acut_specializations": ["frontier-generic-swe", "cheap-generic-swe"],
            "must_not_change_model_tier_or_runtime_budget": True,
        },
    }


def compact_list(values: Sequence[str], limit: int) -> str:
    visible = list(values[:limit])
    suffix = "" if len(values) <= limit else f"; +{len(values) - limit} more"
    return ", ".join(visible) + suffix


def public_symbol_names(symbol_index: Mapping[str, Any]) -> list[str]:
    names: list[str] = []
    for entry in symbol_index.get("entries", []):
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        name = entry.get("qualified_name")
        if not isinstance(path, str) or not isinstance(name, str):
            continue
        if not path.startswith("src/click/"):
            continue
        leaf = str(entry.get("name", ""))
        if leaf.startswith("_"):
            continue
        names.append(name)
    return sorted(dict.fromkeys(names))


def render_context_prompt(
    *,
    repo_map: Mapping[str, Any],
    docs_map: Mapping[str, Any],
    symbol_index: Mapping[str, Any],
    convention_playbook: Mapping[str, Any],
    retrieval_policy: Mapping[str, Any],
    pack_hash: str,
) -> str:
    modules = [
        item["path"]
        for item in repo_map.get("core_modules", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]
    docs = [
        item["path"]
        for item in docs_map.get("docs", [])
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    ]
    playbook_items = [
        item
        for item in convention_playbook.get("playbook", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    ]
    retrieval_steps = [
        item
        for item in retrieval_policy.get("selection_order", [])
        if isinstance(item, str)
    ]
    symbols = public_symbol_names(symbol_index)
    exports = repo_map.get("public_api_exports_from_click_init", [])
    export_names = [item for item in exports if isinstance(item, str)]

    lines = [
        f"<!-- {PACK_MARKER} -->",
        "# Click Specialist Context Pack",
        "",
        f"Pack ID: {PACK_ID}",
        f"Pack hash: sha256:{pack_hash}",
        f"Marker: {PACK_MARKER}",
        "Source: locked local Click checkout public source, docs, tests, and examples only.",
        "Task scope: task-agnostic; generated before any Click-specialist ACUT execution.",
        "Leakage guard: no benchmark solution patch content, hidden verifier files, hidden hints, ACUT outputs, network-fetched docs, credentials, endpoint values, full URLs, hostnames, or IP addresses.",
        "",
        "[CLICK_SECTION:repo_map]",
        f"Locked Click commit: {repo_map.get('locked_click_commit')}",
        f"Layout roots: {repo_map.get('package_layout', {}).get('source_root')}, {repo_map.get('package_layout', {}).get('tests_root')}, {repo_map.get('package_layout', {}).get('docs_root')}, {repo_map.get('package_layout', {}).get('examples_root')}.",
        f"Core modules: {compact_list(modules, 18)}.",
        f"Public exports from click.__init__: {compact_list(export_names, 40)}.",
        "",
        "[CLICK_SECTION:docs_map]",
        f"Docs/examples mapped by headings only: {compact_list(docs, 28)}.",
        "",
        "[CLICK_SECTION:symbol_index]",
        f"Indexed symbols: {symbol_index.get('symbol_count')} total across source, public tests, and examples.",
        f"Public source symbol examples: {compact_list(symbols, 42)}.",
        "",
        "[CLICK_SECTION:convention_playbook]",
    ]
    for item in playbook_items:
        lines.append(f"- {item['id']}: {item.get('guidance')}")
    lines.extend(
        [
            "",
            "[CLICK_SECTION:deterministic_retrieval_policy]",
        ]
    )
    for index, step in enumerate(retrieval_steps, start=1):
        lines.append(f"{index}. {step}")
    lines.extend(
        [
            "Apply this context only for frontier-click-specialist and cheap-click-specialist.",
            "Do not use this context for generic SWE ACUTs.",
            "",
        ]
    )
    return "\n".join(lines)


def assert_no_forbidden_output(path: Path) -> list[dict[str, Any]]:
    text = read_text(path)
    findings = []
    for reason, pattern in FORBIDDEN_OUTPUT_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            findings.append({"path": str(path), "reason": reason, "count": len(matches)})
    return findings


def write_artifact(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(payload), encoding="utf-8")


def artifact_record(path: Path, output_dir: Path) -> dict[str, Any]:
    return {
        "path": relpath(path, output_dir),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def reproducible_command(args: argparse.Namespace) -> str:
    if args.command_label:
        return args.command_label
    return (
        "python3 experiments/core_narrative/tools/build_click_specialist_context_pack.py "
        "--click-root experiments/core_narrative/external_repos/click "
        "--output-dir experiments/core_narrative/context_packs/click_specialist "
        f"--generated-at {args.generated_at}"
    )


def run(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    click_root = Path(args.click_root).resolve()
    output_dir = Path(args.output_dir)
    if not click_root.exists():
        raise ToolError("locked Click checkout does not exist", click_root=str(click_root))
    if not (click_root / "src" / "click").exists():
        raise ToolError("locked Click checkout has unexpected shape", click_root=str(click_root))
    commit = git_output(["rev-parse", "HEAD"], click_root)
    status = git_output(["status", "--porcelain"], click_root)
    if status:
        raise ToolError("locked Click checkout must be clean before context generation")

    files = iter_allowed_files(click_root)
    if not files:
        raise ToolError("source allowlist did not match any files", click_root=str(click_root))
    digest = source_input_digest(files, click_root)

    repo_map = build_repo_map(files, click_root, commit)
    docs_map = build_docs_map(files, click_root)
    symbol_index = build_symbol_index(files, click_root)
    convention_playbook = build_convention_playbook(files, click_root)
    retrieval_policy = build_retrieval_policy()

    output_dir.mkdir(parents=True, exist_ok=True)
    data_artifacts = {
        "repo_map": repo_map,
        "docs_map": docs_map,
        "symbol_index": symbol_index,
        "convention_playbook": convention_playbook,
        "deterministic_retrieval_policy": retrieval_policy,
    }
    for section_id, payload in data_artifacts.items():
        write_artifact(output_dir / ARTIFACT_FILENAMES[section_id], payload)

    data_hash_records = [
        artifact_record(output_dir / ARTIFACT_FILENAMES[section_id], output_dir)
        for section_id in SECTION_IDS
    ]
    pack_hash = sha256_text(stable_json({"pack_id": PACK_ID, "artifacts": data_hash_records}))
    context_prompt = render_context_prompt(
        repo_map=repo_map,
        docs_map=docs_map,
        symbol_index=symbol_index,
        convention_playbook=convention_playbook,
        retrieval_policy=retrieval_policy,
        pack_hash=pack_hash,
    )
    (output_dir / ARTIFACT_FILENAMES["context_prompt"]).write_text(context_prompt, encoding="utf-8")

    artifact_hashes = {
        section_id: artifact_record(output_dir / filename, output_dir)
        for section_id, filename in ARTIFACT_FILENAMES.items()
    }
    manifest = {
        "pack_id": PACK_ID,
        "marker": PACK_MARKER,
        "pack_hash": pack_hash,
        "schema_version": "core-narrative.click-specialist-context-pack.v1",
        "generated_at": args.generated_at,
        "generation_timing": {
            "task_agnostic": True,
            "relative_to_specialist_acut_execution": "before any frontier-click-specialist or cheap-click-specialist ACUT execution",
            "uses_observed_acut_outputs": False,
        },
        "generator": {
            "tool": TOOL,
            "command": reproducible_command(args),
            "history_mining": "not_used",
        },
        "locked_click_commit": commit,
        "source_root_label": DEFAULT_CLICK_ROOT.as_posix(),
        "source_allowlist": SOURCE_ALLOWLIST,
        "source_excludes": SOURCE_EXCLUDES,
        "source_file_count": len(files),
        "source_input_digest": digest,
        "source_material_policy": {
            "public_committed_source_docs_tests_examples_only": True,
            "network_fetched_docs_used": False,
            "rbench_rwork_gold_patches_used": False,
            "hidden_verifier_tests_used": False,
            "hidden_human_hints_used": False,
            "acut_outputs_or_failed_patches_used": False,
            "git_history_mining_used": False,
        },
        "section_ids": SECTION_IDS,
        "artifacts": artifact_hashes,
        "leakage_guards": {
            "credential_values_recorded": False,
            "bearer_tokens_recorded": False,
            "resolved_secrets_recorded": False,
            "full_base_url_values_recorded": False,
            "resolved_endpoint_values_recorded": False,
            "hostnames_recorded": False,
            "ip_addresses_recorded": False,
            "full_urls_recorded": False,
            "hidden_verifier_paths_recorded": False,
            "benchmark_solution_patch_content_recorded": False,
            "post_hoc_pilot_artifacts_recorded": False,
        },
    }
    manifest_path = output_dir / "manifest.json"
    write_artifact(manifest_path, manifest)

    findings: list[dict[str, Any]] = []
    for path in sorted(output_dir.glob("*")):
        if path.is_file():
            findings.extend(assert_no_forbidden_output(path))
    if findings:
        raise ToolError("generated context pack failed leakage guard", findings=findings)

    summary = {
        "tool": TOOL,
        "status": "generated",
        "pack_id": PACK_ID,
        "marker": PACK_MARKER,
        "pack_hash": pack_hash,
        "locked_click_commit": commit,
        "output_dir": str(output_dir),
        "manifest_path": str(manifest_path),
        "section_ids": SECTION_IDS,
        "artifact_hashes": artifact_hashes,
        "source_file_count": len(files),
        "source_input_digest": digest,
        "model_call_made": False,
        "leakage_guard_findings": [],
    }
    print(stable_json(summary), end="")
    return 0


def main() -> int:
    try:
        return run(sys.argv[1:])
    except Exception as exc:
        return fail(TOOL, exc)


if __name__ == "__main__":
    sys.exit(main())
