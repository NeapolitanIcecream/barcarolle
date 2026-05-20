# Barcarolle Restart Consensus

Date: 2026-05-20.

## Decision

Restart Barcarolle as a target-repository benchmark compiler for coding-agent
evaluation and tuning.

The new primary object is a calibrated benchmark release. The old Agent License,
G0-G5 admission, operator console, Golden/Judge governance, and ranking-reversal
experiment are moved out of the current research object.

## Accepted Thesis

Public SWE benchmarks and scalable task generators produce tasks when they are
available; Barcarolle decides which tasks should become the benchmark for this
repository, this agent family, this evaluation budget, and this tuning
objective.

If upstream task-generation pipelines are unavailable for benchmark-external
repositories, Barcarolle may build a minimal repo-history task generator or
adapter. That work is necessary input supply, not the central contribution. It
must be judged by certified yield, replayability, oracle quality, and cost.

## Evidence From Current Repository

The old README and architecture described Barcarolle as an Agent License and
admission system. The old core-narrative experiment targeted an NFL-style
ranking reversal. The latest committed M3-lite report explicitly says the old
story was not established because G-score was unavailable and W evidence was
limited.

The existing work still contributed useful infrastructure:

- ACUT identity and manifest discipline;
- task manifests with source and leakage boundaries;
- hidden-verifier task packaging;
- workspace-mode patch extraction;
- fresh verification;
- scorecard outcome taxonomy;
- artifact and budget hygiene.

## Archive Policy

Archived material is preserved for audit and selective reuse. It is not active
product semantics.

Large local raw experiment outputs stay ignored by Git. Small manifests, reports,
schemas, and scripts can remain tracked under the archive so future work can
reproduce or inspect the old evidence path.

## Productization Boundary

License issuance and G0-G5-style admission remain a natural downstream use of a
credible benchmark compiler. They are not part of this restart's research
deliverable, because the current evidence first has to establish task supply,
repo-specific signal, calibration, and tuning value.

The archived license/admission design should therefore be treated as future
product material. It can be revived by collaborators or downstream work after
the benchmark compiler has a defensible release format and empirical basis.

## New Workstream

1. Phase 0 headroom experiments.
2. MVP release schema, target profile, and runner.
3. Certification and task-supply funnel, including a minimal repo-history task
   generator if source adapters alone are insufficient.
4. Weighted assembly and uncertainty reporting.
5. Predictive validation against held-out future work.
6. Tuning interfaces after predictive or diagnostic value is established.
