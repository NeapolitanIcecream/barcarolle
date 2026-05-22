# Phase 1 Third Repo Replacement Selection Runbook

Status: implementation runbook, 2026-05-22.

This runbook is for one dedicated Codex CLI session. Its job is to replace
Itsdangerous as the Phase 1 third target repo candidate by locally screening,
mining, sourcing, certifying, and hardening one replacement repo before any paid
ACUT smoke run.

This is a local-only runbook. It should make no experiment LLM calls and no paid
ACUT calls. Network access is allowed only for cloning target repos and fetching
sanitized GitHub issue/PR metadata.

## Why This Runbook Exists

The previous runbook repaired the Itsdangerous path and proved that:

- the statement-template bug was fixed;
- stale Itsdangerous artifacts were regenerated;
- Itsdangerous reached local `pilot_grade` with `4` certified tasks;
- Phase 1 hardening still accepted `0` benchmark-grade Itsdangerous candidates;
- the final decision was `replace_third_repo_before_paid_acut`.

The next useful step is not to spend ACUT money on Itsdangerous. The next useful
step is to find a replacement third repo that can produce enough hardened local
benchmark-grade candidates to justify a small future paid ACUT smoke run.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-third-repo-replacement-selection-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

Your job is to replace Itsdangerous as the Phase 1 third target repo candidate.
Start with boltons. If boltons cannot produce enough hardened benchmark-grade
local candidates, try attrs. Do not run paid ACUT task-solving cells and do not
make experiment LLM calls. Local tests, local repository-history mining, GitHub
metadata lookup, local environment probes, local verifier replay, deterministic
reports, and small sanitized manifests are allowed.

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
third_repo_replacement_local_screening
third_repo_replacement_source_adapter_hardening
third_repo_replacement_local_certification
third_repo_replacement_hardening_overlay
ready_for_paid_third_repo_acut_smoke_runbook
replacement_repo_selection_blocked
insufficient_evidence_for_predictive_validation
```

Disallowed claims:

```text
predictive_validity_established
future_holdout_predictive_validity
production_benchmark_ranking
pure_harness_effect
paid_acut_validation_completed
replacement_repo_benchmark_grade_if_source_or_oracle_gates_fail
```

Important interpretation:

- Itsdangerous is now historical diagnostic evidence, not the active third repo.
- Commit-message fallback is diagnostic-only and must not produce
  benchmark-grade source eligibility.
- Issue, PR, issue-comment, PR-comment, manual, or customer problem context can
  support benchmark-grade source if non-leaky.
- A repo is ready for a future paid third-repo ACUT smoke run only if the local
  hardening overlay accepts at least `4` benchmark-grade candidates with a valid
  B/W split.
- This runbook may say a future paid smoke is allowed. It must not run that
  smoke itself.

## Candidate Order

Try candidates in this order:

```text
1. boltons
2. attrs
```

Use `boltons` first because it has a simple Python test environment, low
external-service risk, and a broader utility surface than Itsdangerous. Use
`attrs` second because it has high expected history supply and low
external-service risk, but a broader hatch/test dependency surface.

Do not try `rich` or `requests` in this runbook unless both preferred candidates
are impossible and the worker can justify a local-only bounded probe without
expanding the task.

## Starting Evidence

Confirm these files exist:

```text
experiments/phase1_compiler/results/phase1_third_repo_repair_remine_decision.json
experiments/phase1_compiler/reports/phase1_third_repo_repair_remine_decision.md
experiments/phase1_compiler/results/phase1_certification_hardening_decision.json
experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
experiments/phase0_headroom/configs/repositories.yaml
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase0_headroom/tools/test_repo_history_pilot.py
experiments/phase1_compiler/tools/phase1_source_certification_hardening.py
experiments/phase1_compiler/tests/test_phase1_source_certification_hardening.py
```

Expected current facts:

```text
third repo repair/remine decision: replace_third_repo_before_paid_acut
recommended next runbook: select_replacement_third_repo_and_locally_certify_without_paid_acut
Itsdangerous local release status: pilot_grade
Itsdangerous hardened benchmark candidates: 0
predictive validity: false
```

## Budget And Runtime Rules

This runbook is local-only.

- Paid ACUT calls: disabled.
- Experiment paid LLM calls: disabled.
- GitHub metadata lookup through `gh api`: allowed if authenticated.
- `git clone` or `git fetch` into ignored `external_repos` paths: allowed.
- Local repository mining, certification replay, bounded environment probes,
  deterministic reports, and tests: allowed.
- Expected provider cost change: `0`.

If any step requires paid ACUT or experiment LLM calls, stop and write:

```text
experiments/phase1_compiler/reports/phase1_third_repo_replacement_selection_blocker.md
```

with the reason and exact proposed paid batch.

## Output Layout

Add or update:

```text
experiments/phase0_headroom/
  configs/
    third_repo_replacement_boltons_v1.yaml
    third_repo_replacement_attrs_v1.yaml
  candidate_sources/
    boltons_history_anchors.jsonl
    boltons_candidates.jsonl
    boltons_supply_funnel.csv
    boltons_source_context.jsonl
    boltons_source_context_funnel.csv
    attrs_history_anchors.jsonl
    attrs_candidates.jsonl
    attrs_supply_funnel.csv
    attrs_source_context.jsonl
    attrs_source_context_funnel.csv
  certified_tasks/
    boltons_task_statements.jsonl
    boltons_review_records.jsonl
    boltons_certified_tasks.jsonl
    boltons_near_certified_tasks.jsonl
    boltons_certification_funnel.csv
    attrs_task_statements.jsonl
    attrs_review_records.jsonl
    attrs_certified_tasks.jsonl
    attrs_near_certified_tasks.jsonl
    attrs_certification_funnel.csv
  releases/
    boltons_phase0_pilot_release.json
    boltons_phase0_task_table.csv
    attrs_phase0_pilot_release.json
    attrs_phase0_task_table.csv
  reports/
    boltons_certification_funnel.md
    boltons_mini_release.md
    attrs_certification_funnel.md
    attrs_mini_release.md

experiments/phase1_compiler/
  configs/
    phase1_third_repo_replacement_selection.yaml
  results/
    phase1_third_repo_replacement_selection_preflight.json
    phase1_third_repo_replacement_candidate_screen.json
    phase1_third_repo_replacement_selection_decision.json
    phase1_source_provenance_overlay.json
    phase1_oracle_alignment_audit.json
    phase1_environment_synthesis_diagnosis.json
    phase1_candidate_filter_audit.json
    phase1_hardened_certification_overlay.json
    phase1_certification_hardening_decision.json
  reports/
    phase1_third_repo_replacement_selection_process.md
    phase1_third_repo_replacement_candidate_screen.md
    phase1_third_repo_replacement_selection_decision.md
    phase1_source_provenance_overlay.md
    phase1_oracle_alignment_audit.md
    phase1_environment_synthesis_diagnosis.md
    phase1_candidate_filter_audit.md
    phase1_hardened_certification_overlay.md
    phase1_certification_hardening_decision.md
```

Implementation files may be updated:

```text
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase0_headroom/tools/test_repo_history_pilot.py
experiments/phase1_compiler/tools/phase1_source_certification_hardening.py
experiments/phase1_compiler/tests/test_phase1_source_certification_hardening.py
experiments/phase1_compiler/tools/phase1_compiler.py
experiments/phase1_compiler/tests/test_phase1_compiler.py
experiments/phase1_compiler/README.md
```

Do not commit cloned repositories or workspaces under:

```text
experiments/phase0_headroom/external_repos/
experiments/phase0_headroom/workspaces/
```

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and current git
   status.

2. Confirm previous decision:

```bash
jq -r '.primary_decision_label' \
  experiments/phase1_compiler/results/phase1_third_repo_repair_remine_decision.json

jq -r '.recommended_next_runbook' \
  experiments/phase1_compiler/results/phase1_third_repo_repair_remine_decision.json

jq -r '.hardened_benchmark_candidate_count' \
  experiments/phase1_compiler/results/phase1_third_repo_repair_remine_decision.json

jq -r '.predictive_validity_established' \
  experiments/phase1_compiler/results/phase1_certification_hardening_decision.json
```

Expected:

```text
replace_third_repo_before_paid_acut
select_replacement_third_repo_and_locally_certify_without_paid_acut
0
false
```

3. Run baseline checks:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

4. Confirm ignored raw/workspace/external-repo/cache paths are not tracked:

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

5. Create:

```text
experiments/phase1_compiler/results/phase1_third_repo_replacement_selection_preflight.json
experiments/phase1_compiler/reports/phase1_third_repo_replacement_selection_process.md
```

The JSON should include:

```json
{
  "schema_version": "barcarolle.phase1.third_repo_replacement_selection_preflight.v1",
  "paid_llm_calls_allowed": false,
  "paid_acut_calls_allowed": false,
  "starting_head": "",
  "previous_decision": "replace_third_repo_before_paid_acut",
  "candidate_order": ["boltons", "attrs"],
  "predictive_validity_established": false
}
```

Acceptance:

- scoped tests pass;
- Phase 1 compiler validate returns `status=valid`;
- previous decision is `replace_third_repo_before_paid_acut`;
- no raw, workspace, external repo, venv, or cache files are tracked;
- process report records no paid calls.

Stop if:

- existing tests fail before any change;
- Phase 1 MVP validation fails;
- previous decision does not say to replace Itsdangerous;
- raw artifacts are tracked.

Commit if the preflight artifacts were created:

```text
Record Phase 1 replacement repo preflight
```

## Step 1: Generalize Replacement-Repo Support

Purpose:

Make sure the repo-history and Phase 1 hardening tools can handle a replacement
third repo without hard-coding Itsdangerous.

Actions:

1. Inspect:

```text
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase1_compiler/tools/phase1_source_certification_hardening.py
```

2. Ensure `repo_history_pilot.py` remains generic:

- task IDs use the selected repo ID;
- solver statements use the selected repo ID;
- scope boundaries use the selected repo ID;
- target profiles, candidates, source context, certified rows, and releases are
  written under `<repo_id>_*` names;
- commit-message fallback remains diagnostic-only;
- candidate filtering applies to all replacement repos, not only
  Itsdangerous.

3. Add or keep tests in:

```text
experiments/phase0_headroom/tools/test_repo_history_pilot.py
```

Required tests:

- `solver_statement` uses `boltons` when candidate repo is `boltons`;
- `stable_task_id("boltons", 1)` returns `boltons__hist__001`;
- commit-message fallback does not produce reviewed benchmark source;
- maintenance/dependency/project-file churn is filtered for arbitrary repo IDs;
- source artifacts do not contain full raw PR or issue bodies.

4. Generalize `phase1_source_certification_hardening.py` so the active target
   repo list is not permanently fixed to `("toolz", "humanize", "itsdangerous")`.
   Use one of these approaches:

- preferred: read active third repo from
  `experiments/phase1_compiler/configs/phase1_third_repo_replacement_selection.yaml`;
- acceptable: discover the selected replacement repo from
  `phase1_third_repo_replacement_selection_decision.json`;
- fallback: include `boltons` and `attrs` in a config-driven allowlist and mark
  non-selected repos as diagnostic comparison only.

5. Itsdangerous should remain visible as archived/replaced evidence, but the
   active hardening overlay should focus on:

```text
toolz
humanize
<selected replacement repo>
```

6. Add or update tests in:

```text
experiments/phase1_compiler/tests/test_phase1_source_certification_hardening.py
```

Required tests:

- a selected replacement repo appears in source provenance and hardened overlay
  summaries;
- Itsdangerous can be marked replaced without being counted as the active third
  repo;
- hardening does not treat commit-message fallback as benchmark-grade for the
  replacement repo;
- predictive validity remains false.

Acceptance:

- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools/test_repo_history_pilot.py`
  passes;
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_source_certification_hardening.py`
  passes;
- hardening can include a non-Itsdangerous replacement repo;
- no paid calls are made.

Commit:

```text
Generalize Phase 1 third repo replacement support
```

## Step 2: Create Replacement Configs

Purpose:

Create explicit local-only configs for `boltons` and `attrs`.

Actions:

1. Create:

```text
experiments/phase0_headroom/configs/third_repo_replacement_boltons_v1.yaml
experiments/phase0_headroom/configs/third_repo_replacement_attrs_v1.yaml
experiments/phase1_compiler/configs/phase1_third_repo_replacement_selection.yaml
```

2. `third_repo_replacement_boltons_v1.yaml` should contain:

```yaml
schema_version: barcarolle.third_repo_replacement.v1
selected_repo_id: boltons
status: selected_for_local_replacement_screen
repo_url: https://github.com/mahmoud/boltons.git
local_repo: experiments/phase0_headroom/external_repos/boltons
claim_scope: third_repo_replacement_local_screen_not_predictive_validation
paid_acut_calls: disabled
paid_llm_calls: disabled
source_policy:
  commit_message_fallback: diagnostic_only
  issue_or_pr_problem_context_required_for_benchmark_grade: true
candidate_filter_policy:
  reject_if_changed_lines_over: 250
  reject_if_project_file_heavy: true
  reject_if_no_behavior_code_file: true
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
    - docs
    - documentation
    - release
    - bump
    - dependabot
test_environment:
  pythonpath_mode: src_if_present_else_repo_root
  command_template: uv run --project experiments/phase0_headroom --with "pytest>=8,<9" --with "setuptools<81" python -m pytest -q {test_files}
preferred_task_count:
  certification_attempts: 32
  pilot_certified_min: 4
  benchmark_grade_min: 6
acut:
  adapters: []
  result_prefix: phase1_validation_third_repo_boltons_replacement_v1
budget:
  expected_provider_cost_change_usd: 0
```

3. `third_repo_replacement_attrs_v1.yaml` should contain:

```yaml
schema_version: barcarolle.third_repo_replacement.v1
selected_repo_id: attrs
status: fallback_selected_for_local_replacement_screen
repo_url: https://github.com/python-attrs/attrs.git
local_repo: experiments/phase0_headroom/external_repos/attrs
claim_scope: third_repo_replacement_local_screen_not_predictive_validation
paid_acut_calls: disabled
paid_llm_calls: disabled
source_policy:
  commit_message_fallback: diagnostic_only
  issue_or_pr_problem_context_required_for_benchmark_grade: true
candidate_filter_policy:
  reject_if_changed_lines_over: 250
  reject_if_project_file_heavy: true
  reject_if_no_behavior_code_file: true
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
    - docs
    - documentation
    - release
    - bump
    - dependabot
test_environment:
  pythonpath_mode: src_if_present_else_repo_root
  command_template: uv run --project experiments/phase0_headroom --with "pytest>=8,<9" --with "setuptools<81" python -m pytest -q {test_files}
preferred_task_count:
  certification_attempts: 32
  pilot_certified_min: 4
  benchmark_grade_min: 6
acut:
  adapters: []
  result_prefix: phase1_validation_third_repo_attrs_replacement_v1
budget:
  expected_provider_cost_change_usd: 0
```

4. `phase1_third_repo_replacement_selection.yaml` should contain:

```yaml
schema_version: barcarolle.phase1_third_repo_replacement_selection.v1
status: configured
claim_scope: third_repo_replacement_local_screening
predictive_validity_established: false
paid_acut_calls: disabled
paid_llm_calls: disabled
candidate_order:
  - boltons
  - attrs
active_selection:
  repo_id: ""
  selection_status: pending
readiness_gates:
  min_hardened_benchmark_candidates_for_paid_smoke: 4
  min_certified_for_pilot: 4
  min_certified_for_benchmark_candidate: 6
  min_b_real: 2
  min_w_real: 2
```

5. Do not put secrets or endpoint keys in these configs.

Acceptance:

- both repo configs exist and point to ignored `external_repos` paths;
- paid calls are explicitly disabled;
- Phase 1 selection config has no active repo yet;
- configs do not claim predictive validation.

Commit:

```text
Configure Phase 1 replacement repo candidates
```

## Step 3: Materialize Candidate Repos

Purpose:

Clone or refresh the local target repos under ignored paths.

Actions:

1. Confirm ignored path:

```bash
git check-ignore -v experiments/phase0_headroom/external_repos/boltons || true
git check-ignore -v experiments/phase0_headroom/external_repos/attrs || true
```

2. Clone `boltons` if absent:

```bash
mkdir -p experiments/phase0_headroom/external_repos
if [ ! -d experiments/phase0_headroom/external_repos/boltons/.git ]; then
  git clone https://github.com/mahmoud/boltons.git \
    experiments/phase0_headroom/external_repos/boltons
fi
```

3. Fetch latest metadata for `boltons` without changing branch state
   destructively:

```bash
git -C experiments/phase0_headroom/external_repos/boltons fetch --tags --prune
git -C experiments/phase0_headroom/external_repos/boltons status --short --branch
```

4. Do not clone `attrs` yet unless `boltons` fails screening. If `boltons`
   fails later, repeat the same clone/fetch commands for `attrs`.

5. Record clone/fetch commit heads in:

```text
experiments/phase1_compiler/reports/phase1_third_repo_replacement_selection_process.md
```

Acceptance:

- external repos remain untracked;
- worker records selected repo HEAD and default branch;
- no local target repo changes are committed;
- no paid calls are made.

Commit only if process/preflight reports changed:

```text
Record replacement repo materialization
```

## Step 4: Screen Candidate Supply

Purpose:

Quickly determine whether the candidate repo has enough code-plus-test,
non-maintenance history supply.

Actions for the active candidate repo, starting with `boltons`:

1. Run mining:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_replacement_boltons_v1.yaml \
  mine
```

For `attrs`, use `third_repo_replacement_attrs_v1.yaml`.

2. Inspect candidate count and supply:

```bash
jq -s '{
  count: length,
  subjects: [.[:12][] | .subject],
  max_changed_lines: ([.[] | (.changed_lines_added + .changed_lines_deleted)] | max // 0),
  modules: ([.[] | (.module_or_package // [])[]] | unique)
}' experiments/phase0_headroom/candidate_sources/boltons_candidates.jsonl

cat experiments/phase0_headroom/candidate_sources/boltons_supply_funnel.csv | head -20
```

3. Confirm obvious maintenance/project churn is absent:

```bash
rg -n "update dev dependencies|update project files|remove deprecated|deprecate|drop support|pre-commit|format|lint|typing" \
  experiments/phase0_headroom/candidate_sources/boltons_candidates.jsonl || true
```

4. Write or update:

```text
experiments/phase1_compiler/results/phase1_third_repo_replacement_candidate_screen.json
experiments/phase1_compiler/reports/phase1_third_repo_replacement_candidate_screen.md
```

The screen JSON should include one row per screened repo:

```json
{
  "repo_id": "boltons",
  "screen_status": "candidate_supply_ok|candidate_supply_low|screen_failed",
  "candidate_count_after_filter": 0,
  "max_changed_lines": 0,
  "maintenance_subject_hits": 0,
  "local_repo_head": "",
  "next_action": ""
}
```

Acceptance:

- candidate count after filter is at least `12` for a strong candidate, at least
  `8` for a usable candidate;
- selected candidates have both code and changed test files;
- maintenance/project churn is not present among selected candidates;
- generated artifacts are deterministic enough for local use.

Branch:

- If `boltons` has at least `8` candidates, continue with `boltons`.
- If `boltons` has fewer than `8` candidates, clone/screen `attrs`.
- If both have fewer than `8`, continue to Step 11 with
  `replacement_repo_supply_blocked`.

Commit:

```text
Screen replacement repo candidate supply
```

## Step 5: Build Source Context

Purpose:

Regenerate source context and solver-facing statements for the active candidate
repo, using issue/PR problem context where available.

Actions:

1. Confirm GitHub CLI state:

```bash
gh auth status || true
```

If `gh` is not authenticated, continue once with available metadata and record
the limitation. Do not block unless source yield is too low.

2. Run:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_replacement_boltons_v1.yaml \
  source-context
```

For `attrs`, use its config.

3. Inspect source yield:

```bash
jq -s '{
  statements: length,
  reviewed: map(select(.statement_review_status == "reviewed")) | length,
  context_missing: map(select(.statement_review_status != "reviewed")) | length,
  reviewed_with_commit_ref: map(select(
    .statement_review_status == "reviewed" and
    ((.allowed_context_refs // []) | any(startswith("commit:")))
  )) | length
}' experiments/phase0_headroom/certified_tasks/boltons_task_statements.jsonl

jq -s '{
  rows: length,
  pr_rows: map(select((.ref // "") | startswith("pr:"))) | length,
  issue_rows: map(select((.ref // "") | startswith("issue:"))) | length,
  commit_rows: map(select((.ref // "") | startswith("commit:"))) | length,
  problem_context_rows: map(select(.classification == "problem_context")) | length
}' experiments/phase0_headroom/candidate_sources/boltons_source_context.jsonl
```

4. If fewer than `8` reviewed non-leaky source statements exist, improve the
   deterministic source adapter before giving up:

- parse PR body and title for `Fixes #N`, `Closes #N`, `Refs #N`, `Resolves #N`;
- fetch linked issue metadata through `gh api`;
- store only sanitized fields: ref, title/summary, body digest or short summary,
  source kind, classification, leakage flag;
- do not commit raw API responses;
- do not use LLM classification.

5. Add tests for linked issue extraction and raw-response hygiene if the source
   adapter is extended.

Acceptance:

- `reviewed_with_commit_ref` is `0`;
- at least `8` statements have reviewed non-leaky issue/PR/manual/customer
  problem context for a strong candidate, at least `4` for a minimum paid-smoke
  candidate;
- every statement uses the active repo ID, not `humanize` or `itsdangerous`;
- raw GitHub responses are not committed.

Branch:

- If the active repo has at least `8` reviewed source statements, continue.
- If it has `4-7`, continue but expect only paid-smoke readiness if hardening
  accepts at least `4`.
- If it has fewer than `4`, try the next candidate repo.
- If both candidates have fewer than `4`, continue to Step 11 with
  `replacement_repo_source_blocked`.

Commit:

```text
Build replacement repo source context
```

## Step 6: Certify With Bounded Environment Repair

Purpose:

Run local hidden-test certification for the active candidate repo and repair
only bounded environment issues.

Actions:

1. Remove ignored workspaces for the active repo:

```bash
rm -rf experiments/phase0_headroom/workspaces/repo_history_pilot/boltons
```

For `attrs`, remove its workspace path.

2. Run:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_replacement_boltons_v1.yaml \
  certify
```

3. Inspect:

```bash
cat experiments/phase0_headroom/certified_tasks/boltons_certification_funnel.csv

jq -s '{
  certified: map(select(.status == "certified")) | length,
  near_or_rejected: map(select(.status != "certified")) | length,
  first_failing_gates: group_by(.first_failing_gate) | map({gate: .[0].first_failing_gate, count: length})
}' \
  experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl \
  experiments/phase0_headroom/certified_tasks/boltons_near_certified_tasks.jsonl
```

4. If `reference_pass` failures dominate, run bounded local environment probes.
   Try at most four variants for `boltons`:

```text
configured_command
pytest_8_with_editable:
  uv run --project experiments/phase0_headroom --with "pytest>=8,<9" --with "setuptools<81" python -m pytest -q {test_files}
pytest_7_with_editable:
  uv run --project experiments/phase0_headroom --with "pytest>=7,<8" --with "setuptools<81" python -m pytest -q {test_files}
pytest_6_with_editable:
  uv run --project experiments/phase0_headroom --with "pytest>=6,<7" --with "setuptools<81" python -m pytest -q {test_files}
```

For `attrs`, try at most:

```text
configured_command
pytest_8_with_editable
pytest_7_with_editable
repo_declared_test_extra_if_present
```

5. Record only sanitized command labels, exit codes, durations, and tail hashes
   in the process report. Do not commit raw logs.

6. If one bounded variant clearly improves reference pass without incorrectly
   making no-op pass, update only the active replacement config and rerun
   `certify` once.

7. Do not weaken `no_op_fail`, `known_bad_fail`, source, or oracle gates.

Acceptance:

- every attempted task has a deterministic first failing gate;
- no commit-fallback-only task is certified as benchmark-grade;
- local certification produces at least `4` certified tasks for a minimum paid
  smoke candidate, preferably at least `6`;
- no broad dependency archaeology is performed;
- no raw command output is committed.

Branch:

- If the active repo has at least `4` certified tasks, continue to Step 7.
- If it has fewer than `4` and only one narrow adapter bug remains, fix once and
  rerun.
- If it still has fewer than `4`, try the next candidate repo.
- If both candidates certify fewer than `4`, continue to Step 11 with
  `replacement_repo_certification_blocked`.

Commit:

```text
Certify replacement repo locally
```

## Step 7: Assemble Replacement Release

Purpose:

Build a local pilot release for the active replacement repo.

Actions:

1. Run:

```bash
uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_replacement_boltons_v1.yaml \
  assemble-release

uv run --project experiments/phase0_headroom python \
  experiments/phase0_headroom/tools/repo_history_pilot.py \
  --root . \
  --config experiments/phase0_headroom/configs/third_repo_replacement_boltons_v1.yaml \
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
}' experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json
```

3. Confirm stale repo names did not leak:

```bash
rg -n "Repair the humanize behavior|Repair the itsdangerous behavior" \
  experiments/phase0_headroom/certified_tasks/boltons_certified_tasks.jsonl \
  experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json && exit 1 || true
```

4. For `attrs`, use `attrs_*` paths.

Acceptance:

- `release_status` is `pilot_grade` only if there are at least `4` certified
  tasks and at least `2` tasks in each of `B_real` and `W_real`;
- `benchmark_grade` is true only if there are at least `6` certified tasks and
  at least `3` tasks in each of `B_real` and `W_real`;
- release `claim_scope` does not claim predictive validation;
- no stale repo-name statement remains.

Branch:

- If release is `pilot_grade` or better, continue.
- If release is `diagnostic_only`, try the next candidate repo or continue to
  Step 11 with a blocked decision.

Commit:

```text
Assemble replacement repo pilot release
```

## Step 8: Select Active Replacement Repo

Purpose:

Choose the active third repo for Phase 1 hardening overlays.

Actions:

1. Update:

```text
experiments/phase1_compiler/configs/phase1_third_repo_replacement_selection.yaml
```

Set:

```yaml
active_selection:
  repo_id: boltons
  selection_status: selected_local_pilot
  source_release: experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json
  replacement_for: itsdangerous
```

Use `attrs` if `attrs` is selected.

2. Record selected and rejected candidate summaries in:

```text
experiments/phase1_compiler/results/phase1_third_repo_replacement_candidate_screen.json
experiments/phase1_compiler/reports/phase1_third_repo_replacement_candidate_screen.md
```

3. Do not delete Itsdangerous artifacts. Mark them historical/replaced in Phase
   1 reports.

Acceptance:

- exactly one active replacement repo is selected, or the decision clearly says
  no replacement was found;
- selected repo has local `pilot_grade` or better;
- Itsdangerous is not treated as the active third repo anymore;
- predictive validity remains false.

Commit:

```text
Select active Phase 1 replacement repo
```

## Step 9: Refresh Phase 1 Hardening Overlays

Purpose:

Recompute sidecar evidence with the selected replacement repo.

Actions:

1. Run:

```bash
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_source_certification_hardening.py
```

2. Inspect selected repo summaries:

```bash
SELECTED_REPO=$(python3 - <<'PY'
import re
from pathlib import Path
text = Path("experiments/phase1_compiler/configs/phase1_third_repo_replacement_selection.yaml").read_text()
match = re.search(r"repo_id:\s*([A-Za-z0-9_-]+)", text)
print(match.group(1) if match else "")
PY
)

jq --arg repo "$SELECTED_REPO" '.repo_summary[$repo]' \
  experiments/phase1_compiler/results/phase1_source_provenance_overlay.json

jq --arg repo "$SELECTED_REPO" '.repo_summary[$repo]' \
  experiments/phase1_compiler/results/phase1_oracle_alignment_audit.json

jq --arg repo "$SELECTED_REPO" '.repo_summary[$repo]' \
  experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json

jq '{
  primary_decision_label,
  active_third_repo: (.third_repo_replacement // .active_third_repo // null),
  predictive_validity_established,
  recommended_next_runbook
}' experiments/phase1_compiler/results/phase1_certification_hardening_decision.json
```

3. Confirm hardening does not report stale statement-source mismatch from
   Itsdangerous for the selected replacement repo.

4. If selected repo has manual-review source or oracle risk, do not silently
   promote it. Either:

- keep it as manual review and continue to Step 11 with a blocked/repair
  decision; or
- implement a deterministic audit improvement with tests, then rerun hardening.

Acceptance:

- selected replacement repo appears in source, oracle, and hardened summaries;
- Itsdangerous is archived/replaced and no longer counted as active third repo;
- selected repo hardened benchmark candidate count is computed;
- predictive validity remains `false`;
- no unsupported paid ACUT or ranking claim appears.

Branch:

- If selected repo has at least `4` hardened benchmark-grade candidates and a
  valid B/W split, continue to Step 10 with paid-smoke readiness.
- If selected repo has fewer than `4` but another candidate repo has not been
  tried, try the next repo.
- If both candidates fail hardening, continue to Step 11 with a replacement
  blocked decision.

Commit:

```text
Refresh Phase 1 hardening overlays with replacement repo
```

## Step 10: Refresh Phase 1 Compiler Boundary

Purpose:

Make the Phase 1 MVP closeout reflect the current replacement-repo evidence
without claiming predictive validation.

Actions:

1. If needed, update `phase1_compiler.py` and README/report text so the closeout
   can reference:

```text
phase1_third_repo_replacement_selection_decision.json
phase1_hardened_certification_overlay.json
```

as sidecar evidence.

2. Run:

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

3. Inspect:

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
- production ranking remains `not_produced`;
- closeout identifies the replacement repo sidecar evidence if available;
- next runbook recommendation is either paid smoke readiness or another
  local-only blocker runbook;
- older scorecards are not silently reinterpreted as predictive evidence.

Commit if compiler artifacts or docs changed:

```text
Refresh Phase 1 compiler boundary after replacement selection
```

## Step 11: Write Final Replacement Decision

Actions:

1. Create:

```text
experiments/phase1_compiler/results/phase1_third_repo_replacement_selection_decision.json
experiments/phase1_compiler/reports/phase1_third_repo_replacement_selection_decision.md
```

2. Use exactly one primary decision label:

```text
ready_for_paid_third_repo_acut_smoke_runbook
replacement_repo_needs_one_more_local_repair
replacement_repo_source_blocked
replacement_repo_certification_blocked
replacement_repo_hardening_blocked
replacement_repo_supply_blocked
no_replacement_repo_found
```

3. The JSON must include:

```json
{
  "schema_version": "barcarolle.phase1.third_repo_replacement_selection_decision.v1",
  "starting_head": "",
  "final_head": "",
  "paid_llm_calls_made": false,
  "paid_acut_calls_made": false,
  "candidate_order": ["boltons", "attrs"],
  "selected_repo_id": "",
  "selected_repo_status": "",
  "replaced_repo_id": "itsdangerous",
  "candidate_summaries": [],
  "candidate_count_after_filter": 0,
  "reviewed_non_leaky_statement_count": 0,
  "certified_task_count": 0,
  "release_status": "",
  "b_real_count": 0,
  "w_real_count": 0,
  "hardened_benchmark_candidate_count": 0,
  "ready_for_paid_smoke": false,
  "primary_decision_label": "",
  "recommended_next_runbook": "",
  "allowed_claims": [],
  "disallowed_claims": []
}
```

4. The Markdown report should answer:

- Which repos were screened?
- Which repo was selected, if any?
- Why was `boltons` accepted or rejected?
- Why was `attrs` accepted or rejected, if tried?
- How many candidates survived filtering?
- How many tasks had reviewed non-leaky source context?
- How many certified locally?
- Did the release reach pilot or benchmark grade?
- How many tasks survived Phase 1 hardening?
- May the next runbook run a paid third-repo ACUT smoke batch?
- What claims remain prohibited?

5. If `ready_for_paid_smoke` is true, the recommended next runbook should be:

```text
run_small_paid_third_repo_acut_smoke_with_selected_replacement_repo
```

and should explicitly be a future runbook.

6. If `ready_for_paid_smoke` is false, recommend one of:

```text
repair_replacement_repo_source_adapter_without_paid_acut
repair_replacement_repo_environment_without_paid_acut
select_new_replacement_repo_candidates_without_paid_acut
return_to_future_holdout_design_with_two_repo_evidence_only
```

Acceptance:

- final decision follows from observed local evidence;
- no paid calls were made;
- predictive validity remains false;
- the report does not hide manual-review, source, oracle, or environment
  blockers;
- if ready for paid smoke, there are at least `4` hardened benchmark-grade
  candidates with a valid B/W split.

Commit:

```text
Summarize Phase 1 replacement repo selection
```

## Step 12: Final Verification

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
- final replacement decision is committed;
- no paid calls were made.

Do not push unless the user explicitly asked this worker to push.

## Stop Conditions

Stop and write:

```text
experiments/phase1_compiler/reports/phase1_third_repo_replacement_selection_blocker.md
```

if any of these occur:

- a step would require paid ACUT or experiment LLM calls;
- raw GitHub responses, raw logs, workspaces, or cloned repos would need to be
  committed;
- local test failures cannot be repaired in scoped code;
- source records are inconsistent enough that regenerated artifacts would
  mislead;
- environment diagnosis would require broad dependency archaeology beyond the
  bounded variants in this runbook;
- both preferred repos fail to produce at least `4` reviewed non-leaky candidate
  statements;
- both preferred repos fail to produce at least `4` local certified tasks;
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
ready_for_paid_third_repo_acut_smoke_runbook
```

A replacement repo, preferably `boltons`, has at least four hardened
benchmark-grade candidate tasks with a valid B/W split. The next runbook may run
a small paid Codex/Kilo ACUT smoke batch under the existing endpoint and budget
rules.

Acceptable outcome:

```text
replacement_repo_hardening_blocked
```

One replacement repo reaches local pilot grade, but Phase 1 hardening rejects or
manual-reviews too many tasks. The next runbook should fix the specific source,
oracle, or candidate-filter issue without paid ACUT calls.

Acceptable blocker outcome:

```text
no_replacement_repo_found
```

Both `boltons` and `attrs` fail local supply/source/certification gates. Stop
before paid ACUT and ask for either new candidate repos or permission to proceed
with a two-repo evidence chain while future-holdout design remains pending.

Never claim predictive validity from this runbook.
