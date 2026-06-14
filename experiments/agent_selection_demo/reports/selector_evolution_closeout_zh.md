# Selector Evolution Closeout

生成日期：2026-06-14

## Corrected terminal-state label

Corrected label：`hypothesis_generating_selector_development_result`。

本轮没有停在 diagnostic summary。已实现并评估 RSQ、HRD、强随机基线和 shared decision wrapper，并完成 frozen no-paid replay。没有新 paid Agent cells。

Correction note：该结果不再表述为 independent validation。`hrd_70_30` 的 variant choice、final task subset 和 validation story 都来自同一批 boltons Selection/Holdout evidence；HRD arm 也使用 metadata fallback，而不是 leakage-safe historical Agent-disagreement signal。因此这些数字是 selector-development evidence，不是最终证明。

## Closeout checklist

1. Implemented selectors

`uniform_random_same_budget`、`quality_filtered_random`、`stratified_random`、`rsq_recency_stratified_quota`、`hrd_representative_only`、`hrd_disagreement_only`、`hrd_70_30`、`hrd_60_40`、`hrd_50_50`。

2. Final locked config

`hrd_70_30`，`k=10`，representative/discriminative split `70/30`，shared decision wrapper。

3. Final Selection pass rates

| Agent | Pass rate |
| --- | ---: |
| Codex + GPT mainline | `7/10 = 0.700000` |
| Kilo + GPT mainline | `9/10 = 0.900000` |
| Kilo + GPT low-cost | `7/10 = 0.700000` |
| Kilo + Claude Sonnet | `7/10 = 0.700000` |

4. Final later/Holdout pass rates

| Agent | Holdout pass rate |
| --- | ---: |
| Codex + GPT mainline | `5/10 = 0.500000` |
| Kilo + GPT mainline | `9/10 = 0.900000` |
| Kilo + GPT low-cost | `6/10 = 0.600000` |
| Kilo + Claude Sonnet | `8/10 = 0.800000` |

Doubled-timeout top-2 repeat：Codex + GPT mainline `6/10`，Kilo + GPT mainline `9/10`。

5. Did ranking transfer?

Yes. Selection top Agent is `Kilo + GPT mainline`; Holdout top Agent is also `Kilo + GPT mainline`。Recommended top-pair direction agreement is `true`。

6. Final MAE versus strong random baselines

Final selector MAE：`0.100000`。

Strong random baseline：`stratified_random__k10` mean MAE `0.151700`。

Absolute improvement：`0.051700`。Relative improvement：`34.0804%`。Selector beats/ties stratified-random MAE share：`1.0`。

7. Recommendation regret

Recommendation regret：`0.0`。

8. Decision state

The system output `recommend` and recommended `Kilo + GPT mainline`。

9. New paid cells

New paid cells：`0`。New paid cost：`$0.0`。

No paid completion was needed because the final selected-task Selection grid, all-Agent Holdout grid, and doubled-timeout top-2 repeat grid were complete enough in committed sanitized artifacts.

10. Tests and hygiene

Passed:

- `PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q` -> `29 passed`
- `PYTHONPATH=experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py -q` -> `6 passed`
- `git diff --check` -> pass
- `git ls-files experiments/agent_selection_demo | rg '(__pycache__|\.pyc$|raw|transcript|workspace|\.DS_Store|\.pytest_cache|\.venv)'` -> no matches; `rg` exit `1` recorded as pass

11. Exact development claim now supported

On the frozen `mahmoud/boltons` development slice, the HRD 70/30 selector plus shared decision wrapper can produce a Kilo + GPT mainline recommendation; the already-used original Holdout and doubled-timeout top-2 repeat are consistent with that recommendation, with zero recommendation regret. This motivates corrected validation but does not prove independent selector validity.

12. What remains unproved

This still does not prove independent selector validation, full predictive validity, cross-repository selector superiority, global Agent/model ranking, or future unseen generalization. It also does not establish a cost winner because old Selection cost usage coverage is not comparable across Agents.

## Canonical artifacts

- `experiments/agent_selection_demo/results/selector_evolution_closeout.json`
- `experiments/agent_selection_demo/reports/selector_agent_selection_demo_story_zh.md`
- `experiments/agent_selection_demo/results/selector_final_eval.json`
- `experiments/agent_selection_demo/reports/selector_final_eval_zh.md`
- `experiments/agent_selection_demo/results/selector_decision_eval.json`
- `experiments/agent_selection_demo/reports/selector_decision_eval_zh.md`
