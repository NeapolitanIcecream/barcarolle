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

## Step 1: Build Failure Inventory

Completed on 2026-05-26.

- Parsed `experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_certification_attempts.json`.
- Found 76 `reference_pass` failures: 54 for `attrs` and 22 for `boltons`.
- Grouped failures by repo, year, module, test files, change size bucket, candidate filter status, source context status, reference return codes, stdout/stderr hashes, and duration bucket.
- Selected 12 prioritized replay tasks, 6 per repo.
- Stored only sanitized counts and hashes; no raw command logs were committed.

## Steps 3-6: Replay And Audit Evidence

Completed on 2026-05-26.

- Replayed 12 representative `reference_pass` failures: 6 `attrs` tasks and 6 `boltons` tasks.
- Ran four replay variants for each task: current command, workspace cwd, no editable install, and pytest-config-visible.
- No variant made a sampled reference run pass.
- Patch application audit found no sampled test-material mismatch: patched base test files matched target test files for all sampled tasks.
- Command-contract audit found that replay uses the target workspace and editable install, but setup/import/collection/assertion failures are all currently recorded under the broad `reference_pass` gate.
- Environment audit grouped the sampled failures as dependency version drift, pytest config incompatibility, and Python-version drift.
- Raw replay logs remained under ignored scratch paths.
