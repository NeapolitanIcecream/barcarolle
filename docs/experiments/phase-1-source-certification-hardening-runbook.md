# Phase 1 Source And Certification Hardening Runbook

Status: implementation runbook, 2026-05-22.

This runbook is for one dedicated Codex CLI session. Its job is to resolve the
current Phase 1 evidence-quality blockers before any new paid ACUT scale-up.

The current engineering pipeline can run workspace ACUT cells, capture diffs,
replay hidden verifiers, and record cost. The blocker is not the ACUT boundary.
The blocker is task evidence quality:

- Humanize tasks are executable, but `12/12` certified tasks still use
  commit-message fallback as their public problem source.
- Itsdangerous produced only `1` certified task and `10` near-certified tasks,
  so it did not reach a balanced third-repo pilot.
- We need to distinguish candidate-quality problems, source-adapter problems,
  environment-synthesis problems, oracle-alignment problems, and certification
  implementation bugs.

The expected output is a hardened certification layer and a decision about the
next validation path. This runbook should not run new paid ACUT task-solving
cells.

## Research Alignment

The restart proposal defines Barcarolle as a target-repository benchmark
compiler, not a task generator. The relevant design points are:

- source adapters should output structured task records with source confidence
  and leakage risks;
- certification should reject tasks whose problem statement is ambiguous,
  solution-leaking, scope-misaligned, weakly tested, flaky, or too expensive;
- SWE-Bench++-style task generation is an upstream source, not Barcarolle's core
  contribution;
- Barcarolle's claim depends on benchmark construction and predictive validity,
  not on maximizing task count.

Use these external-method anchors only as design guidance:

- SWE-bench: issue text plus associated PR, fail-to-pass and pass-to-pass tests.
- SWE-Bench++: programmatic sourcing, environment synthesis, test oracle
  extraction, quality assurance.
- SWE-Bench+: solution leakage and weak-test auditing.
- OpenAI SWE-bench Verified audit: narrow tests, wide tests, underspecified
  statements, environment mismatch, and contamination risks.

Do not claim that Barcarolle has reimplemented SWE-Bench++ or SWE-bench
Verified. The output here is a small local hardening pass for the current
Barcarolle Phase 1 evidence.

Method references:

```text
SWE-bench: https://www.swebench.com/original.html
SWE-Bench++: https://arxiv.org/abs/2512.17419
SWE-Bench+: https://arxiv.org/abs/2410.06992
OpenAI SWE-bench Verified audit:
  https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/
SWE-smith: https://openreview.net/forum?id=63iVrXc8cC
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing /Users/chenmohan/gits/barcarolle/docs/experiments/phase-1-source-certification-hardening-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Use uv for repo-local Python tooling.
Make cohesive commits after completing one or more related steps.

Current state: Phase 1 overnight validation completed successfully as an
operational validation pilot, but predictive validity remains false. Humanize
has scoreable ACUT cells but commit-message-fallback source provenance.
Itsdangerous local certification produced only one certified task and no paid
ACUT cells.

Your job is to harden source adapters and certification logic before any new
paid ACUT scale-up. Do not run paid ACUT task-solving cells in this runbook.
Local tests, local repository-history mining, GitHub metadata lookup, local
environment probes, local verifier replay, deterministic reports, and small
sanitized manifests are allowed.

All paid LLM or ACUT calls remain disabled in this runbook. If any future step
seems to need paid LLM or ACUT calls, stop and write a blocker report instead.
If endpoint variables are checked, they must be LLM_BASE_URL plus LLM_API_KEY
after sourcing ~/.zshrc, but no paid task-solving call should be made.

Keep Barcarolle on the benchmark/compiler side of the ACUT boundary. Do not
implement Codex, Kilo, or any other ACUT internals.

Do not commit secrets, raw GitHub API responses, full raw prompts, raw
completions, raw ACUT transcripts, solver workspaces, verifier workspaces,
cloned external repositories, .venv, caches, or large raw outputs. Commit only
small sanitized configs, manifests, tools, tests, reports, summaries, and
digests.
```

## Claim Boundary

Allowed claims:

```text
source_adapter_hardening
certification_gate_hardening
source_provenance_overlay
oracle_alignment_audit
environment_synthesis_diagnosis
third_repo_certification_diagnosis
insufficient_evidence_for_predictive_validation
```

Disallowed claims:

```text
predictive_validity_established
future_holdout_predictive_validity
production_benchmark_ranking
pure_harness_effect
humanize_benchmark_grade_if_commit_fallback_only
third_repo_pilot_grade_if_unbalanced_or_under_certified
```

Important interpretation:

- Commit-message fallback is diagnostic-only by default.
- A task can be benchmark-grade only if its solver-facing statement comes from
  non-leaky issue, PR, manual, customer, or other explicitly reviewed problem
  context.
- A task with good no-op/reference behavior but poor source provenance is still
  valuable operational evidence, but not benchmark-grade evidence.
- Near-certified tasks are useful diagnostic material, not release tasks.

## Starting Evidence

The worker should confirm these files exist:

```text
experiments/phase1_compiler/reports/phase1_validation_overnight_report.md
experiments/phase1_compiler/results/phase1_validation_overnight_decision.json
experiments/phase1_compiler/results/phase1_source_provenance_audit.json
experiments/phase0_headroom/certified_tasks/humanize_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/humanize_task_statements.jsonl
experiments/phase0_headroom/candidate_sources/humanize_source_context.jsonl
experiments/phase0_headroom/certified_tasks/itsdangerous_near_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/itsdangerous_certified_tasks.jsonl
experiments/phase0_headroom/releases/itsdangerous_phase0_pilot_release.json
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase1_compiler/tools/phase1_source_provenance_audit.py
```

Expected current facts:

```text
Humanize source provenance: humanize_source_provenance_fallback_confirmed
Humanize issue/PR-derived context: 0/12
Itsdangerous certified: 1
Itsdangerous near-certified: 10
Itsdangerous release status: diagnostic_only
Predictive validity: false
```

## Budget And Runtime Rules

This runbook is local-first.

- Paid ACUT cells: disabled.
- Paid LLM calls: disabled.
- GitHub metadata lookups through `gh api`: allowed if authenticated.
- Local repository mining, local certification replay, local environment probes,
  and deterministic report generation: allowed.
- Provider-billed cost should not change except for unrelated user activity.

If the worker wants to run any paid call, stop and write:

```text
experiments/phase1_compiler/reports/phase1_source_certification_hardening_blocker.md
```

with the reason and the exact proposed paid batch.

## Output Layout

Add or update:

```text
experiments/phase1_compiler/
  configs/
    phase1_source_certification_hardening.yaml
  results/
    phase1_source_certification_hardening_plan.json
    phase1_source_provenance_overlay.json
    phase1_oracle_alignment_audit.json
    phase1_environment_synthesis_diagnosis.json
    phase1_certification_hardening_decision.json
  reports/
    phase1_source_certification_hardening_process.md
    phase1_source_provenance_overlay.md
    phase1_oracle_alignment_audit.md
    phase1_environment_synthesis_diagnosis.md
    phase1_certification_hardening_decision.md
```

Optional implementation files:

```text
experiments/phase1_compiler/tools/
  phase1_source_certification_hardening.py
  phase1_oracle_alignment_audit.py
  phase1_environment_synthesis_diagnosis.py
experiments/phase1_compiler/tests/
  test_phase1_source_certification_hardening.py
```

Do not overwrite historical Phase 0 task records unless a step explicitly says
to regenerate a new versioned artifact. Prefer overlays and new reports for this
hardening pass.

## Step 0: Preflight

Actions:

1. Record branch, HEAD, date, Python version, `uv --version`, and current git
   status.
2. Confirm starting evidence:

```bash
jq -r '.decision' experiments/phase1_compiler/results/phase1_validation_overnight_decision.json
jq -r '.predictive_validity_established' experiments/phase1_compiler/results/phase1_validation_overnight_decision.json
jq -r '.source_provenance_status.humanize' experiments/phase1_compiler/results/phase1_validation_overnight_decision.json
jq -r '.third_repo_status.release_status' experiments/phase1_compiler/results/phase1_validation_overnight_decision.json
```

Expected:

```text
phase1_operational_validation_pilot_complete
false
humanize_source_provenance_fallback_confirmed
diagnostic_only
```

3. Run hygiene checks:

```bash
git diff --check
uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools
uv run --project experiments/phase1_compiler pytest -q
uv run --project experiments/phase1_compiler python \
  experiments/phase1_compiler/tools/phase1_compiler.py \
  validate \
  --config experiments/phase1_compiler/configs/phase1_mvp.yaml
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
```

4. Confirm ignored raw paths are not tracked:

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
experiments/phase1_compiler/reports/phase1_source_certification_hardening_process.md
```

Acceptance:

- scoped tests pass;
- Phase 1 compiler validate returns `status=valid`;
- no raw, workspace, external repo, venv, or cache files are tracked;
- process report records the starting evidence and no paid calls.

Stop if:

- existing tests fail before any change;
- Phase 1 MVP validation fails;
- raw artifacts are tracked;
- starting evidence does not match the expected current state.

Commit if the process report was created:

```text
Record Phase 1 source hardening preflight
```

## Step 1: Write The Hardening Plan

Actions:

1. Create:

```text
experiments/phase1_compiler/configs/phase1_source_certification_hardening.yaml
experiments/phase1_compiler/results/phase1_source_certification_hardening_plan.json
```

2. The YAML config should include:

```yaml
schema_version: barcarolle.phase1_source_certification_hardening_config.v1
status: configured
claim_scope: source_adapter_and_certification_hardening
predictive_validity_established: false
paid_acut_calls: disabled
paid_llm_calls: disabled
source_policy:
  benchmark_grade_allowed_source_kinds:
    - issue
    - pull_request
    - issue_comment
    - pr_body
    - pr_comment
    - manual_canary
    - customer_regression
  diagnostic_only_source_kinds:
    - commit_message_fallback
    - commit_subject
    - inferred_from_diff
  reject_source_kinds:
    - missing
source_quality_gates:
  commit_message_fallback_max_for_benchmark_grade: 0
  issue_or_pr_context_required_for_benchmark_grade: true
  solution_exposure_risk_allowed_for_benchmark_grade: false
oracle_alignment_gates:
  no_op_fail: required
  reference_pass_twice: required
  hidden_tests_apply_to_base: required
  changed_test_patch_nonempty: required
  wide_test_risk_review: required
  narrow_test_risk_review: required
third_repo:
  preferred_repo_id: itsdangerous
  min_certified_for_pilot: 4
  min_certified_for_benchmark_candidate: 6
  min_b_real: 2
  min_w_real: 2
```

3. The JSON plan should include:
   - current Humanize fallback count;
   - current Itsdangerous certified and near-certified counts;
   - hypotheses to test:
     `source_adapter_too_weak`, `candidate_selection_too_broad`,
     `environment_synthesis_mismatch`, `oracle_alignment_mismatch`,
     `certification_implementation_bug`;
   - expected outputs;
   - stop conditions.

Acceptance:

- plan explicitly says commit-message fallback is diagnostic-only;
- plan does not schedule any paid ACUT cell;
- plan names the decision criteria for Humanize and Itsdangerous separately.

Commit:

```text
Plan Phase 1 source and certification hardening
```

## Step 2: Implement Source Provenance Overlay

Purpose:

Do not destroy historical Phase 0 records. Add a Phase 1 overlay that interprets
the existing records under stricter source-quality rules.

Actions:

1. Implement or extend a deterministic tool that reads:

```text
experiments/phase0_headroom/candidate_sources/toolz_source_context.jsonl
experiments/phase0_headroom/candidate_sources/humanize_source_context.jsonl
experiments/phase0_headroom/candidate_sources/itsdangerous_source_context.jsonl
experiments/phase0_headroom/certified_tasks/toolz_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/humanize_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/itsdangerous_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/itsdangerous_near_certified_tasks.jsonl
```

2. Write:

```text
experiments/phase1_compiler/results/phase1_source_provenance_overlay.json
experiments/phase1_compiler/reports/phase1_source_provenance_overlay.md
```

3. Classify every task into exactly one source tier:

```text
benchmark_grade_source
manual_review_source
diagnostic_only_source
reject_source
```

4. Use these rules:
   - issue/PR/comment/manual/customer context can be
     `benchmark_grade_source` if leakage risk is false;
   - commit-message fallback is always `diagnostic_only_source`;
   - missing source context is `reject_source`;
   - release notes or changelog-only context is `manual_review_source` unless
     it directly links to a problem report.
5. The overlay must preserve the original Phase 0 status and add a new Phase 1
   status, for example:

```json
{
  "task_id": "humanize__hist__002",
  "phase0_status": "certified",
  "phase1_source_tier": "diagnostic_only_source",
  "benchmark_grade_eligible": false,
  "reason": "commit_message_fallback_only"
}
```

Acceptance:

- Humanize certified tasks are not silently kept benchmark-grade if all are
  commit-message fallback;
- Toolz remains eligible only if the overlay sees issue/PR-derived context;
- Itsdangerous certified and near-certified tasks are classified;
- JSON is deterministic and sorted by repo/task ID;
- report contains a per-repo summary table.

Commit:

```text
Add Phase 1 source provenance overlay
```

## Step 3: Harden Humanize Source Adapter

Purpose:

Determine whether Humanize can be repaired into benchmark-grade source
provenance, or whether it must remain diagnostic-only.

Actions:

1. For the 12 Humanize certified tasks, attempt metadata repair without paid LLM
   calls:
   - GitHub commit-to-PR lookup;
   - direct issue references in commit body;
   - issue references in commit subject;
   - `Fixes #...`, `Closes #...`, `Refs #...` patterns;
   - changelog entries only as manual-review evidence, not automatically
     benchmark-grade.
2. Use `gh api` if authenticated. Do not commit raw responses.
3. Store only sanitized metadata:

```text
task_id
target_commit
source_kind
source_ref
source_title
source_body_digest
source_url
classification
leakage_risk
manual_review_required
```

4. If a linked issue or PR is found, classify the source text:
   - `problem_context`: describes observed/expected behavior without revealing
     implementation;
   - `solution_context`: gives implementation steps, exact code, or patch;
   - `mixed_context`: contains both problem and solution content;
   - `insufficient_context`: does not describe the task.
5. A task is repaired only if it has at least one non-leaky
   `problem_context` source.
6. Write updated Humanize source-context artifacts under new names, not by
   overwriting the old records:

```text
experiments/phase0_headroom/candidate_sources/humanize_hardened_source_context.jsonl
experiments/phase0_headroom/candidate_sources/humanize_hardened_source_context_funnel.csv
experiments/phase1_compiler/reports/phase1_humanize_source_hardening.md
```

Acceptance:

- raw GitHub API responses are not committed;
- every Humanize certified task has a hardened decision:
  `repaired_to_problem_context`, `manual_review_required`,
  `diagnostic_only_commit_fallback`, or `reject_missing_context`;
- commit-message fallback alone never produces benchmark-grade eligibility;
- if fewer than 6 tasks are repaired, Humanize remains operational-pilot only.

Branch:

- If at least 6 Humanize tasks are repaired with non-leaky problem context,
  continue with Humanize benchmark-candidate overlay in Step 7.
- Otherwise keep Humanize diagnostic-only and focus on third-repo repair.

Commit:

```text
Harden Humanize source provenance
```

## Step 4: Add Oracle Alignment Audit

Purpose:

Separate executable test validity from problem-oracle alignment. A task may pass
no-op/reference gates but still be benchmark-poor if the hidden tests check
requirements not present in the problem statement, or enforce unnecessary
implementation details.

Actions:

1. Implement a deterministic audit over certified and near-certified tasks for
   Toolz, Humanize, and Itsdangerous.
2. Read each task's:
   - solver-facing statement;
   - code files;
   - hidden test files;
   - test patch metadata;
   - source context tier from Step 2;
   - certification gates.
3. Produce:

```text
experiments/phase1_compiler/results/phase1_oracle_alignment_audit.json
experiments/phase1_compiler/reports/phase1_oracle_alignment_audit.md
```

4. The audit should flag these risks:

```text
wide_test_risk
narrow_test_risk
weak_oracle_risk
multi_issue_patch_risk
maintenance_or_dependency_update_risk
large_cross_module_change_risk
statement_source_mismatch
reference_patch_requires_unmentioned_symbol
test_edits_only_or_config_heavy_change
```

5. Deterministic heuristics are acceptable. Examples:
   - hidden tests import or assert a new public symbol not mentioned in the
     statement;
   - changed files span many unrelated modules;
   - commit subject contains `update`, `deprecate`, `remove deprecated`,
     `drop support`, `project files`, `dev dependencies`;
   - no-op passes after hidden tests apply;
   - target fails hidden tests;
   - source tier is diagnostic-only.

Acceptance:

- every current target task has an oracle-alignment status:
  `aligned`, `manual_review_required`, `diagnostic_only`, or `reject`;
- audit explicitly distinguishes weak oracle from wide/narrow oracle risk;
- report includes per-repo counts and top rejection reasons;
- no paid LLM call is used.

Commit:

```text
Add Phase 1 oracle alignment audit
```

## Step 5: Diagnose Itsdangerous Certification Failures

Purpose:

Determine whether Itsdangerous failed because tasks were bad, the generic
candidate filter was too broad, the test environment was wrong, or the
certification implementation is faulty.

Actions:

1. Create or extend a local diagnosis tool that reads:

```text
experiments/phase0_headroom/certified_tasks/itsdangerous_near_certified_tasks.jsonl
experiments/phase0_headroom/certified_tasks/itsdangerous_certified_tasks.jsonl
experiments/phase0_headroom/candidate_sources/itsdangerous_candidates.jsonl
experiments/phase0_headroom/configs/third_repo_pilot_itsdangerous.yaml
```

2. For each near-certified task, classify the first failure:

```text
reference_pass_failure
no_op_fail_failure
checkout_failure
oracle_extract_failure
source_context_failure
scope_or_taxonomy_failure
```

3. For `reference_pass_failure`, run a bounded local environment probe against
   the target workspace. Use only small variants and record command hashes, exit
   codes, duration, and tail hashes, not full logs. Suggested variants:

```text
configured_command
pytest_current_with_editable
pytest_legacy_7_with_editable
pytest_legacy_6_with_editable
repo_declared_test_extra_if_present
```

Use `uv` and keep probes deterministic. Do not spend time building a broad
language-general environment synthesizer.

4. For `no_op_fail_failure`, inspect whether:
   - hidden test patch applied but did not fail base;
   - changed tests only cover existing behavior;
   - candidate is a maintenance/dependency update;
   - hidden oracle is too weak.
5. Write:

```text
experiments/phase1_compiler/results/phase1_environment_synthesis_diagnosis.json
experiments/phase1_compiler/reports/phase1_environment_synthesis_diagnosis.md
```

Acceptance:

- every Itsdangerous near-certified task has a failure category;
- at least one of these decisions is supported:
  `candidate_pool_bad`, `environment_synthesis_mismatch`,
  `oracle_weakness`, `certification_implementation_bug`,
  `insufficient_repo_history_supply`;
- raw command output is not committed;
- external repo and workspaces remain ignored.

Commit:

```text
Diagnose Itsdangerous certification failures
```

## Step 6: Repair Candidate Selection Rules

Purpose:

Avoid sending maintenance, dependency, deprecation, and project-file churn into
benchmark certification as if they were ordinary behavior tasks.

Actions:

1. Add a candidate-filter policy to the hardening config:

```yaml
candidate_filter_policy:
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
  reject_if_project_file_heavy: true
  reject_if_no_behavior_code_file: true
  reject_if_changed_lines_over: 250
  manual_review_if_cross_module_count_over: 3
  manual_review_if_docs_or_config_change_present: true
```

2. Implement the filter as an overlay first. Do not delete historical candidate
   rows.
3. Apply it to Itsdangerous candidates and, if cheap, to Humanize and Toolz for
   comparison.
4. Write:

```text
experiments/phase1_compiler/results/phase1_candidate_filter_audit.json
experiments/phase1_compiler/reports/phase1_candidate_filter_audit.md
```

Acceptance:

- Itsdangerous maintenance/dependency/deprecation candidates are flagged before
  certification;
- the one certified Itsdangerous task remains visible but does not become
  pilot-grade alone;
- report estimates how many candidates would remain after filtering;
- no historical artifacts are removed.

Commit:

```text
Add Phase 1 candidate filter audit
```

## Step 7: Produce Hardened Certification Overlay

Purpose:

Combine source provenance, oracle alignment, environment diagnosis, and
candidate filtering into a single benchmark-grade eligibility overlay.

Actions:

1. Create:

```text
experiments/phase1_compiler/results/phase1_hardened_certification_overlay.json
experiments/phase1_compiler/reports/phase1_hardened_certification_overlay.md
```

2. For every Toolz, Humanize, and Itsdangerous certified or near-certified task,
   compute:

```text
phase0_status
execution_gate_status
source_tier
oracle_alignment_status
candidate_filter_status
environment_status
hardened_status
hardened_reject_reasons
```

3. Allowed hardened statuses:

```text
benchmark_grade_candidate
manual_review_required
diagnostic_only
rejected
```

4. A task can be `benchmark_grade_candidate` only if:
   - execution gates pass;
   - source tier is benchmark-grade;
   - oracle alignment is aligned;
   - environment status is clean or repaired;
   - candidate filter does not reject it;
   - solution exposure risk is false.
5. Build per-repo counts:

```text
benchmark_grade_candidate_count
manual_review_required_count
diagnostic_only_count
rejected_count
```

Acceptance:

- Humanize commit-message-fallback-only tasks are not benchmark-grade;
- Toolz remains benchmark-grade candidate only if all stricter criteria pass;
- Itsdangerous status follows from evidence, not desired task count;
- report names the exact gate preventing each repo from Phase 1 validation-grade
  use.

Commit:

```text
Build Phase 1 hardened certification overlay
```

## Step 8: Decide Whether To Repair Or Replace The Third Repo

Purpose:

Turn the Itsdangerous diagnosis into an actionable decision.

Actions:

1. Use the Step 5 and Step 6 reports to choose one decision:

```text
repair_itsdangerous_environment
repair_itsdangerous_candidate_filter_and_remine
replace_third_repo
third_repo_manual_review_required
third_repo_not_needed_until_future_holdout_design
```

2. If `repair_itsdangerous_environment`:
   - write the exact environment variant that made reference passes succeed;
   - update only a new versioned config, not the original record;
   - do not run paid ACUT.
3. If `repair_itsdangerous_candidate_filter_and_remine`:
   - run local mining/certification only;
   - require at least 4 certified tasks and balanced B/W before any future paid
     ACUT runbook.
4. If `replace_third_repo`:
   - choose at most two candidate repos from `configs/repositories.yaml`;
   - justify them by expected issue/PR availability, local environment
     simplicity, and non-maintenance task supply;
   - do not clone/run them unless explicitly included in this runbook's local
     budget and artifact hygiene.
5. Write the decision into the final hardening decision report.

Acceptance:

- decision is based on observed failure categories;
- no paid ACUT cell is scheduled;
- next runbook recommendation is concrete.

Commit only if new configs or reports changed:

```text
Decide Phase 1 third repo repair path
```

## Step 9: Refresh Phase 1 Compiler Boundary

Purpose:

Make sure the Phase 1 compiler does not accidentally treat diagnostic-only
tasks as validation-grade evidence.

Actions:

1. If needed, extend Phase 1 compiler summaries to reference the new hardening
   overlay as sidecar evidence.
2. Do not change the historical MVP release to claim predictive validity.
3. Update README or reports only if they currently imply Humanize is
   benchmark-grade despite commit-message fallback.
4. Run:

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

- predictive-validity fields remain `false`;
- MVP closeout still distinguishes infrastructure evidence from validation
  evidence;
- hardening overlay is named as sidecar evidence, not silently mixed into older
  scorecards.

Commit if compiler docs or generated summaries changed:

```text
Refresh Phase 1 compiler boundary after hardening
```

## Step 10: Write Final Hardening Decision

Actions:

1. Create:

```text
experiments/phase1_compiler/results/phase1_certification_hardening_decision.json
experiments/phase1_compiler/reports/phase1_certification_hardening_decision.md
```

2. The decision JSON must include:
   - starting HEAD and final HEAD;
   - tools or configs added;
   - repos analyzed;
   - source-tier counts;
   - oracle-alignment counts;
   - environment-diagnosis counts;
   - hardened certification counts;
   - Humanize decision;
   - Itsdangerous decision;
   - whether a third repo should be repaired or replaced;
   - allowed claims;
   - disallowed claims;
   - recommended next runbook.

3. Use exactly one primary decision label:

```text
source_certification_hardening_complete_ready_for_future_holdout_design
humanize_source_blocker_confirmed_third_repo_repair_needed
third_repo_environment_repair_needed
third_repo_candidate_pool_repair_needed
replace_third_repo_before_future_holdout
certification_implementation_bug_found
```

4. The Markdown report should answer:
   - Are Humanize tasks benchmark-grade after hardening?
   - If not, why exactly?
   - Did Itsdangerous fail because of bad candidates, bad environment, weak
     oracle, or implementation bug?
   - What should the next runbook do before paid ACUT scale-up?
   - What claims are still prohibited?

Acceptance:

- report clearly answers "task selection or certification implementation?";
- report does not hide mixed causes;
- report names the next smallest useful runbook;
- no unsupported predictive-validity claim is made.

Commit:

```text
Summarize Phase 1 source certification hardening
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
git status --short --ignored experiments/phase0_headroom experiments/phase1_compiler docs/experiments AGENTS.md .gitignore
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
- final hardening decision is committed.

Do not push unless the user explicitly asked this worker to push.

## Stop Conditions

Stop and write a blocker report if any of these occur:

- a step would require paid ACUT or paid LLM calls;
- raw GitHub responses, raw logs, workspaces, or cloned repos would need to be
  committed;
- local test failures cannot be repaired in scoped code;
- source records are inconsistent enough that an overlay would mislead;
- environment diagnosis would require broad dependency archaeology beyond this
  runbook;
- hardening would force predictive-validity claims.

Blocker report path:

```text
experiments/phase1_compiler/reports/phase1_source_certification_hardening_blocker.md
```

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

Best likely outcome:

```text
humanize_source_blocker_confirmed_third_repo_repair_needed
Humanize remains diagnostic-only because commit-message fallback is not
benchmark-grade. Itsdangerous failure mode is classified. Next runbook repairs
third-repo source/environment/candidate filters or selects a replacement repo.
```

Strong outcome:

```text
source_certification_hardening_complete_ready_for_future_holdout_design
At least two repos have enough hardened benchmark-grade candidate tasks, and the
next runbook can pre-register a true future-holdout validation design.
```

Acceptable blocker outcome:

```text
certification_implementation_bug_found
The current certification implementation is wrong enough that evidence should
not be expanded until the implementation is fixed and prior artifacts are
reconciled.
```
