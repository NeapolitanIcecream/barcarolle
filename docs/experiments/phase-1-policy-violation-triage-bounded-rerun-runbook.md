# Phase 1 Policy-Violation Triage And Bounded Rerun Runbook

Status: implementation runbook, 2026-05-23.

This runbook is for one dedicated Codex CLI session. Its job is to decide what
the single `attrs` H_future policy violation means, repair benchmark-side
reporting or scope bugs if they exist, and run only the smallest valid replay or
rerun needed to close the Phase 1 two-repo validation.

The current result is:

```text
decision: two_repo_paid_validation_complete_insufficient_evidence
selected repos: boltons, attrs
B_eval scoreable cells: 16
H_future scoreable cells: 15
policy violations: 1
non-scoreable cells: 1
pooled MAE: 0.479167
predictive_validity_established: false
production ranking: not_produced
```

The blocker is the `kilo_workspace` cell for `attrs__hist__027` in
`phase1_two_repo_future_holdout_attrs_h_future`.

Known local evidence at runbook creation time:

```text
score table row:
  adapter_id: kilo_workspace
  task_id: attrs__hist__027
  terminal_status: policy_violation
  scoreable_cell: False
  harness_error: True

verifier result row:
  harness_error: submission_edited_out_of_scope_paths
  changed_paths: [src/attr/_make.py]

submission row:
  changed_paths: [conftest.py, src/attr/_make.py]
  certified task changed_files:
    changelog.d/774.change.rst
    conftest.py
    src/attr/__init__.pyi
    src/attr/_funcs.py
    tests/test_hooks.py

current metrics bug to confirm:
  phase1_two_repo_future_holdout_prediction_metrics.json records the policy
  violation with harness_error=True and changed_paths=[] instead of the verifier
  detail above.
```

Do not treat the above as a final classification. The worker must verify it
from artifacts before changing conclusions.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing <repo>/docs/experiments/phase-1-policy-violation-triage-bounded-rerun-runbook.md.

Work in <repo>. Use uv for repo-local Python tooling.
Make a cohesive git commit after every completed step that changes files. Do
not batch unrelated steps into one commit. If a step has no file changes, record
that fact in the next process-report update and do not create an empty commit.
Do not push unless the user explicitly asks.

Main goal: decide whether the single attrs H_future policy violation is a real
ACUT boundary violation, a benchmark-side task-scope metadata bug, or only a
reporting bug. Repair benchmark-side bugs with tests. Do not modify Codex, Kilo,
or any ACUT internals. Do not broaden allowed paths just because the ACUT edited
them; allowed scope must be justified by target-commit or source-context
evidence before any replay or rerun.

Do not run paid ACUT cells by default. A paid rerun is allowed only if all are
true: the violation is classified as a benchmark-side infrastructure/scope bug,
deterministic replay of the existing captured diff is impossible, endpoint and
cost gates pass, and the rerun is limited to the single affected cell
attrs__hist__027 with kilo_workspace under a new repair prefix.

All paid LLM or ACUT calls must use LLM_BASE_URL plus LLM_API_KEY. If either is
missing, source ~/.zshrc and check again. Do not use local Codex/ChatGPT
subscription auth, OPENAI_API_KEY, OpenRouter variables, or provider-specific
fallback variables.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Barcarolle
may prepare workspaces, invoke configured harnesses, capture diffs, replay diffs
in fresh verifier workspaces, inject private oracle material only in verifier
workspaces, and record sanitized results. It must not reimplement ACUT search,
editing strategy, retry logic, or trace internals.

Do not commit secrets, raw prompts, raw completions, raw ACUT transcripts, raw
GitHub API responses, solver workspaces, verifier workspaces, cloned external
repositories, .venv, caches, or large raw outputs. Commit only small sanitized
configs, manifests, tools, tests, score tables, summaries, reports, decisions,
and digests. Raw artifacts must remain under ignored paths.
```

## Claim Boundary

Allowed claims:

```text
policy_violation_triaged
policy_violation_reporting_repaired
confirmed_acut_policy_violation
benchmark_scope_metadata_bug_repaired
deterministic_policy_replay_completed
single_cell_bounded_repair_rerun_completed
two_repo_metrics_recomputed_from_frozen_design
insufficient_evidence_for_predictive_validation
phase1_predictive_validation_pilot_complete
```

Disallowed claims:

```text
production_benchmark_ranking
pure_harness_effect
predictive_validity_established_with_policy_violations
predictive_validity_established_after_holdout_tuning
contamination_proof_evaluation_if_model_snapshot_unknown
validation_grade_humanize_if_commit_fallback_only
```

The worker may set `predictive_validity_established=true` only if all are true:

- selected target repos are at least `2`;
- H_future scoreable cells are at least `12`;
- policy violations are `0`;
- holdout tuning did not occur;
- metrics are computed from the frozen design or from a documented
  infrastructure repair that does not change task selection;
- the pre-registered decision logic says the validation threshold passed.

If any condition is uncertain, keep `predictive_validity_established=false`.

## Commit Discipline

Every step that changes files must be committed before continuing to the next
logical step. Use one or more commits per step when a step naturally contains
separate units, for example:

```text
Record policy violation triage preflight
Repair two repo policy violation detail reporting
Record attrs H_future policy violation triage
Classify attrs H_future policy violation
Repair attrs task scope metadata
Replay repaired attrs H_future policy cell
Run bounded attrs H_future repair cell
Update two repo repaired validation decision
Record policy violation repair closeout
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

Do not commit ignored raw paths, workspaces, external repos, caches, or secrets.

## Budget And Rerun Rules

Default plan: local-only. Do not make paid calls unless the classification step
proves a benchmark-side bug and deterministic replay cannot produce a valid
scoreable cell.

Current cumulative observed-or-conservative cost:

```text
USD 62.182946
```

Additional paid cap for this runbook:

```text
default paid cell budget: 0
maximum repair paid cells if explicitly justified: 1
incremental hard cap: USD 3
cumulative unattended stop cap: USD 70
```

Stop before paid work if:

- `LLM_BASE_URL` or `LLM_API_KEY` is missing after sourcing `~/.zshrc`;
- the classification is `confirmed_acut_policy_violation`;
- the worker would need to rerun more than the single affected
  `attrs__hist__027` / `kilo_workspace` cell;
- deterministic replay is possible but has not been attempted;
- usage import or conservative cost accounting is broken;
- the proposed rerun would overwrite the original paid prefix instead of using
  a repair prefix or sidecar repair artifact.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_policy_violation_triage_bounded_rerun.yaml
  results/
    phase1_policy_violation_triage_preflight.json
    phase1_policy_violation_triage.json
    phase1_policy_violation_classification.json
    phase1_policy_violation_repair_decision.json
    phase1_two_repo_future_holdout_prediction_metrics.json
    phase1_two_repo_future_holdout_decision.json
    phase1_mvp_closeout.json
  reports/
    phase1_policy_violation_triage_process.md
    phase1_policy_violation_triage.md
    phase1_policy_violation_classification.md
    phase1_policy_violation_repair_decision.md
    phase1_two_repo_future_holdout_prediction_metrics.md
    phase1_two_repo_future_holdout_decision.md
    phase1_mvp_closeout.md
```

If a repair replay or repair rerun is needed, use explicit sidecar names:

```text
experiments/phase0_headroom/results/
  phase1_two_repo_future_holdout_attrs_h_future_policy_repair_*.json*
  phase1_two_repo_future_holdout_attrs_h_future_policy_repair_score_table.csv
```

Raw artifacts remain ignored:

```text
experiments/phase0_headroom/results/raw/
experiments/phase0_headroom/workspaces/
experiments/phase0_headroom/external_repos/
```

Do not overwrite or delete the original paid prefix:

```text
phase1_two_repo_future_holdout_attrs_h_future
```

## Step 0: Preflight And Evidence Lock

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`,
   `codex --version` if available, and `kilo --version` if available.
2. Confirm current worktree state and record any unrelated existing changes:

```bash
git status --short --branch
git log --oneline -12
git diff --check
```

3. Confirm the current two-repo decision:

```bash
jq '{primary_decision_label, selected_repos, selected_repo_id, b_eval_scoreable_cells, h_future_scoreable_cells, policy_violation_count, non_scoreable_count, pooled_mae, predictive_validity_established, production_ranking_status, blockers, recommended_next_runbook}' \
  experiments/phase1_compiler/results/phase1_two_repo_future_holdout_decision.json
```

4. Confirm the exact policy-violation rows from score, submission, verifier, and
   metrics artifacts:

```bash
python3 - <<'PY'
import csv, json
from pathlib import Path

root = Path("experiments/phase0_headroom/results")
prefix = "phase1_two_repo_future_holdout_attrs_h_future"

print("score rows:")
with (root / f"{prefix}_score_table.csv").open(newline="") as f:
    for row in csv.DictReader(f):
        if row.get("terminal_status") == "policy_violation" or row.get("task_id") == "attrs__hist__027":
            print(row)

print("submission rows:")
for line in (root / f"{prefix}_submissions.jsonl").read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") == "attrs__hist__027" and row.get("adapter_id") == "kilo_workspace":
        print(json.dumps({
            "run_id": row.get("run_id"),
            "status": row.get("status"),
            "changed_paths": row.get("changed_paths"),
            "task_package_metadata": row.get("task_package_metadata"),
            "raw_artifacts": row.get("raw_artifacts"),
        }, indent=2))

print("verifier rows:")
for line in (root / f"{prefix}_verifier_results.jsonl").read_text().splitlines():
    row = json.loads(line)
    if row.get("task_id") == "attrs__hist__027" and row.get("adapter_id") == "kilo_workspace":
        print(json.dumps(row, indent=2))
PY
```

5. Run baseline tests:

```bash
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

Acceptance:

- the current blocker is exactly one policy violation;
- no hidden-oracle leak is present in solver workspaces;
- raw artifacts are not staged;
- the process report records the existing untracked or unrelated files;
- no paid calls are made.

Commit:

```text
Record policy violation triage preflight
```

## Step 1: Repair Policy-Violation Detail Reporting

The metrics artifact currently appears to lose verifier details for the policy
violation. The likely cause is a split-name mismatch when joining score rows and
verifier rows: score rows use `H_future`, while the two-repo scorer passes
`h_future`.

Actions:

1. Confirm the root cause in `phase1_future_holdout.py`.
2. Add a focused regression test showing that a policy violation with verifier
   detail keeps:

```text
harness_error: submission_edited_out_of_scope_paths
changed_paths: [src/attr/_make.py]
```

3. Fix the reporting join without changing scoreability or policy semantics.
4. Recompute two-repo metrics and decision:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  two-repo-score \
  --config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml
```

5. Re-run scoped tests:

```bash
uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_future_holdout.py
uv run --project experiments/phase1_compiler pytest -q
git diff --check
```

Acceptance:

- `phase1_two_repo_future_holdout_prediction_metrics.json` still records
  `policy_violation_count: 1`;
- the policy-violation detail now includes
  `harness_error: submission_edited_out_of_scope_paths`;
- the policy-violation detail now includes
  `changed_paths: ["src/attr/_make.py"]`;
- no threshold is relaxed;
- no paid calls are made.

Commit:

```text
Repair two repo policy violation detail reporting
```

If the reporting bug is already fixed, record that in the process report and do
not create an empty commit.

## Step 2: Build A Sanitized Policy-Violation Triage Report

Actions:

1. Create a small config or manifest for this runbook:

```text
experiments/phase1_compiler/configs/phase1_policy_violation_triage_bounded_rerun.yaml
```

2. Build sanitized triage artifacts:

```text
experiments/phase1_compiler/results/phase1_policy_violation_triage.json
experiments/phase1_compiler/reports/phase1_policy_violation_triage.md
```

The triage must include:

- original result prefix;
- adapter id;
- ACUT id;
- task id;
- split;
- score-table terminal status;
- verifier harness error;
- submission changed paths;
- verifier violating paths;
- certified task changed files;
- certified task test files;
- allowed context refs;
- raw patch SHA256 and diffstat only;
- whether the solver edited tests;
- whether the solver edited paths outside certified changed implementation
  files;
- whether target-commit evidence supports every path the solver edited.

3. It may read raw `submission.patch`, `acut_stdout.txt`, or `acut_stderr.txt`
   for diagnosis, but committed reports must not include full raw patch bodies,
   raw prompts, raw completions, or transcript excerpts.

Useful local command for diffstat:

```bash
git apply --stat \
  experiments/phase0_headroom/results/raw/workspace_acut/phase1_two_repo_future_holdout_attrs_h_future/kilo_workspace/phase1_two_repo_future_holdout_attrs_h_future_kilo_workspace__kilo_workspace_gpt_5_4_mini__attrs__hist__027__matrix1/submission.patch
```

Acceptance:

- committed triage artifacts are sanitized and small;
- the report makes clear that `src/attr/_make.py` is the violating path under
  the current package metadata;
- the report separates facts from classification;
- no hidden verifier outcome is used to classify scope correctness;
- no paid calls are made.

Commit:

```text
Record attrs H_future policy violation triage
```

## Step 3: Classify The Violation

Classify the violation before any replay or rerun.

Allowed classification labels:

```text
confirmed_acut_policy_violation_no_rerun
benchmark_scope_metadata_bug_replay_existing_patch
benchmark_scope_metadata_bug_paid_rerun_needed
reporting_only_bug_no_rerun
inconclusive_user_decision_needed
```

Decision rules:

- Use `confirmed_acut_policy_violation_no_rerun` if the violating path is not
  supported by target-commit changed files, certified task metadata, or
  solver-visible source context.
- Use `benchmark_scope_metadata_bug_replay_existing_patch` only if the allowed
  path list was wrong under evidence that existed before the paid run and the
  existing captured diff can be replayed deterministically.
- Use `benchmark_scope_metadata_bug_paid_rerun_needed` only if the allowed path
  list was wrong, deterministic replay is not possible, and a single-cell paid
  repair rerun is the smallest valid action.
- Use `reporting_only_bug_no_rerun` if Step 1 was the only benchmark-side bug
  and the original policy violation is otherwise genuine.
- Use `inconclusive_user_decision_needed` if the worker cannot classify without
  changing the protocol or spending more than the cap.

Important guardrail:

```text
Do not add src/attr/_make.py to allowed_code_paths merely because Kilo edited
it. The path must be justified by pre-existing benchmark evidence, not by the
ACUT's attempted solution or by hidden verifier success/failure.
```

Write:

```text
experiments/phase1_compiler/results/phase1_policy_violation_classification.json
experiments/phase1_compiler/reports/phase1_policy_violation_classification.md
```

Acceptance:

- the classification label is one of the allowed labels above;
- the report explains the evidence in simple terms;
- the report states whether paid rerun is allowed;
- the report states whether predictive validity can still be claimed;
- no paid calls are made.

Commit:

```text
Classify attrs H_future policy violation
```

## Step 4A: If The Violation Is Genuine, Close Without Rerun

Run this branch for either:

```text
confirmed_acut_policy_violation_no_rerun
reporting_only_bug_no_rerun
```

Actions:

1. Recompute two-repo metrics and decision after any reporting fix:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  two-repo-score \
  --config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml
```

2. Rebuild and validate Phase 1 closeout:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  build-mvp \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

3. Write the repair decision:

```text
experiments/phase1_compiler/results/phase1_policy_violation_repair_decision.json
experiments/phase1_compiler/reports/phase1_policy_violation_repair_decision.md
```

Acceptance:

- policy violation count remains `1`;
- predictive validity remains `false`;
- production ranking remains `not_produced`;
- the next recommended runbook does not call for more paid reruns of this same
  genuine violation;
- tests pass:

```bash
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
git diff --check
```

Commit:

```text
Close two repo validation after confirmed policy violation
```

Then skip to Step 8.

## Step 4B: If Scope Metadata Is Wrong, Repair It With Tests

Run this branch only for:

```text
benchmark_scope_metadata_bug_replay_existing_patch
benchmark_scope_metadata_bug_paid_rerun_needed
```

Actions:

1. Fix only benchmark-side metadata or package-building logic. Do not change
   ACUT behavior.
2. Add regression tests proving the intended allowed-code-path derivation.
3. Update the clean-supply overlay or derived package metadata only if the
   pre-existing source evidence justifies it.
4. Do not inspect hidden verifier success/failure to decide the allowed path
   list.

Acceptance:

- the allowed path change is evidence-backed;
- tests fail before the fix or would have caught the bug;
- no task selection changes;
- no holdout tuning;
- no paid calls are made in this step.

Commit:

```text
Repair attrs task scope metadata
```

## Step 5: Prefer Deterministic Replay Of The Existing Captured Diff

Run this step only if Step 3 classified the issue as:

```text
benchmark_scope_metadata_bug_replay_existing_patch
```

Actions:

1. Add or use benchmark-side tooling to replay the existing captured
   `submission.patch` in a fresh verifier workspace under the repaired policy.
2. Keep the original paid prefix unchanged.
3. Write repair replay outputs under an explicit repair sidecar prefix, for
   example:

```text
phase1_two_repo_future_holdout_attrs_h_future_policy_repair
```

4. Import no new usage cost because this step does not invoke an ACUT.
5. Record original run id, original patch SHA256, repaired policy metadata
   version, verifier status, and sanitized result.

Acceptance:

- exactly one cell is replayed:
  `attrs__hist__027` / `kilo_workspace`;
- the original paid artifacts remain unchanged;
- no ACUT is invoked;
- hidden oracle material is injected only into the fresh verifier workspace;
- the repaired sidecar makes clear it is a deterministic replay, not a new
  independent paid solve.

Commit:

```text
Replay repaired attrs H_future policy cell
```

Skip Step 6 unless replay is impossible and the classification is updated to
`benchmark_scope_metadata_bug_paid_rerun_needed`.

## Step 6: Optional Single-Cell Paid Repair Rerun

Run this step only if all are true:

- Step 3 classification is `benchmark_scope_metadata_bug_paid_rerun_needed`;
- deterministic replay is impossible or invalid for a documented reason;
- endpoint variables are present;
- projected cumulative cost stays below `USD 70`;
- the rerun uses a new repair prefix;
- the rerun is limited to one cell.

Actions:

1. Check endpoint variables without printing values:

```bash
zsh -lc 'source ~/.zshrc >/dev/null 2>&1 || true; test -n "$LLM_BASE_URL" && test -n "$LLM_API_KEY"'
```

2. Run only the affected cell under a repair prefix:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  run-matrix \
  --adapter-config experiments/phase0_headroom/configs/acut_workspace_adapters.yaml \
  --adapter-id kilo_workspace \
  --matrix-config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_h_future_policy_repair \
  --task-id attrs__hist__027
```

3. Import usage and summarize:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_usage_import.py \
  --root . \
  --pricing-config experiments/phase0_headroom/configs/model_pricing.yaml \
  --result-prefix phase1_two_repo_future_holdout_attrs_h_future_policy_repair

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/workspace_acut_run.py \
  --root . \
  summarize \
  --result-prefix phase1_two_repo_future_holdout_attrs_h_future_policy_repair
```

Acceptance:

- exactly one paid repair cell is run;
- usage is observed or conservatively bounded;
- no original paid prefix is overwritten;
- if the repair cell still records a policy violation, stop and keep
  predictive validity false;
- if the repair cell is scoreable, continue to Step 7.

Commit:

```text
Run bounded attrs H_future repair cell
```

## Step 7: Recompute Two-Repo Metrics And Decision

Actions:

1. If no repair replay or repair rerun was valid, recompute from the original
   prefixes after reporting fixes only.
2. If repair replay or repair rerun produced a valid replacement for the single
   affected non-scoreable cell, update scoring logic or config to consume that
   replacement as sidecar repair evidence without changing frozen task
   selection.
3. Add tests for sidecar replacement scoring if new scoring logic is added.
4. Recompute:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_future_holdout.py \
  two-repo-score \
  --config experiments/phase1_compiler/configs/phase1_two_repo_future_holdout_validation.yaml
```

5. Rebuild and validate closeout:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  build-mvp \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml

uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

Acceptance:

- frozen task ids still match the preregistration;
- replacement evidence, if used, affects only the single originally
  non-scoreable cell;
- policy violation count is correct after repair;
- predictive validity is true only if all preregistered thresholds pass;
- production ranking remains `not_produced` unless a separate committed
  protocol explicitly permits it;
- tests pass:

```bash
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
git diff --check
```

Commit:

```text
Update two repo repaired validation decision
```

## Step 8: Final Closeout

Actions:

1. Update the process report with a short, simple conclusion:

```text
experiments/phase1_compiler/reports/phase1_policy_violation_triage_process.md
```

2. Ensure the final decision names one of these terminal states:

```text
confirmed_policy_violation_validation_remains_insufficient
reporting_repaired_validation_remains_insufficient
scope_repair_replay_completed_validation_recomputed
scope_repair_paid_rerun_completed_validation_recomputed
blocked_pending_user_protocol_or_budget_decision
```

3. Run final checks:

```bash
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
git diff --check
git status --short
```

4. Confirm that no raw artifacts, workspaces, external repos, caches, or secrets
   are staged.

Acceptance:

- all committed reports are sanitized;
- final metrics and closeout agree;
- final conclusion does not overclaim;
- the next recommended runbook is specific:
  - if genuine violation: analyze attrs H_future generalization and decide
    whether to report a negative/underpowered pilot or mine a third repo;
  - if repaired and still insufficient: analyze predictive signal weakness;
  - if repaired and thresholds pass: write a separate ranking/protocol
    runbook before creating any production ranking;
  - if blocked: state exactly what user decision is needed.

Commit:

```text
Record policy violation repair closeout
```

## Final Response Requirements

The executing agent's final response to the user must be in simple Chinese.
It should state:

- whether the violation was genuine or benchmark-side;
- whether any paid rerun happened;
- final policy violation count;
- final H_future scoreable cells;
- whether predictive validity was established;
- which commit range contains the work;
- the next concrete recommendation.
