# Barcarolle 项目展示 Deck V4 证据准确性审计

状态：V4 evidence accuracy audit，2026-06-03。

用途：锁定 V4 deck 可使用的数字和声明边界。本文只核对已提交报告，不新增实验结果。

## Sources Checked

| Evidence area | Source |
| --- | --- |
| Proposal evidence summary | `docs/research/phase-1-proposal-evidence-package.md` |
| Validation gate | `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md` |
| Random-control distribution | `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md` |
| Baseline envelope | `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_baseline_envelope.md` |
| Future success gate | `experiments/phase1_compiler/reports/phase1_validation_protocol_candidate_policy_hardening_success_gate.md` |
| Evidence manifest | `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md` |
| V5 proposal report | `docs/research/barcarolle-proposal-report-v5.md` |

## Verified Values

| Item | Verified value | Source evidence | V4 deck wording |
| --- | --- | --- | --- |
| MAE candidate value | `0.209` | Baseline envelope `overall:overall`; V5 Section 7.3 | Use `MAE 0.209`. |
| Best simple aggregate baseline MAE | `0.2149` | Baseline envelope: `temporal_recent_baseline` | Use `best simple baseline 0.2149` or Chinese equivalent. |
| MAE edge | `0.0059` | Candidate - baseline MAE is `-0.0059`; V5 states edge `0.0059` | Use `edge 0.0059` and state it is small. |
| Random-control seed count | `1000` | Random baseline distribution report | Use `1000-seed random control`. |
| Random beats/ties share | `93.4%` | Random baseline distribution `overall:overall` | Use `93.4% beats/ties` only. |
| Future random gate | `95.0%` | Joint success gate | State current `93.4%` is below the future `95.0%` gate. |
| Planned cells | `120/120` | V5 and Phase 1 evidence package | Use `120/120 planned cells`. |
| Scoreability | `1.0` | V5 and Phase 1 evidence package | Use `scoreability 1.0`. |
| click source repair | `30/30` | Phase 1 evidence package and click repair decision | Use `click 30/30 tasks repaired`. |

## Gate Interpretation

The committed reports do not support a claim that the random-control criterion passed. The future joint success gate requires at least `95.0%` beats-or-ties on primary MAE, and the committed M3 value is `93.4%`.

Any V4 slide text must therefore use `93.4%` and describe it as traction below the future gate. The deck must not use `>=95%` or the `≥95%` symbol.

## Claim Boundary

Supported for V4:

- benchmark-side execution feasibility: `120/120` planned cells and scoreability `1.0`;
- source-quality repair feasibility: click `30/30` public-context repair;
- selector traction: candidate MAE `0.209` vs best simple aggregate baseline `0.2149`, edge `0.0059`, and `93.4%` random beats/ties across `1000` seeds;
- future gate status: not passed.

Not supported for V4:

- predictive validity has been established;
- the current selector passed the future joint gate;
- the random-control result reached the future `95.0%` gate;
- adapter differences prove model-only superiority;
- Agent Tuning improvement has been validated.
