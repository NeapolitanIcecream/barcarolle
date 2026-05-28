# Phase 1 Third Repo Release Supply Screen Runbook

Status: implementation runbook, 2026-05-28.

This runbook is for one dedicated Codex CLI session. Its job is narrow:

```text
Find one more target repository that can plausibly reach 30 release-eligible
tasks under Barcarolle's local certification and source-context policy.
```

Plain-language summary:

```text
attrs and boltons are now good enough on task supply: both have at least 30
release-eligible tasks.

The paid gate still fails because Barcarolle needs three repos at that level.
toolz and humanize do not currently look close enough. This runbook screens new
candidate repositories, mines bounded repo-history v2 candidates for the best
ones, and runs a small fresh certification wave only where cheap evidence says
the repo has a realistic path to 30 release-eligible tasks.

This is not a new Task Generator research branch. It is supply qualification
work needed before returning to benchmark compiler validation.
```

This is a local-only runbook. Do not run paid ACUT solver cells, paid
task-solving calls, paid replication, benchmark scoring, paid LLM statement
generation, or paid LLM review.

## Starting Point

The attrs source repair run ended with:

```text
attrs release eligible:   31
boltons release eligible: 35
repos meeting 30:         attrs, boltons
paid ready:               false
blocking reason:          third_repo_still_needed
```

The fresh certification run showed:

```text
humanize technical certified: 9
humanize release eligible:    0
toolz technical certified:    6
toolz release eligible:       5
```

Simple interpretation:

```text
attrs is fixed.
boltons is fixed.
The next blocker is one more repo with 30 release-eligible tasks.
```

## Handoff Prompt

Use this prompt to start the worker session:

```text
You are executing docs/experiments/phase-1-third-repo-release-supply-screen-runbook.md.

Work in /Users/chenmohan/gits/barcarolle. Read AGENTS.md first. Use uv for
repo-local Python tooling. Follow AGENTS.md step-level acceptance and commit
requirements: after each step, or after a small group of tightly related steps,
commit the changed files with an appropriately scoped commit.

Main goal: find one additional repository that can plausibly reach 30
release-eligible tasks. attrs and boltons already meet the threshold. The new
repo must pass local supply, source-context, oracle, and certification screens
before it can count.

Use simple language in reports. For every major result, say:
1. What happened.
2. Why it matters.
3. Whether it argues for certifying this repo, rejecting it, or collecting more
   bounded evidence.

Do not run paid ACUT solver cells, paid task-solving calls, paid replication,
benchmark scoring, paid LLM statement generation, or paid LLM review. Network
access is allowed for public repository cloning/fetching and public GitHub
issue/PR metadata lookup. Do not commit cloned repositories, raw GitHub API
responses, raw stdout/stderr logs, raw prompts, raw completions, raw target
diffs, raw test patches, solver workspaces, verifier workspaces, .venv, caches,
or large raw outputs.

Do not treat this as a general SWE task factory project. The only success
criterion is whether one candidate repo can become the third Barcarolle
release-supply repo.

Do not draft or create the next runbook. Stop at a decision report with
completed work, blockers, and recommended next action categories.
```

## Inputs

Read these files before making changes:

```text
AGENTS.md
docs/experiments/phase-1-task-supply-v2-generator-bakeoff-runbook.md
docs/experiments/phase-1-task-supply-v2-fresh-certification-runbook.md
docs/experiments/phase-1-attrs-source-repair-runbook.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_decision.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_fresh_certification_paid_readiness_gate.md
experiments/phase1_compiler/reports/phase1_attrs_source_repair_decision.md
experiments/phase1_compiler/reports/phase1_attrs_source_repair_paid_readiness_gate.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_source_bakeoff_decision.md
experiments/phase1_compiler/reports/phase1_task_supply_v2_future_directions.md
```

Use these machine-readable inputs:

```text
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_paid_readiness_gate.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_decision.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_paid_readiness_gate.json
experiments/phase1_compiler/results/phase1_attrs_source_repair_decision.json
experiments/phase1_compiler/results/phase1_task_supply_v2_raw_anchor_inventory.json
experiments/phase1_compiler/results/phase1_task_supply_v2_source_context_inventory.json
experiments/phase1_compiler/results/phase1_task_supply_v2_oracle_extraction_matrix.json
experiments/phase1_compiler/results/phase1_task_supply_v2_fresh_certification_attempts.json
experiments/phase1_compiler/schemas/task_source_candidate_v2.schema.json
experiments/phase0_headroom/configs/repositories.yaml
```

Useful implementation references:

```text
experiments/phase1_compiler/tools/phase1_task_supply_v2_generator_bakeoff.py
experiments/phase1_compiler/tools/phase1_task_supply_v2_fresh_certification.py
experiments/phase1_compiler/tools/phase1_attrs_source_repair.py
experiments/phase1_compiler/tools/phase1_historical_environment_synthesis_gate.py
experiments/phase0_headroom/tools/repo_history_pilot.py
experiments/phase1_compiler/tests/test_phase1_task_supply_v2_generator_bakeoff.py
experiments/phase1_compiler/tests/test_phase1_task_supply_v2_fresh_certification.py
experiments/phase1_compiler/tests/test_phase1_attrs_source_repair.py
```

## Candidate Repositories

Treat this as a seed list, not as a preselected winner:

```text
packaging
pluggy
cachetools
sortedcontainers
click
jinja2
werkzeug
```

Use these public upstream URLs unless a repo has moved:

```text
packaging:        https://github.com/pypa/packaging.git
pluggy:           https://github.com/pytest-dev/pluggy.git
cachetools:       https://github.com/tkem/cachetools.git
sortedcontainers: https://github.com/grantjenks/python-sortedcontainers.git
click:            https://github.com/pallets/click.git
jinja2:           https://github.com/pallets/jinja.git
werkzeug:         https://github.com/pallets/werkzeug.git
```

Known local comparison repos:

```text
toolz
humanize
```

Do not spend most of the run trying to rescue toolz or humanize. They are useful
comparators and may be included in reports, but the current evidence says they
are far below 30 technical certifications. Use bounded checks only.

## Selection Criteria

Prefer repos with:

```text
pure or mostly pure Python
pytest-based local tests
low external service risk
many commits that touch implementation and tests together
public issue/PR context for a meaningful share of commits
changed-test oracles that can be extracted cleanly
historical environments that uv can reconstruct
short changed-test runtime
limited snapshot/golden-file flakiness
clear package layout
```

Reject or downgrade repos with:

```text
external service or network-heavy tests
large browser/database/container dependencies
very few implementation-plus-test commits
mostly documentation or formatting history
dominant snapshot/golden-output tests that are hard to sanitize
test suites that require unsupported Python versions for most historical tasks
source context that is mostly commit-message-only with no public review path
high material leakage risk
```

## Outputs

Create a new local-only run under this prefix:

```text
phase1_third_repo_release_supply_screen
```

Expected committed outputs:

```text
experiments/phase1_compiler/configs/phase1_third_repo_release_supply_screen.yaml
experiments/phase1_compiler/tools/phase1_third_repo_release_supply_screen.py
experiments/phase1_compiler/tests/test_phase1_third_repo_release_supply_screen.py

experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_preflight.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_repo_shortlist.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_raw_anchor_inventory.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_source_context_inventory.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_oracle_matrix.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_environment_probe.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_certification_attempts.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_release_gate.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_decision.json

experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_process.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_repo_shortlist.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_raw_anchor_inventory.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_source_context_inventory.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_oracle_matrix.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_environment_probe.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_certification_attempts.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_release_gate.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_decision.md
```

Allowed ignored outputs:

```text
experiments/phase1_compiler/tmp/third_repo_release_supply_screen/
experiments/phase0_headroom/workspaces/third_repo_release_supply_screen/
experiments/phase0_headroom/cache/third_repo_release_supply_screen/
experiments/phase0_headroom/external_repos/<candidate_repo>/
```

Committed JSON and Markdown must contain only sanitized metadata, counts, short
summaries, hashes, source-context classes, subgate labels, and task ids.

## Definitions

Use these terms consistently:

```text
raw_anchor:
  A history commit or public issue/PR anchor that may become a task candidate.

oracle_usable:
  The candidate has changed tests that can be extracted as a private verifier
  oracle. Issue-only rows without changed tests are inventory only.

technical_certified:
  Base/no-op fails on the extracted oracle, target/reference passes twice, and
  the task is stable under an accepted uv environment profile.

statement_ready:
  The solver-facing source context is accepted public issue/PR context,
  accepted PR-title-only context, or a separately reviewed repair overlay.

release_eligible:
  technical_certified and statement_ready, with no material leakage or
  ambiguity blocker.

third_repo_candidate_ready:
  A repo has at least 30 release-eligible tasks or a conservative projection
  showing a bounded path to 30 that requires only source review of already
  technical-certified tasks.
```

## Claim Boundary

Allowed claims:

```text
third_repo_supply_screen_completed
repo_shortlist_built
repo_raw_anchor_inventory_completed
repo_source_context_screen_completed
repo_oracle_screen_completed
repo_environment_probe_completed
bounded_certification_wave_completed
third_repo_candidate_ready
third_repo_supply_still_blocked
paid_gate_recomputed
paid_validation_not_run
```

Disallowed claims:

```text
predictive_validity_established
production_benchmark_ranking
paid_acut_validation_completed
solver_performance_improved
task_generator_is_barcarolle_core_contribution
generated_oracle_promoted_to_eval_pool
commit_message_only_context_is_release_eligible_without_review
third_repo_ready_from_raw_candidates_only
third_repo_ready_from_technical_certification_only
```

## Budget And Runtime Caps

Use these caps unless the process report records a smaller conservative cap:

```text
candidate repos in cheap screen:           at most 7
repos cloned/fetched in this run:          at most 7
repos advanced to raw v2 mining:           at most 4
repos advanced to certification wave:      at most 3
raw anchors scanned per repo:              at most 2000
raw candidates retained per repo:          at most 300
certification attempts per advanced repo:  at most 120
environment profiles per candidate:        at most 5
single command timeout:                    120 seconds
single candidate total timeout:            600 seconds
runbook wall-clock budget:                 8 hours
paid provider cost:                        0
```

Do not infer that a repo is exhausted from cap-deferred candidates. Record cap
deferment separately.

## Step 0 - Preflight And Current Gate Snapshot

Goal: prove the run starts from a known local state.

Actions:

1. Run `git status --short --untracked-files=all`.
2. Record branch, HEAD, date, Python version, and `uv --version`.
3. Confirm attrs and boltons are at or above 30 release eligible.
4. Confirm paid readiness is still blocked only by the missing third repo.
5. Confirm no paid ACUT or paid LLM calls are needed.
6. Record which candidate repos already exist under ignored external-repo
   paths and which need clone/fetch.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_preflight.json
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_process.md
```

Acceptance:

- The report says attrs and boltons are already supply anchors.
- The report says the current blocker is third repo supply.
- Dirty/untracked files are classified as relevant, ignored artifact output, or
  unrelated.

Commit guidance:

- Commit preflight artifacts as one preflight commit.
- Do not stage unrelated external-review bundle files.

## Step 1 - Cheap Repository Shortlist

Goal: avoid spending certification time on repos that obviously cannot support
30 release-eligible tasks.

Actions:

1. For each seed candidate, collect cheap metadata:
   - repo URL and local path;
   - language and package manager hints;
   - test framework hints;
   - external service risk;
   - approximate implementation-plus-test commit count;
   - recent maintenance signal from public git history;
   - rough public issue/PR linkability for changed-test commits;
   - obvious environment blockers.
2. Use local git history whenever possible. If network is used, store only
   sanitized metadata and links.
3. Score each repo with an auditable rubric:

```text
history_supply_score
oracle_supply_score
source_context_score
environment_score
runtime_score
external_service_risk_score
overall_screen_label
```

4. Select at most 4 repos for raw v2 mining.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_repo_shortlist.json
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_repo_shortlist.md
```

Acceptance:

- Every seed repo receives a screen label:
  `advance_to_raw_mining`, `backup_only`, or `reject_for_this_run`.
- At most 4 repos advance.
- Rejection reasons are plain and concrete.

Commit guidance:

- Commit shortlist config/tool/test/report artifacts together.

## Step 2 - Raw v2 Mining For Advanced Repos

Goal: produce normalized candidate inventory for repos that passed the cheap
screen.

Actions:

1. Generalize or wrap existing repo-history v2 mining code if needed.
2. For each advanced repo, mine bounded candidates:
   - implementation files changed;
   - test files changed;
   - base commit;
   - target commit;
   - task time;
   - source reservoir;
   - public context refs when available;
   - changed-test oracle presence.
3. Deduplicate candidates by stable key.
4. Validate rows against `TaskSourceCandidate v2` where applicable.
5. Do not include raw diffs or raw test patches in committed artifacts.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_raw_anchor_inventory.json
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_raw_anchor_inventory.md
```

Acceptance:

- Every advanced repo has raw candidate counts and deduplicated counts.
- Every row has a terminal inventory status:
  `oracle_usable`, `oracle_missing_inventory_only`, `material_leakage_risk`,
  `candidate_outside_scope`, or `duplicate_candidate`.
- Repos with too few oracle-usable candidates are stopped before certification.

Commit guidance:

- Commit raw inventory artifacts separately from certification artifacts.

## Step 3 - Source Context And Oracle Screen

Goal: estimate release-eligible potential before running expensive local
certification.

Actions:

1. For every raw candidate in advanced repos, classify source context:
   - `non_leaky_issue_or_pr_context`;
   - `pr_title_only_context`;
   - `commit_message_only_context`;
   - `no_usable_public_context`;
   - `material_ambiguity_risk`;
   - `material_leakage_risk`.
2. Classify oracle usability:
   - changed tests present;
   - private oracle patch extractable;
   - test files are within scope;
   - target patch not exposed to solver.
3. Estimate a conservative release path:

```text
release_ready_before_certification =
  oracle_usable AND source context in accepted release classes

technical_plus_review_upper_bound =
  oracle_usable AND source context not materially leaky
```

4. Select at most 3 repos for environment/certification wave.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_source_context_inventory.json
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_oracle_matrix.json
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_source_context_inventory.md
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_oracle_matrix.md
```

Acceptance:

- A repo should normally advance only if it has at least 45 oracle-usable,
  non-leaky candidates or a strong reason why certification yield is expected
  to be high.
- A repo with mostly commit-message-only context may advance only if the report
  records a bounded source-repair path and does not count those tasks as release
  eligible yet.

Commit guidance:

- Commit source/oracle screen artifacts as one scoped commit.

## Step 4 - Environment Probe

Goal: avoid running a long certification wave in a repo whose historical test
environment is obviously unstable.

Actions:

1. For each repo advanced from Step 3, sample at most 12 oracle-usable
   candidates across time buckets.
2. Run bounded uv environment probes using current and historical profiles.
3. Classify failures with the normalized subgates:
   - checkout_failed;
   - install_failed;
   - import_failed;
   - collect_failed;
   - noop_assert_failed;
   - reference_assert_failed;
   - technical_certified;
   - timeout;
   - unknown_failed.
4. Stop a repo before the full certification wave if environment failures make
   30 technical certifications implausible within this run.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_environment_probe.json
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_environment_probe.md
```

Acceptance:

- Each probed repo has sample size, profiles tried, pass/fail subgates, and a
  decision: `advance_to_certification_wave`, `needs_environment_repair`, or
  `reject_for_this_run`.
- At most 3 repos advance.

Commit guidance:

- Commit environment probe config/tool/test/report artifacts together.

## Step 5 - Bounded Fresh Certification Wave

Goal: measure real technical and release-eligible supply for the best repos.

Actions:

1. For each repo advanced from Step 4, certify up to 120 selected candidates.
2. Use the same benchmark-side technical certification idea as the fresh v2 run:
   - checkout base and target;
   - extract changed-test oracle;
   - apply oracle to base/no-op workspace;
   - expect no-op assertion failure, not install/import/collect failure;
   - run reference on target and expect pass;
   - run reference repeat and expect pass;
   - record subgate labels and command metadata only.
3. Count release eligibility separately from technical certification.
4. Build a source-review queue for technical-certified but source-not-ready
   tasks.
5. Do not promote commit-message-only tasks without a separate review overlay.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_certification_attempts.json
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_certification_attempts.md
```

Acceptance:

- Each attempted candidate has one terminal execution subgate.
- Technical certification and release eligibility are counted separately.
- Raw logs and workspaces are under ignored paths only.

Commit guidance:

- Commit each repo's certification wave separately if it changes many result
  files.

## Step 6 - Third Repo Release Gate

Goal: decide whether the third repo blocker is solved.

Actions:

1. Recompute release-eligible counts by repo using:
   - attrs source-repair overlay;
   - boltons fresh certification count;
   - candidate third repo certification results;
   - any source-review overlay produced in this run.
2. Report:
   - technical certified count by candidate repo;
   - release eligible count by candidate repo;
   - source review queue count by candidate repo;
   - repos meeting 30 release eligible;
   - paid readiness status.
3. If a repo has at least 30 technical certifications but fewer than 30 release
   eligible because of source context, report the exact number of source repairs
   needed. Do not count them as release eligible yet.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_release_gate.json
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_release_gate.md
```

Acceptance:

- Paid ready is true only if at least 3 repos have at least 30 release-eligible
  tasks.
- Raw candidates and technical certifications alone do not satisfy the gate.

Commit guidance:

- Commit gate artifacts as one scoped commit.

## Step 7 - Decision And Closeout

Goal: give the coordinating session a clear next decision.

Actions:

1. Write the final decision report.
2. Answer these research questions:

```text
RQ1: Which repos were screened, advanced, and rejected?
RQ2: Which repo has the strongest path to 30 release-eligible tasks?
RQ3: Did any repo reach 30 release-eligible tasks in this run?
RQ4: If no repo reached 30, what is the smallest blocker:
     raw supply, oracle extraction, environment, source context, or runtime cap?
RQ5: Are attrs, boltons, and a third repo now all at 30 release eligible?
RQ6: Were any paid ACUT, paid task-solving, paid replication, or paid LLM calls
     made?
RQ7: Should the next coordinating step be paid-readiness packaging,
     source-context repair for one candidate repo, environment repair, or more
     repo screening?
```

3. Record completed steps, commits made during the run, tests run, and known
   blockers.
4. Do not draft a follow-up runbook.

Expected evidence:

```text
experiments/phase1_compiler/results/phase1_third_repo_release_supply_screen_decision.json
experiments/phase1_compiler/reports/phase1_third_repo_release_supply_screen_decision.md
```

Acceptance:

- The decision says one of:

```text
third_repo_ready_paid_gate_ready_for_packaging
third_repo_technical_ready_source_repair_needed
third_repo_supply_still_blocked_continue_screening
third_repo_environment_repair_needed
blocked_by_runtime_or_tooling
```

- The report uses simple language and does not overclaim predictive validity.

Commit guidance:

- Commit closeout artifacts as the final runbook execution commit.

## Verification

At minimum, run:

```bash
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_third_repo_release_supply_screen.py -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q
git diff --check
git status --short --untracked-files=all
```

If the full test suite is too slow or blocked, run focused tests plus the
nearest related tests and record the reason.

## Final Reporting Template

The final worker summary should be short and in simple Chinese:

```text
这次 runbook 筛的是第三仓库供给，不是 paid validation。

结果：
- 已经达标的 repo：attrs、boltons。
- 本次筛过的候选 repo：...
- 最强第三仓库候选：...
- 它的 technical certified 数量：...
- 它的 release eligible 数量：...
- paid gate 是否通过：是/否。

如果 paid gate 还没通过，原因是：
- raw/oracle supply 不够，或
- 环境验证不过，或
- 题面来源还需要 review，或
- runtime cap 下证据还不够。

没有运行 paid ACUT solver cells、paid replication、paid LLM generation/review。
```

