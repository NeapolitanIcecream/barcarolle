CLICK_SPECIALIST_CONTEXT_PACK_V1
pack_id: click_rbench_calibrated_context_pack_v1
pack_hash: b1b1ee40b72be5912ea07ac76d6ae6689edb2f3a930c5e2479ea6f71ffc0de85

[CLICK_SECTION:rbench_family_taxonomy]
# RBench-Derived Click Repair Taxonomy

This pack is calibrated from the public RBench Click calibration set, not from W2 or W3 ACUT outputs.

Observed RBench families:
- option help and default rendering: default values should be rendered through explicit Click formatting paths, not incidental truthiness or repr behavior.
- CliRunner exception and stream handling: runner defaults, invoke-time overrides, mixed output, separated stdout/stderr, and Result fields must stay backward compatible.
- prompt and terminal UI rendering: prompt text should preserve defaults, choices, hidden choices, and deterministic testability under CliRunner.
- type conversion and normalization: Choice and DateTime conversions should preserve public return semantics while expanding accepted input forms.
- optional value and parser behavior: parser state, prompt_required, required, defaults, and explicit values must be resolved in the documented order.

[CLICK_SECTION:abstract_repair_patterns]
# Abstract Repair Patterns

Use these as repair heuristics, not as task answers:
- Locate the public API boundary first, then follow the internal normalization path to the final user-visible behavior.
- Preserve old behavior unless the task statement explicitly requires an API extension.
- Prefer a narrow source change in the owning module plus a focused regression test.
- For option/default issues, inspect `Option.get_default`, `Option.full_process_value`, `Parameter.consume_value`, and help/default rendering before changing parser internals.
- For CliRunner issues, inspect `CliRunner.invoke`, isolation setup, Result construction, and exception capture boundaries before changing command execution.
- For prompt/termui issues, verify both prompt text construction and CliRunner-based tests; avoid real-terminal assumptions.
- For type conversion issues, inspect `ParamType.convert`, normalization helpers, return value preservation, and error messages.
- For parser optional-value issues, inspect how missing values, explicit flag values, prompts, and defaults move through parser state.

[CLICK_SECTION:maintainer_style_regression_tests]
# Maintainer-Style Regression Test Patterns

Use focused tests that demonstrate the public behavior:
- Add or update one test near the existing behavior family.
- Prefer `CliRunner` for command behavior, prompts, stream capture, and exceptions.
- Assert both the new behavior and the compatibility edge that could regress.
- Keep tests deterministic and in-process; avoid real terminal state, locale sensitivity, or network calls.
- For type conversions, test accepted input, returned value, and failure message shape when relevant.
- For defaults and prompts, test explicit values, missing values, default values, and opt-out switches.

[CLICK_SECTION:click_module_failure_checklist]
# Click Module and Failure-Mode Checklist

Before patching:
- Map the task family to the owning module: `src/click/core.py`, `src/click/parser.py`, `src/click/testing.py`, `src/click/termui.py`, or `src/click/types.py`.
- Read adjacent tests in `tests/test_options.py`, `tests/test_testing.py`, `tests/test_termui.py`, `tests/test_types.py`, or the named verifier file.
- Run the focused failing test if practical, then rerun the exact verifier command after patching.
- If the obvious module does not explain the failure, inspect the call chain from public API entry to final output or exception.
- Keep the patch minimal. Do not rewrite unrelated formatting, docs, or broad parser behavior.

[CLICK_SECTION:calibration_boundary]
# Calibration Boundary

Allowed calibration sources:
- RBench public task statements and public metadata.
- RBench reference patches only as abstract repair-pattern calibration.
- Public Click source, tests, docs, and bounded pre-W3 history.

Forbidden sources:
- W3 target commits.
- W3 reference patches or final diffs.
- W3 hidden verifiers.
- W3 ACUT outputs, failed patches, or post-hoc tuning.
- M5/W2 ACUT outputs as calibration data.
- Secrets, credentials, private endpoints, or non-public benchmark artifacts.

This pack is for a new M6 hypothesis. It must not be used to reinterpret M5-W2 primary scores.
