# Kilo Completion And Policy Diagnosis

Generated: `2026-05-21T07:50:40+00:00`.

## Kilo Completion

- Kilo ACUT harness errors: `6`.
- Classifications: `{'adapter_timeout_nonempty_diff_nonexit': 6}`.

- `toolz__hist__002` `B_real`: `adapter_timeout_nonempty_diff_nonexit`; exit `124`, elapsed `900.011`, patch non-empty `True`, changed paths `['toolz/functoolz.py']`, stdout tail events `[]`, log idle `False`, log suggestion `False`.
- `toolz__hist__001` `B_real`: `adapter_timeout_nonempty_diff_nonexit`; exit `124`, elapsed `900.008`, patch non-empty `True`, changed paths `['toolz/functoolz.py']`, stdout tail events `[]`, log idle `False`, log suggestion `False`.
- `toolz__hist__004` `W_real`: `adapter_timeout_nonempty_diff_nonexit`; exit `124`, elapsed `900.008`, patch non-empty `True`, changed paths `['toolz/functoolz.py']`, stdout tail events `[]`, log idle `False`, log suggestion `False`.
- `toolz__hist__010` `W_real`: `adapter_timeout_nonempty_diff_nonexit`; exit `124`, elapsed `900.018`, patch non-empty `True`, changed paths `['tlz/_build_tlz.py', 'toolz/curried/__init__.py', 'toolz/functoolz.py']`, stdout tail events `[]`, log idle `False`, log suggestion `False`.
- `toolz__hist__016` `W_real`: `adapter_timeout_nonempty_diff_nonexit`; exit `124`, elapsed `900.011`, patch non-empty `True`, changed paths `['toolz/itertoolz.py']`, stdout tail events `[]`, log idle `False`, log suggestion `False`.
- `click__rbench__004` `G_mini`: `adapter_timeout_nonempty_diff_nonexit`; exit `124`, elapsed `900.009`, patch non-empty `True`, changed paths `['click/testing.py']`, stdout tail events `[]`, log idle `True`, log suggestion `True`.

## Policy Rejections

- Policy violations: `5`.
- Harness error counts: `{'submission_edited_out_of_scope_paths': 2, 'submission_edited_tests': 3}`.

- `codex_workspace` `toolz__hist__010` `W_real`: `submission_edited_out_of_scope_paths` rejected `['toolz/curried/__init__.py']`; statement mentions rejected paths `[]`; statement mentions tests path `False`; editable section `False`.
- `codex_workspace` `click__rbench__002` `G_mini`: `submission_edited_tests` rejected `['tests/test_testing.py']`; statement mentions rejected paths `['tests/test_testing.py']`; statement mentions tests path `True`; editable section `False`.
- `codex_workspace` `click__rbench__003` `G_mini`: `submission_edited_tests` rejected `['tests/test_termui.py']`; statement mentions rejected paths `['tests/test_termui.py']`; statement mentions tests path `True`; editable section `False`.
- `codex_workspace` `click__rbench__004` `G_mini`: `submission_edited_tests` rejected `['tests/test_testing.py']`; statement mentions rejected paths `['tests/test_testing.py']`; statement mentions tests path `True`; editable section `False`.
- `kilo_workspace` `click__rbench__003` `G_mini`: `submission_edited_out_of_scope_paths` rejected `['click/types.py']`; statement mentions rejected paths `[]`; statement mentions tests path `True`; editable section `False`.

## Finding

The Kilo failures are dominated by adapter timeouts with non-empty workspace diffs, not endpoint proof failures. The completed matrix also used solver-visible statements without explicit editable/non-editable sections, while the benchmark policy still rejected test edits and out-of-scope edits.
