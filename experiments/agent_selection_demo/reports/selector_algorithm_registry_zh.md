# Selector Algorithm Registry

生成日期：2026-06-14

## Implemented families

| Algorithm | Role | Status |
| --- | --- | --- |
| rsq_v2 | strong_metadata_baseline | implemented |
| flc | representative_core_set | implemented |
| hrd_v3 | decision_aware_hybrid | implemented |
| cod_lite | contrast_optimal_selector | implemented |
| ro_lsp | low_capacity_learned_scoring_policy | implemented |
| saes_lite | sequential_adaptive_evidence_selector | implemented |
| strong_random_baselines | baseline | implemented |

## Example deterministic selections

Example source: `phase1_blocked_split_heldout_development`；budget: `6` per repo。

| Algorithm | Selected | First tasks |
| --- | --- | --- |
| rsq_v2 | 18 | attrs::attrs__v2__157, attrs::attrs__v2__207, attrs::attrs__v2__215, attrs::attrs__v2__235 |
| flc | 18 | attrs::attrs__v2__044, attrs::attrs__v2__157, attrs::attrs__v2__187, attrs::attrs__v2__202 |
| hrd_v3_70_30 | 18 | attrs::attrs__v2__157, attrs::attrs__v2__202, attrs::attrs__v2__215, attrs::attrs__v2__235 |
| hrd_v3_60_40 | 18 | attrs::attrs__v2__157, attrs::attrs__v2__187, attrs::attrs__v2__202, attrs::attrs__v2__235 |
| hrd_v3_50_50 | 18 | attrs::attrs__v2__157, attrs::attrs__v2__187, attrs::attrs__v2__202, attrs::attrs__v2__235 |
| cod_lite | 18 | attrs::attrs__v2__044, attrs::attrs__v2__157, attrs::attrs__v2__187, attrs::attrs__v2__202 |
| ro_lsp | 18 | attrs::attrs__v2__157, attrs::attrs__v2__187, attrs::attrs__v2__202, attrs::attrs__v2__235 |
| saes_lite | 18 | attrs::attrs__v2__044, attrs::attrs__v2__157, attrs::attrs__v2__187, attrs::attrs__v2__202 |

## Leakage note

HRD v3、COD-lite 和 SAES-lite 都没有使用 leakage-safe historical Agent-disagreement signal；informativeness arm 在 registry 和后续报告中称为 `metadata_informativeness`。

RO-LSP 当前有固定 interpretable default weights；Package 5 只允许在 development sources 上做低容量 grid search，然后在 final replay 前冻结。
