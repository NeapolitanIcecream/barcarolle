# Sphinx Protocol And Manifest Freeze Runbook

Date: 2026-06-17

## Goal

Finish the two Sphinx preparation tasks that must happen before writing the
paid-baseline-preregistration runbook:

1. Correct the rolling-origin protocol so it matches the benchmark-compiler
   story.
2. Freeze a Sphinx certification-expanded task manifest that the future paid
   preregistration can reference.

This runbook does not write the paid-baseline-preregistration runbook and does
not authorize any paid execution.

## Core Correction

The next Sphinx protocol must not use a three-disjoint-segment interpretation
where `selected` is just the slice between `train` and `future`.

For each origin:

```text
history_pool_before_origin = all eligible certified tasks before the origin
selected_benchmark_from_history = tasks selected from that history pool
future_holdout_after_origin = the next time/task window after the origin
```

The benchmark compiler story is:

```text
history pool --selector/compiler--> selected benchmark
selected benchmark pass rate --predicts--> future holdout pass rate
```

Future paid runs must prevent future holdout task IDs, labels, and outcomes from
influencing the selector/compiler.

## Scope Discipline

Follow `PROCESS.md` experiment-scope discipline.

This runbook may perform focused no-paid certification expansion because an
exact task manifest can change the next decision. Do not add new selector
families, tuner variants, plotting pipelines, repository searches, or general
environment-solving machinery.

Keep the output sufficient for the next preregistration runbook, not for a full
product implementation.

## Boundary

This is no-paid.

Do not run:

- paid Agent cells;
- paid LLM calls;
- paid tuner/proposer calls;
- paid baseline discovery;
- before/after tuning experiments;
- a new target-repository search;
- the paid-baseline-preregistration runbook itself.

Allowed:

- no-paid Sphinx replay/certification expansion;
- narrow verifier-profile repair if it directly improves certification quality;
- manifest and protocol generation;
- cost/cell accounting reconciliation;
- tests and hygiene checks.

Do not touch Agent Selection Demo result/report files. Do not refresh the Agent
Tuning selection snapshot unless a blocker directly requires it.

## Context To Read First

Read:

- `AGENTS.md`
- `PROCESS.md`
- `experiments/agent_tuning_demo/reports/sphinx_target_prep_closeout_zh.md`
- `experiments/agent_tuning_demo/results/sphinx_target_prep_closeout.json`
- `experiments/agent_tuning_demo/reports/sphinx_certification_wave_zh.md`
- `experiments/agent_tuning_demo/results/sphinx_certification_wave.json`
- `experiments/agent_tuning_demo/results/sphinx_candidate_inventory.json`
- `experiments/agent_tuning_demo/results/sphinx_rolling_origin_policy.json`
- `experiments/agent_tuning_demo/config/sphinx_target_profile.json`
- Sphinx-related tools/tests under `experiments/agent_tuning_demo/`

## Package 1: Protocol Audit And V2 Schema

Audit the existing Sphinx rolling-origin policy and identify every place where
the old wording implies `train / selected / future` are three disjoint
segments.

Create a corrected protocol artifact:

```text
experiments/agent_tuning_demo/results/sphinx_rolling_origin_protocol_v2.json
experiments/agent_tuning_demo/reports/sphinx_rolling_origin_protocol_v2_zh.md
```

The protocol must define:

- `history_pool_before_origin`;
- `selected_benchmark_from_history`;
- `future_holdout_after_origin`;
- `origin_stride`;
- `selected_benchmark_size`;
- `future_holdout_size`;
- selector leakage rules;
- score-join rules at a high level;
- metric formulas:
  - pass-rate prediction error;
  - MAE across origins;
  - tuning-uplift prediction error, for later paid tuning only.

Do not choose a final selector algorithm in this runbook unless a minimal
default is needed for accounting examples. The next preregistration runbook can
freeze the selector.

## Package 2: Certification-Expanded Manifest

Use the current 180-row Sphinx candidate inventory and existing 24-row
certification wave as inputs.

Build an exact certified task manifest, not just a projection:

```text
experiments/agent_tuning_demo/results/sphinx_certification_expanded_manifest.csv
experiments/agent_tuning_demo/results/sphinx_certification_expanded_manifest.json
experiments/agent_tuning_demo/reports/sphinx_certification_expanded_manifest_zh.md
```

The manifest must include only tasks that have passed no-paid
certification/replay under the Sphinx verifier policy. Each task row should
record:

- task id;
- target commit;
- base commit;
- task time;
- time bucket;
- module/family;
- changed implementation files;
- changed test files;
- pytest entry files;
- winning verifier profile;
- verifier duration;
- source/certification provenance;
- digest or stable reference to any sanitized evidence.

Reuse existing wave results. Expand no-paid certification only as much as needed
to support the corrected rolling-origin protocol.

Target thresholds:

- Preferred: at least `100` certified Sphinx tasks, enough for three origins
  with `history_pool` sizes `40/60/80` and `future_holdout_size=20`.
- Minimum acceptable for the next decision: at least `80` certified tasks,
  enough for two origins with `history_pool` sizes `40/60`.

Stop conditions:

- stop once the preferred threshold is reached and time-bucket coverage is
  adequate;
- stop if the inventory is exhausted;
- stop if the last `30` attempted candidates have conversion below `0.30` and
  failure labels are not clearly repairable;
- stop if verifier profile repair would become a general environment solver.

If preferred or minimum thresholds are not met, complete the run with a
`needs_bounded_repair` terminal state rather than fabricating windows.

## Package 3: Corrected Window Manifest

Using the certified task manifest, create a corrected window manifest:

```text
experiments/agent_tuning_demo/results/sphinx_rolling_origin_window_manifest.json
experiments/agent_tuning_demo/reports/sphinx_rolling_origin_window_manifest_zh.md
```

Recommended default:

- task ordering: certified tasks by task time ascending, stable tie-break by task
  id;
- origins at history sizes `40`, `60`, `80` if enough certified tasks exist;
- `future_holdout_size = 20`;
- `selected_benchmark_size = 20`;
- `origin_stride = 20`;
- `history_pool_before_origin`: all certified tasks before origin;
- `future_holdout_after_origin`: next 20 certified tasks after origin;
- `selected_benchmark_from_history`: not chosen in this run unless a minimal
  example is needed; record the allowed history pool and selection size.

The manifest must list exact task IDs for each history pool and future holdout.
It must also state that future holdout IDs/outcomes are not selector inputs in
the future paid run.

If the default policy cannot be supported, choose the simplest smaller policy
and explain why. Do not invent complex window rules just to get more plotted
points.

## Package 4: Paid Cell Accounting Reconciliation

Create a clear accounting artifact:

```text
experiments/agent_tuning_demo/results/sphinx_paid_cell_accounting.json
experiments/agent_tuning_demo/reports/sphinx_paid_cell_accounting_zh.md
```

The artifact must separate:

- per-window naive cells;
- total naive cells;
- deduplicated unique task-Agent cells, when results can be reused across
  windows;
- selected-benchmark cells;
- future-holdout cells;
- later before/after tuning cells;
- what is known now versus what depends on the next preregistration selector.

Use 4 Agents for baseline discovery unless the report explicitly labels another
count as hypothetical.

Important: if a window has `20` selected benchmark tasks and `20` future holdout
tasks, then naive baseline discovery is:

```text
(20 selected + 20 future) * 4 Agents = 160 cells/window
```

Do not carry forward the old ambiguous `80 cells/window` wording unless it is
clearly labeled as selected-only or future-only accounting.

For later tuning before/after, define the formula separately. For example:

```text
(20 selected + 20 future) * 2 variants = 80 cells/window
```

or a cheaper gated plan if the next runbook will run selected first and only
run future when a dev gate passes. Label this as a future plan, not current
authorization.

## Package 5: Closeout And Process Update

Create:

```text
experiments/agent_tuning_demo/reports/sphinx_protocol_manifest_freeze_closeout_zh.md
experiments/agent_tuning_demo/results/sphinx_protocol_manifest_freeze_closeout.json
```

Terminal states:

- `sphinx_protocol_manifest_ready_for_paid_preregistration`
- `sphinx_manifest_needs_bounded_repair`
- `sphinx_protocol_blocked_revisit_target`

Use `ready` only if:

- the corrected benchmark-compiler protocol is written;
- an exact certified manifest supports at least the minimum acceptable window
  policy;
- the window manifest lists exact history/future task IDs;
- paid cell accounting is no longer ambiguous;
- tests and hygiene pass.

Update `PROCESS.md` with a concise entry and canonical links.

Do not write the paid-baseline-preregistration runbook in this execution. The
coordinating session will decide that next.

## Verification

Run:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
```

If shared helpers or phase0 profile logic change, run the relevant scoped tests.

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

1. corrected protocol schema/report;
2. certification-expanded manifest;
3. corrected window manifest;
4. paid cell accounting;
5. closeout and PROCESS update.

Preserve unrelated untracked files and user work.
