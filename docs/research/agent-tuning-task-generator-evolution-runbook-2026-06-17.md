# Agent Tuning Task Generator Evolution Runbook

Date: 2026-06-17

## Goal

Evolve the Task Generator until it can produce enough locally certified tasks
for the two current Agent Tuning Demo candidate repositories:

- `sphinx` (`sphinx-doc/sphinx`)
- `mypy` (`python/mypy`)

The preferred terminal state is:

```text
task_generator_evolved_two_repo_ready
```

Minimum acceptance for each repository:

- at least `80` exact certified tasks;
- at least `2` corrected rolling-origin windows;
- `selected_benchmark_size = 20`;
- `future_holdout_size = 20`;
- future holdout IDs and outcomes are not selector inputs.

Preferred acceptance for each repository:

- at least `100` exact certified tasks;
- at least `3` corrected rolling-origin windows.

The final deliverable is not just more reports. It must include a sufficiently
evolved, refactored Task Generator whose retained core logic is the logic that
actually produced the accepted manifests.

## Working Principle

This is now a closed-form engineering problem:

```text
target repo history + public context + local verifier constraints
  -> Task Generator
  -> exact certified task manifest
  -> corrected rolling-origin windows
```

Do not keep switching repositories to avoid the problem. Iterate on the Task
Generator. Use evidence from:

- the successful boltons Agent Selection Demo task pipeline;
- local Barcarolle certification reports and failure labels;
- SWE-bench-family methodology and primary sources;
- direct no-paid experiments on Sphinx and mypy.

Autonomously propose hypotheses, implement repairs, run experiments, compare
results, keep what works, discard what does not, and continue until the
acceptance criteria are met or the method has been exhaustively demonstrated to
need a lower-level redesign. Do not stop after producing "recommended next
steps" if there is still an executable no-paid or budgeted LLM experiment that
can materially advance the runbook.

Do not ask for human intervention during this run.

## Boundary

Default boundary: no paid solver Agent cells, no paid tuner/proposer calls, no
before/after tuning experiments, and no paid baseline discovery.

Paid LLM calls are allowed only for Task Generator work that directly supports
task statement generation, statement repair, ambiguity review, leakage review,
or public-context extraction when no-paid/local methods are insufficient. The
maximum LLM experiment budget for this runbook is `$100`.

All paid LLM calls must use `LLM_BASE_URL` and `LLM_API_KEY` only. Do not use
subscription auth, `OPENAI_API_KEY`, provider-specific variables, or any other
fallback. Record model, endpoint proof, input/output digests, token/cost
accounting, and sanitized decisions. Do not commit raw prompts, raw
completions, or transcripts.

The `$100` LLM budget does not authorize paid solver Agent cells, paid
tuner/proposer calls, paid baseline discovery, or before/after tuning
experiments.

Allowed:

- web research of public primary sources;
- repository cloning under ignored workspace/cache paths;
- no-paid mining, replay, certification, and verifier-profile experiments;
- bounded environment/profile repair;
- repo-specific oracle extraction;
- support-file/test-data/fixture mining;
- statement provenance extraction from public issue/PR/commit context;
- bounded paid LLM statement generation/review experiments under the `$100`
  cap and endpoint rule above;
- local refactoring and tests.

Do not touch Agent Selection Demo result files. You may read them as successful
task-generation precedent.

## Context To Read First

Read:

- `AGENTS.md`
- `PROCESS.md`
- `docs/research/research-inputs-and-related-work-reference.md`
- `experiments/agent_selection_demo/reports/boltons_small_expansion_demo_report_zh.md`
- `experiments/agent_selection_demo/results/boltons_small_expansion_task_manifest.json`
- `experiments/agent_selection_demo/reports/boltons_selector_aware_reanalysis_closeout_zh.md`
- `experiments/agent_tuning_demo/reports/target_repair_selection_loop_closeout_zh.md`
- `experiments/agent_tuning_demo/results/target_repair_selection_method_limitation_diagnosis.json`
- `experiments/agent_tuning_demo/results/sphinx_failure_diagnosis.json`
- `experiments/agent_tuning_demo/results/mypy_certification_sample.json`
- existing tools/tests under `experiments/agent_tuning_demo/`
- relevant phase1 task-supply tools/reports under `experiments/phase1_compiler/`

## Package 1: Research And Transfer Matrix

Build a compact transfer matrix from prior work into Barcarolle implementation
ideas. Use primary sources when using web research. Do not rely on blog
summaries if papers/docs/repos are available.

At minimum, inspect methods from:

- SWE-bench;
- SWE-bench Verified;
- SWE-Bench Pro;
- SWE-bench Live;
- SWE-Bench++;
- SWE-smith or another task-production/gym source if it directly helps.

Focus only on mechanisms that can affect this run:

- issue/PR/context sourcing;
- fail-to-pass and pass-to-pass test construction;
- environment/profile synthesis;
- oracle extraction and minimization;
- support files, fixture roots, and generated test assets;
- statement clarity/leakage/ambiguity QA;
- task validity filters;
- contamination or hidden-oracle protection.

Create:

- `experiments/agent_tuning_demo/results/task_generator_related_work_transfer_matrix.json`
- `experiments/agent_tuning_demo/reports/task_generator_related_work_transfer_matrix_zh.md`

The matrix must say for each borrowed idea:

- source;
- mechanism;
- why it might help Sphinx or mypy;
- implementation hypothesis;
- experiment to validate it locally;
- whether it was later kept, rejected, or deferred.

## Package 2: Baseline Failure Reproduction With Full Subgates

Reproduce the current Sphinx and mypy failures with richer per-row subgates.

For each candidate row, record at least:

- checkout/worktree status;
- install/setup status;
- test collection status;
- target/reference changed-test result;
- base-with-injected-tests result;
- pass-to-pass guard result where feasible;
- missing support files or test-data references;
- command profile used;
- timeout/duration;
- concrete failure label.

Use the current Sphinx and mypy artifacts as inputs but do not rely on their
coarse labels.

Create:

- `experiments/agent_tuning_demo/results/task_generator_baseline_failure_reproduction.json`
- `experiments/agent_tuning_demo/reports/task_generator_baseline_failure_reproduction_zh.md`

This package should make the next hypotheses data-driven, not speculative.

## Package 3: Generator Hypotheses And Experiment Plan

Define a small set of concrete generator hypotheses before coding large changes.
The list should be revised as evidence arrives, but it must include these
families unless the baseline reproduction proves one irrelevant:

1. Selection-Demo compatibility: port the successful boltons release-eligible
   task pipeline shape into a reusable generator path.
2. Support-root oracle extraction: include changed fixture roots, test-data
   files, generated docs/test assets, and adjacent support files when they are
   needed for the hidden oracle to be self-contained.
3. Repo-specific oracle adapters:
   - Sphinx: `tests/roots`, doc build fixtures, `conf.py`-style support,
     extension/domain-specific tests, and version-aware pytest commands.
   - mypy: data-driven test files, `test-data` or equivalent repositories of
     expected outputs, mypyc test data, and command profiles that match mypy's
     historical test harness.
4. Version-aware verifier profiles: choose Python/dependency/install profiles by
   task time or repository metadata instead of one generic command.
5. Fail-to-pass/pass-to-pass guards: keep only tasks where the hidden oracle is
   meaningful and not already passing on base, and where nearby unchanged tests
   do not regress under the reference patch.
6. Public context statement provenance: derive solver-visible statements from
   issue/PR/commit context when available; if context is thin, add a
   diff-assisted statement synthesis path as a later, separately labeled
   reservoir.

Create:

- `experiments/agent_tuning_demo/results/task_generator_hypothesis_registry.json`
- `experiments/agent_tuning_demo/reports/task_generator_hypothesis_registry_zh.md`

Each hypothesis needs a local experiment and a keep/reject threshold.

## Package 4: Iterative Implementation And Certification Loop

Implement and test generator improvements iteratively. Each loop should be:

```text
hypothesis -> narrow implementation -> no-paid sample -> measured conversion
  -> keep/refine/reject -> next hypothesis
```

Do not build a large generic framework before the first measured improvement.
Prefer narrow reusable code that directly improves Sphinx or mypy certification.

Minimum loop requirements before declaring the method exhausted:

- at least `3` distinct generator mechanisms implemented and evaluated;
- repo-specific oracle adapters evaluated for both Sphinx and mypy;
- version-aware verifier profile logic evaluated for both repositories;
- at least `60` new no-paid certification attempts per repository, unless the
  repository reaches the target earlier or the candidate inventory is genuinely
  exhausted;
- all failed attempts classified with concrete subgate labels.

Scale up only mechanisms that improve exact certification conversion or
manifest quality.

Candidate reservoirs may include:

- changed Python tests;
- changed non-Python test data;
- changed fixture/support roots;
- public issue/PR-linked historical changes;
- commit-message-only changes with explicit low-confidence labels;
- diff-assisted statement candidates, if locally reviewable and clearly
  separated from hidden oracle material.

Do not promote a reservoir into the final manifest unless local certification
passes.

Create per-iteration artifacts:

- `experiments/agent_tuning_demo/results/task_generator_iteration_log.jsonl`
- `experiments/agent_tuning_demo/reports/task_generator_iteration_log_zh.md`

## Package 5: Exact Manifest Build For Sphinx And Mypy

Once mechanisms show improvement, build exact certified manifests for both
repositories.

Required outputs:

- `experiments/agent_tuning_demo/results/sphinx_task_generator_certified_manifest.csv`
- `experiments/agent_tuning_demo/results/sphinx_task_generator_certified_manifest.json`
- `experiments/agent_tuning_demo/reports/sphinx_task_generator_certified_manifest_zh.md`
- `experiments/agent_tuning_demo/results/mypy_task_generator_certified_manifest.csv`
- `experiments/agent_tuning_demo/results/mypy_task_generator_certified_manifest.json`
- `experiments/agent_tuning_demo/reports/mypy_task_generator_certified_manifest_zh.md`

Each task row must include:

- task id;
- repository id;
- reservoir/source type;
- base commit;
- target commit;
- task time;
- module/family;
- changed implementation files;
- changed test files;
- support/test-data/fixture files included in the oracle;
- solver-visible statement provenance;
- hidden oracle provenance;
- verifier profile;
- verifier command digest;
- subgate results;
- certification duration;
- leakage/ambiguity/source-confidence labels;
- sanitized evidence digest.

Only exact certified tasks count toward the acceptance threshold.

## Package 6: Corrected Rolling-Origin Windows

For each repository, create corrected rolling-origin windows from the exact
manifest.

Required outputs:

- `experiments/agent_tuning_demo/results/sphinx_task_generator_rolling_origin_windows.json`
- `experiments/agent_tuning_demo/reports/sphinx_task_generator_rolling_origin_windows_zh.md`
- `experiments/agent_tuning_demo/results/mypy_task_generator_rolling_origin_windows.json`
- `experiments/agent_tuning_demo/reports/mypy_task_generator_rolling_origin_windows_zh.md`
- `experiments/agent_tuning_demo/results/task_generator_paid_cell_accounting.json`
- `experiments/agent_tuning_demo/reports/task_generator_paid_cell_accounting_zh.md`

For every origin:

```text
history_pool_before_origin = all certified tasks before the origin
selected_benchmark_from_history = not selected by this run unless needed for a
  no-paid example; future paid run will freeze the selector separately
future_holdout_after_origin = next certified future window
```

Default accounting:

```text
(20 selected + 20 future) * 4 agents = 160 baseline cells/window
```

This accounting is not authorization to run paid cells.

## Package 7: Final Refactor And Consolidation

Before closeout, do a cleanup pass. The submitted Task Generator must not be a
pile of experimental scripts.

Refactor requirements:

- keep the final effective generator path in a clear location chosen according
  to existing repo patterns;
- separate repo-specific adapters from shared generator/certification logic;
- remove or quarantine dead experimental branches that did not affect the final
  result;
- keep reports for rejected ideas, but do not leave unused code paths as active
  APIs;
- keep names simple and readable; avoid carrying excessive concept load from
  old experiments;
- add tests for the stable generator contracts and representative Sphinx/mypy
  adapter behavior.

Do not rewrite unrelated Agent Selection Demo code. If shared helpers are useful,
add them under a neutral shared location and keep Tuning isolated from live
Selection results.

## Package 8: Closeout

Create:

- `experiments/agent_tuning_demo/results/task_generator_evolution_closeout.json`
- `experiments/agent_tuning_demo/reports/task_generator_evolution_closeout_zh.md`
- update `PROCESS.md`

The closeout must state:

- final terminal state;
- exact certified task count for Sphinx and mypy;
- corrected rolling-origin window count for Sphinx and mypy;
- which generator mechanisms were kept;
- which mechanisms were rejected and why;
- whether the final generator uses any external related-work idea;
- paid calls used, expected to be `0`;
- next step for paid preregistration if both repositories pass;
- remaining risks.

If acceptance is not met, do not simply say "blocked". The closeout must show
the implemented mechanisms, the experiments run, why they failed, and the
smallest lower-level redesign needed. However, this is a failure terminal state;
the preferred and expected terminal state is two-repo readiness.

## Tests And Hygiene

Run focused tests for touched tools. At minimum:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
```

If phase1 task-supply tools are touched, run the relevant phase1 tests, for
example:

```text
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_task_supply_v2_generator_bakeoff.py -q
```

Always run:

```text
git diff --check
git ls-files | rg '(\.venv|\.pytest_cache|\.DS_Store|transcript|completion|prompt|workspace|raw|external|clone|outputs/)'
```

Explain historical path-name hits. Do not commit raw workspaces, cloned
repositories, caches, full raw logs, prompts, completions, transcripts, or
secrets.

## Commit Discipline

Make focused commits after each package or tightly related package group.

Use commit messages that distinguish:

- literature/transfer matrix;
- baseline reproduction;
- generator mechanism implementation;
- certification scale-up;
- final refactor;
- closeout.

Do not batch unrelated experiments and final refactor into a single commit.
