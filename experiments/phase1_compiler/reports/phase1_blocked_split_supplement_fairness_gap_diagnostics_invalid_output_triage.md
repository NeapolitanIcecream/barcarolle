# Blocked Split Supplement Invalid Output Triage

Classification: `adapter_output_contract_violation`.

What happened: Codex produced a non-scoreable `invalid_output` for `attrs__v2__157` in `experiments/phase0_headroom/results/phase1_blocked_split_missing_cell_supplement_paid_execution_batch_1_smoke_codex_workspace_score_table.csv`.
Why it matters: this affects one denominator cell and should not be silently converted to pass or fail.
Action suggested next: improve no-paid sanitized logging and inspect the Codex output contract only if a benchmark bug is suspected.

- Kilo same task: `verified_fail`.
- Other invalid or non-scoreable patterns: `0`.
- Threatens supplement conclusion: `False`.

Limitation: raw solver output was not read or committed, so the exact invalid-output text remains unknown.
