# Corrected Selector Validation Story

生成日期：2026-06-14

## 结论

corrected validation **没有** 支持目标 user-facing story：

```text
Selection recommends an Agent, and later/Holdout validates that choice.
```

这次 correction 支持的结论更窄：

```text
在独立 Phase 1 pseudo-future held-out block 上，冻结的 HRD v2 selector 让 Kilo 在 Selection 和 later/Holdout 都领先；但 conservative recommend/abstain wrapper 返回 need_more_evidence，且 MAE 没有实质性 beat strongest random baseline。因此当前 selector 还不能对外讲成“Selection recommends an Agent”。
```

## 为什么旧结果不够

旧 `hrd_70_30`, `k=10` boltons result 已经 relabel 为 `hypothesis_generating_selector_development_result`。它的问题是 selector family、variant choice 和 story validation 使用了同一批 boltons Selection/Holdout evidence；HRD 的 disagreement arm 也不是 leakage-safe historical Agent-disagreement signal，而是 metadata fallback。

旧结果仍可作为开发证据，但不能作为 independent validation。

## Corrected validation source

本次使用 no-paid committed sanitized artifacts：

- Source: `phase1_blocked_split_heldout_three_repo`
- Mode: `retrospective_pseudo_future_blocked_split_heldout`
- Repos: `attrs`, `boltons`, `click`
- Agents: `codex_workspace`, `kilo_workspace`
- New paid cells: `0`
- New paid cost: `$0.00`

Protocol 在 join final outcomes 前冻结于：

- `experiments/agent_selection_demo/results/selector_corrected_protocol.json`
- `experiments/agent_selection_demo/reports/selector_corrected_protocol_zh.md`

## Frozen selector

- Selector: `hrd_v2_70_30`
- Budget: `6` tasks per repo, `18` total
- HRD arm name: `metadata_informativeness`
- Decision wrapper: `recommend` / `abstain_indistinguishable` / `need_more_evidence`
- Action margin: `0.05`
- Minimum common-valid selected tasks: `12`

## Frozen tasks

Selected tasks:

```text
attrs::attrs__v2__157
attrs::attrs__v2__202
attrs::attrs__v2__207
attrs::attrs__v2__215
attrs::attrs__v2__235
attrs::attrs__v2__271
boltons::boltons__v2__009
boltons::boltons__v2__076
boltons::boltons__v2__103
boltons::boltons__v2__128
boltons::boltons__v2__154
boltons::boltons__v2__231
click::click__third__091
click::click__third__206
click::click__third__220
click::click__third__238
click::click__third__250
click::click__third__274
```

Later/Holdout tasks: 30 tasks from the Phase 1 `H_future` block across attrs, boltons, and click. Full list is in `selector_corrected_validation_closeout.json`.

## Selection and later rates

| Agent | Selection | Later/Holdout |
| --- | ---: | ---: |
| `codex_workspace` | `6/18` = `0.333333` | `7/30` = `0.233333` |
| `kilo_workspace` | `11/18` = `0.611111` | `16/30` = `0.533333` |

Kilo is the forced top Agent in both Selection and later/Holdout. Forced top diagnostic regret is `0.0`.

But the actual decision output is:

```text
need_more_evidence
```

Reason: `paired_uncertainty_or_discordant_tasks_too_weak`. The selected paired comparison has 18 common-valid tasks: Kilo wins 6, ties 11, and loses 1 against Codex. The preregistered conservative wrapper does not recommend with a discordant loss.

## Random baseline comparison

Strongest same-budget random baseline is `stratified_random`.

| Metric | Frozen selector | Strongest random |
| --- | ---: | ---: |
| MAE | `0.088889` | `0.090146` |
| Absolute improvement | `0.001257` | required `>= 0.02` |
| Relative improvement | `0.013944` | required `>= 0.10` |
| MAE beats/ties random share | `0.402` | n/a |

The selector direction is plausible, but the MAE improvement is too small to claim it beats strong random.

## Paid boundary

Package 5 was skipped. The no-paid final grid was not missing in a way that blocked interpretation: 96/96 selected/later top-2 cells were policy-valid, with 95 scoreable rows and one `invalid_output` policy-fail row. The failure was `selector_does_not_recommend`, with secondary `strong_random_not_beaten`. Paid cells would not fix that without retuning on final evidence.

## Supported claim

Supported:

```text
The corrected validation shows that the frozen HRD v2 selector plus conservative decision wrapper should request more evidence on the independent Phase 1 pseudo-future held-out block.
```

Not supported:

- independent validation of the previous boltons `hrd_70_30` story;
- a corrected Selection benchmark that recommends an Agent;
- full predictive validity;
- global Agent/model ranking;
- cross-repository selector superiority.
