# Sphinx Target Prep Runbook

Date: 2026-06-17

## Goal

Prepare `sphinx-doc/sphinx` as the next candidate target repository for the
Agent Tuning Demo, or reject it with clear evidence.

This runbook answers one decision question:

> Is Sphinx ready to become the no-paid prepared target for a stronger rolling-
> origin Agent Tuning Demo?

It does not run paid Agent cells, paid LLM calls, paid tuner calls, or an Agent
tuning experiment.

## Scope Discipline

Follow `PROCESS.md` experiment-scope discipline.

Exploration is allowed when it directly changes this decision. Do not overbuild
window policies, plotting pipelines, target-profile abstractions, verifier
machinery, or task-generator variants. Use the simplest protocol that can decide
whether Sphinx is a practical target.

The desired output is a target-prep gate, not a complete product system.

## Background

The large-repo target selection gate recommended Sphinx for no-paid target prep:

- `experiments/agent_tuning_demo/reports/large_repo_target_selection_gate_zh.md`
- `experiments/agent_tuning_demo/results/large_repo_target_selection_gate.json`

Current Sphinx signals from that gate:

- implementation-plus-test changes: `804`;
- source-linked changed-test candidates: `514`;
- projected release/certified tasks: `157`;
- count-feasible rolling-origin windows under the coarse gate: `2`;
- current targeted verifier shards passed quickly, around `0.5s` median;
- one generic historical changed-test replay failed, so version-aware verifier
  pinning is the next gate.

Treat these as capacity estimates, not certified task counts.

## Boundary

This is no-paid.

Do not run:

- paid Agent cells;
- paid LLM calls;
- paid tuner/proposer calls;
- new before/after tuning evaluations;
- paid baseline discovery;
- large-scale certification beyond the bounded no-paid wave below.

Allowed:

- clone or repair the public Sphinx checkout under ignored external paths;
- local setup and test smoke;
- no-paid target-profile/package-map work;
- bounded candidate extraction from git history;
- bounded historical replay/certification;
- simple rolling-origin split simulation;
- small code repairs that make this gate reproducible.

Do not touch Agent Selection Demo result/report files. Agent Tuning is now
decoupled from live Selection results; keep it that way.

## Context To Read First

Read:

- `AGENTS.md`
- `PROCESS.md`
- `experiments/agent_tuning_demo/reports/large_repo_target_selection_gate_zh.md`
- `experiments/agent_tuning_demo/results/large_repo_target_selection_gate.json`
- `experiments/agent_tuning_demo/reports/demo_shared_module_extraction_zh.md`
- `experiments/agent_tuning_demo/results/demo_shared_module_extraction.json`
- current target-selection tooling under `experiments/agent_tuning_demo/tools/`
- relevant shared helpers under `experiments/demo_common/`

## Package 1: Target Profile And Local Setup

Create a Sphinx target profile and package map in the Agent Tuning area. Prefer:

```text
experiments/agent_tuning_demo/config/sphinx_target_profile.json
```

The profile should record:

- `repo_id`: `sphinx`;
- repository URL;
- ignored local checkout path;
- package/import roots;
- visible smoke commands;
- candidate hidden verifier command template;
- dependency/setup policy;
- known environment risks;
- unsupported assumptions.

Run current local setup smoke on a small targeted shard. Record:

- command shape, not secrets;
- duration;
- pass/fail status;
- failure label if any;
- whether targeted verifier time is ideal, acceptable, risky, or unusable.

Do not spend time trying to make the entire Sphinx suite pass if targeted shards
are enough for this decision.

## Package 2: Version-Aware Verifier Pinning

The previous gate's main Sphinx caveat was that one historical changed-test
replay failed under a generic dependency profile. This package should determine
whether that was a fixable profile issue or a structural blocker.

Implement or document a narrow version-aware verifier policy:

- how to choose Python/dependency constraints for a historical Sphinx task;
- how to install only what is needed for targeted tests;
- how to run changed tests or narrow module shards;
- how to label failures such as no tests selected, collection failure,
  dependency mismatch, target test failure, or reference replay mismatch.

Keep this pragmatic. Do not build a general environment solver.

Run a small no-paid replay preflight, around `3-5` historical candidates across
different dates/modules. The goal is to confirm whether replay can work at all
before spending the full 20-30 sample budget.

## Package 3: Bounded Candidate Extraction

Extract a bounded Sphinx candidate pool from history.

Use existing git-history heuristics first:

- implementation and test files changed together;
- changed tests available as hidden-oracle candidates;
- public source context available when possible;
- avoid obvious docs-only, examples-only, benchmark-only, or release-only
  changes unless they are genuinely code behavior tasks.

Produce a candidate inventory with:

- task id;
- commit and parent/base commit;
- task time;
- changed implementation files;
- changed test files;
- module/family;
- public source-context reference;
- preliminary risk label;
- expected targeted verifier command.

Do not attempt to mine every possible Sphinx task. The immediate target is a
good enough pool for the certification wave and rolling-origin feasibility.

## Package 4: No-Paid Certification / Replay Wave

Run a bounded no-paid certification/replay wave of `20-30` Sphinx candidates.

The sample must cover at least two time buckets if feasible. Prefer coverage
across:

- pre-2022 / 2022-2023 / 2024+ or the nearest meaningful buckets found in the
  candidate inventory;
- different modules or task families;
- both easy-looking and non-trivial changed-test tasks.

For each candidate, record:

- whether the base workspace can be prepared;
- whether reference patch or changed tests can be reconstructed;
- whether hidden verifier injection works;
- whether base/reference behavior is meaningful;
- verifier duration;
- terminal status;
- failure label.

Required outputs:

```text
experiments/agent_tuning_demo/results/sphinx_certification_wave.csv
experiments/agent_tuning_demo/results/sphinx_certification_wave.json
experiments/agent_tuning_demo/reports/sphinx_certification_wave_zh.md
```

Success is not all-or-nothing. The key is estimating conversion and identifying
whether failures are repairable.

## Package 5: Simple Rolling-Origin Policy

Using only no-paid certified/replay evidence and candidate inventory, propose a
simple rolling-origin policy for Sphinx.

The policy must support the main story:

- predicted pass rate on selected benchmark;
- actual pass rate on later/future tasks;
- prediction error over time;
- before/after tuning effect over time, if future paid tuning is later run.

Keep the policy simple. Prefer one primary policy plus, at most, one exploratory
figure policy. Do not optimize policies just to produce a prettier graph.

Reasonable options include:

- fixed task-count windows ordered by time;
- yearly or two-year origins only if task counts remain balanced;
- overlapping diagnostic windows only if clearly labeled exploratory.

Record:

- origin dates or origin task indices;
- train/selection/dev/future task counts;
- minimum tasks per segment;
- stride;
- overlap policy;
- how MAE and tuning uplift error would be computed;
- expected paid cells per window for baseline discovery and for before/after
  tuning.

Required outputs:

```text
experiments/agent_tuning_demo/results/sphinx_rolling_origin_policy.json
experiments/agent_tuning_demo/reports/sphinx_rolling_origin_policy_zh.md
```

## Package 6: Final Gate Decision

Create the final closeout:

```text
experiments/agent_tuning_demo/reports/sphinx_target_prep_closeout_zh.md
experiments/agent_tuning_demo/results/sphinx_target_prep_closeout.json
```

The closeout must state one terminal state:

- `sphinx_ready_for_paid_baseline_preregistration`
- `sphinx_needs_bounded_repair_then_recheck`
- `sphinx_rejected_return_to_target_selection`

Use `sphinx_ready_for_paid_baseline_preregistration` only if:

- targeted verifier setup is stable enough;
- certification/replay conversion is credible;
- at least two rolling-origin windows look feasible after certification;
- expected paid cells and verifier runtime are practical;
- no artifact-hygiene or endpoint-boundary issue exists.

Use `sphinx_needs_bounded_repair_then_recheck` if the path is plausible but a
specific repair is required, such as dependency pinning or changed-test
selection.

Use `sphinx_rejected_return_to_target_selection` if replay/certification fails
for structural reasons, verifier speed is impractical, or the task pool does not
survive certification.

Update `PROCESS.md` with a short entry and canonical links.

## Required Final Report Content

The final Chinese report must include:

- concise recommendation;
- what was tested;
- certification/replay conversion;
- verifier speed summary;
- dominant failure labels;
- rolling-origin feasibility;
- expected paid baseline discovery cells;
- expected tuning before/after cells per window;
- whether Sphinx is better than attrs/click/boltons for this demo;
- what is still unsupported;
- exact next runbook recommendation.

## Verification

Run relevant tests. Prefer:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
```

If shared helpers are changed, also run tests covering `experiments/demo_common`.
If phase0 workspace/profile code is changed, run the relevant scoped phase0 or
phase1 tests.

Always run:

```text
git diff --check
```

Run a touched-scope artifact hygiene scan and explain any hit:

```text
git ls-files experiments/agent_tuning_demo experiments/demo_common experiments/phase0_headroom/target_profiles PROCESS.md | rg '(\.venv|\.pytest_cache|\.DS_Store|__pycache__|\.pyc$|raw|transcript|workspace|secret|prompt|completion)' || true
```

Do not commit cloned repositories, solver/verifier workspaces, raw prompts, raw
completions, transcripts, secrets, `.venv`, or caches.

## Commit Policy

Make focused commits:

1. target profile and setup smoke;
2. verifier pinning and preflight;
3. candidate extraction and certification wave;
4. rolling-origin policy;
5. closeout and PROCESS update.

Preserve unrelated untracked files and user work.
