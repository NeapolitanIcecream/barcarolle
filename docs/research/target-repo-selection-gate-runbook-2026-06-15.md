# Target Repository Selection Gate Runbook

Date: 2026-06-15

## Goal

Select the next target repository for a stronger Agent Tuning Demo, with an
explicit bias toward discovering whether new repositories can participate in
the Agent-selection and Agent-tuning story.

The repository should support rolling-origin style evaluation and before/after
Agent validation better than the current `mahmoud/boltons` path. The desired
result is a concrete repository recommendation, not a tuning run. The old
repos are baselines, not the center of gravity.

## Boundary

This runbook is no-paid.

Do not run:

- paid Agent cells;
- paid LLM calls;
- paid tuner/proposer calls;
- new Agent tuning experiments;
- production-scale certification or paid baseline discovery.

Public repository cloning, local setup smoke tests, no-paid candidate extraction,
bounded replay/certification probes, and split/window simulations are allowed.
Clone external repositories only under ignored paths.

## Context To Read First

Read these files before making changes:

- `AGENTS.md`
- `PROCESS.md`
- `experiments/agent_tuning_demo/reports/boltons_capacity_final_recommendation_zh.md`
- `experiments/agent_tuning_demo/reports/boltons_capacity_repo_selection_fallback_zh.md`
- `experiments/agent_selection_demo/reports/second_repo_gate_zh.md`
- `experiments/agent_tuning_demo/reports/phase2b_closeout_zh.md`
- `experiments/phase1_compiler/reports/phase1_task_supply_v2_repo_inventory.md`
- any local tool/config files needed to understand current task extraction,
  replay, certification, and target profile mechanics.

## Candidate Pool

Always include these baseline candidates for comparison:

- `mahmoud/boltons`
- `python-attrs/attrs`
- `pallets/click`
- `pytoolz/toolz`
- `python-humanize/humanize`

Autonomously add and evaluate new Python candidates. This is a core part of the
runbook, not an optional extension. Prefer repositories with:

- substantial multi-year history;
- frequent implementation plus test changes;
- pytest or similarly reproducible local tests;
- stable dependency setup or pinning path;
- enough historical diversity to form multiple time-ordered windows;
- feasible hidden verifier construction from changed tests;
- non-trivial but not infrastructure-heavy tasks;
- tolerable local setup cost.

Do not choose a repository only because it is large. Repository size is useful
only if it converts into certified, scoreable, time-distributed benchmark tasks.

The run must include a documented new-repository exploration stage:

- screen at least `8` new Python repositories beyond the baseline candidates,
  unless local evidence shows fewer are available after applying the criteria;
- carry at least `3` new repositories into a deeper no-paid probe when feasible;
- explain why each screened-out new repository was rejected;
- compare the best new repository directly against `attrs`, `click`, and
  `boltons`.

Useful new-candidate categories include mature Python libraries, developer
tools, data/serialization libraries, testing utilities, web/service libraries,
and other repositories with frequent historical test changes. Avoid candidates
whose setup is dominated by external services, GPU dependencies, complex
multi-language builds, or integration tests that cannot be isolated locally.

## Evaluation Dimensions

For every candidate, record:

- repository URL and local checkout status;
- history size and date span;
- implementation-change count;
- test-change count;
- implementation-plus-test change count;
- source-context availability and leakage risk;
- oracle availability from changed tests;
- estimated or observed certification conversion;
- current or projected release-eligible task count;
- time-bucket distribution;
- whether at least two rolling-origin windows are count-feasible;
- whether at least two windows look evidence-backed enough for tuning;
- visible test/setup smoke result;
- verifier-environment risk;
- expected paid baseline discovery cells and rough cost;
- main blockers and repair plan.

Use existing Barcarolle tools and artifacts where practical. If a tool has
boltons-specific assumptions, either make a narrow repo-generic repair or
document the limitation and use a no-paid manual probe.

## Deeper Probe For Top Candidates

After the initial screen, choose a small top set for deeper no-paid probing.
The top set should normally include more new repositories than old baseline
repositories. If it does not, the report must explain why the new candidates
failed the gate.
For each top candidate:

1. Clone or verify the public repository under an ignored external path.
2. Run a visible setup/test smoke.
3. Run or adapt bounded candidate extraction.
4. Sample replay or certification enough to estimate conversion and environment
   risk.
5. Simulate rolling-origin windows.
6. Identify whether the repository can support:
   - a small pilot;
   - a stronger multi-window Agent Tuning Demo;
   - paid baseline discovery without substantial infrastructure repair.

If a candidate fails due to a repairable setup issue, try a bounded repair. If
the repair grows beyond the purpose of this gate, record the blocker and move to
the next candidate.

## Decision Rules

Prefer a repository that can plausibly deliver:

- at least `60` conservative release-eligible tasks, and preferably `90+`;
- at least two time-ordered windows with useful dev/future sizes;
- non-saturated baseline headroom;
- hidden verifier replay without large environment archaeology;
- clear path to paid baseline discovery;
- lower concept and infrastructure burden than continuing to stretch boltons.

`attrs` or `click` may still be recommended if they are the best practical
choice, but this is a fallback outcome. The report must explicitly distinguish:

- small second-repo pilot readiness;
- strong multi-window tuning-demo readiness.

Prefer a new repository over an old baseline when the evidence is close and the
new repository offers better story value for Agent selection or tuning:

- clearer multiple-window capacity;
- cleaner environment reproducibility;
- broader task diversity;
- better chance of non-saturated Agent differences;
- lower accumulated concept baggage from previous experiments.

Do not recommend continuing boltons unless new evidence changes the current
capacity conclusion or the report explicitly narrows the claim to a weaker
single-window story.

## Required Outputs

Create:

- `experiments/agent_tuning_demo/reports/target_repo_selection_gate_zh.md`
- `experiments/agent_tuning_demo/results/target_repo_selection_gate.json`
- any small supporting CSV/JSON tables needed for auditability.

The Chinese report must include:

- short executive recommendation;
- candidate comparison table;
- baseline candidates result;
- newly added candidates result;
- screened-out new-candidate table;
- top-candidate no-paid probe details;
- why the recommended repository beats attrs/click/boltons for the next demo;
- which repositories are not recommended and why;
- next no-paid prep plan;
- rough paid baseline discovery plan and cost range;
- exact unsupported claims.

The JSON must include:

- schema version;
- generated timestamp;
- paid cells run, expected `0`;
- paid LLM calls run, expected `0`;
- candidate list and metrics;
- top recommendation;
- backup recommendation;
- terminal state;
- next action.

Update `PROCESS.md` with a short current-decision entry and links to canonical
outputs. Do not paste large tables into `PROCESS.md`.

## Acceptance Criteria

The run is acceptable if:

- it gives a concrete primary recommendation and backup;
- it compares attrs/click/boltons against any new candidates;
- it screens a meaningful set of new repositories and deep-probes multiple new
  candidates when feasible;
- it does not rely on raw commit count alone;
- it evaluates rolling-origin window capacity;
- it evaluates certification/replay/environment risk;
- it does not run paid calls;
- it records enough evidence for a coordinator to decide the next runbook.

If no candidate is better than attrs/click/boltons, complete the run with that
negative result and a concrete fallback plan. Do not fabricate a better
candidate.

## Verification

Run the most relevant scoped tests. Prefer:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_task_supply_v2_generator_bakeoff.py -q
```

Add or run narrower tests if you change repo-selection, target-profile,
candidate-extraction, replay, or certification code.

Always run:

```text
git diff --check
```

Run a tracked-artifact hygiene scan for the touched scope and confirm that no
raw prompts, raw completions, transcripts, solver/verifier workspaces, cloned
repos, secrets, `.venv`, or caches are tracked.

## Commit Policy

Make focused commits after meaningful phases:

- context/inventory;
- candidate-screen tooling or data;
- top-candidate probes;
- final recommendation/report;
- process update.

Preserve unrelated untracked files and user work.
