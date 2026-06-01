# Phase 1 Historical Environment Synthesis And Third-Repo Gate Runbook

Status: implementation runbook, 2026-05-26.

This runbook is for one dedicated Codex CLI session. Its job is to answer a
bounded next-step question:

```text
Can a small uv-based historical environment mechanism recover enough old
reference_pass failures to continue attrs/boltons, or should Phase 1 move on
to a third repo such as toolz or humanize?
```

Plain-language summary:

```text
Many old tasks failed reference_pass. That does not automatically mean the real
fixed commit was bad. It often means we ran old code with modern Python and
modern test dependencies.

This runbook tries a small number of historical Python/dependency environments.
If that recovers useful supply, we keep going with attrs/boltons. If it does
not, we stop digging and screen the next repo.
```

This runbook is local-only. Do not run paid ACUT cells, paid replication, paid
LLM statement generation, or paid task-solving calls.

## Starting Point

The reference-pass failure audit ended with this decision:

```text
local_validation_code_bug_found: false
sampled_replays: 12
reference_pass_failures: 76
supply_decision: two_repo_supply_blocker_still_exists_screen_new_repo
```

The sampled root causes were environment-shaped:

```text
dependency_version_drift: 1
pytest_collection_or_config_error: 5
python_version_drift: 6
unclassified_reference_fail: 64
```

The important interpretation is:

```text
The current local validation code did not look wrong in the sampled evidence,
but the certification gate is too coarse. It records install, import,
collection, and assertion failures as the same reference_pass label.
```

The two-repo supply expansion is still below the Phase 1 target. The expansion
closeout reported attrs and boltons below 30 certified tasks each, and the
reference-pass audit did not add any newly eligible tasks.

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-historical-environment-synthesis-and-third-repo-gate-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Make a cohesive git commit after every completed
step that changes files. Do not batch unrelated steps into one commit. Do not
push unless the user explicitly asks.

Main goal: decide whether bounded uv-based historical environment synthesis can
recover enough attrs/boltons reference_pass failures to continue the two-repo
path, or whether Phase 1 should move to a third repo.

Use simple language in reports. For each major finding, say:
1. What happened.
2. Why it matters.
3. Whether it argues for attrs/boltons recovery, third-repo screening, or a
   remaining unknown.

Do not run paid ACUT task-solving cells. Do not run paid replication. Do not
run paid LLM statement generation. Do not use hidden verifier material, raw
ACUT transcripts, raw prompts, raw completions, solver workspaces, or verifier
workspaces.

Do not implement ACUT internals. Barcarolle may build workspaces, run local
certification checks, classify benchmark-side failures, and record sanitized
artifacts.

Do not commit secrets, raw stdout/stderr logs, full raw prompts, raw
completions, raw ACUT transcripts, solver workspaces, verifier workspaces,
cloned external repositories, .venv, uv caches, or large raw outputs. Commit
only small sanitized configs, tools, tests, JSON/CSV summaries, reports, and
digests.

Raw replay logs, temporary workspaces, target repo clones, and uv scratch
artifacts must stay under ignored local paths.

If the run suggests a production validation-code change, first add a focused
regression test that captures the expected behavior. Then make the smallest
fix and rerun the focused test plus the relevant suite.

Do not draft or create a follow-up runbook. Record completed work, blockers,
decisions, and recommended next action categories only.
```

## Required Inputs

Use these artifacts if present:

```text
AGENTS.md
docs/architecture/system-design.md
docs/experiments/phase-1-reference-pass-failure-audit-runbook.md
docs/experiments/phase-1-two-repo-certified-supply-expansion-runbook.md
docs/experiments/phase-1-third-repo-replacement-selection-runbook.md
docs/experiments/phase-1-third-repo-repair-remine-runbook.md

experiments/phase0_headroom/configs/repositories.yaml
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase0_headroom/tools/test_repo_history_pilot.py
experiments/phase0_headroom/external_repos/attrs
experiments/phase0_headroom/external_repos/boltons

experiments/phase1_compiler/configs/phase1_reference_pass_failure_audit.yaml
experiments/phase1_compiler/results/phase1_reference_pass_failure_audit_decision.json
experiments/phase1_compiler/results/phase1_reference_pass_failure_inventory.json
experiments/phase1_compiler/results/phase1_reference_pass_replay_matrix.json
experiments/phase1_compiler/results/phase1_reference_pass_environment_drift_audit.json
experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_decision.json
experiments/phase1_compiler/results/phase1_two_repo_supply_expansion_certification_attempts.json
experiments/phase1_compiler/reports/phase1_reference_pass_failure_audit_decision.md
experiments/phase1_compiler/tools/phase1_reference_pass_failure_audit.py
experiments/phase1_compiler/tests/test_phase1_reference_pass_failure_audit.py
```

If an input has moved or is missing, record that in the preflight result and
continue with available committed artifacts.

## Budget And Runtime Rules

This runbook is local-only.

```text
paid ACUT calls: disabled
paid task-solving calls: disabled
paid replication: disabled
paid LLM statement generation: disabled
provider cost change: 0
```

Network access for public package installation and public repository cloning is
allowed only for local environment reconstruction and repository screening.

Do not let this run become open-ended archaeology. Use these caps unless a
blocker report explains why they are impossible:

```text
known reference_pass failures replayed: at most 36
environment profiles tried per task: at most 5
third-repo candidates certified per repo before decision: at most 40
third repos screened in this run: toolz first, humanize only if toolz fails
single pytest command timeout: 120 seconds
single task total environment timeout: 8 minutes
```

## Claim Boundary

Allowed claims:

```text
historical_environment_synthesis_completed
historical_environment_profile_inference_completed
uv_historical_environment_probe_completed
reference_gate_subclassification_completed
known_reference_failures_replayed_under_historical_envs
historical_environment_recovered_reference_pass_sample
historical_environment_did_not_recover_reference_pass_sample
attrs_boltons_reopened_for_local_certification
attrs_boltons_still_below_supply_threshold
third_repo_gate_screen_completed
toolz_local_gate_passed
toolz_local_gate_failed
humanize_local_gate_passed
humanize_local_gate_failed
continue_attrs_boltons_recommended
move_to_third_repo_recommended
paid_replication_not_run
new_paid_acut_cells_not_run
new_paid_llm_calls_not_run
```

Disallowed claims:

```text
predictive_validity_established
paid_replication_completed
new_paid_acut_cells_run
new_paid_llm_statement_generation_run
hidden_oracle_informed_selection
raw_transcript_informed_selection
raw_prompt_or_completion_informed_selection
production_benchmark_ranking
all_reference_pass_failures_are_environment_drift
all_reference_pass_failures_are_validation_bugs
third_repo_paid_smoke_ready_without_local_certification_evidence
followup_runbook_written_by_worker
```

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_historical_environment_synthesis_gate.yaml
  tools/
    phase1_historical_environment_synthesis_gate.py
  tests/
    test_phase1_historical_environment_synthesis_gate.py
    # also update existing tests if production validation code changes
  results/
    phase1_historical_environment_synthesis_preflight.json
    phase1_historical_environment_input_inventory.json
    phase1_historical_environment_profile_catalog.json
    phase1_historical_environment_known_failure_replay_matrix.json
    phase1_reference_gate_subclassification.json
    phase1_historical_environment_recovered_supply_projection.json
    phase1_third_repo_environment_gate_screen.json
    phase1_historical_environment_synthesis_decision.json
  reports/
    phase1_historical_environment_synthesis_process.md
    phase1_historical_environment_input_inventory.md
    phase1_historical_environment_profile_catalog.md
    phase1_historical_environment_known_failure_replay_matrix.md
    phase1_reference_gate_subclassification.md
    phase1_historical_environment_recovered_supply_projection.md
    phase1_third_repo_environment_gate_screen.md
    phase1_historical_environment_synthesis_decision.md
```

Temporary raw artifacts must stay under ignored paths such as:

```text
experiments/phase1_compiler/tmp/historical_environment_synthesis_gate/
experiments/phase0_headroom/workspaces/historical_environment_synthesis_gate/
experiments/phase0_headroom/cache/historical_environment_synthesis_gate/
experiments/phase0_headroom/external_repos/toolz
experiments/phase0_headroom/external_repos/humanize
```

Do not commit those raw paths.

## Research Questions

Answer these questions in the final decision report:

```text
RQ1: Can uv run old target commits in isolated historical Python/dependency
     environments without using Barcarolle's Python 3.11 project environment?

RQ2: How many known attrs/boltons reference_pass failures are recovered by
     bounded historical environment profiles?

RQ3: When failures remain, are they install failures, import failures,
     pytest collection failures, assertion failures, timeouts, or unknowns?

RQ4: Does historical environment synthesis produce enough newly eligible local
     supply to keep attrs/boltons as the active Phase 1 path?

RQ5: If attrs/boltons remain below threshold, does toolz or humanize pass a
     third-repo local environment gate with enough candidate supply?

RQ6: What exact next action should the coordinating session take?
```

## Mechanism Design

The environment mechanism must be bounded and auditable.

### Use uv Outside The Barcarolle Project

Barcarolle's Phase 0 and Phase 1 `pyproject.toml` files require Python 3.11.
Historical target environments must not be forced through those project files.

Use this shape for historical target commands:

```bash
uv run \
  --no-project \
  --isolated \
  --managed-python \
  --python 3.9 \
  --exclude-newer 2020-12-31 \
  --with "pytest<6" \
  --with "setuptools<58" \
  --with "hypothesis<6" \
  --with-editable /path/to/target-workspace \
  python -m pytest -q tests/test_example.py
```

Important details:

- `--no-project` avoids Barcarolle's Python 3.11 project constraint.
- `--isolated` avoids reusing a dirty local virtual environment.
- `--managed-python` makes Python-version availability explicit.
- `--exclude-newer` keeps dependency resolution close to the target commit era.
- `--with-editable` is tried only as one install mode. A `PYTHONPATH`-only
  mode must also exist because some old projects do not build cleanly.

If uv cannot provide an old Python version or dependency set, classify the
result as `historical_environment_unavailable`, not `reference_pass`.

### Environment Profile Fields

Each environment profile must be represented as structured data:

```text
profile_id
python_version
dependency_constraints
exclude_newer_date
install_mode: editable | pythonpath_only
cwd_mode: target_workspace | repo_root
pytest_mode: explicit_test_files | config_discovery
extra_env
max_seconds
why_selected
```

Each replay result must record:

```text
task_id
repo_id
base_commit
target_commit
target_commit_date
test_files
profile_id
command_shape
cwd_shape
python_version_observed
installed_dependency_summary
pytest_rootdir_summary
returncode
duration_seconds
stdout_tail_hash
stderr_tail_hash
sanitized_error_class
subgate_label
```

Do not commit raw stdout or stderr.

### Default Profile Catalog

Start with a small catalog. The worker may tune exact dependency constraints
after reading target metadata, but must keep the number of profiles bounded.

```text
py311_current:
  python: 3.11
  dependencies: current reference-pass audit command dependencies
  purpose: baseline comparison

py310_pytest7:
  python: 3.10
  dependencies: pytest>=7,<8; setuptools<81; hypothesis<6
  purpose: newer historical projects

py39_pytest6:
  python: 3.9
  dependencies: pytest>=6,<7; setuptools<66; hypothesis<6
  purpose: 2020-2022-era projects

py38_pytest5:
  python: 3.8
  dependencies: pytest>=5,<6; setuptools<58; hypothesis<6
  purpose: older pytest configuration compatibility

py37_pytest4:
  python: 3.7
  dependencies: pytest>=4,<5; setuptools<58; hypothesis<5
  purpose: old commits affected by removed stdlib aliases or setup.cfg pytest behavior
  note: optional; skip cleanly if uv cannot provide Python 3.7 on this machine
```

Use target commit date plus a small grace window for `--exclude-newer`:

```text
exclude_newer_date = min(target_commit_date + 180 days, current_date)
```

If that makes dependency resolution impossible, record the failure and try the
next bounded profile. Do not keep manually searching package versions.

### Reference Gate Subclassification

Replace the single coarse local label with these sublabels in reports:

```text
reference_install_failed
reference_import_failed
reference_collect_failed
reference_assert_failed
reference_timeout
reference_environment_unavailable
reference_pass
reference_unknown_failed
```

Only `reference_assert_failed` means the target commit's changed tests actually
ran and failed. Install, import, collection, and unavailable-Python failures are
environment problems until proven otherwise.

### Eligibility Rule

Recovering `reference_pass` is not enough by itself. A recovered task is newly
eligible only if the full local certification record passes all required
benchmark-side gates under one recorded environment profile:

```text
checkout
changed-test material equivalence
no-op behavior
reference behavior
source provenance
solution leakage review
scope/path policy
artifact hygiene
```

The accepted task record must include an environment proof:

```text
profile_id
python_version_observed
direct dependency versions
command shape
cwd shape
install mode
pytest rootdir/config summary
result hashes
```

## Step 0: Preflight

Actions:

1. Read `AGENTS.md`.
2. Record branch, HEAD, date, Python version, `uv --version`, and git status.
3. Record `uv run --help` support for:

```text
--no-project
--isolated
--managed-python
--python
--exclude-newer
--with
--with-editable
```

4. Confirm that `experiments/phase1_compiler/tmp/`,
   `experiments/phase0_headroom/workspaces/`,
   `experiments/phase0_headroom/cache/`, and
   `experiments/phase0_headroom/external_repos/` are ignored.
5. Confirm paid calls are disabled.
6. Write the config and process ledger.

Acceptance:

- Preflight records `paid_acut_calls: disabled`.
- Preflight records `paid_llm_calls: disabled`.
- Preflight explains why historical env commands use `uv --no-project`.
- No raw logs are committed.

## Step 1: Build The Input Inventory

Actions:

1. Load the previous reference-pass audit decision and replay matrix.
2. Select known attrs/boltons failures:

```text
required sample:
  all 12 previously replayed sampled failures

additional sample:
  up to 24 unclassified reference_pass failures
  prioritize unique stderr hashes, old target dates, simple test-file sets,
  and candidates whose no-op behavior was otherwise interpretable
```

3. Summarize selected tasks by repo, target year, failure signature, changed
   files, and previous root-cause label.
4. Identify the third-repo screening order:

```text
first: toolz
fallback: humanize
defer: rich and requests unless explicitly needed later
```

Acceptance:

- Inventory contains at most 36 known failures.
- Inventory records why each selected failure is useful.
- The report says plainly whether the sample is enough to make a bounded
  decision or only a rough screen.

## Step 2: Add The Historical Environment Tool

Actions:

1. Implement `phase1_historical_environment_synthesis_gate.py`.
2. Keep the core as small pure functions where possible.
3. Required subcommands:

```text
preflight
inventory
profile-catalog
replay-known-failures
subclassify-reference-gates
project-recovered-supply
screen-third-repo
decision
all
```

4. Required pure functions:

```text
build_uv_command(profile, target_workspace, test_files)
infer_profile_candidates(repo_id, target_commit_date, target_metadata)
classify_reference_subgate(returncode, stdout_tail, stderr_tail)
sanitize_command_shape(argv)
sanitize_output_tail(text)
summarize_dependency_versions(stdout_or_probe_json)
```

5. Add tests for command construction and classification before running the
   full replay.

Acceptance:

- Tests prove historical commands use `uv --no-project`.
- Tests prove `--project experiments/...` is not used for old Python profiles.
- Tests cover install/import/collection/assertion/timeout classification.
- Raw output redaction is tested.

## Step 3: Run Known Failures Under Bounded Historical Profiles

Actions:

1. For each selected known failure, run:

```text
A. baseline profile matching the previous audit command
B. inferred historical profile
C. at most three fallback profiles from the catalog
```

2. Try both install modes when useful:

```text
editable install:
  uv run --no-project --isolated ... --with-editable <target_ws> python -m pytest ...

PYTHONPATH-only:
  PYTHONPATH=<target_ws> uv run --no-project --isolated ... python -m pytest ...
```

3. Stop trying profiles for a task after the first clean `reference_pass`.
4. Store raw logs only under ignored tmp paths.
5. Commit only sanitized summaries, hashes, profile ids, and short error
   classes.

Acceptance:

- The matrix shows which profile, if any, recovered each task.
- The matrix separates `uv/Python unavailable` from target test failure.
- The report explains the results in simple language.

## Step 4: Subclassify Reference Failures

Actions:

1. Reclassify each known replay result into:

```text
reference_install_failed
reference_import_failed
reference_collect_failed
reference_assert_failed
reference_timeout
reference_environment_unavailable
reference_pass
reference_unknown_failed
```

2. Compare the old coarse `reference_pass` label with the new sublabels.
3. Identify whether production certification code should store subgate labels.

Acceptance:

- The report states how many old `reference_pass` failures were really
  install/import/collection/environment failures in the sample.
- If a production classification change is recommended, a focused regression
  test exists before the code change.

## Step 5: Project Recoverable attrs/boltons Supply

Actions:

1. For each known failure that now has `reference_pass`, rerun the relevant
   full local certification gates under the winning environment profile.
2. Count only fully certified records as recovered eligible supply.
3. Estimate the likely recovery range for unsampled failures using repeated
   signatures only. Do not extrapolate from unrelated signatures.
4. Produce a conservative projection:

```text
confirmed_recovered_eligible
same_signature_projected_recoverable
still_blocked
unknown
```

Acceptance:

- The projection clearly separates confirmed recovery from rough projection.
- No task is counted as eligible from reference behavior alone.
- The report says whether attrs/boltons can plausibly reach 30 tasks each.

## Step 6: Screen Third Repo With The Same Gate

Actions:

1. Screen `toolz` first. Clone or refresh it only under the ignored external
   repo path.
2. Use the existing repository-history tooling where possible. Do not write a
   new mining framework.
3. Run local candidate mining and certification with the same reference-gate
   subclassification and environment-profile logic.
4. Stop after enough evidence for a gate decision:

```text
toolz passes if:
  at least 30 locally certified candidate tasks
  low external-service risk remains true
  reference failures are not dominated by unresolved environment failures
  no raw prompt/completion/transcript material is used

toolz fails if:
  fewer than 30 locally certified candidate tasks after bounded repair
  certification depends mostly on commit-message fallback
  environment failures dominate and cannot be classified cleanly
  source or oracle quality is too weak for benchmark-grade tasks
```

5. Screen `humanize` only if `toolz` fails the local gate.

Acceptance:

- The report says whether `toolz` is the recommended third repo.
- If `toolz` fails and `humanize` is screened, the report says exactly why.
- `rich` and `requests` are not screened unless the decision report explains
  why both `toolz` and `humanize` failed and more screening is still local-only.

## Step 7: Decision Rules

Apply these rules in order.

### Continue attrs/boltons

Recommend continuing attrs/boltons if both are true:

```text
1. Historical environment synthesis confirms enough recovered eligible tasks
   or same-signature projected recovery to plausibly reach 30 certified tasks
   per repo.

2. The required mechanism is simple:
   bounded profiles, structured environment proof, no hidden-oracle access,
   no bespoke per-task dependency archaeology.
```

### Integrate Subgate Classification But Still Add A Third Repo

Recommend a mixed path if:

```text
historical environments improve diagnosis or recover some tasks,
but not enough to reach the two-repo supply threshold.
```

In this case, the next implementation should keep the subgate classification
because it improves auditability, but the supply path should move to the third
repo.

### Move To Third Repo

Recommend moving to a third repo if any of these are true:

```text
confirmed recovered eligible tasks are too few to matter
historical profile search requires many per-task special cases
old Python/dependency availability is unreliable
attrs/boltons still cannot plausibly reach 30 certified tasks each
toolz or humanize passes the local third-repo gate
```

### Stop With Blocker

Write a blocker report instead of a normal decision if:

```text
uv cannot run isolated historical environments at all
required committed input artifacts are missing and cannot be reconstructed
the needed step would require paid ACUT or paid LLM calls
the worker finds evidence of hidden-oracle or raw-transcript contamination
```

## Step 8: Verification And Closeout

Actions:

1. Run focused tests:

```bash
uv run --project experiments/phase1_compiler pytest \
  experiments/phase1_compiler/tests/test_phase1_historical_environment_synthesis_gate.py \
  -q
```

2. If shared certification code changed, run the related suites:

```bash
uv run --project experiments/phase1_compiler pytest \
  experiments/phase1_compiler/tests/test_phase1_reference_pass_failure_audit.py \
  experiments/phase1_compiler/tests/test_phase1_two_repo_certified_supply_expansion.py \
  -q
```

3. If repo-history tooling changed, run:

```bash
uv run --project experiments/phase0_headroom pytest \
  experiments/phase0_headroom/tools/test_repo_history_pilot.py \
  -q
```

4. Run the full Phase 1 compiler tests if production code changed broadly:

```bash
uv run --project experiments/phase1_compiler pytest \
  experiments/phase1_compiler/tests \
  -q
```

5. Run:

```bash
git diff --check
```

6. Write the final decision report and JSON.

Final decision report must include:

```text
primary_decision_label
plain_language_summary
known_failure_sample_size
profiles_tried
confirmed_recovered_eligible_attrs
confirmed_recovered_eligible_boltons
same_signature_projected_recoverable_attrs
same_signature_projected_recoverable_boltons
third_repo_screened
third_repo_certified_candidate_count
recommended_next_action_category
paid_acut_calls_made: false
paid_llm_calls_made: false
verification
```

Allowed `primary_decision_label` values:

```text
continue_attrs_boltons_after_historical_env_recovery
integrate_subgates_and_move_to_third_repo
move_to_toolz_as_third_repo
move_to_humanize_as_third_repo
historical_environment_synthesis_blocked
insufficient_local_evidence
```

Acceptance:

- Decision report answers all research questions.
- Reports use simple language.
- Raw logs, target clones, caches, and workspaces are not committed.
- The git worktree is clean except for intentional committed artifacts.
