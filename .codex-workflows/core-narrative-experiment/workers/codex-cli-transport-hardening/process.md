# Process

status: delivered
updated: 2026-05-01T19:52:39+08:00

## Summary

Focused no-model transport hardening/diagnostic worker for the Codex CLI inner
patch-generation command after reviewed pilot 006 and pilot 007 both ended
before verifier with a redacted Responses streaming disconnect after five
reconnects.

The worker must inspect only coordinator-approved workflow files, structured
raw/normalized artifacts, run manifests, and relevant tool source/tests. It must
not inspect any `cli.log` file and must not start any ACUT attempt, live
BARCAROLLE model call, retry, second attempt, additional specialist run, broad
execution, further pilot attempt, or large model-call batch.

## Owned Paths

- `experiments/core_narrative/tools/codex_cli_patch_command.py`
- `experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- `experiments/core_narrative/tools/acut_patch_adapter.py` if needed for a
  tightly scoped integration guard
- `experiments/core_narrative/tools/test_acut_patch_adapter.py` if needed
- `experiments/core_narrative/reports/codex_cli_transport_hardening.md`
- `experiments/core_narrative/results/raw/codex_cli_transport_hardening*/**`
- `experiments/core_narrative/results/normalized/codex_cli_transport_hardening*.json`
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening/**`

## Branch / Worktree

- Branch: `codex/core-exp-codex-cli-transport-hardening`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening`
- tmux session: `bcx-codex-cli-transport-hardening`

## Current Blockers

None.

## Delivery Summary

Implemented a no-model/static transport mitigation for the reviewed Codex CLI
inner patch command:

- `codex_cli_patch_command.py` now classifies the known redacted Responses
  `/responses` stream-disconnect signature as
  `responses_streaming_disconnect`, including reconnect count metadata without
  recording message bodies, full URLs, hostnames, IP addresses, credentials, or
  bearer tokens.
- `acut_patch_adapter.py` now reads the existing inner `--summary-output` file
  when it is from `codex_cli_patch_command` and carries the sanitized inner
  failure class into raw adapter output, future normalized `infra_failed`
  metadata, and future ledger metadata. Adapter status, ledger event, cost
  accounting, verifier policy, retry policy, and primary-attempt policy are
  unchanged.
- Required report written at
  `experiments/core_narrative/reports/codex_cli_transport_hardening.md`.

No non-streaming Codex CLI transport switch was established from local no-model
discovery (`codex exec --help`, `codex features list`,
`codex debug models --bundled`), so this delivery is the conservative
machine-readable classifier/fallback path.

No ACUT attempt, live BARCAROLLE model call, retry, second attempt, additional
specialist run, broad execution, further pilot attempt, large model-call batch,
or cost-ledger append occurred. No `cli.log` file was inspected.

## Files Changed

- `experiments/core_narrative/tools/codex_cli_patch_command.py`
- `experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/test_acut_patch_adapter.py`
- `experiments/core_narrative/reports/codex_cli_transport_hardening.md`
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening/process.md`

## Verification

- `python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py`
  passed, 5 tests.
- `python3 experiments/core_narrative/tools/test_acut_patch_adapter.py`
  passed, 4 tests.
- `PYTHONPYCACHEPREFIX=/tmp/barcarolle-pycache python3 -m py_compile experiments/core_narrative/tools/codex_cli_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py`
  passed.
- `git diff --check` passed.
- Scoped no-secret scan over 6 changed files passed with zero findings.

## Activity Log

- 2026-05-01T19:43:15+08:00: Worker dispatched for focused no-model Codex CLI
  transport hardening. Read coordinator and relevant worker `process.md` files
  first. Do not inspect `cli.log`.
- 2026-05-01T19:52:39+08:00: Delivered no-model static classifier and adapter
  metadata propagation for the known Responses streaming disconnect. Scoped
  tests and static checks passed. No live execution or ledger append occurred.

## Handoff

Next coordinator step should be focused no-model/static review of this worker
delivery before integration or any later execution hypothesis. If reviewed and
integrated, any later live execution still requires a separate explicit
coordinator decision.
