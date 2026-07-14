# Real Target Walkthrough

This walkthrough shows the path from `examples/minimal` to a production-shaped
run against a target repository. Barcarolle stays harness-neutral: your Agent
harness can be a shell command, a script, or another tool that edits a real
worktree.

## 1. Lock The Target Repository

Choose the target repository and record the exact base commits that tasks may
use. Each `TaskRecord` should bind to a `repository_id`, `base_commit`,
solver-visible material refs, and one or more linked checks.

The solver workspace starts at the task base commit. Barcarolle writes
`.barcarolle/solver-visible-task.json` and `.barcarolle/TASK.md` in that
workspace so the Agent harness can read the task without verifier-only
material.

## 2. Create Task And Check Records

Use `barcarolle.task_pool` to freeze accepted `TaskRecord` and `CheckRecord`
records. Keep public task material in `TaskRecord.solver_material_refs`.
Private check bundles belong only to `CheckRecord.hidden_check_bundle_digest`
and verifier setup.

Before freezing the pool, run execution-based task validation. The task check
must fail at the base commit and, when a reference patch is available, pass
after applying it. Repeat the check when repeatability needs evidence. For
SWE-bench data, retain the standard `FAIL_TO_PASS` and `PASS_TO_PASS` labels.

The hidden check bundle is injected only in the verifier workspace. It should
not appear in solver material refs, solver artifacts, prompts, or checked-in
records.

## 3. Configure Workspaces

Bind the repository source to a `WorkspaceConfig`:

```python
from pathlib import Path

from barcarolle.workspace import bind_repository_source

bind_repository_source(workspace_config, Path("target-repo"))
```

Bind each Agent harness command to its `AgentRecord`:

```python
from barcarolle.workspace import bind_agent_harness

bind_agent_harness(agent, ("./run-agent.sh",))
```

The binder validates the command argv. When results will be reused, change the
Agent identity whenever the harness or its behavior-changing configuration
changes. The harness adapter decides how to compute that identity.

For a concrete Codex CLI shell example, see
`examples/harnesses/codex-cli/`. It is one harness option; Barcarolle does not
require Codex CLI.

The command edits files in the provided solver worktree. Barcarolle captures
the final `git diff`, replays it in a fresh verifier worktree, and runs the
hidden check there.

## 4. Record Usage And Cost

The harness adapter owns usage extraction. Barcarolle accepts an adapter-provided
usage mapping and applies cost rates by matching numeric keys:

```python
from barcarolle.result_store import ScoringConfig
from barcarolle.workspace import AgentRunOutcome

outcome = AgentRunOutcome(
    terminal_status="completed",
    duration_seconds=12.4,
    usage={"input_tokens": 10, "output_tokens": 2},
    safe_output_digest="sha256-digest",
    failure_label=None,
)

scoring_config = ScoringConfig(
    scoring_config_digest="scoring-v1",
    pricing_version="agent-prices-v1",
    usage_coverage="reported",
    cost_rates={"input_tokens": 0.001, "output_tokens": 0.01},
)
```

The built-in shell workspace path does not yet parse a harness result envelope,
so it produces an empty usage mapping. Use `usage_coverage="unknown"` or
`"unreported"` for that path. A custom adapter may use `"reported"` only when
it supplies at least one finite, non-negative numeric usage value. Reports count
unknown usage separately from measured zero-cost results.

## 5. Preserve Run Artifacts

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
hidden check material.

## 6. Store Results

Use `barcarolle.result_store` to compute cache identity, build a `ResultRecord`,
and append it to a `ResultStore`. Preserve raw usage so pricing and derived cost
can be recomputed without rerunning a paid Agent result. Unknown cost remains
unknown rather than becoming zero.

## 7. Build Rolling-Origin Selection

Use `barcarolle.selection` to create rolling origins, feature snapshots,
selector inputs, benchmark selections, result matrices, and metrics.

Metadata-only selector inputs can start with no pre-origin results. Keep the
empty `pre_origin_result_ids=()` and `pre_origin_result_digests=()` explicit so
the cold-start state remains auditable.

## 8. Write Reports

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
