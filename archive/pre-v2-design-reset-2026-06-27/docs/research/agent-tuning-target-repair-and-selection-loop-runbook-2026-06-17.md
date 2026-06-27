# Agent Tuning Target Repair And Selection Loop Runbook

Date: 2026-06-17

## Goal

Advance the Agent Tuning Demo target-repository preparation until one of these
terminal states is reached:

1. `target_ready_for_paid_baseline_preregistration`: one target repository has an
   exact certified task manifest large enough for the corrected rolling-origin
   protocol and can support the next paid baseline/tuning preregistration.
2. `task_generation_method_needs_revision`: Sphinx repair, the existing
   candidate list, and additional repository search all fail under bounded
   no-paid gates, showing that the current task-mining/certification method
   needs improvement rather than another repository retry.

Do not stop only because one repository fails. Move through the loop until a
ready target is found or the evidence clearly says the method is the bottleneck.

## Boundary

This runbook is no-paid.

Do not run:

- paid Agent cells;
- paid LLM calls;
- paid tuner/proposer calls;
- paid baseline discovery;
- before/after tuning experiments.

Allowed:

- no-paid repository cloning in ignored workspace paths;
- no-paid setup smoke tests;
- no-paid candidate mining;
- no-paid replay/certification;
- bounded verifier/profile repair;
- bounded task-source repair when the failure is mechanical and locally
  testable;
- repository search if the existing shortlist is exhausted;
- tests, hygiene checks, reports, and step-level commits.

Do not touch Agent Selection Demo results or reports. Do not refresh the Agent
Tuning selection snapshot unless a direct blocker requires it.

## Context To Read First

Read:

- `AGENTS.md`
- `PROCESS.md`
- `experiments/agent_tuning_demo/reports/sphinx_protocol_manifest_freeze_closeout_zh.md`
- `experiments/agent_tuning_demo/results/sphinx_protocol_manifest_freeze_closeout.json`
- `experiments/agent_tuning_demo/reports/sphinx_certification_expanded_manifest_zh.md`
- `experiments/agent_tuning_demo/results/sphinx_certification_expanded_manifest.json`
- `experiments/agent_tuning_demo/reports/sphinx_rolling_origin_protocol_v2_zh.md`
- `experiments/agent_tuning_demo/results/sphinx_rolling_origin_protocol_v2.json`
- `experiments/agent_tuning_demo/reports/large_repo_target_selection_gate_zh.md`
- `experiments/agent_tuning_demo/results/large_repo_target_selection_gate.json`
- `experiments/agent_tuning_demo/results/large_repo_target_selection_candidates.csv`
- `experiments/agent_tuning_demo/reports/target_repo_selection_gate_zh.md`
- `experiments/agent_tuning_demo/results/target_repo_selection_gate.json`
- current target-repo and Sphinx tools/tests under
  `experiments/agent_tuning_demo/`

## Correct Rolling-Origin Standard

Use this protocol for every target candidate:

```text
history_pool_before_origin = all eligible certified tasks before the origin
selected_benchmark_from_history = tasks selected from that history pool
future_holdout_after_origin = the next time/task window after the origin
```

The selected benchmark is a subset of historical certified tasks. It is not a
separate segment between train and future.

Default minimum:

- `selected_benchmark_size = 20`
- `future_holdout_size = 20`
- at least `2` corrected origins
- at least `80` exact certified tasks

Preferred:

- at least `3` corrected origins
- at least `100` exact certified tasks

Do not fabricate windows from projections. Window manifests must be based on
exact certified tasks.

## Repository Priority

Start with Sphinx repair because it already has a target profile and failure
evidence. If Sphinx does not become ready under bounded repair, continue through
the candidate loop.

Initial priority:

1. `sphinx`
2. `mypy`
3. `black`
4. `starlette`
5. `attrs`
6. `click`

Conditional candidates from prior gates:

- `django`, `pandas`, `scikit-learn`: only if a targeted verifier profile can
  avoid heavy full-suite or compiled-extension setup cost.
- `packaging`, `marshmallow`, `urllib3`: only if their previous replay/setup
  blocker has a clear bounded repair.
- `pytest`: avoid unless no better target exists; its self-hosting harness risk
  is high.

If these candidates fail, search for additional Python repositories. Favor
repositories with:

- substantial implementation-plus-test history;
- many public issue/PR references or readable commit context;
- pure-Python or wheel-friendly dependencies;
- targetable test shards;
- no mandatory external service, database, browser, GPU, or long build step for
  ordinary unit tests;
- stable historical releases or tags that can support version-aware verifier
  pinning.

## Package 1: Sphinx Failure Diagnosis And Bounded Repair

Classify the Sphinx failure, then repair only if the root cause is narrow and
mechanical.

Inputs:

- `experiments/agent_tuning_demo/results/sphinx_certification_expanded_manifest.json`
- `experiments/agent_tuning_demo/results/sphinx_candidate_inventory.json`
- existing Sphinx certification wave/expanded attempts

Sample enough failures to classify the dominant cause:

- at least `10` `reference_target_test_failure` rows if available;
- all `target_worktree_failed` rows if the count is small;
- a few known-passing Sphinx rows for contrast.

Classify failures into concrete labels, for example:

- wrong base/target checkout or patch reconstruction;
- target tests require changed support files, fixtures, generated docs, or
  configuration not included by the verifier;
- dependency or version-profile mismatch;
- pytest node/path selection is wrong or too narrow;
- candidate has changed tests but no meaningful fail-to-pass oracle;
- target worktree setup failure;
- broad historical change unsuitable for this demo.

Try bounded repairs only when they address a repeated root cause:

- add or adjust Sphinx target profile/package map;
- include changed test support files or fixture roots when safe;
- improve pytest entry extraction;
- pin version-aware dependencies or environment flags;
- add pass-to-pass/reference replay guards;
- filter out unsuitable candidate shapes before certification.

After repair, run another no-paid certification wave. Continue only while the
recent conversion and failure labels justify it.

Sphinx stop conditions:

- ready if exact certified count reaches the minimum threshold and corrected
  windows are available;
- reject if the last `30` attempted candidates convert below `0.30` and failure
  labels are heterogeneous or not locally repairable;
- reject if repair becomes a general environment solver or a Sphinx-specific
  product project.

Artifacts:

- `experiments/agent_tuning_demo/results/sphinx_failure_diagnosis.json`
- `experiments/agent_tuning_demo/reports/sphinx_failure_diagnosis_zh.md`
- updated Sphinx profile/tooling only if repaired;
- updated Sphinx manifest/window/accounting only if the repair changes them.

## Package 2: Candidate Loop

For each candidate repository, execute the same no-paid gate. Do not wait for
user input between candidates.

### 2.1 Setup And Smoke

Create or update a target profile. Clone external repositories only under
ignored workspace/cache paths. Do not commit cloned repositories, virtualenvs,
caches, raw logs, or raw transcripts.

Run a current-version smoke test using a narrow, representative shard. Record:

- install/setup command;
- verifier command;
- median and p95 duration for targeted shards where feasible;
- dependency or environment risks.

Preferred speed:

- verifier p95 under `60s`.

Acceptable speed:

- verifier p95 under `120s` if task supply is strong and the shard is stable.

Reject or demote:

- tests require full-suite execution for ordinary certification;
- setup is repeatedly flaky or service-dependent;
- historical replay cannot be bounded.

### 2.2 Candidate Inventory

Mine a candidate inventory using existing tools where possible. The inventory
should include:

- task id;
- base commit;
- target commit;
- task time;
- changed implementation files;
- changed test files;
- pytest entry files;
- module/family;
- public issue/PR refs or other public context when available;
- preliminary risk label.

Use history-based implementation-plus-test anchors first. If a repository has
strong raw history but the current miner undercounts it, add the smallest
repo-specific adapter needed to expose the history shape. Do not build a
general new Task Generator in this run unless every repository fails and the
closeout must diagnose method limitations.

### 2.3 Certification Wave

Run a no-paid certification wave across time buckets:

- start with `24-30` candidates;
- if conversion is strong, continue until the manifest reaches the target
  threshold;
- if conversion is weak but failures are clearly repairable, perform bounded
  repair and retry;
- if conversion stays below `0.30` over the last `30` attempts and the cause is
  not repairable, reject the repository and move on.

Only exact certified tasks enter the manifest.

### 2.4 Corrected Window Manifest

If the certified manifest is large enough, create corrected rolling-origin
artifacts for that repository:

- `<repo>_certification_manifest.csv`
- `<repo>_certification_manifest.json`
- `<repo>_certification_manifest_zh.md`
- `<repo>_rolling_origin_window_manifest.json`
- `<repo>_rolling_origin_window_manifest_zh.md`
- `<repo>_paid_cell_accounting.json`
- `<repo>_paid_cell_accounting_zh.md`

The window manifest must list exact task IDs for every history pool and future
holdout. Future holdout IDs/outcomes must not be selector inputs in the future
paid run.

Default paid baseline accounting:

```text
baseline_cells_per_window = (selected_benchmark_size + future_holdout_size) * agent_count
```

For the default demo shape:

```text
(20 selected + 20 future) * 4 agents = 160 cells/window
```

No paid cells are authorized by this accounting.

## Package 3: Repository Search Expansion

Run this package only if Sphinx and the initial candidate list fail.

Build a broader no-paid screen of additional Python repositories. Include a
short table with:

- repository;
- rough scale;
- implementation-plus-test anchor count;
- public context availability;
- setup smoke result;
- targeted verifier speed;
- projected certified task count;
- certification sample result if run;
- decision label.

Search should be broad enough to test whether the repository list was the
problem. It does not need to exhaust GitHub.

If several candidates look promising, deep-probe the best `3-5` rather than
spending time on every screened repository.

## Package 4: Method-Limitation Diagnosis

If no repository reaches the exact manifest threshold, write a method-level
diagnosis instead of stopping with a single-repo failure.

Answer:

- Did repositories fail mainly because they are too small?
- Did they fail mainly because historical environments cannot be reproduced?
- Did they fail because changed tests are not self-contained hidden oracles?
- Did the miner undercount tasks because it relies on the wrong source pattern?
- Would SWE-bench-style PR/issue mining, environment synthesis, or richer
  oracle extraction likely change the result?
- What is the smallest next Task Generator improvement that could unlock the
  most candidates?

This diagnosis is the terminal state `task_generation_method_needs_revision`.

## Package 5: Closeout And Process Update

Always produce:

- `experiments/agent_tuning_demo/results/target_repair_selection_loop_closeout.json`
- `experiments/agent_tuning_demo/reports/target_repair_selection_loop_closeout_zh.md`
- a candidate decision table in CSV/JSON;
- updated `PROCESS.md`.

The closeout must state:

- final terminal state;
- selected target repository, if any;
- exact certified task count;
- corrected rolling-origin window count;
- verifier speed summary;
- expected baseline cells per window and total cells for the prepared windows;
- paid calls used, which must be `0`;
- repositories tried and why each passed/failed;
- whether the next step is paid preregistration or Task Generator repair.

If a target is ready, do not run paid baseline discovery. Provide the
preregistration inputs and stop.

## Tests And Hygiene

Run the scoped tests relevant to touched code. At minimum, if Agent Tuning Demo
tools changed:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
```

If phase1 compiler task-supply tools are touched, also run the relevant focused
phase1 tests, for example:

```text
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_task_supply_v2_generator_bakeoff.py -q
```

Always run:

```text
git diff --check
git ls-files | rg '(\.venv|\.pytest_cache|\.DS_Store|transcript|completion|prompt|workspace|raw|external|clone|outputs/)'
```

The hygiene scan may hit historical committed files or source helper filenames;
explain any hit. Do not commit raw workspaces, cloned repositories, caches,
full raw logs, prompts, completions, transcripts, or secrets.

## Commit Discipline

Make focused commits after each completed package or tightly related package
group. Do not batch unrelated repository probes, code changes, reports, and
PROCESS updates into one large commit.

If the run reaches a ready target, the final commit should make the prepared
target and closeout easy to identify. If the run reaches method-limitation
diagnosis, the final commit should make that conclusion explicit.
