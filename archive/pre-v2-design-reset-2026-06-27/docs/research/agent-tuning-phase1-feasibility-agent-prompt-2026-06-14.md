# Prompt For Agent Tuning Phase 1 Feasibility Agent

Please execute this runbook end to end:

```text
/Users/chenmohan/gits/barcarolle/docs/research/agent-tuning-phase1-feasibility-runbook-2026-06-14.md
```

The goal is to finish all preparation required before Agent Tuning Demo Phase 2.
Do not run the full tuning demo and do not start GEPA/DSPy/Phoenix optimization
as the main experiment. Phase 1 must determine whether tuner-produced artifacts
can be injected into real Codex/Kilo-style workspace Agents and whether
Barcarolle can observe behavior changes caused by those artifacts.

Work autonomously through every package in the runbook. If one tuning surface is
unsupported or unreliable, mark it honestly and keep testing the remaining
surfaces. If all real-Agent artifact-injection paths fail, produce the
tuner-native fallback recommendation required by the runbook.

Do not ask for manual intervention unless the repository cannot be read or all
tooling is unusable. Make focused commits after each package. Do not commit raw
prompts, completions, transcripts, solver/verifier workspaces, secrets, caches,
or large raw outputs.

All paid LLM or Agent calls, if any are unavoidable for a minimal smoke test,
must use `LLM_BASE_URL` plus `LLM_API_KEY`; otherwise prefer no-paid/mock/local
dry runs.

Final closeout must state:

- proof-of-injection results;
- behavior-change smoke-test results;
- supported and risky tuning surfaces;
- tuner compatibility recommendation;
- Phase 2 readiness state;
- recommended Phase 2 primary path and fallback path;
- tests and hygiene checks;
- exact claim boundary.
