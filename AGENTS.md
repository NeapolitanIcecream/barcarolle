# Barcarolle Agent Instructions

These instructions apply to all coding-agent sessions in this repository.

## Mission

Barcarolle's first principle is to provide reliable evaluation methods for
self-evolving agents. Repository-level coding agents are the first concrete
domain.

A self-evolving agent retains behavior-changing updates across tasks, including
changes to its model, harness, persistent prompts, memory, skills, tools, or other
persistent state. Those changes may be autonomous or produced by an external
agent optimizer. Subject evolution is the core research context. Evaluator
coevolution is one optional method, not a required system property.

Reliability is bounded by a declared task population, outcome definition, agent
lineage and optimizer, feedback interface, optimization budget, threat model,
time horizon, and decision. Do not make universal or permanent reliability or
Goodhart-resistance claims.

The default estimand is **operational behavior**—what an exact agent actually
does under a declared deployment-like harness and runtime policy. Performance
under a separate, predeclared capability-elicitation protocol is a different
estimand. A change to persistent agent configuration or its generation, tool,
or runtime policy creates a new version. Task inputs and temporary cues allowed
by a frozen policy are run contexts for the same version and must be recorded
separately. For self-evolving studies, preserve frozen snapshots,
parent-to-child transitions, and the complete agent lineage rather than only
the final winner.

The active primary empirical objectives are:

1. minimize pass-rate mean absolute error (MAE) on future real-world tasks;
2. minimize pass-rate-difference MAE between agents on those tasks;
3. minimize the increase in both errors as the predeclared budget for repeated
   evaluator-guided optimization grows.

The first two are the primary numerical metrics. Objective 3 evaluates their
retention under optimization. Apply four stages in order:

1. Evidence validity is a hard prerequisite: invalid outcomes, leakage, or a
   prospective test set whose outcomes affected its own selection do not
   produce a reliability result.
2. Absolute error limits require both errors, coverage, and uncertainty to meet
   predeclared deployment requirements. Without such requirements, report a
   comparative result rather than calling a method reliable.
3. Degradation under optimization separately measures how both errors change
   from the same evaluation method's no-optimization baseline (`b=0`);
   predeclare tolerated degradation.
4. Method comparison chooses among methods. Give pass-rate-difference MAE
   decision priority only if, at every predeclared evaluation budget, the
   method's pass-rate MAE is no more than a predeclared margin worse than a
   named comparator.

A reliability claim must pass Stages 1 and 2, plus Stage 3 when it covers
evaluator-guided optimization. Stage 4 cannot repair an earlier failure.
Neither stability from an already inaccurate `b=0` nor non-inferiority to an
inaccurate comparator establishes reliable evaluation.

Read `docs/research-program.md` for the authoritative research plan. The method
space is not restricted to task selection. It includes task generation, task
sampling and weighting, statistical outcome models, calibration and
abstention, evaluator feedback policies, evaluator updating, adversarial stress
testing of evaluators and metrics, and agent–evaluator coevolution. Every method
must be tested on an independent, temporally held-out set of future real-world
tasks. Meta-evaluation means evaluating evaluators and their metrics.

The system should stay small, auditable, and centered on:

- task collection or generation and execution-based validation;
- fresh-workspace agent execution under a cooperative-agent threat model;
- hidden-check verification;
- normalized result storage;
- evaluator construction and rolling-origin evaluation (backtesting across
  successive time cutoffs);
- explicit evidence about agent pairs, evaluator feedback, and optimization
  budgets;
- independent prospective evidence that remains unavailable to the agent
  optimizer and evaluator-update process until the corresponding predictions
  and protocol are frozen;
- reports that separate evidence from claims.

The tested agent owns its model, harness, prompts, memory, skills, tools,
retrieval, edit loop, retries, public-test policy, persistent state, and runtime
budget.

The current Barcarolle runtime owns the benchmark execution boundary:

- create a clean solver workspace at the task base commit;
- provide only solver-visible task material;
- invoke the configured agent harness;
- capture the final workspace diff;
- enforce benchmark-side rules;
- replay the diff in a fresh verifier workspace;
- inject private check material only in the verifier workspace;
- run the hidden check;
- record terminal status, cost, latency, failure labels, and sanitized
  artifacts.

Scoreable agent runs should use a workspace adapter that lets the agent modify a
real worktree while Barcarolle captures the resulting `git diff`.

The current built-in adapter assumes a cooperative agent. An experiment that
deliberately searches for test, scorer, grader, or host exploits must use an
execution adapter whose isolation matches that threat model; hidden checks
alone are not host isolation.

## Engineering Defaults

Prefer mature libraries, standard tooling, and direct data contracts over
bespoke frameworks or broad abstractions. Custom code is appropriate for
benchmark boundaries, reproducibility, artifact hygiene, agent isolation,
hidden-check protection, and auditability.

Keep core concepts simple. Current implemented data vocabulary is `Task`, `Check`,
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

Prefer the module vocabulary above when describing implemented code; avoid
renaming existing modules speculatively. In research prose, evaluator, task
generator, agent version, evaluator feedback, optimization round, and
meta-evaluation are ordinary domain terms, not implemented records unless an
exact backticked record name is given.

For public and handoff documentation, prefer plain, established terms over
project-specific shorthand. Use “pass-rate MAE,” “pass-rate-difference MAE,”
“future real-world tasks,” and “repeated evaluator-guided optimization.” Avoid
using “future-grounded,” “later-real,” “level error,” “gap error,”
“cardinal error,” or “reality anchor” as Barcarolle terminology. Capitalize
names such as `Task`, `Check`, `Result`, and `Selector` only when referring to
the exact code record or module. Explain an exact code name in ordinary language
on first use.

Use `uv` for repo-local Python tooling.

## Benchmark LLM Endpoint Rule

This rule applies to Barcarolle benchmark or evidence-producing paid calls:
target agent-solving runs, paid validation runs, evaluator, task-selection, or
task-generation experiments, benchmark harness calls, and any other paid call
whose output may become benchmark evidence or research evidence.

Those calls must use:

```text
OPENAI_BASE_URL
OPENAI_API_KEY
```

If either variable is missing, source `~/.zshrc` and check again before making
the benchmark/evidence-producing call. Do not use subscription auth,
`LLM_BASE_URL`, `LLM_API_KEY`, OpenRouter variables, or provider-specific
variables for those benchmark/evidence-producing calls unless the user
explicitly changes this rule.

If a harness cannot be proven to use the required endpoint, stop before paid
task-solving calls and write a blocker report.

This rule does not apply to repository-maintenance Codex sessions used to
implement, review, or coordinate work in this repository. Runbook Reviewer Codex
CLI sessions should use the user's local Codex CLI authentication/subscription,
not `OPENAI_BASE_URL` or `OPENAI_API_KEY`, unless the user explicitly requests a
different reviewer execution mode.

## Artifact Hygiene

Do not commit secrets, full raw prompts, raw completions, raw agent transcripts,
solver workspaces, verifier workspaces, cloned external repositories, `.venv`,
caches, or large raw outputs.

Store raw artifacts only under ignored paths. Commit small sanitized indexes,
summaries, reports, schemas, and digests.

Before committing experiment or infrastructure changes, run the scoped tests
relevant to the touched area and `git diff --check`.

## Process Notes

Read `PROCESS.md` after this file when working on experiments, paid validation,
benchmark design, evaluator research, agent adapters, or research
interpretation.

Read `docs/literature-review.md` before proposing a new evaluator method or
claiming that prior work validates one. Preserve each source's publication
status, assumptions, transfer limits, and distinction between adjacent evidence
and Barcarolle-specific results.

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
