# Design Review Reference Notes

## Status

Non-normative reference notes.

These notes are not part of Barcarolle's source-of-truth architecture, requirements, decisions, policy semantics, or executable specification. They are reviewer observations from an architecture-baseline review and must not be treated as golden requirements by future agents or contributors.

If a later design change adopts any item below, that change must update the normative documents under `docs/architecture`, `docs/analysis`, or `docs/decisions` with its own rationale, contract language, and compatibility impact. Until then, these notes are prompts for further review only.

## Context

The reviewed design is intended as a complete architecture baseline rather than an MVP plan. The major architecture direction appears stable enough to commit as a design checkpoint:

- repository-specific benchmark and admission rather than a generic coding leaderboard;
- full ACUT evaluation rather than model-only evaluation;
- Runner Integration Layer as the default boundary rather than a default agent framework;
- clean-room canonical verification as the correctness root;
- immutable benchmark releases as comparison bases;
- separate benchmark facts, scorecards, authorization decisions, repository-agent admissions, and operating-state projections;
- repository-scoped `G0` through `G5` admission semantics;
- PostgreSQL, object storage, Temporal, OCI/gVisor, and policy-engine-oriented implementation direction.

The points below are not asserted as defects in the accepted design. They are candidate closure topics to consider while converting the architecture baseline into an executable specification.

## Reference Priority Notes

### P0 Reference: Calibration Truth and Maturity

The automatic policy-calibration design may need a more explicit truth and maturity model before high-tier authorization semantics become executable.

Why it matters:

- correctness truth can often be rooted in canonical verification;
- authorization safety truth, especially for `G4` and `G5`, is harder to derive only from objective historical controls;
- without an explicit maturity model, implementation could either promote too broadly or block too conservatively.

Possible follow-up direction:

- define calibration maturity states such as `seed_only`, `shadow`, `low_tier_active`, and `high_tier_eligible`;
- define minimum control power per tier and semantic slice;
- keep human governance as risk acceptance or rollback authority, not calibration truth.

### P1 Reference: ACUT Assurance Levels

High-tier native YOLO admission from non-invasive modes such as `patch_only` or `trace_submission` may need explicit assurance-level semantics.

Possible follow-up direction:

- define evidence-basis levels for material ACUT fields, for example declared, owner-attested, third-party-attested, adapter-observed, and Barcarolle-controlled;
- define minimum basis requirements by tier, operation class, and target condition;
- make clear when declared-only fields can support high-tier admission and when they force targeted validation or downgrade.

### P1 Reference: License Consumer Conformance

The License certificate and status model is detailed, but consumer-side conformance may need its own executable spec.

Possible follow-up direction:

- define deterministic matching algorithms and test vectors;
- define operation/resource taxonomy inputs consumed by local policy;
- provide SDK or CLI conformance behavior;
- define minimum consumer audit-event requirements and local policy overlay semantics.

### P1 Reference: Repository Operation and Resource Taxonomy

The `G0` through `G5` tier model names repository operations, but a provider-independent operation/resource vocabulary may be needed for machine-readable authorization.

Possible follow-up direction:

- define operation classes for branch, PR, issue, CI, workflow, dependency, merge, release, secret-adjacent, repository-admin, and protected-resource actions;
- map those classes to GitHub first, while leaving room for other providers;
- use the taxonomy in capability envelopes, certificates, policy rules, and consumer audit events.

### P1 Reference: Organization, Actor, and Consumer Model

Several documents reference organizations, repository owners, reviewers, consumers, and inherited risk profiles, but the required core model may need explicit identity and tenancy resources.

Possible follow-up direction:

- add or reference canonical entities for organization, user, team, installation, consumer integration, and membership/role bindings;
- define ownership of risk-profile inheritance, review authority, and License-consumer identity;
- keep this separate from external IdP implementation details.

### P1 Reference: Golden and Judge Minimum Schemas

Golden and Judge are first-class capability surfaces, but their minimum artifact and finding schemas may need to be locked before implementation.

Possible follow-up direction:

- define minimum output fields, confidence labels, risk/finding codes, evidence refs, and lifecycle states;
- default Judge output to advisory unless a governed score-contributing contract is explicitly defined;
- define comparison and promotion checks for governed assessor configurations.

### P1 Reference: Cross-Entity Invariant Catalog

The design has many append-only entities, lifecycle states, projections, and single-writer boundaries. A centralized invariant catalog may be needed to prevent locally valid records from producing globally inconsistent facts.

Possible follow-up direction:

- enumerate illegal state combinations;
- define projection rebuild rules for operating state and current status;
- specify writer ownership, race handling, conflict detection, and compensating-event patterns;
- turn high-risk invariants into API/workflow tests.

## Other Reference Topics

These are important but were not classified as immediate P0/P1 blockers for committing the architecture baseline:

- service virtualization and replay strategy for databases, queues, SaaS APIs, and other non-hermetic external dependencies;
- curated owner-authored or policy-authored tasks for high-risk capabilities not represented in repository history;
- evidence privacy, artifact-level access control, retention, legal hold, secret/PII incident handling, and redaction provenance;
- explicit multi-repository federation once the single-repository design is proven.

## Usage Rule for Future Agents

Future agents may use this file to find review prompts and closure candidates. They must not cite this file as authority for product semantics, policy behavior, required scope, or implementation acceptance criteria unless a later normative document adopts the relevant point.
