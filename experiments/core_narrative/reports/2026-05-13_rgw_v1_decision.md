# RGW-full-workspace-v1 Decision Note

Date: 2026-05-13

## Decision

Freeze `RGW-full-workspace-v1` as a negative / neutral baseline for the NFL story. Do not mix its RWork denominator with M5-W2, and do not run ACUT G as the next primary step.

## Evidence

RBench is useful but mostly separates model tier: `cheap-generic-swe` is 2/8, `cheap-click-specialist` is 3/8, `frontier-generic-swe` is 5/8, and `frontier-click-specialist` is 5/8.

RWork did not separate configurations. In the fixed denominator, all four ACUTs are 2/6. After validity audit, seven of nine RWork `unsafe_or_scope_violation` cells are source-derived URL-only policy holds, but the derived measured scores still do not show a Click-specialist advantage: `cheap-generic-swe`, `cheap-click-specialist`, and `frontier-generic-swe` are 2/4, while `frontier-click-specialist` is 2/5.

G is not interpretable yet. The 24 G cells are `verifier_infra_error` records from missing G6 evaluator/data readiness, so they are neither zero-score model failures nor usable ranking evidence.

## Consequences

M5 must answer a narrower question: whether a stronger task-agnostic Click specialist treatment can beat generic SWE on new held-out Click work.

The source-derived URL-only issue is a measurement repair for future primary semantics:

- model-generated URL, secret, credential, or ambiguous unsafe content remains `unsafe_or_scope_violation`;
- source-derived URL-only content in diff context or removed source lines can enter private verifier replay;
- public artifacts remain redacted and do not record the raw URL-bearing patch.

If M5-W2 fails to show W separation, stop before R2 or ACUT G and report a negative result.
