# Barcarolle 项目展示 Deck 重复内容审计 V2

状态：V2 重复内容审计与 pruning plan，2026-06-02。

用途：把页面职责矩阵转成实际删并计划，减少重复页面角色、重复流程图、重复证据使用和重复句式。本文是内部执行依据，不作为投影片正文。

## Local Overlap Check

辅助检查位置：

```text
outputs/manual-20260602-114006-showcase-pruning/presentations/barcarolle-project-showcase-deck-pruning-style/qa/v1-term-overlap.txt
```

高重复组合：

| Pair | Shared terms | Manual judgment |
| --- | ---: | --- |
| Slide 7 `方法` / Slide 13 `研究路线` | 13 | 两页都使用 release、future、baseline、score、selection、fallback、validation 等词。V2 中 Slide 7 只保留 compiler workflow，Slide 13 只保留 validation protocol。 |
| Slide 5 `项目位置` / Slide 7 `方法` | 12 | Slide 5 的分层流程与 Slide 7 的 compiler workflow 重复。Slide 5 删除。 |
| Slide 5 `项目位置` / Slide 13 `研究路线` | 10 | Slide 5 的 future validation 末端与 Slide 13 重复。Slide 5 删除。 |
| Slide 1 `项目定位` / Slide 7 `方法` | 9 | Slide 1 的 release formula 与 Slide 7 workflow 重复。V2 Slide 1 只保留对象定义和三方关系。 |
| Slide 6 `研究目标` / Slide 13 `研究路线` | 8 | 两页都讲 future / baseline / freeze。V2 Slide 6 只讲 estimand 和 MAE，Slide 13 讲 future validation route。 |
| Slide 10 `算法环境` / Slide 13 `研究路线` | 4 | 两页都讲 baseline / fallback / selection / support。V2 Slide 10 讲当前 algorithm lab，Slide 13 讲正式验证 gate。 |

The overlap check is heuristic. Final pruning decisions are based on reader role and visual role, not term counts alone.

## Duplication Findings

### Page Roles

- Slide 5 does not have a unique reader-facing role after Slides 1, 4, and 7 remain.
- Slide 6 and Slide 13 should not both present a freeze-to-result strip. Slide 6 is the prediction target; Slide 13 is the future validation protocol.
- Slide 10 and Slide 13 can both mention baselines only if their roles differ: current comparison environment versus future validation gate.
- Slide 11 and Slide 12 can both mention MAE/fallback only if Slide 11 shows traction and Slide 12 maps weaknesses to required actions.
- Slides 14 and 15 can remain separate only if governance and tuning use different visual grammars and reader actions.

### Visual Objects

V1 repeated too many horizontal process strips:

- Slide 5: candidate supply -> certification -> assembly -> frozen release -> future validation.
- Slide 6: pre-outcome freeze -> named ACUT -> future evidence -> baseline envelope -> scoped result.
- Slide 7: candidate supply -> certification -> target profile -> assembly -> release -> score/refresh.
- Slide 13: freeze release -> run named ACUTs -> join outcomes -> compare baselines -> state result.

V2 distribution:

| Concept | V2 owner slide | Visual grammar |
| --- | --- | --- |
| Project object definition | Slide 1 | three-entity evidence layer diagram |
| Target-repo prediction gap | Slide 2 | source-to-target gap diagram |
| Deployment/tuning/governance stakes | Slide 3 | consequence map |
| Related-work layer positioning | Slide 4 | compact adjacent-layer matrix |
| Prediction target and MAE | Slide 5 from V1 Slide 6 | estimand panel + MAE interpretation |
| Compiler workflow | Slide 6 from V1 Slide 7 | single complete workflow |
| ACUT boundary | Slide 7 from V1 Slide 8 | solver/diff/verifier boundary diagram |
| Selection problem | Slide 8 from V1 Slide 9 | negative-result metric comparison + decision map |
| Algorithm environment | Slide 9 from V1 Slide 10 | algorithm lab map |
| Traction evidence | Slide 10 from V1 Slide 11 | evidence callout dashboard |
| Weakness to action | Slide 11 from V1 Slide 12 | limitation bridge |
| Future validation | Slide 12 from V1 Slide 13 | validation protocol route |
| Agent License path | Slide 13 from V1 Slide 14 | governance decision matrix |
| Agent Tuning path | Slide 14 from V1 Slide 15 | protected feedback loop |

### Key Vocabulary

Vocabulary is assigned to avoid local repetition:

| Vocabulary family | Primary owner | Allowed secondary use |
| --- | --- | --- |
| `target repository`, `ACUT`, `frozen release` | Slide 1 | ACUT boundary on Slide 7; named configurations on Slide 12 |
| `future target-repo work`, prediction gap | Slide 2 | estimand on Slide 5 |
| `deployment governance`, tuning stakes | Slide 3 | product use on Slides 13/14 |
| `related work`, candidate supply | Slide 4 | compiler workflow start on Slide 6 |
| `MAE`, average prediction error | Slide 5 | evidence value on Slide 10; margin issue on Slide 11 |
| `candidate supply`, `certification`, `assembly rule`, `release` | Slide 6 | not repeated as a full route elsewhere |
| `solver workspace`, `verifier workspace`, `hidden oracle` | Slide 7 | no other full boundary diagram |
| `weighted failure`, `selection`, `support`, `fallback` | Slide 8 | algorithm environment on Slide 9; weakness/action on Slide 11 |
| `baselines`, `random envelope`, `adapter diagnostics` | Slide 9 | baseline envelope only on Slide 12 |
| `120/120`, `30/30`, `0.209`, `0.2149`, `0.0059`, `93.4%` | Slide 10 | Slide 11 may cite only the small edge consequence |
| `6/18`, `6/6`, Codex/Kilo named configuration | Slide 11 | none |
| `pre-outcome freeze`, `outcome-unseen score join`, `baseline envelope`, `scoped result` | Slide 12 | none as a complete process |
| `evidence status`, `scoped use decision` | Slide 13 | no tuning loop repetition |
| `dev/eval/canary`, `failure taxonomy`, `scorecard`, `regression signal` | Slide 14 | no governance matrix repetition |

### Evidence Numbers

Evidence numbers remain unchanged and stay in their assigned roles:

- Weighted gaps: attrs `0.3148`, boltons `0.7481`; simple same-budget baselines `0.25` and `0.125` on the selection-problem slide.
- Execution and source-quality evidence: `120/120`, scoreability `1.0`, click `30/30` on the traction slide.
- Current candidate traction: MAE `0.209`, best aggregate baseline `0.2149`, edge `0.0059`, random beats/ties `93.4%` on the traction slide.
- Support/fallback limits: `6/18` selected slots fallback and boltons `6/6` fallback on the limitations slide.
- Adapter boundary: Codex/Kilo differences reported as named ACUT configuration evidence on the limitations and boundary slides; not as model-only superiority.

No score table, task ID, split label, source eligibility, task statement, or hidden-oracle material is changed by this pruning plan.

## Final Slide Order

| V2 slide | V1 source | Retained title label | Unique role | Primary visual |
| --- | --- | --- | --- | --- |
| 1 | Slide 1 | 项目定位 | Define Barcarolle's object and evidence-layer boundary. | three-entity evidence layer |
| 2 | Slide 2 | 问题 | Explain target-repo future-work prediction gap. | prediction gap diagram |
| 3 | Slide 3 | 代价 | Show why the gap changes deployment, tuning, and governance decisions. | consequence map |
| 4 | Slide 4 + part of Slide 5 | 相关工作 | Position Barcarolle after adjacent task/quality/freshness/scale/environment systems. | adjacent-layer matrix |
| 5 | Slide 6 | 研究目标 | Define the north-star estimand and MAE reading direction. | estimand and metric panel |
| 6 | Slide 7 + part of Slide 5 | 方法 | Show the only full compiler workflow and release output. | compiler workflow |
| 7 | Slide 8 | 执行边界 | Separate Barcarolle workspace/replay responsibilities from ACUT harness internals. | solver/diff/verifier boundary |
| 8 | Slide 9 | 算法问题 | Use weighted failure to show selection/support/fallback are research objects. | negative-result proof |
| 9 | Slide 10 | 算法环境 | Show current selector comparison environment. | algorithm lab map |
| 10 | Slide 11 | 当前效果 | Present traction evidence without claiming validity. | evidence callout dashboard |
| 11 | Slide 12 | 限制 | Convert weaknesses into repair/validation actions. | weakness-to-action bridge |
| 12 | Slide 13 | 研究路线 | Show future validation protocol. | validation route |
| 13 | Slide 14 | 产品化方向 | Show Agent License / governance evidence use. | governance matrix |
| 14 | Slide 15 | 产品化方向 | Show Agent Tuning feedback use with protected eval boundaries. | protected feedback loop |

## Merge Map

| Source content | Destination | Treatment |
| --- | --- | --- |
| Slide 5 statement that Barcarolle sits at the target-repo release compilation layer | Slide 4 | Add as the bottom synthesis line after the adjacent-work matrix. |
| Slide 5 candidate-supply/certification/assembly/release progression | Slide 6 | Reuse only as part of the single compiler workflow; do not keep a second process strip. |
| Slide 5 boundary against task generator / ACUT harness / leaderboard | Slide 1 and Slide 7 | Slide 1 defines benchmark compiler and ACUT boundary; Slide 7 defines harness boundary. No negative identity list in reader-facing text. |

## Process Visual Distribution

Rules for V2 build:

- One complete compiler workflow: Slide 6.
- One future validation route: Slide 12, visually distinct from Slide 6.
- One protected tuning loop: Slide 14, with dev feedback separated from eval/canary/future material.
- No retained slide may use a lightly edited copy of Slide 6's workflow grammar.
- Slide 5 uses equation/metric layout, not a flow strip.
- Slide 9 uses a lab map, not a future route.
- Slide 13 uses a decision matrix, not a feedback loop.

## Reader-Facing Style Implications

The final outline and PPTX must remove V1's visible binary-reframe patterns. Direct replacements should state the positive claim:

- Barcarolle controls benchmark compilation and verifier replay boundaries; ACUT controls its harness.
- Public benchmarks and task systems provide broad signals and supply; target-repo future estimation needs a compiled release and validation protocol.
- The current evidence is traction for continued optimization; predictive validity remains future work.
- Agent License and Agent Tuning are product paths that can consume Barcarolle evidence; Barcarolle does not issue licenses or prove tuning-loop improvement yet.

These style implications are execution guidance. The final reader-facing material should not expose runbook/process language.
