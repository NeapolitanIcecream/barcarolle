# Process

status: working
updated: 2026-04-29T16:08:35+08:00

## Summary

Focused worker is starting from the parent-session Codex CLI harness handoff.
The goal is to implement or spike replacing only the inner ACUT
patch-generation agent with `codex exec`, while keeping the outer Barcarolle
adapter responsible for task materialization, budget gate, cost ledger,
redaction, normalized result, verifier, and reviewer handoff.

No broad ACUT execution, retry, second attempt, specialist ACUT run, additional
pilot attempt, or large model-call batch is authorized.

## Owned Paths

- `experiments/core_narrative/tools/**` for the Codex CLI inner patch command
  and any minimal adapter integration needed to call it
- `experiments/core_narrative/reports/codex_cli_harness_adapter.md`
- `experiments/core_narrative/results/normalized/codex_cli_harness_adapter*.json`
- `experiments/core_narrative/results/raw/codex_cli_harness_adapter*/**`
- `experiments/core_narrative/results/cost_ledger.jsonl` only if a live
  BARCAROLLE model-call smoke is performed and ledgered
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-harness-adapter/**`

## Branch / Worktree

- Branch: `codex/core-exp-codex-cli-harness-adapter`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-codex-cli-harness-adapter`

## Current Blockers

None at dispatch. If the worker determines a live BARCAROLLE model call is
required and cannot be capped, ledgered, and redacted within the existing
contract, it must set `status: blocked` before making the call.

## Handoff

Read `.codex-workflows/core-narrative-experiment/coordinator.md` and
`.codex-workflows/core-narrative-experiment/shared/codex-cli-harness-handoff.md`
first. Do not inspect any `cli.log` file. Deliver only after a minimal
no-secret smoke is recorded and the process file lists changed files, checks,
whether any live BARCAROLLE model call occurred, and the reviewed-ready command
template with no secret values or full endpoint values.
