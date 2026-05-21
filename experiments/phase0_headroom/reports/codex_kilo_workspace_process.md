# Codex Kilo Workspace Process

## 2026-05-21

- Started from branch `codex/restart-benchmark-compiler` at `3998be02`.
- Step 0 preflight passed: `codex` and `kilo` were installed, both help commands worked, endpoint env was present, `G_mini` same-protocol count was `4`, `git diff --check` passed, Phase 0 tool tests passed, and Phase 1 compiler tests passed.
- Commit `f5b47e6c` added multi-ACUT workspace adapter config support, result prefixes, adapter selection, isolated raw/workspace paths, and fake-adapter coverage.
- Commit `fd673bec` added Codex and Kilo candidate workspace ACUT configs for `gpt-5.4-mini`.
- Endpoint proof stopped before scoreable task-solving calls because both harnesses failed proof:
  - `codex_workspace`: `codex_blocked_endpoint_proof`.
  - `kilo_workspace`: `kilo_blocked_endpoint_proof`.

## Cost And Scope

- Scoreable workspace ACUT cells run: `0`.
- Smoke matrix run: `false`.
- Full matrix run: `false`.
- Usage observed from proof probes: `false`.
- Estimated scoreable-run cost: `0.0`.

## Next Smallest Runbook

Resolve endpoint proof before any scoreable workspace ACUT call:

- Codex: provide a Codex CLI transport/config path that completes against the configured endpoint without local subscription auth.
- Kilo: provide a Kilo provider/auth config path that attaches an auth header sourced from `LLM_API_KEY` while using `LLM_BASE_URL`.
