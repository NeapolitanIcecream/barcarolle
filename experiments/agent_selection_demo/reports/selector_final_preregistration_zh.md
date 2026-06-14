# Selector Final Preregistration

生成日期：2026-06-14

## Locked selector

- Selector: `hrd_70_30`。
- Budget k: `10`。
- Representative/discriminative split: `70/30`。
- Representative selector: `rsq_recency_stratified_quota`。
- Disagreement source: `metadata_cluster_density_difficulty_proxy`。

## Frozen task IDs

- Selected tasks before outcome join: `boltons__clean_ext__010, boltons__hist__014, boltons__hist__017, boltons__supply_expansion_20260526__001, boltons__supply_expansion_20260526__004, boltons__supply_expansion_20260526__006, boltons__supply_expansion_20260526__048, boltons__supply_expansion_20260526__066, boltons__supply_expansion_20260526__093, boltons__supply_expansion_20260526__095`。
- Later/Holdout tasks: `boltons__clean_ext__017, boltons__hist__019, boltons__hist__020, boltons__hist__022, boltons__hist__023, boltons__hist__024, boltons__hist__025, boltons__hist__026, boltons__hist__027, boltons__hist__028`。

## Decision thresholds

- Action margin: `0.05`。
- Minimum common valid tasks: `8`。
- Bootstrap iterations: `1000`。

## Paid boundary

默认不运行新 paid cells。只有 no-paid final result 因 missing cells 而无法解释时，才按 runbook paid boundary 补最小 frozen grid。本 preregistration 的 planned paid use 是 `0`。
