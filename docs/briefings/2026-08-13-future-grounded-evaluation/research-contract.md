# Research Contract

> 这是 2026-08-13 briefing 交付任务的历史合同，不是 Barcarolle 当前科学
> 合同。当前科学合同见
> [`../../research-program.md`](../../research-program.md)。

## 1. 目标

在 2026-08-13 16:30（Asia/Shanghai）前，交付一套可供用户自行编辑成 PPT 的中文研究材料：完整转存指定共享聊天；核查并扩展其论点；覆盖领域 landscape、Barcarolle 的位置、核心问题、相关工作及其未闭合缺口、拟议工作与预期效果；同时提供可复现图表和至少一幅 ImageGen 配图。

## 2. 范围与定义

- 核心问题：评测被用于反复选择或优化 Agent 后，评测上的改进是否仍能预测后来真实软件工程工作上的改进。
- “未来真实工作”指在历史 origin 之后才发生、且在评测构造与优化环节不可见的真实 repository workload；它是外部锚，不由 Generator、Selector 或 Optimizer 自行定义。
- “完整转存”指沿分享页 serialized React Router payload 的当前分支 mapping，还原并保存全部 11 条 user 与 11 条 assistant `final` 消息，以及角色、顺序、来源 URL 和抓取时间；system/tool/reasoning/commentary 和页面导航不属于这 11 轮可见问答。
- 交付面向非原生 AI 背景、技术转管理的评委：先用具体失败场景和实验讲清问题，再给必要术语；正文公式不超过两个。

## 3. 完成证据

1. 原始聊天同时有 Markdown 和结构化 JSON，消息数、角色顺序和文本长度经脚本核对。
2. landscape 覆盖静态真实任务、合成/生成任务、未来导向、交互式、自动改进/自适应评测等相邻方向；关键判断可追溯到一手来源。
3. 每个核心相关工作均回答“解决了什么、没有解决什么、为何不能单独闭合本项目问题”。
4. Barcarolle 的现状与数字引用仓库内可定位证据，并明确正反结果和 claim boundary。
5. 提案给出可证伪的工作包、核心对照实验、指标、里程碑、风险和不声称内容。
6. 视觉素材包含 ImageGen 配图、Python 科学图表、源数据/脚本、用途说明；真实数据与 hypothetical illustration 严格分开。
7. 完成来源、论断、视觉和仓库卫生审计；`git diff --check` 通过。

## 4. 不构成完成的结果

- 只润色聊天、没有外部核查；
- 只列论文、不解释问题边界和未解决缺口；
- 把生成任务“看起来真实”当作能预测真实未来 Agent 排名的证据；
- 把固定 Agent 的 pointwise MAE 改善当作 adaptive optimization safety；
- 把示意曲线或预期数字写成已观察结果；
- 用 RSI 愿景替代当前可验证 milestone；
- 让 Generator 自证 Generator 的有效性。

## 5. Optimistic premise

本 sprint 假定上述完整交付在给定边界内可以实现；该假定只用于保持搜索与执行，不作为任何候选结论正确的证据。

## 6. 边界与资源

- 时间上限：2026-08-13 16:30（Asia/Shanghai）。
- 允许：仓库只读审计、公开网络、一手论文/官方资料、并行研究代理、内置 ImageGen、repo-local Python/uv。
- 禁止：付费 benchmark Agent-solving/validation 调用、读取 sealed outcomes、实现具体 Generator、把未获支持的材料写成研究证据、提交 secrets/raw model transcripts/workspaces。
- 本次不是正式论文系统综述；目标是覆盖决策相关的代表性工作，并把缺口论证到可审计程度。

## 7. 主要失败模式与检查

| 失败模式 | 检查 |
| --- | --- |
| 共享聊天缺消息或混入侧栏 | 解析 structured payload 的 current-branch mapping；代码断言 11+11、严格交替、逐条文本进入 Markdown |
| 共享聊天中的来源占位符被误当引用 | 独立查找原论文/官方页；聊天仅标为原始讨论 |
| 相关工作名称、日期或主张错误 | 用论文/官方仓库交叉核对，记录访问日期 |
| “我们的差异”只是换名 | 对每项工作给出其 estimand、data anchor、exposure regime 与未闭合链条 |
| 内部正结果被夸大 | 同时呈现 estimand reversal、transfer failure 与 selection-after-search 限制 |
| 视觉误导 | 图注显式标注 observed / derived / hypothetical；脚本内写数据来源 |
| 好看的文档掩盖证据缺口 | 终审按 claim-evidence matrix 逐条检查 |

## 8. 路线组合

| 路线 | 核心问题 | 决定性材料 |
| --- | --- | --- |
| A：benchmark 机制版图 | 现有评测分别固定了什么、验证了什么 | 一手来源对比表 |
| B：optimization pressure | 为什么低平均误差不等于可安全指导反复优化 | 机制解释、相关理论与可证伪指标 |
| C：Barcarolle continuity | 新方向是否继承现有基础、还差什么 | 仓库证据、正反结果、work packages |
| D：adversarial audit | 叙事是否把未来愿景、示意和证据混在一起 | 逐条 claim/evidence/limitation 审计 |

只有当所有完成证据被具体产物覆盖、且审计没有与原目标同等强度的缺口时，才标记完成。
