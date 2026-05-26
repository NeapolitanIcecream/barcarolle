# Phase 1 Reference Gate Subclassification

Plain-language summary: the old `reference_pass` gate is too coarse. This report separates install, import, collection, assertion, timeout, unavailable environment, pass, and unknown failures.

| final subgate | task count |
| --- | ---: |
| reference_collect_failed | 10 |
| reference_import_failed | 8 |
| reference_install_failed | 10 |
| reference_pass | 8 |

Install/import/collection/environment shaped failures in sample: `28`.

Production classification change recommended: `True`.
