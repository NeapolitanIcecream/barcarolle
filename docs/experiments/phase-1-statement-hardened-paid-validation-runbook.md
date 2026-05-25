# Phase 1 Statement-Hardened Paid Validation Runbook

Status: implementation runbook, 2026-05-25.

This runbook is for one dedicated Codex CLI session. Its job is to execute the
statement-hardened release frozen after canonical split repair, import the paid
results, and write a bounded validation decision.

Paid validation approval is granted by the coordinating session for this
runbook. The worker does not need to ask for another user confirmation before
paid cells, but it must still pass the local entry gates, endpoint checks, cost
caps, and scoreability checks before and between paid batches.

Do not draft or create a follow-up runbook. Record recommended next actions in
the final decision and closeout reports only.

## Frozen Release

Release:

```text
release_id: statement_hardened_after_canonical_split_repair_20260525
paid_validation_prefix: phase1_statement_hardened_after_canonical_repair_paid_validation_20260525
planned adapters:
  codex_workspace
  kilo_workspace
planned cells: 32
```

Required inputs:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_release_manifest.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_preregistration.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_release_preview.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_inventory.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_screen.json
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_validation_decision.json
experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
experiments/phase0_headroom/target_profiles/boltons_target_profile.json
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
You are executing docs/experiments/phase-1-statement-hardened-paid-validation-runbook.md.

Work in the repository root. Use uv for repo-local Python tooling. Make a
cohesive git commit after every completed step that changes files. Do not batch
unrelated steps into one commit. If a step only records state, commit the small
sanitized report/result update for that step. Do not push unless the user
explicitly asks.

Paid validation approval has been granted by the coordinating session for this
runbook. You may run paid ACUT cells after the local entry gates pass. Every
paid LLM or ACUT call must use LLM_BASE_URL plus LLM_API_KEY. If either
variable is missing, source ~/.zshrc and check again before any paid call. Do
not fall back to local Codex/ChatGPT subscription auth, OPENAI_API_KEY,
OpenRouter variables, or provider-specific fallback variables.

Run the frozen statement-hardened release only. Use the frozen manifest,
statement digests, canonical split labels, and reviewed visible statements from
the after-canonical-repair artifacts. Do not rerun old scoreable cells. Do not
write into old two-repo or clean-future-holdout result prefixes. Do not repair
or overwrite historical paid results.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Barcarolle
may prepare clean solver workspaces, invoke configured ACUT workspace adapters,
capture final git diffs, replay those diffs in fresh verifier workspaces,
inject private oracle material only in verifier workspaces, and record sanitized
results. Do not implement Codex, Kilo, or another ACUT harness.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
Codex/Kilo logs, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, raw GitHub API responses, raw target diffs, or
large raw outputs. Commit only small sanitized configs, tools, tests, score
tables, cost summaries, reports, manifests, digests, and decision files. Raw
harness outputs must remain under ignored paths.

Do not draft or create the next runbook. Record only recommended next actions
in the decision and closeout reports.
```

## Endpoint Rule

Every paid call must use:

```text
LLM_BASE_URL
LLM_API_KEY
```

Before paid work, check without printing values:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

Stop before paid work if either variable is missing after sourcing `~/.zshrc`.
Do not use subscription auth, `OPENAI_API_KEY`, OpenRouter variables, or any
provider-specific fallback for paid ACUT cells.

## Claim Boundary

Allowed claims after this runbook:

```text
statement_hardened_paid_validation_run
statement_hardened_paid_cells_completed
statement_hardened_score_tables_imported
per_repo_split_paid_metrics_recorded
observed_or_conservative_cost_accounting_recorded
policy_violation_rate_recorded
predictive_validity_threshold_met
predictive_validity_threshold_not_met
paid_validation_blocked_with_precise_reason
```

Disallowed claims unless explicitly supported by final metrics:

```text
predictive_validity_established
production_benchmark_ranking
old_paid_result_repaired
attrs_policy_violation_repaired
generated_statement_is_scoreable_result
hidden_oracle_informed_statement_rewrite
same_as_old_two_repo_score
```

Interpretation rules:

- `verified_pass` and `verified_fail` are scoreable ACUT outcomes.
- `policy_violation`, `invalid_output`, `acut_harness_error`,
  `harness_error`, and `timeout` are non-scoreable or boundary failures.
- Old paid cells are historical context only and must not be merged into the new
  statement-hardened score.
- Generated statements are task statements, not scoreable results.
- `attrs__hist__027` may be included in this new frozen paid validation, but
  its old policy-violation cell remains historical and unrepaired.

## Budget And Batch Policy

Paid cells must run sequentially by adapter and repo/split batch.

```text
batch size: 4 tasks * 2 adapters = 8 cells
total planned cells: 16 tasks * 2 adapters = 32 cells
incremental hard cap for this runbook: USD 40
per-batch projected cap before starting next batch: USD 12
paid ACUT concurrency: 1
cross-harness paid parallelism: disabled
```

Stop before the next paid batch if observed-or-conservative cost cannot be
bounded, if projected total cost exceeds USD 40, or if scoreability/policy gates
fail.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_statement_hardened_after_canonical_repair_paid_validation.yaml
  tools/
    phase1_statement_hardened_after_canonical_repair_paid_validation.py
  tests/
    test_phase1_statement_hardened_after_canonical_repair_paid_validation.py
  results/
    phase1_statement_hardened_after_canonical_repair_paid_preflight.json
    phase1_statement_hardened_after_canonical_repair_paid_tooling_check.json
    phase1_statement_hardened_after_canonical_repair_paid_entry_gate.json
    phase1_statement_hardened_after_canonical_repair_paid_metrics.json
    phase1_statement_hardened_after_canonical_repair_paid_decision.json
  reports/
    phase1_statement_hardened_after_canonical_repair_paid_process.md
    phase1_statement_hardened_after_canonical_repair_paid_preflight.md
    phase1_statement_hardened_after_canonical_repair_paid_tooling_check.md
    phase1_statement_hardened_after_canonical_repair_paid_entry_gate.md
    phase1_statement_hardened_after_canonical_repair_paid_metrics.md
    phase1_statement_hardened_after_canonical_repair_paid_decision.md

experiments/phase0_headroom/
  configs/
    phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml
  results/
    phase1_statement_hardened_after_canonical_repair_attrs_b_eval_*.json*
    phase1_statement_hardened_after_canonical_repair_attrs_b_eval_score_table.csv
    phase1_statement_hardened_after_canonical_repair_attrs_h_future_*.json*
    phase1_statement_hardened_after_canonical_repair_attrs_h_future_score_table.csv
    phase1_statement_hardened_after_canonical_repair_boltons_b_eval_*.json*
    phase1_statement_hardened_after_canonical_repair_boltons_b_eval_score_table.csv
    phase1_statement_hardened_after_canonical_repair_boltons_h_future_*.json*
    phase1_statement_hardened_after_canonical_repair_boltons_h_future_score_table.csv
    workspace_usage_ledger.jsonl
    workspace_cost_reconciliation.json
```

Raw outputs must stay under ignored paths:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
experiments/phase0_headroom/external_repos/
```

## Step 0: Preflight And Approval Record

Actions:

1. Read `AGENTS.md`, this runbook, the frozen manifest, preregistration, release
   preview, inventory, and validation decision.
2. Record branch, HEAD, date, Python version, `uv --version`, `codex --version`
   if available, and `kilo --version` if available.
3. Record `git status --short --branch` and `git diff --check`.
4. Verify:

```text
release manifest status == frozen
preregistration status == written
validation decision == ready_for_user_approved_paid_validation
planned cells == 32
selected task count == 16
followup_runbook_written_by_worker == false
predictive_validity_established == false before paid validation
```

5. Verify endpoint variables without printing secret values.
6. Write preflight result and report.

Acceptance:

- User approval for this paid-validation runbook is recorded as granted by the
  coordinating session.
- Endpoint variables are present.
- Input artifact digests are recorded.
- No paid calls have run before this preflight.
- No local absolute paths or secret values are written to new committed files.

Stop if:

- the release is not frozen;
- the validation decision is not `ready_for_user_approved_paid_validation`;
- endpoint variables are missing after sourcing `~/.zshrc`;
- raw or secret material would need to be committed.

Commit:

```text
Record statement-hardened paid validation preflight
```

## Step 1: Add Statement-Hardened Workspace Loading

Current workspace ACUT tooling may not know how to build task packages directly
from the statement-hardened after-canonical-repair manifest. Add the smallest
benchmark-side loader needed for this release.

Actions:

1. Add paid-validation config files that name:

```text
release_manifest: experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_release_manifest.json
release_preview: experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_release_preview.json
inventory: experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_inventory.json
screen: experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_screen.json
attrs_certified_tasks: experiments/phase0_headroom/certified_tasks/attrs_clean_outcome_unseen_supply_certified_tasks.jsonl
boltons_clean_ext_certified_tasks: experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl
boltons_canonical_certified_tasks: experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl
adapter_config: experiments/phase0_headroom/configs/acut_workspace_adapters.yaml
```

2. Extend or wrap `workspace_acut_run.py` so `inspect-packages`,
   `preflight`, `smoke`, and `run-matrix` can select these 16 task IDs from the
   statement-hardened manifest.
3. Build each `TaskPackage` from:
   - base/target/test metadata in certified task files;
   - full solver-visible statement text from the release preview or inventory;
   - editable implementation paths and non-editable test paths from the frozen
     manifest;
   - canonical split labels from the frozen manifest.
4. Do not use raw target diffs, hidden verifier files, old paid outcomes, or raw
   ACUT transcripts to construct solver-visible statements.
5. Add focused tests. At minimum, test that:
   - all 16 canonical tasks are selectable;
   - `boltons__clean_ext__017` remains `boltons/H_future`;
   - statement text digest matches the frozen digest;
   - tests are non-editable;
   - current inventory split is not used for selection;
   - paid outcomes do not affect package loading;
   - no follow-up runbook file is created.

Acceptance:

- `inspect-packages` can select every frozen task ID.
- Package statements match frozen digests.
- Solver-visible statements contain no raw diff hunks, target commit hashes,
  hidden verifier markers, paid outcome text, or raw test assertions.
- Tests pass.
- No paid ACUT cell has run in this step.

Verification:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_paid_validation.py

uv run --project experiments/phase0_headroom pytest -q \
  experiments/phase0_headroom/tools/test_workspace_acut_run.py
```

Commit:

```text
Support statement-hardened packages in workspace validation
```

## Step 2: Local Entry Gate

Actions:

1. Run package inspection for all four repo/split groups:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  inspect-packages \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_inspect
```

2. Run adapter preflight for both adapters. Use separate result prefixes:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_codex_preflight

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  preflight \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_kilo_preflight
```

3. Confirm the matrix selects exactly the 16 frozen task IDs.
4. Confirm no results already exist under the four paid result prefixes unless
   they are from this runbook and already committed.
5. Record projected cost and the exact paid batches that will run.

Acceptance:

- Both adapter preflights are `ready`.
- Endpoint env proof is present and does not print values.
- Selected task IDs match the manifest exactly.
- No old score tables are reused.
- Projected incremental cost is below USD 40.
- Paid parallelism remains disabled.

Commit:

```text
Record statement-hardened paid entry gate
```

## Step 3: Run Paid Attrs B_eval Batch

Actions:

Run Codex and Kilo sequentially:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_attrs_b_eval \
  --task-id attrs__hist__001 \
  --task-id attrs__hist__003 \
  --task-id attrs__hist__004 \
  --task-id attrs__hist__008

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_attrs_b_eval \
  --task-id attrs__hist__001 \
  --task-id attrs__hist__003 \
  --task-id attrs__hist__004 \
  --task-id attrs__hist__008
```

Then import usage if available and summarize:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_statement_hardened_after_canonical_repair_attrs_b_eval
```

Acceptance:

- All 8 cells have terminal status.
- At least 6 cells are scoreable.
- Policy violations are 0.
- Cost remains within the per-batch and total caps.
- No hidden oracle material is present in solver workspaces.

Commit:

```text
Run statement-hardened attrs B_eval batch
```

## Step 4: Run Paid Attrs H_future Batch

Actions:

Run Codex and Kilo sequentially:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_attrs_h_future \
  --task-id attrs__hist__012 \
  --task-id attrs__hist__013 \
  --task-id attrs__hist__023 \
  --task-id attrs__hist__027

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_attrs_h_future \
  --task-id attrs__hist__012 \
  --task-id attrs__hist__013 \
  --task-id attrs__hist__023 \
  --task-id attrs__hist__027
```

Then summarize the prefix.

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_statement_hardened_after_canonical_repair_attrs_h_future
```

Acceptance:

- All 8 cells have terminal status.
- At least 6 cells are scoreable.
- Policy violations are 0.
- Cost remains within caps.
- The old historical policy violation for `attrs__hist__027` is not edited or
  relabeled; this is a new run under a new prefix.

Commit:

```text
Run statement-hardened attrs H_future batch
```

## Step 5: Run Paid Boltons B_eval Batch

Actions:

Run Codex and Kilo sequentially:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_boltons_b_eval \
  --task-id boltons__clean_ext__001 \
  --task-id boltons__clean_ext__008 \
  --task-id boltons__clean_ext__010 \
  --task-id boltons__hist__011

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_boltons_b_eval \
  --task-id boltons__clean_ext__001 \
  --task-id boltons__clean_ext__008 \
  --task-id boltons__clean_ext__010 \
  --task-id boltons__hist__011
```

Then summarize the prefix.

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_statement_hardened_after_canonical_repair_boltons_b_eval
```

Acceptance:

- All 8 cells have terminal status.
- At least 6 cells are scoreable.
- Policy violations are 0.
- Cost remains within caps.

Commit:

```text
Run statement-hardened boltons B_eval batch
```

## Step 6: Run Paid Boltons H_future Batch

Actions:

Run Codex and Kilo sequentially:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id codex_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_boltons_h_future \
  --task-id boltons__clean_ext__017 \
  --task-id boltons__hist__022 \
  --task-id boltons__hist__023 \
  --task-id boltons__hist__027

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase0_headroom/configs/phase1_statement_hardened_after_canonical_repair_workspace_matrix.yaml \
  --result-prefix phase1_statement_hardened_after_canonical_repair_boltons_h_future \
  --task-id boltons__clean_ext__017 \
  --task-id boltons__hist__022 \
  --task-id boltons__hist__023 \
  --task-id boltons__hist__027
```

Then summarize the prefix.

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_statement_hardened_after_canonical_repair_boltons_h_future
```

Acceptance:

- All 8 cells have terminal status.
- At least 6 cells are scoreable.
- Policy violations are 0.
- Cost remains within caps.

Commit:

```text
Run statement-hardened boltons H_future batch
```

## Step 7: Compute Paid Metrics And Decision

Actions:

1. Build a metrics tool or extend the paid-validation tool to read the four
   score tables and cost summaries.
2. Write:

```text
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_metrics.json
experiments/phase1_compiler/reports/phase1_statement_hardened_after_canonical_repair_paid_metrics.md
experiments/phase1_compiler/results/phase1_statement_hardened_after_canonical_repair_paid_decision.json
experiments/phase1_compiler/reports/phase1_statement_hardened_after_canonical_repair_paid_decision.md
```

3. Compute:
   - terminal status counts by repo/split and adapter;
   - scoreable pass rate by repo/split;
   - B_eval to H_future gap by repo and adapter;
   - adapter disagreement rate;
   - policy violation rate;
   - observed-or-conservative cost and latency by adapter;
   - Wilson or bootstrap intervals if practical.
4. Choose exactly one primary decision:

```text
statement_hardened_paid_validation_complete_threshold_met:
  Use only if both repos have B_eval and H_future scoreable enough, policy
  violations are 0, cost is bounded, and the pre-paid decision rule recorded in
  this runbook is met.

statement_hardened_paid_validation_complete_threshold_not_met:
  Use if all required paid batches completed but the predictive threshold or
  scoreability threshold is not met.

statement_hardened_paid_validation_blocked_non_scoreable_cells:
  Use if a paid batch ran but scoreable cells fell below the gate.

statement_hardened_paid_validation_blocked_policy_or_cost:
  Use if policy violations occur or cost cannot be bounded.

statement_hardened_paid_validation_blocked_tooling:
  Use if the workspace loader or verifier replay cannot safely support the
  frozen release.
```

Acceptance:

- Metrics are derived only from the new statement-hardened result prefixes.
- Old score tables are not merged.
- Decision says whether `predictive_validity_established` is true or false and
  why.
- If the threshold is met, the decision names the exact threshold and evidence.
- If the threshold is not met or blocked, the decision names exact repo/split
  blockers.

Commit:

```text
Compute statement-hardened paid metrics and decision
```

## Step 8: Closeout

Actions:

1. Update process report with:

```text
steps completed
commits created
tests run
paid ACUT calls made: true/false
paid cell count by repo/split
scoreable cell count by repo/split
terminal status counts
policy violation count
observed-or-conservative spend
raw artifacts committed: false
primary decision
predictive_validity_established: true/false
recommended next action
follow-up runbook written by worker: false
```

2. Run:

```bash
git diff --check
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
```

3. Confirm staged files contain no raw outputs, secrets, or local absolute
   paths:

```bash
git diff --cached --name-only
git diff --cached --check
```

Acceptance:

- Final process report agrees with JSON artifacts.
- No raw workspaces, transcripts, completions, caches, or secrets are committed.
- No follow-up runbook is created by the worker.
- Final tests pass or any failures are explained as blockers.

Commit:

```text
Record statement-hardened paid validation closeout
```

## Verification Commands

At minimum:

```bash
uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_paid_validation.py

uv run --project experiments/phase1_compiler pytest -q \
  experiments/phase1_compiler/tests/test_phase1_statement_hardened_after_canonical_repair_preregistration.py \
  experiments/phase1_compiler/tests/test_phase1_canonical_split_statement_repair.py \
  experiments/phase1_compiler/tests/test_phase1_diff_assisted_codex_loop_statement_regeneration.py \
  experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py \
  experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py \
  experiments/phase0_headroom/tools/test_workspace_acut_run.py

git diff --check
```

## Final Response Template

Use simple Chinese:

```text
这轮 paid validation 完成后的结论：

1. 32 个计划 paid cell 是否跑完。
2. 每个 repo/split 有多少 scoreable cell，pass rate 是多少。
3. 是否出现 policy violation、timeout、harness error 或 cost blocker。
4. predictive validity 是否达到预设阈值；如果没有，具体差在哪里。
5. 下一步建议是什么；注意执行 agent 不写下一份 runbook。

不要说旧 paid 结果被修好了。
不要说 attrs__hist__027 的旧 policy violation 被修好了。
不要说 generated statement 本身是 scoreable result。
```
