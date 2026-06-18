# Agent Prompt: Selector-Aware Agent Selection Reanalysis

You are working in `/Users/chenmohan/gits/barcarolle`.

Read and execute this runbook end to end:

```text
docs/research/agent-selection-selector-aware-reanalysis-runbook-2026-06-16.md
```

Goal: fix the Agent-selection demo evidence so it is selector-aware. The current
expanded boltons outcome matrix is already paid for; do not run new paid Agent
cells. Rerun the selector analysis offline: for each origin, each selector must
choose a budgeted benchmark from the historical task pool, then the chosen tasks
are compared against later/future tasks using existing outcomes.

Important boundaries:

- Run every implemented selector, not only HRD. If HRD v3 `70/30` is not the
  best selector under the new selector-aware evaluation, switch the final demo
  story and charts to the better selector.
- Count timeout, harness-error, invalid-output, and no-meaningful-change cells
  as failed attempts in the main presentation/evaluation path.
- Do not use future task IDs, future outcomes, or outcomes for unselected
  candidate tasks while selecting. If an algorithm cannot be made leakage-safe,
  mark it diagnostic-only and exclude it from final-selector eligibility.
- Regenerate the PPT assets in
  `/Users/chenmohan/playground/barcarolle_ppt_assets`, especially the user-view
  Selection/Future chart, the selector-aware rolling-origin timeline, the
  random-baseline comparison, and the final algorithm schematic prompt.
- Update `PROCESS.md` so future sessions do not treat the old fixed-window
  rolling-origin chart as selector evidence.

Execute autonomously. If metadata, selector integration, plotting, or score-join
issues appear, diagnose and fix them where feasible instead of stopping early.
Stop only if the committed outcome matrix is unusable for all selectors, and
write a precise blocker report if that happens.

Commit focused changes after each completed package or tightly related group.
At the end, report:

- new paid cells used, expected `0`;
- selectors evaluated and any diagnostic-only exclusions;
- final winning selector and budget;
- latest-origin selector-chosen Selection vs Future matrix;
- selector-aware rolling-origin metrics;
- random baseline comparison;
- regenerated chart files;
- tests and hygiene checks;
- supported and unsupported claims;
- commit hashes.
