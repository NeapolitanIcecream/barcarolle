# Agent Prompt: Large-Repo Target Selection Gate

Please execute this runbook end to end:

`/Users/chenmohan/gits/barcarolle/docs/research/large-repo-target-selection-gate-runbook-2026-06-15.md`

Work in `/Users/chenmohan/gits/barcarolle`.

This is a no-paid repository selection run for the next stronger Agent
Selection and Agent Tuning Demo. Do not run paid Agent cells, paid LLM calls, or
paid tuner calls. Do not start a tuning experiment.

The main goal is to find a target repository that is both large enough and fast
enough: enough certified task capacity for rolling-origin evaluation, but
evaluation/replay light enough for practical iteration. Do not over-focus on the
old candidates, and do not assume NumPy/SciPy are preferred just because they
are examples. Actively compare large/heavy candidates with medium-large
fast-evaluation candidates.

Follow the runbook's candidate screening, deep-probe, reporting, verification,
hygiene, and commit requirements. If a candidate fails, diagnose whether it is a
capacity problem, evaluation-speed problem, environment problem, or bounded
repair opportunity, then continue. Complete with an honest recommendation or
negative result.
