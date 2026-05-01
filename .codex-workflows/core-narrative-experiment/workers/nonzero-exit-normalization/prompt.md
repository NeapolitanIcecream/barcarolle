# Nonzero-Exit Normalization Worker

You are the focused no-model harness repair worker for the Barcarolle core
narrative experiment.

## Coordination Contract

- Repo: `/Users/chenmohan/gits/barcarolle-wt-nonzero-exit-normalization`
- Branch: `codex/core-exp-nonzero-exit-normalization`
- Process file:
  `.codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization/process.md`
- Read coordinator first:
  `.codex-workflows/core-narrative-experiment/coordinator.md`
- Read relevant worker/review files first:
  - `.codex-workflows/core-narrative-experiment/workers/pilot-004-execution/process.md`
  - `.codex-workflows/core-narrative-experiment/workers/pilot-005-execution/process.md`
  - `.codex-workflows/core-narrative-experiment/workers/pilot-006-execution/process.md`
  - `.codex-workflows/core-narrative-experiment/workers/pilot-006-reviewer/process.md`
  - `.codex-workflows/core-narrative-experiment/workers/empty-patch-gate-r1-reviewer/process.md`
  - `.codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture-r1-reviewer/process.md`
- Do not inspect any `cli.log` file.
- Never record credential values, bearer tokens, resolved secrets, hostnames,
  IP addresses, or full base URL values.
- Do not start any ACUT attempt, live BARCAROLLE model call, retry, second
  attempt, additional specialist ACUT run, broad execution, further pilot
  attempt, or large model-call batch.

## Background

Pilot 004, pilot 005, and pilot 006 are reviewed/integrated. All three are
cheap Click-specialist attempts on `click__rbench__001`. Each completed a
no-model dry run with the reviewed Click specialist context pack injected, then
made exactly one live patch-generation call through the reviewed Codex CLI
harness. All three ended before verifier with adapter status `command_failed`,
inner status `codex_exec_failed`, a zero-byte patch artifact, and one ledger
append. Pilot 006 adds reviewed structured `failure_capture` and
`workspace_patch` metadata showing a non-timeout nonzero exit with no usable
workspace patch, without reading `cli.log`.

The current harness risk is that this reviewed nonzero-exit path may leave the
coordinator depending on raw adapter/inner summaries instead of always getting a
normalized outer result artifact. The next step is a no-model repair to make
the outer adapter normalization/classification stable and reviewer-friendly.

## Task

Implement a focused no-model repair for nonzero-exit inner-command failure
normalization/classification in:

- `experiments/core_narrative/tools/acut_patch_adapter.py`

Required behavior:

- When the inner patch-generation command ends in a nonzero-exit failure and no
  verifier-ready patch is available, the adapter should still emit a normalized,
  no-secret `infra_failed` result artifact.
- Keep this path distinct from:
  - exit-0 empty diff / `no_patch_generated`
  - unsafe patch rejection
  - timeout
  - successful verifier-eligible patch generation
- Preserve the reviewed outer adapter budget/ledger/redaction contract and the
  reviewed inner failure-capture metadata shape.
- Do not append to `experiments/core_narrative/results/cost_ledger.jsonl`; this
  worker is no-model only.
- Do not modify existing pilot 004/005/006 result artifacts.

Tests / smoke:

- Add or update no-model regression coverage in
  `experiments/core_narrative/tools/test_acut_patch_adapter.py`.
- Cover at least the reviewed nonzero-exit/no-patch shape and assert it writes
  normalized `infra_failed` output without misclassifying it as
  `no_patch_generated`.
- Preserve coverage or assertions that exit-0 empty diff and unsafe patch
  rejection remain distinct.
- Run no-model checks only. If a live BARCAROLLE call would be required, stop
  and mark `status: blocked` in `process.md`.

Artifacts:

- Add/update `experiments/core_narrative/reports/acut_adapter_nonzero_exit_normalization.md`
  with the repaired contract, no-model verification, and recommended next
  coordinator gate.
- Optional no-model smoke artifacts may go under
  `experiments/core_narrative/results/raw/nonzero_exit_normalization*/**` and
  `experiments/core_narrative/results/normalized/nonzero_exit_normalization*.json`.

## Delivery

Before finishing:

- Run focused no-model tests or smokes.
- Run `python3 -m py_compile experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/test_acut_patch_adapter.py`
- Run `git diff --check`
- Update the process file with `status: delivered`, changed files,
  verification commands, and handoff summary.
- Commit your changes on this branch.

Do not inspect any `cli.log` file.
