# Codex Kilo Workspace Preflight

Status: `workspace_acut_matrix_complete`.

- Branch: `codex/restart-benchmark-compiler`.
- HEAD before final matrix commit: `e0523984`.
- Comparison design: `same_model_cross_harness`.
- Preferred model: `gpt-5.4-mini`.
- Adapter config:
  `experiments/phase0_headroom/configs/acut_workspace_adapters.yaml`.
- Matrix config:
  `experiments/phase0_headroom/configs/codex_kilo_workspace_matrix.yaml`.
- Required endpoint env present: `true`.
- Endpoint host hash: `9952174049b2`.
- Local subscription fallback: `disabled`.
- Provider fallback outside `LLM_BASE_URL` and `LLM_API_KEY`: `disabled`.
- Generic same-protocol scoreable tasks: `4`.

## Eligibility

- `codex_workspace`: `codex_eligible`; full matrix scoreable cells `6/10`.
- `kilo_workspace`: `kilo_eligible`; full matrix scoreable cells `3/10`.

## Endpoint Evidence

The initial Codex proof was tested with a temporary `CODEX_HOME`,
`--ignore-user-config`, `openai_base_url` sourced from `LLM_BASE_URL`, and
`OPENAI_API_KEY` mapped from `LLM_API_KEY`. The non-scoreable proof prompt did
not complete because the CLI attempted a Responses websocket/stream path and
ended with a stream completion failure. Later diagnosis showed this was a
configuration issue, not endpoint unavailability.

The working Codex pattern sets a custom model provider with
`env_key="LLM_API_KEY"`, uses a `/v1` `base_url`, sets
`wire_api="responses"`, and sets `supports_websockets=false`.

The initial Kilo proof reached the configured endpoint path but failed because
the attempted mapping did not attach an authentication header. Later diagnosis
showed that Kilo is endpoint-capable when configured through the documented
`openai-compatible` provider shape with `apiKey: "{env:LLM_API_KEY}"`, a `/v1`
`baseURL`, a custom `gpt-5.4-mini` model entry, and `--model
openai-compatible/gpt-5.4-mini`.

Detailed notes:

- `experiments/phase0_headroom/reports/codex_endpoint_failure_diagnosis.md`
- `experiments/phase0_headroom/reports/kilo_endpoint_diagnosis.md`

## Workspace Command Template Dry-Run

Both adapters have configured command templates that invoke repo-local wrapper
scripts through `uv run --project experiments/phase0_headroom`.

- `codex_workspace`: temporary git workspace dry-run returned code `0`, changed
  only `target.txt`, and left `target.txt` as `PONG\n`.
- `kilo_workspace`: temporary git workspace dry-run returned code `0`, changed
  only `target.txt`, and left `target.txt` as `PONG\n`.

These dry-runs are not scoreable ACUT cells. They prove that each wrapper reads
a statement file, uses isolated endpoint config, and mutates the supplied
workspace.

## Matrix Result

- Scheduled cells: `20`.
- Scoreable cells: `9`.
- Terminal status counts: `verified_pass=4`, `verified_fail=5`,
  `policy_violation=5`, `acut_harness_error=6`.
- Codex scoreable cells: `6/10`.
- Kilo scoreable cells: `3/10`.
- Estimated matrix cost: `USD 10.0` using a conservative `USD 0.50` per-cell
  estimate because harness usage is not imported.
- Solver workspaces contained no tracked hidden verifier material in the
  checked paths.

## Kilo Non-Interactive Note

Kilo's endpoint and command shape are proven enough to run real cells, but its
non-interactive process exit behavior is unstable for this harness. The docs
and local help support `kilo run --auto "message"` as autonomous mode. The
current wrapper uses that mode. The observed blocker is that several Kilo runs
perform edits and then fail to exit before the adapter timeout.
