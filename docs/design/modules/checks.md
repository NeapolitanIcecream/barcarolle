# Module Design: Checks

Status: draft, 2026-06-27.

## Responsibility

Define how a `Check` runs in a verifier `Workspace` and how its outcome is
normalized.

Checks do not select tasks, run Agents, or store Results.

## Inputs

- `CheckRecord`;
- verifier `WorkspaceRef`;
- applied candidate diff;
- check runtime config.

## Outputs

- `CheckOutcome` with pass, fail, or invalid;
- failure label;
- evidence summary safe to store.

## System Boundary

Input sources:

- Task Pool provides `CheckRecord`;
- Workspace provides verifier workspace and applied diff.

Output consumers:

- Workspace;
- Results;
- Reporting.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Functions

### prepare_check_material

Input:

- `check: CheckRecord`
- `verifier_workspace: WorkspaceRef`

Output:

- `WorkspaceRef`

Effect:

- Injects hidden check material only into the verifier workspace and returns
  that workspace reference.

### run_check

Input:

- `check: CheckRecord`
- `verifier_workspace: WorkspaceRef`
- `runtime_config: RuntimeConfig`

Output:

- `CheckOutcome`

Effect:

- Executes the check under bounded time and resource limits.

### normalize_check_outcome

Input:

- `raw_output: object`
- `normalization_config: CheckNormalizationConfig`

Output:

- `CheckOutcome`

Effect:

- Converts framework-specific outputs into pass, fail, or invalid with a
  failure label.

### repeat_check

Input:

- `check: CheckRecord`
- `verifier_workspace_factory: Callable`
- `repeat_count: int`
- `runtime_config: RuntimeConfig`

Output:

- `Sequence[CheckOutcome]`

Effect:

- Runs the check multiple times when certification or flakiness analysis needs
  stability evidence.

### summarize_check_evidence

Input:

- `outcome: CheckOutcome`

Output:

- `EvidenceSummary`

Effect:

- Produces sanitized evidence for Result and Reporting. It must not include
  hidden test text, expected outputs, or raw verifier logs unless explicitly
  allowed by a safe rule.

## Source Alignment Check

Aligned with the architecture:

- Keeps hidden oracle material out of solver workspaces.
- Allows checks beyond unit tests.
- Returns normalized outcomes that Workspace passes to Results. Selection reads
  those outcomes only through Result records.
