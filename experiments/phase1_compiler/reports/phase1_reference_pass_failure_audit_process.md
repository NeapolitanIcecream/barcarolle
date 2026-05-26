# Phase 1 Reference-Pass Failure Audit Process

Status: running.

Plain-language summary: the earlier two-repo supply expansion rejected many candidates because the target commit's own changed tests did not pass. That is suspicious. This audit checks whether Barcarolle replayed the target commits incorrectly, or whether old commits no longer pass in the modern local environment.

## Step 0: Preflight And Ledger

Completed on 2026-05-26.

- Read `AGENTS.md` and the reference-pass failure audit runbook.
- Confirmed the run is local-only: paid ACUT calls, paid replication, paid task-solving calls, and paid LLM calls are disabled.
- Confirmed no hidden verifier material, raw ACUT transcript, raw prompt, raw completion, solver workspace, or verifier workspace is used.
- Confirmed required committed artifacts and local external repos are present.
- Confirmed current reference-pass failure counts from the certified supply expansion: `attrs=54`, `boltons=22`.
- Added `experiments/phase1_compiler/tmp/` to `.gitignore` so raw replay logs stay out of committed artifacts.

## Running Notes

- Raw replay logs, stdout/stderr, and temporary workspaces must stay under ignored scratch paths.
- Committed outputs should contain only sanitized counts, command shapes, hashes, bounded categories, and short representative snippets where needed.
- No follow-up runbook will be drafted by this worker.
