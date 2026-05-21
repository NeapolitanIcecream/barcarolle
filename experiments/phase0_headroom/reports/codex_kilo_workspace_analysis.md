# Codex Kilo Workspace Analysis

The Codex/Kilo cross-harness workspace matrix completed on 2026-05-21 using
the same endpoint model, `gpt-5.4-mini`, through `LLM_BASE_URL + LLM_API_KEY`.
This is a realistic harness comparison, not a pure harness-effect estimate:
both harnesses share the endpoint model and task set, but their CLI runtime,
tool policy, prompts, and completion behavior differ.

## Matrix Result

- Scheduled cells: `20`.
- Scoreable cells: `9`.
- Terminal statuses: `verified_pass=4`, `verified_fail=5`,
  `policy_violation=5`, `acut_harness_error=6`.
- Estimated incremental cost: `USD 10.0`, using the conservative `USD 0.50`
  per-cell estimate because neither harness exported billable usage.
- Median recorded latency: `87.604` seconds.

Per harness:

- `codex_workspace`: `10` cells, `6` scoreable, `3` verified pass, `3`
  verified fail, `4` policy violations.
- `kilo_workspace`: `10` cells, `3` scoreable, `1` verified pass, `2`
  verified fail, `1` policy violation, `6` ACUT harness errors.

Per split:

- `B_real`: `6` cells, `4` scoreable, pass rate `1.0`.
- `W_real`: `6` cells, `2` scoreable, pass rate `0.0`.
- `G_mini`: `8` cells, `3` scoreable, pass rate `0.0`.

The matrix technically has `G_mini -> W_real` and
`G_mini + B_real -> W_real` coverage flags available, but the effective sample
is still too small and too harness-sensitive for a predictive-validity claim.
`mae`, `rmse`, and `brier_score` remain
`not_applicable_underpowered`.

## Kilo Non-Interactive Check

The timeout pattern is not endpoint failure and not proof that Kilo never works.
Kilo completed scoreable runs for `toolz__hist__003`,
`click__rbench__001`, `click__rbench__002`, and `click__rbench__003`. Those
runs produced full JSON event streams and normal adapter durations of about
`26.8`, `30.5`, `29.6`, and `109.4` seconds.

For timeout rows, the solver workspaces still contain normal-looking diffs.
Examples include `toolz/functoolz.py`, `toolz/itertoolz.py`,
`click/testing.py`, and other implementation files. This means Kilo often did
real workspace work before the outer adapter timeout classified the cell as
`acut_harness_error`.

The installed Kilo `7.3.1` help and official CLI docs agree that
`kilo run --auto "message"` is the intended autonomous/non-interactive mode.
The current wrapper uses that shape, with an isolated temporary HOME/XDG config,
`--pure`, `--auto`, `--format json`, `--model
openai-compatible/gpt-5.4-mini`, `--dir <workspace>`, and an attached task
statement. A local side check also showed that `--command` dispatches Kilo
internal commands rather than shell commands, so it is not the missing
non-interactive invocation for task solving.

The most likely Kilo-specific issue is process completion: at least one
preserved timeout log reached `suggestion.shown` and `session.idle` without the
`kilo run` process exiting before the adapter timeout. A narrow follow-up should
test either a stricter terminal prompt or wrapper-side JSON event handling that
recognizes a final/idle state without accepting partial work prematurely.

Docs consulted:

- `https://kilo.ai/docs/code-with-ai/platforms/cli`
- `https://kilo.ai/docs/code-with-ai/platforms/cli-reference`

## Decision

The result supports continuing Barcarolle as a regression-benchmark compiler.
It does not support moving to `proceed_predictive` or claiming a validated
generic-comparator predictor. The next useful work is to reduce Kilo harness
timeouts and policy violations before scaling this comparison.
