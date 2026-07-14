# Module Design: Verification

Status: draft, 2026-07-14.

## Responsibility

Verify a candidate diff in a verifier `Workspace` by executing a `Check` and
normalizing the outcome.

Verification does not select tasks, run Agents, or store Result records.

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
- Result Store;
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
  that workspace reference. The low-level function confines the destination
  to the verifier workspace; the Workspace module additionally reserves the
  `.barcarolle` namespace for its bound hidden material.

### verify_diff

Input:

- `check: CheckRecord`
- `verifier_workspace: WorkspaceRef`
- `runtime_config: RuntimeConfig`

Output:

- `CheckOutcome`

Effect:

- Executes the check against the applied candidate diff within the configured
  timeout. An execution adapter may add stronger process, network, filesystem,
  or resource limits.

### normalize_outcome

Input:

- `raw_output: object`
- `normalization_config: CheckNormalizationConfig`

Output:

- `CheckOutcome`

Effect:

- Converts framework-specific outputs into pass, fail, or invalid with a
  failure label.

### summarize_evidence

Input:

- `outcome: CheckOutcome`

Output:

- `EvidenceSummary`

Effect:

- Produces sanitized evidence for Result and Reporting. It must not include
  hidden test text, expected outputs, or raw verifier logs unless explicitly
  allowed by a safe rule.

## Design Consistency Check

- Keeps hidden oracle material out of solver workspaces.
- Allows checks beyond unit tests.
- Returns normalized outcomes that Workspace passes to Result Store. Selection
  reads those outcomes only through Result records.
