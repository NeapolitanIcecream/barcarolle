# Phase 1 Compiler Skeleton

This workspace is a minimal Barcarolle Phase 1 compiler skeleton. It does not claim Phase 1 predictive validation.

It currently provides:

- typed dataclass schemas for task manifests, release manifests, target profiles, certification reports, agent run manifests, scorecards, and weighted score summaries;
- a converter from the current Phase 0 `toolz` mini release into a draft Phase 1 release manifest;
- a small stratified weighting module that marks missing or incompatible evidence as `insufficient_evidence`;
- tests for schema validation and weighted score computation.

Run:

```bash
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py import-phase0
```
