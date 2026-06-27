# Module Design: Workspace

Status: draft, 2026-06-27.

## Responsibility

Create isolated solver and verifier workspaces, invoke the configured Agent,
capture the diff, replay it, and run the Check through the Checks module.

Workspace does not implement the Agent edit loop.

## Inputs

- `TaskRecord`;
- `CheckRecord`;
- `AgentRecord`;
- `WorkspacePolicy`;
- `RuntimePolicy`;
- `CheckRuntimePolicy`.

## Outputs

- captured diff digest;
- solver execution metadata;
- verifier replay metadata;
- check outcome.

## Functions

### create_solver_workspace

Input:

- `task: TaskRecord`
- `workspace_policy: WorkspacePolicy`

Output:

- `WorkspaceRef`

Effect:

- Checks out the target repository at the task base commit and writes only
  solver-visible task material.

### invoke_agent

Input:

- `solver_workspace: WorkspaceRef`
- `task: TaskRecord`
- `agent: AgentRecord`
- `runtime_policy: RuntimePolicy`

Output:

- `AgentRunOutcome`

Effect:

- Calls the Agent harness and captures terminal status, duration, usage, and
  safe output digests.

### capture_diff

Input:

- `solver_workspace: WorkspaceRef`

Output:

- `CapturedDiff`

Effect:

- Captures the final workspace diff after Agent execution.

### create_verifier_workspace

Input:

- `task: TaskRecord`
- `workspace_policy: WorkspacePolicy`

Output:

- `WorkspaceRef`

Effect:

- Creates a fresh repository checkout for verification.

### apply_diff

Input:

- `verifier_workspace: WorkspaceRef`
- `diff: CapturedDiff`

Output:

- `DiffReplayOutcome`

Effect:

- Applies the captured diff in the verifier workspace and reports replay
  success or failure.

### verify_agent_diff

Input:

- `verifier_workspace: WorkspaceRef`
- `check: CheckRecord`
- `check_runtime_policy: CheckRuntimePolicy`

Output:

- `CheckOutcome`

Effect:

- Delegates check preparation and execution to the Checks module.

### run_agent_on_task

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_policy: WorkspacePolicy`
- `runtime_policy: RuntimePolicy`
- `check_runtime_policy: CheckRuntimePolicy`

Output:

- `WorkspaceRunRecord`

Effect:

- Orchestrates solver workspace, Agent invocation, diff capture, verifier
  workspace, diff replay, and Check execution.

## Source Alignment Check

Aligned with the architecture:

- Keeps Agent execution outside Barcarolle.
- Separates solving from verification.
- Provides only solver-visible material before diff capture.
- Produces data for Result storage without exposing raw transcripts.
