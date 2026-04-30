# Empty Patch Gate Review

status: issues_found

## Summary

Reviewed implementation commit `1504e5e` for the post-pilot-004 empty-patch
adapter hardening. The committed no-model regression smoke passes, and a
scratch no-model harness confirmed that an exit-0 command with an empty git diff
now records adapter status and ledger event `no_patch_generated` with normalized
status `infra_failed`.

One issue remains: unsafe patch rejection still keeps its top-level status and
ledger event distinct, but the new empty-patch boolean is computed from the
sanitized patch artifact size after unsafe content is withheld. That causes an
unsafe non-empty diff to record `no_patch_generated: true` in adapter and ledger
metadata and to receive the empty-patch normalized message.

## Findings

- `experiments/core_narrative/tools/acut_patch_adapter.py:532`: unsafe patch
  rejection can be tagged as `no_patch_generated`. The new
  `no_patch_generated` value is computed as exit code `0` plus zero-byte patch
  artifact before excluding `unsafe_patch_rejected`. For unsafe content,
  `write_safe_patch` returns a zero-byte sanitized artifact, so the adapter
  status remains `unsafe_patch_rejected` and the ledger event remains
  `command_completed_unsafe_patch_rejected`, but adapter payload and ledger
  metadata also say `no_patch_generated: true`. The same boolean then triggers
  the normalized empty-patch error at line `609`. This weakens the required
  separation between unsafe patch rejection and true exit-0 empty-diff runs.

## Evidence

- Read the required coordinator and worker process files. No `cli.log` file was
  inspected.
- Reviewed the scoped diff for `1504e5e` only across the requested files.
- Ran `python3 experiments/core_narrative/tools/test_acut_patch_adapter.py`:
  passed, `1` test.
- Ran scratch no-model adapter cases with `--command-no-model`:
  non-empty success returned status/event `command_completed` with nonzero patch
  size; non-zero empty command returned `command_failed`; timeout returned
  `timeout` with exit `124`; unsafe patch rejection returned
  `unsafe_patch_rejected` / `command_completed_unsafe_patch_rejected` but also
  recorded `no_patch_generated: true` and wrote an empty-patch normalized
  `infra_failed` result.
- Ran syntax check with `PYTHONPYCACHEPREFIX=/tmp/... python3 -m py_compile`
  over the adapter and regression test: passed. An initial default-cache
  attempt was blocked by sandbox cache permissions only.
- Ran scoped redaction-oriented scans excluding `cli.log`. Matches were limited
  to allowed environment variable names, negative `record_full_base_url` /
  `record_resolved_base_url` fields, command templates, and dummy test-only
  values; no bearer token string, literal full URL, or IP address was found in
  the scoped artifact/workflow review set.
- This review did not start any live BARCAROLLE model call, ACUT attempt, retry,
  second attempt, additional specialist run, broad execution, or large batch.

## Required Closure

Before integration, make true empty-patch classification exclude unsafe patch
rejection. A minimal closure is to compute or act on `no_patch_generated` only
when the command exited `0`, did not time out, and `unsafe_patch_rejected` is
false, and to guard the normalized empty-patch write on
`status == "no_patch_generated"`.

Add a no-model regression case for unsafe patch rejection that asserts the
adapter and ledger metadata do not mark `no_patch_generated` while preserving
the distinct unsafe status/event.
