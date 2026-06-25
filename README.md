# Barcarolle

Barcarolle is a target-repository benchmark compiler for coding-agent
evaluation and tuning.

The project is in proposal review and v2 design. The current priority is to
turn the existing evidence and prototype code into a clean, low-abstraction
system for:

- generating or importing repository-specific tasks;
- certifying each task with an auditable check;
- running complete coding Agents in isolated workspaces;
- caching reusable `Agent x Task` results;
- selecting benchmark tasks under rolling-origin evaluation;
- measuring whether selected tasks predict later repository work.

Predictive validity is the north star. It is not an established result yet.

## Start Here

- [AGENTS.md](AGENTS.md): operational rules for coding-agent sessions.
- [PROCESS.md](PROCESS.md): current process decisions and claim boundaries.
- [V2 system architecture](docs/architecture/v2-system-architecture-2026-06-25.md):
  draft architecture for the rewrite.
- [Learned selector roadmap prompt](docs/research/learned-selector-roadmap-gpt-5-5-pro-prompt-2026-06-25.md):
  prompt for external algorithm-roadmap review.
- [Goodhart note](docs/research/goodhart-law-note-2026-06-23.md):
  validity boundary between benchmark prediction and tuning utility.

## Current Design Shape

The v2 system should keep a small vocabulary:

- `Task`: solver-visible problem and repository metadata.
- `Check`: task acceptance method or oracle.
- `Workspace`: isolated solver and verifier execution.
- `Result`: one Agent on one task, including status, cost, latency, and failure
  labels.
- `Selector`: chooses benchmark tasks from historical supply under a budget.
- `RollingOrigin`: evaluates whether selected tasks predict later work.

Three assets should stay decoupled:

- `Task Pool`: generated or imported tasks, checks, metadata, and certification
  records.
- `Benchmark Selection`: selector version, origin, history pool, selected task
  IDs, weights, and budget.
- `Agent Results`: cached outcomes for `Agent x Task x environment`, with cost
  and verifier status.

This decoupling matters because paid Agent results are durable assets. Selector
research should be able to iterate over cached result tables without rerunning
identical paid cells.

## Repository Layout

- `docs/architecture/`: system design notes, including the v2 architecture
  draft.
- `docs/research/`: research notes, prompts, claim-boundary notes, and
  reader-facing context.
- `experiments/`: prototype code, tests, result schemas, and sanitized evidence
  from completed experiments. Treat this as evidence and source material, not
  as the v2 architecture.
- `archive/`: historical material kept for audit only.

## Related-Work Direction

Built-in task generation should reuse and adapt established coding-agent
benchmark methods instead of inventing similar ideas under new names. Initial
families to study include:

- SWE-bench-style issue/PR tasks with fail-to-pass and pass-to-pass tests;
- SWE-bench Verified-style quality filtering;
- SWE-bench Live-style refresh and origin-aware freezing;
- SWE-Bench Pro-style harder long-horizon tasks;
- SWE-Bench++ / SWE-Bench Atlas-style large-scale generation;
- SWE-smith-style task and environment generation;
- SWE-Future-style future-oriented task synthesis;
- user-provided task pools and custom checks.

## Paid Calls

Paid LLM or Agent calls must use:

```text
LLM_BASE_URL
LLM_API_KEY
```

Do not use subscription auth, `OPENAI_API_KEY`, OpenRouter variables, or
provider-specific variables unless the user explicitly changes the rule.

Raw prompts, completions, Agent transcripts, solver workspaces, verifier
workspaces, cloned external repositories, caches, and secrets must not be
committed.

## Useful Commands

Run the main retained experiment tests:

```bash
uv run --project experiments/phase1_compiler pytest -q
```

Run workspace-adapter tests:

```bash
uv run --project experiments/phase0_headroom pytest experiments/phase0_headroom/tools -q
```

Check patch hygiene before committing:

```bash
git diff --check
```
