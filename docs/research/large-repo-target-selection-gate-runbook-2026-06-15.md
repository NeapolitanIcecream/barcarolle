# Large-Repo Target Selection Gate Runbook

Date: 2026-06-15

## Goal

Find the best next target repository for a stronger Agent Selection and Agent
Tuning Demo.

The target should have enough task capacity for rolling-origin evaluation while
still allowing fast, stable local evaluation. The central question is:

> Which repository is large enough to support a persuasive multi-window demo,
> but lightweight enough that verifier/replay cost does not dominate the work?

Examples such as NumPy or SciPy are only examples of the size/risk tradeoff.
They are not preferred targets by default.

## Boundary

This is a no-paid selection and feasibility run.

Do not run:

- paid Agent cells;
- paid LLM calls;
- paid tuner/proposer calls;
- Agent tuning experiments;
- full paid baseline discovery.

Allowed:

- public repository search and cloning under ignored external paths;
- no-paid setup/test smoke;
- no-paid candidate extraction;
- bounded no-paid certification or replay probes;
- targeted verifier timing probes;
- rolling-origin split simulation;
- small tooling repairs needed to make the gate repo-generic.

## Prior Context

Read first:

- `AGENTS.md`
- `PROCESS.md`
- `experiments/agent_tuning_demo/reports/target_repo_selection_gate_zh.md`
- `experiments/agent_tuning_demo/results/target_repo_selection_gate.json`
- `experiments/agent_tuning_demo/reports/boltons_capacity_final_recommendation_zh.md`
- `experiments/agent_tuning_demo/reports/phase2b_closeout_zh.md`
- current target-repo selection tooling and tests.

Treat the previous gate as evidence that small/medium library candidates often
have insufficient certified capacity. This run should deliberately explore a
larger capacity frontier.

## Search Strategy

Build a candidate pool with three tracks:

1. Baseline track:
   - `python-attrs/attrs`
   - `pallets/click`
   - `mahmoud/boltons`
   - any previous strong/near-miss candidates worth keeping.

2. Large-repo track:
   - larger Python repositories with long history and substantial tests;
   - examples may include numerical, framework, data, ORM, test, or developer
     tooling projects;
   - include NumPy/SciPy-like projects only as candidates to measure, not as
     assumptions.

3. Medium-large fast-evaluation track:
   - pure-Python or mostly-Python repositories with more capacity than
     attrs/click, but less build complexity than scientific compiled stacks.

The run must screen at least `12` new repositories beyond the old baseline
candidates, unless the report documents why fewer could be evaluated. At least
`5` new repositories should receive deeper no-paid probes when feasible. The
deep-probe set should include both:

- at least `2` large/heavy candidates;
- at least `2` medium-large fast-evaluation candidates.

Do not let one example family dominate the search.

## Core Metrics

For each screened repository, record:

- repository URL;
- local checkout status;
- history span;
- total commits scanned;
- implementation-change count;
- test-change count;
- implementation-plus-test change count;
- source-context availability;
- changed-test oracle availability;
- estimated candidate volume;
- estimated release-eligible volume;
- time-bucket distribution;
- count-feasible rolling-origin windows;
- visible setup smoke status;
- likely verifier command;
- external service / compiled-extension / database / network risk;
- expected evaluation speed class;
- reason to deep-probe or reject.

For deep-probed repositories, additionally record:

- setup/test smoke command and wall time;
- targeted verifier command and median/p95 wall time over samples when possible;
- bounded historical replay/certification sample size;
- replay/certification pass count;
- dominant failure labels;
- whether failures look repairable;
- projected certified task count after bounded repair;
- projected number of evidence-backed rolling-origin windows;
- expected paid baseline discovery cells and rough cost.

## Evaluation-Speed Standard

Do not reject large repositories only because full-suite tests are heavy. The
question is whether Barcarolle can build a fast hidden verifier for historical
tasks.

Prefer repositories where a task-level verifier can usually run targeted tests
within:

- ideal: under `60s`;
- acceptable: under `180s`;
- risky: `180s` to `600s`;
- avoid by default: over `600s`, unless capacity/story value is exceptional and
  failures are easy to isolate.

Measure targeted tests where possible. If only full-suite timing is available,
record that limitation and avoid over-penalizing the repo until a targeted probe
is attempted.

## Capacity Standard

Prefer repositories that plausibly support:

- at least `60` conservative certified/release-eligible tasks;
- preferably `90+` tasks for stronger multi-window claims;
- at least two rolling-origin windows with non-trivial dev/future sizes;
- ideally three windows or a clear path to three windows.

Raw history does not count unless it can plausibly convert into replayable,
scoreable, oracle-backed tasks.

## Decision Rules

Recommend a repository only if it has a credible path to both:

1. enough capacity for rolling-origin evaluation;
2. fast enough evaluation for practical Agent selection/tuning loops.

If a large repository has huge capacity but slow or fragile replay, mark it as
`large_but_heavy`. If a medium repository is fast but too small, mark it as
`fast_but_underpowered`. The preferred target is the best balance, not the
largest repo.

If no repository beats attrs/click as a practical next target, say so directly.
But the report must show that larger candidates were actually explored and why
they failed.

## Required Outputs

Create:

- `experiments/agent_tuning_demo/reports/large_repo_target_selection_gate_zh.md`
- `experiments/agent_tuning_demo/results/large_repo_target_selection_gate.json`
- `experiments/agent_tuning_demo/results/large_repo_target_selection_candidates.csv`

The report must include:

- executive recommendation;
- candidate table grouped by track;
- large/heavy candidate findings;
- medium-large fast-evaluation candidate findings;
- top deep-probe summaries;
- capacity vs evaluation-speed tradeoff;
- recommended target and backup;
- repositories rejected despite high capacity;
- repositories rejected despite fast evaluation;
- next no-paid prep plan;
- paid baseline discovery estimate;
- unsupported claims.

The JSON must include:

- schema version;
- generated timestamp;
- paid calls run, expected `0`;
- candidate metrics;
- deep-probe metrics;
- recommendation;
- backup recommendation;
- terminal state;
- next action.

Update `PROCESS.md` with a short entry and canonical links.

## Acceptance Criteria

The run is acceptable if:

- it screens at least `12` new repositories or explains why not;
- it deep-probes at least `5` new repositories when feasible;
- it includes both large/heavy and medium-large fast-evaluation candidates;
- it explicitly evaluates both capacity and evaluation speed;
- it does not equate repository size with readiness;
- it produces a concrete target recommendation or a clear negative result;
- it runs no paid calls;
- it leaves enough evidence to write the next target-prep runbook.

## Verification

Run relevant scoped tests. Prefer:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_task_supply_v2_generator_bakeoff.py -q
```

Add tests if repo-selection tooling changes meaningfully.

Always run:

```text
git diff --check
```

Run a touched-scope artifact hygiene scan and confirm no raw prompts, raw
completions, transcripts, solver/verifier workspaces, cloned repositories,
secrets, `.venv`, or caches are tracked.

## Commit Policy

Make focused commits after meaningful phases:

- candidate discovery/screening;
- deep-probe tooling or data;
- final recommendation;
- PROCESS update.

Preserve unrelated untracked files and user work.
