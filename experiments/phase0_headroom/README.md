# Phase 0 Headroom Experiments

This directory is for the Barcarolle restart experiments.

Phase 0 asks whether repo-specific benchmark signal exists before building a
larger benchmark compiler:

- distribution mismatch between general SWE benchmarks and target-repo work;
- same-repo predictive headroom from early tasks to later work;
- task-supply and certification funnel from candidate anchors to
  benchmark-grade tasks.

If existing task-generation pipelines cannot provide inputs for the selected
repositories, add a minimal repo-history generator under this experiment tree.
Treat it as candidate supply infrastructure: measure certified yield,
replayability, oracle quality, and manual effort.

The certification funnel should report gate-level rejection reasons, including
known-bad failure, ambiguity, solution leakage, scope clarity, cost boundedness,
and taxonomy labelability. Keep `near_certified` tasks separate from
benchmark-grade `certified` tasks.

Large raw artifacts should not be committed. Store them outside Git and commit a
small manifest with path, digest, producer, and reproduction command.

Expected layout:

```text
configs/
candidate_sources/
target_profiles/
certified_tasks/
releases/
results/
reports/
```
