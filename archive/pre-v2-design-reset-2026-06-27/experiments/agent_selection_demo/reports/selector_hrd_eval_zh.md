# HRD Decision-aware Selector Eval

生成日期：2026-06-14

## Disagreement source

当前 frozen Selection candidate tasks 没有 leakage-safe 的历史 current-Agent disagreement matrix。因此 HRD 使用 fallback：source-cluster density、change-size proxy、legacy/source diversity 和 module redundancy penalty。

## Variant comparison

| Variant | k | Rep/Disc | MAE | Pairwise | Forced top | Later top | Forced regret | MAE beats stratified random | Regret beats stratified random |
| --- | ---: | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| `hrd_representative_only__k10` | `10` | `10/0` | `0.25` | `0.5` | `kilo_gpt_5_4` | `kilo_gpt_5_4` | `0.0` | `0.012` | `1.0` |
| `hrd_disagreement_only__k10` | `10` | `0/10` | `0.1` | `0.5` | `kilo_gpt_5_4` | `kilo_gpt_5_4` | `0.0` | `1.0` | `1.0` |
| `hrd_70_30__k10` | `10` | `7/3` | `0.1` | `0.5` | `kilo_gpt_5_4` | `kilo_gpt_5_4` | `0.0` | `1.0` | `1.0` |
| `hrd_60_40__k10` | `10` | `6/4` | `0.1` | `0.5` | `kilo_gpt_5_4` | `kilo_gpt_5_4` | `0.0` | `1.0` | `1.0` |
| `hrd_50_50__k10` | `10` | `5/5` | `0.1` | `0.5` | `kilo_gpt_5_4` | `kilo_gpt_5_4` | `0.0` | `1.0` | `1.0` |
| `hrd_representative_only__k20` | `20` | `20/0` | `0.1375` | `0.333333` | `codex_gpt_5_4` | `kilo_gpt_5_4` | `0.4` | `1.0` | `1.0` |
| `hrd_disagreement_only__k20` | `20` | `0/20` | `0.1375` | `0.333333` | `codex_gpt_5_4` | `kilo_gpt_5_4` | `0.4` | `1.0` | `1.0` |
| `hrd_70_30__k20` | `20` | `14/6` | `0.1375` | `0.333333` | `codex_gpt_5_4` | `kilo_gpt_5_4` | `0.4` | `1.0` | `1.0` |
| `hrd_60_40__k20` | `20` | `12/8` | `0.1375` | `0.333333` | `codex_gpt_5_4` | `kilo_gpt_5_4` | `0.4` | `1.0` | `1.0` |
| `hrd_50_50__k20` | `20` | `10/10` | `0.1375` | `0.333333` | `codex_gpt_5_4` | `kilo_gpt_5_4` | `0.4` | `1.0` | `1.0` |

## Best no-paid HRD slice

最佳 HRD variant 是 `hrd_70_30__k10`，k=`10`，MAE `0.1`，forced top `kilo_gpt_5_4`，later top `kilo_gpt_5_4`，forced regret `0.0`。

Selected tasks: `boltons__clean_ext__010, boltons__hist__014, boltons__hist__017, boltons__supply_expansion_20260526__001, boltons__supply_expansion_20260526__004, boltons__supply_expansion_20260526__006, boltons__supply_expansion_20260526__048, boltons__supply_expansion_20260526__066, boltons__supply_expansion_20260526__093, boltons__supply_expansion_20260526__095`。

这不是最终 recommend 规则；它说明 HRD 的 metadata disagreement arm 能把 selector 从原始 Selection tie 推向可由 Package 5 进一步检查的决策候选。
