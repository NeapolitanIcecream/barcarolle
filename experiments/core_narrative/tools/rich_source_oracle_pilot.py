#!/usr/bin/env python3
"""Run one Rich source-only Golden-Oracle admission smoke pilot for a time split."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
from pathlib import Path
from typing import Any, Mapping, Sequence

from _common import ToolError, emit_json, fail, iso_now, write_json
from rich_direct_smoke_pilot import (
    DEFAULT_REPO,
    admission_decision,
    patch_for_candidate,
    problem_statement,
    repo_relative,
    run_noop_smoke,
    run_reference_smoke,
    sha256_text,
    source_anchor_digest,
    verifier_script,
)
from rich_source_oracle_queue import item_sort_key, public_source_oracle_item, triage_source_only_candidate
from rich_task_admission_readiness import changed_file_set_digest, discover_candidates


TOOL = "rich_source_oracle_pilot"
SCHEMA_VERSION = "core-narrative.rich-source-oracle-pilot.v1"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PRIVATE_ROOT = REPO_ROOT / "experiments/core_narrative/large_artifacts/rich_source_oracle_pilot_20260514"
DEFAULT_OUTPUT = REPO_ROOT / "experiments/core_narrative/results/rich_source_oracle_pilot_20260514.json"
DEFAULT_REPORT = REPO_ROOT / "experiments/core_narrative/reports/2026-05-14_rich_source_oracle_pilot.md"


def split_slug(split: str) -> str:
    return split.lower().replace("_star", "star")


KBD_INLINE_TEST = '''\
from __future__ import annotations

import io

from rich.console import Console
from rich.markdown import Markdown


def test_inline_kbd_html_renders_as_styled_inline_markdown() -> None:
    """Inline <kbd> HTML should render inline and use the markdown.kbd style."""
    stream = io.StringIO()
    console = Console(width=40, color_system="truecolor", force_terminal=True, file=stream)

    console.print(Markdown("Press <kbd>Ctrl</kbd> now."))

    output = stream.getvalue()
    assert output.startswith("Press ")
    assert "Ctrl" in output
    assert "<kbd>" not in output
    style = console.get_style("markdown.kbd")
    assert style.bold
    assert style.color is not None
'''

LAZY_EMOJI_TEST = '''\
from __future__ import annotations

import sys


def test_emoji_code_table_loads_only_after_first_lookup() -> None:
    """Importing rich.emoji should not eagerly load the emoji code table."""
    sys.modules.pop("rich._emoji_codes", None)

    import rich.emoji as emoji_module

    assert "rich._emoji_codes" not in sys.modules
    assert str(emoji_module.Emoji("smiley"))
    assert "rich._emoji_codes" in sys.modules
'''

LINK_ID_SEQUENCE_TEST = '''\
from __future__ import annotations

from rich.style import Style


def test_link_style_ids_use_adjacent_counter_prefixes() -> None:
    """Consecutive link style IDs should use adjacent counter prefixes."""
    suffix = str(hash(None))
    link_ids = [Style(link=f"https://example.com/{index}")._link_id for index in range(3)]
    prefixes = [int(link_id[: -len(suffix)]) for link_id in link_ids]

    assert prefixes[1] == prefixes[0] + 1
    assert prefixes[2] == prefixes[1] + 1
'''

PEP604_TYPING_ALIAS_SHIM = '''\
def _permit_pep604_typing_aliases() -> None:
    import typing

    def _alias_or(self, other):
        return typing.Union[self, other]

    def _alias_ror(self, other):
        return typing.Union[other, self]

    for name in ("_CallableGenericAlias", "_GenericAlias"):
        alias_type = getattr(typing, name, None)
        if alias_type is not None:
            alias_type.__or__ = _alias_or
            alias_type.__ror__ = _alias_ror


_permit_pep604_typing_aliases()
'''

PATHLIKE_ANNOTATIONS_TEST = '''\
from __future__ import annotations

import os
import typing

from rich.console import Console


def _annotation_has_str_pathlike(annotation: object) -> bool:
    if typing.get_origin(annotation) is typing.Union:
        candidates = typing.get_args(annotation)
    else:
        candidates = (annotation,)
    return any(
        typing.get_origin(candidate) is os.PathLike and typing.get_args(candidate) == (str,)
        for candidate in candidates
    )


def test_console_save_paths_use_typed_pathlike() -> None:
    """Save helpers should type PathLike with str after dropping Python 3.8."""
    for method_name in ("save_text", "save_html", "save_svg"):
        annotation = getattr(Console, method_name).__annotations__["path"]
        assert _annotation_has_str_pathlike(annotation), (method_name, annotation)
'''

SVG_HASH_REMOVED_TEST = '''\
from __future__ import annotations

import rich.console as console_module


def test_dead_svg_hash_helper_is_removed() -> None:
    """The obsolete private SVG hash helper should not remain in rich.console."""
    assert not hasattr(console_module, "_svg_hash")
'''

CURRENTFRAME_NONE_TEST = PEP604_TYPING_ALIAS_SHIM + '''\
from rich.console import Console


def test_caller_frame_info_accepts_none_currentframe() -> None:
    """Caller frame lookup should accept None and fall back to inspect.currentframe."""
    filename, line_number, locals_map = Console._caller_frame_info(0, currentframe=None)
    assert isinstance(filename, str)
    assert isinstance(line_number, int)
    assert isinstance(locals_map, dict)
'''

LAZY_PRETTY_IMPORT_TEST = PEP604_TYPING_ALIAS_SHIM + '''\
import sys

from rich.console import Console


def test_collecting_plain_text_does_not_import_pretty_module() -> None:
    """Plain text collection should not eagerly import the pretty printer."""
    sys.modules.pop("rich.pretty", None)
    console = Console()

    console._collect_renderables(["plain text"], sep=" ", end="\\n")

    assert "rich.pretty" not in sys.modules
'''

EMOJI_MAIN_LAZY_IMPORT_TEST = PEP604_TYPING_ALIAS_SHIM + '''\
import contextlib
import io
import runpy


def test_emoji_module_main_runs_after_lazy_code_table_import() -> None:
    """The rich.emoji module entrypoint should import the code table before rendering."""
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        runpy.run_module("rich.emoji", run_name="__main__")
    assert stream.getvalue()
'''

CALLER_FRAME_DOCSTRING_TEST = PEP604_TYPING_ALIAS_SHIM + '''\
from rich.console import Console


def test_caller_frame_docstring_documents_none_default() -> None:
    """The caller frame helper docstring should document the None default."""
    doc = Console._caller_frame_info.__doc__ or ""
    assert "Defaults to None" in doc
    assert "inspect.currentframe()" in doc
    assert "Defaults to ``sys._getframe``" not in doc
'''

SPLIT_GRAPHEMES_DOCSTRING_TEST = '''\
from __future__ import annotations

from rich.cells import split_graphemes


def test_split_graphemes_docstring_spells_additionally() -> None:
    """The split_graphemes docstring should spell additionally correctly."""
    doc = split_graphemes.__doc__ or ""
    assert "additionally" in doc
    assert "additonally" not in doc
'''

MARKDOWN_STALE_COMMENTS_REMOVED_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_tabledata_append_stale_commented_code_removed() -> None:
    """The obsolete commented-out TableDataElement append code should be removed."""
    source = Path("rich/markdown.py").read_text(encoding="utf-8")
    assert "# text = Text(text)" not in source
    assert "# text.stylize(context.current_style)" not in source
    assert "# self.content.append_text(text)" not in source
'''

SPLIT_LINES_TERMINATOR_TEST = '''\
from __future__ import annotations

from rich.segment import Segment


def test_split_lines_terminator_reports_trailing_newline_per_line() -> None:
    """Line splitting should report whether each yielded line ended with a newline."""
    lines = list(Segment.split_lines_terminator([Segment("alpha\\nbeta\\n"), Segment("gamma")]))

    assert [([segment.text for segment in line], add_new_line) for line, add_new_line in lines] == [
        (["alpha"], True),
        (["beta"], True),
        (["gamma"], False),
    ]
'''


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(DEFAULT_REPO), help="Local Rich checkout.")
    parser.add_argument("--split", choices=["C", "R", "W_star"], default="W_star", help="Time split to admit.")
    parser.add_argument("--private-root", default=str(DEFAULT_PRIVATE_ROOT), help="Ignored private artifact root.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Public redacted JSON output.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Public markdown report.")
    parser.add_argument("--candidate-index", type=int, default=0, help="Zero-based high-priority source-only candidate index.")
    parser.add_argument("--install-timeout-seconds", type=int, default=240)
    parser.add_argument("--verifier-timeout-seconds", type=int, default=120)
    parser.add_argument("--venv-python", default="python3")
    parser.add_argument("--force", action="store_true", default=True)
    parser.add_argument("--no-force", dest="force", action="store_false")
    return parser.parse_args(list(argv) if argv is not None else None)


def source_only_oracle_candidates(repo_path: Path, split: str = "W_star") -> list[Mapping[str, Any]]:
    candidates = [
        candidate
        for candidate in discover_candidates(repo_path)
        if candidate.get("window") == split and candidate.get("oracle_requirement") == "golden_oracle_required"
    ]
    return sorted(
        candidates,
        key=lambda candidate: item_sort_key(public_source_oracle_item(candidate, index=0)),
    )


def hidden_verifier_for_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    subject = str(candidate.get("subject", "")).strip().lower()
    source_files = set(str(path) for path in candidate.get("source_files", []))
    if subject == "support html inline" and {"rich/default_styles.py", "rich/markdown.py"}.issubset(source_files):
        return {
            "hidden_files": [
                {
                    "path": "tests/test_markdown_html_inline_kbd.py",
                    "content": KBD_INLINE_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_markdown_html_inline_kbd.py",
            "test_node_count": 1,
            "oracle_template": "markdown_inline_kbd_html",
        }
    if subject == "lazy load emoji" and {"rich/_emoji_replace.py", "rich/emoji.py"}.issubset(source_files):
        return {
            "hidden_files": [
                {
                    "path": "tests/test_emoji_lazy_import.py",
                    "content": LAZY_EMOJI_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_emoji_lazy_import.py",
            "test_node_count": 1,
            "oracle_template": "emoji_code_table_lazy_import",
        }
    if subject == "use faster generator for link ids" and "rich/style.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_style_link_id_sequence.py",
                    "content": LINK_ID_SEQUENCE_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_style_link_id_sequence.py",
            "test_node_count": 1,
            "oracle_template": "style_link_id_counter_sequence",
        }
    if subject == "made current frame none-able" and "rich/console.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_console_currentframe_none.py",
                    "content": CURRENTFRAME_NONE_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_console_currentframe_none.py",
            "test_node_count": 1,
            "oracle_template": "console_caller_frame_currentframe_none",
        }
    if subject == "lazy is_expandable" and "rich/console.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_console_lazy_pretty_import.py",
                    "content": LAZY_PRETTY_IMPORT_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_console_lazy_pretty_import.py",
            "test_node_count": 1,
            "oracle_template": "console_collect_renderables_lazy_pretty_import",
        }
    if subject == "drop 3.8" and "rich/console.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_console_pathlike_annotations.py",
                    "content": PATHLIKE_ANNOTATIONS_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_console_pathlike_annotations.py",
            "test_node_count": 1,
            "oracle_template": "console_save_pathlike_str_annotations",
        }
    if subject == "fix docstring" and "rich/console.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_console_caller_frame_docstring.py",
                    "content": CALLER_FRAME_DOCSTRING_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_console_caller_frame_docstring.py",
            "test_node_count": 1,
            "oracle_template": "console_caller_frame_docstring_none_default",
        }
    if subject == "refactor: remove dead _svg_hash function" and "rich/console.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_console_svg_hash_removed.py",
                    "content": SVG_HASH_REMOVED_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_console_svg_hash_removed.py",
            "test_node_count": 1,
            "oracle_template": "console_dead_svg_hash_removed",
        }
    if subject == "import" and "rich/emoji.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_emoji_module_main.py",
                    "content": EMOJI_MAIN_LAZY_IMPORT_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_emoji_module_main.py",
            "test_node_count": 1,
            "oracle_template": "emoji_module_main_lazy_codes_import",
        }
    if subject == "spelling" and "rich/cells.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_cells_split_graphemes_docstring.py",
                    "content": SPLIT_GRAPHEMES_DOCSTRING_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_cells_split_graphemes_docstring.py",
            "test_node_count": 1,
            "oracle_template": "cells_split_graphemes_docstring_spelling",
        }
    if subject == "remove comments" and "rich/markdown.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_markdown_stale_comments_removed.py",
                    "content": MARKDOWN_STALE_COMMENTS_REMOVED_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_markdown_stale_comments_removed.py",
            "test_node_count": 1,
            "oracle_template": "markdown_tabledata_stale_comments_removed",
        }
    if subject == "split lines terminator" and {"rich/console.py", "rich/segment.py"}.issubset(source_files):
        return {
            "hidden_files": [
                {
                    "path": "tests/test_segment_split_lines_terminator.py",
                    "content": SPLIT_LINES_TERMINATOR_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_segment_split_lines_terminator.py",
            "test_node_count": 1,
            "oracle_template": "segment_split_lines_terminator",
        }
    raise ToolError(
        "no source-oracle template is available for selected candidate",
        subject_digest=sha256_text(str(candidate.get("subject", ""))),
        source_file_set_digest=changed_file_set_digest([str(path) for path in candidate.get("source_files", [])]),
    )


def select_candidate(repo_path: Path, index: int, split: str = "W_star") -> Mapping[str, Any]:
    candidates = source_only_oracle_candidates(repo_path, split)
    if not candidates:
        raise ToolError("no Rich source-only Golden-Oracle candidates found", split=split)
    if index < 0 or index >= len(candidates):
        raise ToolError("candidate index out of range", index=index, candidate_count=len(candidates), split=split)
    return candidates[index]


def hidden_verifier_digest(verifier: Mapping[str, Any]) -> str:
    files = [
        {
            "path_digest": sha256_text(str(hidden_file["path"])),
            "content_sha256": sha256_text(str(hidden_file["content"])),
        }
        for hidden_file in verifier.get("hidden_files", [])
        if isinstance(hidden_file, Mapping)
    ]
    return sha256_text(json.dumps({"command": verifier.get("command"), "hidden_files": files}, sort_keys=True))


def materialize_task_pack(
    candidate: Mapping[str, Any],
    verifier: Mapping[str, Any],
    task_dir: Path,
    *,
    split: str = "W_star",
    task_id: str = "rich__wstar_source_oracle_pilot__001",
) -> dict[str, Any]:
    shutil.rmtree(task_dir, ignore_errors=True)
    public_dir = task_dir / "public"
    verifier_dir = task_dir / "verifier"
    public_dir.mkdir(parents=True)
    verifier_dir.mkdir(parents=True)
    (public_dir / "statement.md").write_text(
        f"# {task_id}\n\n## Problem Statement\n\n{problem_statement(str(candidate['subject']))}\n",
        encoding="utf-8",
    )
    run_path = verifier_dir / "run.sh"
    run_path.write_text(verifier_script(str(verifier["command"])), encoding="utf-8")
    run_path.chmod(run_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    hidden_files: list[str] = []
    for hidden_file in verifier.get("hidden_files", []):
        if not isinstance(hidden_file, Mapping):
            continue
        hidden_path = verifier_dir / "hidden" / str(hidden_file["path"])
        hidden_path.parent.mkdir(parents=True, exist_ok=True)
        hidden_path.write_text(str(hidden_file["content"]), encoding="utf-8")
        hidden_files.append(str(hidden_file["path"]))
    task = {
        "schema_version": "core-narrative.task.v1",
        "task_id": task_id,
        "repo_slug": "rich",
        "split": split,
        "source": {
            "kind": "commit_or_pull_request",
            "base_commit": candidate["base_commit"],
            "target_commit": candidate["commit"],
        },
        "task_family": candidate["family"],
        "task_statement_path": "public/statement.md",
        "allowed_context": {
            "include_git_history_before_base": True,
            "include_issue_text": False,
            "include_pr_text": False,
            "include_reference_patch": False,
        },
        "disallowed_context": [
            "reference patch",
            "target diff",
            "hidden verifier files",
            "target commit",
            "ACUT outputs",
            "W* results",
        ],
        "verifier": {"command": "verifier/run.sh", "timeout_seconds": 120},
        "expected": {"no_op_fails": True, "reference_passes": True},
        "leakage": {"reviewed": True, "notes": "Source-oracle pilot keeps raw source anchors in ignored private artifacts only."},
        "admission": {"status": "pilot_pending", "reviewer": "codex-rich-source-oracle-pilot"},
    }
    task_path = task_dir / "task.json"
    write_json(task_path, task)
    return {"task_id": task_id, "task_path": task_path, "hidden_files": hidden_files}


def public_result(
    *,
    candidate: Mapping[str, Any],
    verifier: Mapping[str, Any],
    reference_patch_digest: str,
    reference_patch_bytes: int,
    noop: Mapping[str, Any],
    reference: Mapping[str, Any],
    private_root: str,
    split: str = "W_star",
) -> dict[str, Any]:
    decision = admission_decision(str(noop.get("status")), str(reference.get("status")))
    triage = triage_source_only_candidate(candidate)
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "status": "completed",
        "generated_at": iso_now(),
        "model_calls_made": 0,
        "repo_slug": "rich",
        "split": split,
        "pilot_scope": "one_source_only_golden_oracle_candidate",
        "oracle_template": verifier.get("oracle_template"),
        "source_anchor_digest": source_anchor_digest(str(candidate["commit"])),
        "base_anchor_digest": source_anchor_digest(str(candidate["base_commit"])),
        "subject_digest": sha256_text(str(candidate["subject"])),
        "family": candidate["family"],
        "surface": candidate["surface"],
        "source_file_count": candidate["source_file_count"],
        "test_file_count": candidate["test_file_count"],
        "test_node_count": verifier.get("test_node_count"),
        "changed_file_set_digest": candidate.get("changed_file_set_digest")
        or changed_file_set_digest(list(candidate.get("source_files", [])) + list(candidate.get("test_files", []))),
        "statement_digest": sha256_text(problem_statement(str(candidate["subject"]))),
        "hidden_verifier_digest": hidden_verifier_digest(verifier),
        "reference_patch_digest": reference_patch_digest,
        "reference_patch_bytes": reference_patch_bytes,
        "oracle_priority": triage["oracle_priority"],
        "triage_code": triage["triage_code"],
        "no_op_result": {
            "status": noop.get("status"),
            "verifier_exit_code": noop.get("verifier_exit_code"),
            "public_artifact_redacted": True,
        },
        "reference_result": {
            "status": reference.get("status"),
            "verifier_exit_code": reference.get("verifier_exit_code"),
            "public_artifact_redacted": True,
        },
        "admission_decision": decision,
        "primary_runs_authorized": False,
        "private_artifact_root": private_root,
        "claim_boundary": [
            "This is a one-candidate source-only Golden-Oracle smoke pilot, not a frozen Rich denominator.",
            "Raw source commits, raw subjects, reference patches, and hidden verifier files are retained only in ignored private artifacts.",
            "No ACUT primary attempt or model call was made.",
        ],
    }


def render_report(payload: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Rich Source-Only Golden-Oracle Pilot",
            "",
            f"Status: `{payload.get('status')}`",
            f"Split: `{payload.get('split')}`",
            f"Generated at: `{payload.get('generated_at')}`",
            "",
            "## Result",
            "",
            f"- Admission decision: `{payload.get('admission_decision')}`",
            f"- No-op status: `{payload.get('no_op_result', {}).get('status') if isinstance(payload.get('no_op_result'), Mapping) else None}`",
            f"- Reference status: `{payload.get('reference_result', {}).get('status') if isinstance(payload.get('reference_result'), Mapping) else None}`",
            f"- Oracle template: `{payload.get('oracle_template')}`",
            f"- Family: `{payload.get('family')}`",
            f"- Test node count: `{payload.get('test_node_count')}`",
            "",
            "Primary R/W* model attempts remain unauthorized. This pilot checks one source-only Rich candidate only.",
            "",
        ]
    )


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_path = Path(args.repo).resolve()
    private_root = Path(args.private_root).resolve()
    if args.force:
        shutil.rmtree(private_root, ignore_errors=True)
    private_root.mkdir(parents=True, exist_ok=True)
    candidate = select_candidate(repo_path, args.candidate_index, args.split)
    verifier = hidden_verifier_for_candidate(candidate)
    task_pack = materialize_task_pack(
        candidate,
        verifier,
        private_root / "candidate_task_pack",
        split=args.split,
        task_id=f"rich__{split_slug(args.split)}_source_oracle_pilot__{args.candidate_index + 1:03d}",
    )
    task_path = Path(task_pack["task_path"])
    reference_patch = patch_for_candidate(repo_path, candidate)
    reference_digest = sha256_text(reference_patch)
    noop = run_noop_smoke(
        task_path,
        repo_path,
        private_root,
        args.install_timeout_seconds,
        args.verifier_timeout_seconds,
        args.venv_python,
    )
    reference = run_reference_smoke(
        task_path,
        repo_path,
        candidate,
        private_root,
        args.install_timeout_seconds,
        args.verifier_timeout_seconds,
        args.venv_python,
    )
    payload = public_result(
        candidate=candidate,
        verifier=verifier,
        reference_patch_digest=reference_digest,
        reference_patch_bytes=len(reference_patch.encode("utf-8")),
        noop=noop,
        reference=reference,
        private_root=repo_relative(private_root),
        split=args.split,
    )
    output = Path(args.output)
    report = Path(args.report)
    write_json(output, payload)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    emit_json({**payload, "output_path": repo_relative(output), "report_path": repo_relative(report)})
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except Exception as exc:
        raise SystemExit(fail(TOOL, exc))
