# Module Design: Workspace

Status: draft, 2026-07-14.

## Responsibility

Create fresh solver and verifier workspaces, invoke the configured Agent,
capture the diff, replay it, and run the Check through the Verification module.

Workspace does not implement the Agent edit loop.

The default execution model assumes a cooperative Agent. Workspaces keep
solver-visible and verifier-only material separate; they are not a host
security boundary. Filesystem, network, process, CPU, and memory limits may be
supplied by an execution adapter when the deployment requires them.

## Inputs

- `TaskRecord`;
- `CheckRecord`;
- `AgentRecord`;
- `WorkspaceConfig`;
- `RuntimeConfig`.

## Outputs

- captured diff digest;
- solver execution metadata;
- verifier replay metadata;
- check outcome.

## System Boundary

Input sources:

- Task Pool provides `TaskRecord` and `CheckRecord`;
- user or run config provides Agent and configs;
- Verification provides check execution.

Output consumers:

- Result Store.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Functions

### create_solver_workspace

Input:

- `task: TaskRecord`
- `workspace_config: WorkspaceConfig`

Output:

- `WorkspaceRef`

Effect:

- Creates a checkout of the target repository at the task base commit and writes only
  solver-visible task material, including a machine-readable task reference and
  a human-readable task file.

### invoke_agent

Input:

- `solver_workspace: WorkspaceRef`
- `task: TaskRecord`
- `agent: AgentRecord`
- `runtime_config: RuntimeConfig`

Output:

- `AgentRunOutcome`

Effect:

- Calls the Agent harness and captures terminal status, duration, usage, and
  safe output digests. Stdout and stderr may be retained in the in-memory
  outcome for artifact preservation, but normalized records store only digests
  and usage.
- Reads optional harness-reported usage from `.barcarolle/usage.json`. The file
  must be a JSON object with finite, nonnegative numeric values. Missing usage
  remains an empty mapping; malformed usage makes the Agent run invalid.

### capture_diff

Input:

- `solver_workspace: WorkspaceRef`

Output:

- `CapturedDiff`

Effect:

- Captures a replayable final diff against the task base commit, including
  committed, staged, unstaged, and untracked Agent edits.
- Excludes Barcarolle's reserved `.barcarolle` material from the patch.

### create_verifier_workspace

Input:

- `task: TaskRecord`
- `workspace_config: WorkspaceConfig`

Output:

- `WorkspaceRef`

Effect:

- Creates a fresh repository checkout for verification.

### cleanup_workspace

Input:

- `workspace: WorkspaceRef`

Output:

- `None`

Effect:

- Removes a workspace returned by a low-level create function. High-level run
  functions call this automatically; direct callers own cleanup.
- Rejects workspace paths not created by this Workspace owner.

### apply_diff

Input:

- `verifier_workspace: WorkspaceRef`
- `diff: CapturedDiff`

Output:

- `DiffReplayOutcome`

Effect:

- Applies the captured diff in the verifier workspace and reports replay
  success, patch failure, or replay-infrastructure invalidity as distinct
  states.

### verify_agent_diff

Input:

- `verifier_workspace: WorkspaceRef`
- `check: CheckRecord`
- `runtime_config: RuntimeConfig`

Output:

- `CheckOutcome`

Effect:

- Delegates verification preparation and check execution to the Verification
  module. Workspace bindings accept hidden-material destinations only under
  the reserved `.barcarolle` namespace; preparation and launch failures are
  returned as invalid outcomes rather than escaping as exceptions.

### run_agent_on_task

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`

Output:

- `WorkspaceRunRecord`

Effect:

- Orchestrates solver workspace, Agent invocation, diff capture, verifier
  workspace, diff replay, and Check execution.
- Removes solver and verifier workspaces before returning, after any configured
  summaries or diffs have been preserved. Cleanup failures are terminal errors.
- Classifies a passing Check on an empty diff as benchmark-invalid
  (`baseline_check_passed_without_diff`). Post-Agent diff-capture failures,
  including damaged Git metadata or config, are Agent-invalid
  (`agent_workspace_corrupted`).
- Attributes an unapplicable captured patch (`replay_status=failed`) to the
  Agent, while replay launch or missing-workspace infrastructure failures
  (`replay_status=invalid`) remain benchmark-owned.
- Classifies failures by whether they arise before or after the Agent diff is
  applied, preserving benchmark-owned and Agent-owned failure labels.

### run_agent_on_task_with_artifacts

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `artifact_config: WorkspaceArtifactConfig | None`

Output:

- `WorkspaceRunResult`

Effect:

- Runs the same benchmark boundary as `run_agent_on_task`.
- When configured, preserves final diff, Agent stdout/stderr, and optional
  workspace summaries under an output root.
- Removes the live solver and verifier workspaces on success, normalized
  failure, or artifact-preservation error.
- Returns artifact refs relative to the output root.
- Marks verifier workspace summaries as private artifacts.

## Design Consistency Check

- Keeps Agent execution outside Barcarolle.
- Separates solving from verification.
- Provides only solver-visible material before diff capture.
- Produces data for Result storage without storing full Agent logs in normalized
  records.
