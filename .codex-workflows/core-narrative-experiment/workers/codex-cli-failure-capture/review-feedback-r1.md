# Review Feedback R1

status: issues_found

## Summary

Focused no-model/static review completed for delivery commit `64c5d9b`. The
implementation adds useful structured `failure_capture` and `workspace_patch`
metadata and preserves the outer adapter contract, but closure is required
before this can gate a later live attempt.

## Findings

1. `experiments/core_narrative/tools/codex_cli_patch_command.py` hard-codes a
   limited hostname suffix list and relies on that expression for stdout/stderr
   artifact and tail redaction. Hostname-shaped text outside that suffix list
   can remain unredacted while `failure_capture.redaction_policy` claims
   `hostnames_redacted: true`.

2. `experiments/core_narrative/tools/test_codex_cli_patch_command.py` covers
   only `nonzero_exit` and `no_workspace_patch`. The delivered command reports
   `timeout` and `unsafe_patch_content` classes, but there are no no-model
   regression tests for them. Tests also need to read redacted stdout/stderr
   artifact contents and assert that credential values, bearer-token-shaped
   strings, full URLs, hostnames, and IP address-shaped strings are absent.

## Required Closure

Broaden failure-capture hostname redaction without relying on a narrow suffix
list, add no-model regression coverage for timeout and unsafe patch content,
and verify redacted artifact file contents. Re-review the repair before any
later live ACUT attempt or model-call authorization.
