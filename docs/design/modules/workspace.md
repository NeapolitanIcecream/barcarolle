# Module Design: Workspace

Status: current behavior, 2026-07-22.

## Responsibility

Create fresh solver and verifier workspaces, invoke the configured Agent,
capture the diff, replay it, and run the Check through the Verification module.

Workspace does not implement the Agent edit loop.

The default execution model assumes a cooperative Agent. Workspaces keep
solver-visible and verifier-only material separate; they are not a host
security boundary. Filesystem, network, process, CPU, and memory limits may be
supplied by an execution adapter when the deployment requires them.
The built-in path makes no adversarial containment or resource-isolation
claim.

## Inputs

- `TaskRecord`;
- `CheckRecord`;
- `AgentRecord`;
- `WorkspaceConfig`;
- `RuntimeConfig`.
- `WorkspaceRunContext` carrying the Repository, Agent harness, and Check
  material bindings for one certification or execution run.

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

`WorkspaceRunContext` is an immutable value, not a service or registry. Binding
functions return a new context. Repeating an identical binding is idempotent;
binding a different value under the same semantic key in one context fails.
Independent runs may use independent contexts without shared execution state.
The locked process-global owned-workspace table tracks only cleanup ownership.

## Functions

### bind_repository_source

Input:

- `context: WorkspaceRunContext`
- `workspace_config: WorkspaceConfig`
- `repository_path: Path`

Output:

- `WorkspaceRunContext`

Effect:

- Validates WorkspaceConfig before it can key the immutable run context.
- Binds a local Git checkout to
  `workspace_config.repository_checkout_config_digest` in a returned context.
  Runner performs this binding before task certification or Agent execution.
- A missing binding raises `RepositorySourceNotBoundError`; checkout failures
  remain internal but map to `repository_checkout_failed`. Higher layers use
  these types, not substrings from Git or filesystem messages.

### bind_agent_harness

Input:

- `context: WorkspaceRunContext`
- `agent: AgentRecord`
- `command: Sequence[str]`
- `execution_mode: "offline" | "openai_paid" | None`
- `endpoint_harness_paths: Sequence[Path]`

Output:

- `WorkspaceRunContext`

Effect:

- Binds a harness command in a returned context whose argv digest matches the
  valid Agent record. Offline mode requires the literal `offline` network-policy
  value. Paid mode requires
  declared endpoint-enforcing harness files, direct command linkage to at
  least one such file, and content digests that match the Agent's canonical
  endpoint proof.

### preflight_run_bindings

Input:

- `context: WorkspaceRunContext`;
- complete `Sequence[tuple[TaskRecord, CheckRecord, AgentRecord]]` plan;
- `WorkspaceConfig`;
- `RuntimeConfig`.

Output:

- `None`.

Effect:

- Validates the complete WorkspaceConfig and RuntimeConfig even for an empty
  plan, so config validity does not depend on whether cache resolution found a
  cell to execute.
- Fails before workspace creation when the repository, Task/Check relation,
  Check timeout, hidden material, exact Check command, Agent model identity,
  harness command/content, or paid endpoint proof is invalid. Paid execution
  with an unresolved model alias must occur inside its declared campaign
  window. Paid mode
  accepts only `OPENAI_BASE_URL` and `OPENAI_API_KEY`, sourcing `~/.zshrc` when
  either is absent from the current environment. It exposes neither the key nor
  raw endpoint URL in evidence or errors.
- Validates every Task/Check/Agent relation in the complete plan, then validates
  immutable Check bindings and full Agent-record bindings once per unique
  identity. This batch deduplication does not remove the per-cell rechecks before
  workspace creation and immediately before Agent invocation.

### bind_check_material

Input:

- `context: WorkspaceRunContext`
- `check: CheckRecord`
- `check_command: Sequence[str]`
- `hidden_material_source: Path`
- optional verifier-workspace destination under `.barcarolle`
- optional structured `check_manifest`

Output:

- `WorkspaceRunContext`

Effect:

- Verifies the Check manifest and hidden-material digests, then binds the
  material in a returned context for verifier preparation. Without an explicit
  manifest, the exact command remains the manifest. Adapters may instead
  provide a structured manifest so machine-local executable and output paths do
  not become Check identity. The exact bound command is still digested and
  rechecked before execution. Runner performs this binding before
  certification.

### create_solver_workspace

Input:

- `task: TaskRecord`
- `workspace_config: WorkspaceConfig`
- `context: WorkspaceRunContext`

Output:

- `WorkspaceRef`

Effect:

- Fetches only the task base commit and its reachable ancestors into a detached
  checkout. Base history remains available for `git log` and `git blame`, while
  later commits, source remotes, and the transient fetch pointer are absent.
- Writes only solver-visible task material. The machine-readable file names
  the task text file and optional refs; internal Task, source, Check, and digest
  metadata remains in Barcarolle records rather than the Agent workspace.
- Writes the exact `TaskRecord.task_text` into `.barcarolle/TASK.md`, so the
  instruction can be replayed from the frozen Task record.
- Lists `solver_material_refs` as repository-relative supporting-file paths; it
  does not copy or inline their contents. Every resolved path must remain
  inside the checkout. A symlink is allowed when its resolved target also stays
  inside that checkout.

### invoke_agent

Input:

- `solver_workspace: WorkspaceRef`
- `task: TaskRecord`
- `agent: AgentRecord`
- `runtime_config: RuntimeConfig`
- `context: WorkspaceRunContext`

Output:

- `AgentRunOutcome`

Effect:

- Revalidates the bound harness, model-resolution scope, and paid endpoint
  proof immediately before execution, then calls the Agent harness and captures terminal status,
  monotonic duration, usage, bounded stdout/stderr excerpts, and full-stream
  output digests. Normalized records store only digests and usage; configured
  ignored artifacts may retain the bounded excerpts.
- The shared bounded subprocess path validates its finite positive timeout,
  positive integer capture bound, and finite nonnegative termination grace
  before process start.
- On POSIX, owns a process group and escalates timeout or pipe-cleanup failures
  from TERM to KILL. A containment failure is benchmark-owned rather than an
  ordinary Agent outcome.
- Reads optional harness-reported usage from `.barcarolle/usage.json`. The file
  must be a JSON object with finite, nonnegative numeric values. Missing usage
  and malformed usage remain an empty mapping so telemetry cannot change the
  task outcome; total cost is then unknown.

### capture_diff

Input:

- `solver_workspace: WorkspaceRef`

Output:

- `CapturedDiff`

Effect:

- Captures a replayable final diff against the task base commit, including
  committed, staged, unstaged, and untracked Agent edits.
- Excludes Barcarolle's reserved `.barcarolle` material from the patch.
- Excludes generated Python `.pytest_cache` and `__pycache__` files; these are
  runtime byproducts rather than Agent edits to replay.

### create_verifier_workspace

Input:

- `task: TaskRecord`
- `workspace_config: WorkspaceConfig`
- `context: WorkspaceRunContext`

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
- `context: WorkspaceRunContext`

Output:

- `CheckOutcome`

Effect:

- Delegates verification preparation and check execution to the Verification
  module. Workspace bindings accept hidden-material destinations only under
  the reserved `.barcarolle` namespace; preparation and launch failures are
  returned as invalid outcomes rather than escaping as exceptions.
- Preserves the structured failure label supplied by verifier preparation.
  Unexpected setup failures use the generic `verifier_preparation_failed`
  label; message wording is diagnostic only.

### run_agent_on_task

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `context: WorkspaceRunContext`

Output:

- `WorkspaceRunRecord`

Effect:

- Orchestrates solver workspace, Agent invocation, diff capture, verifier
  workspace, diff replay, and Check execution.
- Persists monotonic `solver_checkout_seconds`, `verifier_checkout_seconds`,
  `diff_replay_seconds`, `agent_seconds`, and `verification_seconds` inside the
  existing latency mapping. `workspace_seconds` covers the high-level run up to
  record construction; it excludes best-effort artifact preservation and the
  separately measured cleanup phase.
- Removes solver and verifier workspaces before returning, after any configured
  summaries or diffs have been preserved. A cleanup failure emits a bounded
  runtime warning without replacing an already completed run record. The
  attempted removal duration is persisted as `cleanup_seconds` even on that
  warning path.
- Classifies a passing Check on an empty diff as benchmark-invalid
  (`baseline_check_passed_without_diff`). Post-Agent diff-capture failures,
  including damaged Git metadata or config, are Agent-invalid
  (`agent_workspace_corrupted`).
- Attributes an unapplicable captured patch (`replay_status=failed`) to the
  Agent, while replay launch or missing-workspace infrastructure failures
  (`replay_status=invalid`) remain benchmark-owned.
- Attributes a post-diff Check launch failure or configured invalid exit to the
  Agent only when replay changed a workspace-relative path named by the Check
  command, including an interpreter-launched script. External and unchanged
  workspace Check failures remain benchmark-owned.

### run_agent_on_task_with_artifacts

`WorkspaceArtifactConfig` always emits relative refs below `output_root`; path
mode is not configurable. Its stdout/stderr and diff retention controls must be
exact booleans, and workspace-summary modes must be `never`, `on_failure`, or
`always`. These checks run when the config is constructed.

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `context: WorkspaceRunContext`
- `artifact_config: WorkspaceArtifactConfig | None`

Output:

- `WorkspaceRunResult`

Effect:

- Runs the same benchmark boundary as `run_agent_on_task`.
- Rejects invalid static artifact configuration before invoking the Agent.
- When configured, preserves final diff, Agent stdout/stderr, and optional
  workspace summaries under an output root.
- Removes the live solver and verifier workspaces on success, normalized
  failure, or artifact-preservation error.
- If artifact persistence fails after execution, emits a bounded runtime
  warning and returns the completed `run` with `artifacts=null`.
- Returns artifact refs relative to the output root.
- Marks verifier workspace summaries as private artifacts.

## Design Consistency Check

- Keeps Agent execution outside Barcarolle.
- Separates solving from verification.
- Provides only solver-visible material before diff capture.
- Produces data for Result storage without storing full Agent logs in normalized
  records.
