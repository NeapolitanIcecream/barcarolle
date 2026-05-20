# Phase 1 Compiler Skeleton Report

Status: `skeleton_initialized`.

This workspace implements the smallest useful Phase 1 compiler pieces after the Phase 0 measured Matrix A run. It is not a Phase 1 validation result.

## Implemented

- Task manifest, release manifest, target profile, certification report, agent run manifest, scorecard, and weighted score summary dataclasses.
- Phase 0 `toolz` mini-release importer.
- Stratified module weighting with explicit `insufficient_evidence` handling.
- CLI import path that writes draft release and weighted-score artifacts under `experiments/phase1_compiler/results/`.
- Tests for schema validation, compatible weighted scoring, incompatible evidence handling, and CLI artifact generation.

## Current Boundary

The current Matrix A outcomes are still harness-sensitive and underpowered. The Phase 1 skeleton can represent that evidence, but it does not turn it into predictive validation.

## Next Useful Compiler Work

Add split-generation policies, uncertainty summaries, and a stricter output-contract repair experiment before any broad residual-predictive-validity run.
