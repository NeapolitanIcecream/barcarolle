# ACUT Adapter Empty Patch Gate

status: revision_1_no_model_smoke_passed
updated: 2026-04-30T13:31:20+08:00

## Summary

The ACUT adapter classifies a successful inner command that leaves no git diff
as `no_patch_generated` instead of `command_completed`. When
`--normalized-output` is supplied for that final adapter status, the normalized
run result is written with status `infra_failed` so the run cannot proceed as a
scored/verifier-ready submission.

This directly covers the observed Codex CLI harness risk where an inner agent
can exit `0` with a progress-only final answer and no repository patch.

Revision 1 also preserves unsafe patch rejection as a distinct outcome. Unsafe
content can still produce a sanitized zero-byte patch artifact, but it is not a
true empty-patch run: adapter and ledger metadata now keep
`no_patch_generated: false`, the adapter status remains `unsafe_patch_rejected`,
and the ledger event remains `command_completed_unsafe_patch_rejected`.

## Scope

- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/test_acut_patch_adapter.py`

No ACUT execution, retry, second attempt, broad execution, additional
specialist run, live BARCAROLLE model call, or large batch was started.

## Smoke

- command: `python3 experiments/core_narrative/tools/test_acut_patch_adapter.py`
- mode: no-model scratch workspace
- behavior checked:
  - inner command exits `0`
  - workspace git diff remains empty
  - adapter status is `no_patch_generated`
  - ledger event is `no_patch_generated`
  - normalized status is `infra_failed`
  - unsafe non-empty patch content is rejected as `unsafe_patch_rejected`
  - unsafe rejection ledger event remains
    `command_completed_unsafe_patch_rejected`
  - unsafe rejection adapter and ledger metadata do not mark
    `no_patch_generated: true`
  - unsafe rejection does not receive the empty-patch normalized message

## Follow-Up

Before any new bounded pilot attempt, the coordinator should confirm this
harness hardening is in place and keep broad execution disabled unless a
separate explicit start decision is recorded.
