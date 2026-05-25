# Phase 1 Statement-Hardened Holdout Preregistration Runbook

Status: draft next-runbook recommendation, 2026-05-25.

This draft exists because the attrs H_future statement-quality audit found that
the current attrs H_future evidence is not clean enough for a predictive-validity
claim. It must not be run automatically from that audit. Any paid validation
requires explicit user approval and a new frozen release or preregistration.

## Purpose

Prepare a statement-hardened holdout release that preserves the Barcarolle
boundary:

- use only public solver-visible task context;
- keep hidden verifier material out of solver statements;
- require statement-quality gates before task freezing;
- preserve existing paid outcomes as historical observations;
- avoid treating diagnostic statement previews as repaired scores.

## Preconditions

- `LLM_BASE_URL` and `LLM_API_KEY` must be present before any paid ACUT call.
- No paid ACUT or paid LLM calls are allowed during preregistration setup.
- The statement-quality helper in
  `experiments/phase0_headroom/tools/statement_quality.py` must be active in
  clean-supply mining and workspace package rendering.
- Existing score tables must remain immutable inputs.

## Local Setup Steps

1. Rebuild or select candidate holdout tasks using the hardened statement
   quality gate.
2. Reject or hold for manual review any task with:
   - old 240-character body-summary truncation;
   - unclosed code fence;
   - trailing incomplete sentence;
   - empty or nearly empty public problem summary;
   - PR-context source without an adequate issue-backed problem context;
   - missing editable implementation scope.
3. Render solver-visible statement previews for every candidate.
4. Inspect package metadata and verify editable paths contain implementation
   files only.
5. Freeze a preregistered release manifest that records task IDs, statement
   digests, allowed context refs, editable paths, verifier command metadata, and
   statement-quality diagnostics.

## Paid Validation Gate

Stop before paid validation unless the user explicitly approves a new paid run.
If approved, run only the newly frozen release. Do not rerun or relabel the old
attrs H_future cells.

## Required Output

The future runbook should produce new preregistration artifacts under a new
result prefix. It should also record:

- paid calls made;
- endpoint proof using `LLM_BASE_URL` and `LLM_API_KEY`;
- statement-quality gate pass/fail counts;
- release manifest digest;
- scoreable result table for the new release only;
- comparison against the old attrs H_future observation as historical context,
  not as a repaired score.

## Stop Conditions

Stop and write a blocker if hidden verifier material is needed to improve a
statement, if ACUT internals would need modification, or if the work would
rewrite historical paid results.

