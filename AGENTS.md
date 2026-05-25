# Barcarolle Agent Instructions

These instructions apply to all Codex or other coding-agent sessions working in
this repository.

## Project Boundary

Barcarolle is a target-repository benchmark compiler for coding-agent evaluation
and tuning. It is not an ACUT agent harness, a general SWE task factory, an
agent-license product, or a public leaderboard.

The ACUT, or Agent Configuration Under Test, owns its own agent harness:

- file search and reading;
- editing strategy;
- multi-turn reasoning loop;
- public-test execution policy;
- retry behavior;
- tool-use and trace internals;
- model, prompt, skills, retrieval, and runtime budget.

Barcarolle must not reimplement those ACUT internals. Barcarolle's job at the
ACUT boundary is to:

- build a clean solver workspace at the task base commit;
- provide only solver-visible task statements and allowed context;
- invoke a configured ACUT harness against that workspace;
- capture the final workspace diff with Git;
- enforce benchmark-side policy checks such as no hidden-oracle access, no test
  edits when tests are prohibited, and no out-of-scope path edits;
- replay the captured diff in a fresh verifier workspace;
- inject private oracle material only in the verifier workspace;
- run the hidden verifier;
- record terminal status, cost, latency, and sanitized artifacts.

Do not use one-shot chat-completion diff generation as the primary scoreable
ACUT protocol. A diff-only prompt may be kept only as a diagnostic baseline or
negative control. Scoreable Phase 0+ ACUT runs should use a workspace adapter
that lets the ACUT harness modify a real worktree, with Barcarolle capturing the
resulting `git diff`.

## LLM Endpoint Rule

All paid LLM or ACUT calls in active experiments must use:

```text
LLM_BASE_URL
LLM_API_KEY
```

If either variable is missing in a worker shell, source `~/.zshrc` and check
again before making any call. Do not fall back to local Codex/ChatGPT
subscription auth, `OPENAI_API_KEY`, OpenRouter variables, or provider-specific
variables unless the user explicitly updates this rule.

An ACUT harness may be used only if it is configured to call the required
endpoint or if the run is explicitly marked as non-scoreable setup work. If the
worker cannot prove the ACUT harness uses `LLM_BASE_URL` plus `LLM_API_KEY`, it
must stop before paid task-solving calls and write a blocker report.

## Artifact Hygiene

Do not commit secrets, full raw prompts, raw completions, raw ACUT transcripts,
solver workspaces, verifier workspaces, cloned external repositories, `.venv`,
caches, or large raw outputs. Store raw artifacts under ignored paths and commit
only small sanitized manifests, summaries, reports, and digests.

Use `uv` for repo-local Python tooling. Before committing experiment changes,
run the scoped tests named by the relevant runbook and `git diff --check`.

## Runbook Execution Boundary

When executing a runbook, do not draft or create the next runbook unless the
user explicitly asks for that in the same execution task. The executing agent
should keep advancing the current runbook until it reaches a real stop
condition, then record completed work, blockers, decisions, and recommended
next actions in the closeout report. The coordinating user-facing session is
responsible for interpreting the result and writing any follow-up runbook.
