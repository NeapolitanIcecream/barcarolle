# Codex Kilo Workspace Analysis

The Codex/Kilo cross-harness comparison has completed the smoke subset but not the full matrix. Endpoint proof is resolved for both harnesses, and command-template dry-runs passed for both wrappers.

The main decision is operational rather than statistical: no predictive `same_model_cross_harness` estimate should be computed from this smoke run. The adapter code can isolate multiple harnesses, and both candidates now have proven endpoint/provider and workspace-mutation shapes.

Smoke results:

- Codex: `2/2` scoreable smoke cells, with `1` verified pass and `1` verified fail.
- Kilo: `1/2` scoreable smoke cells, with `1` verified fail and `1` ACUT timeout on `toolz__hist__002`.
- Overall: `3/4` scoreable, no corrupt model-emitted patch category, estimated smoke cost `USD 2.0`.

Required next evidence:

- A full-matrix result protocol that either reuses smoke rows intentionally or prevents full-run results from double-counting smoke cells.
- The full 20-cell matrix only after the result protocol is clarified.
