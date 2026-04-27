# Native YOLO Admission Evidence Semantics

## Status

Proposed on 2026-04-27.

## Context

Barcarolle supports repository-scoped high-tier admission for native agent operation, including open-network YOLO-style operation. A concern was raised that open-network evaluation can measure production-fidelity behavior without proving blind capability, while offline or restricted-network evaluation can underestimate modern agent configurations whose normal production form depends on search, package registries, hosted documentation, issue trackers, and other networked tools.

The existing architecture already defines condition-bound License artifacts:

- `license_certificate` carries target-condition identity, capability-envelope identity, admitted subject, ACUT evidence basis, binding/attestation basis, License-consumption basis, policy gate results, and supporting refs.
- `repository_agent_admission` records the evaluated subject, admission subject, evaluation mode, adapter purity, target condition, capability envelope, evidence lineage, and gate basis.
- `repository_agent_operating_state.coverage_entries[]` exposes per-target-condition coverage for the selected or observed operating snapshot.
- Barcarolle records and signs admission semantics, certificate status, and audit surfaces, but does not implement a runtime enforcement plane.

The design question is therefore not whether Barcarolle should forbid open-network native evaluation. It should not. The design question is how to interpret high-tier native YOLO evidence without treating a bare tier label as a condition-free certification claim.

## Decision

Admission tier is condition-bound. A granted tier is meaningful only together with the certificate's target condition, capability envelope, evaluation mode, adapter purity, ACUT field evidence basis, binding/attestation basis, evidence lineage, freshness state, and repository scope.

Native open-network evidence is valid evidence for native open-network target conditions. It should not be downgraded merely because network access was available when the intended production condition also includes network access.

Offline or restricted-network evidence is valid for the offline or restricted target condition it evaluated. It must not be treated as a capability upper bound for a full native open-network agent configuration unless a governed compatibility rule explicitly says the restricted condition is equivalent or broader for the requested operation.

Open-network historical-task evidence should be described as production-fidelity evidence. It may or may not be blind-capability evidence, depending on task sealing, leakage checks, retrieval-only controls, memory posture, and the recorded evidence basis. This distinction affects interpretation, not the validity of the target-condition-bound admission.

Barcarolle does not enforce runtime behavior. It defines, records, signs, publishes, and audits the applicability semantics of the admission. Downstream systems may enforce locally, but downstream use outside the certificate condition is outside Barcarolle's claimed applicability.

## Non-Decisions

- No new trust-tier scale is introduced.
- No separate "native YOLO tier" is introduced.
- No sealed or holdout benchmark track is required as a precondition for native YOLO admission.
- No Barcarolle runtime enforcement plane is added.
- No requirement is added that modern native agents must be evaluated offline before open-network admission.
- No consumer implementation is mandated beyond the existing certificate, status, and audit contract.

## Consequences

User interfaces, reports, API summaries, and audit views must not present a bare `G5` or other bare tier as the full result. They should show the granted tier with at least the target condition, admitted subject, evaluation mode, adapter purity, capability envelope summary, scope, evidence lineage, and material evidence-basis summary.

Policy must not compare, downgrade, reuse, or consume scorecards across materially different target conditions, network postures, capability envelopes, evaluation modes, adapter-purity levels, or ACUT evidence bases without an explicit governed compatibility rule.

An offline or restricted-network result that performs poorly may be negative evidence for that restricted condition, but it is not automatically negative evidence for the same agent's full native open-network condition. Authorization should return `targeted_validation_required`, `full_rebenchmark_required`, `blocked`, or a condition-specific lower tier when the requested target condition was not actually evaluated.

An open-network native result can support high-tier native admission when the normal correctness, coverage, reliability, subject-applicability, ACUT-binding, License-consumption, risk-profile, freshness, and governance gates pass under the target condition recorded in the certificate and admission.

Sealed, private, or holdout tasks can strengthen the evidence basis by reducing answer-retrieval ambiguity. They remain optional evidence-enhancement mechanisms rather than mandatory conditions for native YOLO admission.

## Examples

`G5` under `native_yolo + open_network + full_tool_profile + declared_or_attested_native_runtime` is not the same admission as `G5` under `harness_bound + restricted_network + mediated_tools`.

`G3` under `offline_restricted` does not mean the same tested-agent snapshot is capped at `G3` under `native_yolo + open_network`, unless a governed compatibility rule says the offline condition is an adequate proxy for the requested open-network operation.

A `patch_only` open-network native run can be high-production-fidelity evidence for native YOLO operation. Its ACUT field evidence basis and binding/attestation basis must still be visible so operators can tell which material fields were declared, observed, attested, or Barcarolle-trusted.

## Links

- [Authorization semantics](../architecture/authorization-semantics.md)
- [API schema: License certificate](../architecture/api-schema.md#417a-license-certificate)
- [Data model: License certificate](../architecture/data-model.md#425a-license_certificate)
- [Operator console: License certificate detail](../architecture/operator-console.md#5-screen-map)
