# Selector No-paid Independent Eval

生成日期：2026-06-14

## Result

- Preferred terminal state achieved: `False`。
- Negative blocker: `selector_does_not_recommend`。
- Decision state: `need_more_evidence`。
- Recommended Agent: `None`。
- Later top Agent: `kilo_workspace`。
- Recommendation regret: `None`。
- Top-pair direction agreement: `None`。

## Pass rates

- Selection: `codex_workspace: 6/18, kilo_workspace: 11/18`。
- Later/Holdout: `codex_workspace: 7/30, kilo_workspace: 16/30`。

## Strong random comparison

- Selector MAE: `0.088889`。
- Strongest random baseline: `stratified_random`。
- Strongest random MAE mean: `0.090146`。
- Absolute improvement: `0.001257`。
- Relative improvement: `0.013944`。
- MAE beats/ties random share: `0.402`。
- Regret beats/ties random share: `1.0`。

## Decision comparison

- Selector regret: `None`。
- Strongest random mean regret when recommending: `0.0`。
- Selector false-recommendation rate: `0.0`。
- Strongest random false-recommendation rate: `0.0`。
- Selector beats random on regret or false recommendation: `True`。

## Boundary

This is no-paid replay from committed sanitized Phase 1 artifacts. It is independent of the prior boltons selector-development slice, but remains pseudo-future held-out demo evidence rather than full predictive-validity proof.
