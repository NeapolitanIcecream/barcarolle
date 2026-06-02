# Barcarolle 项目展示 Deck V3 架构说明

状态：V3 reader-centered architecture，2026-06-02。

用途：锁定 V3 的读者问题、页数、合并/删除决定和每页证明对象。本文是
内部执行与审计材料，不作为 reader-facing PPT 文案。

## Architecture Decision

V3 采用 `11` 页结构。这个页数符合 runbook 推荐范围，不需要额外页数
说明。

V3 的主线按读者顺序组织：

1. 项目对象是什么，ACUT 是什么。
2. 通用 benchmark 分数和目标仓库未来工作之间有什么缺口。
3. 相关工作已经贡献什么，Barcarolle 还要回答哪一层问题。
4. 研究目标和 MAE 怎样读。
5. Barcarolle 怎样把候选任务编译成 release。
6. 执行边界怎样保护 ACUT harness 与 hidden oracle。
7. 为什么 task selection / support / fallback 是核心算法问题。
8. 当前证据能支持什么、不能支持什么。
9. 后续研究怎样推进 task-selection algorithm 和 outcome-unseen validation。
10. Agent License 怎样使用仓库级证据层。
11. Agent Tuning 怎样使用受保护反馈回路。

## Slide Plan

| V3 slide | Title label | Reader question | V2 source | Proof object | Structural change |
| --- | --- | --- | --- | --- | --- |
| 1 | 项目定位 | Barcarolle 连接哪些对象，ACUT 是什么？ | V2 Slide 1 | target repo / benchmark release / ACUT relationship diagram | 首次解释 `ACUT = Agent Configuration Under Test，一次被评估的 agent 配置`；删除 `被测 ACUT`；重画三方关系图。 |
| 2 | 问题与代价 | 为什么通用 benchmark 分数还不能直接回答本仓库未来表现？ | V2 Slides 2-3 | general score -> target-repo future-work gap plus consequence rail | 合并问题与代价；把部署、调优、治理影响写成同一个决策问题。 |
| 3 | 相关工作与缺口 | 相邻工作贡献了什么，仍留下什么问题？ | V2 Slide 4 plus source sanity | adjacent-work contribution/gap matrix | 写全 SWE-bench、SWE-bench Verified、SWE-bench-Live、SWE-Bench++、SWE-smith、R2E-Gym；用 source sanity report 支撑。 |
| 4 | 研究目标 | predictive validity 和 MAE 对非内部读者意味着什么？ | V2 Slide 5 | formula panel plus MAE interpretation | 用可视化公式对象呈现 `W_r(a)`，不把公式留成普通正文；删除 `Formal scope` / `Route finding` / `Boundary` 卡片。 |
| 5 | 方法 | Barcarolle 的 compiler workflow 是什么？ | V2 Slide 6 | candidate supply -> certification -> target profile -> assembly -> frozen release workflow | 保留完整 workflow，但降低术语密度；删除底部意义不明矩形和过程文本。 |
| 6 | 执行边界 | Barcarolle 如何不变成 ACUT harness？ | V2 Slide 7 | solver workspace -> captured diff -> verifier workspace sequence | 全部可见说明改成中文；hidden oracle 只解释为 verifier-side validation material。 |
| 7 | 算法问题 | 为什么 task selection 改变估计，为什么需要 algorithm lab？ | V2 Slides 8-9 | selection/support/fallback decision map plus negative-result mini chart | 合并旧 weighted failure、support/fallback 和 algorithm lab；将 `算法环境` 吸收为算法问题的一部分。 |
| 8 | 当前证据 | 当前证据回答哪些读者问题，哪些仍未证明？ | V2 Slide 10 plus selected V2 Slides 8-9 evidence | evidence-by-question board | 只保留 traction evidence：`120/120`、scoreability `1.0`、click `30/30`、MAE `0.209` vs `0.2149`、random `93.4%`；不保留过程数据页。 |
| 9 | 研究路线 | 后续算法和验证怎样演进？ | V2 Slide 12 plus algorithm roadmap | algorithm-evolution roadmap with validation gates | 以 task-selection algorithm evolution 为中心；future holdout / rolling-origin 是验证路径；release freeze 和 success criteria 是协议前置条件。 |
| 10 | Agent License | deployment governance 如何使用证据层？ | V2 Slide 13 | evidence-status governance flow | 使用正面用途语言；删除 `但不负责` / `不接管` 风格；重画无孤立矩形的治理图。 |
| 11 | Agent Tuning | tuning 如何使用受保护反馈而不过拟合正式验证材料？ | V2 Slide 14 | protected dev/eval/canary feedback loop | 使用正面用途语言；重画清晰连接的反馈回路；不声称 tuning-loop improvement 已验证。 |

## Merge And Delete Map

| V2 content | V3 treatment | Reason |
| --- | --- | --- |
| Slide 2 `问题` and Slide 3 `代价` | Merge into V3 Slide 2 | 两页回答同一个读者问题：通用分数到目标仓库未来工作之间的决策缺口及其代价。 |
| Slide 4 `相关工作` | Keep as V3 Slide 3 | 相关工作页必须更具体，补充 source sanity 与全名。 |
| Slide 5 `研究目标` | Keep as V3 Slide 4 | 目标和 MAE 是必要 reader anchor，但需要更直观公式和解释。 |
| Slide 6 `方法` | Keep as V3 Slide 5 | 唯一完整 compiler workflow 保留，清理术语和错误生成残留。 |
| Slide 7 `执行边界` | Keep as V3 Slide 6 | ACUT boundary 是核心项目边界，但可见文本需要中文化。 |
| Slides 8-9 `算法问题` / `算法环境` | Merge into V3 Slide 7 | 旧 weighted failure、support/fallback 和 algorithm lab 都服务同一个问题：selection rule 怎样影响估计。 |
| Slide 10 `当前效果` | Keep as V3 Slide 8 | 证据按读者问题重组，不再堆过程数据。 |
| Slide 11 `限制` | Delete as standalone; absorb into V3 Slides 8-9 | fallback、adapter、small edge 是证据边界和路线约束，放到当前证据和研究路线中比独立限制页更清楚。 |
| Slide 12 `研究路线` | Recenter as V3 Slide 9 | 原路线页需要把算法演进放回中心，并把 protocol prerequisites 降为 gate。 |
| Slides 13-14 `产品化方向` | Keep as V3 Slides 10-11 | Agent License 和 Agent Tuning 是不同用例；都需要正向用途语言和重画图。 |

## Required Visual And Text Rules

- Slide 1 必须首次定义 ACUT；PPTX 中不得出现 `被测 ACUT`。
- Slide 3 相关工作名称必须完整显示，不使用 standalone `Verified` 或 `Live`。
- Slide 4 公式使用视觉上类似 LaTeX 的 typeset math block。若 PowerPoint 不支持
  原生 equation export，使用高质量可编辑文本分层近似，并在 QA 报告记录限制。
- Slides 1、5、6、10、11 是显式 diagram sanity check 对象。
- 所有图都必须有清楚 connector 方向；不得有孤立白色矩形、漂浮 connector、
  不可解释标签或可见生成痕迹。
- Reader-facing materials 不得包含 runbook/handoff 语言、本机 Downloads 路径、
  `不是……而是……` / `是……不是……` 式二分重述、`但不负责` 或 `不接管` 风格声明。
- 声明边界保持：预测效度尚未建立；Agent Tuning 效果尚未完成实证验证；
  adapter 差异按 named ACUT configuration 报告。

## Source Boundary

V3 事实边界来自：

- `docs/research/barcarolle-proposal-report-v5.md`
- `docs/research/phase-1-proposal-evidence-package.md`
- `docs/research/phase-1-validation-protocol-and-candidate-policy-hardening.md`
- `experiments/phase1_compiler/reports/proposal_report_v5_evidence_manifest.md`
- V2 deck package audit artifacts
- V3 related-work source sanity report

V3 不修改 score tables、selected task IDs、split labels、source eligibility、
task statements、hidden-oracle material 或已完成实验决定。
