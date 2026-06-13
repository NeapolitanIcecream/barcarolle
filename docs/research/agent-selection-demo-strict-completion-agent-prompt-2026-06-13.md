# Prompt For Strict Autonomous Demo Completion Agent

Please execute this mandatory runbook:

```text
/Users/chenmohan/gits/barcarolle/docs/research/agent-selection-demo-strict-completion-runbook-2026-06-13.md
```

Important: do not stop after producing or reviewing the final demo package. The
previous completion pass stopped too early. This runbook requires you to finish
all mandatory work packages unless a package has a specific blocker report with
attempted fixes and evidence.

Read `AGENTS.md`, `PROCESS.md`, and the strict runbook first. Then work
autonomously through every mandatory package:

1. state audit and gap list;
2. tooling/artifact hygiene audit;
3. Kilo timeout and usage root-cause work;
4. Kilo smoke/gate and frozen top-2 repeat attempt if gates pass;
5. no-paid second-repo gate;
6. runnable Agent tuning feedback summary generator;
7. final package, closeout, and `PROCESS.md` update.

Autonomy means diagnosing, patching, testing, and retrying within the runbook's
boundaries. It does not mean deciding that optional-looking work can be skipped.

Do not expand the Agent matrix, tune candidates, run second-repo paid cells,
introduce a learned selector, or claim predictive validity. Any paid calls must
stay inside the explicit paid-call boundary and must use `LLM_BASE_URL` plus
`LLM_API_KEY`.

Make focused commits after each completed package. Final closeout must answer
the checklist in the runbook.
