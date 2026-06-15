# Agent Prompt: Boltons Agent Selection Small Expansion

You are working in `/Users/chenmohan/gits/barcarolle`.

Read and execute this runbook end to end:

```text
docs/research/agent-selection-boltons-small-expansion-runbook-2026-06-15.md
```

Important boundaries:

- Stay on `mahmoud/boltons`; do not switch to `attrs`, `click`, or any other
  fallback repository.
- This is a presentation-oriented Agent Selection Demo expansion, not a full
  predictive-validity proof.
- Expand the paid Selection/Holdout cells where needed, then regenerate the PPT
  charts in `~/playground/barcarolle_ppt_assets`.
- Use strict chronological rolling-origin diagnostics based on real `task_time`;
  do not mix ordinary heldout split labels into the rolling-origin claim.
- Use `LLM_BASE_URL` and `LLM_API_KEY` only for paid Agent/LLM calls.
- Do not commit raw prompts, completions, transcripts, solver/verifier
  workspaces, secrets, or large raw outputs.

Execute autonomously. If a task-source, adapter, timeout, plotting, or
score-join issue appears, diagnose and fix it where feasible instead of stopping
early. Stop only for missing required secrets after sourcing `~/.zshrc`, model
unavailability, secret-isolation failure, or the paid-cell hard cap in the
runbook.

Commit focused changes after each completed package or tightly related group.
At the end, report:

- final task counts and paid-cell counts;
- final Selection vs later-check matrix;
- strict chronological rolling-origin metrics;
- chart files regenerated;
- tests and hygiene checks run;
- exact claims now supported and unsupported;
- commit hashes.
