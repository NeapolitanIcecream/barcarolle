# Selector Bakeoff Final Eval

生成日期：2026-06-14

## Result

- Preferred terminal state achieved: `False`。
- Validated recommendation achieved: `True`。
- Negative terminal blocker: `random_decision_quality_not_strictly_beaten`。
- Independence label: `limited_no_paid_final_replay_after_development_on_sparse_sources`。
- Decision state: `recommend`。
- Recommended Agent: `kilo_workspace`。
- Later top Agent: `kilo_workspace`。
- Recommendation regret: `0.0`。
- Top-pair direction agreement: `True`。
- New paid cells: `0`；new paid cost: `$0.0`。

## Pass rates

- Selection: `codex_workspace: 5/26, kilo_workspace: 14/26`。
- Later/Holdout: `codex_workspace: 16/40, kilo_workspace: 22/40`。

## Random comparison

- Strongest random decision baseline: `uniform_random_same_budget`。
- Selector validated recommendation: `True`。
- Strongest random validated recommendation rate: `1.0`。
- Selector false-recommendation rate: `0.0`；random false-recommendation rate: `0.0`。
- Decision quality strictly beats random: `False`。
- Decision quality ties strong random: `True`。

## MAE auxiliary

- Selector MAE: `0.109615`。
- Strongest random MAE baseline: `source_recency_stratified_random`。
- Strongest random MAE mean: `0.106711`。
- Relative MAE improvement: `-0.027214`。
- MAE beats/ties random share: `0.454`。

## Boundary

This is a no-paid replay on committed sanitized outcomes. The source was held out from threshold and variant selection, but it is still a sparse retrospective pseudo-future source, not full predictive-validity proof.
