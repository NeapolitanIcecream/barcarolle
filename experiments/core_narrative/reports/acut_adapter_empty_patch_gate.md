# ACUT Adapter Empty Patch Gate

status: implemented_no_model_smoke_passed
updated: 2026-04-30T11:28:00+08:00

## Summary

The ACUT adapter now classifies a successful inner command that leaves no git
diff as `no_patch_generated` instead of `command_completed`. When
`--normalized-output` is supplied, the normalized run result is written with
status `infra_failed` so the run cannot proceed as a scored/verifier-ready
submission.

This directly covers the observed Codex CLI harness risk where an inner agent
can exit `0` with a progress-only final answer and no repository patch.

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

## Follow-Up

Before any new bounded pilot attempt, the coordinator should confirm this
harness hardening is in place and keep broad execution disabled unless a
separate explicit start decision is recorded.
