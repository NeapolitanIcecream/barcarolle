# Phase 1 Statement-Hardened Preregistration After Canonical Split Repair Runbook

Status: implementation runbook, 2026-05-25.

This runbook is for one dedicated Codex CLI session. Its job is to freeze a
local statement-hardened preregistration from the canonical split repair output.
It must not run paid ACUT cells, paid LLM calls, or old scoreable cells.

Important boundary: do not draft or create the next runbook. Record the
recommended next action and suggested follow-up path in the decision and
closeout reports only. The coordinating user-facing session will write any
follow-up runbook.

## Starting Point

The canonical split repair completed with:

```text
primary decision: canonical_split_repair_complete_retry_preregistration
canonical selected tasks: 16
canonical review/QA pass count: 16
selected counts:
  attrs/B_eval: 4
  attrs/H_future: 4
  boltons/B_eval: 4
  boltons/H_future: 4
boltons/H_future: 0 reclassified as split/inventory bug
paid ACUT calls made: false
paid solver cells run: false
```

Required source artifacts:

```text
experiments/phase1_compiler/results/phase1_canonical_split_map.json
experiments/phase1_compiler/results/phase1_canonical_selected_inventory.json
experiments/phase1_compiler/results/phase1_canonical_statement_screen.json
experiments/phase1_compiler/results/phase1_canonical_statement_qa.json
experiments/phase1_compiler/results/phase1_canonical_statement_reviews.json
experiments/phase1_compiler/results/phase1_canonical_split_repair_decision.json
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_generated_statements.jsonl
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_statement_reviews.json
experiments/phase1_compiler/results/phase1_canonical_regenerated_statements.jsonl
experiments/phase1_compiler/reports/phase1_canonical_split_repair_process.md
experiments/phase1_compiler/reports/phase1_canonical_split_repair_decision.md
```

Canonical selected tasks:

```text
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
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing <repo>/docs/experiments/phase-1-statement-hardened-preregistration-after-canonical-split-repair-runbook.md.

Work in <repo>. Use uv for repo-local Python tooling.
Make a cohesive git commit after every completed step that changes files. Do
not batch unrelated steps into one commit. If a step has no file changes, record
that fact in the process report and do not create an empty commit. Do not push
unless the user explicitly asks.

Main goal: freeze a local statement-hardened preregistration from the canonical
split repair artifacts. Use the canonical split labels and reviewed statement
digests. Preserve the old paid results as historical observations only.

Do not run paid ACUT cells or paid LLM calls. Do not rerun old scoreable cells.
Do not rerun the confirmed attrs__hist__027 policy-violation cell. Do not
modify ACUT internals. Do not rewrite historical score tables.

Do not generate, draft, or edit the next runbook. If the tooling currently
auto-writes future runbooks, remove or bypass that side effect and record only a
recommended next action plus suggested path in JSON/Markdown decision artifacts.

Do not commit secrets, raw prompts, raw completions, raw Codex CLI logs, raw
ACUT transcripts, raw GitHub API responses, solver workspaces, verifier
workspaces, cloned external repositories, .venv, caches, raw patch bodies, raw
target diffs, full public issue/PR bodies, or large raw outputs. Commit only
small sanitized configs, tools, tests, manifests, statement digests, summaries,
reports, and short excerpts.

The final user-facing summary should be simple Chinese. It should say whether
the statement-hardened preregistration was frozen, whether paid validation is
still blocked until explicit approval, and what next action is recommended. Do
not claim predictive validity or paid validation.
```

## Research Boundary

Preserve these distinctions:

```text
historical paid observation:
  Old two-repo paid results remain immutable. They motivate this repair but are
  not corrected, rerun-equivalent, or merged into the new release score.

canonical statement-hardened preregistration:
  A local frozen release using canonical split labels, reviewed statements, and
  statement digests from the repair artifacts.

future paid validation:
  A later action requiring explicit user approval and a separate runbook written
  by the coordinating session.
```

Allowed claims:

```text
canonical_statement_hardened_preflight_recorded
canonical_statement_inputs_verified
statement_hardened_release_manifest_frozen
statement_hardened_preregistration_written
paid_validation_gate_defined
historical_paid_results_preserved
future_paid_validation_requires_user_approval
```

Disallowed claims:

```text
predictive_validity_established
production_benchmark_ranking
paid_validation_completed
old_paid_result_repaired
attrs_policy_violation_repaired
generated_statement_is_scoreable_result
hidden_oracle_informed_statement_rewrite
next_runbook_written_by_worker
```

## Commit Discipline

Every step that changes files must be committed before moving on. Use one or
more commits per step when the step naturally contains separate units.

Suggested commit messages:

```text
Record canonical preregistration preflight
Add canonical statement-hardened preregistration tooling
Verify canonical statement-hardened inputs
Freeze canonical statement-hardened release manifest
Write canonical statement-hardened preregistration
Decide canonical statement-hardened validation gate
Record canonical preregistration closeout
```

Before every commit:

```bash
git diff --check
git status --short
```

Use non-interactive git commands:

```bash
git add <paths>
git commit -m "<message>"
```

## Budget And Runtime Rules

This runbook is local-only.

```text
paid ACUT calls: disabled
paid LLM calls: disabled
Codex generator/reviewer sessions: disabled
provider cost change: USD 0
```

Stop and write a blocker if:

- any required full statement text is missing from the existing JSONL artifacts;
- any selected task lacks review pass or deterministic QA pass;
- any selected task's statement digest does not match the statement text;
- any statement contains raw diff hunks, target commit hashes, hidden verifier
  markers, paid outcome text, or raw test assertions;
- any step would require a paid ACUT call, paid LLM call, or new Codex
  generator/reviewer session;
- the worker cannot separate public solver-visible statement material from
  hidden verifier material;
- the worker would need to change ACUT internals or rewrite old score tables.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_statement_hardened_after_canonical_repair_preregistration.yaml
  tools/
    phase1_statement_hardened_after_canonical_repair_preregistration.py
  tests/
    test_phase1_statement_hardened_after_canonical_repair_preregistration.py
  results/
    phase1_statement_hardened_after_canonical_repair_preflight.json
    phase1_statement_hardened_after_canonical_repair_inventory.json
    phase1_statement_hardened_after_canonical_repair_screen.json
    phase1_statement_hardened_after_canonical_repair_release_preview.json
    phase1_statement_hardened_after_canonical_repair_release_manifest.json
    phase1_statement_hardened_after_canonical_repair_preregistration.json
    phase1_statement_hardened_after_canonical_repair_validation_decision.json
    phase1_statement_hardened_after_canonical_repair_blocker.json
  reports/
    phase1_statement_hardened_after_canonical_repair_process.md
    phase1_statement_hardened_after_canonical_repair_inventory.md
    phase1_statement_hardened_after_canonical_repair_screen.md
    phase1_statement_hardened_after_canonical_repair_release_preview.md
    phase1_statement_hardened_after_canonical_repair_preregistration.md
    phase1_statement_hardened_after_canonical_repair_validation_decision.md
    phase1_statement_hardened_after_canonical_repair_blocker.md
```

Do not create:

```text
docs/experiments/phase-1-statement-hardened-paid-validation-runbook.md
docs/experiments/phase-1-statement-hardened-replacement-supply-runbook.md
```

If one of those files already exists from earlier work, do not modify it unless
the user explicitly asks.

## Step 0: Preflight

Actions:

1. Read `AGENTS.md`, this runbook, and the canonical repair decision.
2. Record current `git status --short --branch`.
3. Verify the canonical repair decision says:

```text
primary_decision == canonical_split_repair_complete_retry_preregistration
canonical_selected_task_count == 16
canonical_review_qa_pass_count == 16
statement_hardened_preregistration_ready_after_split_repair == true
targeted_replacement_supply_still_needed == false
paid_acut_calls_made == false
paid_solver_cells_run == false
```

4. Write preflight JSON and initialize the process report.

Acceptance:

- Preflight records all required input artifact paths and their SHA256 digests.
- Preflight records any pre-existing dirty files but does not revert them.
- Preflight records that this worker must not write the next runbook.

Commit:

```text
Record canonical preregistration preflight
```

## Step 1: Add Or Update Tooling

Actions:

1. Add a canonical-repair-specific tool instead of reusing the old source-context
   truncation workflow unchanged.
2. The tool must read canonical repair artifacts and merge statement text from:

```text
experiments/phase1_compiler/results/phase1_diff_assisted_codex_loop_generated_statements.jsonl
experiments/phase1_compiler/results/phase1_canonical_regenerated_statements.jsonl
```

3. The tool must use canonical split labels from:

```text
experiments/phase1_compiler/results/phase1_canonical_split_map.json
experiments/phase1_compiler/results/phase1_canonical_statement_screen.json
```

4. The tool must not reject a task only because an old 240-character source
   excerpt was truncated. The active statement is the reviewed generated
   statement, not the old capped source excerpt.
5. The tool must not write future runbook files. If it records a next path, use
   fields such as:

```text
recommended_next_action
suggested_followup_runbook_path
followup_runbook_written_by_worker: false
```

6. Add focused tests for:

```text
canonical split labels override current inventory split
all 16 canonical tasks are required
old 240-character cap is not a rejection reason for reviewed generated statements
statement digest must match statement text
review pass plus QA pass are both required
paid outcomes do not affect selection
tool does not create docs/experiments follow-up runbook files
```

Acceptance:

- Tests fail if `boltons__clean_ext__017` is not in `boltons/H_future`.
- Tests fail if any selected canonical task is missing.
- Tests fail if a future runbook file is created by the tool.
- Tests do not require paid endpoints or Codex CLI sessions.

Verification:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_preregistration.py
```

Commit:

```text
Add canonical statement-hardened preregistration tooling
```

## Step 2: Build Canonical Inventory And Screen

Actions:

1. Run the tool in inventory/screen mode.
2. Write inventory and screen artifacts.
3. The inventory must include exactly 16 tasks from the canonical split map.
4. The screen must require:

```text
review_status == pass
deterministic_qa_status == pass
eligible_under_canonical_split_repair == true
historical_pass_fail_outcomes_used_for_selection == false
current_inventory_split_used_for_selection == false
```

5. The screen must report:

```text
attrs/B_eval: 4
attrs/H_future: 4
boltons/B_eval: 4
boltons/H_future: 4
remaining_missing_supply: {}
```

Acceptance:

- Every selected task has a full visible statement and stable digest.
- Every selected task has implementation-only editable paths and separate
  non-editable test paths.
- No paid outcome, terminal status, or policy result is used for selection.
- No raw diff, target commit, hidden verifier marker, or raw test assertion
  appears in the visible statement fields.

Commit:

```text
Verify canonical statement-hardened inputs
```

## Step 3: Freeze Release Preview And Manifest

Actions:

1. Write release preview JSON and Markdown for the 16 visible statements.
2. Write the frozen release manifest.
3. The manifest must include:

```text
release_id
created_at
input_artifact_digests
canonical selected task IDs by repo/split
statement digests
editable implementation paths
non-editable test paths
allowed public context refs
planned adapters
planned cells
paid validation prefix reserved for future run only
historical result policy
scoreability policy
```

4. Keep planned paid validation gated, not executed.

Acceptance:

- Manifest status is `frozen`.
- Planned cells are derived from selected task count times planned adapters.
- Old paid result tables are referenced only as historical immutable context.
- Preview says generated statements are solver-visible task statements, not
  scoreable results.

Commit:

```text
Freeze canonical statement-hardened release manifest
```

## Step 4: Write Preregistration

Actions:

1. Write preregistration JSON and Markdown from the frozen manifest.
2. The preregistration must define:

```text
research question
release ID
canonical split policy
task inclusion rule
statement-quality gate
scoreability rules
policy-violation handling
planned adapters
planned metrics
uncertainty metrics
cost cap placeholder
endpoint rule for future paid validation
stop conditions
historical result handling
```

3. The endpoint rule for future paid validation must require:

```text
LLM_BASE_URL
LLM_API_KEY
```

4. The preregistration must explicitly say:

```text
paid validation has not started
predictive validity has not been established
old paid results are not repaired or overwritten
attrs__hist__027 old policy violation is not repaired by this local preregistration
future paid validation requires explicit user approval and a separate runbook
```

Acceptance:

- Preregistration is complete enough for a future paid-validation runbook.
- It does not authorize paid calls.
- It does not create the future paid-validation runbook.

Commit:

```text
Write canonical statement-hardened preregistration
```

## Step 5: Decide Validation Gate

Actions:

1. Write validation decision JSON and Markdown.
2. Choose exactly one:

```text
ready_for_user_approved_paid_validation:
  Use only if manifest and preregistration were frozen successfully.

blocked_on_canonical_statement_inputs:
  Use if any selected task lacks reviewed/QA-passed statement material.

blocked_on_policy_or_scope:
  Use if any statement leaks forbidden material or editable scope is unsafe.

blocked_on_tooling:
  Use if local deterministic tooling cannot produce reproducible artifacts.
```

3. If ready, record:

```text
recommended_next_action: ask user whether to authorize paid validation runbook
suggested_followup_runbook_path: docs/experiments/phase-1-statement-hardened-paid-validation-runbook.md
followup_runbook_written_by_worker: false
paid_validation_blocked_until_user_approval: true
```

4. If blocked, record exact task IDs and reasons.

Acceptance:

- The decision states whether the release is frozen.
- It states whether paid validation is still blocked.
- It recommends the next action without writing a next runbook.
- It does not claim predictive validity.

Commit:

```text
Decide canonical statement-hardened validation gate
```

## Step 6: Closeout

Actions:

1. Update the process report with:

```text
steps completed
commits created
tests run
paid ACUT calls made: false
paid LLM calls made: false
Codex generator/reviewer sessions started: false
raw artifacts committed: false
release frozen: true/false
preregistration written: true/false
primary decision
recommended next action
suggested follow-up runbook path
follow-up runbook written by worker: false
```

2. Run:

```bash
git diff --check
git status --short
```

3. If closeout changed files, commit them.

Acceptance:

- Process report agrees with JSON artifacts.
- No paid calls were made.
- No future runbook file was created or modified by this runbook.
- Worktree status contains only intentional changes or pre-existing unrelated
  files.

Commit:

```text
Record canonical preregistration closeout
```

## Verification Commands

At minimum:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_preregistration.py

uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_canonical_split_statement_repair.py \
  experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py \
  experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py \
  experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py \
  experiments/phase0_headroom/tools/test_workspace_acut_run.py

git diff --check
```

If broader code paths were touched, expand the test scope accordingly.

## Final Response Template

Use simple Chinese:

```text
这轮 runbook 完成后的结论：

1. 是否成功冻结 statement-hardened preregistration。
2. 16 个 canonical 任务是否都进入 manifest，并且题面 review/QA 是否通过。
3. paid validation 是否仍然需要用户明确批准。
4. 建议下一步做什么；注意这里只是建议，不是执行 agent 写了下一份 runbook。

不要说 predictive validity 已经建立。
不要说 paid validation 已经完成。
不要说旧 paid 结果被修好了。
不要说 attrs__hist__027 的旧 policy violation 被修好了。
```
