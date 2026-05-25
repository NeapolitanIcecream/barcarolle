# Phase 1 Canonical Statement Reviews

Generated: `2026-05-25T07:44:40Z`.

- Candidate statements reviewed: `4`.
- Review counts: `{'pass': 4}`.
- LLM API calls made: `False`.
- Codex Subscription session used: `True`.
- Paid ACUT calls made: `false`.
- Raw prompts or completions committed: `false`.

## Verdicts

### boltons__hist__011

- Status: `pass`.
- Checks: `{'leakage_pass': True, 'sufficiency_pass': True, 'faithfulness_pass': True, 'scope_pass': True, 'formatting_pass': True}`.
- Reasons: `['Statement stays within sanitized public context and diff metadata, with no raw diff hunks, gold patch text, raw test assertions, paid outcome/status, target commit hash, or hidden oracle material.', 'It gives a complete problem summary, observable iterable strip behavior, expected public API behavior, implementation-only editable scope, and no truncation or formatting defects.']`.
- Required revision: ``.

### boltons__hist__022

- Status: `pass`.
- Checks: `{'leakage_pass': True, 'sufficiency_pass': True, 'faithfulness_pass': True, 'scope_pass': True, 'formatting_pass': True}`.
- Reasons: `['Statement stays within sanitized public context and diff metadata, with no raw diff hunks, gold patch text, raw test assertions, paid outcome/status, target commit hash, or hidden oracle material.', 'It faithfully describes chunk_ranges, windowing/overlap behavior, edge cases, and invalid argument expectations while keeping tests and docs out of the editable scope.']`.
- Required revision: ``.

### boltons__hist__023

- Status: `pass`.
- Checks: `{'leakage_pass': True, 'sufficiency_pass': True, 'faithfulness_pass': True, 'scope_pass': True, 'formatting_pass': True}`.
- Reasons: `['Statement stays within sanitized public context and diff metadata, with no raw diff hunks, gold patch text, raw test assertions, paid outcome/status, target commit hash, or hidden oracle material.', 'It provides enough public traceback parsing behavior to attempt the fix, matches the tbutils packet scope, and has complete required sections with no truncation.']`.
- Required revision: ``.

### boltons__hist__027

- Status: `pass`.
- Checks: `{'leakage_pass': True, 'sufficiency_pass': True, 'faithfulness_pass': True, 'scope_pass': True, 'formatting_pass': True}`.
- Reasons: `['Statement stays within sanitized public context and diff metadata, with no raw diff hunks, gold patch text, raw test assertions, paid outcome/status, target commit hash, or hidden oracle material.', 'It accurately frames cache mapping view behavior, preserves implementation-only scope, and includes complete required sections without over-prescribing an implementation recipe.']`.
- Required revision: ``.
