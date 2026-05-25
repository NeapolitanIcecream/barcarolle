# Phase 1 Canonical Split Repair For Statement-Hardened Supply Runbook

Status: corrected implementation runbook, 2026-05-25.

This runbook replaces the earlier "targeted replacement supply" draft. The
current problem should not be treated as "boltons has no future tasks" until we
first repair the statement-regeneration input pool and split mapping.

The observed `boltons/H_future: 0` result came from two local design mistakes:

```text
1. The Codex-loop statement regeneration input inventory omitted old boltons
   future-holdout tasks:
     boltons__hist__022
     boltons__hist__023
     boltons__hist__027

2. The newer screen derived split eligibility from the current inventory row's
   split field. That remapped boltons__clean_ext__017 to B_eval, even though
   the frozen Phase 1 future-holdout design used it as H_future.
```

The goal of this runbook is to repair those two issues before mining new
replacement tasks.

## Starting Point

Latest valid Codex-loop result:

```text
real generator Codex CLI session completed: true
real reviewer Codex CLI session completed: true
local Codex Subscription used: true
LLM API endpoint used: false
generated statements: 22
review pass count: 22
deterministic QA pass count: 22
eligible after regeneration: 22
selected counts under flawed split map:
  attrs/B_eval: 4
  attrs/H_future: 4
  boltons/B_eval: 4
  boltons/H_future: 0
```

Important reports:

```text
experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_process.md
experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_session_proof.md
experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_statement_screen.md
experiments/phase1_compiler/reports/phase1_diff_assisted_codex_loop_recovery_decision.md
experiments/phase1_compiler/reports/phase1_preregistered_clean_future_holdout_entry_gate.md
experiments/phase1_compiler/reports/phase1_two_repo_task_outcome_matrix.md
```

The canonical Phase 1 split assignments to recover are:

```text
boltons/B_eval:
  boltons__clean_ext__001
  boltons__clean_ext__008
  boltons__clean_ext__010
  boltons__hist__011

boltons/H_future:
  boltons__clean_ext__017
  boltons__hist__022
  boltons__hist__023
  boltons__hist__027

attrs/B_eval:
  attrs__hist__001
  attrs__hist__003
  attrs__hist__004
  attrs__hist__008

attrs/H_future:
  attrs__hist__012
  attrs__hist__013
  attrs__hist__023
  attrs__hist__027
```

These assignments are split metadata only. Do not use historical pass/fail
outcomes for candidate selection.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing <repo>/docs/experiments/phase-1-targeted-statement-hardened-replacement-supply-runbook.md.

Work in <repo>. Use uv for repo-local Python tooling.
Make a cohesive git commit after every completed step that changes files. Do
not batch unrelated steps into one commit. If a step has no file changes, record
that fact in the process report and do not create an empty commit. Do not push
unless the user explicitly asks.

Main goal: fix the false boltons/H_future supply hole by restoring canonical
Phase 1 split assignments and adding any old canonical selected tasks that were
omitted from the Codex-loop statement-regeneration inventory. Only if the
canonical selected tasks still cannot pass statement generation/review/QA should
the worker recommend mining new replacement supply.

Use the user's local Codex Subscription for any generator/reviewer Codex CLI
sessions. Do not use LLM_BASE_URL / LLM_API_KEY, OPENAI_API_KEY, OpenRouter, or
provider-specific API keys for statement generation/review. The run scripts
must unset API endpoint variables before invoking codex exec.

Paid ACUT solver cells remain disabled. Do not rerun existing scoreable cells.
Do not rerun the confirmed attrs__hist__027 policy-violation cell. Do not
rewrite historical score tables. Do not claim predictive validity or paid
validation from this runbook.

Do not commit secrets, raw prompts, raw completions, raw Codex CLI logs, raw
ACUT transcripts, raw GitHub API responses, solver workspaces, verifier
workspaces, cloned external repositories, .venv, caches, raw patch bodies, full
public issue/PR bodies, raw target diffs, or large raw outputs. Commit only
small sanitized configs, prompt templates, candidate packets, generated
statements, statement digests, review verdicts, summaries, reports, and
process-file summaries.

The final user-facing summary should be simple Chinese. It should say whether
the boltons/H_future hole was a split/inventory bug, whether canonical selected
tasks now have reviewed statements, and whether a new statement-hardened
preregistration can run next.
```

## Claim Boundary

Allowed claims:

```text
canonical_split_map_recovered
missing_canonical_boltons_tasks_imported
boltons_h_future_false_hole_repaired
canonical_selected_statements_reviewed
canonical_statement_screen_ready
statement_hardened_preregistration_ready_after_split_repair
targeted_replacement_supply_still_needed
```

Disallowed claims:

```text
predictive_validity_established
production_benchmark_ranking
paid_validation_completed
old_paid_result_repaired
attrs_policy_violation_repaired
historical_pass_fail_used_for_selection
generated_statement_is_scoreable_result
```

## Core Rules

- Use canonical split assignment from frozen preregistration / entry-gate /
  matrix task membership. Do not infer split from the newer inventory row when
  the task is in the canonical split map.
- Use historical score artifacts only for task membership and split labels. Do
  not use pass/fail/policy outcomes for selection.
- Reuse existing real Codex-loop generated statements when the task already has
  review pass plus deterministic QA pass.
- Run a new real Codex CLI generator/reviewer loop only for canonical selected
  tasks missing reviewed statements.
- If a canonical task fails review or deterministic QA, mark that task as a real
  statement-supply blocker and only then recommend replacement supply.
- Paid ACUT validation remains out of scope.

## Local Subscription Rules

Use local Codex Subscription for generator/reviewer sessions:

```bash
command -v codex
command -v tmux
```

Run scripts must remove API endpoint variables:

```bash
env -u LLM_BASE_URL -u LLM_API_KEY -u OPENAI_API_KEY -u OPENROUTER_API_KEY \
  codex exec ...
```

Record only booleans about subscription use. Do not commit credentials, account
tokens, raw prompts, raw completions, or CLI logs.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_canonical_split_statement_repair.yaml
  tools/
    phase1_canonical_split_statement_repair.py
  tests/
    test_phase1_canonical_split_statement_repair.py
  results/
    phase1_canonical_split_repair_preflight.json
    phase1_canonical_split_map.json
    phase1_canonical_selected_inventory.json
    phase1_canonical_missing_statement_packets.json
    phase1_canonical_codex_loop_session_proof.json
    phase1_canonical_regenerated_statements.jsonl
    phase1_canonical_statement_reviews.json
    phase1_canonical_statement_qa.json
    phase1_canonical_statement_screen.json
    phase1_canonical_split_repair_decision.json
  reports/
    phase1_canonical_split_repair_process.md
    phase1_canonical_selected_inventory.md
    phase1_canonical_statement_reviews.md
    phase1_canonical_statement_screen.md
    phase1_canonical_split_repair_decision.md
```

If the repair succeeds, draft:

```text
docs/experiments/phase-1-statement-hardened-preregistration-after-canonical-split-repair-runbook.md
```

If the repair fails because specific canonical tasks cannot produce non-leaky
sufficient statements, draft:

```text
docs/experiments/phase-1-true-targeted-statement-hardened-replacement-supply-runbook.md
```

## Step 0: Preflight And Problem Reclassification

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, git status, and
   existing unrelated paths.
2. Read the latest Codex-loop result and the old future-holdout entry gate.
3. Reclassify the previous `boltons/H_future: 0` result as:

```text
suspected_inventory_and_split_mapping_bug
```

not yet:

```text
true_replacement_supply_needed
```

4. Verify local Codex CLI and tmux availability for any missing statement
   generation.
5. Write:

```text
experiments/phase1_compiler/configs/phase1_canonical_split_statement_repair.yaml
experiments/phase1_compiler/results/phase1_canonical_split_repair_preflight.json
experiments/phase1_compiler/reports/phase1_canonical_split_repair_process.md
```

Acceptance:

- Preflight says paid ACUT calls are disabled.
- Preflight says old pass/fail outcomes will not be used for selection.
- Preflight states that replacement mining is deferred until canonical split
  repair is attempted.

Commit:

```text
Record canonical split repair preflight
```

## Step 1: Build Canonical Split Map

Actions:

1. Add canonical split repair tooling:

```text
experiments/phase1_compiler/tools/phase1_canonical_split_statement_repair.py
experiments/phase1_compiler/tests/test_phase1_canonical_split_statement_repair.py
```

2. Build a canonical map with exactly the four repo/split groups listed in this
   runbook.
3. Cross-check the map against:

```text
experiments/phase1_compiler/reports/phase1_preregistered_clean_future_holdout_entry_gate.md
experiments/phase1_compiler/results/phase1_two_repo_task_outcome_matrix.json
```

4. Store only task IDs and split labels from score artifacts. Drop statuses,
   pass/fail counts, policy outcomes, and adapter outcomes before selection.
5. Write:

```text
experiments/phase1_compiler/results/phase1_canonical_split_map.json
```

Acceptance:

- `boltons__clean_ext__017` maps to `boltons/H_future`, not `boltons/B_eval`.
- `boltons__hist__011`, `boltons__hist__022`, `boltons__hist__023`, and
  `boltons__hist__027` are present.
- Tests prove pass/fail statuses are ignored by the split-map builder.

Commit:

```text
Build canonical Phase 1 split map
```

## Step 2: Build Canonical Selected Inventory

Actions:

1. Merge canonical selected tasks from:

```text
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_statement_screen.json
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_generated_statements.jsonl
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_statement_reviews.json
experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
experiments/phase0_headroom/candidate_sources/boltons_clean_outcome_unseen_supply_source_context.jsonl
experiments/phase0_headroom/candidate_sources/boltons_source_context.jsonl
experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/candidate_sources/attrs_clean_outcome_unseen_supply_source_context.jsonl
```

2. For each canonical task, record:

```text
task_id
repo_id
canonical_split
task_time
source_ref
source_kind
implementation_files
test_files
certification_gate_summary
existing_codex_loop_statement_digest if present
existing_review_status if present
existing_qa_status if present
needs_new_codex_loop_statement
```

3. Expected missing reviewed statements before this step:

```text
boltons__hist__011
boltons__hist__022
boltons__hist__023
boltons__hist__027
```

4. Write:

```text
experiments/phase1_compiler/results/phase1_canonical_selected_inventory.json
experiments/phase1_compiler/reports/phase1_canonical_selected_inventory.md
```

Acceptance:

- Inventory has exactly 16 canonical task rows.
- No canonical task is missing certified/source metadata without an explicit
  blocker.
- Existing reviewed statements are reused only when review and QA are both
  `pass`.

Commit:

```text
Build canonical selected task inventory
```

## Step 3: Generate Missing Canonical Statements With Real Codex Loop

Actions:

1. If `needs_new_codex_loop_statement` is non-empty, build sanitized candidate
   packets for those tasks.
2. Use target diff summaries and digests, not raw committed diffs.
3. Start real Codex CLI generator and reviewer sessions using local Codex
   Subscription:

```text
.codex-workflows/phase1-canonical-split-statement-repair-codex-loop/
  generator/process.md
  reviewer/process.md
```

4. Use the same leakage and sufficiency rubric as the previous corrected Codex
   loop.
5. Write:

```text
experiments/phase1_compiler/results/phase1_canonical_missing_statement_packets.json
experiments/phase1_compiler/results/phase1_canonical_codex_loop_session_proof.json
experiments/phase1_compiler/results/phase1_canonical_regenerated_statements.jsonl
experiments/phase1_compiler/results/phase1_canonical_statement_reviews.json
experiments/phase1_compiler/reports/phase1_canonical_statement_reviews.md
```

Acceptance:

- If no statements are missing, this step records that and makes no empty
  Codex call.
- If statements are missing, real generator and reviewer sessions must run.
- Generator/reviewer use local Codex Subscription and unset API endpoint vars.
- Every missing canonical task has a reviewer verdict.
- Raw prompts, completions, logs, and raw diffs are not committed.

Commit:

```text
Run canonical missing-task Codex statement loop
```

or if no loop is needed:

```text
Record canonical statements already reviewed
```

## Step 4: Deterministic QA And Statement Merge

Actions:

1. Run deterministic QA over all 16 canonical selected statements:

```text
existing reused statements
newly generated statements
```

2. QA must reject:

```text
raw diff markers
target commit hashes
hidden verifier text
paid status text
unclosed code fences
non-implementation editable paths
missing expected behavior
```

3. Write:

```text
experiments/phase1_compiler/results/phase1_canonical_statement_qa.json
```

Acceptance:

- All pass statements have stable digests.
- QA results distinguish reused statements from newly generated statements.
- A failure in `boltons__hist__022`, `023`, or `027` is reported as a true
  canonical statement blocker, not as "no boltons H_future exists".

Commit:

```text
Run QA for canonical selected statements
```

## Step 5: Rerun Screen With Canonical Splits

Actions:

1. Rerun the statement-hardened screen using canonical split labels only.
2. Do not infer split from `B_real`, `W_real`, task time, or current inventory
   row when the task is in the canonical split map.
3. Require:

```text
review_status: pass
deterministic_qa_status: pass
canonical_split present
```

4. Write:

```text
experiments/phase1_compiler/results/phase1_canonical_statement_screen.json
experiments/phase1_compiler/reports/phase1_canonical_statement_screen.md
```

Acceptance:

- Expected selected counts if repair succeeds:

```text
attrs/B_eval: 4
attrs/H_future: 4
boltons/B_eval: 4
boltons/H_future: 4
```

- The report explicitly says whether the previous `boltons/H_future: 0` was
  repaired by split/inventory correction.
- The report does not claim predictive validity or paid validation.

Commit:

```text
Screen canonical split repaired statements
```

## Step 6: Decide Next Branch

Actions:

1. Write:

```text
experiments/phase1_compiler/results/phase1_canonical_split_repair_decision.json
experiments/phase1_compiler/reports/phase1_canonical_split_repair_decision.md
```

2. Choose exactly one:

```text
canonical_split_repair_complete_retry_preregistration:
  All 16 canonical tasks have reviewed, QA-passed statements under the canonical
  split map.

true_targeted_replacement_supply_needed:
  One or more canonical tasks cannot produce a non-leaky sufficient statement,
  so replacement supply is genuinely needed.

blocked_on_missing_canonical_metadata:
  Certified/source metadata needed for canonical tasks is missing.

blocked_on_codex_loop:
  Local Codex generator/reviewer loop could not run for missing statements.
```

3. If repair succeeds, record this suggested follow-up path without creating or
   editing the file:

```text
docs/experiments/phase-1-statement-hardened-preregistration-after-canonical-split-repair-runbook.md
```

4. If true replacement is needed, record this suggested follow-up path without
   creating or editing the file:

```text
docs/experiments/phase-1-true-targeted-statement-hardened-replacement-supply-runbook.md
```

Acceptance:

- The decision answers whether `boltons/H_future` was a false hole.
- The decision names exact blocked or replacement task IDs if any.
- The decision does not start paid validation.
- The decision does not create or edit a follow-up runbook.

Commit:

```text
Decide canonical split repair branch
```

## Step 7: Closeout

Actions:

1. Update:

```text
experiments/phase1_compiler/reports/phase1_canonical_split_repair_process.md
```

with:

```text
steps completed
commits created
tests run
paid ACUT calls made: false
Codex Subscription statement sessions used: true/false
LLM API endpoint used for statement sessions: false
raw artifacts committed: false
canonical selected tasks: 16
canonical statements review/QA pass count
selected counts by repo/split
primary decision
next runbook path
```

2. Run:

```bash
git diff --check
git status --short
```

3. Commit closeout if files changed.

Acceptance:

- No paid ACUT calls were made.
- No raw prompts, completions, logs, raw diffs, or workspaces were committed.
- Process report agrees with JSON results.

Commit:

```text
Record canonical split repair closeout
```

## Verification Commands

At minimum:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_canonical_split_statement_repair.py

uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py \
  experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py \
  experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py \
  experiments/phase0_headroom/tools/test_workspace_acut_run.py

git diff --check
```

## Final Response Template

Use simple Chinese:

```text
这轮 runbook 完成后的结论：

1. boltons/H_future: 0 是否确认是输入池/split 映射问题。
2. 旧 canonical boltons H_future 任务是否已纳入并通过题面 review/QA。
3. 是否可以重新跑 statement-hardened preregistration，还是仍需真正补 supply。

不要说 paid validation 已经完成。
不要说 predictive validity 已经建立。
不要说旧 paid 结果被修好了。
```
