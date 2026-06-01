# Phase 1 Reference-Pass Failure Audit Runbook

Status: implementation runbook, 2026-05-26.

This runbook is for one long-running Codex CLI session. Its job is to explain
why the two-repo supply expansion produced many `reference_pass` failures and
to determine whether Barcarolle's local certification replay code is wrong.

Plain-language summary:

```text
reference_pass means: check out the real target commit, run the tests that
commit changed, and confirm the real fixed version passes.

If reference_pass fails often, something is suspicious. Either many old commits
no longer run in our modern local environment, or our replay code is testing
the wrong thing.
```

This runbook is local-only. Do not run paid ACUT cells, paid replication, or
paid LLM statement generation.

## Starting Point

The two-repo certified supply expansion ended with this decision:

```text
decision: existing_repos_supply_exhausted_screen_new_repo
attrs:   10 existing eligible + 10 new eligible = 20 total, below 30
boltons: 12 existing eligible + 15 new eligible = 27 total, below 30
```

The surprising failure mode was `reference_pass`:

```text
attrs certification attempts:
  attempt_count: 69
  certified: 10
  near_certified: 59
  first_failing_gate_counts:
    reference_pass: 54
    solution_leakage_review: 4
    no_op_fail: 1
    none: 10

boltons certification attempts:
  attempt_count: 55
  certified: 15
  near_certified: 24
  rejected: 16
  first_failing_gate_counts:
    reference_pass: 22
    checkout: 16
    solution_leakage_review: 2
    none: 15
```

That is counterintuitive because the target commit is supposed to be the
reference implementation. If its changed tests fail, we may be misclassifying
candidate supply.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-reference-pass-failure-audit-runbook.md.

Work in the repository root. Read AGENTS.md first. Use uv for repo-local Python
tooling. Make a cohesive git commit after every completed step that changes
files. Do not batch unrelated steps into one commit. Do not push unless the
user explicitly asks.

Main goal: explain why many candidate tasks failed reference_pass in the
two-repo certified supply expansion, with special attention to whether the
local certification replay code is wrong.

Use simple language in reports. For every major finding, state:
1. What happened.
2. Why it matters.
3. Whether it points to a Barcarolle bug, environment drift, bad candidate
   mining, or an unresolved unknown.

Do not run paid ACUT task-solving cells. Do not run paid replication. Do not
use hidden verifier material, raw ACUT transcripts, raw prompts, raw
completions, solver workspaces, or verifier workspaces. Commit only small
sanitized configs, tools, tests, JSON/CSV summaries, reports, and digests.

Raw stdout/stderr, temporary workspaces, full diffs, and large logs may be
written only under ignored local scratch paths. Commit sanitized failure
signatures, command shapes, hashes, root-cause labels, and small representative
snippets only when they are needed to understand the result.

If you find a likely bug in the local validation code, first add or update a
focused regression test that captures the expected replay behavior. Then make
the smallest fix and rerun the focused test plus the relevant suite.

Do not draft or create a follow-up runbook. Record completed work, blockers,
decisions, and recommended next action categories only.
```

## Required Inputs

Use these artifacts if present:

```text
AGENTS.md
docs/architecture/system-design.md
docs/experiments/phase-1-two-repo-certified-supply-expansion-runbook.md
experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_decision.json
experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_certification_attempts.json
experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_raw_candidates.json
experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_source_contexts.json
experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_eligibility_audit.json
experiments/phase1_compiler/reports/phase1_two_repo_supply_expansion_decision.md
experiments/phase1_compiler/tools/phase1_two_repo_certified_supply_expansion.py
experiments/phase1_compiler/tests/test_phase1_two_repo_certified_supply_expansion.py
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase0_headroom/tools/statement_quality.py
experiments/phase0_headroom/external_repos/attrs
experiments/phase0_headroom/external_repos/boltons
experiments/phase0_headroom/candidate_sources/attrs_supply_expansion_20260526_candidates.jsonl
experiments/phase0_headroom/candidate_sources/boltons_supply_expansion_20260526_candidates.jsonl
experiments/phase0_headroom/certified_tasks/attrs_supply_expansion_20260526_review_records.jsonl
experiments/phase0_headroom/certified_tasks/boltons_supply_expansion_20260526_review_records.jsonl
```

If a required historical artifact has moved or is missing, record that in the
preflight report and continue with available committed artifacts.

## Claim Boundary

Allowed claims:

```text
reference_pass_failure_audit_completed
reference_pass_failure_inventory_completed
reference_replay_reproduction_completed
command_contract_audit_completed
environment_drift_audit_completed
patch_application_audit_completed
local_validation_bug_found
local_validation_bug_not_found
local_validation_bug_fixed
reference_pass_failures_reclassified
reference_pass_failures_remain_unexplained
paid_replication_not_run
new_paid_acut_cells_not_run
```

Disallowed claims:

```text
predictive_validity_established
paid_replication_completed
new_paid_acut_cells_run
hidden_oracle_informed_selection
raw_transcript_informed_selection
raw_prompt_or_completion_informed_selection
all_reference_pass_failures_are_candidate_depletion
all_reference_pass_failures_are_validation_bugs
followup_runbook_written_by_worker
```

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_reference_pass_failure_audit.yaml
  tools/
    phase1_reference_pass_failure_audit.py
  tests/
    test_phase1_reference_pass_failure_audit.py
    # also update existing tests if a validation-code regression is found
  results/
    phase1_reference_pass_failure_audit_preflight.json
    phase1_reference_pass_failure_inventory.json
    phase1_reference_pass_replay_matrix.json
    phase1_reference_pass_command_contract_audit.json
    phase1_reference_pass_patch_application_audit.json
    phase1_reference_pass_environment_drift_audit.json
    phase1_reference_pass_root_cause_taxonomy.json
    phase1_reference_pass_code_fix_decision.json
    phase1_reference_pass_failure_audit_decision.json
  reports/
    phase1_reference_pass_failure_audit_process.md
    phase1_reference_pass_failure_inventory.md
    phase1_reference_pass_replay_matrix.md
    phase1_reference_pass_command_contract_audit.md
    phase1_reference_pass_patch_application_audit.md
    phase1_reference_pass_environment_drift_audit.md
    phase1_reference_pass_root_cause_taxonomy.md
    phase1_reference_pass_code_fix_decision.md
    phase1_reference_pass_failure_audit_decision.md
```

Temporary raw replay logs and workspaces must stay under ignored paths such as:

```text
experiments/phase1_compiler/tmp/reference_pass_failure_audit/
experiments/phase0_headroom/workspaces/reference_pass_failure_audit/
```

Do not commit those raw paths.

## Research Questions

Answer these questions in the final decision report:

```text
RQ1: How many reference_pass failures occurred by repo, year, module, test file,
     command return code, and stderr/stdout signature?

RQ2: Can a small representative sample of reference_pass failures be reproduced
     from committed artifacts and local repositories?

RQ3: Are reference_pass failures caused by Barcarolle replay bugs, environment
     drift, dependency drift, historical Python incompatibility, flaky tests,
     bad candidate metadata, or something else?

RQ4: Does the current certification code test the right workspace, with the
     right tests, the right cwd, the right PYTHONPATH, and the right editable
     package?

RQ5: Are no-op and reference runs comparing equivalent test material?

RQ6: If a validation bug exists, what is the smallest regression test and fix?

RQ7: After any fix or reclassification, how many previously rejected candidates
     become locally eligible or move to another failure category?
```

## Suspect List

Audit these possible causes before concluding that the repository supply is
really depleted:

```text
1. Wrong commit material:
   - base_commit or target_commit is not what the candidate row says.
   - target archive does not contain the expected test files.
   - target archive differs from `git show target:path` for selected files.

2. Wrong patch direction or patch scope:
   - changed-test patch is reversed.
   - renamed or newly added tests are not applied correctly to base.
   - no-op and reference runs are not using equivalent target test content.

3. Wrong workspace import:
   - tests import an installed package or Barcarolle cwd package instead of the
     archived target workspace.
   - PYTHONPATH and `uv --with-editable` disagree.
   - src-layout and flat-layout repos are handled differently.

4. Wrong pytest root or config:
   - pytest picks the wrong rootdir.
   - pytest does not load the target repo's pytest.ini, tox.ini, setup.cfg, or
     pyproject configuration.
   - absolute test paths from a different cwd change collection behavior.

5. Dependency or Python-version drift:
   - old commits need old pytest, hypothesis, attrs, setuptools, click, or other
     dependencies.
   - target tests are incompatible with the current Python version.
   - `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_*` is missing or uses the wrong name.

6. Test command contract bug:
   - `command_template` is suitable for current repo tests but not historical
     commits.
   - `--with-editable` install fails silently or masks the target package.
   - timeout or collection errors are recorded as reference_pass instead of
     environment failure.

7. Candidate-mining metadata bug:
   - selected test files are not the right oracle files for the target change.
   - docs/config/test-only changes slipped through as behavior candidates.
```

## Step 0: Preflight And Ledger

Actions:

1. Read `AGENTS.md` and record boundary rules.
2. Record branch, HEAD, date, Python version, `uv --version`, and git status.
3. Confirm the current reference-pass failure counts from:

```bash
jq '.summary_by_repo' \
  experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_certification_attempts.json
```

4. Create the config and process ledger.
5. Record that paid ACUT calls and paid LLM calls are disabled.

Acceptance:

- Preflight records `paid_acut_calls: disabled`.
- Preflight records no raw transcript, prompt, completion, solver workspace, or
  verifier workspace is used.
- Process report starts with a simple-language summary of the problem.

## Step 1: Build Failure Inventory

Actions:

1. Parse all rows in
   `phase1_two_repo_supply_expansion_certification_attempts.json`.
2. Select rows where `first_failing_gate == "reference_pass"` or
   `review_first_failing_gate == "reference_pass"`.
3. Summarize by:

```text
repo_id
task_time year
module_or_package
test_files
change_size_bucket
candidate_filter_status
source_context_status
reference_run_1 returncode
reference_run_2 returncode
stderr_tail_hash
stdout_tail_hash
duration bucket
```

4. Produce a prioritized sample:

```text
high priority:
  failures where no-op failed as expected but reference failed
  repeated stderr hash across many tasks
  failures in otherwise simple accepted candidates
  failures with one implementation file and one test file

medium priority:
  failures with manual_review_required
  failures in old years likely affected by dependency drift

low priority:
  known timeout-prone or huge cross-module changes
```

Acceptance:

- Inventory reports exact counts and the top repeated failure signatures.
- Inventory names 6-12 representative tasks to replay manually and
  automatically, covering both repos.
- No raw logs are committed.

## Step 2: Add A Focused Audit Tool

Actions:

1. Implement `phase1_reference_pass_failure_audit.py` with deterministic
   subcommands. Prefer small pure functions that can be unit tested.
2. Required subcommands:

```text
preflight
inventory
replay-sample
audit-command-contract
audit-patch-application
audit-environment-drift
root-cause-taxonomy
decision
all
```

3. The tool must support `--task-id` for focused debugging and `--sample-size`
   for bounded replay.
4. Store raw stdout/stderr only under ignored tmp paths. Commit only:

```text
returncode
duration
command argv shape
cwd
workspace path kind, not full local absolute path
PYTHONPATH shape
pytest rootdir/config summary when detectable
stdout/stderr hashes
short sanitized error class
```

Acceptance:

- The tool can run on a synthetic tiny fixture without external repos.
- The tool never writes raw logs to committed results.
- The tests cover parsing and classification before any production fix.

## Step 3: Reproduce A Representative Sample

Actions:

1. Replay the prioritized sample from Step 1 without changing production code.
2. For each sampled task, run at least these variants:

```text
A. current Barcarolle command:
   run_candidate_tests(config, target_ws, test_files, root)

B. workspace-cwd variant:
   same command shape but cwd = target_ws

C. no editable install variant:
   PYTHONPATH points at target workspace or target src only

D. pytest-config visible variant:
   run from target_ws and let pytest discover repo-local config

E. full target test-file path check:
   compare target archive test file content with `git show target_commit:path`
```

3. Do not treat a variant as a fix yet. This step is evidence gathering.
4. Classify each sampled task as:

```text
current_command_only_failure
all_variants_fail_same_way
workspace_cwd_fixes_failure
editable_install_fixes_failure
dependency_or_python_version_failure
target_test_file_missing_or_mismatched
patch_or_candidate_metadata_failure
unclassified
```

Acceptance:

- At least 6 sampled `attrs` failures and 6 sampled `boltons` failures are
  replayed unless fewer are available after filtering.
- The report explains in simple language what each category means.
- If one command variant fixes multiple failures, mark it as a likely local
  validation bug and proceed to regression tests.

## Step 4: Audit Patch And Test Equivalence

Actions:

For each sampled task:

1. Confirm the target archive contains each `test_files` path.
2. Confirm target archive file content hash matches `git show target:path`.
3. Confirm `git diff base target -- test_files` applies to the base archive.
4. After applying the test patch to base, confirm the base test files match
   target test files exactly.
5. Confirm no-op runs use the patched base tests and reference runs use the
   same target tests.

Acceptance:

- The report says whether no-op and reference runs compare the same test
  material.
- Any mismatch is labeled as `patch_application_bug`,
  `candidate_metadata_bug`, or `rename_handling_gap`.
- Add a regression test if a mismatch can be reproduced with a small fixture.

## Step 5: Audit Command Contract

Actions:

Inspect and test the behavior of these functions:

```text
repo_history_pilot.command_test_files
repo_history_pilot.with_editable_workspace
repo_history_pilot.pythonpath_for
repo_history_pilot.run_candidate_tests
repo_history_pilot.certify_candidate
phase1_two_repo_certified_supply_expansion.safe_certify_candidate
```

Check that the command contract is explicit:

```text
which cwd is used
which package is imported
which pytest config is loaded
which dependency set is installed
which version env var is set
how collection errors are classified
how install errors are classified
```

Acceptance:

- Add unit tests for command construction and environment construction if they
  do not already exist.
- If command construction is wrong, add a failing regression test before fixing
  it.
- If command construction is correct but too weak for historical repos, record
  a `historical_environment_model_gap` rather than a validation bug.

## Step 6: Audit Environment Drift

Actions:

For repeated failure signatures, determine whether old commits fail because of
modern environment drift. Check:

```text
Python version
pytest version
hypothesis version
setuptools version
package build backend
src-layout vs flat-layout
missing optional test dependencies
removed stdlib behavior or syntax incompatibility
```

Use lightweight alternatives before adding dependencies:

```text
uv run --project experiments/phase0_headroom --with ...
python -m pytest --collect-only
python -c "import target_package; print(target_package.__file__)"
python -c "import sys; print(sys.version)"
```

Do not solve this by broad dependency pinning unless evidence says a specific
historical range is required.

Acceptance:

- Repeated failures are grouped into environment causes when possible.
- If historical dependency drift is common, propose a reclassification such as
  `environment_reference_fail` instead of treating those candidates as ordinary
  task-supply failures.
- No paid calls are made.

## Step 7: Regression Tests And Minimal Fixes

Actions:

Only enter this step if earlier steps identify a likely Barcarolle bug.

1. Add a small fixture-based regression test first.
2. The test must state the expected observable behavior, for example:

```text
reference replay imports from target workspace
reference replay runs with target repo pytest config
test patch applied to base produces the same target test file content
collection/setup errors are classified separately from reference behavior fail
```

3. Run the test and confirm it fails for the right reason before fixing when
   feasible.
4. Make the smallest code change.
5. Rerun:

```bash
uv run --project experiments/phase1_compiler pytest \
  experiments/phase1_compiler/tests/test_phase1_reference_pass_failure_audit.py \
  experiments/phase1_compiler/tests/test_phase1_two_repo_certified_supply_expansion.py -q

uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q
git diff --check
```

Acceptance:

- Every code fix has a focused regression test or a written reason why the bug
  cannot be isolated in a small test.
- Reports say how many previously `reference_pass` failures would change
  category or become certified after the fix.
- Do not silently rewrite old committed result artifacts unless the runbook
  explicitly regenerates versioned audit outputs.

## Step 8: Reclassification And Supply Impact

Actions:

Using the audited evidence, classify every `reference_pass` failure into one of:

```text
local_validation_bug
environment_reference_fail
dependency_version_drift
python_version_drift
pytest_collection_or_config_error
candidate_metadata_bug
patch_application_bug
target_commit_itself_unstable
true_reference_behavior_failure
unclassified_reference_fail
```

Then compute:

```text
before:
  attrs eligible total
  boltons eligible total
  reference_pass failures

after audited reclassification:
  candidates still blocked
  candidates needing environment synthesis repair
  candidates eligible after validation-code fix
  candidates needing remine or exclusion
```

Acceptance:

- The report clearly separates "code bug" from "environment model gap".
- The report does not overclaim. If evidence is mixed, say so.
- If counts remain below 30 per repo, say the two-repo supply blocker still
  exists.

## Step 9: Final Decision And Closeout

Actions:

Write:

```text
phase1_reference_pass_failure_audit_decision.json
phase1_reference_pass_failure_audit_decision.md
```

The final report must answer:

```text
1. Was there a local validation-code bug?
2. If yes, what was fixed and how was it tested?
3. If no, what is the main reason reference_pass failed so often?
4. How many tasks changed category?
5. Does this reopen attrs/boltons supply expansion, or should the project still
   screen a new repo?
6. What should the coordinating session decide next?
```

Acceptance:

- Final report uses simple language.
- No follow-up runbook is drafted.
- No paid calls are made.
- Verification commands and results are recorded.
- `git diff --check` passes.

## Stop Conditions

Stop and write a blocker report if:

```text
required committed artifacts are missing and cannot be reconstructed
external repos are missing and cannot be used locally
the replay requires raw hidden verifier material
raw logs or workspaces would need to be committed
the audit cannot reproduce any reference_pass failure
```

If stopped, record exactly what is missing and the smallest next action category.
