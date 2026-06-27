# Barcarolle Agent Instructions

These instructions apply to all coding-agent sessions in this repository.

## Mission

Barcarolle compiles target-repository benchmarks for coding-agent evaluation
and tuning. The system should stay small, auditable, and centered on:

- task supply and certification;
- isolated Agent execution;
- hidden-oracle verification;
- normalized result storage;
- task selection under rolling-origin evaluation;
- reports that separate evidence from claims.

The tested Agent owns its model, harness, prompts, skills, tools, retrieval,
edit loop, retries, public-test policy, and runtime budget.

Barcarolle owns the benchmark boundary:

- create a clean solver workspace at the task base commit;
- provide only solver-visible task material;
- invoke the configured Agent harness;
- capture the final workspace diff;
- enforce benchmark-side rules;
- replay the diff in a fresh verifier workspace;
- inject private oracle material only in the verifier workspace;
- run the hidden check;
- record terminal status, cost, latency, failure labels, and sanitized
  artifacts.

Scoreable Agent runs should use a workspace adapter that lets the Agent modify a
real worktree while Barcarolle captures the resulting `git diff`.

## Engineering Defaults

Prefer mature libraries, standard tooling, and direct data contracts over
bespoke frameworks or broad abstractions. Custom code is appropriate for
benchmark boundaries, reproducibility, artifact hygiene, Agent isolation,
hidden-oracle protection, and auditability.

Keep core concepts simple. Current data vocabulary is `Task`, `Check`,
`Workspace`, `Result`, `Selector`, `RollingOrigin`, `Task Pool`,
`Benchmark Selection`, and `Agent Results`.

Use current module names consistently:

- `Records`
- `Task Pool`
- `Verification`
- `Workspace`
- `Result Store`
- `Selection`
- `Reporting`
- `Runner`

Prefer the module vocabulary above; avoid alternate module names.

Use `uv` for repo-local Python tooling.

## LLM Endpoint Rule

All paid LLM or Agent calls must use:

```text
LLM_BASE_URL
LLM_API_KEY
```

If either variable is missing, source `~/.zshrc` and check again before making
the call. Do not use subscription auth, `OPENAI_API_KEY`, OpenRouter variables,
or provider-specific variables unless the user explicitly changes this rule.

If a harness cannot be proven to use the required endpoint, stop before paid
task-solving calls and write a blocker report.

## Artifact Hygiene

Do not commit secrets, full raw prompts, raw completions, raw Agent transcripts,
solver workspaces, verifier workspaces, cloned external repositories, `.venv`,
caches, or large raw outputs.

Store raw artifacts only under ignored paths. Commit small sanitized indexes,
summaries, reports, schemas, and digests.

Before committing experiment or infrastructure changes, run the scoped tests
relevant to the touched area and `git diff --check`.

## Process Notes

Read `PROCESS.md` after this file when working on experiments, paid validation,
benchmark design, selector research, Agent adapters, or research
interpretation.

Keep `PROCESS.md` current and short. Update it when the active research
direction, paid-call boundary, claim boundary, or cross-session handoff state
changes.

## Runbook Execution

When executing a runbook, keep advancing until a real stop condition is reached.
Record completed work, blockers, decisions, and recommended next actions in the
final report.

Do not create the next runbook unless the user explicitly asks for it.

Commit runbook work in focused steps with enough evidence to show each step is
complete.
