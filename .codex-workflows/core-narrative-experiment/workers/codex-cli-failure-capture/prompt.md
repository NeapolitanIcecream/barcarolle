# Codex CLI Failure Capture Worker

You are the focused no-model harness diagnostic/repair worker for the
Barcarolle core narrative experiment.

## Coordination Contract

- Repo: `/Users/chenmohan/gits/barcarolle-wt-codex-cli-failure-capture`
- Branch: `codex/core-exp-codex-cli-failure-capture`
- Process file:
  `.codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture/process.md`
- Read coordinator first:
  `.codex-workflows/core-narrative-experiment/coordinator.md`
- Read relevant worker process files first:
  `.codex-workflows/core-narrative-experiment/workers/pilot-004-execution/process.md`
  `.codex-workflows/core-narrative-experiment/workers/pilot-005-execution/process.md`
  `.codex-workflows/core-narrative-experiment/workers/pilot-004-reviewer/process.md`
  `.codex-workflows/core-narrative-experiment/workers/pilot-005-reviewer/process.md`
- Do not inspect any `cli.log` file.
- Never record credential values, bearer tokens, resolved secrets, hostnames,
  IP addresses, or full base URL values.
- Do not start any ACUT attempt, live BARCAROLLE model call, retry, second
  attempt, additional specialist ACUT run, broad execution, further pilot
  attempt, or large model-call batch.

## Background

Pilot 004 and pilot 005 are reviewed/integrated. Both were cheap
Click-specialist attempts on `click__rbench__001`, both completed no-model dry
runs with the reviewed Click specialist context pack injected, then each made
exactly one live ACUT model call through the reviewed Codex CLI harness. Both
ended with inner status `codex_exec_failed`, zero-byte `submission.patch`,
normalized `infra_failed`, one ledger append, and no verifier run. These are
not task scoring results.

Coordinator-local triage concluded that the next no-model step is to improve
structured failure capture and artifact preservation in the Codex CLI harness
so future `codex_exec_failed` outcomes are diagnosable without reading
`cli.log`.

## Task

Implement a focused no-model repair/diagnostic for Codex CLI failure capture.

Primary target:

- `experiments/core_narrative/tools/codex_cli_patch_command.py`

Expected behavior:

- When the inner `codex exec` subprocess fails, times out, or exits without a
  usable patch, its JSON summary should preserve a structured, non-secret
  failure record sufficient for review without reading `cli.log`.
- Include only safe metadata such as command exit code, timeout flag, duration,
  stdout/stderr artifact paths when present, bounded redacted stdout/stderr
  tail snippets if useful, and a coarse failure class. Do not include secret
  values, bearer tokens, full base URLs, hostnames, or IP addresses.
- Preserve the existing temporary `CODEX_HOME`, BARCAROLLE provider override,
  provider-prefixed model catalog, non-interactive base-instructions, dry-run,
  specialist context injection, and outer adapter budget/ledger/redaction
  contract.
- Do not append to `experiments/core_narrative/results/cost_ledger.jsonl`; this
  worker is no-model only.
- Do not modify existing pilot 004 or pilot 005 result artifacts.

Tests / smoke:

- Add or update no-model tests using a fake `codex` executable/subprocess path
  that returns a controlled nonzero exit and emits safe stdout/stderr.
- Confirm the resulting summary records the structured failure fields and does
  not require `cli.log`.
- Run only no-model tests/smokes. If a live BARCAROLLE call would be required,
  stop and mark `status: blocked` in `process.md` instead.

Artifacts:

- Add/update `experiments/core_narrative/reports/codex_cli_failure_capture.md`
  with the failure-capture behavior, no-model verification, and next recommended
  coordinator gate.
- Optional no-model smoke artifacts may go under
  `experiments/core_narrative/results/raw/codex_cli_failure_capture*/**` and
  `experiments/core_narrative/results/normalized/codex_cli_failure_capture*.json`.

## Delivery

Before finishing:

- Run focused no-model tests or smokes.
- Run `git diff --check`.
- Update the process file with `status: delivered`, changed files,
  verification commands, and handoff summary.
- Commit your changes on this branch.

Do not inspect any `cli.log` file.
