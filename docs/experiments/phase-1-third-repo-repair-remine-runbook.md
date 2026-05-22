# Phase 1 Third Repo Repair And Remine Runbook

Status: implementation runbook, 2026-05-22.

This runbook is for one dedicated Codex CLI session. Its job is to repair the
Itsdangerous third-repo certification path, regenerate the local Itsdangerous
task artifacts, and decide whether Phase 1 can proceed to a paid third-repo
ACUT smoke run.

This is not a paid ACUT runbook. It should spend no LLM or ACUT money. It is a
local source-adapter, candidate-filter, environment, and certification repair
runbook.

## Why This Runbook Exists

The previous hardening runbook completed successfully but stopped at an
acceptable conservative outcome:

```text
certification_implementation_bug_found
```

The hardening evidence found:

- Toolz remains the only current benchmark-grade candidate pool.
- Humanize remains diagnostic-only because nearly all usable tasks still rely on
  commit-message fallback instead of issue or PR problem context.
- Itsdangerous cannot be used yet because the generated solver statements used
  the wrong repo name, candidate selection admitted maintenance/project churn,
  and several near-certified tasks failed reference or no-op gates.

This runbook performs the missing repair/remine work that was only described at
a decision level in the previous runbook.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-third-repo-repair-remine-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

Your job is to repair and rerun the local Itsdangerous third-repo certification
path. Do not run paid ACUT task-solving cells and do not make paid LLM calls.
Local tests, local repository-history mining, GitHub metadata lookup, local
environment probes, local verifier replay, deterministic reports, and small
sanitized manifests are allowed.

The previous hardening run found that the Itsdangerous artifacts are polluted by
a statement-template bug: solver statements say "Repair the humanize behavior"
for an Itsdangerous task. Current code may already contain a regression fix, but
the committed Itsdangerous task artifacts must be regenerated from a verified
fixed implementation.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Do not
implement Codex, Kilo, or any other ACUT internals.

Do not commit secrets, raw GitHub API responses, full raw prompts, raw
completions, raw ACUT transcripts, solver workspaces, verifier workspaces,
cloned external repositories, .venv, caches, or large raw outputs. Commit only
small sanitized configs, manifests, tools, tests, reports, summaries, and
digests.

Do not push unless explicitly asked.
```

## Claim Boundary

Allowed claims:

```text
third_repo_source_adapter_repaired
third_repo_candidate_filter_repaired
third_repo_local_certification_replayed
third_repo_local_pilot_grade_candidate
third_repo_replacement_needed
insufficient_evidence_for_predictive_validation
ready_for_paid_third_repo_acut_smoke_runbook
```

Disallowed claims:

```text
predictive_validity_established
future_holdout_predictive_validity
production_benchmark_ranking
pure_harness_effect
paid_acut_validation_completed
itsdangerous_benchmark_grade_if_source_or_oracle_gates_fail
```

Important interpretation:

- Commit-message fallback is diagnostic-only and must not by itself produce a
  reviewed benchmark-grade statement.
- Issue or PR problem context can support benchmark-grade source if it is
  non-leaky and not merely a changelog/release summary.
- Passing no-op/reference gates is necessary but not sufficient. Source
  provenance, oracle alignment, scope clarity, and candidate filtering must also
  pass.
- A third repo can be considered ready for a paid ACUT smoke run only after the
  local repaired artifacts produce enough benchmark-grade candidate tasks.

## Starting Evidence

The worker should confirm these files exist:

```text
experiments/phase1_compiler/results/phase1_certification_hardening_decision.json
experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
experiments/phase1_compiler/reports/phase1_certification_hardening_decision.md
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase0_headroom/tools/test_repo_history_pilot.py
experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous.yaml
experiments/phase0_headroom/candidate_sources/itsdangerous_candidates.jsonl
experiments/phase0_headroom/candidate_sources/itsdangerous_source_context.jsonl
experiments/phase0_headroom/certified_tasks/itsdangerous_task_statements.jsonl
experiments/phase0_headroom/certified_tasks/itsdangerous_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/itsdangerous_near_certified_tasks.jsonl
experiments/phase0_headroom/releases/itsdangerous_phase0_pilot_release.json
```

Expected current facts:

```text
primary decision: certification_implementation_bug_found
recommended next runbook:
  fix_itsdangerous_statement_template_environment_and_candidate_filter_then_remine_certify_without_paid_acut
old Itsdangerous hardened benchmark candidates: 0
old Itsdangerous certified tasks: 1
old Itsdangerous near-certified tasks: 10
old Itsdangerous statements contain "humanize behavior"
```

## Budget And Runtime Rules

This runbook is local-only.

- Paid ACUT calls: disabled.
- Paid LLM calls: disabled.
- GitHub metadata lookups through `gh api`: allowed if authenticated.
- Local repository mining, local certification replay, bounded environment
  probes, deterministic report generation, and tests: allowed.
- Expected provider cost change: `0`.

If any step seems to require paid LLM or paid ACUT work, stop and write:

```text
experiments/phase1_compiler/reports/phase1_third_repo_repair_remine_blocker.md
```

with the reason and the exact proposed paid batch.

## Output Layout

Add or update:

```text
experiments/phase0_headroom/
  configs/
    third_repo_pilot_itsdangerous_repair_v2.yaml
  candidate_sources/
    itsdangerous_history_anchors.jsonl
    itsdangerous_candidates.jsonl
    itsdangerous_supply_funnel.csv
    itsdangerous_source_context.jsonl
    itsdangerous_source_context_funnel.csv
  certified_tasks/
    itsdangerous_task_statements.jsonl
    itsdangerous_review_records.jsonl
    itsdangerous_certified_tasks.jsonl
    itsdangerous_near_certified_tasks.jsonl
    itsdangerous_certification_funnel.csv
  releases/
    itsdangerous_phase0_pilot_release.json
    itsdangerous_phase0_task_table.csv
  reports/
    itsdangerous_certification_funnel.md
    itsdangerous_mini_release.md

experiments/phase1_compiler/
  results/
    phase1_third_repo_repair_remine_preflight.json
    phase1_third_repo_repair_remine_decision.json
    phase1_source_provenance_overlay.json
    phase1_oracle_alignment_audit.json
    phase1_environment_synthesis_diagnosis.json
    phase1_candidate_filter_audit.json
    phase1_hardened_certification_overlay.json
    phase1_certification_hardening_decision.json
  reports/
    phase1_third_repo_repair_remine_process.md
    phase1_third_repo_repair_remine_decision.md
    phase1_source_provenance_overlay.md
    phase1_oracle_alignment_audit.md
    phase1_environment_synthesis_diagnosis.md
    phase1_candidate_filter_audit.md
    phase1_hardened_certification_overlay.md
    phase1_certification_hardening_decision.md
```

Implementation files may be updated if needed:

```text
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase0_headroom/tools/test_repo_history_pilot.py
experiments/phase1_compiler/tools/phase1_source_certification_hardening.py
experiments/phase1_compiler/tests/test_phase1_source_certification_hardening.py
```

Historical bad Itsdangerous artifacts may be overwritten by repaired
Itsdangerous artifacts in the standard paths above. The previous state remains
available through git history and the hardening reports. Before overwriting, the
worker must write a compact preflight summary, not a full duplicate copy of the
old artifacts.

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and current git
   status.

2. Confirm previous hardening state:

```bash
jq -r '.primary_decision_label' \
  experiments/phase1_compiler/results/phase1_certification_hardening_decision.json

jq -r '.recommended_next_runbook' \
  experiments/phase1_compiler/results/phase1_certification_hardening_decision.json

jq -r '.repo_summary.itsdangerous.benchmark_grade_candidate_count' \
  experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json

jq -r '.release_status, .certified_task_count' \
  experiments/phase0_headroom/releases/itsdangerous_phase0_pilot_release.json
```

Expected:

```text
certification_implementation_bug_found
fix_itsdangerous_statement_template_environment_and_candidate_filter_then_remine_certify_without_paid_acut
0
diagnostic_only
1
```

3. Confirm the stale artifact really contains the known bug:

```bash
rg -n "Repair the humanize behavior" \
  experiments/phase0_headroom/certified_tasks/itsdangerous_task_statements.jsonl \
  experiments/phase0_headroom/certified_tasks/itsdangerous_certified_tasks.jsonl \
  experiments/phase0_headroom/certified_tasks/itsdangerous_near_certified_tasks.jsonl
```

This should find old stale records before repair.

4. Run hygiene checks:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

5. Confirm raw paths are not tracked:

```bash
git ls-files \
  experiments/phase0_headroom/results/raw \
  experiments/phase0_headroom/workspaces \
  experiments/phase0_headroom/external_repos \
  experiments/phase0_headroom/.venv \
  experiments/phase1_compiler/.venv \
  experiments/phase0_headroom/tools/__pycache__ \
  experiments/phase1_compiler/tools/__pycache__ \
  experiments/phase1_compiler/tests/__pycache__
```

6. Create:

```text
experiments/phase1_compiler/results/phase1_third_repo_repair_remine_preflight.json
experiments/phase1_compiler/reports/phase1_third_repo_repair_remine_process.md
```

The JSON should include:

```json
{
  "schema_version": "barcarolle.phase1.third_repo_repair_remine_preflight.v1",
  "paid_llm_calls_allowed": false,
  "paid_acut_calls_allowed": false,
  "starting_head": "",
  "previous_primary_decision": "certification_implementation_bug_found",
  "previous_itsdangerous_release_status": "diagnostic_only",
  "previous_itsdangerous_certified_count": 1,
  "previous_statement_template_bug_observed": true
}
```

Acceptance:

- scoped tests pass;
- Phase 1 compiler validate returns `status=valid`;
- old Itsdangerous stale statement bug is observed before repair;
- no raw, workspace, external repo, venv, or cache files are tracked;
- process report records no paid calls.

Stop if:

- existing tests fail before any change;
- Phase 1 MVP validation fails;
- old state does not match the expected hardening decision;
- raw artifacts are tracked.

Commit if the preflight report was created:

```text
Record Phase 1 third repo repair preflight
```

## Step 1: Repair Source Adapter Semantics

Purpose:

Fix the implementation before regenerating any Itsdangerous artifacts.

Actions:

1. Inspect `experiments/phase0_headroom/tools/repo_history_pilot.py`.

2. Ensure `solver_statement(candidate, refs)` uses the candidate repo ID, not a
   hard-coded repo name. The generated Itsdangerous statement must contain:

```text
Repair the itsdangerous behavior
```

and must not contain:

```text
Repair the humanize behavior
```

3. Ensure commit-message fallback is diagnostic-only by default:

- `commit_context_ref(...)` may still record sanitized commit subject/body
  digests or short summaries.
- But commit-message fallback must not be counted as non-leaky problem context
  for benchmark-grade certification.
- `allowed_context_refs` must include only issue/PR/manual/customer problem
  context, not commit-message fallback.
- If a candidate has only commit-message fallback, its statement review status
  should be `near_certified_context_missing` or another non-reviewed status,
  not `reviewed`.

4. Add candidate-filter rules to `repo_history_pilot.py` or a config-driven
   helper:

```text
reject_subject_terms:
  update dev dependencies
  update project files
  drop support
  remove deprecated
  deprecate
  typing
  lint
  format
  pre-commit
  docs
  documentation
  release
  bump
  dependabot
reject_if_project_file_heavy: true
reject_if_no_behavior_code_file: true
reject_if_changed_lines_over: 250
manual_review_if_cross_module_count_over: 3
manual_review_if_docs_or_config_change_present: true
```

5. Keep the implementation deterministic. Do not use LLM classification.

6. Add or update tests in:

```text
experiments/phase0_headroom/tools/test_repo_history_pilot.py
```

Required regression tests:

- `solver_statement` uses `itsdangerous` when the candidate repo is
  Itsdangerous.
- commit-message fallback alone does not produce `allowed_context_refs`.
- maintenance/dependency/project-file subjects are rejected before
  certification.
- large changes over 250 lines are rejected or excluded from ordinary
  certification.
- project-file-heavy changes are rejected or excluded.

Acceptance:

- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools/test_repo_history_pilot.py`
  passes.
- No current test expects commit fallback to become benchmark-grade.
- No paid calls are made.

Commit:

```text
Repair repo history source adapter for third repo remine
```

## Step 2: Add A Versioned Repair Config

Purpose:

Keep the old third-repo config as historical context and run the repaired pass
from a clearly named config.

Actions:

1. Create:

```text
experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml
```

2. Start from `third_repo_pilot_itsdangerous.yaml`, but set:

```yaml
schema_version: barcarolle.third_repo_pilot.repair_v2.v1
selected_repo_id: itsdangerous
status: selected_for_repair_remine
claim_scope: third_repo_local_repair_remine_not_predictive_validation
preferred_task_count:
  certification_attempts: 32
  pilot_certified_min: 4
  benchmark_grade_min: 6
```

3. Add explicit policy fields if the config parser supports them. If it does
   not, record the policy in comments and enforce it in the tool:

```yaml
source_policy:
  commit_message_fallback: diagnostic_only
  issue_or_pr_problem_context_required_for_benchmark_grade: true
candidate_filter_policy:
  reject_if_changed_lines_over: 250
  reject_if_project_file_heavy: true
  reject_subject_terms:
    - update dev dependencies
    - update project files
    - drop support
    - remove deprecated
    - deprecate
    - typing
    - lint
    - format
    - pre-commit
```

4. Keep the test command local and bounded. Start with the current command:

```yaml
test_environment:
  pythonpath_mode: src_if_present_else_repo_root
  command_template: uv run --project experiments/phase0_headroom --with "pytest>=9" --with "setuptools<81" python -m pytest -q {test_files}
```

5. If Step 5 later proves a better bounded environment variant, update this
   versioned config only.

Acceptance:

- the old `third_repo_pilot_itsdangerous.yaml` remains present;
- the new repair config exists;
- the new config makes clear that the run is local-only and not predictive
  validation;
- no paid ACUT adapter is invoked by this config.

Commit:

```text
Configure Itsdangerous repair remine
```

## Step 3: Re-Mine Candidates

Purpose:

Regenerate Itsdangerous candidate rows using the repaired source adapter and
candidate filter.

Actions:

1. Remove only ignored stale Itsdangerous workspaces, not tracked artifacts:

```bash
rm -rf experiments/phase0_headroom/workspaces/repo_history_pilot/itsdangerous
```

2. Run:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml \
  mine
```

3. Inspect:

```bash
wc -l experiments/phase0_headroom/candidate_sources/itsdangerous_candidates.jsonl
head -5 experiments/phase0_headroom/candidate_sources/itsdangerous_supply_funnel.csv
jq -s '{
  count: length,
  subjects: [.[:10][] | .subject],
  max_changed_lines: ([.[] | (.changed_lines_added + .changed_lines_deleted)] | max)
}' experiments/phase0_headroom/candidate_sources/itsdangerous_candidates.jsonl
```

4. Confirm rejected maintenance/project churn no longer appears among selected
   candidates:

```bash
rg -n "update dev dependencies|update project files|remove deprecated|deprecate|drop support" \
  experiments/phase0_headroom/candidate_sources/itsdangerous_candidates.jsonl || true
```

Acceptance:

- selected candidate count is greater than or equal to `8`, unless source
  supply is genuinely exhausted;
- selected candidates do not include obvious maintenance/dependency/project-file
  churn;
- selected candidates include both code and changed test files;
- no changed-line total above 250 remains in selected ordinary candidates;
- generated artifacts are deterministic enough that rerunning the command
  without code changes does not produce unexplained large diffs.

Branch:

- If fewer than `8` candidates remain, continue to Step 8 but expect a
  `replace_third_repo` or `third_repo_supply_exhausted` decision.
- Otherwise continue to Step 4.

Commit:

```text
Remine Itsdangerous candidates with repaired filter
```

## Step 4: Rebuild Source Context And Statements

Purpose:

Regenerate solver-facing Itsdangerous statements from issue/PR problem context
where available, with commit-message fallback remaining diagnostic-only.

Actions:

1. If `gh` is available and authenticated, use it. If not authenticated, do not
   block immediately; run the local fallback path and record that benchmark
   source eligibility may be low.

```bash
gh auth status || true
```

2. Run:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml \
  source-context
```

3. Confirm the stale template bug is gone:

```bash
rg -n "Repair the humanize behavior" \
  experiments/phase0_headroom/certified_tasks/itsdangerous_task_statements.jsonl \
  experiments/phase0_headroom/candidate_sources/itsdangerous_source_context.jsonl && exit 1 || true

rg -n "Repair the itsdangerous behavior" \
  experiments/phase0_headroom/certified_tasks/itsdangerous_task_statements.jsonl
```

4. Confirm commit-message fallback is not silently benchmark-grade:

```bash
jq -s '{
  statements: length,
  reviewed: map(select(.statement_review_status == "reviewed")) | length,
  context_missing: map(select(.statement_review_status != "reviewed")) | length,
  reviewed_with_commit_ref: map(select(
    .statement_review_status == "reviewed" and
    ((.allowed_context_refs // []) | any(startswith("commit:")))
  )) | length
}' experiments/phase0_headroom/certified_tasks/itsdangerous_task_statements.jsonl
```

The `reviewed_with_commit_ref` value must be `0`.

5. Inspect source context provenance:

```bash
jq -s '{
  rows: length,
  pr_rows: map(select((.ref // "") | startswith("pr:"))) | length,
  issue_rows: map(select((.ref // "") | startswith("issue:"))) | length,
  commit_rows: map(select((.ref // "") | startswith("commit:"))) | length,
  problem_context_rows: map(select(.classification == "problem_context")) | length
}' experiments/phase0_headroom/candidate_sources/itsdangerous_source_context.jsonl
```

Acceptance:

- no regenerated Itsdangerous statement says `humanize behavior`;
- all regenerated Itsdangerous statements say or imply `itsdangerous behavior`;
- `reviewed_with_commit_ref` is `0`;
- at least `4` statements have reviewed non-leaky issue/PR/manual/customer
  problem context, or the final decision must not permit paid ACUT scale-up;
- raw GitHub API responses are not committed.

Branch:

- If fewer than `4` reviewed non-leaky source statements exist, continue to
  Step 8 and prepare a replacement-repo decision.
- Otherwise continue to Step 5.

Commit:

```text
Regenerate Itsdangerous source context and statements
```

## Step 5: Re-Certify With Bounded Environment Repair

Purpose:

Run local hidden-test certification and repair only bounded environment issues.

Actions:

1. Run the certification with the current repair config:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml \
  certify
```

2. Inspect the certification funnel:

```bash
cat experiments/phase0_headroom/certified_tasks/itsdangerous_certification_funnel.csv
jq -s '{
  certified: map(select(.status == "certified")) | length,
  near_or_rejected: map(select(.status != "certified")) | length,
  first_failing_gates: group_by(.first_failing_gate) | map({gate: .[0].first_failing_gate, count: length})
}' \
  experiments/phase0_headroom/certified_tasks/itsdangerous_certified_tasks.jsonl \
  experiments/phase0_headroom/certified_tasks/itsdangerous_near_certified_tasks.jsonl
```

3. If `reference_pass` failures dominate, run a bounded environment variant
   probe. Try at most four variants:

```text
configured_command
pytest_8_with_editable:
  uv run --project experiments/phase0_headroom --with "pytest>=8,<9" --with "setuptools<81" python -m pytest -q {test_files}
pytest_7_with_editable:
  uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" python -m pytest -q {test_files}
pytest_6_with_editable:
  uv run --project experiments/phase0_headroom --with "pytest>=6,<7" --with "setuptools<81" python -m pytest -q {test_files}
```

Record only sanitized command labels, exit codes, durations, and tail hashes in
the process report. Do not commit full command output.

4. If one variant clearly makes target reference passes succeed without making
   no-op pass incorrectly, update only:

```text
experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml
```

Then rerun `certify`.

5. If `no_op_fail` failures dominate, do not weaken the gate. Classify those
   tasks as weak-oracle/no-op-pass failures and keep them out of the release.

6. If source-context gates dominate, do not turn commit fallback into reviewed
   source. Keep those tasks near-certified or diagnostic-only.

Acceptance:

- every attempted candidate has a deterministic first failing gate;
- certification does not mark commit-fallback-only tasks as benchmark-grade;
- reference-pass repair is bounded to the variants above;
- no broad dependency archaeology is performed;
- no raw command output is committed.

Branch:

- If there are at least `4` certified tasks with reviewed non-leaky source
  context, continue to Step 6.
- If there are fewer than `4` certified tasks but the failure mode is a small
  implementation bug in the adapter, fix it and rerun once.
- If there are still fewer than `4` certified tasks after one adapter repair and
  one bounded environment repair, continue to Step 8 with a replacement or
  supply-exhausted decision.

Commit:

```text
Recertify Itsdangerous after local repair
```

## Step 6: Assemble The Repaired Third-Repo Release

Purpose:

Build a repaired local Itsdangerous release manifest and split.

Actions:

1. Run:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml \
  assemble-release

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous_repair_v2.yaml \
  summarize
```

2. Inspect:

```bash
jq '{
  release_status,
  pilot_grade,
  benchmark_grade,
  certified_task_count,
  b_real_count: (.splits.B_real | length),
  w_real_count: (.splits.W_real | length),
  claim_scope
}' experiments/phase0_headroom/releases/itsdangerous_phase0_pilot_release.json
```

3. Confirm no stale statement bug was copied into certified tasks:

```bash
rg -n "Repair the humanize behavior" \
  experiments/phase0_headroom/certified_tasks/itsdangerous_certified_tasks.jsonl \
  experiments/phase0_headroom/releases/itsdangerous_phase0_pilot_release.json && exit 1 || true
```

Acceptance:

- `release_status` is `pilot_grade` only if there are at least `4` certified
  tasks and at least `2` tasks in each of `B_real` and `W_real`;
- `benchmark_grade` is true only if there are at least `6` certified tasks and
  at least `3` tasks in each of `B_real` and `W_real`;
- release `claim_scope` does not claim predictive validation;
- no stale `humanize behavior` statement remains.

Branch:

- If the release is `pilot_grade` or better, continue to Step 7.
- If the release is still `diagnostic_only`, continue to Step 8.

Commit:

```text
Assemble repaired Itsdangerous pilot release
```

## Step 7: Refresh Phase 1 Hardening Overlays

Purpose:

Recompute the Phase 1 sidecar evidence against the repaired Itsdangerous
artifacts.

Actions:

1. Run the hardening overlay tool:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_source_certification_hardening.py
```

2. Inspect:

```bash
jq '.repo_summary.itsdangerous' \
  experiments/phase1_compiler/results/phase1_source_provenance_overlay.json

jq '.repo_summary.itsdangerous' \
  experiments/phase1_compiler/results/phase1_oracle_alignment_audit.json

jq '.repo_summary.itsdangerous' \
  experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json

jq '{
  primary_decision_label,
  itsdangerous_decision,
  third_repo_should_be_repaired_or_replaced,
  predictive_validity_established
}' experiments/phase1_compiler/results/phase1_certification_hardening_decision.json
```

3. If the hardening tool still reports `statement_source_mismatch` for
   Itsdangerous, stop and fix the stale artifact or audit heuristic before
   continuing.

4. If the hardening tool still says `certification_implementation_bug_found`,
   check whether that is stale wording from the report renderer or still
   supported by current evidence. Fix stale wording if the evidence no longer
   supports it.

Acceptance:

- Itsdangerous no longer has `statement_source_mismatch` caused by `humanize`
  wording;
- hardened Itsdangerous benchmark candidate count is consistent with the
  repaired certification release;
- predictive validity remains `false`;
- the final decision does not silently mix diagnostic-only tasks into
  benchmark-grade evidence.

Branch:

- If hardened Itsdangerous benchmark candidates are at least `4`, continue to
  Step 9 with `ready_for_paid_third_repo_acut_smoke_runbook`.
- If local release is pilot-grade but hardening rejects most tasks, continue to
  Step 8 to classify the reason.
- If local release is diagnostic-only, continue to Step 8.

Commit:

```text
Refresh Phase 1 hardening overlays after Itsdangerous repair
```

## Step 8: Decide Repair, Replace, Or Stop

Purpose:

Produce a concrete decision if the repaired local run is still not enough.

Actions:

1. Classify the outcome into exactly one label:

```text
itsdangerous_ready_for_paid_acut_smoke
itsdangerous_needs_one_more_local_repair
replace_third_repo_before_paid_acut
third_repo_supply_exhausted
third_repo_environment_blocker
third_repo_source_context_blocker
```

2. Use these rules:

- `itsdangerous_ready_for_paid_acut_smoke` only if Step 7 yields at least `4`
  hardened benchmark-grade Itsdangerous candidates with a valid B/W split.
- `itsdangerous_needs_one_more_local_repair` only if there is a single narrow
  implementation issue and the worker has not already used the one allowed
  adapter repair or environment repair rerun.
- `replace_third_repo_before_paid_acut` if candidate filtering leaves too few
  candidates, source context is too weak, or oracle quality remains poor after
  bounded repair.
- `third_repo_supply_exhausted` if Itsdangerous history does not have enough
  issue/PR-backed behavior tasks.
- `third_repo_environment_blocker` if local reference runs cannot be made
  reliable without broad dependency archaeology.
- `third_repo_source_context_blocker` if GitHub metadata cannot supply
  non-leaky problem context and commit fallback is the only source.

3. If replacing the repo, choose at most two candidates from:

```text
experiments/phase0_headroom/configs/repositories.yaml
```

Prefer repos with:

- issue/PR-rich history;
- simple local Python test environment;
- behavior-level changes, not mostly dependency/project churn;
- low external-service risk.

Do not clone or run the replacement repos in this runbook unless the evidence
above is already complete and the changes are still local-only and bounded.

Acceptance:

- the decision follows from observed counts and gates;
- the report names the smallest next useful runbook;
- no paid ACUT or paid LLM call is scheduled inside this runbook;
- predictive validity remains false.

## Step 9: Write Final Repair/Remine Decision

Actions:

1. Create:

```text
experiments/phase1_compiler/results/phase1_third_repo_repair_remine_decision.json
experiments/phase1_compiler/reports/phase1_third_repo_repair_remine_decision.md
```

2. The JSON must include:

```json
{
  "schema_version": "barcarolle.phase1.third_repo_repair_remine_decision.v1",
  "starting_head": "",
  "final_head": "",
  "paid_llm_calls_made": false,
  "paid_acut_calls_made": false,
  "repo_id": "itsdangerous",
  "statement_template_bug_fixed_in_code": true,
  "statement_template_bug_absent_from_regenerated_artifacts": true,
  "commit_message_fallback_benchmark_grade_allowed": false,
  "candidate_count_after_filter": 0,
  "reviewed_non_leaky_statement_count": 0,
  "certified_task_count": 0,
  "release_status": "",
  "b_real_count": 0,
  "w_real_count": 0,
  "hardened_benchmark_candidate_count": 0,
  "primary_decision_label": "",
  "recommended_next_runbook": "",
  "allowed_claims": [],
  "disallowed_claims": []
}
```

3. The Markdown report should answer:

- Was the statement-template bug fixed in code?
- Were stale Itsdangerous artifacts regenerated?
- Did commit-message fallback remain diagnostic-only?
- How many candidates survived filtering?
- How many tasks had reviewed non-leaky source context?
- How many certified locally?
- Did the release reach pilot grade or benchmark grade?
- Did the Phase 1 hardening overlay accept enough tasks?
- Is the next step paid third-repo ACUT smoke, one more local repair, or
  replacement repo selection?

Acceptance:

- report clearly says whether Phase 1 may proceed to paid third-repo ACUT smoke;
- if it may proceed, the allowed next paid batch is only a small smoke batch in a
  future runbook, not this runbook;
- if it may not proceed, the report names the precise blocker;
- no unsupported predictive-validity claim is made.

Commit:

```text
Summarize Phase 1 third repo repair remine
```

## Step 10: Refresh Phase 1 Compiler Boundary

Purpose:

Make sure the Phase 1 MVP closeout still describes the evidence boundary after
the repaired Itsdangerous local run.

Actions:

1. Run:

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

2. Inspect:

```bash
jq '{
  release_status,
  predictive_validity_established,
  production_ranking_status,
  hardening_sidecar_evidence,
  next_runbook_recommendation
}' experiments/phase1_compiler/results/phase1_mvp_closeout.json
```

Acceptance:

- predictive-validity fields remain `false`;
- MVP closeout still distinguishes infrastructure evidence from validation
  evidence;
- repaired Itsdangerous evidence is named as sidecar/local readiness evidence
  only, unless the compiler has explicit schema support for third-repo import;
- no production ranking is produced.

Commit if generated summaries or docs changed:

```text
Refresh Phase 1 compiler boundary after third repo repair
```

## Step 11: Final Verification

Actions:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml

git status --short --ignored \
  experiments/phase0_headroom \
  experiments/phase1_compiler \
  docs/experiments \
  AGENTS.md \
  .gitignore

git ls-files \
  experiments/phase0_headroom/results/raw \
  experiments/phase0_headroom/workspaces \
  experiments/phase0_headroom/external_repos \
  experiments/phase0_headroom/.venv \
  experiments/phase1_compiler/.venv \
  experiments/phase0_headroom/tools/__pycache__ \
  experiments/phase1_compiler/tools/__pycache__ \
  experiments/phase1_compiler/tests/__pycache__
```

Acceptance:

- all scoped tests pass;
- Phase 1 compiler validate passes;
- branch is clean except ignored raw/cache/workspace/external-repo files;
- raw artifacts are not tracked;
- final repair/remine decision is committed;
- no paid calls were made.

Do not push unless the user explicitly asks this worker to push.

## Stop Conditions

Stop and write:

```text
experiments/phase1_compiler/reports/phase1_third_repo_repair_remine_blocker.md
```

if any of these occur:

- a step would require paid ACUT or paid LLM calls;
- raw GitHub responses, raw logs, workspaces, or cloned repos would need to be
  committed;
- local test failures cannot be repaired in scoped code;
- source records are inconsistent enough that regenerated artifacts would
  mislead;
- environment diagnosis would require broad dependency archaeology beyond the
  bounded variants in this runbook;
- Itsdangerous cannot produce at least `4` reviewed non-leaky candidate
  statements and the worker cannot justify a replacement decision from local
  evidence;
- hardening would force predictive-validity claims.

The blocker report must include:

```text
last completed step
blocking condition
affected files
why the worker stopped
smallest next repair
whether paid calls were made
```

## Expected End States

Strong outcome:

```text
itsdangerous_ready_for_paid_acut_smoke
```

Itsdangerous has at least four hardened benchmark-grade candidate tasks with a
valid B/W split. The next runbook may run a small paid Codex/Kilo third-repo
ACUT smoke batch under the existing endpoint and budget rules.

Acceptable outcome:

```text
replace_third_repo_before_paid_acut
```

The implementation bug is fixed and stale artifacts are regenerated, but
Itsdangerous still lacks enough source/oracle/environment quality for a useful
third-repo pilot. The next runbook should select and locally certify a
replacement repo.

Acceptable blocker outcome:

```text
third_repo_environment_blocker
```

The repaired candidate/source path is plausible, but local reference execution
cannot be made reliable without broad dependency archaeology. Stop before paid
ACUT and report the exact failing gates and bounded variants tried.

Never claim predictive validity from this runbook.
