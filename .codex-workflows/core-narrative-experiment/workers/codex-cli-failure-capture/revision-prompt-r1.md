# Codex CLI Failure Capture Revision 1

You are the focused no-model revision worker for the Barcarolle core narrative
experiment.

## Coordination Contract

- Repo: `/Users/chenmohan/gits/barcarolle-wt-codex-cli-failure-capture`
- Branch: `codex/core-exp-codex-cli-failure-capture`
- Process file:
  `.codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture/process.md`
- Review feedback:
  `.codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture/review-feedback-r1.md`

Read first:

- `.codex-workflows/core-narrative-experiment/coordinator.md`
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture/process.md`
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture/review-feedback-r1.md`

Do not inspect any `cli.log` file.

Never record credential values, bearer tokens, resolved secrets, hostnames, IP
addresses, or full base URL values.

Do not start any ACUT attempt, live BARCAROLLE model call, retry, second
attempt, additional specialist ACUT run, broad execution, further pilot attempt,
or large model-call batch.

## Task

Fix the review findings from `review-feedback-r1.md`.

Required closure:

1. Broaden failure-capture hostname redaction so it does not rely on a narrow
   hard-coded suffix list, and make the `hostnames_redacted: true` policy true
   for structured `failure_capture`, redacted stdout/stderr artifacts, and
   bounded tail snippets.
2. Add no-model regression coverage for `timeout` and `unsafe_patch_content`
   failure classes.
3. Add assertions that redacted stdout/stderr artifact contents do not contain
   credential values, bearer-token-shaped strings, full URLs, hostname-shaped
   values, or IP address-shaped values.
4. Preserve existing temporary `CODEX_HOME`, BARCAROLLE provider override,
   provider-prefixed model catalog, non-interactive base instructions, dry-run,
   specialist context injection, and outer adapter budget/ledger/redaction
   contract.
5. Do not append to `experiments/core_narrative/results/cost_ledger.jsonl`.

## Verification

Run only no-model tests/static checks:

- `python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- `python3 experiments/core_narrative/tools/test_acut_patch_adapter.py`
- `python3 -m py_compile experiments/core_narrative/tools/codex_cli_patch_command.py experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- `git diff --check`

If a live BARCAROLLE call would be required, stop and mark `status: blocked`.

## Delivery

Before finishing:

- Update `experiments/core_narrative/reports/codex_cli_failure_capture.md` with
  the revision summary and verification.
- Update the process file with `status: delivered`, changed files, no-model
  verification, and handoff.
- Commit your changes on this branch.

Do not inspect any `cli.log` file.
