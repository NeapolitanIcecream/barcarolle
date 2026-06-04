# Phase 1 Local Algorithm Bakeoff Process

Run ID: `phase1_local_algorithm_bakeoff_20260526`.
Runbook: `docs/experiments/phase-1-local-algorithm-bakeoff-runbook.md`.
Generated at: `2026-06-04T06:40:22Z`.

## Boundary

- New paid ACUT calls made: `False`.
- New paid LLM calls made: `False`.
- Follow-up runbook written by worker: `False`.
- Raw ACUT transcripts, prompts, completions, solver workspaces, and verifier workspaces committed: `False`.

## Environment

- Branch: `codex/restart-benchmark-compiler`.
- HEAD at latest report write: `91ab66e3`.
- uv: `uv 0.11.16 (Homebrew 2026-05-21 aarch64-apple-darwin)`.
- Python: `3.11.13`.

## Dependency Decision

- Decision: `stay_with_standard_library`.
- Reason: the candidate pools are small enough for exhaustive enumeration and deterministic fallback weighting.

## Work Queue

| Step | Title | Status | Commit target |
| --- | --- | --- | --- |
| 0 | Preflight, Dependency Audit, And Work Queue | completed | Record local algorithm bakeoff preflight |
| 1 | Reproduce Paid Pilot Metrics And Build Task Audit | completed | Reproduce weighted pilot metrics for bakeoff |
| 2 | Quantify Metadata Objective Underidentification | completed | Measure weighted objective underidentification |
| 3 | Define Coarse Features And Target Profile Prototype | completed | Define local bakeoff features and target profile prototype |
| 4 | Implement Candidate Compiler Designs | completed | Build local bakeoff compiler candidates |
| 5 | Implement Capped Shrinkage Weights | completed | Evaluate capped shrinkage weights |
| 6 | Rolling-Origin Or Pseudo-Future Local Validation | completed | Run local bakeoff validation |
| 7 | Ablation Study And Mainline Recommendation | completed | Compare local bakeoff ablations |
| 8 | Paid-Readiness Gate | completed | Evaluate local bakeoff paid readiness |
| 9 | Final Decision And Closeout | pending | Record local algorithm bakeoff decision |

## Verification Commands

- `uv run --project experiments/phase1_compiler pytest -q`
- `git diff --check`

## Closeout Notes

- Paid-readiness gate evaluated; no paid runbook written.

## Commit Tracking

The exact final commit range is reported by the coordinating session after commits are created.
