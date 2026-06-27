# Prompt For Boltons Task Generator Capacity Audit Agent

Please execute this runbook end to end:

```text
/Users/chenmohan/gits/barcarolle/docs/research/boltons-task-generator-capacity-audit-runbook-2026-06-15.md
```

The goal is to decide whether `mahmoud/boltons` has enough remaining
task-generator capacity to support a stronger rolling-origin Agent Tuning Demo,
or whether Barcarolle should return to target-repository selection.

Do not run paid Agent or LLM cells. This is a no-paid capacity audit. Use local
task-supply artifacts, generator tools, bounded certification dry runs, window
simulation, and repository fallback comparison. If local evidence is
insufficient, say that directly and recommend the smallest next no-paid repair.

Work autonomously through every package in the runbook. Make focused commits
after each package. Preserve unrelated untracked runbook/prompt drafts. Do not
commit raw prompts, completions, transcripts, solver/verifier workspaces,
secrets, cloned repositories, caches, or large raw outputs.

Final closeout must state:

- whether to continue expanding `boltons` or return to target-repo selection;
- current and projected `boltons` supply counts;
- certification dry-run conversion estimate;
- rolling-origin window capacity;
- next paid-pilot cost estimate if continuing;
- best fallback repository if not continuing;
- tests and hygiene checks;
- commits made.
