# Agent Selection Demo Completion Plan 2026-06-13

Status: long-running execution plan for an autonomous Codex agent.

Primary inputs:

- `docs/research/agent-selection-demo-execution-proposal-2026-06-12.md`
- `docs/research/agent-selection-demo-alignment-note-2026-06-13.md`
- `experiments/agent_selection_demo/reports/target_repo_coding_agent_selection_demo_report_zh.md`
- `experiments/agent_selection_demo/reports/post_demo_diagnostics_zh.md`
- `experiments/agent_selection_demo/reports/top2_repeatability_check_zh.md`
- `experiments/agent_selection_demo/results/`

## Mission

Finish the Agent selection demo as a coherent, usable project artifact.

The demo is not required to prove predictive validity, rank Agents globally, or
prove that Kilo is better than Codex. It should show, with clean artifacts and a
reader-friendly story, that Barcarolle can compare complete Coding Agents on a
target repository, verify their diffs in clean workspaces, report
quality/cost/latency/failure evidence, and use fresh holdout tasks to catch an
unstable selection recommendation.

## Definition Of Done

The demo is complete when all of these are true:

- a final Chinese demo package explains the completed `mahmoud/boltons` run,
  the post-demo diagnostics, and the top-2 repeatability blocker without
  centering the story on Kilo repair;
- the package has a clear claim boundary: end-to-end target-repo Agent
  selection works; fresh holdout exposed recommendation instability;
  predictive validity and general Agent rankings remain unproven;
- demo code and reports are reproducible from committed sanitized artifacts;
- recommendation logic no longer uses incomparable estimated costs to choose a
  single production-value winner;
- adapter reliability and cost/usage limitations are documented as engineering
  follow-up, not hidden in the main claim;
- any additional paid cells, if run, satisfy the endpoint, secret-isolation,
  artifact-hygiene, and scoreability gates below;
- `PROCESS.md` points to the final demo package and records the next recommended
  work;
- scoped tests and hygiene checks pass.

## Autonomy Rules

The executing agent should keep moving without asking for clarification unless a
decision would materially change paid-call scope, public claims, or repository
architecture.

It may:

- refactor or patch the demo tooling when tests and reports show a concrete
  need;
- add focused tests for changed behavior;
- create new sanitized reports, manifests, charts, or summary tables;
- inspect ignored raw workspaces or logs locally only when needed for debugging,
  while never committing raw prompts, completions, transcripts, solver
  workspaces, verifier workspaces, cloned repos, or secrets;
- make small, focused commits after each completed work package.

It must not:

- expand the Agent matrix;
- tune prompts, tools, or model settings to improve a candidate after seeing
  results;
- introduce a learned selector;
- start a full second-repository paid matrix;
- claim predictive validity;
- claim Kilo, Codex, GPT, or Claude is generally superior;
- treat the blocked top-2 repeatability check as the whole demo result.

## Paid-call Boundary

Default: no new paid cells are required to finish the demo package.

Allowed paid work inside this plan, after all gates pass:

- up to 4 paid smoke or adapter-debug cells for `Kilo + GPT mainline`;
- one frozen top-2 holdout repeat batch, at most 20 cells, using only:
  - `Codex + GPT mainline`
  - `Kilo + GPT mainline`
  - the same 10 frozen `mahmoud/boltons` holdout tasks.

If the agent chooses the top-2 repeat batch, rerun both Agents on the same 10
tasks unless it explicitly records a cheaper recovery-mode rationale. Recovery
mode may run only the missing Kilo cells and compare them with the persisted
Codex repeat, but the report must label that comparison as asymmetric.

No second-repository paid run is approved by this plan. A clean second-repo gate
may produce a cost projection and go/no-go recommendation for the user.

## Work Package 0: Orientation And State Audit

Read `AGENTS.md`, `PROCESS.md`, the primary inputs above, and the current demo
code under `experiments/agent_selection_demo/`.

Produce or update a short internal audit note only if something has changed
since the current committed artifacts.

Acceptance:

- current branch and worktree state are recorded in closeout;
- active source of truth is the completion plan plus alignment note;
- no stale `phase`, `ACUT`, `release`, or proposal-process vocabulary is added
  to reader-facing demo materials.

## Work Package 1: Final Demo Story Package

Create a final Chinese package from the already completed first run and
diagnostics. Suggested path:

```text
experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md
```

Required content:

- one-page executive summary;
- what was tested: target repo, task source, four Agents, selection/holdout
  split;
- what the system did: run Agents, capture diffs, replay in clean verifier
  workspaces, report verified outcomes;
- main result: selection recommended Codex GPT mainline, holdout contradicted
  that recommendation, so fresh holdout is valuable;
- diagnostic result: selection quality tie, fragile cost tie-breaker, task-split
  difference, Kilo usage gap, top-2 repeatability blocker;
- product relevance: Agent selection and Agent tuning feedback can use this
  kind of evidence, but production use needs stronger gates and more data;
- clean claim boundary and next steps.

Optional but useful:

- a compact table suitable for a slide;
- simple Mermaid or markdown-friendly diagrams;
- an appendix mapping each claim to the committed artifact that supports it.

Acceptance:

- readable by someone who has not followed the full research process;
- does not require raw artifacts;
- does not present Kilo timeout as the main story;
- does not overclaim ranking, generality, or predictive validity.

## Work Package 2: Demo Tooling And Report Hygiene

Audit the demo code and committed artifacts for practical reproducibility and
low abstraction burden.

Focus areas:

- recommendation rule behavior after the cost tie-breaker guard;
- scoreable-cell accounting and failure categories;
- Kilo timeout status handling;
- usage/cost schema clarity;
- report generation inputs and outputs;
- ignored raw paths and cache hygiene.

Make small patches only where they directly improve demo correctness,
reproducibility, or closeout clarity.

Acceptance:

- scoped demo tests pass;
- no committed `__pycache__`, raw transcript, raw completion, workspace, secret,
  or cloned external repo artifacts;
- future recommendation reports can distinguish observed usage, estimated
  usage, missing usage, and real billed cost if available.

## Work Package 3: Kilo Adapter And Usage Triage

This work package is important only if the agent wants to strengthen the
top-2 repeatability story. It must not block the final demo package.

Diagnose why `Kilo + GPT mainline` produced consecutive 900-second timeouts in
the frozen holdout repeat and why Kilo usage coverage was missing.

Likely investigation areas:

- process termination and child-process cleanup;
- CLI stream draining or blocked stdout/stderr;
- machine-readable completion detection;
- timeout propagation into the result schema;
- workspace lock or test command state;
- Kilo usage output location and parser assumptions;
- whether the adapter can emit a normalized usage record without reading or
  committing raw transcripts.

Acceptance before any rerun:

- a concrete timeout hypothesis is documented;
- adapter tests cover the fixed behavior where feasible;
- a minimal smoke/gate run shows Kilo can terminate cleanly under the configured
  endpoint and secret-isolation policy;
- usage remains labeled `cost-inconclusive` unless observed or billed usage is
  actually available.

If this cannot be completed within a reasonable work session, write a blocker
section in the final package and move on.

## Work Package 4: Optional Frozen Top-2 Repeat Completion

Run this only if Work Package 3 makes Kilo reliable enough and the paid-call
boundary still fits.

Use the same frozen `mahmoud/boltons` holdout tasks from
`experiments/agent_selection_demo/results/frozen_split.json`.

Preferred execution:

- rerun both `Codex + GPT mainline` and `Kilo + GPT mainline`;
- 2 Agents x 10 tasks = 20 paid cells;
- no prompt/tool/model/timeout tuning other than infrastructure fixes required
  to make the adapter obey the original run policy.

Fallback execution:

- run only the missing Kilo cells;
- compare with the persisted Codex repeat;
- label the comparison as asymmetric and weaker.

Acceptance:

- scoreable-cell rate at least 95%;
- every scored diff is replayed in a clean verifier workspace;
- task-level stability table compares original holdout, previous repeat, and
  new repeat where available;
- conclusion is one of: stable contradiction, noisy/inconclusive, or
  infrastructure blocker;
- no global Agent ranking claim is made.

## Work Package 5: No-paid Second-repo Gate

Run this if the final demo needs a path toward generality, but do not start
second-repo paid scoring.

Candidate:

- default `python-attrs/attrs`, unless audit finds a cleaner target.

Gate questions:

- can at least 30 tasks be locally certified?
- are checkout, dependency setup, visible tests, hidden verifier replay, and
  task statements stable?
- would this repo answer a question not answered by `boltons`?
- what would the paid matrix cost?

Suggested output:

```text
experiments/agent_selection_demo/reports/second_repo_gate_zh.md
```

Acceptance:

- clear go/no-go recommendation;
- no paid second-repo cells are run;
- if go, include a concise future paid-run plan and budget estimate.

## Work Package 6: Agent Tuning Feedback Prototype

Use existing sanitized results to show how the same demo can feed Agent tuning
or configuration improvement.

Suggested output:

```text
experiments/agent_selection_demo/reports/agent_tuning_feedback_prototype_zh.md
```

Content:

- failure categories by Agent;
- task examples where a candidate repeatedly failed or flipped;
- verifier-backed feedback signals that a tuning system could consume;
- what evidence is available now versus what needs future repeated runs.

Acceptance:

- no claim that tuning has already improved an Agent;
- makes the product direction concrete enough for presentation or follow-up
  engineering.

## Work Package 7: Final Closeout

At the end, write a closeout summary in Chinese. Suggested path:

```text
experiments/agent_selection_demo/reports/demo_completion_closeout_zh.md
```

It must state:

- what was completed;
- what additional paid cells, if any, were run;
- the final demo-level claim;
- what cannot be claimed;
- remaining blockers;
- recommended next work;
- tests and hygiene checks run.

Update `PROCESS.md` with links to the final package, any new canonical
diagnostic reports, and the recommended next work.

## Required Validation

Run at minimum:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
git diff --check
git ls-files | rg '(__pycache__|\\.pyc$|raw|transcript|workspace|\\.DS_Store|\\.pytest_cache|\\.venv)'
```

The artifact scan may return false positives only if each result is documented
and justified. It must not include raw paid-call transcripts, solver/verifier
workspaces, secrets, or caches.

Run broader tests if code changes touch shared phase0 or phase1 adapter logic.

## Commit Policy

Make focused commits after each completed work package:

- story package/report changes;
- tooling fixes;
- Kilo adapter fixes;
- rerun artifacts;
- second-repo gate;
- tuning feedback prototype;
- process closeout.

Do not batch unrelated phases into one large commit.

## Stop Conditions

Stop and write a blocker report if:

- endpoint compliance cannot be proven;
- `LLM_BASE_URL` or `LLM_API_KEY` is missing after sourcing `~/.zshrc`;
- the planned model is unavailable from `/models`;
- secret isolation fails;
- hidden verifier material is visible in solver workspaces;
- scoreable-cell rate cannot meet the stated gate;
- explaining a public claim would require committing raw prompts, raw
  completions, raw transcripts, or workspaces;
- the next useful action would exceed the paid-call boundary in this plan.

When a blocker affects only a narrow follow-up claim, keep finishing the final
demo package instead of stopping the whole demo.
