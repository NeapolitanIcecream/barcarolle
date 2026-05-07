# ACUT Adapter Nonzero-Exit Normalization

status: delivered
updated: 2026-05-01

## Summary

`experiments/core_narrative/tools/acut_patch_adapter.py` now writes a
normalized run result when the inner patch-generation command exits nonzero,
does not time out, passes unsafe-content rejection, and leaves no
verifier-ready patch.

The normalized artifact uses `status: infra_failed` and records a no-secret
metadata classification:

- `adapter_status: command_failed`
- `failure_class: nonzero_exit`
- `no_patch_generated: false`
- `verifier_ready_patch_available: false`

This closes the pilot 006 result-contract gap where the raw adapter and inner
Codex CLI summaries were sufficient for review, but the outer normalized result
file was absent.

## Preserved Distinctions

- Exit-0 empty diff remains `no_patch_generated`, with ledger event
  `no_patch_generated` and normalized `infra_failed`.
- Unsafe patch content remains `unsafe_patch_rejected`, with ledger event
  `command_completed_unsafe_patch_rejected`; it is not normalized as an
  empty-patch or nonzero-exit result.
- Timeout remains `timeout` / `command_timeout`; this repair does not fold it
  into the nonzero-exit path.
- Successful verifier-eligible patch generation remains the exit-0,
  safe, non-empty patch path.

The reviewed inner `codex_cli_patch_command.py` failure-capture contract is
unchanged. Its structured `failure_capture` and `workspace_patch` summaries
remain the detailed inner-command diagnostics, and no `cli.log` inspection is
required.

## No-Model Verification

Commands run:

```bash
python3 experiments/core_narrative/tools/test_acut_patch_adapter.py
python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py
python3 -m py_compile experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/test_acut_patch_adapter.py
PYTHONPYCACHEPREFIX=/tmp/nonzero-exit-normalization-pycache python3 -m py_compile experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/test_acut_patch_adapter.py
git diff --check
```

Results:

- `test_acut_patch_adapter.py`: passed, 3 tests.
- `test_codex_cli_patch_command.py`: passed, 4 tests.
- Plain `py_compile`: blocked by sandboxed macOS Python cache creation outside
  the writable worktree before project compilation.
- `PYTHONPYCACHEPREFIX` py_compile: passed.
- `git diff --check`: passed.

No ACUT attempt, live BARCAROLLE model call, retry, second attempt, additional
specialist run, broad execution, further pilot attempt, large model-call batch,
or cost-ledger append was started.

## Coordinator Gate

Recommended next gate: run a focused no-model review of this worker delivery
before integration. After a clean review, any later live execution still needs a
separate explicit coordinator decision; this repair alone does not authorize a
new pilot attempt.
