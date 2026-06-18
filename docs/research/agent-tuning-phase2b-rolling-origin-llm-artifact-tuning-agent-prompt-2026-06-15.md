# Prompt For Agent Tuning Phase 2b Agent

Please execute this runbook end to end:

```text
/Users/chenmohan/gits/barcarolle/docs/research/agent-tuning-phase2b-rolling-origin-llm-artifact-tuning-runbook-2026-06-15.md
```

The goal is to move beyond the weak Phase 2a pilot. Phase 2a proved
action-level artifact injection and before/after validation mechanics, but it
did not show tuned improvement and did not run a real LLM-driven tuner. Phase 2b
must use rolling-origin or time-ordered future validation, choose task windows
with real headroom, and use an LLM-driven artifact proposer.

Start with the no-paid task-supply/headroom audit. Do not run paid tuning if
rolling-origin windows, headroom, or recurring failure labels are inadequate.
If the audit passes, freeze the protocol before any proposer or paid validation
run.

Use the runbook's default path unless evidence requires a fallback:

```text
LLM-driven GEPA/GEPA-shaped reflective proposer -> one Kilo AGENTS.md appendix
-> Kilo workspace Agent -> rolling-origin dev and future validation
```

Do not present a deterministic local template as a real tuner. If GEPA/Phoenix
cannot run with an LLM proposal/reflection step, stop or label the result as a
non-LLM control. Holdout/future tasks must remain invisible until the selected
artifact hash is frozen.

All paid LLM or Agent calls must use `LLM_BASE_URL` plus `LLM_API_KEY`. Stay
within the runbook's paid-cell and cost caps. Commit only sanitized reports,
summaries, schemas, and manifests. Never commit raw prompts, completions,
transcripts, solver/verifier workspaces, secrets, caches, cloned repositories,
or large raw outputs.

Work autonomously through every package, make focused commits after each
package, and finish with a closeout listing terminal state, rolling-origin
windows, task counts, proposer used, paid cells/cost, dev/future matrices,
paired net wins, tests, hygiene checks, supported claims, unsupported claims,
and commits made.
