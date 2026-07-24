# Module Design: Verification

Status: current built-in behavior, 2026-07-23.

## Responsibility

Verify a candidate diff in a verifier `Workspace` by executing a `Check` and
normalizing the outcome.

Verification does not select tasks, run Agents, or store Result records.

## Inputs

- `CheckRecord`;
- verifier `VerifierWorkspace` adapter value;
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

`VerifierWorkspace` is a transient Verification-adapter value containing the
Check execution binding. It is deliberately distinct from Workspace's
lifecycle-owning `WorkspaceRef`; solver workspaces do not carry verifier-only
nullable fields.

## Functions

### hidden_material_digest

Input:

- hidden material file or directory path.

Output:

- canonical tree digest.

Effect:

- Digests relative paths, entry types, file contents, and executable bits using
  one versioned representation shared by Workspace and Verification.
- Rejects a symlink at the root or anywhere below it, and rejects unsupported
  filesystem entry types. Directory entries, including empty directories, are
  part of the identity.

`VERIFICATION_ADAPTER_DIGEST` identifies the exact built-in preparation and
execution semantics used by certification evidence.

### prepare_verifier

Input:

- `check: CheckRecord`
- `verifier_workspace: VerifierWorkspace`

Output:

- `VerifierWorkspace`

Effect:

- Injects hidden check material only into the verifier workspace and returns
  that workspace reference. The low-level function confines the destination
  to the verifier workspace; the Workspace module additionally reserves the
  `.barcarolle` namespace for its bound hidden material.
- Requires the destination to be absent. When the destination is inside the
  reserved namespace, that namespace must also be absent before creation.
  Material is copied without merging and the destination tree is rehashed
  before returning.
- Rechecks the bound command digest before material injection. This transient
  execution check is separate from the semantic Check manifest stored in
  `CheckRecord`.
- Preparation failures raise the `ValueError`-compatible
  `VerifierPreparationError`, which carries a stable failure label. Workspace
  maps that field into `CheckOutcome`; callers do not infer machine-readable
  state from exception text.

### verify_diff

Input:

- `check: CheckRecord`
- `verifier_workspace: VerifierWorkspace`
- `runtime_config: RuntimeConfig`

Output:

- `CheckOutcome`

Effect:

- Executes the check against the applied candidate diff within the configured
  timeout. `RuntimeConfig.timeout_seconds` is the default. A positive
  `CheckRecord.resource_limits["timeout_seconds"]` narrows it; an empty mapping
  uses the runtime default.
- Other resource-limit entries have effect only when the active execution
  adapter implements them. The built-in subprocess path does not claim
  filesystem, network, process, CPU, or memory isolation.
- Rechecks the bound command digest immediately before execution.
- Treats exit code 2 as an invalid Check execution rather than an ordinary test
  failure; adapters use it for verifier or harness infrastructure errors.

### normalize_outcome

Input:

- `raw_output: object`
- `normalization_config: CheckNormalizationConfig`

Output:

- `CheckOutcome`

Effect:

- Converts framework-specific outputs into pass, fail, or invalid with a
  failure label.
- Requires an exact boolean timeout, an integer-or-null exit code that excludes
  booleans, and a finite nonnegative duration. Malformed execution state becomes
  `invalid` with zero duration; it cannot compare equal to a pass exit code.
- `CheckNormalizationConfig` requires disjoint integer pass/invalid code tuples,
  nonempty failure labels, a positive excerpt bound, string redaction markers,
  and an exact boolean raw-text control before normalization.

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
