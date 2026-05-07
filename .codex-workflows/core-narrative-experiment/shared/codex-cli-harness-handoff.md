# Codex CLI Harness Handoff

status: ready_for_focused_adapter_worker
updated: 2026-04-29T16:04:08+08:00

## Summary

Parent-session diagnostics indicate that Codex CLI can replace the current
hand-written inner patch-generation command for ACUT runs, while the existing
outer Barcarolle adapter must remain responsible for task materialization,
budget gates, ledgering, result normalization, verifier execution, and
redaction.

This is a harness direction change only. It does not authorize broad ACUT
execution, retries, specialist runs, or any additional pilot attempt.

## Verified Capability

- Codex CLI supports startup-time config override through repeated
  `-c key=value` arguments.
- A startup-only `model_providers.barcarolle` override with
  `wire_api = "responses"` is accepted.
- The BARCAROLLE provider route can service `codex exec` requests through the
  Responses API when using the required environment variables.
- A temporary `CODEX_HOME` plus temporary project trust config prevents writes
  to the real user Codex profile.
- A temporary `model_catalog_json` can map provider-prefixed active ACUT model
  routes such as `openai/gpt-5.4-mini` and `openai/gpt-5.5` onto Codex
  tool-capable model metadata.
- With a non-interactive base instruction in that temporary model catalog,
  both cheap-tier and frontier-tier model routes successfully executed shell
  commands, modified a file, and verified the result.

## Required Shape For The Replacement Inner Command

The focused adapter worker should implement a Codex CLI patch command that uses
this pattern without recording secrets or full endpoint values:

```text
CODEX_HOME=<run-local-codex-home> \
codex -a never exec \
  --json \
  --ephemeral \
  --ignore-rules \
  --skip-git-repo-check \
  --full-auto \
  --cd <prepared-task-workspace> \
  --model <provider-prefixed-acut-model> \
  -c 'model_provider="barcarolle"' \
  -c 'model_providers.barcarolle={name="Barcarolle", base_url="<from BARCAROLLE_LLM_BASE_URL at runtime>", env_key="BARCAROLLE_LLM_API_KEY", wire_api="responses"}' \
  -c 'model_catalog_json="<run-local-model-catalog.json>"' \
  -o <artifact-dir>/codex_final.txt \
  <experiment prompt>
```

Implementation notes:

- The command may read `BARCAROLLE_LLM_BASE_URL` at runtime, but must not write
  the resolved value to Git, `process.md`, reports, normalized results, prompts,
  or committed artifacts.
- Do not rely on `--ignore-user-config` alone for isolation. Parent diagnostics
  observed local Codex state changes without a temporary `CODEX_HOME`.
- The temporary `CODEX_HOME/config.toml` should mark only the prepared task
  workspace as trusted.
- The temporary model catalog should define provider-prefixed active ACUT model
  slugs and inherit shell/edit tool metadata from the bundled Codex models.
- Override the model base instructions for non-interactive evaluation:
  complete the task using tools, do not emit progress-only final answers, verify
  changed files before finishing, and keep the final answer brief.
- Treat provider `/models` catalog refresh warnings as non-fatal if the explicit
  model route and temporary model catalog are present.

## Required Next Worker

Start a focused implementation worker, suggested name
`codex-cli-harness-adapter`, with owned paths limited to:

- `experiments/core_narrative/tools/**` for the replacement Codex CLI patch
  command and any adapter integration needed to call it.
- `experiments/core_narrative/reports/**` for a concise no-secret harness
  handoff or smoke report.
- `experiments/core_narrative/results/normalized/**` and
  `experiments/core_narrative/results/raw/**` only for bounded smoke artifacts.
- `experiments/core_narrative/results/cost_ledger.jsonl` only if the worker
  performs a BARCAROLLE model-call smoke that must be ledgered.
- The worker's own `.codex-workflows/core-narrative-experiment/workers/**`
  process files.

The worker should first implement or spike the command path, then run the
smallest no-secret smoke that proves the outer adapter can invoke Codex CLI as
the inner patch generator. If a live BARCAROLLE model call is needed for that
smoke, it must be explicitly ledgered and capped. Do not start broad pilot
execution.

## Follow-Up Review

After the focused worker delivers, start a reviewer to check:

- no secret or full endpoint leakage;
- temporary `CODEX_HOME` isolation;
- provider-prefixed model catalog handling for both active model tiers;
- non-interactive instruction behavior;
- budget and ledger compliance for any live smoke call;
- compatibility with the existing outer ACUT adapter contract.
