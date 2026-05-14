<!-- RICH_STATIC_CONTEXT_PACK_V1 -->
# Rich Static Context Pack

Pack ID: rich_static_context_pack_v1
Marker: RICH_STATIC_CONTEXT_PACK_V1
Source: locked local Rich public source, docs, tests, examples, and task-agnostic public pre-base history summaries.
Task scope: task-agnostic; generated after task admission and before any Rich C/R/W* primary ACUT execution.
Leakage guard: no W* target commit, reference patch, hidden verifier, hidden hint, ACUT output, final diff, exact task answer pattern, credentials, endpoint values, full URLs, hostnames, or IP addresses.

[RICH_SECTION:module_map]
Use `rich/console.py`, `rich/segment.py`, `rich/measure.py`, `rich/align.py`, and `rich/padding.py` for console orchestration, render options, segment streams, measurement, alignment, and padding.
Use `rich/text.py`, `rich/style.py`, `rich/markup.py`, `rich/emoji.py`, and `rich/cells.py` for text spans, style parsing, markup, emoji replacement, grapheme width, and cell-length behavior.
Use `rich/table.py`, `rich/panel.py`, `rich/columns.py`, `rich/rule.py`, `rich/tree.py`, and `rich/layout.py` for presentation containers and layout measurement.
Use `rich/progress.py`, `rich/live.py`, `rich/live_render.py`, `rich/status.py`, and `rich/spinner.py` for live terminal updates, progress state, status rendering, and spinner demos.
Use `rich/traceback.py`, `rich/syntax.py`, `rich/logging.py`, `rich/_inspect.py`, and `rich/pretty.py` for formatted diagnostics, syntax highlighting, logging integration, object inspection, and pretty rendering.

[RICH_SECTION:semantic_invariants]
Preserve Console protocol boundaries: measure and render through console options, render hooks, and Segment streams rather than ad hoc string conversion.
Text, Style, markup, emoji, and cell-width changes should preserve grapheme width, combining character, variation selector, and East Asian width behavior unless the public task requires a visible rendering change.
Live, Progress, Status, and Spinner changes should preserve refresh behavior, nested rendering state, terminal-control output, and deterministic non-terminal behavior under tests.
Traceback, Syntax, Logging, Inspect, and Pretty changes should preserve public formatting behavior and keep introspection or syntax-highlighting imports lazy where surrounding code expects it.
Presentation containers should keep measurement and rendering responsibilities separated; avoid broad rewrites when a focused render or measurement path owns the bug.

[RICH_SECTION:testing_guide]
Start with the smallest adjacent public test module, then run the exact benchmark verifier after patching.
For console/rendering work: `.venv/bin/python -m pytest -q tests/test_console.py tests/test_segment.py tests/test_measure.py`.
For text/style/markup/cells work: `.venv/bin/python -m pytest -q tests/test_text.py tests/test_style.py tests/test_markup.py tests/test_cells.py`.
For progress/live/status work: `.venv/bin/python -m pytest -q tests/test_progress.py tests/test_live.py tests/test_live_render.py tests/test_status.py`.
For traceback/syntax/logging/inspect work: `.venv/bin/python -m pytest -q tests/test_traceback.py tests/test_syntax.py tests/test_logging.py tests/test_inspect.py`.

[RICH_SECTION:calibration_boundary]
Allowed: public task statement, files named by the task, failing-test surfaced files, adjacent public tests, direct symbol/filename search, this task-agnostic context pack, and public source/docs/tests in the prepared workspace.
Forbidden: W* target commit, reference patch, hidden verifier implementation, hidden human hints, previous ACUT outputs, current task final diff, and post-hoc answer-pattern summaries.
