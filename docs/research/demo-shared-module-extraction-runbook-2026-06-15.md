# Demo Shared Module Extraction Runbook

Date: 2026-06-15

## Goal

Decouple the Agent Tuning Demo from the live Agent Selection Demo implementation
and result files.

The immediate requirement is operational isolation: another session may add or
change Agent Selection Demo results, and those changes must not silently alter
the current Agent Tuning Demo behavior, reports, or reproducibility.

This runbook should extract small shared helpers where useful, but it should not
turn into a broad framework rewrite.

## Desired End State

After this run:

- `experiments/agent_tuning_demo/tools/` no longer imports
  `experiments/agent_selection_demo/tools/agent_selection_demo.py`.
- Agent Tuning Demo code no longer reads live Selection Demo result files by
  default.
- Any Selection-derived input that the Tuning Demo still needs is copied,
  frozen, or explicitly referenced through a Tuning-owned snapshot/manifest
  under `experiments/agent_tuning_demo/`.
- Future changes to `experiments/agent_selection_demo/results/` do not change
  Agent Tuning Demo outputs unless a later runbook deliberately refreshes the
  Tuning snapshot.
- Shared utilities live in a neutral, low-abstraction location and are tested.

## Boundary

This is a no-paid refactor.

Do not run:

- paid Agent cells;
- paid LLM calls;
- paid tuner/proposer calls;
- new Agent Selection or Agent Tuning experiments;
- result-regeneration commands that would reinterpret old paid data.

Do not edit live Agent Selection Demo result/report files:

- `experiments/agent_selection_demo/results/`
- `experiments/agent_selection_demo/reports/`

Avoid editing Agent Selection Demo code while a parallel session may be updating
it. If a clean extraction can be done without touching
`experiments/agent_selection_demo/tools/agent_selection_demo.py`, prefer that.
It is acceptable for Selection Demo code to keep its current helpers for now.
The main blocker to remove is Tuning Demo's dependency on Selection Demo.

If a true shared helper must eventually be adopted by Selection Demo too, record
that as a follow-up rather than forcing a risky concurrent edit.

## Context To Read First

Read:

- `AGENTS.md`
- `PROCESS.md`
- `experiments/agent_tuning_demo/tools/phase2_artifact_tuning.py`
- `experiments/agent_tuning_demo/tools/phase2b_rolling_origin_tuning.py`
- `experiments/agent_selection_demo/tools/agent_selection_demo.py`, read-only,
  only to identify copied helper behavior
- current Agent Tuning tests under `experiments/agent_tuning_demo/tests/`

Also inspect the latest target-repo selection reports only as context:

- `experiments/agent_tuning_demo/reports/large_repo_target_selection_gate_zh.md`
- `experiments/agent_tuning_demo/results/large_repo_target_selection_gate.json`

## Extraction Strategy

Prefer a small neutral module such as:

```text
experiments/demo_common/
```

Keep modules narrow and boring. Good candidates:

- JSON/CSV read/write helpers if duplicated;
- cost usage normalization;
- cost observation metadata;
- failure-category mapping;
- candidate/config lookup helpers that are not tied to boltons;
- task package dataclasses or lightweight package-map helpers when they can be
  made repo-generic.

Avoid:

- a generic framework;
- moving large CLI logic;
- changing old result semantics;
- adding dependencies;
- over-generalizing around future unknown demos.

If direct extraction from `agent_selection_demo.py` would require major edits,
copy the stable helper behavior into `experiments/demo_common/` with tests and
leave the Selection Demo untouched. This is acceptable because the immediate
purpose is to stabilize Tuning Demo.

## Freeze Tuning Inputs

Inventory all active references from Tuning Demo code to Selection Demo paths.
At minimum check for:

- imports of `agent_selection_demo`;
- reads from `experiments/agent_selection_demo/config/`;
- reads from `experiments/agent_selection_demo/results/`;
- assumptions about boltons-specific package maps or split files.

For every live Selection path still needed by historical Tuning phases, create a
Tuning-owned snapshot or manifest. Suggested shape:

```text
experiments/agent_tuning_demo/config/selection_input_snapshot.json
experiments/agent_tuning_demo/results/selection_input_snapshot_manifest.json
```

The snapshot/manifest should record:

- source path;
- destination or embedded minimal data;
- SHA-256 digest of the source at freeze time;
- reason the input is still needed;
- phase that consumes it;
- policy that later Selection result changes do not refresh it automatically.

If a file is small and stable, copying it under `agent_tuning_demo` is fine. If a
file is larger, store only the minimal rows/fields required by the Tuning Demo,
plus source digest and schema version.

Do not copy raw prompts, raw completions, transcripts, workspaces, or secrets.

## Implementation Requirements

1. Add the neutral shared module and tests.
2. Update `phase2_artifact_tuning.py` and
   `phase2b_rolling_origin_tuning.py` so they import neutral helpers or
   Tuning-owned snapshot/config files, not `agent_selection_demo.py`.
3. Make current historical reports reproducible from frozen Tuning-owned inputs.
4. Add guard tests that fail if Tuning Demo tools reintroduce live Selection
   imports or live Selection result reads.
5. Keep CLI behavior and existing report/result paths stable unless a path
   change is necessary for isolation.
6. Update `PROCESS.md` with a short entry and links to the refactor closeout.

## Required Closeout Artifacts

Create:

- `experiments/agent_tuning_demo/reports/demo_shared_module_extraction_zh.md`
- `experiments/agent_tuning_demo/results/demo_shared_module_extraction.json`

The report must include:

- what was decoupled;
- what remains intentionally duplicated or deferred;
- which Selection paths are now frozen in Tuning-owned snapshots;
- how future Selection Demo result changes are prevented from affecting Tuning;
- tests run;
- unsupported claims.

The JSON must include:

- schema version;
- generated timestamp;
- paid calls run, expected `0`;
- list of old Tuning-to-Selection dependencies found;
- list of dependencies removed;
- list of frozen snapshot inputs and digests;
- guard-test status;
- terminal state.

## Acceptance Criteria

The run is acceptable if:

- `rg "import agent_selection_demo|from agent_selection_demo" experiments/agent_tuning_demo/tools`
  returns no active code references;
- `rg "experiments/agent_selection_demo/results|experiments/agent_selection_demo/config" experiments/agent_tuning_demo/tools`
  returns no active live-input reads, except references inside comments or
  snapshot provenance strings that tests explicitly allow;
- changing Selection Demo result files would not affect Tuning Demo behavior
  unless the Tuning snapshot is deliberately refreshed;
- Agent Tuning tests pass;
- Agent Selection tests still pass if Selection code was touched;
- no paid calls were made;
- no raw artifacts or workspaces are tracked.

## Verification

Run:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
```

If any Selection Demo code is touched, also run:

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
```

Run any new shared-module tests.

Always run:

```text
git diff --check
```

Run a touched-scope artifact hygiene scan:

```text
git ls-files experiments/demo_common experiments/agent_tuning_demo PROCESS.md | rg '(\.venv|\.pytest_cache|\.DS_Store|raw|transcript|workspace|secret|prompt|completion)' || true
```

The scan may mention historical strings in reports only if they are clearly not
tracked raw artifacts. Explain any hit.

## Commit Policy

Make focused commits:

1. dependency inventory and shared helper scaffold;
2. Tuning Demo code migration and snapshots;
3. guard tests and verification updates;
4. closeout report and PROCESS update.

Preserve unrelated untracked files and user work. Do not stage or commit the
parallel Agent Selection Demo session's changes.
