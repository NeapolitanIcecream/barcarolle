# External Codex CLI Generator

You are the real external Codex CLI generator session for the corrected Phase 1 diff-assisted statement regeneration run.

Work in `/Users/chenmohan/gits/barcarolle`. Do not commit. Do not push. Do not run solver ACUT cells.

Read only this sanitized candidate packet file for generation input:

`experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_candidate_packets.json`

Write one JSONL row per packet to:

`.codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/generator/output/generated_statements.jsonl`

Update this process file before and after work:

`.codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/generator/process.md`

Required output row shape:

```json
{"task_id":"...","statement":"...","statement_digest":"sha256:...","generation_notes":"...","used_diff_summary":true,"contains_raw_diff":false,"contains_paid_outcome":false}
```

Rules:

- Generate solver-facing statements from public context plus diff summaries and digests in the packets.
- Do not copy previous `phase1_diff_assisted_statement_*` regenerated statements or deterministic dry-run output.
- Do not use deterministic behavior overrides, local rule-based statement generation, or old reviewer verdicts.
- Do not include raw diff hunks, `diff --git`, exact patch recipes, raw test assertions, target commit hashes, hidden verifier material, paid outcomes, or terminal statuses.
- Target 1500-2500 characters per statement, soft maximum 4000 characters, and never substring-truncate.
- Include problem summary, behavior details, expected behavior, editable implementation paths, non-editable test paths, verifier metadata, and scope boundaries.
- Set `statement_digest` to `sha256:` plus the SHA-256 digest of the exact statement string.
- Set `status: delivered` in the process file only after the JSONL output is complete.

Process file format:

```text
status: delivered
updated: <UTC timestamp>
summary: Generated <N> statements as a real external Codex CLI generator session.
artifacts:
  - .codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/generator/output/generated_statements.jsonl
verification:
  - row count and statement digest check performed
```
