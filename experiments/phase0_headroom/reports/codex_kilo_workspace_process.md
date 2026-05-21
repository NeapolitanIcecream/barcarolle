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

## Cost And Scope

- Scoreable workspace ACUT cells run: `0`.
- Smoke matrix run: `false`.
- Full matrix run: `false`.
- Usage observed from proof probes: `false`.
- Estimated scoreable-run cost: `0.0`.

## Next Smallest Runbook

Resolve remaining endpoint proof and workspace command setup before any scoreable workspace ACUT call:

- Codex: convert the working custom-provider proof into a workspace command template that mutates `{workspace}` and captures `git diff`.
- Kilo: provide a Kilo provider/auth config path that attaches an auth header sourced from `LLM_API_KEY` while using `LLM_BASE_URL`.
