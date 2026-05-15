# Repository-Local Rich-W20 Pause Checkpoint

Paused at: 2026-05-15 17:10 CST

Reason: operator requested work to pause before the expected network interruption window and before 17:30 local time.

## Status

- Primary live run was stopped intentionally before completion.
- Public summary was refreshed after stopping the runner.
- No repository-local Rich-W20 runner, workspace runner, Codex patch command, or verifier process remained active at pause time.
- No private raw artifact directory existed without a matching public normalized result at pause time.

## Completed Cells

- Total normalized results: 130 / 160
- W* axis: 80 / 80, primary-score ready
- R axis: 50 / 80, 30 cells missing
- Summary status: `primary_incomplete_or_infra_blocked`

## Missing Cells

The paused run is missing these R-axis primary cells:

- `rich__r__013`: `cheap-rich-inert-control-v1`, `cheap-rich-localization-tool-v1`
- `rich__r__014`: `cheap-generic-swe`, `cheap-rich-c-calibrated-v1`, `cheap-rich-inert-control-v1`, `cheap-rich-localization-tool-v1`
- `rich__r__015`: `cheap-generic-swe`, `cheap-rich-c-calibrated-v1`, `cheap-rich-inert-control-v1`, `cheap-rich-localization-tool-v1`
- `rich__r__016`: `cheap-generic-swe`, `cheap-rich-c-calibrated-v1`, `cheap-rich-inert-control-v1`, `cheap-rich-localization-tool-v1`
- `rich__r__017`: `cheap-generic-swe`, `cheap-rich-c-calibrated-v1`, `cheap-rich-inert-control-v1`, `cheap-rich-localization-tool-v1`
- `rich__r__018`: `cheap-generic-swe`, `cheap-rich-c-calibrated-v1`, `cheap-rich-inert-control-v1`, `cheap-rich-localization-tool-v1`
- `rich__r__019`: `cheap-generic-swe`, `cheap-rich-c-calibrated-v1`, `cheap-rich-inert-control-v1`, `cheap-rich-localization-tool-v1`
- `rich__r__020`: `cheap-generic-swe`, `cheap-rich-c-calibrated-v1`, `cheap-rich-inert-control-v1`, `cheap-rich-localization-tool-v1`

## Completion Audit Checklist

The experiment is complete only when all items below have direct evidence:

- `summary.json` reports `normalized_result_count: 160`.
- `summary.json` reports W* present cells `80`, missing cells `0`, and `primary_score_ready: true`.
- `summary.json` reports R present cells `80`, missing cells `0`, and `primary_score_ready: true`.
- No normalized result has `requires_rerun_or_exclusion: true` or `triage_paused: true`.
- No private raw artifact directory exists without a matching public normalized result.
- The final analysis report evaluates the frozen success criteria:
  - `A4_vs_A0_w_star_min_delta_tasks: 4`
  - `r_selected_vs_A0_w_star_min_delta_tasks: 3`
  - `r_selected_within_tasks_of_w_star_best: [1, 2]`
  - inert control guard for A1 selection
- Public artifacts pass the privacy scan for raw commit hashes, raw subjects, and reference patches.
- Relevant unit tests, py_compile, JSON validation, and `git diff --check` pass after the final run.
- Final experiment artifacts are committed, and pushed if network access is available and expected.

## Resume

The primary runner skips existing normalized results when `--force` is not set, so the next run can resume from the current public results directory after network access returns.

Recommended resume command:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/repository_local_rich_w20_primary_runner.py --phase primary --mode live --max-workers 4 --codex-provider-mode default --verifier-timeout-seconds 2400
```

After resume completes, regenerate summary and continue with analysis, privacy scan, tests, commit, and push.

## Offline Validation

Validation performed after pause:

- `PYTHONPATH=experiments/core_narrative/tools python3 -m unittest experiments/core_narrative/tools/test_repository_local_rich_w20_primary_runner.py experiments/core_narrative/tools/test_codex_cli_patch_command.py experiments/core_narrative/tools/test_click_specialist_context.py`
- `python3 -m py_compile experiments/core_narrative/tools/repository_local_rich_w20_primary_runner.py experiments/core_narrative/tools/codex_cli_patch_command.py experiments/core_narrative/tools/click_specialist_context.py`
- `find experiments/core_narrative/results/repository_local_rich_w20_v1 -type f -name '*.json' -print0 | xargs -0 -n1 jq empty`
- `git diff --check`
- Public-artifact privacy scan for raw commit hashes, raw subjects, and reference patches.
