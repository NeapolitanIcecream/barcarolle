# Phase 1 Diff-Assisted Statement Regeneration Codex Loop

Status: pending.

Runbook: `docs/experiments/phase-1-diff-assisted-statement-regeneration-runbook.md`.

This workflow is the corrected external Codex CLI generator/reviewer loop. Deterministic helpers may build packets, validate schemas, run leakage checks, and screen reviewed statements. They must not generate final statements or reviewer verdicts.

## Sessions

- Generator tmux session: `phase1-diffstmt-generator`.
- Reviewer tmux session: `phase1-diffstmt-reviewer`.

## Coordination Contract

- Check `generator/process.md` and `reviewer/process.md`; do not read CLI logs for normal coordination.
- Start reviewer only after the generator process reports `status: delivered` and the sanitized generated statements have been copied to `experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_generated_statements.jsonl`.
- Raw logs are ignored and must not be committed.
