# Codex CLI Transport Hardening Worker

You are the focused no-model implementation/diagnostic worker for the
Barcarolle core narrative experiment.

Repository/worktree:
`/Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening`

## Coordination Contract

Read first:

1. `.codex-workflows/core-narrative-experiment/coordinator.md`
2. `.codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening/process.md`
3. `.codex-workflows/core-narrative-experiment/workers/pilot-006-execution/process.md`
4. `.codex-workflows/core-narrative-experiment/workers/pilot-006-reviewer/process.md`
5. `.codex-workflows/core-narrative-experiment/workers/pilot-007-execution/process.md`
6. `.codex-workflows/core-narrative-experiment/workers/pilot-007-reviewer/process.md`

Do not inspect any `cli.log` file in any worktree or artifact tree.

This is a no-model/static harness-hardening step. Do not start any ACUT attempt,
live BARCAROLLE model call, retry, second attempt, additional specialist ACUT
run, broad execution, further pilot attempt, or large model-call batch. Do not
append to the main cost ledger.

Never record credential values, bearer tokens, resolved secrets, hostnames, IP
addresses, or full base URL values.

## Background

Reviewed pilot 006 (`cheap-click-specialist`) and reviewed pilot 007
(`cheap-generic-swe`) both ran on `click__rbench__001` through the reviewed
Codex CLI harness using provider-prefixed route `openai/gpt-5.4-mini`. Each
made exactly one ledgered live adapter/model-call attempt, then ended before
verifier with:

- inner Codex CLI status `codex_exec_failed`
- structured failure class `nonzero_exit`
- zero-byte/no usable workspace patch
- no retry, no second attempt, no broad execution, and no batch

The treatment routing behaved as expected: pilot 006 injected the reviewed
Click specialist context pack; pilot 007 excluded it. The shared structured
failure signal is a redacted Responses streaming disconnect after five
reconnects, independent of generic-vs-specialist treatment. This is not a
scorable ACUT capability result.

## Task

Perform one focused no-model transport-hardening pass for the inner Codex CLI
patch command.

Inspect:

- `experiments/core_narrative/tools/codex_cli_patch_command.py`
- `experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- `experiments/core_narrative/tools/acut_patch_adapter.py` only if a tightly
  scoped integration guard is needed
- `experiments/core_narrative/tools/test_acut_patch_adapter.py` only if needed
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml` as
  read-only planning context
- structured pilot 006/007 raw/normalized/ledger artifacts, excluding all
  `cli.log`

Deliver one of these outcomes:

1. Implement a safe no-model-reviewed mitigation in the harness that can be
   reviewed before any later live ACUT attempt. Examples include a documented or
   locally discoverable non-streaming Codex CLI transport/profile, a bounded
   output-cap profile that preserves the 2x2 control contract, or a static
   guard/fallback that classifies the known streaming-disconnect failure before
   wasting repeated ACUT budget.
2. If no safe mitigation can be established without a live BARCAROLLE call or
   external user input, write a precise no-secret blocker explaining what is
   missing and why another live attempt is not justified yet.

Keep the 2x2 design controls intact: same harness, same task budget/turn cap
/test cap/retry policy across comparable cells, one primary attempt policy, no
gold patches, no hidden hints, no post-hoc tuning, and no undeclared history
mining.

## Required Artifact

Write `experiments/core_narrative/reports/codex_cli_transport_hardening.md`
with:

- method and inputs, explicitly noting `cli.log` was not inspected
- structured evidence from pilot 006 and pilot 007
- mitigation implemented or blocker recorded
- impact on the next execution hypothesis
- verification run
- no-secret/redaction notes

## Verification

Run no-model/static checks only. Prefer:

- `python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- `python3 experiments/core_narrative/tools/test_acut_patch_adapter.py`
- `PYTHONPYCACHEPREFIX=/tmp/barcarolle-pycache python3 -m py_compile experiments/core_narrative/tools/codex_cli_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py`
- `git diff --check`
- scoped no-secret scan over changed files and any new no-model artifacts

Do not contact BARCAROLLE and do not run a live patch-generation attempt.

## Output

Update
`.codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening/process.md`
with `status: delivered` or `status: blocked`, a concise summary, files changed,
verification, and handoff. If delivered, commit your changes on branch
`codex/core-exp-codex-cli-transport-hardening`.
