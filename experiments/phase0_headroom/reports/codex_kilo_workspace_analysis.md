# Codex Kilo Workspace Analysis

The Codex/Kilo cross-harness comparison is not scoreable yet. Post-run diagnosis resolved endpoint proof for both harnesses, and command-template dry-runs passed for both wrappers, but the experiment has not yet run the smoke or full matrix cells.

The main decision is operational rather than statistical: no `same_model_cross_harness` estimate should be computed from this run. The adapter code can isolate multiple harnesses, and both candidates now have proven endpoint/provider and workspace-mutation shapes, but neither has a scoreable ACUT smoke result.

Required next evidence:

- A four-cell smoke matrix using the now-proven endpoint/provider and command-template shapes before any full matrix run.
