# Agent Prompt: Target Repository Selection Gate

Please execute this runbook end to end:

`/Users/chenmohan/gits/barcarolle/docs/research/target-repo-selection-gate-runbook-2026-06-15.md`

Work in `/Users/chenmohan/gits/barcarolle`.

This is a no-paid target repository selection gate for the next stronger Agent
Tuning Demo. Do not run paid Agent cells, paid LLM calls, or paid tuner calls.
Do not start a tuning experiment. The goal is to choose the best next target
repository, with evidence.

Important emphasis: actively explore new repositories. The old candidates
(`boltons`, `attrs`, `click`, `toolz`, `humanize`) are baselines for comparison,
not the center of the search. Follow the runbook's requirements to screen a
meaningful set of new Python repositories and deep-probe multiple new candidates
when feasible.

Read `AGENTS.md`, `PROCESS.md`, and the context files named by the runbook.
Include the required baseline candidates, add stronger Python repository
candidates, run no-paid local probes, evaluate certification and rolling-origin
window capacity, and produce the required Chinese report, JSON, PROCESS update,
tests, hygiene checks, and focused commits.

If tools or candidate repositories fail, repair bounded issues or move to the
next candidate. Do not stop for human input unless every candidate is impossible
to evaluate. If no repository is better than attrs/click/boltons, complete the
negative result honestly and provide the best fallback.
