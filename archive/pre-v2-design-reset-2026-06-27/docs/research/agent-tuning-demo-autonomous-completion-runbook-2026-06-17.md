# Agent Tuning Demo Autonomous Completion Runbook

Date: 2026-06-17

## Goal

Push the Agent Tuning Demo to completion with the same autonomous exploration
strategy used for Task Generator evolution.

Run until one of these terminal conditions is reached:

1. `agent_tuning_demo_complete`: the demo has a clear end-to-end story,
   committed evidence, cost ledger, and final report.
2. `deadline_checkpoint_2026_06_18_0800_bjt`: Beijing time has reached
   `2026-06-18 08:00:00 +0800`, so the run must checkpoint for the user's
   planned network interruption.

If the demo is incomplete, do not voluntarily stop before Beijing time
`2026-06-18 07:00:00 +0800`. Before that time, keep solving concrete blockers,
running bounded experiments, and iterating. After `07:00`, continue if completion
is still plausible before the hard deadline, but prioritize a clean checkpoint
if the remaining work cannot finish safely before `08:00`.

## Demo Completion Definition

The demo is complete when all of the following are true:

- A preregistered Agent Tuning protocol is frozen before paid result
  inspection.
- The protocol uses the corrected rolling-origin shape:

  ```text
  history_pool_before_origin -> selected_benchmark_from_history -> future_holdout_after_origin
  ```

- At least one of the prepared target repositories (`sphinx`, `mypy`) has a
  completed before/after tuning evaluation on held-out future tasks.
- Preferably both repositories are used. If time or cost makes that infeasible,
  one repository can be primary and the second can be used as a no-paid or
  smaller paid sanity check, with the tradeoff clearly recorded.
- A real deployable tuning artifact is produced, frozen, injected, and evaluated
  against a baseline Agent. The preferred surface is the most reliable Kilo
  repo-local artifact path established by earlier Phase 1/2 work, unless a
  better path is demonstrated.
- The tuner/proposer may be GEPA-style, Phoenix-style, DSPy-native, a local
  learned/rule-based proposer, or another implementable strategy. Choose
  pragmatically based on the evidence and available time.
- Training/dev feedback must not use future holdout outcomes or future holdout
  task IDs as tuning inputs.
- The final report can explain what happened in simple terms:
  - what was tuned;
  - what feedback Barcarolle supplied;
  - what changed in the artifact;
  - how Selection/dev and future holdout behaved;
  - whether the tuned artifact improved, did not move, or regressed;
  - what this proves and does not prove.
- All LLM/Agent/tuner call costs in USD are recorded rigorously.
- Paid-cell execution uses an audited bounded-concurrency path, or the final
  report explicitly justifies why a sequential fallback was acceptable for the
  small remaining batch or deadline checkpoint.

A positive improvement is preferred. A negative or neutral result can still be
accepted only after the Agent has made serious autonomous attempts to improve
the artifact/tuner strategy and the final story is still useful: Barcarolle can
generate task supply, produce feedback, run before/after held-out validation,
and quantify why the current tuning approach did or did not work.

## Time Policy

Use Asia/Shanghai / Beijing time for all deadline decisions.

- Current run deadline: `2026-06-18 08:00:00 +0800`.
- Incomplete-demo persistence floor: `2026-06-18 07:00:00 +0800`.
- Start checkpoint preparation no later than `2026-06-18 07:30:00 +0800` unless
  the final completion package is already being written.
- Hard stop by `2026-06-18 08:00:00 +0800`.

If the run reaches `07:00` and the demo is incomplete:

- continue execution if the remaining work is concrete and likely to finish
  before `08:00`;
- otherwise switch to checkpoint mode: close running paid batches cleanly,
  preserve partial ledgers, write reports, commit, and state the exact restart
  command/next action.

If a paid cell is still running near the hard deadline, stop launching new paid
cells and write a checkpoint from completed artifacts. Do not leave required
sessions running when the run closes.

## Paid-Call Boundary And Cost Ledger

Paid calls are allowed when needed to complete the Agent Tuning Demo. They do
not require additional user confirmation in this runbook.

All paid LLM, solver Agent, tuner/proposer, reflection, or model calls must use
`LLM_BASE_URL` and `LLM_API_KEY`. If either variable is missing, source
`~/.zshrc` and recheck before any paid call. Do not fall back to subscription
auth, `OPENAI_API_KEY`, provider-specific variables, or unproven harness auth.

Maintain a rigorous cost ledger from the first paid call:

```text
experiments/agent_tuning_demo/results/agent_tuning_demo_cost_ledger.jsonl
experiments/agent_tuning_demo/results/agent_tuning_demo_cost_summary.json
experiments/agent_tuning_demo/reports/agent_tuning_demo_cost_summary_zh.md
```

Every ledger row must include:

- stable call/cell id;
- timestamp with timezone;
- call category: solver Agent, tuner/proposer, reflection, statement generation,
  verifier-adjacent LLM, or other;
- repository;
- window/origin;
- task id or artifact id where applicable;
- Agent/model/harness/surface;
- endpoint proof status;
- input/output token usage if observed;
- token usage source;
- observed or estimated USD cost;
- cost observation kind: actual billed, observed tokens estimated, missing usage
  conservative estimate, no-cost local, or unknown;
- latency;
- terminal status;
- artifact/result path;
- cumulative estimated cost after the row.

If token usage is missing, use a conservative estimate and mark it as such. Do
not present estimated cost as actual billing. The final report must separate
observed-token estimates, conservative estimates, and actual billed costs if any
actual billed costs are available.

Use staged paid batches. Before each batch, write the planned maximum cells and
estimated cost. After each batch, update the ledger and decide whether the next
batch is still needed for the demo story. Avoid spending on large matrices that
do not change the story.

## Paid-Cell Parallelization Gate

Paid solver Agent cells are expected to be the main wall-clock bottleneck. Before
launching any medium or large paid batch, audit the current Agent Tuning runner
and shared helpers for safe batch execution.

If a safe parallel runner already exists, record:

- command entry point;
- maximum concurrency used for this run;
- per-cell timeout and cleanup grace;
- checkpoint/resume behavior;
- duplicate-cell prevention;
- cost-ledger write strategy;
- workspace isolation strategy;
- endpoint-proof behavior for each worker.

If no safe runner exists, implement the smallest bounded-concurrency runner
needed for this demo before large paid batches. It must provide:

- stable cell ids and idempotent skip/resume for completed cells;
- configurable `--max-concurrency` with a conservative default of `2`;
- an explicit upper bound of `4` unless smoke evidence shows the endpoint,
  harness, and local machine are stable at a higher value;
- separate solver/verifier workspaces per cell;
- per-cell timeout, cleanup grace, and terminal status recording;
- no-future-leakage preservation across workers;
- endpoint proof in each worker before paid calls;
- duplicate-paid-call protection when restarting after interruption;
- cost ledger correctness under concurrency, using either a file lock,
  per-worker ledgers followed by deterministic merge, or atomic temp-file
  writes;
- progress/checkpoint artifacts that make a deadline stop restartable.

Run a tiny smoke batch before the first large paid batch. Prefer no-paid or
already-cached cells for the smoke. If a paid smoke is necessary, cap it at the
minimum number of cells needed to prove scheduler behavior and record the cost.

Sequential fallback is allowed only when:

- the remaining batch is small enough that parallelism would not materially
  affect completion before the deadline; or
- parallel scheduling itself is the blocker and the demo can still reach a
  useful terminal state sequentially; or
- it is already checkpoint mode and starting new infrastructure work would
  increase risk.

Any fallback must be recorded in the preregistration or checkpoint/final
closeout with the expected wall-clock impact.

## Context To Read First

Read:

- `AGENTS.md`
- `PROCESS.md`
- `experiments/agent_tuning_demo/results/task_generator_evolution_closeout.json`
- `experiments/agent_tuning_demo/reports/task_generator_evolution_closeout_zh.md`
- `experiments/agent_tuning_demo/results/sphinx_task_generator_certified_manifest.json`
- `experiments/agent_tuning_demo/results/mypy_task_generator_certified_manifest.json`
- `experiments/agent_tuning_demo/results/sphinx_task_generator_rolling_origin_windows.json`
- `experiments/agent_tuning_demo/results/mypy_task_generator_rolling_origin_windows.json`
- prior Phase 1/2 Agent Tuning reports:
  - `experiments/agent_tuning_demo/reports/phase1_feasibility_closeout_zh.md`
  - `experiments/agent_tuning_demo/reports/phase2_closeout_zh.md`
  - `experiments/agent_tuning_demo/reports/phase2b_closeout_zh.md`
- current tools/tests under `experiments/agent_tuning_demo/`

## Mainline Story To Preserve

Do not drift into a general tuner framework or a new product architecture.

The demo story is:

1. Barcarolle can generate enough repo-specific certified tasks for real target
   repositories.
2. It can freeze rolling-origin windows without future leakage.
3. It can evaluate a real workspace Agent before tuning.
4. It can turn Selection/history feedback into a deployable repo-local artifact.
5. It can validate the artifact on future holdout tasks and report cost,
   pass-rate, failure labels, and uncertainty honestly.

Keep the explanation understandable. Avoid excessive internal terms in the
final report.

## Package 1: Preflight And Preregistration

Freeze a preregistration artifact before running new paid evaluation cells:

```text
experiments/agent_tuning_demo/results/agent_tuning_demo_preregistration.json
experiments/agent_tuning_demo/reports/agent_tuning_demo_preregistration_zh.md
```

It must define:

- selected target repository or repositories;
- selected rolling-origin window(s);
- baseline Agent(s);
- tuned Agent surface;
- artifact type and injection path;
- train/dev/selection inputs available to tuner;
- future holdout inputs withheld from tuner;
- score-join rules;
- invalid/unscoreable policy;
- timeout settings;
- paid-cell scheduler, maximum concurrency, resume policy, and sequential
  fallback rule if any;
- retry/repeat policy;
- cost accounting rules;
- success criteria;
- stop conditions;
- checkpoint deadline policy.

Choose a minimal protocol that can finish by the deadline while still telling
the story. A reasonable default is:

- primary repository: choose `sphinx` or `mypy` based on expected verifier speed,
  task clarity, and tuning surface relevance;
- secondary repository: use if time permits;
- one or two rolling-origin windows initially, expanding only if the story needs
  more evidence;
- one baseline Agent and one tuned variant for the first paid gate;
- add a second artifact or second repo only if the first result is inconclusive.

Do not overbuild a full 2 repo x 3 windows x many artifact matrix unless the
earlier batches justify it.

## Package 2: Baseline And Feedback Collection

Run or reuse baseline Agent evaluations needed by the frozen protocol.

Before running new paid baseline cells, complete the Paid-Cell Parallelization
Gate. Use the audited or newly implemented bounded-concurrency runner for any
batch where parallelism materially improves the chance of finishing before the
deadline.

For each chosen window:

- run baseline on selected/history benchmark tasks needed to generate feedback;
- run baseline on future holdout tasks only after the selected benchmark and
  tuning inputs are frozen;
- record verifier outcomes, failure labels, cost, latency, and scoreable status;
- keep raw prompts/completions/transcripts/workspaces under ignored paths only;
- commit only sanitized summaries, manifests, and digests.

Create:

- `experiments/agent_tuning_demo/results/agent_tuning_demo_baseline_matrix.csv`
- `experiments/agent_tuning_demo/results/agent_tuning_demo_baseline_summary.json`
- `experiments/agent_tuning_demo/reports/agent_tuning_demo_baseline_summary_zh.md`

If baseline cells expose infrastructure failures, fix the adapter/profile when
bounded and rerun the affected cells. Do not let a repairable timeout,
endpoint-proof issue, or usage-parsing issue become the final answer before
`07:00`.

## Package 3: Feedback Export And Artifact Proposal

Generate tuning feedback only from allowed historical/selection tasks.

The feedback should be concrete enough for a tuner/proposer to act on:

- recurring failure labels;
- task families/modules where baseline fails;
- public-test behavior if observed;
- patch/no-patch patterns;
- cost/latency issues;
- narrow behavioral instructions that can be deployed as an Agent artifact.

Create:

- `experiments/agent_tuning_demo/results/agent_tuning_demo_feedback_export.jsonl`
- `experiments/agent_tuning_demo/reports/agent_tuning_demo_feedback_export_zh.md`

Then propose one or more artifacts:

- Use the most practical proposer available. GEPA-style or Phoenix-style
  proposer is acceptable, but a simpler local/LLM proposer is also acceptable if
  it better fits the deadline.
- If using an LLM proposer or reflection step, record costs in the ledger.
- Freeze each candidate artifact by hash before evaluation.

Create:

- `experiments/agent_tuning_demo/results/agent_tuning_demo_candidate_artifacts.json`
- `experiments/agent_tuning_demo/reports/agent_tuning_demo_candidate_artifacts_zh.md`

## Package 4: Dev Selection Evaluation And Iteration

Evaluate candidate artifacts on allowed selected/history tasks.

Iterate autonomously:

```text
feedback -> artifact -> selected/dev evaluation -> diagnose -> improve artifact
```

Continue until one of these is true:

- a candidate clears the frozen dev gate;
- no candidate improves after serious attempts and further iteration would not
  plausibly change the demo before the deadline;
- time has reached checkpoint mode.

Do not stop after the first neutral result before `07:00`. Try another artifact,
another proposer prompt, a narrower failure-specific artifact, a simpler
rule-based artifact, or a different primary repo/window when justified.

Create:

- `experiments/agent_tuning_demo/results/agent_tuning_demo_dev_eval.csv`
- `experiments/agent_tuning_demo/results/agent_tuning_demo_dev_eval_summary.json`
- `experiments/agent_tuning_demo/reports/agent_tuning_demo_dev_eval_zh.md`

## Package 5: Frozen Future Holdout Validation

After choosing the artifact from dev/selection evidence, validate it on future
holdout tasks.

Requirements:

- future holdout task IDs/outcomes were not tuner inputs;
- baseline and tuned runs use the same Agent/model/harness/runtime policy except
  for the frozen artifact;
- verifier policy and invalid-cell policy match preregistration;
- all costs are in the ledger;
- failures are classified, not just counted.

Create:

- `experiments/agent_tuning_demo/results/agent_tuning_demo_future_holdout.csv`
- `experiments/agent_tuning_demo/results/agent_tuning_demo_future_holdout_summary.json`
- `experiments/agent_tuning_demo/reports/agent_tuning_demo_future_holdout_zh.md`

If the artifact improves, preserve the result and continue only if more evidence
is necessary for the story. If it is neutral or negative, do not immediately
stop before `07:00`: diagnose whether a second artifact, a narrower feedback
slice, or a different prepared repo/window could produce a clearer demo.

## Package 6: Final Story Or Deadline Checkpoint

If the demo is complete, write:

```text
experiments/agent_tuning_demo/results/agent_tuning_demo_final_closeout.json
experiments/agent_tuning_demo/reports/agent_tuning_demo_final_report_zh.md
experiments/agent_tuning_demo/reports/agent_tuning_demo_final_closeout_zh.md
```

The final report must be reader-facing Chinese and low-jargon. It should cover:

- the problem;
- the target repositories and task supply;
- the frozen protocol;
- the baseline result;
- the feedback and artifact;
- the before/after future holdout result;
- costs in USD;
- what claim is supported;
- what claim is not supported;
- next step if the project continues.

If the hard deadline arrives before completion, write:

```text
experiments/agent_tuning_demo/results/agent_tuning_demo_deadline_checkpoint.json
experiments/agent_tuning_demo/reports/agent_tuning_demo_deadline_checkpoint_zh.md
```

The checkpoint must include:

- current terminal state;
- what completed;
- what is running or intentionally stopped;
- cost ledger summary;
- exact next command or next package;
- blockers and attempted repairs;
- uncommitted/ignored raw artifact locations if any.

## PROCESS Update

Update `PROCESS.md` with a short current-state entry:

- terminal state;
- whether demo completed or deadline checkpointed;
- target repo(s);
- artifact/tuner path;
- future holdout result;
- total estimated/observed cost;
- canonical final report/checkpoint links;
- next action.

Do not paste long experiment tables into `PROCESS.md`.

## Tests And Hygiene

Run focused tests for touched code. At minimum:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
```

If workspace adapter code is touched, also run the relevant phase0 adapter
tests.

Always run:

```text
git diff --check
git ls-files | rg '(\.venv|\.pytest_cache|\.DS_Store|transcript|completion|prompt|workspace|raw|external|clone|outputs/)'
```

Explain historical path-name hits. Do not commit raw workspaces, cloned
repositories, caches, full raw logs, prompts, completions, transcripts, or
secrets.

## Commit Discipline

Make focused commits after each completed package or tightly related batch:

- preregistration;
- baseline/feedback;
- artifact proposal;
- dev iteration;
- future holdout;
- final report or deadline checkpoint;
- PROCESS update if not already included.

Do not leave the worktree dirty at terminal state unless the final checkpoint
explicitly records why.
