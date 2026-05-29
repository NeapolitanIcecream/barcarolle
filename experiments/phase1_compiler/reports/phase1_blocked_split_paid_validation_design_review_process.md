# Phase 1 Blocked Split Paid Validation Design Review Process

## Step 0: Preflight And Dirty-Tree Audit

What happened: preflight passed for the no-paid design review. The current branch is `codex/restart-benchmark-compiler` at commit `f565a737bc3eb2d5b0162b75b2b246d4631773a6` (`Add blocked split paid design review runbook`).

Why it matters: this run can proceed using committed inputs only. It does not need ignored raw artifacts, new paid LLM calls, or new paid ACUT solver cells.

What action it suggests next: codify the exploratory claim policy, then compute exact overlap between the frozen blocked split and completed paid score tables.

## Dirty Tree

- Tracked changes present: `false`.
- Untracked files present: `true`.
- Untracked file count: `106`.
- Classification: the untracked paths are under `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/`, matching the known external-review bundle described by the runbook.
- Action: left unstaged.

## Input Availability

- Required committed path count checked: `26`.
- Missing required paths: `[]`.
- Completed paid score tables found: `10`.
- Completed paid cost summaries found: `10`.

## Boundary

This is an exploratory design review. Post-hoc blocked split design is acceptable for Phase 1 exploration only when labeled honestly. This run does not claim formal preregistration or predictive validity.

No paid calls are required or allowed for this run. Paid calls made by this run so far: `0`.

## Starting Point

- Blocked split decision label: `blocked_split_ready_with_click_minor_risk`.
- Blocked split paid calls made: `0`.
- Completed paid decision changed: `false`.
- Predictive validity established: `false`.

## Step 1: Codify Claim Policy

What happened: the claim policy was written in `experiments/phase1_compiler/configs/phase1_blocked_split_paid_validation_design_review.yaml`, `experiments/phase1_compiler/results/phase1_blocked_split_paid_validation_design_review_claim_policy.json`, and `experiments/phase1_compiler/reports/phase1_blocked_split_paid_validation_design_review_claim_policy.md`.

Why it matters: this run now has a machine-readable guardrail that accepts post-hoc split design only for exploratory accounting and rejects formal preregistration or predictive-validity wording.

What action it suggests next: compute exact task/adapter overlap with completed score tables without imputing missing outcomes and without changing the selected split.

## Step 2: Compute Overlap And Missing Cells

What happened: the design-review tool computed exact overlap for both selected blocked splits. The same-budget split has `36/60` known tasks and `48/120` missing task/adapter cells. The expanded split has `56/90` known tasks and `68/180` missing task/adapter cells.

Why it matters: the same-budget selected score table is incomplete by `24` tasks, with `24` missing cells for `codex_workspace` and `24` missing cells for `kilo_workspace`. Missing outcomes were not imputed, and reusable cells retain committed score-table provenance.

What action it suggests next: compare the five protocol options using the exact overlap and missing-cell manifests.

## Step 3: Compare Protocol Options

What happened: five protocol options were compared. Option `B` (`same_budget_missing_cell_supplement`) is recommended, with `48` new paid cells and `72` reused cells. Option `C` and Option `D` are acceptable secondary full-rerun choices. Option `A` is not recommended because it remains incomplete, and Option `E` is not recommended because click risk is currently an accepted visible caveat rather than a stop condition.

Why it matters: the recommended protocol fills the primary selected same-budget score table at lower cost than a full rerun, while preserving the post-hoc exploratory claim boundary.

What action it suggests next: project adapter-stratified token-estimated cost for each option before packaging the later paid-execution inputs.

## Step 4: Project Cost And Latency

What happened: adapter-stratified token-estimated cost was projected for every protocol option. Option `B` needs `48` new cells with estimated new cost `$20.506944`: `$12.889248` for `codex_workspace` and `$7.617696` for `kilo_workspace`.

Why it matters: the same-budget missing-cell supplement is materially cheaper than a same-budget full rerun (`$51.26736`) while still filling the primary selected score table. Provider-billed exact cost remains unavailable because no committed `actual_provider_billed_cost_usd` value is present.

What action it suggests next: package the recommended exploratory supplement with exact reusable cells, missing cells, endpoint requirements, and stop conditions.

## Step 5: Define Reuse Policy And Ready Package

What happened: the reuse policy and ready package were written for Option `B`. The package freezes the same-budget selected split, `60` selected task IDs, `72` reusable cells, and `48` missing paid cells to run.

Why it matters: a later paid execution can use exact protocol inputs without reselecting tasks or treating reused cells as formal preregistered evidence. The package requires `LLM_BASE_URL` and `LLM_API_KEY` and forbids fallback to other LLM auth.

What action it suggests next: add focused tests and run the required consistency checks before writing the final decision.

## Step 6: Tests And Consistency Checks

What happened: focused design-review tests passed (`8 passed in 0.03s`), the full Phase 1 compiler test suite passed (`270 passed in 38.75s`), and `git diff --check` passed.

Why it matters: the generated policy, overlap, protocol, cost, and ready-package artifacts now have executable coverage for the runbook's key invariants.

What action it suggests next: write the final decision with `tests_and_diff_check_passed` set to true.
