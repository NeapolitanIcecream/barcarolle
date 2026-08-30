# Experiment Archive

The files in this directory are dated, fixed records of experiments that were
actually designed or run. Preserve their original target quantities, plans,
negative results, and evidence limits for auditability.

They are not the current project roadmap. In particular, older documents may
describe task selection as the only method, direct pass-rate MAE as the sole
primary metric, or distribution shift between reference and evaluated agents
as the only next action. Those statements are superseded for new work by:

- [`../research-program.md`](../research-program.md): active scientific
  objectives, method families, and experiment sequence;
- [`../research-improvement-backlog.md`](../research-improvement-backlog.md):
  active work packages and method registry;
- [`../../PROCESS.md`](../../PROCESS.md): short cross-session handoff.

Do not rewrite a historical plan to match the new program. A new experiment
must create a new dated plan with pass-rate MAE, pass-rate-difference MAE
between agents, and, where repeated optimization is studied, the change in both
metrics under a predeclared optimization protocol.
