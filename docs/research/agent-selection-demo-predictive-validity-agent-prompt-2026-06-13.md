# Prompt For Predictive-validity Demo Completion Agent

Please execute this mandatory runbook:

```text
/Users/chenmohan/gits/barcarolle/docs/research/agent-selection-demo-predictive-validity-completion-runbook-2026-06-13.md
```

Important: the previous strict runbook completed the Agent-selection demo layer,
but predictive validity was still treated as future work. This runbook brings it
back into the demo. Do not stop after summarizing the existing final package.

Read `AGENTS.md`, `PROCESS.md`, and the predictive-validity completion runbook
first. Then work autonomously through every mandatory package:

1. audit existing predictive-validity evidence and produce a ledger;
2. freeze the estimand, metrics, baselines, and claim boundary;
3. build rolling-origin window/data feasibility tooling;
4. implement rolling-origin evaluation with tests;
5. run no-paid retrospective analysis from committed sanitized outcomes;
6. decide whether a bounded paid pilot is necessary, and run it only if the
   runbook gates pass and the 40-cell boundary is respected;
7. write the final predictive-validity demo story;
8. update final package, closeout, and `PROCESS.md`.

Autonomy means diagnosing missing data, adapting existing phase1/demo tooling,
patching code, adding tests, and continuing through blockers where the runbook
allows. It does not mean choosing a document-only shortcut.

Do not expand claims beyond evidence. Do not claim predictive validity unless
the preregistered metrics and baselines actually justify it. If results are
negative or underpowered, make that part of the demo story: it still supports
why predictive-validity optimization is the core project problem.

All paid calls, if any, must use `LLM_BASE_URL` plus `LLM_API_KEY`, must stay
inside the runbook's 40-cell boundary, and must be preregistered before
execution. Do not commit raw prompts, completions, transcripts, solver/verifier
workspaces, provider logs, cloned repos, caches, or secrets.

Make focused commits after each completed package. Final closeout must answer
the checklist in the runbook.
