# M5-W2 to M6 Transition Decision

Status: `m5_frozen_m6_new_hypothesis`  
Generated at: `2026-05-13T00:00:00+08:00`

## Decision

M5-W2 is frozen as a completed negative result. The primary scores are not modified:

| ACUT | W2 score |
|---|---:|
| `cheap-generic-swe` | 5 / 10 |
| `cheap-click-deep-specialist-v2` | 5 / 10 |
| `cheap-click-specialist` | 4 / 10 |
| `frontier-generic-swe` | 4 / 10 |

The static Click context treatment did not beat the same-tier generic baseline. The M5 context-effect gate failed with margin 0 against the required +2 task margin.

M6 is a new preregistered hypothesis, not a continuation of M5 scoring and not a post-hoc rescue of M5. Its hypothesis is:

> RBench-calibrated repository repair guidance may improve cheap-tier Click performance on a fresh held-out W3 denominator.

## Boundaries

- Do not mix M5-W2 with RGW v1 or future W3 denominators.
- Do not lower the M5-W2 gate.
- Do not treat `cheap-click-deep-specialist-v2 > frontier-generic-swe` by one W2 task as NFL candidate evidence.
- Do not run R2, R3, or ACUT G before a new W3 gate is passed.
- Do not use W3 target commits, W3 reference patches, W3 hidden verifiers, W3 final diffs, W3 ACUT outputs, or W3 failed patches in the calibrated ACUT.

## M6 Setup Evidence

- M5 negative result: `experiments/core_narrative/reports/2026-05-13_m5_w2_negative_result.md`
- M5 no-new-call forensics: `experiments/core_narrative/reports/2026-05-13_m5_w2_failure_forensics.md`
- M6 calibrated ACUT: `experiments/core_narrative/configs/acuts/cheap-click-rbench-calibrated-v1.yaml`
- RBench-calibrated context pack: `experiments/core_narrative/context_packs/click_rbench_calibrated_v1/manifest.json`
- W3 protocol: `experiments/core_narrative/configs/m6_w3_protocol.yaml`

## Claim Boundary

M6 can only support a new repository-calibration claim if a fresh W3 denominator is admitted and the preregistered W3 gates pass. Until then, the current evidence remains a negative result for static Click context advantage.
