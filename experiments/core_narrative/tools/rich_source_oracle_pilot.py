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

CACHED_CELL_LEN_UNICODE_VERSION_TEST = '''\
from __future__ import annotations

from rich.cells import cached_cell_len


def test_cached_cell_len_accepts_unicode_version_for_short_text() -> None:
    """The short-text cache should include unicode_version in its key."""
    cached_cell_len.cache_clear()

    assert cached_cell_len("abc", "auto") == 3
    assert cached_cell_len("abc", "latest") == 3
    assert cached_cell_len.cache_info().misses == 2
'''

TRACEBACK_LOCALS_OPTIONS_TEST = '''\
from __future__ import annotations

from rich.traceback import Traceback


def test_traceback_from_exception_accepts_locals_depth_and_overflow() -> None:
    """Traceback construction should expose locals depth and overflow controls."""
    traceback = Traceback.from_exception(
        ValueError,
        ValueError("boom"),
        None,
        show_locals=True,
        locals_max_depth=1,
        locals_overflow="ellipsis",
    )

    assert traceback.locals_max_depth == 1
    assert traceback.locals_overflow == "ellipsis"
'''

PROGRESS_DISABLE_NO_BLANK_LINE_TEST = '''\
from __future__ import annotations

import io

from rich.console import Console
from rich.progress import Progress


def test_disabled_progress_stop_does_not_write_blank_line() -> None:
    """Stopping disabled progress should not write an extra blank line."""
    stream = io.StringIO()
    console = Console(file=stream, force_terminal=False)
    progress = Progress(console=console, disable=True)

    progress.start()
    progress.stop()

    assert stream.getvalue() == ""
'''

UNICODE_CACHE_PY38_FALLBACK_TEST = '''\
from __future__ import annotations

import builtins
import functools
import types
from pathlib import Path


def test_unicode_data_cache_import_falls_back_to_lru_cache() -> None:
    """Unicode data import should tolerate Python 3.8 without functools.cache."""
    source = Path("rich/_unicode_data/__init__.py").read_text(encoding="utf-8")
    original_import = builtins.__import__
    fake_functools = types.ModuleType("functools")
    fake_functools.lru_cache = functools.lru_cache

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "functools" and level == 0:
            return fake_functools
        return original_import(name, globals, locals, fromlist, level)

    namespace = {"__name__": "rich._unicode_data_fallback_probe", "__package__": "rich._unicode_data"}
    builtins.__import__ = fake_import
    try:
        exec(compile(source, "rich/_unicode_data/__init__.py", "exec"), namespace)
    finally:
        builtins.__import__ = original_import

    assert namespace["cache"] is functools.lru_cache
'''

UNICODE_LOAD_LATEST_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_unicode_data_package_adds_latest_table_loader() -> None:
    """Unicode data should expose loader source for the latest generated table."""
    source = Path("rich/_unicode_data/__init__.py").read_text(encoding="utf-8")
    versions = Path("rich/_unicode_data/_versions.py").read_text(encoding="utf-8")

    assert "from rich._unicode_data._versions import VERSIONS" in source
    assert 'module_name = f".unicode{version_path_component}"' in source
    assert 'if unicode_version == "latest":' in source
    assert '"17.0.0"' in versions
'''

UNICODE_INVALID_VERSION_FALLBACK_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_invalid_unicode_version_source_falls_back_to_latest_table() -> None:
    """Unicode loader source should catch invalid versions and fall back to latest."""
    source = Path("rich/_unicode_data/__init__.py").read_text(encoding="utf-8")

    assert "except ValueError:\\n            version_numbers = _parse_version(VERSIONS[-1])" in source
    assert "if version not in VERSION_SET:" in source
    assert "if TYPE_CHECKING:\\n        assert isinstance(module.cell_table, CellTable)" in source
'''

CELL_STRING_BASIC_API_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_cell_string_exposes_basic_string_like_behavior() -> None:
    """CellString should expose text, truthiness, iteration, and cached cell length."""
    source = Path("rich/cell_string.py").read_text(encoding="utf-8")
    namespace = {"__name__": "rich_cell_string_probe"}
    exec(compile("from __future__ import annotations\\n" + source, "rich/cell_string.py", "exec"), namespace)
    CellString = namespace["CellString"]

    value = CellString("abc")

    assert value.text == "abc"
    assert value.cell_length == 3
    assert list(value) == ["a", "b", "c"]
    assert bool(value)
'''

CELL_TABLE_API_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_cell_table_records_unicode_width_metadata() -> None:
    """CellTable should carry unicode table metadata and hash by version."""
    source = Path("rich/cell_string.py").read_text(encoding="utf-8")
    namespace = {"__name__": "rich_cell_table_probe"}
    exec(compile("from __future__ import annotations\\n" + source, "rich/cell_string.py", "exec"), namespace)
    CellTable = namespace["CellTable"]

    table = CellTable("probe", ((65, 65, 1),), frozenset({9731}))

    assert table.unicode_version == "probe"
    assert table.widths == ((65, 65, 1),)
    assert 9731 in table.narrow_to_wide
'''

CELL_STRING_SPLIT_TEXT_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_split_text_source_adds_cell_offset_splitting() -> None:
    """Cell string source should add public split_text and its fast path."""
    source = Path("rich/cell_string.py").read_text(encoding="utf-8")

    assert "def split_text(" in source
    assert "def _split_text(" in source
    assert "return text[:cell_position], text[cell_position:]" in source
    assert "return _split_text(text, cell_position, unicode_version)" in source
'''

PRETTY_IPYTHON_CUSTOM_CONSOLE_TEST = '''\
from __future__ import annotations

import builtins
import io
import sys
import types

from rich.console import Console
import rich.pretty as pretty


def test_ipython_formatter_uses_installed_custom_console() -> None:
    """IPython pretty formatting should preserve the console passed to install()."""
    captured = {}

    class BaseFormatter:
        pass

    formatters_module = types.ModuleType("IPython.core.formatters")
    formatters_module.BaseFormatter = BaseFormatter
    core_module = types.ModuleType("IPython.core")
    ipython_module = types.ModuleType("IPython")
    saved_modules = {name: sys.modules.get(name) for name in ("IPython", "IPython.core", "IPython.core.formatters")}
    sys.modules["IPython"] = ipython_module
    sys.modules["IPython.core"] = core_module
    sys.modules["IPython.core.formatters"] = formatters_module

    class FakeDisplayFormatter:
        def __init__(self) -> None:
            self.formatters = {"text/plain": None}

    class FakeIPython:
        def __init__(self) -> None:
            self.display_formatter = FakeDisplayFormatter()

    fake_ipython = FakeIPython()
    original_get_ipython = getattr(builtins, "get_ipython", None)
    original_hook = pretty._ipy_display_hook

    def fake_display_hook(value, **kwargs):
        captured["value"] = value
        captured.update(kwargs)
        return "formatted"

    builtins.get_ipython = lambda: fake_ipython
    pretty._ipy_display_hook = fake_display_hook
    custom_console = Console(file=io.StringIO())
    try:
        pretty.install(console=custom_console)
        result = fake_ipython.display_formatter.formatters["text/plain"]("value")
    finally:
        pretty._ipy_display_hook = original_hook
        if original_get_ipython is None:
            delattr(builtins, "get_ipython")
        else:
            builtins.get_ipython = original_get_ipython
        for name, module in saved_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    assert result == "formatted"
    assert captured["value"] == "value"
    assert captured["console"] is custom_console
'''

PROGRESS_RESET_DOCSTRING_TEST = '''\
from __future__ import annotations

from rich.progress import Progress


def test_progress_reset_docstring_describes_visible_none_semantics() -> None:
    """Progress.reset should document visible=None semantics."""
    doc = Progress.reset.__doc__ or ""

    assert "Set visible flag if not None." in doc
    assert "Enable display of the task. Defaults to True." not in doc
'''

CELLS_VARIATION_SELECTOR_SIMPLIFIED_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_cell_len_variation_selector_branch_is_simplified() -> None:
    """Cell width source should simplify the variation-selector branch."""
    source = Path("rich/cells.py").read_text(encoding="utf-8")

    assert 'elif character == "\\\\ufe0f" and last_measured_character:' not in source
    assert 'elif last_measured_character:' in source
'''

CELLS_BINARY_SEARCH_UNPACK_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_cell_width_binary_search_unpacks_table_entries() -> None:
    """Cell width lookup should unpack start, end, and width directly."""
    source = Path("rich/cells.py").read_text(encoding="utf-8")

    assert "start, end, width = table[index]" in source
    assert "entry = table[index]" not in source
    assert "return entry[2]" not in source
'''

UNICODE_FALLBACK_COMMENT_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_unicode_data_invalid_environment_comment_is_complete() -> None:
    """Unicode data source should keep the invalid-env fallback comment complete."""
    source = Path("rich/_unicode_data/__init__.py").read_text(encoding="utf-8")

    assert "Fallback to using the latest version seems reasonable" in source
    assert "Fallback to using the latest version seems s" not in source
'''

UNICODE_CELL_TABLE_TYPE_IMPORT_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_unicode_data_type_checking_import_uses_cells_module() -> None:
    """Unicode data type checking should refer to rich.cells.CellTable."""
    source = Path("rich/_unicode_data/__init__.py").read_text(encoding="utf-8")

    assert "from rich.cells import CellTable" in source
    assert "from rich.cell_string import CellTable" not in source
'''

TABLE_COLUMN_EXPAND_DOC_REMOVED_TEST = '''\
from __future__ import annotations

from pathlib import Path


def test_column_docstring_does_not_list_removed_expand_argument() -> None:
    """Column docs should not list the removed expand argument."""
    source = Path("rich/table.py").read_text(encoding="utf-8")
    expand_doc = "expand (bool, optional): Expand the table to fit the available space"

    assert "class Column:" in source
    assert source.count(expand_doc) == 2
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
    if subject == "restore caching behavior" and "rich/cells.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_cells_cached_len_unicode_version.py",
                    "content": CACHED_CELL_LEN_UNICODE_VERSION_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_cells_cached_len_unicode_version.py",
            "test_node_count": 1,
            "oracle_template": "cells_cached_len_unicode_version",
        }
    if subject == "feat: traceback - expose more locals rendering options" and {
        "rich/scope.py",
        "rich/traceback.py",
    }.issubset(source_files):
        return {
            "hidden_files": [
                {
                    "path": "tests/test_traceback_locals_options.py",
                    "content": TRACEBACK_LOCALS_OPTIONS_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_traceback_locals_options.py",
            "test_node_count": 1,
            "oracle_template": "traceback_locals_depth_overflow_options",
        }
    if subject == "update progress.py" and "rich/progress.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_progress_disabled_stop_output.py",
                    "content": PROGRESS_DISABLE_NO_BLANK_LINE_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_progress_disabled_stop_output.py",
            "test_node_count": 1,
            "oracle_template": "progress_disabled_stop_no_blank_line",
        }
    if subject == "py3.8 fix" and "rich/_unicode_data/__init__.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_unicode_data_py38_cache_fallback.py",
                    "content": UNICODE_CACHE_PY38_FALLBACK_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_unicode_data_py38_cache_fallback.py",
            "test_node_count": 1,
            "oracle_template": "unicode_data_py38_cache_fallback",
        }
    if subject == "f string path" and {
        "rich/_unicode_data/__init__.py",
        "rich/_unicode_data/_versions.py",
    }.issubset(source_files):
        return {
            "hidden_files": [
                {
                    "path": "tests/test_unicode_data_load_latest.py",
                    "content": UNICODE_LOAD_LATEST_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_unicode_data_load_latest.py",
            "test_node_count": 1,
            "oracle_template": "unicode_data_load_latest_table",
        }
    if subject == "test" and "rich/_unicode_data/__init__.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_unicode_data_invalid_version_fallback.py",
                    "content": UNICODE_INVALID_VERSION_FALLBACK_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_unicode_data_invalid_version_fallback.py",
            "test_node_count": 1,
            "oracle_template": "unicode_data_invalid_version_fallback",
        }
    if subject == "cell string class" and "rich/cell_string.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_cell_string_basic_api.py",
                    "content": CELL_STRING_BASIC_API_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_cell_string_basic_api.py",
            "test_node_count": 1,
            "oracle_template": "cell_string_basic_api",
        }
    if subject == "cell tables" and "rich/cell_string.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_cell_string_table_api.py",
                    "content": CELL_TABLE_API_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_cell_string_table_api.py",
            "test_node_count": 1,
            "oracle_template": "cell_table_metadata_api",
        }
    if subject == "split text" and {
        "rich/_unicode_data/__init__.py",
        "rich/cell_string.py",
    }.issubset(source_files):
        return {
            "hidden_files": [
                {
                    "path": "tests/test_cell_string_split_text.py",
                    "content": CELL_STRING_SPLIT_TEXT_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_cell_string_split_text.py",
            "test_node_count": 1,
            "oracle_template": "cell_string_split_text",
        }
    if subject == "respect custom console instance in ipython output" and "rich/pretty.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_pretty_ipython_custom_console.py",
                    "content": PRETTY_IPYTHON_CUSTOM_CONSOLE_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_pretty_ipython_custom_console.py",
            "test_node_count": 1,
            "oracle_template": "pretty_ipython_custom_console",
        }
    if subject == "docstring" and "rich/progress.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_progress_reset_visible_docstring.py",
                    "content": PROGRESS_RESET_DOCSTRING_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_progress_reset_visible_docstring.py",
            "test_node_count": 1,
            "oracle_template": "progress_reset_visible_docstring",
        }
    if subject == "simplify" and "rich/cells.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_cells_variation_selector_simplified.py",
                    "content": CELLS_VARIATION_SELECTOR_SIMPLIFIED_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_cells_variation_selector_simplified.py",
            "test_node_count": 1,
            "oracle_template": "cells_variation_selector_branch_simplified",
        }
    if subject == "refine" and "rich/cells.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_cells_binary_search_unpack.py",
                    "content": CELLS_BINARY_SEARCH_UNPACK_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_cells_binary_search_unpack.py",
            "test_node_count": 1,
            "oracle_template": "cells_binary_search_entry_unpack",
        }
    if subject == "update rich/_unicode_data/__init__.py" and "rich/_unicode_data/__init__.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_unicode_data_fallback_comment.py",
                    "content": UNICODE_FALLBACK_COMMENT_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_unicode_data_fallback_comment.py",
            "test_node_count": 1,
            "oracle_template": "unicode_data_fallback_comment_completed",
        }
    if subject == "remove reference to cell strings" and "rich/_unicode_data/__init__.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_unicode_data_cell_table_type_import.py",
                    "content": UNICODE_CELL_TABLE_TYPE_IMPORT_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_unicode_data_cell_table_type_import.py",
            "test_node_count": 1,
            "oracle_template": "unicode_data_cell_table_type_import",
        }
    if subject == "remove error docstring" and "rich/table.py" in source_files:
        return {
            "hidden_files": [
                {
                    "path": "tests/test_table_column_expand_doc_removed.py",
                    "content": TABLE_COLUMN_EXPAND_DOC_REMOVED_TEST,
                }
            ],
            "command": ".venv/bin/python -m pytest -q tests/test_table_column_expand_doc_removed.py",
            "test_node_count": 1,
            "oracle_template": "table_column_expand_doc_removed",
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
