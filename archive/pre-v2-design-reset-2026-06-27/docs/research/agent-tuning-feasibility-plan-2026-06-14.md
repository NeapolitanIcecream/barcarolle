# Agent Tuning Feasibility Plan 2026-06-14

Status: Phase 1 preparation plan for Agent Tuning Demo Phase 2. This is not a
tuning experiment and does not start GEPA, DSPy, Phoenix, or another optimizer.

## Gating Question

Phase 1 must answer whether tuner-produced text artifacts can be injected into
real Codex/Kilo-style workspace Agents and whether Barcarolle can observe a
behavior difference caused by those artifacts.

## Current Execution Boundary

Barcarolle already has reusable workspace execution primitives:

- `experiments/phase0_headroom/tools/workspace_acut_run.py` creates clean solver
  workspaces at the task base commit, writes solver-visible task statements,
  invokes an adapter command, captures `git diff`, replays the diff in a fresh
  verifier workspace, injects hidden oracle material only there, and records
  sanitized submission/verifier fields.
- `experiments/agent_selection_demo/tools/agent_selection_demo.py` builds
  Codex/Kilo adapter configs, enforces `LLM_BASE_URL` plus `LLM_API_KEY`, records
  cost/usage summaries, and persists score tables/reports.
- `experiments/phase0_headroom/tools/codex_workspace_adapter.py` runs
  `codex exec` with an isolated `CODEX_HOME`, a custom LLM endpoint provider,
  no approval prompts, and the real solver workspace as `--cd`.
- `experiments/phase0_headroom/tools/kilo_workspace_adapter.py` runs
  `kilo run` with isolated `HOME`/`XDG_*` roots, a generated OpenAI-compatible
  provider config, and the real solver workspace as `--dir`.
- `experiments/phase0_headroom/tools/llm_endpoint_proxy.py` strips paid endpoint
  secrets from child environments and forwards only through the configured
  `LLM_BASE_URL`/`LLM_API_KEY` endpoint.

The missing primitive is pre-Agent artifact materialization. `run_workspace_cell`
archives the source tree, initializes a Git base commit, writes
`.barcarolle/statement.md`, and then invokes the adapter. There is no hook today
to add `AGENTS.md`, skills, Kilo rules, or policy snippets before the Agent
starts. Phase 1 therefore needs a narrow helper that validates an artifact,
writes only declared workspace-relative paths, hashes deterministic content, and
emits a sanitized injection record.

## Phase 1 Package Plan

1. Context audit: document reusable runner paths, injection gap, observable
   fields, paid-call boundary, and artifact hygiene.
2. Tuning surface inventory: classify Codex/Kilo `AGENTS.md`, skills, Kilo
   rules, harness prompt/context, runtime policy, and model selection knobs.
3. Artifact schema and helper: define JSON schemas for tuning artifacts and
   injection records; implement deterministic hashing and safe materialization.
4. Proof-of-injection smoke tests: use no-paid local LLM endpoint request capture
   against real Codex/Kilo CLIs where feasible. Record sanitized loaded/not
   loaded evidence; do not commit raw request bodies or transcripts.
5. Behavior-change smoke test: use two controlled instruction variants against
   the same no-paid smoke harness and record whether the real Agent request
   context changes in the expected direction.
6. Tuner compatibility: compare GEPA, Phoenix Prompt Learning, DSPy, Opik,
   TextGrad, ProTeGi, SKVM/SkillRT, and SkillOpt-style systems as artifact
   proposers or tuner-native fallbacks.
7. Readiness gate: write a final closeout and update `PROCESS.md` with only the
   current effective decision and links.

## Evidence Standard

Passing Phase 1 requires at least one reliable real-Agent artifact-injection
path and at least one observable behavior-change path. If one surface is
unsupported or flaky, record that status and continue testing other surfaces.
If all real-Agent artifact injection fails, recommend a tuner-native fallback
instead of proceeding with Codex/Kilo artifact tuning.

Proof may be no-paid: the planned smoke harness can run real CLI adapters
against a local fake OpenAI-compatible endpoint and inspect sanitized request
summaries for injected fixed phrases. This proves the CLI assembled a model
request containing the artifact text without spending LLM tokens.

## Phase 2 Boundary If Ready

If Phase 1 passes, Phase 2 may attempt this narrow claim:

> Barcarolle can provide target-repo feedback to an external optimizer/proposer,
> materialize the selected repo-specific instruction artifact into a real
> workspace Coding Agent, and validate before/after behavior under the same
> hidden-verifier protocol.

Phase 2 may not claim model fine-tuning, full opaque-Agent optimization,
general predictive validity, or holdout improvement before an actual frozen
before/after run.

## Leakage And Hygiene Rules

- No Holdout hidden details, hidden test bodies, raw prompts, raw completions, or
  raw Agent transcripts may be visible to optimizers/proposers.
- Raw CLI stdout/stderr, request captures, solver workspaces, verifier
  workspaces, endpoint secrets, and caches remain ignored/local-only.
- Committed artifacts are limited to schemas, helper code, tests, sanitized
  reports, and sanitized aggregate JSON.
- Any paid smoke test, if later unavoidable, must use only `LLM_BASE_URL` and
  `LLM_API_KEY`, record cost, and commit only summaries.
