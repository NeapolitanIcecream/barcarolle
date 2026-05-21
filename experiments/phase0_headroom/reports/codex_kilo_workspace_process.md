# Codex Kilo Workspace Process

## 2026-05-21

- Started from branch `codex/restart-benchmark-compiler` at `3998be02`.
- Step 0 preflight passed: `codex` and `kilo` were installed, both help commands worked, endpoint env was present, `G_mini` same-protocol count was `4`, `git diff --check` passed, Phase 0 tool tests passed, and Phase 1 compiler tests passed.
- Commit `f5b47e6c` added multi-ACUT workspace adapter config support, result prefixes, adapter selection, isolated raw/workspace paths, and fake-adapter coverage.
- Commit `fd673bec` added Codex and Kilo candidate workspace ACUT configs for `gpt-5.4-mini`.
- Initial endpoint proof stopped before scoreable task-solving calls because both harnesses failed proof:
  - `codex_workspace`: `codex_blocked_endpoint_proof`.
  - `kilo_workspace`: `kilo_blocked_endpoint_proof`.
- Later isolated diagnosis resolved the Codex endpoint proof blocker. The working Codex shape is a custom `model_provider` with `env_key="LLM_API_KEY"`, `/v1` `base_url`, `wire_api="responses"`, and `supports_websockets=false`. This does not retroactively run or score any workspace task.
- Later isolated diagnosis also resolved the Kilo endpoint proof blocker. The working Kilo shape is an `openai-compatible` provider with `apiKey: "{env:LLM_API_KEY}"`, a `/v1` `baseURL`, a custom `gpt-5.4-mini` model entry, and `--model openai-compatible/gpt-5.4-mini`. A temporary workspace dry-run edited only the requested file, but no scoreable workspace ACUT cell was run.
- Command templates were added for both adapters through repo-local wrapper scripts. Non-scoreable temporary git workspace dry-runs passed for both wrappers: each changed only `target.txt` to `PONG\n`.
- Smoke ran sequentially for both adapters on `toolz__hist__002` and `click__rbench__001`.
- Smoke terminal statuses: Codex `verified_pass`, `verified_fail`; Kilo `acut_harness_error`, `verified_fail`.

## Cost And Scope

- Workspace ACUT smoke cells run: `4` scheduled, `3` scoreable.
- Smoke matrix run: `true`.
- Full matrix run: `false`.
- Usage observed from harness output: `false`.
- Estimated scoreable-run cost: `2.0` for smoke, using a conservative `USD 0.50` per-cell estimate.

## Next Smallest Runbook

Resolve the full-matrix result protocol before any full matrix:

- The smoke gate produced at least one scoreable cell per harness, so full matrix is not blocked by the Step 5 scoreability rule.
- Before running full matrix, ensure full-run result rows do not double-count smoke rows unless smoke cells are intentionally reused.
