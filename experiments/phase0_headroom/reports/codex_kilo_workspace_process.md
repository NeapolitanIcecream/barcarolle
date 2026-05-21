# Codex Kilo Workspace Process

## 2026-05-21

- Started from branch `codex/restart-benchmark-compiler` at `3998be02`.
- Step 0 preflight passed: `codex` and `kilo` were installed, both help
  commands worked, endpoint env was present, `G_mini` same-protocol count was
  `4`, `git diff --check` passed, Phase 0 tool tests passed, and Phase 1
  compiler tests passed.
- Commit `f5b47e6c` added multi-ACUT workspace adapter config support, result
  prefixes, adapter selection, isolated raw/workspace paths, and fake-adapter
  coverage.
- Commit `fd673bec` added Codex and Kilo candidate workspace ACUT configs for
  `gpt-5.4-mini`.
- Initial endpoint proof stopped before scoreable task-solving calls because
  both harnesses failed proof:
  - `codex_workspace`: `codex_blocked_endpoint_proof`.
  - `kilo_workspace`: `kilo_blocked_endpoint_proof`.
- Commit `8041be76` recorded the Codex endpoint lesson. The working Codex shape
  is a custom `model_provider` with `env_key="LLM_API_KEY"`, `/v1` `base_url`,
  `wire_api="responses"`, and `supports_websockets=false`.
- Commit `78c761bf` proved the Kilo endpoint/provider configuration. The
  working Kilo shape is an `openai-compatible` provider with `apiKey:
  "{env:LLM_API_KEY}"`, a `/v1` `baseURL`, a custom `gpt-5.4-mini` model
  entry, and `--model openai-compatible/gpt-5.4-mini`.
- Commit `57e1a945` added repo-local Codex and Kilo workspace wrapper scripts.
  Non-scoreable temporary git workspace dry-runs passed for both wrappers:
  each changed only `target.txt` to `PONG\n`.
- Commit `e0523984` ran the 4-cell smoke subset and committed smoke artifacts.
  Smoke terminal statuses were Codex `verified_pass`, Codex `verified_fail`,
  Kilo `acut_harness_error`, and Kilo `verified_fail`.
- The full matrix then reused existing smoke rows intentionally and ran the
  remaining cells per adapter, sequentially and within budget.
- Commit `0cc85197` recorded the 20-cell matrix outputs, full analysis, updated
  preflight status, and Phase 0 decision memo.

## Full Matrix

- Scheduled cells: `20`.
- Scoreable cells: `9`.
- Terminal statuses: `verified_pass=4`, `verified_fail=5`,
  `policy_violation=5`, `acut_harness_error=6`.
- `codex_workspace`: `10` cells, `6` scoreable.
- `kilo_workspace`: `10` cells, `3` scoreable.
- Estimated incremental cost: `USD 10.0`.
- Usage observed from harness output: `false`.

## Kilo Non-Interactive Side Check

The Kilo timeout question was checked without modifying the user's Kilo
configuration. All probes used temporary HOME/XDG state or existing ignored
experiment workspaces.

Findings:

- Official docs and local `kilo run --help` both identify `--auto` as the
  autonomous/non-interactive mode.
- The installed `kilo 7.3.1` help does not expose
  `--dangerously-skip-permissions`, even though the online command reference
  currently lists it. The local binary help is the safer source for this host.
- `--command` is not a shell-command escape hatch for task solving. A side
  probe showed it dispatches Kilo internal commands such as `init`, `review`,
  `local-review`, `local-review-uncommitted`, and `kilo-config`.
- Kilo is not always timing out: four Kilo cells completed normally and
  produced JSON event streams.
- Timeout workspaces still contain implementation diffs, so several timeout
  rows represent non-exiting Kilo sessions after real work rather than no-op
  failures.
- A preserved timeout log for `click__rbench__004` reached
  `suggestion.shown` and `session.idle`; the outer adapter later classified the
  run as `acut_harness_error` when `kilo run` did not exit before the 900s
  timeout.

## Next Smallest Runbook

Do not scale the Codex/Kilo comparison until Kilo completion behavior is
isolated. The next bounded experiment should use a non-scoreable workspace and
compare:

- the current wrapper prompt;
- a stricter prompt that tells Kilo to produce one final answer and exit without
  suggestions, follow-up questions, or plan mode;
- optional wrapper-side JSON event monitoring that treats a clear terminal
  state as completion only when a diff has been captured and no tool call is
  running.

## Final Hygiene

- `git diff --check`: passed.
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`:
  `38 passed`.
- `uv run --project experiments/phase1_compiler pytest -q`: `4 passed`.
- `git status --short`: clean after committing tracked artifacts.
- Ignored paths include `.venv`, caches, raw logs, cloned external repos, and
  solver/verifier workspaces; none are staged.
