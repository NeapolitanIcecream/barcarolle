RICH_C_CALIBRATED_CONTEXT_PACK_V1
pack_id: rich_c_calibrated_context_pack_v1

[RICH_SECTION:c_family_taxonomy]
# C-Derived Rich Repair Taxonomy

This pack is calibrated from admitted Rich C calibration tasks and public Rich source/tests only. It does not use W* target commits, W* reference patches, W* hidden verifiers, W* results, R scores, or ACUT outputs.

Observed C calibration families:
- console rendering, measurement, and options;
- text, style, cells, unicode, and markup;
- progress, live, status, and spinner rendering;
- traceback, syntax, logging, inspect, and pretty diagnostics;
- documentation, type annotations, demos, and public source contracts.

[RICH_SECTION:abstract_repair_patterns]
# Abstract Repair Patterns

Use these as repair heuristics, not as task answers:
- Map the public symptom to the owning render or measurement protocol before changing general-purpose helpers.
- For rendering issues, preserve Segment and Console option flow; prefer focused changes in the module that owns the visible output.
- For text, style, unicode, and cell-width issues, test grapheme boundaries, variation selectors, combining characters, and cached width behavior.
- For progress/live/status issues, verify refresh ordering and nested or stacked live-display behavior under deterministic tests.
- For diagnostics and syntax work, check import laziness, type annotations, recursion guards, and explicit None checks where public formatting depends on them.
- For source-level compatibility tasks, treat public docstrings, annotations, comments used by docs, and demo output as observable contracts when the task statement names them.

[RICH_SECTION:maintainer_style_regression_tests]
# Maintainer-Style Regression Test Patterns

Use focused tests that demonstrate the public behavior:
- Add or update one test near the existing behavior family.
- Prefer render-segment, measurement, import-side-effect, or public API assertions over broad snapshots.
- Use source-level assertions only for public docstrings, annotations, demo text, compatibility branch removal, or intentionally source-visible contracts.
- Keep tests deterministic and in-process; avoid real terminal state, network calls, or environment-dependent output.

[RICH_SECTION:calibration_boundary]
# Calibration Boundary

Allowed calibration sources:
- Rich C public task metadata and admitted abstract calibration outcomes.
- Public Rich source, tests, docs, and task-agnostic bounded history.

Forbidden sources:
- W* target commits.
- W* reference patches or final diffs.
- W* hidden verifiers.
- W* ACUT outputs, failed patches, or post-hoc tuning.
- R scores or W* results.
- Secrets, credentials, private endpoints, or non-public benchmark artifacts.
