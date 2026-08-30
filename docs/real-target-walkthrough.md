# Real Target Walkthrough

This walkthrough shows the path from `examples/minimal` to a production-shaped
run against a target repository. Barcarolle stays harness-neutral: your agent
harness can be a shell command, a script, or another tool that edits a real
worktree.

This walkthrough covers the current static `Task Pool` and `Selection` modules.
It does not implement the active research program's built-in task generation,
parent links between agent versions, evaluator-feedback records, error curves by
optimization budget, adversarial stress testing of evaluators and metrics, or
agent–evaluator coevolution. See
[`research-program.md`](research-program.md) for that target and
[`implementation-status.md`](implementation-status.md) for the gap.

## 1. Bind Repository Identity To A Local Checkout

Choose a stable `repository_id`, a local Git checkout, and the exact base
commits that tasks may use. The ID is stored in records. The local path is a
runtime input and must not become record identity.

The solver workspace starts at the task base commit. Barcarolle writes
`.barcarolle/solver-visible-task.json` and `.barcarolle/TASK.md` in that
workspace so the agent harness can read the task without verifier-only
material.

## 2. Prepare Candidates And Check Inputs

Each `TaskCandidate` carries direct `task_text` and optional
`solver_material_refs`. The refs name supporting files already in the target
checkout. Workspace lists those paths in `TASK.md`; it does not inline their
contents. A ref may use an internal symlink, but its resolved target must remain
inside the checkout.

`dependency_cluster_id` and `sampling_stratum` may be empty. The former is only
for dependence-aware origin blocking; the latter may support visible sampling
or coverage features. Do not replace either with a default label.
`resource_limits` may also be empty: `RuntimeConfig.timeout_seconds` is the
default Check timeout, and a per-Check timeout only narrows it.

Prepare one check command, hidden-material path, and trusted reference patch for
every candidate. Private check bundles belong only to
`CheckRecord.hidden_check_bundle_digest` and verifier setup.

Before freezing the pool, run execution-based task validation. The task check
must fail at the base commit and pass after applying its reference patch.
When `repeat_count` is greater than one, repeat the whole fresh-workspace
base-fail/patched-pass pair. This certifies one
aggregate Check transition. A SWE-bench adapter that needs separate
`FAIL_TO_PASS` and `PASS_TO_PASS` evidence must execute and distinguish both in
its Check wrapper.

The hidden check bundle is injected only in the verifier workspace. It should
not appear in task text, solver material refs, solver artifacts, prompts, or
checked-in records.

## 3. Build The Task Pool Through Runner

`Runner.build_task_pool` performs the bindings before certification, freezes
the record, then writes the exact Task, Check, and sanitized certification
evidence sequences referenced by that record:

```python
from pathlib import Path

from barcarolle.runner import TaskPoolConfig, build_task_pool

task_pool = build_task_pool(
    TaskPoolConfig(
        repository_id="target-project",
        repository_path=Path("target-repo"),
        workspace_config=workspace_config,
        runtime_config=runtime_config,
        reference_patches=reference_patches,
        check_commands=check_commands,
        hidden_material_paths=hidden_material_paths,
        import_path=Path("candidates.jsonl"),
        metadata={
            "task_records_ref": "records/tasks.jsonl",
            "check_records_ref": "records/checks.jsonl",
            "certification_evidence_ref": "records/certification-evidence.jsonl",
        },
    )
)
```

The canonical digests of those exact sequences are stored on `TaskPoolRecord`.
Do not edit a referenced file in place; rebuild the pool record when its
contents change.

## 4. Use The Low-Level Binders Directly

Direct callers must preserve the same order: bind the repository, build the
Check, bind its command and hidden material, then certify the candidate.

```python
from pathlib import Path

from barcarolle.task_pool import build_check_candidate, certify_task_candidate
from barcarolle.workspace import bind_check_material, bind_repository_source

bind_repository_source(workspace_config, Path("target-repo"))
check = build_check_candidate(candidate)
bind_check_material(check, check_command, hidden_material_path)
certification = certify_task_candidate(
    candidate,
    certification_config,
    workspace_config,
    runtime_config,
    reference_patch,
)
```

`freeze_task_pool` only constructs the record. A direct caller must write the
accepted Task records, accepted Check records, and
`certification_evidence_records(...)` to the refs stored on that record and
verify their canonical digests. Runner is the shorter path.

## 5. Bind The Agent Harness

Bind each agent harness command to its `AgentRecord`:

```python
from barcarolle.workspace import bind_agent_harness

bind_agent_harness(agent, ("./run-agent.sh",))
```

The binder validates the command argv. When results will be reused, change the
agent identity whenever the harness or its behavior-changing configuration
changes. The harness adapter decides how to compute that identity.

Record the requested model name separately from the immutable snapshot returned
by a provider. If the adapter cannot prove a snapshot, leave it null and bind
the agent to one declared campaign ID and execution window. Paid preflight
rejects missing cells outside that window; cached evidence remains readable.

For a concrete Codex CLI shell example, see
`examples/harnesses/codex-cli/`. It is one harness option; Barcarolle does not
require Codex CLI.

The command edits files in the provided solver worktree. Barcarolle captures
the final `git diff`, replays it in a fresh verifier worktree, and runs the
hidden check there.

## 6. Record Usage And Cost

The harness adapter owns usage extraction. Barcarolle accepts an adapter-provided
usage mapping and applies cost rates by matching numeric keys:

```python
from barcarolle.result_store import ScoringConfig
from barcarolle.workspace import AgentRunOutcome

outcome = AgentRunOutcome(
    terminal_status="completed",
    duration_seconds=12.4,
    usage={
        "input_tokens": 10,
        "cached_input_tokens": 4,
        "uncached_input_tokens": 6,
        "output_tokens": 2,
    },
    safe_output_digest="sha256-digest",
    failure_label=None,
)

scoring_config = ScoringConfig(
    pricing_version="agent-prices-v1",
    cost_rates={
        "cached_input_tokens": 0.0001,
        "uncached_input_tokens": 0.001,
        "output_tokens": 0.01,
    },
)
```

`scoring_config_digest` is derived from `pricing_version` and `cost_rates`; it
is not supplied by the caller.

The harness may write `.barcarolle/usage.json` in the solver workspace. The
built-in workspace runner reads this file after the command exits. The Codex
CLI helper reads only the current `turn.completed.usage` event, preserves its
numeric keys, and derives `uncached_input_tokens` as `input_tokens -
cached_input_tokens`. It does not search nested objects or translate alternate
token names. Missing or malformed usage remains unknown and does not change the
task outcome. If usage is absent, no rates are configured, or a priced key is
missing, `cost.total_cost` is `null`; reports keep that distinct from measured
zero cost.

## 7. Preserve Run Artifacts

For diagnosis, provide an ignored output root:

```python
from barcarolle.workspace import WorkspaceArtifactConfig, run_agent_on_task_with_artifacts

result = run_agent_on_task_with_artifacts(
    task,
    check,
    agent,
    workspace_config,
    runtime_config,
    WorkspaceArtifactConfig(
        output_root=Path("outputs/runs"),
        preserve_stdout_stderr=True,
        preserve_final_diff=True,
        preserve_solver_workspace_summary="on_failure",
        preserve_verifier_workspace_summary="on_failure",
    ),
)
```

The returned artifact refs are relative to `output_root`. Final diffs and
stdout/stderr stay separate from normalized `ResultRecord` data. Verifier
workspace summaries are marked private because verifier workspaces may contain
hidden check material. Invalid artifact modes fail before agent execution. If
artifact I/O fails after execution, the call emits a runtime warning and still
returns the completed run with `artifacts=None` so paid evidence can be stored.

## 8. Store Results

Use `barcarolle.result_store` to compute cache identity, build a `ResultRecord`,
and append it to a `ResultStore`. Preserve raw usage so pricing and derived cost
can be recomputed without rerunning a paid agent result. Unknown cost remains
unknown rather than becoming zero.

When the exact execution is requested under a new price table, Runner appends
a repriced Result from retained usage and binds evaluation cells to that view.
It does not rerun the agent or count the pricing view as another execution.

## 9. Build Rolling-Origin Selection

Use `barcarolle.selection` to create rolling origins, feature snapshots,
selector inputs, benchmark selections, result matrices, and metrics.

Metadata-only selector inputs can start with no pre-origin results. Keep the
empty `pre_origin_result_ids=()` and `pre_origin_result_digests=()` explicit so
the cold-start state remains auditable.

## 10. Write Reports

Use `barcarolle.reporting.write_report` for markdown and JSON reports. Artifact
paths under the report root or configured artifact root are emitted as relative
refs, with digests preserved in the report sections.

## Harness Preflight Output

Paid evidence-producing runs must use the endpoint and authentication required
by `AGENTS.md`. Stop before paid solving work if the harness cannot establish
that boundary.

Treat noninteractive terminal or display warnings as harness UX warnings when
the solving command itself succeeds, the endpoint/auth boundary is proven, and
the captured diff and verifier result are valid. Preserve preflight logs under
an ignored output root when they help diagnose a run.
