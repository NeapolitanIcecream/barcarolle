# External Codex CLI Reviewer

You are the real external Codex CLI reviewer session for the corrected Phase 1 diff-assisted statement regeneration run.

Work in `/Users/chenmohan/gits/barcarolle`. Do not commit. Do not push. Do not edit generated statements.

Read:

- Sanitized candidate packets: `experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_candidate_packets.json`
- Generated statement JSONL copied from the generator session: `experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_generated_statements.jsonl`

Write review verdicts to:

`.codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/reviewer/output/statement_reviews.json`

Update this process file before and after work:

`.codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/reviewer/process.md`

Also write a concise handoff summary to:

`.codex-workflows/phase1-diff-assisted-statement-regeneration-codex-loop/reviewer/review-to-generator.md`

Each review row must use this shape:

```json
{"task_id":"...","status":"pass","leakage_pass":true,"sufficiency_pass":true,"faithfulness_pass":true,"scope_pass":true,"formatting_pass":true,"reasons":["..."],"required_revision":"","statement_digest":"sha256:..."}
```

Top-level output must include:

```json
{"schema_version":"barcarolle.phase1.diff_assisted_codex_loop_statement_reviews.v1","generated_at":"...","candidate_count":0,"review_counts":{},"paid_llm_calls_made":true,"paid_acut_calls_made":false,"reviews":[]}
```

Review checks:

- Leakage: no gold patch text, no raw diff hunks, no `diff --git`, no exact implementation recipe, no hidden verifier content, no raw test assertions, no paid outcome/status, no target commit hash.
- Sufficiency: problem summary, expected public behavior, reproduction or behavior description, closed code fences, no mid-sentence truncation, and enough detail to attempt without hidden tests.
- Faithfulness: statement must be consistent with public context and diff summary.
- Scope: editable paths must be implementation-only; tests are non-editable metadata.
- Formatting: target 1500-2500 characters, soft max 4000, required sections present.

Return `pass`, `revise`, or `reject`. A `pass` row must have all five boolean checks true. Do not create replacement statements.

Set `status: delivered` in the process file only after every generated statement has exactly one review verdict.
