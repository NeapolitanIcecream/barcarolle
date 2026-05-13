<!-- CLICK_SPECIALIST_CONTEXT_PACK_V1 -->
# Click Deep Specialist Context Pack

Pack ID: click_deep_specialist_context_pack_v2
Pack hash: sha256:4c4906338af6c57bf833363937073d6045b820d1157f77adcc7687e372a59f75
Marker: CLICK_SPECIALIST_CONTEXT_PACK_V1
Source: locked local Click checkout public source, docs, tests, examples, and task-agnostic public pre-base history summaries.
Task scope: task-agnostic; generated before M5-W2 primary execution.
Leakage guard: no target commit, reference patch, hidden verifier, hidden hint, ACUT output, RWork final diff, exact task answer pattern, credentials, endpoint values, full URLs, hostnames, or IP addresses.

[CLICK_SECTION:module_map]
Use `src/click/core.py` for Command, Group, Context, Parameter, Option, Argument, default/envvar/prompt/source resolution, and help entry points.
Use `src/click/types.py` for conversion, composite values, ranges, files, paths, UUID, DateTime, and conversion error rendering.
Use `src/click/testing.py` for CliRunner isolation, synthetic streams, filesystem isolation, env overrides, and result capture.
Use `src/click/termui.py` for prompts, confirmations, progress bars, echo helpers, hidden input, and terminal wrappers.
Use `src/click/parser.py` for low-level token parsing, option matching, arity, and parser state.
Use `src/click/decorators.py`, `src/click/formatting.py`, and `src/click/shell_completion.py` for decorator construction, help formatting, and completion behavior.

[CLICK_SECTION:semantic_invariants]
Option/default/envvar/flag_value: keep source provenance distinct; envvar values are external string input before conversion; flag activation is not the same as declared default behavior; avoid invoking callable defaults or flag values merely for comparison/display; resolve shared-destination defaults before collapsing to a final parameter value.
CliRunner/testing: isolate Click-managed stdin, stdout, stderr, cwd, env, and exception capture; synthetic stdin must behave like a readable text stream for file parameters, prompts, echoing, and EOF; temporary global patches must be restored after invoke.
Prompt/termui/output: visible default text can differ from the internal default; prompt rendering crosses option metadata, confirmation, hidden input, and stream capability; terminal width/color/pager/progress behavior should be tested through Click helpers.
Type conversion/parameter normalization: ParamType.convert owns type-specific user-visible conversion errors; composite/repeated parameters normalize between parser output and type conversion; Path/File behavior crosses filesystem, streams, lazy open, and cleanup.

[CLICK_SECTION:testing_guide]
Start with the smallest focused pytest selection that exercises the changed behavior; then run the adjacent public module before broadening.
For option/default/envvar/flag_value work: `.venv/bin/python -m pytest -q tests/test_options.py tests/test_defaults.py`.
For CliRunner/testing/io isolation: `.venv/bin/python -m pytest -q tests/test_testing.py tests/test_chain.py`.
For prompt/termui/output: `.venv/bin/python -m pytest -q tests/test_termui.py tests/test_formatting.py`.
For type conversion/normalization: `.venv/bin/python -m pytest -q tests/test_types.py tests/test_arguments.py`.
Local tests inside the ACUT run workspace are auxiliary; primary scoring comes only from fresh verifier replay.

[CLICK_SECTION:pre_base_history_summary]
Recent public Click work repeatedly touches option default display, ParameterSource ordering, default_map behavior, stream compatibility, and parallel-friendly test isolation. Treat source tracking and restoration as behavioral contracts, not incidental metadata.
Docs and formatting changes often accompany behavior changes; do not infer a required code change from docs-only anchors.
Use public source/docs/tests and this task-agnostic summary as prior context. Do not use target commits, reference patches, hidden verifiers, ACUT outputs, RWork final diffs, or exact task answer patterns.

[CLICK_SECTION:leakage_boundary]
Allowed: public task statement, files named by the task, failing-test surfaced files, adjacent public tests, direct symbol/filename search, this task-agnostic context pack, and public source/docs/tests in the prepared workspace.
Forbidden: target commit, reference patch, hidden verifier implementation, hidden human hints, future task history, previous ACUT outputs, current task final diff, and post-hoc answer-pattern summaries from RBench/RWork reference patches.
When source-derived full URLs appear only in diff context or removed source lines, the harness may use a private replay patch while public artifacts remain redacted. Model-generated URLs, secrets, credentials, and ambiguous unsafe content remain unsafe_or_scope_violation.
