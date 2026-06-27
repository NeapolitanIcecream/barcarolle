# Selector Algorithm Bakeoff Closeout

生成日期：2026-06-14

## Closeout checklist

1. 实现的算法：RSQ v2、FLC、HRD v3 `70/30`/`60/40`/`50/50`、COD-lite、RO-LSP、SAES-lite、四个强 random baselines。
2. 运行的 ablations：representative-only、informativeness-only、HRD split、with/without recency、with/without source/module caps、wrapper v1 vs wrapper v2。historical outcome feature ablation 没有作为 final-eligible ablation 运行，因为没有 leakage-safe historical Agent-disagreement feature。
3. 选中的决策规则：wrapper v2，`action_margin=0.10`，`min_common_valid=8`，`lcb_tolerance=0.10`，`tie_epsilon=0.05`，无 zero-loss 要求。
4. Development bakeoff table leader：`hrd_v3_70_30`；COD-lite 只是普通候选项。
5. Bakeoff replay source：`phase1_original_three_repo_split_heldout`，limited no-paid replay，作为附录证据而非最终 demo 主线。
6. Selection 是否推荐 Agent：是，推荐 `kilo_workspace`。
7. later/Holdout 是否验证推荐：是，later/Holdout top 也是 `kilo_workspace`。
8. Recommendation regret：`0.0`。
9. Random comparison：最终 decision quality 与最强 `source_recency_stratified_random` 持平，不是 strict beat。
10. MAE：final selector MAE `0.109615`，strong random MAE mean `0.106711`，relative MAE improvement `-0.027214`。
11. 新 paid cells 和成本：`0` cells，`$0.0`。
12. Tests and hygiene：agent-selection tests `41 passed`；Phase 1 retrospective predictive signal tests `6 passed`；`git diff --check` 通过；tracked artifact hygiene check 无匹配。
13. 当前支持的 bakeoff appendix claim：limited no-paid replay 中，HRD v3 `70/30` 推荐 Kilo，later/Holdout 验证 Kilo，regret 为 0。
14. 仍未证明：selector 严格优于最强 same-budget random、MAE 优于 random、full predictive validity、跨仓库 selector superiority、全局 Agent/model 排名。

## Artifacts

- `experiments/agent_selection_demo/results/selector_bakeoff_gate_reframe.json`
- `experiments/agent_selection_demo/results/selector_bakeoff_feature_manifest.json`
- `experiments/agent_selection_demo/results/selector_algorithm_registry.json`
- `experiments/agent_selection_demo/results/selector_decision_wrapper_v2_eval.json`
- `experiments/agent_selection_demo/results/selector_algorithm_bakeoff_eval.json`
- `experiments/agent_selection_demo/results/selector_bakeoff_final_preregistration.json`
- `experiments/agent_selection_demo/results/selector_bakeoff_final_eval.json`
- `experiments/agent_selection_demo/results/selector_algorithm_bakeoff_closeout.json`

## Boundary

本次没有运行 fresh paid cells。Bakeoff replay 达到“推荐被 later/Holdout 验证”的行为，但没有达到“推荐决策严格优于最强 random baseline”的完整 preferred terminal state。最终读者报告使用 HRD v3 `70/30` 作为主线；COD-lite 只保留在算法对比表或附录中。
