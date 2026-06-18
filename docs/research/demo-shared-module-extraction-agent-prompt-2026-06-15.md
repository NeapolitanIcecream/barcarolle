# Agent Prompt: Demo Shared Module Extraction

Please execute this runbook end to end:

`/Users/chenmohan/gits/barcarolle/docs/research/demo-shared-module-extraction-runbook-2026-06-15.md`

Work in `/Users/chenmohan/gits/barcarolle`.

This is a no-paid refactor. Do not run paid Agent cells, paid LLM calls, or paid
tuner/proposer calls. Do not run new Selection or Tuning experiments.

The main goal is to decouple Agent Tuning Demo code from live Agent Selection
Demo code and results. Another session may update Agent Selection Demo data, so
your work must ensure those future result changes do not silently affect current
Agent Tuning Demo behavior. Prefer creating a neutral shared module and
Tuning-owned frozen snapshots/manifests. Avoid touching
`experiments/agent_selection_demo/results/` or
`experiments/agent_selection_demo/reports/`, and avoid editing Selection Demo
code unless it is truly necessary.

Follow the runbook's inventory, migration, guard-test, closeout, PROCESS,
verification, hygiene, and commit requirements. If you find that a full shared
helper adoption by Selection Demo would conflict with the parallel Selection
work, defer that part and complete the Tuning-side decoupling honestly.
