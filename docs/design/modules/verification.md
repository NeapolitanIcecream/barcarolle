# Module Design: Verification

Status: draft, 2026-06-27.

## Responsibility

Verify a candidate diff in a verifier `Workspace` by executing a `Check` and
normalizing the outcome.

Verification does not select tasks, run Agents, or store Results.

## Inputs

- `CheckRecord`;
- verifier `WorkspaceRef`;
- applied candidate diff;
- verification runtime config.

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

### prepare_verifier

Input:

- `check: CheckRecord`
- `verifier_workspace: WorkspaceRef`

Output:

- `WorkspaceRef`

Effect:

- Injects hidden check material only into the verifier workspace and returns
  that workspace reference.

### verify_diff

Input:

- `check: CheckRecord`
- `verifier_workspace: WorkspaceRef`
- `runtime_config: RuntimeConfig`

Output:

- `CheckOutcome`

Effect:

- Executes the check against the applied candidate diff under bounded time and
  resource limits.

### normalize_outcome

Input:

- `raw_output: object`
- `normalization_config: CheckNormalizationConfig`

Output:

- `CheckOutcome`

Effect:

- Converts framework-specific outputs into pass, fail, or invalid with a
  failure label.

### repeat_verification

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

### summarize_evidence

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
