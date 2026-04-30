<!-- CLICK_SPECIALIST_CONTEXT_PACK_V1 -->
# Click Specialist Context Pack

Pack ID: click_specialist_context_pack_v1
Pack hash: sha256:dfb271ad174531a7dd2f00da4cd0486193d87ce33349380982150889ecf84e48
Marker: CLICK_SPECIALIST_CONTEXT_PACK_V1
Source: locked local Click checkout public source, docs, tests, and examples only.
Task scope: task-agnostic; generated before any Click-specialist ACUT execution.
Leakage guard: no benchmark solution patch content, hidden verifier files, hidden hints, ACUT outputs, network-fetched docs, credentials, endpoint values, full URLs, hostnames, or IP addresses.

[CLICK_SECTION:repo_map]
Locked Click commit: 8bd8b4a074c55c03b6eb5666edc44a9c43df38a2
Layout roots: src/click, tests, docs, examples.
Core modules: src/click/__init__.py, src/click/_compat.py, src/click/_termui_impl.py, src/click/_textwrap.py, src/click/_utils.py, src/click/_winconsole.py, src/click/core.py, src/click/decorators.py, src/click/exceptions.py, src/click/formatting.py, src/click/globals.py, src/click/parser.py, src/click/shell_completion.py, src/click/termui.py, src/click/testing.py, src/click/types.py, src/click/utils.py.
Public exports from click.__init__: Abort, Argument, BOOL, BadArgumentUsage, BadOptionUsage, BadParameter, Choice, ClickException, Command, CommandCollection, Context, DateTime, FLOAT, File, FileError, FloatRange, Group, HelpFormatter, INT, IntRange, MissingParameter, NoSuchOption, Option, ParamType, Parameter, ParameterSource, Path, STRING, Tuple, UNPROCESSED, UUID, UsageError, argument, clear, command, confirm, confirmation_option, echo, echo_via_pager, edit; +23 more.

[CLICK_SECTION:docs_map]
Docs/examples mapped by headings only: README.md, docs/advanced.md, docs/api.md, docs/arguments.md, docs/changes.rst, docs/click-concepts.md, docs/command-line-reference.md, docs/commands-and-groups.md, docs/commands.md, docs/complex.md, docs/contrib.md, docs/contributing.md, docs/design-opinions.md, docs/documentation.md, docs/entry-points.md, docs/exceptions.md, docs/extending-click.md, docs/faqs.md, docs/handling-files.md, docs/index.rst, docs/license.md, docs/option-decorators.md, docs/options.md, docs/parameter-types.md, docs/parameters.md, docs/prompts.md, docs/quickstart.md, docs/setuptools.md; +20 more.

[CLICK_SECTION:symbol_index]
Indexed symbols: 1115 total across source, public tests, and examples.
Public source symbol examples: click._compat._AtomicFile.close, click._compat._AtomicFile.name, click._compat._FixupStream.read1, click._compat._FixupStream.readable, click._compat._FixupStream.seekable, click._compat._FixupStream.writable, click._compat._NonClosingTextIOWrapper.isatty, click._compat.get_best_encoding, click._compat.get_binary_stderr, click._compat.get_binary_stdin, click._compat.get_binary_stdout, click._compat.get_text_stderr, click._compat.get_text_stdin, click._compat.get_text_stdout, click._compat.is_ascii_encoding, click._compat.isatty, click._compat.open_stream, click._compat.should_strip_ansi, click._compat.strip_ansi, click._compat.term_len, click._termui_impl.Editor, click._termui_impl.Editor.edit, click._termui_impl.Editor.edit_files, click._termui_impl.Editor.get_editor, click._termui_impl.ProgressBar, click._termui_impl.ProgressBar.eta, click._termui_impl.ProgressBar.finish, click._termui_impl.ProgressBar.format_bar, click._termui_impl.ProgressBar.format_eta, click._termui_impl.ProgressBar.format_pct, click._termui_impl.ProgressBar.format_pos, click._termui_impl.ProgressBar.format_progress_line, click._termui_impl.ProgressBar.generator, click._termui_impl.ProgressBar.make_step, click._termui_impl.ProgressBar.pct, click._termui_impl.ProgressBar.render_finish, click._termui_impl.ProgressBar.render_progress, click._termui_impl.ProgressBar.time_per_iteration, click._termui_impl.ProgressBar.update, click._termui_impl.open_url, click._termui_impl.pager, click._textwrap.TextWrapper; +306 more.

[CLICK_SECTION:convention_playbook]
- patch_public_api_carefully: When changing public behavior, check exports in src/click/__init__.py and behavior tests in tests/test_*.py.
- use_cli_runner_for_cli_behavior: CLI behavior is commonly exercised through click.testing.CliRunner and result exit/output assertions.
- keep_parser_option_type_boundaries: Parser, option, argument, type, formatting, terminal UI, and shell-completion behavior live in separate modules with matching public tests.
- prefer_focused_pytest: Use focused pytest module or test-name selection first; broaden only when the changed surface crosses modules.
- docs_follow_behavior: When user-facing command semantics change, inspect the matching docs page heading map before editing docs.

[CLICK_SECTION:deterministic_retrieval_policy]
1. Read the public task statement and named files.
2. Map mentioned symbols or failing imports to symbol_index exact names.
3. Inspect repo_map for the owning Click module and adjacent public tests.
4. Use docs_map headings only when behavior is public or documented.
5. Apply convention_playbook guidance for verification scope and public API boundaries.
Apply this context only for frontier-click-specialist and cheap-click-specialist.
Do not use this context for generic SWE ACUTs.
